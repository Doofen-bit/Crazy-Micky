"""Prepare static assets and explicit hypergeometric/BH GO enrichment."""
from pathlib import Path
import json, math, hashlib, shutil
import numpy as np
import pandas as pd
from scipy.stats import hypergeom

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'results'; OUT=ROOT/'site/data'
for sub in ['contrasts','expression','networks']: (OUT/sub).mkdir(parents=True,exist_ok=True)
def clean(v):
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,float)): return float(v) if np.isfinite(v) else None
    if pd.isna(v): return None
    return v
def dump(p,v): p.write_text(json.dumps(clean(v),ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
samples=pd.read_csv(RES/'samples.csv')
expr=pd.read_csv(RES/'normalized_counts.csv').set_index('ensembl_id')
annotations=pd.read_csv(RES/'gene_annotations.csv').set_index('ENSEMBL')
geneids=list(expr.index); index={g:i for i,g in enumerate(geneids)}
symbols={g:None if g not in annotations.index or pd.isna(annotations.at[g,'SYMBOL']) else annotations.at[g,'SYMBOL'] for g in geneids}
genes=[[g,symbols[g],i//256] for i,g in enumerate(geneids)]
dump(OUT/'genes.json',genes)
dump(OUT/'samples.json',samples[['sample_id_source','sample_id_analysis','animal_id','region','zt','phenotype','normalization_factor']].to_dict('records'))
assert list(expr.columns)==samples.sample_id_analysis.tolist()
for start in range(0,len(genes),256):
    chunk={str(i):expr.iloc[i].tolist() for i in range(start,min(start+256,len(genes)))}
    dump(OUT/'expression'/f'{start//256}.json',chunk)
edges=pd.read_csv(RES/'annotation_edges.csv')
term_names=edges.drop_duplicates('GOALL').set_index('GOALL').term_name.to_dict()
members=edges.groupby('GOALL').ENSEMBL.agg(set).to_dict()
mapped=set(edges.ENSEMBL)
overview=pd.read_csv(RES/'overview.csv').to_dict('records')
enrichments=[]
for context in overview:
    cid=context['id']; d=pd.read_csv(RES/'contrasts'/f'{cid}.csv')
    d['i']=d.ensembl_id.map(index)
    cols=['i','log2FoldChange','padj','baseMean','pvalue','lfcSE']
    dump(OUT/'contrasts'/f'{cid}.json',dict(columns=cols,rows=d[cols].values.tolist()))
    context['thresholds']={}
    for alpha in [.01,.05,.1]:
        for lfc in [0,.5,1,2]:
            sig=d.padj.lt(alpha)&d.log2FoldChange.abs().gt(lfc)
            context['thresholds'][f'{alpha}:{lfc:g}']={'up':int((sig&d.log2FoldChange.gt(0)).sum()),'down':int((sig&d.log2FoldChange.lt(0)).sum())}
    universe=set(d.loc[d.padj.notna(),'ensembl_id'])&mapped
    foreground=set(d.loc[d.padj.lt(.05)&d.log2FoldChange.abs().gt(.5),'ensembl_id'])&universe
    terms=[]
    for term,gs in members.items():
        bg=gs&universe
        if not 10<=len(bg)<=500: continue
        overlap=bg&foreground
        p=float(hypergeom.sf(len(overlap)-1,len(universe),len(bg),len(foreground))) if foreground else 1.
        terms.append(dict(id=term,name=term_names[term],pvalue=p,overlap_count=len(overlap),term_background=len(bg),background_size=len(universe),foreground_size=len(foreground)))
    terms.sort(key=lambda t:(t['pvalue'],t['id']))
    m=len(terms); prev=1.
    for rank in range(m,0,-1):
        t=terms[rank-1];prev=min(prev,t['pvalue']*m/rank);t['padj']=prev;t['tested_terms']=m;t['context']=cid
    enrichments.extend(terms)
    enriched=[t for t in terms if t['padj']<.05 and t['overlap_count']>0]
    present=set(d.ensembl_id)
    if enriched:
        chosen=enriched[:5];mode='enrichment'
    else:
        top=set(d.sort_values('padj',na_position='last').head(30).ensembl_id)
        chosen=sorted([t for t in terms if len(members[t['id']]&top)>=2],key=lambda t:(-len(members[t['id']]&top),t['term_background'],t['id']))[:5]
        mode='annotation'
    network=[]
    for t in chosen:
        network.append(dict(t,members=sorted(index[g] for g in members[t['id']]&present)))
    dump(OUT/'networks'/f'{cid}.json',dict(mode=mode,terms=network,total_enriched=len(enriched),tested_terms=m,background_size=len(universe),foreground_size=len(foreground),alpha=.05,lfc=.5,max_terms=5,max_genes=30))
    context['enriched_terms']=len(enriched)
pd.DataFrame(enrichments).to_csv(RES/'go_enrichment_all.csv',index=False)
dump(OUT/'overview.json',overview)
meta=json.loads((RES/'analysis_metadata.json').read_text())
audit=json.loads((ROOT/'audit/input_audit.json').read_text())
meta.update(dataset_doi='10.12751/g-node.jj57l9',paper_doi='10.1038/s41398-024-03100-w',created_at='2026-11-23',raw_zip_sha256=audit['zip_sha256'],samples=audit,expression_chunk_size=256,go_method='One-sided hypergeometric overrepresentation; BH across all eligible BP terms (10–500 background genes) per contrast; GOALL ancestor memberships',go_universe='GO BP-mapped genes with finite padj in that contrast',go_thresholds='Fixed padj < 0.05 and abs(log2FC) > 0.5; does not change with exploration controls',source_commit=None,public_url=None)
dump(OUT/'manifest.json',meta)
meta.update(public_url='https://doofen-bit.github.io/Crazy-Micky/',repository='https://github.com/Doofen-bit/Crazy-Micky',code_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['scripts/prepare_inputs.py','scripts/verify_label_provenance.py','analysis/run_analysis.R','scripts/export_site.py','site/app.js']})
dump(OUT/'manifest.json',meta)
for src,dst in [('overview.csv','overview.csv'),('samples.csv','samples.csv'),('analysis_metadata.json','analysis_metadata.json'),('annotation_metadata.csv','annotation_metadata.csv'),('session_info.txt','session_info.txt')]: shutil.copy2(RES/src,OUT/dst)
# Relative browser paths and full precision scientific values are kept; no NA->zero coercion.
checks={'contrast_count':len(overview),'gene_count':len(genes),'expression_samples':expr.shape[1],'all_expression_finite':bool(np.isfinite(expr.values).all()),'all_expression_nonnegative':bool((expr.values>=0).all()),'all_contrasts_have_enrichment_audit':len(set(t['context'] for t in enrichments))==24}
assert checks['contrast_count']==24 and checks['expression_samples']==93
assert checks['all_expression_finite'] and checks['all_expression_nonnegative']
dump(ROOT/'audit/export_validation.json',checks)
print(json.dumps(checks,indent=2))
