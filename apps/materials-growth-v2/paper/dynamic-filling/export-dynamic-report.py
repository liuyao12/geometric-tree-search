"""Export aggregate/occupancy report data; no atom coordinates or model clouds."""
import hashlib,json,sys
from pathlib import Path

poolp,searchp,checkp,weightcheckp,weightp,out=map(Path,sys.argv[1:])
pool,search,check,weightcheck,weights=[json.loads(p.read_text()) for p in [poolp,searchp,checkp,weightcheckp,weightp]]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert check['poolHash']==search['poolHash']==sha(poolp) and check['searchHash']==sha(searchp)
assert weightcheck['resultHash']==sha(weightp)
frames={f['configuration']:f for f in pool['frames']};verified={r['configuration'] for r in check['positiveWitnesses']};rows=[]
for result in search['rows']:
    f=frames[result['configuration']];good=result['status']=='verified-finite-point-model'
    assert good==(result['configuration'] in verified)
    points=[p['id'] for p in f['points']];roots=set(f['required']);totals=dict.fromkeys(points,0)
    def snapshot():return [totals[p] for p in points]
    states=[snapshot()];byid={c['id']:c for c in f['candidates']}
    for cid in result['selected']:
        for t in byid[cid]['t']:totals[t['point']]+=t['value']
        states.append(snapshot())
    rows.append(dict(id=result['configuration'],phase='alpha' if '-alpha-' in result['configuration'] else 'beta',
                     verified=good,candidates=len(f['candidates']),atomRoots=[p in roots for p in points],
                     capacity=f['capacity'],states=states,stats=result['stats']))
report=dict(version='dynamic-filling-2026-09-20',rows=rows,weightSummary=weights['summary'],
            sourceHashes=dict(pool=sha(poolp),search=sha(searchp),check=sha(checkp),weights=sha(weightp)),
            scope='88 source-order evaluation frames. Known atom positions, motif partition, poses and cell supplied. Latent sites generated from all surviving contact alternatives, not a chosen cover. Fixed-pose finite domain; not blind growth or same-condition validation.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(frames=len(rows),verified=sum(r['verified'] for r in rows))))
