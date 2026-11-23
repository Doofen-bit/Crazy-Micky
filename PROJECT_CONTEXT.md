# Project context as of 2026-11-23

## Current state after local implementation

The original handoff below is historical. This session inspected the actual Windows classroom files, resolved label mapping with content-level evidence, executed 24 DESeq2 comparisons and GO overrepresentation, built the four-view D3 site, and generated report/proposal/slides plus an Rmd/HTML workbench. See README.md, DECISIONS.md and audit/ for current details. User supplied the empty public Crazy-Micky repository for GitHub Pages. Actual deployment status is recorded in audit/deployment.json. Team scientific/writing review is pending; no instructor meeting or user study is claimed as completed.

## Historical context supplied in handoff

## Goals and constraints
Team: Yixuan Du (yd2927), Yi Yao (yy5075, CS), Jinyu Zheng (jz6539, GB).
User wants broad coverage: both SCN and Hb, ZT4/10/16/22, control/resilient/susceptible. This supersedes earlier SCN-ZT16-only scope.
Team formation reported to Gu; proposal meeting booked for 2026-11-24. GitHub repository has NOT been created.

Information Visualization requirements: three-person team; >=4 distinct views; >=1 node-link/treemap/geomap; >=2 linked views; D3 or Vega-Lite; static public GitHub Pages; 2–3 user tasks. Proposal <=3 pages incl. sketches due Nov25; publish by Dec6; all present Dec7 or9; final report <=5 pages with reflection, code and public link due Dec11. Presentation/demo weight40%, proposal25%, instructor discussion10%.

GB requirements: start from counts or BAM (FASTQ unnecessary); use in-class DEG/annotation pipeline; interpretable plots; one downstream validation proposal; presentation25–30min Dec8 11:15, report Dec11 11:15; code workbench .Rmd AND .html. AI assistance must be explained/cited and work understood/revised by the team, not copied uncritically. Do not assume this InfoVis trio is necessarily the entire GB team.

## Dataset and actual audit
Narain et al 2024, doi:10.1038/s41398-024-03100-w; GIN doi:10.12751/g-node.jj57l9, dataset CC BY4.0.
Uploaded archive: narain_et_al-2024-translational_psychiatry-master.zip (180436879 bytes).
SHA256 edefea6fc5042d0eb377a05c32585d665fd0b9001a014901d795b48f9df75495.
Actual audit:96 raw count files;46603 rows each; identical gene order; nonnegative integer counts; no duplicate IDs;4473888 values;11159 genes zero in all96. 48 inferred complete animal-ID suffixes, each with two regions. Raw count file total97317480 bytes. See audit CSVs.
Source folder appears twice in ZIP path before 01_data_raw/03_seq/02_counts_r/. Labels are 01_data_raw/04_labelling_legend.json and 05_label_changes.xlsx.
Original filename codes L=Hb, S=SCN; digit1/2/3/4=ZT4/10/16/22; C/R/S=control/resilient/susceptible. Parse complete suffix after first hyphen as animal identifier; do not truncate underscore components. Naming-derived pairing must be verified.

## Metadata blockers and provenance
1. Correction sheet lists L2C-C01_E1→L1C-C01_E1 and S2C→S1C. Current raw names are already ZT4, but processed timeseries_scn_control.csv contains ZT10_C01-E1_1. Do not mix tables by their old header labels.
2. A15_A region swap is logged via a temporary name; cannot tell from names alone whether count CONTENT has been swapped. Trace original processing or compare reliable references/markers; do not blindly swap again.
3. Author exclusions: L1R-E05_5, S1R-E05_5, L2S-E05_1. Subtracting only these gives93 provisional samples; final QC/exclusion set not approved or determined. Check pairing and retain transparent decisions.
4. Some processed normalization/RDS/ECHO files are annex pointer stubs (63 bytes), not actual data. All96 raw counts are real data.
5. Author phenotype outputs include42 comparison tables:24 exact-ZT comparisons plus day/night/global. They are references, NOT our rerun. Example scn_zt16_resilient_vs_control.csv has35364 genes,19204 missing padj,14 missing pvalue,12 missing symbols. Preserve Ensembl keys and NA.
6. Hb source outputs use lhb; paper says Hb contains LHb and MHb markers. Use Hb display label with source mapping, not pure LHb claim.

## Proposed analysis, not yet implemented
Preserve all eligible experimental conditions. Reconcile metadata first, low-count filtering, normalization and sample QC (PCA offline). Adapt classroom R/DESeq2 for3 phenotype contrasts per region-time stratum=24. Show normalized gene expression across times using comparable normalization within region. Do not refit models in the browser. Confirm model/rank/covariates and filtering with actual classroom code. A descriptive time profile does not prove rhythmicity; significance at one time but not another is not a formal interaction test. Cross-region tests, if added, must account for animal pairing. Use public GO Biological Process annotations/enrichment with recorded version, gene universe and ID mapping; not dependent on a paid IPA account. No DESeq2/GO results have been generated in this chat.

## UI design proposal
Audience: biology undergraduates/new lab students. Tasks: compare contexts; inspect candidates and individual variability; explore functional relationships.
A overview heatmap region×ZT for selected contrast, numeric DEG/tested counts and n; B volcano; C selected gene across4times with individual dots and group means (no animal trajectories); D small bipartite gene–process network (required complex layout). Network max5terms/30genes with truncation annotation; annotation-only mode when no enriched terms, clearly labeled. Search, reset, keyboard controls, color+shape/outline labels, explicit NA/empty states. PCA not one of four core website views.
Data source and analysis version visible. Use D3, relative asset paths, static GitHub Pages. Code structure and contracts in DATA_CONTRACT.md. Start a single-contrast integration first, then expand24 while retaining the declared scope.

## Local work status
C:\Users\Doofen\Desktop\NYU\26Fall\Genomics is the user's existing class-code folder; THIS CHAT COULD NOT ACCESS IT. No local code has been inspected/edited. User plans to continue in VS Code with Codex. Handoff files transfer context, not automatic conversation synchronization. Proposal is ready for discussion; repository URL must be inserted before formal submission.

