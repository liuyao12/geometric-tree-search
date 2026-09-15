"""Fixed-cover pairwise common-field radius diagnostic; no threshold training."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist

paths=list(map(Path,sys.argv[1:]));assert len(paths)==7
coverp,dictp,libp,transferp,rescuep,checkp,out=paths
cover,dictionary,library,transfer,rescue,check=[json.loads(p.read_text()) for p in paths[:-1]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert check['rescueHash']==sha(rescuep) and check['libraryHash']==sha(libp)
assert rescue['sourceHashes'][transferp.name]==sha(transferp)
assert library['sourceHashes']['cover']==sha(coverp) and library['sourceHashes']['dictionary']==sha(dictp)
cv={r['id']:r for r in cover['results']};dd={r['id']:r for r in dictionary['configurations']};tt={r['id']:r for r in transfer['results']}
grid=[.2,.3,.4,.5,.6,.8,transfer['summary']['diagnosticThreshold']]
def field(i,s,R):
    f=library['motifs'][i]['fieldM'][s]
    return np.asarray(f['vectors'])@R,np.asarray(f['amplitudes']),np.asarray(f['colors']),f['sigma']
def inner(a,b):
    x,w,c,s=a;y,v,d,t=b;assert s==t
    return float(np.sum(w[:,None]*v[None,:]*np.exp(-cdist(x,y,'sqeuclidean')/(2*s*s))*(c[:,None]==d[None,:])))
rows=[]
for row in rescue['results']:
    if not row['complete']:continue
    cid=row['id'];repairs={a['edge']:a['witness'] for a in row['repairs']};inc=defaultdict(list);source_radius=0.;selected=[]
    for w in tt[cid]['matches']:
        edge=w['edge'];o=dd[cid]['occurrences'][edge];fix=repairs.get(edge)
        if fix:
            motif=fix['motif'];R=np.asarray(fix['rotationRow']);roots=fix['roots'];distances=fix['endpointDistances']
        else:
            motif=w['motif'];R=np.asarray(o['rotationRow']);distances=w['endpointDistances']
            atoms=[o['ids'][j] for j in o['permutation']]
            roots=[root for sites,root in sorted((sorted(j for j,a in enumerate(atoms) if a in cv[cid]['components'][root]),root) for root in cv[cid]['componentPairs'][edge])]
        source_radius=max(source_radius,*distances)
        selected.append(dict(edge=edge,motif=motif,rotationRow=R.tolist(),roots=roots))
        for side,root in enumerate(roots):inc[root].append((edge,motif,side,R))
    assert len(inc)==len(cv[cid]['components']) and all(len(v)==2 for v in inc.values())
    pairs=[]
    for root,items in sorted(inc.items()):
        a,b=[field(i,s,R) for e,i,s,R in items];squared=math.fsum([inner(a,a),inner(b,b),-2*inner(a,b)])
        assert squared>=-1e-10
        pairs.append(dict(root=root,edges=[v[0] for v in items],distance=math.sqrt(max(0.,squared))))
    required=max(p['distance']/2 for p in pairs)
    assert required<=source_radius+1e-8
    rows.append(dict(id=cid,sourceWitnessRadius=source_radius,midpointWitnessRadius=required,pairs=pairs,selected=selected))
summary=[dict(radius=r,sourceWitnessCovers=sum(x['sourceWitnessRadius']<=r for x in rows),midpointWitnessCovers=sum(x['midpointWitnessRadius']+1e-8<=r for x in rows)) for r in grid]
report=dict(scope=__doc__,sourceHashes={p.name:sha(p) for p in paths[:-1]},codeHash=sha(Path(__file__)),protocolHash=sha(Path(__file__).with_name('ICE-PAIR-RADIUS-PROTOCOL.md')),configurations=len(rows),summary=summary,results=rows,limits='Developmental fixed-witness diagnostic, not trained thresholds, specificity, new geometry, search reconstruction or independent-condition validation. Midpoint convention valid only at exactly two-field anchors. Guarded floating-point checks, not exact certificates.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(summary),flush=True)
