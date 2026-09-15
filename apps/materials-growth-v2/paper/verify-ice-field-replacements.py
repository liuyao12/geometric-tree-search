"""Independent all-replacement compatibility audit using nonnegative bounds.

Uses independently evaluated norms, reconstructs incidence without producer
helpers, and computes remaining cross kernels from world-coordinate component
differences. Proves compatibility numerically, not exact real arithmetic.
Does not replay or certify the producer's reported maximum distance.
"""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

cover_path,dictionary_path,library_path,transfer_path,replacement_path,norm_path,output=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cover,dictionary,library,transfer,replacement,normreport=[json.loads(p.read_text()) for p in [cover_path,dictionary_path,library_path,transfer_path,replacement_path,norm_path]]
for path in [cover_path,dictionary_path,library_path,transfer_path]:assert replacement['sourceHashes'][path.name]==sha(path)
assert normreport['libraryHash']==transfer['libraryHash']==sha(library_path) and normreport['transferHash']==sha(transfer_path)
cv={c['id']:c for c in cover['results']};dd={c['id']:c for c in dictionary['configurations']};reported={c['id']:c for c in replacement['results']}
allowed={p['motif'] for r in library['trainingRegistrations'] if r['id'] in transfer['fitFrames'] for p in r['selected']}
norms={(r['motif'],r['side']):r['upperSquaredNorm'] for r in normreport['norms']}
assert set(norms)=={(i,s) for i in allowed for s in [0,1]}
bybase=defaultdict(list);values={}
for i in sorted(allowed):
    motif=library['motifs'][i];bybase[motif['base']].append(i)
    for s,f in enumerate(motif['fieldM']):
        x=np.asarray(f['vectors']);a=np.asarray(f['amplitudes']);c=np.asarray(f['colors'])
        assert np.all(a>=0) and np.isfinite(x).all() and np.isfinite(a).all()
        values[i,s]=(x,a,c,f['sigma'])
bound=(2*transfer['summary']['diagnosticThreshold'])**2;rows=[]
for case in transfer['results']:
    if not case.get('complete',False):continue
    cid=case['id'];selected={w['edge']:w for w in case['matches']};incidence=defaultdict(list);ends={};world={}
    for edge,w in selected.items():
        o=dd[cid]['occurrences'][edge];site_atoms=[o['ids'][j] for j in o['permutation']]
        roots=sorted((sorted(j for j,a in enumerate(site_atoms) if a in cv[cid]['components'][root]),root) for root in cv[cid]['componentPairs'][edge])
        assert [r[0] for r in roots]==library['baseMotifs'][w['base']]['componentSites'];ends[edge]=roots
        R=np.asarray(o['rotationRow']);assert np.max(np.abs(R.T@R-np.eye(3)))<1e-10 and abs(np.linalg.det(R)-1)<1e-10
        for side,(_,root) in enumerate(roots):incidence[root].append((edge,side))
        for i in bybase[w['base']]:
            for side in [0,1]:
                v=values[i,side];world[edge,i,side]=(v[0]@R,v[1],v[2],v[3])
    assert all(len(items)==2 for items in incidence.values())
    fast=0;explicit=0;tested=0;maxupper=0.
    for edge,w in selected.items():
        for i in bybase[w['base']]:
            for side,(_,root) in enumerate(ends[edge]):
                other,os=next(x for x in incidence[root] if x[0]!=edge);j=selected[other]['motif']
                upper=norms[i,side]+norms[j,os]
                if upper<bound:fast+=1
                else:
                    x,a,c,sigma=world[edge,i,side];y,b,d,sigma2=world[other,j,os];assert sigma==sigma2
                    dx=x[:,None,0]-y[None,:,0];dy=x[:,None,1]-y[None,:,1];dz=x[:,None,2]-y[None,:,2]
                    terms=a[:,None]*b[None,:]*np.exp(-(dx*dx+dy*dy+dz*dz)/(2*sigma*sigma))*(c[:,None]==d[None,:])
                    cross=math.fsum(map(float,terms.ravel()))
                    guard=1024*np.finfo(float).eps*max(1.,(sum(a)+sum(b))**2)
                    upper=upper-2*cross+guard;explicit+=1
                assert upper<bound,(cid,edge,i,side,upper,bound)
                maxupper=max(maxupper,upper)
            tested+=1
    assert tested==reported[cid]['testedReplacementsIncludingIdentity'] and reported[cid]['rejected']==0 and reported[cid]['numericallyUnknown']==0
    row=dict(id=cid,replacementsVerifiedCompatible=tested,normBoundEndpoints=fast,explicitKernelEndpoints=explicit,maximumSquaredUpperBound=maxupper)
    rows.append(row);print(json.dumps(row),flush=True)
assert {r['id'] for r in rows}==set(reported)
summary=dict(configurations=len(rows),**{k:sum(r[k] for r in rows) for k in ['replacementsVerifiedCompatible','normBoundEndpoints','explicitKernelEndpoints']})
report=dict(scope=__doc__,sourceHashes={p.name:sha(p) for p in [cover_path,dictionary_path,library_path,transfer_path,replacement_path,norm_path]},
            verifierHash=sha(Path(__file__)),summary=summary,results=rows,
            limits='Complete numerical compatibility audit for this fixed-witness replacement set. Norm report is an independently computed dependency, not recomputed here. No maximum-distance, global-admissibility, geometry, physical-negative or arbitrary-rotation certificate.')
with output.open('x') as out:json.dump(report,out,indent=2)
print(json.dumps(summary),flush=True)
