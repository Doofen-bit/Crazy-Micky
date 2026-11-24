# Direct GO Biological Process annotations with evidence codes for genes shown in the website networks.
# Used only to set edge thickness in View 4 (how directly a gene is linked to a process). Enrichment is unchanged.
.libPaths(c('.r-library','../../Genomics/.r-library',.libPaths()))
suppressPackageStartupMessages(library(org.Mm.eg.db))
keys <- readLines('analysis/input/network_genes.txt')
go <- suppressMessages(AnnotationDbi::select(org.Mm.eg.db, keys=keys, keytype='ENSEMBL', columns=c('GO','EVIDENCE','ONTOLOGY')))
go <- unique(go[!is.na(go$GO) & go$ONTOLOGY=='BP', c('ENSEMBL','GO','EVIDENCE')])
write.csv(go, 'results/go_direct_evidence.csv', row.names=FALSE)
cat(nrow(go), 'direct BP annotations for', length(unique(go$ENSEMBL)), 'genes\n')
print(sort(table(go$EVIDENCE), decreasing=TRUE))
