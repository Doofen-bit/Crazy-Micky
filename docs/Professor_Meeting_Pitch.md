# Instructor meeting (Nov 24): 2-minute pitch and prep

Bring: `Professor_Brief.pdf` (one page, printed or on screen) and a laptop with https://doofen-bit.github.io/Crazy-Micky/ open, scrolled to the top.

## The pitch (about 2 minutes, ~280 words)

> Our project is called **Stress Atlas**. It's an interactive D3 website that lets people with **no biology background** explore a real, public brain experiment.
>
> **The experiment (30 seconds).** Researchers stressed mice for 15 days by putting them with a bigger, aggressive mouse every day. Afterwards some mice stayed social. They're called *resilient*. Others started avoiding other mice; they're *susceptible*. A third group was never stressed. The researchers then measured how active about 46,000 genes were in two brain regions: the brain's master clock, and a region that reacts to bad experiences. They took samples at four times of day.
>
> **The data.** That gives 93 samples from 47 mice. Before anything reaches the browser, we run a standard statistics package that compares the groups gene by gene. That produces 24 comparisons: two regions, times four times of day, times three pairs of groups. Each gene gets two numbers: how big the change is, and how confident we are.
>
> **The visualization.** We have four linked views. An overview grid shows where and when genes change. A volcano plot shows every gene in one comparison. A profile shows one gene in every individual mouse across the day. And a node-link diagram connects genes to the biological processes they share. Clicking a box, a gene or a process updates the other views.
>
> **For non-experts**, we added an illustrated 30-second primer, a hover glossary and a three-step guided story. A reader can discover the main pattern themselves: almost all the changes happen early in the night, and mostly in resilient mice.
>
> It's already deployed on GitHub Pages. We'd love your feedback on a few design questions.

**Then show (30 seconds, optional):** click the story buttons **1 → 2 → 3** at the top of the explorer.

## Questions to ask (also printed on the brief)

1. Is the four-view scope right, or should we merge or cut a view to strengthen the story?
2. Is the plain-language layer enough for a general audience, or would a scrolling narrative before the dashboard be better?
3. Is the bipartite gene–process node-link diagram acceptable as the required "complex layout"?
4. Since a working prototype exists, may the proposal use real screenshots alongside the sketches?
5. The same public dataset is used in one member's Genomics course, and the InfoVis work is the visualization. Is that acceptable?

Write the answers down; they go into the proposal (due Nov 25) and into `DECISIONS.md`.

## Questions the professor may ask

| Question | Short answer |
|---|---|
| Who is the audience, concretely? | Classmates and curious readers with no biology training. A secondary audience is new lab members. |
| Why is a volcano plot right for non-experts? | It answers both "how big?" and "how sure?" for all ~16,000 genes in one picture. We label the axes in words ("less active / more active", "more confident ↑") and explain it in the glossary. |
| What exactly is linked? | Box click → volcano, profile and network update. Gene click → profile and network. Process click → its genes are outlined in the volcano. A selected gene stays selected when you change box. |
| Why not a force-directed network? | It kept moving and labels overlapped. A fixed two-column layout is stable, readable, and makes clear that an edge only means "belongs to this process". |
| How do you avoid relying on colour? | Every box prints its number. Groups use shapes (● ▲ ■) and line styles. Selection uses outlines and labels. Day and night are shaded bands with text labels. |
| How big is the data in the browser? | All statistics are precomputed. The first load is ≈3.7 MB, and per-gene data loads in 256-gene chunks on demand. |
| What data cleaning did you do? | We applied the authors' 3 documented exclusions. One mouse's two brain regions were swapped in its file names; we proved this by matching all genes' values and fixed it once. Missing statistics stay missing (never zero). |
| What did AI do? | Codex drafted the pipeline and D3 code. Claude revised the site for non-experts and drafted slides. We review, test and can explain every part; see `AI_USAGE.md`. |
| Can a reader draw wrong conclusions? | We state the limits on the page: 3–5 mice per group, males only, one study. Significance at one time but not another is not proof of a time effect, and network edges are not causal. |
