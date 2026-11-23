"""Immutable count audit and content-supported metadata correction."""
from pathlib import Path
import hashlib, json, re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'narain_et_al-2024-translational_psychiatry/narain_et_al-2024-translational_psychiatry'
out = ROOT / 'analysis/input'
out.mkdir(parents=True, exist_ok=True)
files = sorted((SOURCE/'01_data_raw/03_seq/02_counts_r').glob('*.txt'))
if not files:
    files = sorted(p for p in (SOURCE/'01_data_raw/03_seq/02_counts_r').iterdir() if p.is_file() and p.name[0] in 'LS')
exclusions = {'L1R-E05_5','S1R-E05_5','L2S-E05_1'}
samples, arrays, ids = [], [], None
for p in files:
    sid=p.stem
    m=re.fullmatch(r'([LS])([1234])([CRS])-(.+)',sid)
    assert m, p
    region,t,ph,animal=m.groups()
    d=pd.read_csv(p,sep='\t',header=None,names=['ensembl_id','count'])
    if ids is None: ids=d.ensembl_id.tolist()
    assert d.ensembl_id.tolist()==ids and d.ensembl_id.is_unique
    a=d['count'].to_numpy()
    assert np.isfinite(a).all() and (a>=0).all() and (a==a.astype(int)).all()
    corrected=sid
    reason='Filename metadata; no correction required'
    if animal=='A15_A':
        region={'L':'S','S':'L'}[region]
        corrected=region+sid[1:]
        reason='One region swap; full-gene proportional match to author normalized tables (see metadata-content-matching.json)'
    if animal=='C01_E1': reason='Keep corrected raw ZT4; ignore stale ZT10 processed header'
    samples.append(dict(sample_id_source=sid,sample_id_analysis=corrected,animal_id=animal,region={'L':'Hb','S':'SCN'}[region],zt=[4,10,16,22][int(t)-1],phenotype={'C':'control','R':'resilient','S':'susceptible'}[ph],inclusion=sid not in exclusions,exclusion_reason='Author documented exclusion' if sid in exclusions else '',mapping_reason=reason,library_counts=int(a.sum()),source_file=str(p.relative_to(ROOT.parent)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    arrays.append(a)
mat=np.column_stack(arrays)
meta=pd.DataFrame(samples)
assert len(meta)==96 and len(ids)==46603
assert meta.sample_id_analysis.is_unique and len(meta.animal_id.unique())==48
assert meta.groupby('animal_id').size().eq(2).all()
assert meta.groupby('animal_id').zt.nunique().eq(1).all()
assert meta.groupby('animal_id').phenotype.nunique().eq(1).all()
assert meta.inclusion.sum()==93
meta.to_csv(out/'samples.csv',index=False)
pd.DataFrame(mat,index=ids,columns=meta.sample_id_analysis).rename_axis('ensembl_id').to_csv(out/'counts.csv')
meta[meta.inclusion].groupby(['region','zt','phenotype']).size().rename('n').to_csv(ROOT/'audit/included_group_counts.csv')
summary=dict(raw_samples=96,included_samples=93,raw_genes=len(ids),all_zero_genes=int((mat.sum(axis=1)==0).sum()),animals=48,included_animals=int(meta[meta.inclusion].animal_id.nunique()),corrected_content_mappings=meta[meta.sample_id_source!=meta.sample_id_analysis][['sample_id_source','sample_id_analysis']].to_dict('records'),exclusions=sorted(exclusions),zip_sha256=hashlib.sha256((ROOT.parent/'narain_et_al-2024-translational_psychiatry-master.zip').read_bytes()).hexdigest())
(ROOT/'audit/input_audit.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
