# Data and interaction contract

## Implemented schema (v1.0.0; supersedes proposal below)

- `site/data/manifest.json`: analysis specifications, actual annotation/package versions, input ZIP SHA256, inclusion/mapping summary, source/provenance and scientific limits.
- `genes.json`: ordered `[ensembl_id, nullable_symbol, expression_chunk_number]` records. Array index is a compact browser key; Ensembl ID remains the scientific identity.
- `samples.json`: 93 ordered objects with source ID, analysis ID, full animal ID, region, zt, phenotype and size factor.
- `expression/<chunk>.json`: object from gene index to 93 full-precision normalized values, in samples.json order. Chunks contain up to 256 genes. All 46,603 genes remain accessible, even if excluded from models. The browser transforms count and arithmetic group mean as `log2(value+1)`.
- `contrasts/<context>.json`: `{columns, rows}`; fields `[i, log2FoldChange, padj, baseMean, pvalue, lfcSE]`. Missing values are null. Full offline CSVs additionally retain Wald statistic and both normalized group means.
- `overview.json`: 24 entries, finite/NA padj counts, retained genes, n per contrasted group, default up/down and summaries for alpha=.01/.05/.1 × abs LFC=0/.5/1/2. Exact direction is first-vs-second.
- `networks/<context>.json`: `mode` (enrichment/annotation), up to five terms with GO ID/name, raw/BH p, overlap/background/foreground counts, tested term count and all context member indices. Drawing selects at most 30 ranked members, prioritizes selected-term members and retains selected gene. Genes may be isolated when not members of displayed terms.
- `results/annotation_edges.csv`, `go_enrichment_all.csv`: complete offline annotation and eligible-term evidence, regenerable and omitted from Git due to size. Annotation metadata and R session are in public data/.
- Browser tests export `audit/browser_validation.json`; scientific export checks export `audit/scientific_validation.json`. No network coordinate encodes a biological quantity.

## Original proposed interface (historical)
These schemas are a design proposal. Only audit/ files exist today. Define actual normalized fields after reading classroom code; do not fabricate final exports.

## Offline outputs
1. manifest.json: dataset DOI, raw ZIP hash, analysis_version, code_commit, created_at, annotation_version, exclusions/mapping version, model/contrast specification, thresholds, group sizes, provenance(author_reference or team_reanalysis), asset paths.
2. samples.csv: sample_id_source, sample_id_analysis, animal_id, region(Hb/SCN), zt(4/10/16/22), phenotype(control/resilient/susceptible), inclusion, exclusion_reason, library_counts, normalization_factor. Corrected IDs must join one-to-one; keep original IDs.
3. genes.csv: ensembl_id(primary key), symbol(nullable), annotation_status. Symbol is a display label, never a join key.
4. overview.csv: analysis_version, region, zt, contrast, alpha, abs_lfc_cutoff, tested_genes, unavailable_padj, up, down, n_group1, n_group2. Never compare totals silently using different thresholds.
5. contrasts/<context>.json: per gene, ensembl_id, baseMean, log2FoldChange, pvalue, padj, lfcSE, available_statistics. All NA becomes JSON null, not0. Preserve high precision in exports, round only display. Record whether effect estimates are shrunken and ensure displayed/tested metrics are coherent. Positive log2FC=first named group higher.
6. expression/<chunk>.json: ensembl_id, sample_id_analysis, normalized_count, log2_normalized_plus1. File can contain limited gene blocks; manifest maps gene IDs to chunk. All valid biological samples, not only means, should be accessible for selected genes. Means and any uncertainty summaries must use independent animals within each group/region/time.
7. annotation_edges.csv: ensembl_id, GO_id, term_name, annotation_source, annotation_version. These edges express membership, never directed regulation. Export enrichment separately with comparison ID, background size, tested-term adjustment, adjusted_p and overlap_count. Do not treat annotation overlap as enrichment.

## Model and frontend separation
Classroom R pipeline -> exported static files -> frontend. No DESeq2 refitting on clicks. Recompute only threshold summaries/highlights from existing statistics. All24 region-time phenotype comparisons are planned. Time profiles are descriptive; interactions/time effects require separately specified tests.

## State
{contrast, region, zt, selectedGeneId, selectedTermId, alpha, absLfcCutoff, analysisVersion}
- initial recommended demo context: SCN,ZT16,resilient_vs_control; no claimed best gene. Proposed starting cutoffs alpha=0.05 and |log2FC|=0.5, matching the paper, subject to classroom-code review; label the selected cutoffs explicitly.
- overview cell click: set region+zt; update B/D and C selected-time marker; preserve selected gene when available.
- volcano or gene node click: set gene; update C and cross-highlights in B/D.
- term click: set term; highlight its members in B/D, preserve the remaining comparison context.
- contrast change: reload its cached/prepared data; retain a selected gene if represented. If unavailable, display reason, do not silently replace with a new gene.
- reset: clear gene/term; restore documented default context and thresholds.
- no DEGs or enrichment: explicit empty/enrichment-unavailable state. If GO annotations exist, annotation-only network must be labeled as such. No annotations means an honest empty network.

## Visual encoding and performance
Overview row=region,column=ZT; lightness+printed values; fixed comparable scale across contexts where practical. Volcano x=log2FC,y=-log10padj; handle reported zero p-values via a documented display cap without editing original data. Group colors are supplemented by point shapes and line styles in expression profile. Network is bounded, deterministic, and uses shapes for node type. Axis units, comparison direction and included sample sizes visible. Load comparison and gene expression chunks on demand, use local cache; target a small initial payload (e.g. under5MB, to be measured). Use Canvas within D3 if SVG point counts impair interaction. Use accessible HTML controls and relative paths for GitHub Pages.

## Acceptance checks
- Raw-to-export spot checks for at least one gene in each group and metadata ID joins.
- Verify exclusion/label mapping before any final fitting; keep an audit trail and sample counts.
- Verify contrast sign with normalized group summaries, accounting for model-estimate differences.
- Check known NA, no-selected-gene, no-DEG and no-GO states; no fake zeros.
- Trace cell -> contrast -> gene -> profile -> process highlight -> reset with actual exported records.
- Browser at typical laptop width; keyboard controls and legends legible; reload direct public URL without login.

