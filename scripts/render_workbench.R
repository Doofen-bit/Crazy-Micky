.libPaths(c('.r-library','../../Genomics/.r-library',.libPaths()))
rmarkdown::render('analysis/Stress_RNAseq_Workbench.Rmd',quiet=TRUE)
