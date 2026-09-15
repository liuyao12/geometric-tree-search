"""Independent fixed-cover midpoint-field witness audit."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

paths=list(map(Path,sys.argv[1:]));assert len(paths)==8
coverp,dictp,libp,transferp,rescuep,priorp,resultp,out=paths
cover,dictionary,lib,transfer,rescue,prior,result=[json.loads(p.read_text()) for p in paths[:-1]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p in paths[:6]:assert result['sourceHashes'][p.name]==sha(p)
assert prior['rescueHash']==sha(rescuep) and prior['libraryHash']==sha(libp)
cc={r['id']:r for r in cover['results']};dd={r['id']:r for r in dictionary['configurations']};tt={r['id']:r for r in transfer['results']};rr={r['id']:r for r in rescue['results']}
assert [r['id'] for r in result['results']]==[r['id'] for r in rescue['results'] if r['complete']]
checked=0;maxerror=0.;required=[]
for row in result['results']:
    cid=row['id'];repairs={r['edge']:r['witness'] for r in rr[cid]['repairs']};old={r['edge']:r for r in tt[cid]['matches']};inc=defaultdict(list);sr=0.
    assert [s['edge'] for s in row['selected']]==list(old)
    for s in row['selected']:
        edge=s['edge'];fix=repairs.get(edge);o=dd[cid]['occurrences'][edge];w=fix or old[edge]
        assert s['motif']==w['motif'] and s['rotationRow']==(fix['rotationRow'] if fix else o['rotationRow'])
        sr=max(sr,*w['endpointDistances']);R=np.asarray(s['rotationRow'])
        atoms=[o['ids'][j] for j in (fix['permutation'] if fix else o['permutation'])]
        b=lib['baseMotifs'][lib['motifs'][s['motif']]['base']]
        expected=[]
        for sites in b['componentSites']:
            roots=[root for root in cc[cid]['componentPairs'][edge] if {atoms[j] for j in sites}==set(cc[cid]['components'][root])]
            assert len(roots)==1;expected.append(roots[0])
        assert s['roots']==expected and len(set(expected))==2
        for side,root in enumerate(expected):
            f=lib['motifs'][s['motif']]['fieldM'][side];assert f['sigma']==.4
            inc[root].append((edge,np.asarray(f['vectors'])@R,f['amplitudes'],f['colors']))
    assert set(inc)==set(range(len(cc[cid]['components']))) and all(len(v)==2 for v in inc.values())
    assert [p['root'] for p in row['pairs']]==sorted(inc)
    maximum=0.
    for p in row['pairs']:
        a,b=inc[p['root']];assert p['edges']==[a[0],b[0]]
        x=np.vstack([a[1],b[1]]);weights=np.r_[a[2],-np.asarray(b[2])];colors=np.r_[a[3],b[3]]
        dx=x[:,None,0]-x[None,:,0];dy=x[:,None,1]-x[None,:,1];dz=x[:,None,2]-x[None,:,2]
        terms=weights[:,None]*weights[None,:]*np.exp(-(dx*dx+dy*dy+dz*dz)/.32)*(colors[:,None]==colors[None,:])
        squared=math.fsum(map(float,terms.ravel()));assert squared>=-1e-10
        distance=math.sqrt(max(0.,squared));error=abs(distance-p['distance']);assert error<1e-8
        maximum=max(maximum,distance/2);maxerror=max(maxerror,error);checked+=1
    assert abs(row['sourceWitnessRadius']-sr)<1e-12 and abs(row['midpointWitnessRadius']-maximum)<1e-8
    assert maximum<=sr+1e-8;required.append((sr,maximum))
assert result['configurations']==len(required)
assert [x['radius'] for x in result['summary']]==[.2,.3,.4,.5,.6,.8,transfer['summary']['diagnosticThreshold']]
for r in result['summary']:
    assert r['sourceWitnessCovers']==sum(s<=r['radius'] for s,m in required)
    assert r['midpointWitnessCovers']==sum(m+1e-8<=r['radius'] for s,m in required)
report=dict(resultHash=sha(resultp),priorCheckHash=sha(priorp),verifierHash=sha(Path(__file__)),configurations=len(required),checkedPairs=checked,maxDistanceDisagreement=maxerror,summary=result['summary'],limits='Numerical common midpoint witnesses at exactly two-field anchors. Not all-pose completeness, physical neighborhoods, learned thresholds, negative specificity or search.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report),flush=True)
