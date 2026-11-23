# Run from project root. Original classroom files are read-only references.
.libPaths(c('.r-library','../../Genomics/.r-library',.libPaths()))
suppressPackageStartupMessages({library(DESeq2);library(AnnotationDbi);library(org.Mm.eg.db);library(GO.db);library(jsonlite)})
dir.create('results/contrasts',recursive=TRUE,showWarnings=FALSE)
dir.create('results/qc',recursive=TRUE,showWarnings=FALSE)
meta <- read.csv('analysis/input/samples.csv',stringsAsFactors=FALSE)
raw <- as.matrix(read.csv('analysis/input/counts.csv',row.names=1,check.names=FALSE))
storage.mode(raw) <- 'integer'
stopifnot(identical(colnames(raw),meta$sample_id_analysis), !anyDuplicated(rownames(raw)), all(raw>=0))
meta$inclusion <- tolower(meta$inclusion)=='true'
meta <- meta[meta$inclusion,]
rownames(meta) <- meta$sample_id_analysis
raw <- raw[,rownames(meta)]
meta$phenotype <- factor(meta$phenotype,levels=c('control','resilient','susceptible'))
meta$normalization_factor <- NA_real_
normalized <- matrix(NA_real_,nrow(raw),ncol(raw),dimnames=dimnames(raw))
for (region in c('SCN','Hb')) {
  ii <- which(meta$region==region)
  d <- DESeqDataSetFromMatrix(raw[,ii],meta[ii,],~phenotype)
  d <- estimateSizeFactors(d)
  meta$normalization_factor[ii] <- sizeFactors(d)
  normalized[,ii] <- counts(d,normalized=TRUE)
  # Descriptive sample QC, explicitly log2 normalized counts (not VST).
  x <- log2(normalized[,ii]+1)
  variable <- head(order(apply(x,1,var),decreasing=TRUE),500)
  pc <- prcomp(t(x[variable,]),center=TRUE,scale.=FALSE)
  q <- data.frame(meta[ii,],PC1=pc$x[,1],PC2=pc$x[,2])
  write.csv(q,paste0('results/qc/pca_',region,'.csv'),row.names=FALSE)
  pdf(paste0('results/qc/pca_',region,'.pdf'),width=8,height=6)
  plot(q$PC1,q$PC2,col=c('#546981','#008c86','#cc633d')[as.integer(q$phenotype)],pch=match(q$zt,c(4,10,16,22))+14,xlab=paste0('PC1 (',round(100*pc$sdev[1]^2/sum(pc$sdev^2),1),'%)'),ylab='PC2',main=paste(region,'log2 normalized counts; top 500 variable genes'))
  text(q$PC1,q$PC2,labels=q$sample_id_analysis,cex=.45,pos=3)
  legend('topright',legend=levels(meta$phenotype),col=c('#546981','#008c86','#cc633d'),pch=16,bty='n')
  dev.off()
}
write.csv(meta,'results/samples.csv',row.names=FALSE)
write.csv(data.frame(ensembl_id=rownames(normalized),normalized,check.names=FALSE),'results/normalized_counts.csv',row.names=FALSE)
allkeys <- intersect(rownames(raw),keys(org.Mm.eg.db,keytype='ENSEMBL'))
ann <- AnnotationDbi::select(org.Mm.eg.db,keys=allkeys,keytype='ENSEMBL',columns=c('SYMBOL','GENENAME'))
ann <- ann[order(ann$ENSEMBL,is.na(ann$SYMBOL),ann$SYMBOL),]
ann <- ann[!duplicated(ann$ENSEMBL),]
write.csv(ann,'results/gene_annotations.csv',row.names=FALSE)
go <- AnnotationDbi::select(org.Mm.eg.db,keys=allkeys,keytype='ENSEMBL',columns=c('GOALL','ONTOLOGYALL'))
go <- unique(go[!is.na(go$GOALL)&go$ONTOLOGYALL=='BP',c('ENSEMBL','GOALL')])
terms <- AnnotationDbi::select(GO.db,keys=unique(go$GOALL),keytype='GOID',columns='TERM')
go$term_name <- terms$TERM[match(go$GOALL,terms$GOID)]
write.csv(go,'results/annotation_edges.csv',row.names=FALSE)
write.csv(AnnotationDbi::metadata(org.Mm.eg.db),'results/annotation_metadata.csv',row.names=FALSE)
pairs <- list(c('resilient','control'),c('susceptible','control'),c('resilient','susceptible'))
summary <- list(); validations <- list()
# Start with the handoff's reference context, then cover all eight strata.
contexts <- rbind(data.frame(region='SCN',zt=16),subset(expand.grid(region=c('SCN','Hb'),zt=c(4,10,16,22)),!(region=='SCN'&zt==16)))
for (k in seq_len(nrow(contexts))) {
  region <- as.character(contexts$region[k]); zt <- contexts$zt[k]
  message('Fitting ',region,' ZT',zt)
  ii <- which(meta$region==region & meta$zt==zt)
  cm <- meta[ii,]; cnt <- raw[,ii,drop=FALSE]
  stopifnot(identical(colnames(cnt),rownames(cm)),all(table(cm$phenotype)>=2),!anyDuplicated(cm$animal_id))
  med <- sapply(levels(cm$phenotype),function(g) apply(cnt[,cm$phenotype==g,drop=FALSE],1,median))
  keep <- apply(med,1,max)>=10
  mm <- model.matrix(~phenotype,cm)
  stopifnot(qr(mm)$rank==ncol(mm))
  d <- DESeqDataSetFromMatrix(cnt[keep,],cm,~phenotype)
  # Shared region-wide normalization makes all four time-profile panels comparable.
  sizeFactors(d) <- cm$normalization_factor
  d <- DESeq(d,quiet=TRUE)
  pdf(paste0('results/qc/dispersion_',region,'_',zt,'.pdf')); plotDispEsts(d); dev.off()
  for (pair in pairs) {
    name <- paste(region,paste0('zt',zt),paste(pair,collapse='_vs_'),sep='_')
    r <- as.data.frame(results(d,contrast=c('phenotype',pair),alpha=.05))
    # Keep independent filtering and Cook's-distance NA; do not change missing tests to zero.
    r$ensembl_id <- rownames(r)
    r$symbol <- ann$SYMBOL[match(r$ensembl_id,ann$ENSEMBL)]
    r$mean_first <- rowMeans(normalized[r$ensembl_id,rownames(cm)[cm$phenotype==pair[1]],drop=FALSE])
    r$mean_second <- rowMeans(normalized[r$ensembl_id,rownames(cm)[cm$phenotype==pair[2]],drop=FALSE])
    r <- r[,c('ensembl_id','symbol','baseMean','log2FoldChange','lfcSE','stat','pvalue','padj','mean_first','mean_second')]
    write.csv(r,paste0('results/contrasts/',name,'.csv'),row.names=FALSE,na='NA')
    sig <- !is.na(r$padj)&r$padj<.05&abs(r$log2FoldChange)>.5
    s <- data.frame(id=name,region=region,zt=zt,contrast=paste(pair,collapse='_vs_'),retained_genes=nrow(r),tested_genes=sum(!is.na(r$padj)),unavailable_padj=sum(is.na(r$padj)),up=sum(sig&r$log2FoldChange>0),down=sum(sig&r$log2FoldChange<0),n_group1=sum(cm$phenotype==pair[1]),n_group2=sum(cm$phenotype==pair[2]))
    summary[[name]] <- s
    # A reversed explicit contrast must negate every finite effect and preserve p-values.
    reverse <- as.data.frame(results(d,contrast=c('phenotype',rev(pair)),alpha=.05))
    stopifnot(isTRUE(all.equal(r$log2FoldChange,-reverse$log2FoldChange,tolerance=1e-8)),isTRUE(all.equal(r$pvalue,reverse$pvalue,tolerance=1e-8)))
    nonzero <- abs(r$log2FoldChange)>.1 & r$mean_first>0 & r$mean_second>0
    validations[[name]] <- data.frame(id=name,reverse_contrast_pass=TRUE,normalized_mean_sign_agreement=mean(sign(r$log2FoldChange[nonzero])==sign(log2(r$mean_first[nonzero]/r$mean_second[nonzero]))),model_rank=qr(mm)$rank,n_samples=nrow(cm))
  }
}
write.csv(do.call(rbind,summary),'results/overview.csv',row.names=FALSE)
write.csv(do.call(rbind,validations),'audit/model_validation.csv',row.names=FALSE)
writeLines(capture.output(sessionInfo()),'results/session_info.txt')
jsonlite::write_json(list(analysis_version='1.0.0',provenance='team_reanalysis',design='Within region and ZT: ~ phenotype; three groups, three explicit contrasts',normalization='DESeq2 median ratios across included samples within region; same factors supplied to each stratum',filter='Any phenotype median raw count >= 10 within stratum',lfc_shrinkage=FALSE,alpha=.05,abs_lfc_cutoff=.5,independent_filtering=TRUE,annotation_package=as.character(packageVersion('org.Mm.eg.db')),GO_db_version=as.character(packageVersion('GO.db')),DESeq2_version=as.character(packageVersion('DESeq2')),n_samples=ncol(raw)), 'results/analysis_metadata.json',pretty=TRUE,auto_unbox=TRUE)
message('All 24 contrasts completed.')
