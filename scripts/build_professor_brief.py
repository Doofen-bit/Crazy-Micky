"""One-page project brief for the instructor meeting (no biology background assumed).
Outputs docs/Professor_Brief.pdf (exactly one page) and docs/Professor_Brief.docx (editable)."""
from pathlib import Path
import json
import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from docx import Document
from docx.shared import Pt, Inches

ROOT = Path(__file__).resolve().parents[1]; D = ROOT / 'docs'
URL, REPO = 'https://doofen-bit.github.io/Crazy-Micky/', 'https://github.com/Doofen-bit/Crazy-Micky'
ov = pd.read_csv(ROOT / 'results/overview.csv'); ov['n'] = ov.up + ov.down
rc = ov[ov.contrast == 'resilient_vs_control']
night = int(rc[rc.zt == 16].n.sum()); total = int(rc.n.sum())

INK, TEAL, MUTED = colors.HexColor('#142c40'), colors.HexColor('#007f79'), colors.HexColor('#536b7c')
body = ParagraphStyle('b', fontName='Helvetica', fontSize=8.9, leading=11.2, textColor=INK, spaceAfter=3)
small = ParagraphStyle('s', parent=body, fontSize=7.9, leading=10, textColor=MUTED)
head = ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=10, leading=12.5, textColor=TEAL, spaceBefore=5, spaceAfter=2)
title = ParagraphStyle('t', fontName='Times-Roman', fontSize=22, leading=25, textColor=INK)

S = [  # (heading, paragraphs) — shared by PDF and DOCX
 ('In one sentence', [f'An interactive D3 website that lets people <b>with no biology background</b> explore a real, public brain experiment: which genes change in mice after social stress, <b>in which brain region</b>, and <b>at what time of day</b>.']),
 ('The experiment, without jargon', ['Mice were stressed for 15 days by daily encounters with a larger, aggressive mouse. A social test then split them into <b>resilient</b> (still sociable) and <b>susceptible</b> (avoidant); <b>control</b> mice were never stressed. Brain tissue from two regions, the <b>SCN</b> (the body’s master clock) and the <b>habenula</b> (reacts to bad experiences, linked to depression), was collected at <b>four times of day</b>. A lab technique (RNA-seq) measured how active each of ~46,000 genes was in each sample. Source: Narain et al. (2024), <i>Translational Psychiatry</i>; open data, CC BY 4.0.']),
 ('Data and preparation (offline, before the browser)', ['Raw: 96 count files × 46,603 genes (one integer “activity” count per gene per sample). After the authors’ documented exclusions: <b>93 samples from 47 mice</b>, 3–5 mice per group. A standard statistics package (DESeq2) compares groups gene by gene in each region × time: <b>24 comparisons</b>, each giving per gene a <i>change size</i> (log2 fold change) and a <i>confidence</i> (adjusted p-value). Public “Gene Ontology” tags then group genes into biological processes. The site loads only these prepared JSON files (first load ≈3.7 MB; per-gene data in on-demand chunks). <b>Limitations:</b> small groups, males only, one study; missing statistics are kept as missing, never zero.']),
]
TASKS = [['Task (audience words)', 'Vis task', 'View'],
         ['Where and when do genes change?', 'Compare groups, locate hot spots', '1 · Overview grid'],
         ['How does one gene behave in every mouse?', 'Distribution, outliers', '2 · Volcano → 3 · Profile'],
         ['What do the changed genes do together?', 'Explore relationships', '4 · Network → 2']]
VIEWS = [['View', 'Chart / encoding', 'Linked behaviour'],
         ['1 Overview', 'Region × time grid; printed counts + sequential colour', 'Click a box → Views 2, 3, 4 update'],
         ['2 Volcano', 'Scatter of ~16k genes: change size (x) × confidence (y)', 'Click a gene → Views 3, 4 update'],
         ['3 Gene profile', 'Every mouse at 4 times; shape + colour per group; mean lines', 'Keeps the gene when the context changes'],
         ['4 Network', '<b>Node-link</b> (bipartite) diagram: genes ↔ processes', 'Click a process → its genes outlined in View 2']]
STATUS = [f'Implemented and live on GitHub Pages ({URL}); code at {REPO}. D3.js v7, static, no backend.',
          'Requirement check: 4 distinct views (3-person team) · node-link layout · linked interactions beyond tooltips · numbers/shapes so colour is never the only cue · keyboard-accessible · real cited data · libraries acknowledged.',
          'Plain-language layer for general readers: 30-second illustrated experiment primer, hover glossary, worded axes, day/night shading, a 3-step guided story.',
          f'Headline pattern a reader can find: {night:,} of {total:,} changed genes (resilient vs control) occur at ZT16, early night; susceptible mice show few changes.',
          'Automated checks: statistics re-verified; browser tests of all 24 comparisons, linked states, empty states, 390-px phone layout.']
ASK = ['Is the four-view scope right, or should we merge or cut a view to strengthen the story?',
       'Is the plain-language layer enough for a general audience, or would you prefer a scrolling narrative before the dashboard?',
       'Is the bipartite gene–process node-link diagram acceptable as our “complex layout”?',
       'Since a working prototype exists, may the proposal use real screenshots alongside the sketches?',
       'The same public dataset is used in one member’s Genomics course; the InfoVis work is the visualization. Is that acceptable?']

def table(rows, widths):
    t = Table([[Paragraph(c, small if r else ParagraphStyle('th', parent=small, fontName='Helvetica-Bold', textColor=INK)) for c in row] for r, row in enumerate(rows)], colWidths=widths, hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7f0f3')), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#dce4eb')), ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]))
    return t

flow = [Paragraph('Stress Atlas · “Stress, across time.”', title),
        Paragraph(f'Information Visualization final project · Yixuan Du (yd2927) · Jinyu Zheng (jz6539) · Yi Yao (yy5075) · NYU Shanghai, Fall 2026<br/>Live site: <link href="{URL}" color="#007f79">{URL}</link> · Code: <link href="{REPO}" color="#007f79">{REPO}</link>', small)]
for h, ps in S:
    flow.append(Paragraph(h, head)); flow += [Paragraph(p, body) for p in ps]
img_path = D / 'figures/slides/dashboard_linked.png'
iw, ih = PILImage.open(img_path).size; w = 2.05 * 72; h = w * ih / iw
right = [Paragraph('Audience and three tasks', head), table(TASKS, [138, 92, 80]), Paragraph('Four linked views', head), table(VIEWS, [55, 140, 115])]
left_img = Image(str(img_path), width=w, height=h)
grid = Table([[left_img, right]], colWidths=[w + 8, 318]); grid.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
flow += [Spacer(1, 3), grid, Paragraph('Status', head)] + [Paragraph('• ' + x, body) for x in STATUS]
flow += [Paragraph('Questions we would like your feedback on', head)] + [Paragraph(f'{i + 1}. {q}', body) for i, q in enumerate(ASK)]
pdf = D / 'Professor_Brief.pdf'
SimpleDocTemplate(str(pdf), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=26, bottomMargin=24,
                  title='Stress Atlas project brief').build(flow)

doc = Document(); st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(10)
strip = lambda t: t.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<br/>', '\n')
doc.add_heading('Stress Atlas · “Stress, across time.”', 0)
doc.add_paragraph(f'Information Visualization final project · Yixuan Du (yd2927) · Jinyu Zheng (jz6539) · Yi Yao (yy5075)\nLive site: {URL} · Code: {REPO}')
for h, ps in S:
    doc.add_heading(h, 2); [doc.add_paragraph(strip(p)) for p in ps]
doc.add_picture(str(img_path), width=Inches(3.0))
for h, rows in [('Audience and three tasks', TASKS), ('Four linked views', VIEWS)]:
    doc.add_heading(h, 2); t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Light Grid Accent 1'
    for r, row in enumerate(rows):
        for c, v in enumerate(row): t.cell(r, c).text = strip(v)
doc.add_heading('Status', 2); [doc.add_paragraph(x, style='List Bullet') for x in STATUS]
doc.add_heading('Questions we would like your feedback on', 2); [doc.add_paragraph(q, style='List Number') for q in ASK]
doc.save(D / 'Professor_Brief.docx')
print('brief written')
