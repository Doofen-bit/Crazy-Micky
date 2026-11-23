# Project instructions

- Read PROJECT_CONTEXT.md, DATA_CONTRACT.md, DECISIONS.md and audit/audit_summary.json before project work.
- Explain work in Chinese with English technical terms; code and identifiers in English.
- Keep raw data immutable. Write outputs to new analysis/export locations. Do not overwrite classroom files.
- Inspect existing classroom code in C:\Users\Doofen\Desktop\NYU\26Fall\Genomics before implementing the R workflow. If inaccessible, report that limitation; do not invent its contents.
- Use the classroom pipeline for the GB assignment and preserve an explainable .Rmd plus rendered .html. Do not silently substitute a new method.
- Use all eligible brain-region, time and phenotype conditions. Full coverage does not require sending all raw matrices to the browser.
- Audit author label corrections and exclusions. C01_E1 and A15_A need explicit provenance decisions. Do not mechanically apply swaps twice.
- Keep source file IDs, corrected analysis IDs and animal IDs separate and record any mapping. Repeated brain regions are paired within an animal, not independent animals. Different times are different animals.
- Do not claim biological findings from this structural audit. Mark author results, reanalysis outputs and schematic visuals distinctly.
- Preserve NA statistics. Do not replace NA adjusted p-values with zero. Validate comparison direction and identity joins.
- Use D3.js for the core static website, deployable to GitHub Pages. Four distinct core views: context overview, volcano, temporal gene expression, gene–GO process network. At least two truly linked views.
- Network edges mean annotation membership, not causal regulation. Do not invent GO data or enrichment; track annotation source/version and background genes.
- Browser is for prepared-data exploration, not differential-expression model fitting. Chunk contrast/expression assets and use relative paths.
- Before finalizing scientific results, test meaningful invariants: sample/ID alignment, contrast signs, exclusion lists, missing-value behavior and model inputs. Before publishing UI, check cell/gene/process/reset transitions and empty states against exported values.
- Maintain AI_USAGE.md and DECISIONS.md. All team members must review and understand their contributions. Do not claim a repository or public deployment exists before it does.

