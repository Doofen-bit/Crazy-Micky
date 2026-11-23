"""Build the final-presentation deck (PPTX + PDF) and the matching speaker script (Markdown + DOCX).

One source of truth: SCRIPT below feeds both the PowerPoint speaker notes and the script documents.
Numbers are read from results/ so slides never drift from the analysis.
Run after `python scripts/capture_slide_images.py` (needs the local site on :8000).
"""
from pathlib import Path
import json, re, subprocess, sys
import pandas as pd
import matplotlib
from matplotlib import cm
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from docx import Document
from docx.shared import Pt as DPt, RGBColor as DRGB

ROOT = Path(__file__).resolve().parents[1]
D, SL = ROOT / 'docs', ROOT / 'docs/figures/slides'
URL, REPO = 'https://doofen-bit.github.io/Crazy-Micky/', 'https://github.com/Doofen-bit/Crazy-Micky'

# ---------- data used on slides ----------
ov = pd.read_csv(ROOT / 'results/overview.csv'); ov['n'] = ov.up + ov.down
def grid(contrast):
    m = ov[ov.contrast == contrast].pivot(index='region', columns='zt', values='n')
    return m.loc[['SCN', 'Hb'], [4, 10, 16, 22]].astype(int).values.tolist()
RC, SC = grid('resilient_vs_control'), grid('susceptible_vs_control')
cx = pd.read_csv(ROOT / 'results/contrasts/SCN_zt16_resilient_vs_control.csv')
k = cx.loc[cx.symbol == 'Kcnk2'].iloc[0]
KFOLD, KLFC, KP = 2 ** k.log2FoldChange, k.log2FoldChange, k.padj
net = json.loads((ROOT / 'site/data/networks/SCN_zt16_resilient_vs_control.json').read_text())
T0 = net['terms'][0]
EXPECTED = net['foreground_size'] * T0['term_background'] / net['background_size']
OBS = T0['overlap_count']
TOTAL_R = sum(map(sum, RC)); NIGHT_R = RC[0][2] + RC[1][2]; TOTAL_S = sum(map(sum, SC))
SCN16 = RC[0][2]

# ---------- palette & helpers ----------
INK, MUTED, PAPER, LINE = '142C40', '536B7C', 'F4F7FA', 'DCE4EB'
TEAL, CORAL, BLUE, NAVY, CTRL, SUN = '007F79', 'C25532', '356AB4', '103F59', '596B85', 'E7B93F'
TITLE_FONT, BODY_FONT = 'Georgia', 'Segoe UI'
rgb = RGBColor.from_string
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]

def text(slide, x, y, w, h, paras, size=18, color=INK, bold=False, font=BODY_FONT, align=None, anchor=MSO_ANCHOR.TOP, space=6, italic=False):
    """paras: str (newline = paragraph) or list of str. **bold** spans are rendered bold."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(.04); tf.margin_top = tf.margin_bottom = Inches(.02)
    if isinstance(paras, str): paras = paras.split('\n')
    for j, line in enumerate(paras):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        if align: p.alignment = align
        p.space_after = Pt(space)
        for k2, part in enumerate(re.split(r'\*\*', line)):
            if not part: continue
            r = p.add_run(); r.text = part; f = r.font
            f.size = Pt(size); f.name = font; f.color.rgb = rgb(color); f.bold = bold or k2 % 2 == 1; f.italic = italic
    return tb

def box(slide, x, y, w, h, fill='FFFFFF', line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=.06, weight=1):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    if line: s.line.color.rgb = rgb(line); s.line.width = Pt(weight)
    else: s.line.fill.background()
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = radius
    s.text_frame.text = ''
    return s

def badge(slide, x, y, n, fill=TEAL, d=.42, size=15):
    s = box(slide, x, y, d, d, fill, None, MSO_SHAPE.OVAL)
    tf = s.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = str(n)
    r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = rgb('FFFFFF'); r.font.name = BODY_FONT
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return s

def arrow(slide, x, y, w=.45, h=.32, fill=TEAL):
    return box(slide, x, y, w, h, fill, None, MSO_SHAPE.RIGHT_ARROW)

def picture(slide, path, x, y, w=None, h=None, border=True, crop_bottom=0.0):
    iw, ih = Image.open(path).size; ih_eff = ih * (1 - crop_bottom)
    if w and h: s = min(w / iw, h / ih_eff); w, h = iw * s, ih_eff * s
    elif w: h = w * ih_eff / iw
    else: w = h * iw / ih_eff
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    if crop_bottom: pic.crop_bottom = crop_bottom
    if border: pic.line.color.rgb = rgb(LINE); pic.line.width = Pt(1)
    return pic, w, h

SPEAKER_COLOR = {'Yixuan': TEAL, 'Jinyu': BLUE, 'Yi Yao': CORAL, 'All': NAVY}
def new_slide(kicker, title, speaker, dark=False):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(INK if dark else PAPER)
    n = len(prs.slides)
    if kicker: text(s, .6, .38, 9.5, .35, kicker.upper(), 12, '7FD1C9' if dark else TEAL, True)
    if title: text(s, .6, .7, 10.6, .9, title, 32, 'FFFFFF' if dark else INK, font=TITLE_FONT)
    if speaker:
        chip = box(s, 11.05, .36, 1.7, .38, SPEAKER_COLOR[speaker], None, radius=.5)
        tf = chip.text_frame; p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = speaker; r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = rgb('FFFFFF'); r.font.name = BODY_FONT
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    text(s, .6, 7.05, 8, .3, 'Stress Atlas · Information Visualization · NYU Shanghai · Fall 2026', 10, '9FB3C2' if dark else MUTED)
    text(s, 12.2, 7.05, .6, .3, f'{n:02}', 10, '9FB3C2' if dark else MUTED, align=PP_ALIGN.RIGHT)
    return s

def card(slide, x, y, w, h, heading, body, num=None, color=TEAL, hsize=18, bsize=14):
    box(slide, x, y, w, h)
    tx = x + .22
    if num is not None: badge(slide, x + .2, y + .2, num, color); tx = x + .74
    text(slide, tx, y + .2, w - (tx - x) - .15, .45, heading, hsize, INK, True)
    text(slide, x + .22, y + .78, w - .4, h - .9, body, bsize, MUTED, space=4)

# ---------- speaker script (single source for notes + documents) ----------
# Each entry: speaker, target time, list of ('do', operator cue for Yixuan) / ('say', words to speak).
SCRIPT = [
 ('Yixuan', '0:20', [('do', 'Slides open in Slide Show (F5). Browser tab with the website already open in the background, scrolled to the top, “Reset all” pressed.'),
   ('say', 'Hi everyone, we are Yixuan, Jinyu and Yi Yao. Our project is called “Stress, across time”. It is an interactive website that lets anyone, with no biology background needed, explore a real brain experiment about stress. I will introduce the experiment and our question, Jinyu will explain the two lab technologies behind the data, and Yi Yao will walk you through the visualization.')]),
 ('Yixuan', '0:30', [('do', 'Press → (next slide).'),
   ('say', 'Think about people who go through something really stressful. Some develop depression, and others stay fine. That ability to bounce back is called resilience. To study it, researchers use mice. After the same stress, some mice cope and stay social. We call them resilient. Others start avoiding other mice. They are susceptible. A third group, the control group, is never stressed. These three shapes, circle, triangle and square, appear everywhere on our website.')]),
 ('Yixuan', '0:40', [('do', 'Press →.'),
   ('say', 'Here is the experiment, from a 2024 paper by Narain and colleagues, who shared all their data. Step one: for fifteen days, each test mouse met a bigger, aggressive mouse every day. Step two: a social test sorted them into resilient and susceptible. Step three: brain tissue was collected at four times of day. Step four: RNA-seq measured how active each of about forty-six thousand genes was. Jinyu will explain that.')]),
 ('Yixuan', '0:35', [('do', 'Press →.'),
   ('say', 'They looked at two brain regions. The SCN is the brain’s master clock. It keeps our daily rhythm in step with light and dark. The habenula reacts to disappointment and bad experiences, and it is over-active in depression. Because one region is literally a clock, time of day matters. Mice are active at night, so samples were taken twice while the lights were on and the mice rested, and twice after lights off, when they are active. These times are called ZT4, 10, 16 and 22: hours after lights on.')]),
 ('Yixuan', '0:30', [('do', 'Press →.'),
   ('say', f'So our research question is: which genes differ between resilient, susceptible and never-stressed mice, and does that depend on the brain region and the time of day? We have 93 brain samples from 47 mice, about forty-six thousand genes each, and 24 comparisons: two regions, times four times of day, times three pairs of groups. That is far too much to read in a table, which is why we built a visualization. Jinyu?')]),
 ('Jinyu', '0:50', [('do', 'Press → when Jinyu starts.'),
   ('say', 'Thanks. How do you measure what a gene is doing? Think of DNA as a cookbook. Every cell in your body has the same cookbook. What makes a brain cell different is which recipes it is actually using right now. When a cell uses a recipe, it makes photocopies of it, and those copies are called RNA. RNA-seq takes the tissue, reads millions of short pieces of those copies, and counts how many came from each gene. More copies means a more active gene. The result is a big table: one row per gene and one column per mouse.')]),
 ('Jinyu', '0:50', [('do', 'Press →.'),
   ('say', f'Then we compare the groups gene by gene, using a standard tool called DESeq2. We ask two questions. First, how big is the change? That is the fold change. For example, a gene called Kcnk2 is about {KFOLD:.1f} times as active in resilient mice as in control mice, in the clock region at ZT16. Second, how sure are we? With four mice per group and sixteen thousand genes tested at once, some differences are just luck, so we use an adjusted p-value: smaller means more confident. For Kcnk2 it is about {round(KP * 1e6)} in a million. We call a gene “changed” only if it passes both cutoffs. The volcano plot on the right shows every gene this way.')]),
 ('Jinyu', '0:45', [('do', 'Press →.'),
   ('say', f'{SCN16} changed genes are still hard to read, so we ask: what do they do? The Gene Ontology is a public database that tags genes with the jobs they do, a bit like hashtags. Then we check whether any tag appears more often than chance would predict. Take “regulation of membrane potential”, which is basically how neurons control their electrical charge, or how easily they fire. By chance we would expect about {EXPECTED:.0f} of our changed genes to carry this tag. We actually see {OBS}, almost {OBS / EXPECTED:.0f} times more. That is called enrichment. One caution: sharing a tag does not mean one gene controls another. Now Yi Yao will show how we turned all this into pictures.')]),
 ('Yi Yao', '0:30', [('do', 'Press → when Yi Yao starts.'),
   ('say', 'Thanks Jinyu. Our audience is people like you: classmates and curious readers with no biology background. We designed for three tasks. One, compare: where and when do genes change? Two, inspect: how does one gene behave in every individual mouse, not just on average? And three, explore: what do the changed genes do together?')]),
 ('Yi Yao', '0:40', [('do', 'Press →.'),
   ('say', 'We answer these with four views that share one state. View 1, the overview grid, counts changed genes for each region and time. View 2 is the volcano plot for one comparison. View 3 follows one gene through the day, showing every mouse. View 4 is a node-link diagram linking genes to the processes they share: our required complex layout. Clicking a box updates the other three views, clicking a gene updates Views 3 and 4, and clicking a process highlights its genes in View 2. Everything is built with D3.')]),
 ('Yi Yao', '0:45', [('do', 'Press →.'),
   ('say', 'Some key design choices. Because our audience is not biologists, we added a plain-language layer: a thirty-second primer, a hover glossary for every technical word, axes written in words, and a three-step guided story. We never rely on colour alone: boxes print their numbers, and groups use shapes and line styles. We show every mouse, not just averages, so you can see how noisy four mice are. And we replaced a moving force-directed network with a fixed two-column layout that is much easier to read.')]),
 ('Yi Yao', '1:45', [('do', 'Press →, then Alt+Tab to the browser (website at the top of the page).'),
   ('say', 'Let’s see it live. This is the public site on GitHub Pages.'),
   ('do', 'Scroll slowly past “The experiment in 30 seconds” down to “Follow the story”.'),
   ('say', 'At the top is the thirty-second primer we just explained.'),
   ('do', 'Hover the dotted words “adjusted p” in the dark control bar and hold for two seconds.'),
   ('say', 'Any dotted word shows a plain-language definition.'),
   ('do', 'Click the story button “1 When and where do genes change?”.'),
   ('say', f'Step one. In View 1, look at the ZT16 column: {RC[0][2]} changed genes in the clock region and {RC[1][2]} in the habenula, and almost nothing at the other times.'),
   ('do', 'In “Which groups to compare”, choose “Susceptible vs control”. Wait one second, then switch back to “Resilient vs control”.'),
   ('say', 'If we switch to susceptible mice, the night-time peak almost disappears.'),
   ('do', 'Click the story button “2 Follow one gene through the day”.'),
   ('say', 'Step two picks the most confident gene, Kcnk2. View 3 shows every single mouse. At ZT16 the triangles, the resilient mice, sit above the circles, the control mice.'),
   ('do', 'Scroll up a little and click the “Hb” box in the ZT16 column of View 1.'),
   ('say', 'If I click a different box, the gene stays selected and every view updates. That is the linking.'),
   ('do', 'Click the “SCN · ZT16” box again, scroll up to the story buttons, then click “3 What do the changed genes do?” (the page scrolls to View 4 by itself).'),
   ('say', 'Step three. In View 4, “regulation of membrane potential” is selected, and its genes are now outlined in the volcano plot.'),
   ('do', 'Click “Reset all”, then Alt+Tab back to the slides and press →.')]),
 ('Yi Yao', '0:35', [('say', 'Under the hood, the statistics run offline in R and Python, from the 96 raw count files. The website only loads small prepared files and draws them with D3, with no server, and GitHub Actions publishes it to GitHub Pages. Automatic tests cover all 24 comparisons, every linked click, empty states and phone screens. AI assistants, Codex and Claude, helped with code and drafts; we reviewed and tested everything and documented it. Yixuan will wrap up.')]),
 ('Yixuan', '0:40', [('do', 'Press →.'),
   ('say', f'So, back to our question. Yes, it depends strongly on time and on the group. Of the {TOTAL_R:,} genes that differ between resilient and control mice, {NIGHT_R:,} appear at ZT16, early in the active night, in both regions. And resilient mice, not susceptible ones, differ most from never-stressed mice: susceptible mice show only {TOTAL_S} changed genes in total. This agrees with the original paper. Our limits: four mice per group, males only, one study, and a difference at one time is not formal proof of a time effect.')]),
 ('All', '0:15', [('do', 'Press →. Leave this slide up during Q&A.'),
   ('say', '(Yixuan) The website is public. Please visit the link and try the guided story yourself. Thank you! We are happy to take questions.')]),
]

def _target(items):
    words = sum(len(t.split()) for k_, t in items if k_ == 'say')
    secs_ = words / 140 * 60 + (45 if sum(k_ == 'do' for k_, _ in items) > 3 else 0)
    secs_ = int(round(secs_ / 5) * 5); return f'{secs_ // 60}:{secs_ % 60:02}'
SCRIPT = [(spk, _target(items), items) for spk, _, items in SCRIPT]

# ---------- slides ----------
# 1 Title
s = new_slide('Information Visualization · Final project', None, None, dark=True)
text(s, .6, 1.25, 6.6, 1.2, 'Stress, across time.', 50, 'FFFFFF', font=TITLE_FONT)
text(s, .6, 2.55, 6.3, 1.6, 'Why do some stressed mice bounce back? An interactive look at **which genes** change, **where** in the brain, and **when** in the day.', 21, 'D6E4EC')
text(s, .6, 4.55, 6.3, 1.2, ['Yixuan Du · Jinyu Zheng · Yi Yao', URL], 17, '9FD3CD', space=8)
text(s, .6, 5.85, 6.3, .6, 'Data: Narain et al. (2024), Translational Psychiatry · public dataset, CC BY 4.0', 12, '9FB3C2')
picture(s, SL / 'dashboard_linked.png', 7.25, 1.1, w=5.5, crop_bottom=.5)
text(s, 7.25, 4.05, 5.5, .4, 'The live website: four linked D3 views', 12, '9FB3C2', align=PP_ALIGN.CENTER)

# 2 Resilience hook
s = new_slide('The experiment · why it matters', 'Same stress, different outcomes', 'Yixuan')
text(s, .6, 1.85, 5.1, 4.6, ['Many people go through serious stress. **Only some** develop depression; others stay well.',
     'That ability to bounce back is called **resilience**, and scientists still do not fully understand it.',
     'To study it, researchers use a **mouse model** in which some mice cope and others do not.'], 20, INK, space=16)
groups = [(MSO_SHAPE.OVAL, CTRL, 'Control', 'Never stressed. The baseline.'),
          (MSO_SHAPE.ISOSCELES_TRIANGLE, TEAL, 'Resilient', 'Stressed, but still approaches a new mouse.'),
          (MSO_SHAPE.RECTANGLE, CORAL, 'Susceptible', 'Stressed and now avoids other mice: a depression-like behaviour.')]
for j, (shp, col, name, desc) in enumerate(groups):
    y = 1.85 + j * 1.6
    box(s, 6.3, y, 6.4, 1.38)
    box(s, 6.6, y + .42, .55, .55, col, None, shp)
    text(s, 7.45, y + .2, 5.1, .45, name, 21, col, True)
    text(s, 7.45, y + .68, 5.1, .6, desc, 15, MUTED)
text(s, 6.3, 6.6, 6.4, .35, 'These shapes encode the three groups everywhere on our website.', 12, MUTED, italic=True)

# 3 Experiment steps
s = new_slide('The experiment', 'Four steps, from stress to data', 'Yixuan')
steps = [('Stress', '**15 days.** Each test mouse meets a larger, aggressive mouse every day (“chronic social defeat”). Controls are never stressed.'),
         ('Sort', 'A **social test** sorts stressed mice: resilient mice still approach a new mouse, susceptible mice avoid it.'),
         ('Sample', 'Brains collected at **4 times of day**, from **2 regions**: the SCN and the habenula.'),
         ('Measure', '**RNA-seq** measures how active each of **~46,000 genes** is in every sample.')]
for j, (h, b) in enumerate(steps):
    x = .6 + j * 3.15
    card(s, x, 1.95, 2.8, 3.55, h, b, j + 1, hsize=20, bsize=15)
    if j < 3: arrow(s, x + 2.82, 3.55, .3, .3)
# simple icons
ic = 2.65
box(s, .9, 4.55, .55, .38, '9FB3C2', None, MSO_SHAPE.OVAL); box(s, 1.5, 4.45, .8, .52, CORAL, None, MSO_SHAPE.OVAL)
box(s, 4.0, 4.5, .45, .45, TEAL, None, MSO_SHAPE.ISOSCELES_TRIANGLE); box(s, 4.65, 4.5, .45, .45, CORAL, None, MSO_SHAPE.RECTANGLE)
box(s, 7.1, 4.45, .55, .55, SUN, None, MSO_SHAPE.OVAL); box(s, 7.85, 4.45, .55, .55, NAVY, None, MSO_SHAPE.MOON)
for j, hgt in enumerate([.35, .6, .25, .5, .7]):
    box(s, 10.15 + j * .22, 5.0 - hgt, .16, hgt, BLUE if j < 3 else CORAL, None, MSO_SHAPE.RECTANGLE)
text(s, .6, 5.85, 12.1, .9, 'Source: Narain, Petković, … Chaudhury (2024). “Nighttime-specific gene expression changes in suprachiasmatic nucleus and habenula are associated with resiliency to chronic social stress.” Translational Psychiatry. All raw data are public (GIN, CC BY 4.0).', 12, MUTED)

# 4 Regions and time
s = new_slide('The experiment', 'Where and when they looked', 'Yixuan')
for j, (name, sub, desc, col) in enumerate([
        ('SCN', 'the master clock', 'A tiny region that keeps the body’s daily rhythm in step with light and dark.', TEAL),
        ('Hb', 'the habenula', 'Reacts to disappointment and bad experiences; over-active in depression.', CORAL)]):
    y = 1.9 + j * 2.25
    box(s, .6, y, 5.0, 2.0)
    text(s, .85, y + .2, 4.6, .6, f'**{name}** · {sub}', 22, col)
    text(s, .85, y + .85, 4.5, 1.1, desc, 16, MUTED)
X0, X1, Y = 6.3, 12.7, 3.3
text(s, X0, 1.95, 6.4, .5, 'One 24-hour day in the lab', 18, INK, True)
wd = (X1 - X0) / 2
box(s, X0, Y, wd, .7, 'F6DF92', None, MSO_SHAPE.RECTANGLE); box(s, X0 + wd, Y, wd, .7, NAVY, None, MSO_SHAPE.RECTANGLE)
text(s, X0, Y + .16, wd, .4, '☀ lights on · mice rest', 15, INK, True, align=PP_ALIGN.CENTER)
text(s, X0 + wd, Y + .16, wd, .4, '☾ lights off · mice active', 15, 'FFFFFF', True, align=PP_ALIGN.CENTER)
for z in [4, 10, 16, 22]:
    xx = X0 + (X1 - X0) * z / 24
    box(s, xx - .13, Y + .85, .26, .26, TEAL, None, MSO_SHAPE.OVAL)
    text(s, xx - .6, Y + 1.15, 1.2, .4, f'ZT{z}', 16, INK, True, align=PP_ALIGN.CENTER)
for z, lab in [(0, 'ZT0'), (12, 'ZT12'), (24, 'ZT24')]:
    text(s, X0 + (X1 - X0) * z / 24 - .5, Y - .42, 1.0, .35, lab, 11, MUTED, align=PP_ALIGN.CENTER)
text(s, X0, 5.0, 6.4, 1.4, ['**ZT** (“zeitgeber time”) = hours after the lights turn on.', 'Samples were taken at the **4 teal dots**: 2 in the rest phase, 2 in the active phase. Different mice at each time.'], 15, MUTED, space=8)

# 5 Research question
s = new_slide('Our research question', None, 'Yixuan')
box(s, .6, 1.2, 12.1, 2.3, 'E7F2F0', None)
box(s, .6, 1.2, .12, 2.3, TEAL, None, MSO_SHAPE.RECTANGLE)
text(s, 1.05, 1.45, 11.4, 1.9, 'Which genes differ between resilient, susceptible and never-stressed mice, and does the answer depend on the **brain region** and the **time of day**?', 30, INK, font=TITLE_FONT, anchor=MSO_ANCHOR.MIDDLE)
stats = [('93', 'brain samples'), ('47', 'mice'), ('~46,000', 'genes per sample'), ('24', 'comparisons\n2 regions × 4 times × 3 group pairs')]
for j, (num, lab) in enumerate(stats):
    x = .6 + j * 3.1
    text(s, x, 3.95, 2.9, .8, num, 40, TEAL, font=TITLE_FONT)
    text(s, x, 4.8, 2.9, .9, lab, 15, MUTED, space=2)
text(s, .6, 5.9, 12.1, .8, 'The paper reports that most changes happen at night and in resilient mice. Our website lets anyone check that claim in our own re-analysis of the public data.', 16, INK, italic=True)

# 6 RNA-seq
s = new_slide('Technology 1 · RNA-seq', 'Counting gene “messages”', 'Jinyu')
flow = [('DNA', 'The cookbook.\nEvery cell has the same one.'), ('RNA', 'Photocopies of the recipes a cell is using right now.'),
        ('Sequencing', 'Read millions of short snippets of those copies.'), ('Count table', 'Snippets per gene, per mouse = gene activity.')]
for j, (h, b) in enumerate(flow):
    x = .6 + j * 3.15
    card(s, x, 1.9, 2.75, 2.1, h, b, j + 1, BLUE, 20, 15)
    if j < 3: arrow(s, x + 2.8, 2.8, .3, .3, BLUE)
# schematic count table
rows = [['Gene', 'Mouse A', 'Mouse B', 'Mouse C', '…'], ['Gene 1', '1,204', '1,350', '2,410', '…'], ['Gene 2', '15', '9', '22', '…'], ['Gene 3', '0', '2', '1', '…'], ['… ×46,000', '', '', '', '']]
tbl = s.shapes.add_table(len(rows), 5, Inches(.6), Inches(4.45), Inches(6.4), Inches(2.0)).table
for r_, row in enumerate(rows):
    for c_, v in enumerate(row):
        cell = tbl.cell(r_, c_); cell.text = v; p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(13); p.font.name = BODY_FONT; p.font.bold = r_ == 0; p.font.color.rgb = rgb('FFFFFF' if r_ == 0 else INK)
        cell.fill.solid(); cell.fill.fore_color.rgb = rgb(BLUE if r_ == 0 else ('FFFFFF' if r_ % 2 else 'EEF3F8'))
text(s, .6, 6.5, 6.4, .35, 'Schematic numbers, for illustration only.', 11, MUTED, italic=True)
text(s, 7.4, 4.45, 5.3, 2.2, ['More copies of a gene’s RNA → **more reads** → a **more active** gene.', 'Our data: 96 count files (2 regions per mouse), 93 kept after the authors’ quality exclusions.'], 17, INK, space=12)

# 7 Comparing groups
s = new_slide('Technology 1 · comparing groups', 'Is a gene really different?', 'Jinyu')
card(s, .6, 1.85, 5.9, 1.75, 'How big?  →  fold change', f'Average in resilient ÷ average in control.\nKcnk2 (SCN, ZT16): **{KFOLD:.1f}× more active** (log₂ fold change = {KLFC:.2f}).', 1, BLUE, 19, 15)
card(s, .6, 3.75, 5.9, 1.75, 'How sure?  →  adjusted p-value', f'Only 4 mice per group, and ~16,000 genes tested at once, so we correct for luck. Smaller = more confident. Kcnk2: **{KP:.1e}**.', 2, BLUE, 19, 15)
box(s, .6, 5.65, 5.9, 1.1, 'FFF8E6', 'F0D58C')
text(s, .8, 5.75, 5.5, .95, '**“Changed gene”** = passes both cutoffs (adjusted p < 0.05 **and** change > 1.4×). Tool: DESeq2, run on all 24 comparisons.', 15, INK, anchor=MSO_ANCHOR.MIDDLE)
picture(s, SL / 'volcano.png', 6.85, 1.85, w=5.85, h=4.9)

# 8 GO enrichment
s = new_slide('Technology 2 · Gene Ontology (GO) analysis', 'What do the changed genes do?', 'Jinyu')
text(s, .6, 1.85, 6.0, 3.0, ['The **Gene Ontology** is a public database that tags each gene with the jobs it does, like hashtags.',
     '**Enrichment** asks: does a tag appear among our changed genes **more often than chance** would predict?',
     '“Regulation of membrane potential” = how neurons control their electrical charge, i.e. how easily they fire.'], 17, INK, space=14)
box(s, .6, 5.4, 6.0, 1.25, 'FFF8E6', 'F0D58C')
text(s, .8, 5.5, 5.6, 1.05, f'**Caution:** genes sharing a tag ≠ one gene controls another. In SCN at ZT16, {net["total_enriched"]} of {net["tested_terms"]:,} tested processes were enriched.', 14, INK, anchor=MSO_ANCHOR.MIDDLE)
# native bar chart: expected vs observed
bx, by, bw, bh = 7.6, 2.2, 4.7, 3.6
text(s, 7.1, 1.85, 5.6, .4, 'Changed genes tagged “regulation of membrane potential”', 15, INK, True)
scale_ = bh / (OBS * 1.15)
for j, (lab, val, col) in enumerate([('Expected by chance', EXPECTED, '9FB3C2'), ('Observed', OBS, TEAL)]):
    x = bx + .4 + j * 2.2; hh = val * scale_
    box(s, x, by + bh - hh + .4, 1.4, hh, col, None, MSO_SHAPE.RECTANGLE)
    text(s, x - .3, by + bh - hh - .15, 2.0, .5, f'{val:.0f}', 28, col if j else MUTED, True, TITLE_FONT, PP_ALIGN.CENTER)
    text(s, x - .4, by + bh + .5, 2.2, .5, lab, 14, INK, align=PP_ALIGN.CENTER)
box(s, bx, by + bh + .4, 4.7, .02, MUTED, None, MSO_SHAPE.RECTANGLE)
text(s, 7.1, 6.55, 5.6, .4, f'≈{OBS / EXPECTED:.1f}× more than chance · adjusted p = {T0["padj"]:.0e}', 14, TEAL, True, align=PP_ALIGN.CENTER)

# 9 Audience and tasks
s = new_slide('Visualization · audience and tasks', 'Who it is for, and what they can do', 'Yi Yao')
text(s, .6, 1.75, 12.1, .7, '**Audience:** classmates and curious readers with **no biology background** (and new lab members).', 19, INK)
tasks = [('Compare', 'Where and when do genes change?', 'Compare groups · locate hot spots', 'View 1 overview grid'),
         ('Inspect', 'How does one gene behave in every mouse?', 'See distribution · spot outliers', 'Views 2 + 3'),
         ('Explore', 'What do the changed genes do together?', 'Explore relationships', 'View 4 network → View 2')]
for j, (h, q, vt, v) in enumerate(tasks):
    x = .6 + j * 4.1
    card(s, x, 2.55, 3.8, 3.4, h, f'**“{q}”**\n\nVis task: {vt}\nAnswered by: {v}', j + 1, CORAL, 22, 16)
text(s, .6, 6.2, 12.1, .5, 'Success = a reader can say which groups, region and time they compared, how many mice, and what the result can and cannot show.', 15, MUTED, italic=True)

# 10 Four linked views
s = new_slide('Visualization · four linked views', 'Four views, one shared state', 'Yi Yao')
pic, pw, ph = picture(s, SL / 'dashboard_linked.png', .6, 1.6, h=5.3)
for j, (fx, fy) in enumerate([(.02, .015), (.455, .015), (.02, .435), (.455, .435)]):
    badge(s, .6 + pw * fx, 1.6 + ph * fy, j + 1, CORAL, .36, 13)
views = [('Overview grid', 'Region × time. Each box counts changed genes (heatmap + printed numbers).'),
         ('Volcano plot', 'Every gene in one comparison: change size vs confidence.'),
         ('Gene through the day', 'Every mouse at 4 times, plus group averages.'),
         ('Gene–process network', 'Node-link diagram: our required complex layout.')]
for j, (h, b) in enumerate(views):
    y = 1.6 + j * .92
    badge(s, 6.1, y + .05, j + 1, CORAL, .4, 14)
    text(s, 6.65, y, 6.1, .4, h, 17, INK, True)
    text(s, 6.65, y + .37, 6.1, .5, b, 13, MUTED)
box(s, 6.1, 5.4, 6.6, 1.45, 'FFFFFF')
text(s, 6.3, 5.48, 6.3, 1.3, ['**Linked interactions**', 'Click a box → Views 2, 3, 4 update', 'Click a gene → Views 3, 4 update', 'Click a process → its genes light up in View 2'], 13, INK, space=2)

# 11 Design choices
s = new_slide('Visualization · design choices', 'Designed for non-experts', 'Yi Yao')
choices = [('Plain language first', '30-second experiment primer; hover glossary for every technical word; axes in words (“◀ less active | more active ▶”); a 3-step guided story.'),
           ('Never colour alone', 'Boxes print their numbers; groups use shapes ● ▲ ■ and line styles; selections use outlines and labels.'),
           ('Show every mouse', 'View 3 plots individual mice, not only averages, so the small sample size stays visible. Missing data is never drawn as zero.'),
           ('Stable network layout', 'Alternative: a force-directed layout moved constantly and was hard to read. A fixed two-column layout is stable and readable.')]
for j, (h, b) in enumerate(choices):
    x = .6 + (j % 2) * 6.15; y = 1.75 + (j // 2) * 2.15
    card(s, x, y, 5.95, 1.95, h, b, j + 1, CORAL, 19, 15)
picture(s, SL / 'story.png', .6, 6.15, w=12.1)

# 12 Live demo
s = new_slide('Visualization · live demo', 'Let’s try it', 'Yi Yao')
demo = ['Experiment primer and hover glossary', 'Story step 1: the ZT16 night-time column stands out',
        'Switch to susceptible vs control: the peak almost vanishes', 'Story step 2: follow Kcnk2 and see every mouse',
        'Click another box: the gene stays selected (linking)', 'Story step 3: a process lights up its genes in the volcano']
for j, d in enumerate(demo):
    y = 1.8 + j * .72
    badge(s, .6, y, j + 1, CORAL, .42, 14)
    text(s, 1.2, y + .02, 6.6, .5, d, 18, INK)
box(s, 8.3, 1.8, 4.4, 3.0, NAVY, None)
text(s, 8.55, 2.0, 3.9, 2.6, ['Open it yourself', URL, '', 'No sign-in. Works on phones.'], 17, 'FFFFFF', space=6)
text(s, 8.3, 5.05, 4.4, 1.4, 'Backup if the network fails: run start_explorer.cmd for a local copy, or talk through the screenshots on slides 7 and 10.', 12, MUTED, italic=True)

# 13 Implementation & testing
s = new_slide('Visualization · how it is built and checked', 'From raw counts to a static website', 'Yi Yao')
pipe = [('96 raw count files', 'public dataset'), ('R · DESeq2', '24 comparisons'), ('Python', 'GO enrichment\nJSON export'),
        ('D3.js app', 'shared state\n4 views'), ('GitHub Pages', 'auto-deployed\nby Actions')]
for j, (h, b) in enumerate(pipe):
    x = .6 + j * 2.5
    box(s, x, 1.85, 2.15, 1.5, 'FFFFFF')
    text(s, x + .1, 1.95, 1.95, .45, h, 16, INK, True, align=PP_ALIGN.CENTER)
    text(s, x + .1, 2.45, 1.95, .85, b, 13, MUTED, align=PP_ALIGN.CENTER, space=0)
    if j < 4: arrow(s, x + 2.17, 2.45, .3, .3, CORAL)
text(s, .6, 3.75, 6.0, 3.0, ['**Tested automatically**', '• Statistics re-checked: all 24 comparisons, directions, missing values, GO math',
     '• Browser tests: every comparison, every linked click, empty states, phone width (390 px), no errors',
     '• Statistics never run in the browser; it only filters prepared results'], 17, INK, space=8)
text(s, 6.9, 3.75, 5.8, 3.0, ['**Credits and AI use**', '• Data: Narain et al. 2024 (CC BY 4.0) · DESeq2 · Bioconductor mouse GO · D3.js v7',
     '• AI assistants: Codex (pipeline and code drafts), Claude (plain-language revision, slides). The team reviewed and tested all of it; see AI_USAGE.md'], 17, INK, space=8)

# 14 Findings
s = new_slide('Answer to our question', 'So, what did we find?', 'Yixuan')
cmap = matplotlib.colormaps['GnBu']; vmax = max(max(map(max, RC)), 1)
def mini_grid(x, y, title, g):
    text(s, x, y, 5.6, .4, title, 16, INK, True)
    for c_, z in enumerate([4, 10, 16, 22]):
        text(s, x + .9 + c_ * 1.15, y + .45, 1.1, .35, f'ZT{z}' + (' ☾' if z > 12 else ''), 12, MUTED, True, align=PP_ALIGN.CENTER)
    for r_, reg in enumerate(['SCN', 'Hb']):
        text(s, x, y + .9 + r_ * .7, .85, .4, reg, 14, INK, True)
        for c_ in range(4):
            v = g[r_][c_]; rgba = cmap(.08 + .92 * v / vmax) if v else (0.97, 0.98, 0.98, 1)
            hexc = '%02X%02X%02X' % tuple(int(t * 255) for t in rgba[:3])
            box(s, x + .9 + c_ * 1.15, y + .8 + r_ * .7, 1.08, .62, hexc, LINE, radius=.08)
            text(s, x + .9 + c_ * 1.15, y + .81 + r_ * .7, 1.08, .6, f'{v:,}', 19, 'FFFFFF' if v > vmax * .6 else INK, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
mini_grid(.6, 1.65, 'Resilient vs control', RC)
mini_grid(.6, 4.0, 'Susceptible vs control', SC)
text(s, .6, 6.45, 5.6, .5, 'Numbers = changed genes (adjusted p < .05, change > 1.4×). Same colour scale.', 11, MUTED, italic=True)
text(s, 6.6, 1.75, 6.1, 3.2, [f'**1 · Time matters.** {NIGHT_R:,} of {TOTAL_R:,} changes ({NIGHT_R / TOTAL_R:.0%}) appear at **ZT16**, early night, when mice are active, in **both** regions.',
     f'**2 · Resilience leaves the bigger trace.** Susceptible mice show only {TOTAL_S} changed genes across all eight boxes.',
     '**3 · It agrees with the original paper**, now visible to anyone in a few clicks.'], 17, INK, space=14)
box(s, 6.6, 5.15, 6.1, 1.6, 'FFF8E6', 'F0D58C')
text(s, 6.8, 5.25, 5.7, 1.4, '**Honest limits:** 3–5 mice per group, males only, one study, bulk tissue. A difference at one time but not another is not formal proof of a time effect.', 14, INK, anchor=MSO_ANCHOR.MIDDLE)

# 15 Thanks
s = new_slide('Thank you', None, None, dark=True)
text(s, .6, 1.2, 12, 1.2, 'Explore it. Question it.', 46, 'FFFFFF', font=TITLE_FONT)
text(s, .6, 2.6, 12, .7, URL, 30, '7FD1C9', True)
text(s, .6, 3.35, 12, .5, f'Code: {REPO}', 16, 'D6E4EC')
roles = [('Yixuan Du', 'Experiment and research question · demo operator', TEAL), ('Jinyu Zheng', 'RNA-seq and GO analysis', BLUE), ('Yi Yao', 'Visualization design, interaction and requirements', CORAL)]
for j, (n_, r_, c_) in enumerate(roles):
    x = .6 + j * 4.1
    box(s, x, 4.4, 3.8, 1.3, '1D3A52', None)
    box(s, x, 4.4, .1, 1.3, c_, None, MSO_SHAPE.RECTANGLE)
    text(s, x + .3, 4.5, 3.4, .45, n_, 18, 'FFFFFF', True)
    text(s, x + .3, 4.95, 3.4, .7, r_, 13, 'B8CAD6')
text(s, .6, 6.1, 12, .6, 'Questions welcome. Data: Narain et al. (2024), CC BY 4.0 · Built with D3.js v7 · AI assistance disclosed in AI_USAGE.md', 13, '9FB3C2')

assert len(prs.slides) == len(SCRIPT), (len(prs.slides), len(SCRIPT))
TITLES = ['Title', 'Same stress, different outcomes', 'Four steps, from stress to data', 'Where and when they looked', 'Our research question',
          'Counting gene “messages” (RNA-seq)', 'Is a gene really different?', 'What do the changed genes do? (GO)', 'Who it is for, and what they can do',
          'Four views, one shared state', 'Designed for non-experts', 'Live demo', 'From raw counts to a static website', 'So, what did we find?', 'Thank you / Q&A']

# ---------- speaker notes ----------
def note_text(i):
    spk, t, items = SCRIPT[i]
    out = [f'SPEAKER: {spk} · target {t}', '']
    for kind, line in items: out.append(('▶ OPERATOR (Yixuan): ' if kind == 'do' else '') + line); out.append('')
    return '\n'.join(out).strip()
for i, slide in enumerate(prs.slides): slide.notes_slide.notes_text_frame.text = note_text(i)
pptx_path = D / 'Presentation.pptx'; prs.save(pptx_path)

# ---------- script documents ----------
def secs(t): m, s_ = t.split(':'); return int(m) * 60 + int(s_)
total = sum(secs(t) for _, t, _ in SCRIPT)
by = {}
for spk, t, _ in SCRIPT: by[spk] = by.get(spk, 0) + secs(t)
mmss = lambda v: f'{v // 60}:{v % 60:02}'
QA = [('Jinyu', 'Did you reproduce the paper exactly?', 'No. We re-ran a standard pipeline (DESeq2) with our own documented settings, so exact numbers differ, but the main pattern (night-time, resilient mice) agrees. All settings are on the Methods page.'),
      ('Jinyu', 'What does “adjusted” mean in adjusted p-value?', 'Testing ~16,000 genes at once produces some false hits by luck. The Benjamini–Hochberg adjustment controls the expected share of false hits, so a cutoff of 0.05 keeps that share around 5%.'),
      ('Jinyu', 'What happens to genes with missing statistics?', 'They are never treated as zero. They are left off the volcano plot’s vertical axis, counted in a note, and remain searchable with their activity shown in View 3.'),
      ('Yixuan', 'Why might night-time matter?', 'Mice are active at night, and the SCN is the clock. The paper suggests resilient mice adjust gene activity specifically in the active phase. We only show the pattern; we do not prove the mechanism.'),
      ('Yi Yao', 'Why a volcano plot and not a ranked bar chart?', 'A volcano shows both questions (how big and how sure) for all ~16,000 genes at once. A bar chart would show only one of them for a few genes.'),
      ('Yi Yao', 'Why not a force-directed network?', 'We tried it. It kept moving and labels overlapped. A fixed two-column (bipartite) layout is stable, so clicks always land in the same place, and it shows exactly what an edge means: membership.'),
      ('Yi Yao', 'How does the site stay fast?', 'All statistics are precomputed. The first load is about 3.7 MB; gene activity is split into 256-gene chunks that load only when a gene is selected.'),
      ('Yi Yao', 'Which parts were AI-assisted?', 'Codex drafted the pipeline and D3 code; Claude revised the wording for non-experts and drafted these slides. We reviewed, tested and can explain each part; AI_USAGE.md lists the details.'),
      ('Jinyu', 'Were there data problems?', 'Yes. One mouse (A15_A) had its two brain regions swapped in the file names; we proved the swap by matching every gene’s values and fixed it once. We also followed the authors’ three documented sample exclusions.')]
md = ['# Stress Atlas: final presentation script', '',
      f'**Length:** about {mmss(total)} (target 8–10 min) · **Speakers:** Yixuan Du ({mmss(by["Yixuan"] + by["All"])}), Jinyu Zheng ({mmss(by["Jinyu"])}), Yi Yao ({mmss(by["Yi Yao"])})  ',
      f'**Slides:** `docs/Presentation.pptx` (speaker notes contain the same script) · **Website:** {URL}', '',
      '**Who does what:** Yixuan introduces the experiment and the research question, then answers it at the end. Jinyu explains RNA-seq and GO analysis. Yi Yao explains the visualization, narrates the live demo and covers the course requirements. **Yixuan operates the slides and the website throughout.** Lines marked ▶ are operator actions for Yixuan, not words to say.', '',
      '## Before the talk (Yixuan)', '',
      f'1. Open {URL} in a browser tab. Press **Reset all**, scroll to the very top, and set browser zoom to 90% so View 1 and View 2 fit side by side.',
      '2. Open `Presentation.pptx` and start Slide Show (F5). Check that Alt+Tab switches between the slides and the browser.',
      '3. Backup: if the network fails, double-click `start_explorer.cmd` (needs Python) and use http://localhost:8000. If that fails too, slides 7 and 10 contain screenshots of every view.',
      '4. Practise the demo path (slide 12) once. Hovering and dropdown changes are the steps people forget.', '']
for i, (spk, t, items) in enumerate(SCRIPT):
    md += [f'## Slide {i + 1} · {TITLES[i]}', f'*Speaker: **{spk}** · about {t}*', '']
    for kind, line in items: md += [f'> ▶ **Operator (Yixuan):** {line}' if kind == 'do' else line, '']
md += ['## Likely questions (who answers)', '']
for who, q, a in QA: md += [f'**Q: {q}** ({who})  ', f'A: {a}', '']
(D / 'Presentation_Script.md').write_text('\n'.join(md), encoding='utf-8')

doc = Document(); st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = DPt(11)
def para_md(p, line):
    for k2, part in enumerate(re.split(r'\*\*', line)):
        if part: r = p.add_run(part.replace('`', '')); r.bold = k2 % 2 == 1
doc.add_heading('Stress Atlas: final presentation script', 0)
for line in md[2:]:
    if line.startswith('## '): doc.add_heading(line[3:], 1)
    elif line.startswith('> ▶'):
        p = doc.add_paragraph(); r = p.add_run('▶ OPERATOR (Yixuan): ' + line.split(':**', 1)[1].strip()); r.italic = True; r.font.color.rgb = DRGB(0x00, 0x7F, 0x79)
    elif line.startswith('*Speaker'):
        p = doc.add_paragraph(); r = p.add_run(line.strip('*').replace('**', '')); r.bold = True; r.font.color.rgb = DRGB(0xC2, 0x55, 0x32)
    elif line.strip(): para_md(doc.add_paragraph(), line.rstrip())
doc.save(D / 'Presentation_Script.docx')

# ---------- PDF export through PowerPoint (Windows); keeps the PDF identical to the PPTX ----------
pdf_path = D / 'Presentation.pdf'
ps = f"$p=New-Object -ComObject PowerPoint.Application; $d=$p.Presentations.Open('{pptx_path}',$true,$false,$false); $d.SaveAs('{pdf_path}',32); $d.Close(); $p.Quit()"
try:
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], check=True, timeout=180)
    print('PDF exported via PowerPoint.')
except Exception as e:
    print('PDF export skipped (PowerPoint unavailable):', e, file=sys.stderr)
print(f'Slides: {len(prs.slides)} · script ≈ {mmss(total)} · Yixuan {mmss(by["Yixuan"] + by["All"])}, Jinyu {mmss(by["Jinyu"])}, Yi Yao {mmss(by["Yi Yao"])}')
