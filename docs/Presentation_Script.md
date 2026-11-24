# Stress Atlas: final presentation script

**Length:** about 9:55 (target 8–10 min) · **Speakers:** Yixuan Du (3:20), Jinyu Zheng (2:25), Yi Yao (4:10)  
**Slides:** `docs/Presentation.pptx` (speaker notes contain the same script) · **Website:** https://doofen-bit.github.io/Crazy-Micky/

**Who does what:** Yixuan introduces the experiment and the research question, then answers it at the end. Jinyu explains RNA-seq and GO analysis. Yi Yao explains the visualization, narrates the live demo and covers the course requirements. **Yixuan operates the slides and the website throughout.** Lines marked ▶ are operator actions for Yixuan, not words to say.

## Before the talk (Yixuan)

1. Open https://doofen-bit.github.io/Crazy-Micky/ in a browser tab. Press **Reset all**, scroll to the very top, and set browser zoom to 90% so View 1 and View 2 fit side by side.
2. Open `Presentation.pptx` and start Slide Show (F5). Check that Alt+Tab switches between the slides and the browser.
3. Backup: if the network fails, double-click `start_explorer.cmd` (needs Python) and use http://localhost:8000. If that fails too, slides 7 and 10 contain screenshots of every view.
4. Practise the demo path (slide 12) once. Hovering and dropdown changes are the steps people forget.

## Slide 1 · Title
*Speaker: **Yixuan** · about 0:25*

> ▶ **Operator (Yixuan):** Slides open in Slide Show (F5). Browser tab with the website already open in the background, scrolled to the top, “Reset all” pressed.

Hi everyone, we are Yixuan, Jinyu and Yi Yao. Our project is called “Stress, across time”. It is an interactive website that lets anyone, with no biology background needed, explore a real brain experiment about stress. I will introduce the experiment and our question, Jinyu will explain the two lab technologies behind the data, and Yi Yao will walk you through the visualization.

## Slide 2 · Same stress, different outcomes
*Speaker: **Yixuan** · about 0:30*

> ▶ **Operator (Yixuan):** Press → (next slide).

Think about people who go through something really stressful. Some develop depression, and others stay fine. That ability to bounce back is called resilience. To study it, researchers use mice. After the same stress, some mice cope and stay social. We call them resilient. Others start avoiding other mice. They are susceptible. A third group, the control group, is never stressed. These three shapes, circle, triangle and square, appear everywhere on our website.

## Slide 3 · Four steps, from stress to data
*Speaker: **Yixuan** · about 0:30*

> ▶ **Operator (Yixuan):** Press →.

Here is the experiment, from a 2024 paper by Narain and colleagues, who shared all their data. Step one: for fifteen days, each test mouse met a bigger, aggressive mouse every day. Step two: a social test sorted them into resilient and susceptible. Step three: brain tissue was collected at four times of day. Step four: RNA-seq measured how active each of about forty-six thousand genes was. Jinyu will explain that.

## Slide 4 · Where and when they looked
*Speaker: **Yixuan** · about 0:35*

> ▶ **Operator (Yixuan):** Press →.

They looked at two brain regions. The SCN is the brain’s master clock. It keeps our daily rhythm in step with light and dark. The habenula reacts to disappointment and bad experiences, and it is over-active in depression. Mice are active at night, so samples were taken twice while the lights were on and the mice rested, and twice after lights off, when they are active. These times are called ZT4, 10, 16 and 22: hours after lights on.

## Slide 5 · Our research question
*Speaker: **Yixuan** · about 0:30*

> ▶ **Operator (Yixuan):** Press →.

So our research question is: which genes differ between resilient, susceptible and never-stressed mice, and does that depend on the brain region and the time of day? We have 93 brain samples from 47 mice, about forty-six thousand genes each, and 24 comparisons: two regions, times four times of day, times three pairs of groups. That is far too much to read in a table, which is why we built a visualization. Jinyu?

## Slide 6 · Counting gene “messages” (RNA-seq)
*Speaker: **Jinyu** · about 0:40*

> ▶ **Operator (Yixuan):** Press → when Jinyu starts.

Thanks. How do you measure what a gene is doing? Think of DNA as a cookbook. Every cell in your body has the same cookbook. What makes a brain cell different is which recipes it is actually using right now. When a cell uses a recipe, it makes photocopies of it, and those copies are called RNA. RNA-seq takes the tissue, reads millions of short pieces of those copies, and counts how many came from each gene. More copies means a more active gene. The result is a big table: one row per gene and one column per mouse.

## Slide 7 · Is a gene really different?
*Speaker: **Jinyu** · about 0:55*

> ▶ **Operator (Yixuan):** Press →.

Then we compare the groups gene by gene, using a standard tool called DESeq2. We ask two questions. First, how big is the change? That is the fold change. For example, a gene called Kcnk2 is about 2.0 times as active in resilient mice as in control mice, in the clock region at ZT16. Second, how sure are we? With four mice per group and sixteen thousand genes tested at once, some differences are just luck, so we use an adjusted p-value: smaller means more confident. For Kcnk2 it is about 3 in a million. We call a gene “changed” only if it passes both cutoffs. On our volcano plot, up-regulated genes are at the top in red, down-regulated at the bottom in blue, and further right means more confident.

## Slide 8 · What do the changed genes do? (GO)
*Speaker: **Jinyu** · about 0:50*

> ▶ **Operator (Yixuan):** Press →.

779 changed genes are still hard to read, so we ask: what do they do? The Gene Ontology is a public database that tags genes with the jobs they do, a bit like hashtags. Then we check whether any tag appears more often than chance would predict. Take “regulation of membrane potential”, which is basically how neurons control their electrical charge, or how easily they fire. By chance we would expect about 23 of our changed genes to carry this tag. We actually see 63, almost 3 times more. That is called enrichment. One caution: sharing a tag does not mean one gene controls another. Now Yi Yao will show how we turned all this into pictures.

## Slide 9 · Who it is for, and what they can do
*Speaker: **Yi Yao** · about 0:25*

> ▶ **Operator (Yixuan):** Press → when Yi Yao starts.

Thanks Jinyu. Our audience is people like you: classmates and curious readers with no biology background. We designed for three tasks. One, compare: where and when do genes change? Two, inspect: how does one gene behave in every individual mouse, not just on average? And three, explore: what do the changed genes do together?

## Slide 10 · Four views, one shared state
*Speaker: **Yi Yao** · about 0:45*

> ▶ **Operator (Yixuan):** Press →.

We answer these with four views that share one state. View 1, the overview grid, counts changed genes for each region and time, with a see-through 3D brain that shows where the two regions are. View 2 is the volcano plot for one comparison, with up-regulated genes on top. View 3 follows one gene through the day, showing every mouse. View 4 is a node-link diagram linking genes to the processes they share: our required complex layout. Red genes go up, blue go down, and thicker lines mean stronger evidence. Clicking a box, a gene or a process updates the other views. Everything is built with D3.

## Slide 11 · Designed for non-experts
*Speaker: **Yi Yao** · about 0:35*

> ▶ **Operator (Yixuan):** Press →.

Several of these choices came from our meeting with the professor. Because our audience is not biologists, we drew the experiment as detailed pictures, added a hover glossary and a three-step story, turned the volcano so that up means up, and used plain counts instead of a log scale, with a break mark where we zoom the axis. We never rely on colour alone: boxes print their numbers, and groups use shapes and line styles. And the page ends with a short takeaway to remember.

## Slide 12 · Live demo
*Speaker: **Yi Yao** · about 1:50*

> ▶ **Operator (Yixuan):** Press →, then Alt+Tab to the browser (website at the top of the page).

Let’s see it live. This is the public site on GitHub Pages.

> ▶ **Operator (Yixuan):** Scroll slowly past “The experiment in 30 seconds” down to “Follow the story”.

At the top is the thirty-second primer we just explained.

> ▶ **Operator (Yixuan):** Hover the dotted words “adjusted p” in the dark control bar and hold for two seconds.

Any dotted word shows a plain-language definition.

> ▶ **Operator (Yixuan):** Click the story button “1 When and where do genes change?”.

Step one. In View 1, look at the ZT16 column: 779 changed genes in the clock region and 225 in the habenula, and almost nothing at the other times.

> ▶ **Operator (Yixuan):** In “Which groups to compare”, choose “Susceptible vs control”. Wait one second, then switch back to “Resilient vs control”.

If we switch to susceptible mice, the night-time peak almost disappears.

> ▶ **Operator (Yixuan):** Click the story button “2 Follow one gene through the day”.

Step two picks the most confident gene, Kcnk2. View 3 shows every single mouse. At ZT16 the triangles, the resilient mice, sit above the circles, the control mice.

> ▶ **Operator (Yixuan):** Scroll up to View 1 and click the green “Hb” dot on the 3D brain (or the “Hb” button beside it).

The brain shows where the habenula is. Clicking it switches every view to the habenula, and the gene stays selected. That is the linking.

> ▶ **Operator (Yixuan):** Click the “SCN · ZT16” box, scroll up to the story buttons, then click “3 What do the changed genes do?” (the page scrolls to View 4 by itself).

Step three. In View 4, “regulation of membrane potential” is selected, and its genes are now outlined in the volcano plot.

> ▶ **Operator (Yixuan):** Scroll to the bottom of the page to show “The takeaway”.

And the page ends with three facts to remember.

> ▶ **Operator (Yixuan):** Click “Reset all”, then Alt+Tab back to the slides and press →.

## Slide 13 · From raw counts to a static website
*Speaker: **Yi Yao** · about 0:35*

Under the hood, the statistics run offline in R and Python, from the 96 raw count files. The website only loads small prepared files and draws them with D3, with no server, and GitHub Actions publishes it to GitHub Pages. Automatic tests cover all 24 comparisons, every linked click, empty states and phone screens. AI assistants, Codex and Claude, helped with code and drafts; we reviewed and tested everything and documented it. Yixuan will wrap up.

## Slide 14 · So, what did we find?
*Speaker: **Yixuan** · about 0:40*

> ▶ **Operator (Yixuan):** Press →.

So, back to our question. Yes, it depends strongly on time and on the group. Of the 1,038 genes that differ between resilient and control mice, 1,004 appear at ZT16, early in the active night, in both regions. And resilient mice, not susceptible ones, differ most from never-stressed mice: susceptible mice show only 48 changed genes in total. This agrees with the original paper. Our limits: four mice per group, males only, one study, and a difference at one time is not formal proof of a time effect.

## Slide 15 · Thank you / Q&A
*Speaker: **All** · about 0:10*

> ▶ **Operator (Yixuan):** Press →. Leave this slide up during Q&A.

(Yixuan) The website is public. Please visit the link and try the guided story yourself. Thank you! We are happy to take questions.

## Likely questions (who answers)

**Q: Did you reproduce the paper exactly?** (Jinyu)  
A: No. We re-ran a standard pipeline (DESeq2) with our own documented settings, so exact numbers differ, but the main pattern (night-time, resilient mice) agrees. All settings are on the Methods page.

**Q: What does “adjusted” mean in adjusted p-value?** (Jinyu)  
A: Testing ~16,000 genes at once produces some false hits by luck. The Benjamini–Hochberg adjustment controls the expected share of false hits, so a cutoff of 0.05 keeps that share around 5%.

**Q: What happens to genes with missing statistics?** (Jinyu)  
A: They are never treated as zero. They are left off the volcano plot’s vertical axis, counted in a note, and remain searchable with their activity shown in View 3.

**Q: Why might night-time matter?** (Yixuan)  
A: Mice are active at night, and the SCN is the clock. The paper suggests resilient mice adjust gene activity specifically in the active phase. We only show the pattern; we do not prove the mechanism.

**Q: Why a volcano plot and not a ranked bar chart?** (Yi Yao)  
A: A volcano shows both questions (how big and how sure) for all ~16,000 genes at once. A bar chart would show only one of them for a few genes.

**Q: Why not a force-directed network?** (Yi Yao)  
A: We tried it. It kept moving and labels overlapped. A fixed two-column (bipartite) layout is stable, so clicks always land in the same place, and it shows exactly what an edge means: membership.

**Q: How does the site stay fast?** (Yi Yao)  
A: All statistics are precomputed. The first load is about 3.7 MB; gene activity is split into 256-gene chunks that load only when a gene is selected.

**Q: Which parts were AI-assisted?** (Yi Yao)  
A: Codex drafted the pipeline and D3 code; Claude revised the wording for non-experts and drafted these slides. We reviewed, tested and can explain each part; AI_USAGE.md lists the details.

**Q: Were there data problems?** (Jinyu)  
A: Yes. One mouse (A15_A) had its two brain regions swapped in the file names; we proved the swap by matching every gene’s values and fixed it once. We also followed the authors’ three documented sample exclusions.
