"""Add an edge 'strength' level to every gene–process edge in site/data/networks/*.json.

3 = direct annotation with experimental evidence (EXP, IDA, IPI, IMP, IGI, IEP and high-throughput HTP/HDA/HMP/HGI/HEP)
2 = direct annotation with other evidence (orthology/sequence/phylogeny/electronic/author/curator: ISO, ISS, IBA, IEA, TAS, NAS, IC, ...)
1 = indirect: gene is annotated only to a more specific child process (GOALL ancestor membership)
Input: results/go_direct_evidence.csv from analysis/export_go_evidence.R. Enrichment statistics are not touched.
"""
from pathlib import Path
import json, glob, collections
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTAL = {'EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP', 'HTP', 'HDA', 'HMP', 'HGI', 'HEP'}
ev = pd.read_csv(ROOT / 'results/go_direct_evidence.csv')
level = collections.defaultdict(int)
for g, t, e in ev.itertuples(index=False):
    level[(g, t)] = max(level[(g, t)], 3 if e in EXPERIMENTAL else 2)
genes = json.loads((ROOT / 'site/data/genes.json').read_text())
counts = collections.Counter()
for f in sorted(glob.glob(str(ROOT / 'site/data/networks/*.json'))):
    n = json.loads(Path(f).read_text())
    for t in n['terms']:
        t['strength'] = [level.get((genes[i][0], t['id']), 0) or 1 for i in t['members']]
        counts.update(t['strength'])
    n['strength_levels'] = {'3': 'direct, experimental evidence', '2': 'direct, inferred evidence', '1': 'indirect (via a more specific sub-process)'}
    Path(f).write_text(json.dumps(n, separators=(',', ':')))
assert set(counts) <= {1, 2, 3}
print('edge strength levels across all 24 networks:', dict(sorted(counts.items())))
