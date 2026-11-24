# Stress Atlas: Stress, across time

**Why do some stressed mice bounce back?** Stress Atlas is an interactive D3 visualization that lets anyone, with no biology background needed, explore a real public brain experiment. It shows which genes change in mice after chronic social stress, in which brain region, and at what time of day.

- **Live site (GitHub Pages):** https://doofen-bit.github.io/Crazy-Micky/
- **Team:** Yixuan Du (yd2927) · Jinyu Zheng (jz6539) · Yi Yao (yy5075). NYU Shanghai, Information Visualization, Fall 2026
- **Data:** [Narain et al. 2024, *Translational Psychiatry*](https://doi.org/10.1038/s41398-024-03100-w). Raw data on [GIN](https://doi.gin.g-node.org/10.12751/g-node.jj57l9/), CC BY 4.0.

## The experiment in 30 seconds

1. **Stress.** For 15 days, each test mouse met a larger, aggressive mouse every day. Control mice were never stressed.
2. **Sort.** A social test split the stressed mice: *resilient* mice still approached a new mouse; *susceptible* mice avoided it.
3. **Sample.** Brain tissue was collected at four times of day (ZT4 and ZT10 with lights on, ZT16 and ZT22 with lights off). It came from two regions: the **SCN**, the master clock, and the **habenula (Hb)**, which reacts to bad experiences.
4. **Measure.** RNA-seq counted how active each of ~46,000 genes was in each of 93 samples from 47 mice.

**Question:** which genes differ between the groups, and does it depend on brain region and time of day?

## The visualization

| View | Chart | Linked behaviour |
|---|---|---|
| 1 · When and where do genes change? | Region × time grid (printed counts + sequential colour) with a see-through rotating 3D mouse-brain locator for SCN and Hb | Click a box or a brain region → Views 2, 3, 4 update |
| 2 · Which genes changed, and how much? | Sideways volcano (Canvas, ~16k genes): up-regulated on top (red), down at the bottom (blue), more confident to the right | Click a gene → Views 3, 4 update |
| 3 · One gene, through the day | Every mouse at 4 times; linear normalized counts on a zoomed axis with a break mark; shape + colour per group; mean lines | Gene stays selected when the context changes |
| 4 · What do the genes do? | **Node-link** bipartite diagram: red/blue genes ↔ Gene Ontology processes; edge width = annotation evidence (experimental / inferred / indirect) | Click a process → its genes are outlined in View 2 |

Plain-language layer: a detailed illustrated experiment primer (defeat and divider, social-interaction arena, sampling, sequencing), a hover glossary, worded axes and tooltips, day/night shading, a three-step guided story ("Follow the story") and a closing takeaway. The page runs from simple to detailed. Several of these changes came from the instructor discussion on 24 Nov 2026 (see `DECISIONS.md`). Colour is never the only cue: we use printed numbers, shapes (● ▲ ■), line styles and outlines.

## Run locally

The site is static (HTML/CSS/JS, D3 bundled in `site/vendor/`), with no backend and no CDN.

```powershell
python -m http.server 8000 --bind 127.0.0.1 --directory site
```

Then open http://localhost:8000. On Windows you can also double-click `start_explorer.cmd`. Do not open `site/index.html` directly: browsers block JSON loading from `file://`.

## Deliverables (`docs/`)

| File | Purpose |
|---|---|
| `Proposal_Updated.pdf` / `_Editable.docx` | Proposal, sections 4.1–4.7 (3 pages) |
| `Final_Report.pdf` / `_Editable.docx` | Final report with changes and reflection (5 pages) |
| `Presentation.pptx` / `.pdf` | 15-slide final presentation; speaker notes contain the script |
| `Presentation_Script.md` / `.docx` | Word-for-word English script for three speakers, with operator cues and Q&A prep |
| `Professor_Brief.pdf` / `.docx` | One-page project introduction for the instructor (no biology assumed) |
| `Professor_Meeting_Pitch.md` | 2-minute spoken pitch, questions to ask, likely questions |
| `dashboard-*.png`, `view-*.png`, `figures/` | Screenshots and figures generated from the real site and results |
| `source-code-review.md` | Mapping to the classroom RNA-seq code |

## Pipeline and reproduction

```
96 raw count files ──► prepare_inputs.py / verify_label_provenance.py   (audit, label fixes)
                   ──► analysis/run_analysis.R                          (DESeq2: 8 models, 24 comparisons)
                   ──► export_site.py                                    (GO enrichment, chunked JSON for the browser)
                   ──► site/ (index.html + app.js + styles.css, D3 v7)   (all four views share one state object)
                   ──► .github/workflows/pages.yml                       (GitHub Actions → GitHub Pages)
```

```powershell
python -m pip install -r requirements.txt
Rscript scripts/setup.R
python scripts/verify_label_provenance.py
python scripts/prepare_inputs.py
Rscript analysis/run_analysis.R
python scripts/export_site.py
Rscript analysis/export_go_evidence.R      # direct GO evidence codes for network genes
python scripts/add_edge_strength.py         # edge width levels for View 4 (enrichment unchanged)
python scripts/validate_results.py          # scientific invariants
```

The raw dataset is expected next to this folder at `../narain_et_al-2024-translational_psychiatry/…`; large intermediates are not committed. Tested with Python 3.14, R 4.6.1 / Bioconductor 3.23 (`results/session_info.txt`).

Tests and documents need the local server running on port 8000:

```powershell
python -m playwright install chromium
python scripts/browser_qa.py                # all 24 contexts, linked interactions, empty states, 1440/1366/390 px
python scripts/build_deliverables.py        # report + proposal
python scripts/capture_slide_images.py      # screenshots for slides
python scripts/build_presentation.py        # slides (PPTX; PDF via PowerPoint on Windows) + script
python scripts/build_professor_brief.py     # one-page brief
```

## Analysis summary

- 96 raw files → 93 samples / 47 mice after the authors' three documented exclusions (L1R-E05_5, S1R-E05_5, L2S-E05_1). Mouse A15_A's two brain regions were swapped in the file names. We proved the swap by matching every gene's values and fixed it exactly once. C01_E1 keeps its corrected ZT4 label.
- DESeq2 `~ phenotype` within each region × time (8 models, 24 comparisons). Size factors are estimated per region. Genes are kept if any group's median raw count is ≥ 10. Default "changed gene": adjusted p < .05 and |log₂ fold change| > .5. Browser cutoffs only re-sort stored results; nothing is refitted in the browser.
- GO Biological Process from `org.Mm.eg.db` 3.23.0 / `GO.db` 3.23.1. Hypergeometric test with Benjamini–Hochberg correction. Background = annotated genes with a finite adjusted p. Missing statistics are kept as missing (never zero).
- Limits: 3–5 male mice per group and one study. Significance at one time but not another is not a formal time effect, and network edges mean membership, not causation.

## Credits and AI use

D3.js 7.9.0 (ISC, licence in `site/vendor/D3-LICENSE.txt`); DESeq2 (Love, Huber & Anders 2014); Bioconductor mouse annotations; data CC BY 4.0. No third-party templates or article figures were used. AI assistance: OpenAI Codex (pipeline, D3 implementation, tests, report drafts) and Anthropic Claude (plain-language revision, slides, script, brief). Details and checks are in [`AI_USAGE.md`](AI_USAGE.md); decisions are in [`DECISIONS.md`](DECISIONS.md).
