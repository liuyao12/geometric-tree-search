"""Independent replay of fixed-cover, freely selected decoration search."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

libp,transferp,pairp,dictp,resultp,out=map(Path,sys.argv[1:])
lib,transfer,pair,dictionary,result=[json.loads(p.read_text()) for p in [libp,transferp,pairp,dictp,resultp]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pp={r['id']:r for r in pair['results']};dd={r['id']:r for r in dictionary['configurations']}
allowed={s['motif'] for r in lib['trainingRegistrations'] if r['id'] in transfer['fitFrames'] for s in r['selected']}
assert [(r['id'],r['enabled']) for r in result['results']]==[(cid,enabled) for cid in ['c00400','c00900','c01400','c01900'] for enabled in [False,True]]
rows=[]
for run in result['results']:
    cid=run['id'];poses={s['edge']:s for s in pp[cid]['selected']};inc=defaultdict(list);totals=defaultdict(int);owners=set();changed=0
    for key in run['selected']:
        edge,i=map(int,key.split(':'));assert edge in poses and i in allowed and edge not in owners;owners.add(edge)
        s=poses[edge];assert lib['motifs'][i]['base']==lib['motifs'][s['motif']]['base'];changed+=i!=s['motif']
        for atom in dd[cid]['occurrences'][edge]['ids']:totals[atom]+=1;assert totals[atom]<=2
        for side,root in enumerate(s['roots']):
            f=lib['motifs'][i]['fieldM'][side];assert f['sigma']==.4
            inc[root].append((np.asarray(f['vectors'])@np.asarray(s['rotationRow']),np.asarray(f['amplitudes']),f['colors']))
    required={a for edge in poses for a in dd[cid]['occurrences'][edge]['ids']};complete=all(totals[a]==2 for a in required)
    assert complete==run['scalarComplete'];maxdist=0.;incompatible=0;pairs=0
    for values in inc.values():
        assert len(values)<=2
        if len(values)<2:continue
        a,b=values;x=np.vstack([a[0],b[0]]);w=np.r_[a[1],-b[1]];c=np.r_[a[2],b[2]]
        dx=x[:,None,0]-x[None,:,0];dy=x[:,None,1]-x[None,:,1];dz=x[:,None,2]-x[None,:,2]
        terms=w[:,None]*w[None,:]*np.exp(-(dx*dx+dy*dy+dz*dz)/.32)*(c[:,None]==c[None,:])
        sq=math.fsum(map(float,terms.ravel()));assert sq>=-1e-10;distance=math.sqrt(max(0,sq));maxdist=max(maxdist,distance);pairs+=1
        incompatible+=distance>1.2+1e-8
        if run['enabled']:assert distance<=1.2+1e-8
    if run['status']=='complete-awaiting-independent-replay':assert complete and len(owners)==len(poses)
    rows.append(dict(id=cid,enabled=run['enabled'],placements=len(owners),complete=complete,changedDecorationsFromSuppliedWitness=changed,checkedOverlapPairs=pairs,incompatiblePairsAtRadius06=incompatible,maxEndpointDistance=maxdist))
report=dict(sourceHashes={p.name:sha(p) for p in [libp,transferp,pairp,dictp,resultp]},verifierHash=sha(Path(__file__)),results=rows,limits='Independent selected integer t totals, inventory, fitting membership, known-pose identity and signed world-coordinate field checks. Relies on prior geometric-pose witnesses; not an independent verification of candidate-universe completeness, runtime scheduling, timings, full continuous registration or blind growth.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(rows),flush=True)
