"""Exploratory fixed-witness decoration substitutions at radius 0.6.

Radius selected after the developmental pair-radius diagnostic; NOT calibrated
or held-out. Each candidate changes one decoration, not its geometry or t-values.
"""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial.distance import cdist

libp,transferp,pairp,checkp,out=map(Path,sys.argv[1:])
lib,transfer,pair,check=[json.loads(p.read_text()) for p in [libp,transferp,pairp,checkp]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert check['resultHash']==sha(pairp) and pair['sourceHashes'][libp.name]==sha(libp) and pair['sourceHashes'][transferp.name]==sha(transferp)
radius=.6;bound=(2*radius)**2
allowed={w['motif'] for r in lib['trainingRegistrations'] if r['id'] in transfer['fitFrames'] for w in r['selected']}
bybase=defaultdict(list);values={};norms={}
def inner(a,b):
    x,w,c,s=a;y,v,d,t=b;assert s==t
    return float(np.sum(w[:,None]*v[None,:]*np.exp(-cdist(x,y,'sqeuclidean')/(2*s*s))*(c[:,None]==d[None,:])))
for i in sorted(allowed):
    bybase[lib['motifs'][i]['base']].append(i)
    for side,f in enumerate(lib['motifs'][i]['fieldM']):
        a=np.asarray(f['vectors']),np.asarray(f['amplitudes']),np.asarray(f['colors']),f['sigma']
        values[i,side]=a;norms[i,side]=inner(a,a)
rows=[];start=time.monotonic()
for case in pair['results']:
    if case['midpointWitnessRadius']+1e-8>radius:continue
    selected={s['edge']:s for s in case['selected']};inc=defaultdict(list)
    for edge,s in selected.items():
        for side,root in enumerate(s['roots']):inc[root].append((edge,side))
    assert all(len(v)==2 for v in inc.values())
    tested=0;identities=0;rejected=[];unknown=[];maxdistance=0.
    for edge,s in selected.items():
        R=np.asarray(s['rotationRow']);partners=[]
        for side,root in enumerate(s['roots']):
            e,j=next(v for v in inc[root] if v[0]!=edge);other=selected[e];i=other['motif'];a=values[i,j]
            partners.append(((a[0]@np.asarray(other['rotationRow'])@R.T,a[1],a[2],a[3]),norms[i,j]))
        for i in bybase[lib['motifs'][s['motif']]['base']]:
            distances=[];separated=False;uncertain=False
            for side,(b,nn) in enumerate(partners):
                a=values[i,side];sq=math.fsum([norms[i,side],nn,-2*inner(a,b)])
                guard=1024*np.finfo(float).eps*max(1.,(sum(a[1])+sum(b[1]))**2);assert sq>=-guard
                separated|=sq-guard>bound;uncertain|=sq+guard>bound
                distances.append(math.sqrt(max(0.,sq)))
            tested+=1;maxdistance=max(maxdistance,*distances)
            if separated:rejected.append(dict(edge=edge,motif=i,distances=distances))
            elif uncertain:unknown.append(dict(edge=edge,motif=i,distances=distances))
            if i==s['motif']:assert not separated and not uncertain;identities+=1
    r=dict(id=case['id'],tested=tested,identitiesRetained=identities,rejected=len(rejected),unknown=len(unknown),maxDistance=maxdistance,exclusions=rejected,uncertain=unknown);rows.append(r)
    print(json.dumps({k:v for k,v in r.items() if k not in ['exclusions','uncertain']}),flush=True)
summary=dict(configurations=len(rows),radius=radius,**{k:sum(r[k] for r in rows) for k in ['tested','identitiesRetained','rejected','unknown']})
report=dict(scope=__doc__,sourceHashes={p.name:sha(p) for p in [libp,transferp,pairp,checkp]},codeHash=sha(Path(__file__)),summary=summary,results=rows,seconds=time.monotonic()-start,limits='Pending independent replacement audit. Fixed-pose one-decoration contexts only; not global negatives, geometry challenges, calibrated thresholds or search performance.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(summary),flush=True)
