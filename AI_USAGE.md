# AI assistance record

## Instructor-feedback revision — 2026-11-24 (Anthropic Claude, Claude Code)

User relayed six feedback items from the Nov 24 instructor meeting. Claude implemented them in `site/index.html`, `site/app.js` and `site/styles.css`. It also added `analysis/export_go_evidence.R` and `scripts/add_edge_strength.py` (edge-strength levels written into `site/data/networks/*.json`), extended `scripts/browser_qa.py`, and updated the proposal, report, slides, script and README.
Checks: `validate_results.py` PASS; `browser_qa.py` PASS, including the brain-locator click, sideways volcano, zoomed linear axis, ≥2 edge widths, takeaway facts, 1440/1366/390 px, and no console/HTTP errors. Proposal 3 pages; report 5 pages.
Limits: the 3D brain is a schematic point cloud with approximate positions, not an atlas mesh. Evidence codes describe annotation provenance, not biological effect size. Team review pending.

## Plain-language revision, slides and script — 2026-11-23 (Anthropic Claude, Claude Code)

User (Yixuan Du) asked Claude to review the Codex-built project against the course guideline, make it understandable for a general audience, redo the final-presentation slides and three-person speaker script, prepare a one-page brief for the instructor meeting, test the program and push to GitHub.

Component/files: `site/index.html`, `site/app.js`, `site/styles.css`, `site/methods.html` (plain-language layer: experiment primer, hover glossary, worded titles/axes/tooltips, day/night shading, readable GO process names, three-step guided story, example-gene shortcut, narrow-screen label variants); `scripts/browser_qa.py` (new checks for glossary, story and example shortcut); `scripts/build_deliverables.py` (audience and design text, slide code moved out); new `scripts/capture_slide_images.py`, `scripts/build_presentation.py`, `scripts/build_professor_brief.py`; `docs/Presentation.pptx/.pdf`, `docs/Presentation_Script.md/.docx`, `docs/Professor_Brief.pdf/.docx`, `docs/Professor_Meeting_Pitch.md`; English `README.md`.
Not changed: raw data, R/Python statistics, exported results, or any analysis decision. All numbers on slides and in the brief are read from `results/` at build time.
Checks performed: `python scripts/validate_results.py` (PASS); `python scripts/browser_qa.py` (PASS: 24 contexts, linked transitions, edge states, glossary/story, 1440/1366/390 px, no console or HTTP errors); page limits (report 5, proposal 3, brief 1); visual review of every slide.
Team reviewer: pending. Each speaker should rehearse and rewrite their part of the script in their own words.
Remaining limitations: no human user study; experiment descriptions are simplified for lay readers and should be checked by Jinyu (GB background).
Source: Anthropic Claude, https://claude.ai/.

## Implementation completed 2026-11-23 (current record)

User requested completion of the Information Visualization project from the supplied handoff, raw dataset and actual Genomics classroom code, then supplied the public repository https://github.com/Doofen-bit/Crazy-Micky.git for publication.

Codex inspected the local class notebook and data, delegated a bounded read-only metadata/classroom evidence review, implemented and executed the input audit, eight DESeq2 models / 24 contrasts, real mouse GO annotation and Python hypergeometric/BH enrichment, static D3 website, tests, Rmd/HTML workbench, proposal/report and presentation drafts. A15_A correction is supported by all-gene content reconstruction, not a guessed swap. All raw and classroom files remain unchanged.

Actual validation: source/analysis/animal identities, exclusion list, rank and reverse contrasts; full normalized-value reconstruction; all export values/nulls; independently checked hypergeometric/BH; all 24 browser contexts, linked actions, search, clear/reset/download, no-selection, zero-DEG, filtered-gene and no-GO test states; responsive screenshots. See audit/. Public deployment evidence is in audit/deployment.json once confirmed.

No team member is recorded as having personally reviewed this implementation yet. No instructor discussion, user study, presentation or submission is claimed. Team assignments in documents are proposed review ownership. Reflection is explicitly an implementation draft to be revised in the team's own voice. The team remains responsible for scientific choices, explanations, authorship and any submission; this record does not certify understanding.

Sources: OpenAI ChatGPT/Codex https://chatgpt.com/; D3 https://d3js.org/; DESeq2 https://bioconductor.org/packages/DESeq2/; mouse annotation https://bioconductor.org/packages/org.Mm.eg.db/; source data and article below. Sites skill was used for static-site development/QA guidance; final hosting follows the course-required GitHub Pages platform, not Sites hosting.

## Historical preparation record (superseded status below)

## Preparation 2026-11-23
Assistant helped read provided course guidelines, inspect the uploaded ZIP and metadata, draft a read-only structural audit script, produce a schematic wireframe/implementation diagram, and write bilingual team background and an English discussion proposal. This is preliminary planning, not new biological results.

Team review still required: resolve source labeling/exclusions, read actual local classroom code, choose/justify models and preprocessing, verify scientific interpretation, revise writing in team voice, and insert repository URL. Do not represent the draft as independently authored or final instructor-approved work.

## Per-task log template
Date:
Component/files:
Prompt and assistance summary:
Suggested change accepted/revised/rejected:
Team reviewer:
Data/code checks performed:
Remaining limitations:

## Planned responsibilities
- Audit/R/export drafts: AI may help parsing and repetitive code; Du/Zheng verify metadata, inputs, contrasts, IDs and outputs and understand the Rmd.
- D3/state/UI: AI may help render/event-handler drafts; Yao and team choose semantics, test transitions and inspect actual values.
- Writing: AI may suggest structure/wording; team revises and takes responsibility for claims.
- Keep library/source links, versions and externally reused code credits in repository documentation.

Sources: ChatGPT/Codex https://chatgpt.com/ ; dataset https://doi.gin.g-node.org/10.12751/g-node.jj57l9/ ; manuscript https://doi.org/10.1038/s41398-024-03100-w .

