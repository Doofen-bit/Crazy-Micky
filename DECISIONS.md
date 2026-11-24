# Decisions and open items

## Current implementation decisions — 2026-11-23

1. User scope is Information Visualization. All outputs live inside Visualization/StressRNAseqExplorer; original raw data and Genomics files remain immutable.
2. Actual classroom code was read; source-code-review.md documents exact steps and adaptations. No unclaimed in-class methods were substituted silently.
3. Apply A15_A source L→analysis S and source S→analysis L exactly once, supported by 35,364-gene proportional matching. Retain C01_E1 corrected raw ZT4. Exclude only the three author-listed samples. 93 tissues / 47 inferred animals remain; laboratory animal identities are not independently verified.
4. Eight region/time three-phenotype DESeq2 fits, 24 explicit contrasts. Any group median raw count >=10 filtering. Region-wide median-ratio normalization shared with profiles. No cross-region inference, no formal interaction or rhythmicity claim. Three-group dispersions and normalization scope are explicit classroom adaptations.
5. Fixed DESeq2 independent filtering alpha=.05; default exploration .05/.5; unshrunken log2FC. Slider/select changes only reclassify stored statistics. NA stays null.
6. org.Mm.eg.db 3.23.0 / GO.db 3.23.1 GOALL BP annotation; Python/SciPy hypergeometric/BH. Background = BP-mapped genes with finite padj; terms 10–500 background genes; correction over all eligible terms, including zero-overlap terms. Fixed .05/.5 foreground. Annotation-only fallback when enrichment is absent. No GSEA is claimed for this InfoVis scope.
7. D3 7.9.0, Canvas volcano, SVG overview/profile/bipartite network, relative static assets, cached 256-gene expression chunks. Core state and every render are in app.js, deliberately buildless. All eligible genes have accessible expression; filtered genes need not be drawn in the volcano.
8. User provided https://github.com/Doofen-bit/Crazy-Micky.git; repository was empty and public. Use main + GitHub Actions Pages deployment. Exact publication evidence belongs in audit/deployment.json; configuration alone is not proof of deployment.
9. Proposal/report/PPTX/PDF, scientific checks and browser acceptance tests are generated from real outputs. Human review, personal reflection, instructor discussion, final presentation and Gradescope submission remain team responsibilities.
10. Audience re-targeted from biology students to a general audience (2026-11-23). Added a plain-language layer (experiment primer, hover glossary, worded axes and tooltips, day/night bands, GO process names instead of IDs, three-step guided story). Views, linking, statistics and data are unchanged. Final presentation: 15 slides, ~9:45; Du = experiment and question (and operates slides/site), Zheng = RNA-seq and GO, Yao = visualization, demo narration and requirements.
11. Instructor discussion held 2026-11-24. Feedback implemented: (1) detailed primer scenes for the defeat procedure and the social-interaction test; (2) translucent 3D mouse-brain locator in View 1 (schematic point cloud, positions approximate after the Allen Mouse Brain Atlas; clicking a region selects it); (3) sideways volcano with up-regulated genes on top (red) and down-regulated at the bottom (blue); (4) View 3 uses linear normalized counts on a y-axis zoomed to the data, with an explicit break mark and caption; (5) View 4 colours genes and edges red/blue by direction and sets edge width from GO evidence: direct experimental (EXP/IDA/IPI/IMP/IGI/IEP/HTP family), direct inferred (all other codes), indirect (GOALL ancestor only). Evidence comes from org.Mm.eg.db via analysis/export_go_evidence.R; enrichment statistics are unchanged; (6) closing takeaway with three facts computed from exported results. Susceptible colour changed to purple to keep red reserved for up-regulation. Proposal, report and slides updated.

## Historical handoff decisions (retained for traceability)

## Established by user
- Three-person InfoVis team: Du yd2927, Yao yy5075(CS), Zheng jz6539(GB).
- Use Narain/Chaudhury2024 public bulk RNA-seq, not the later sleep-deprivation capstone dataset.
- Expand beyond SCN ZT16 to both regions, all four times and all three groups, with legitimate QC.
- Team registered; meeting with Gu booked for Nov24; no GitHub repo yet.
- Continue local implementation in VS Code; class code in C:\Users\Doofen\Desktop\NYU\26Fall\Genomics.

## Proposed for meeting, not final instructor approval
- Four linked core views: context overview, volcano, temporal gene profile, GO gene-process network.
- Full eligible data offline; compact/on-demand browser exports.
- D3 static website on GitHub Pages; shared state and module ownership as in proposal.
- 24 phenotype comparisons as core; extra timepoint contrasts and behavior optional.

## Must resolve next
- Read actual class code, existing results and installed R packages; map in-class workflow.
- Resolve C01_E1 header conflict; audit A15_A swap provenance; review3author exclusions and independent QC.
- Fix analysis manifest, contrast direction, normalization scope, low-count rules, annotation source/version and statistical model.
- Create GitHub repo and insert exact URL into proposal before Nov25 submission.
- Discuss cross-course reuse and four-view scope with Gu; record any requested changes.
- Course policies require understandable, reviewed, cited AI-assisted work. All team members review submitted documents; the current proposal is a discussion draft.

## Completed here
Read both course instructions; inspected uploaded ZIP; generated reproducible structural audit; wrote bilingual team brief, annotated wireframe, three-page discussion proposal and explicit Codex handoff. No biological DE/GO model has been fit. No Windows folder was read. No external messages sent. No repo/deployment created.


## Publication verified

GitHub Actions run 45137296767 succeeded for 3d577c3a5fb1a883ef60601d5f478dcfa9bff01e. Public site returned HTTP 200 and was tested in an unsigned-in Chromium session: 8 overview cells, Kcnk2 selection, 47 SCN expression points and GO:0042391 cross-highlighting, with no JavaScript errors. Evidence: audit/deployment.json and audit/public_browser_validation.json.
