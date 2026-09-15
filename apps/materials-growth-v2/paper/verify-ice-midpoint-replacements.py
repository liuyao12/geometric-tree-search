"""Independent all-substitution audit in world coordinates (floating point)."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

libp,transferp,pairp,checkp,resultp,out=map(Path,sys.argv[1:])
lib,transfer,pair,check,result=[json.loads(p.read_text()) for p in [libp,transferp,pairp,checkp,resultp]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p in [libp,transferp,pairp,checkp]:assert result['sourceHashes'][p.name]==sha(p)
assert check['resultHash']==sha(pairp)
radius=.6;assert result['summary']['radius']==radius
allowed={s['motif'] for r in lib['trainingRegistrations'] if r['id'] in transfer['fitFrames'] for s in r['selected']}
bybase=defaultdict(list);fields={};norms={}
def kernel_sum(a,b):
    x,w,c=a;y,v,d=b
    dx=x[:,None,0]-y[None,:,0];dy=x[:,None,1]-y[None,:,1];dz=x[:,None,2]-y[None,:,2]
    terms=w[:,None]*v[None,:]*np.exp(-(dx*dx+dy*dy+dz*dz)/.32)*(c[:,None]==d[None,:])
    return np.sum(terms,dtype=np.longdouble)
for i in sorted(allowed):
    bybase[lib['motifs'][i]['base']].append(i)
    for s,f in enumerate(lib['motifs'][i]['fieldM']):
        assert f['sigma']==.4
        fields[i,s]=(np.asarray(f['vectors']),np.asarray(f['amplitudes']),np.asarray(f['colors']))
        norms[i,s]=kernel_sum(fields[i,s],fields[i,s])
expected=[r for r in pair['results'] if r['midpointWitnessRadius']+1e-8<=radius]
assert [r['id'] for r in result['results']]==[r['id'] for r in expected]
rows=[]
for case,reported in zip(expected,result['results']):
    selected={s['edge']:s for s in case['selected']};inc=defaultdict(list);world={}
    for e,s in selected.items():
        for side,root in enumerate(s['roots']):inc[root].append((e,side))
        for i in bybase[lib['motifs'][s['motif']]['base']]:
            for side in [0,1]:
                x,w,c=fields[i,side];world[e,i,side]=(x@np.asarray(s['rotationRow']),w,c)
    assert all(len(v)==2 for v in inc.values())
    rejected=set();uncertain=set();tested=0;identities=0
    for e,s in selected.items():
        for i in bybase[lib['motifs'][s['motif']]['base']]:
            separated=False;boundary=False
            for side,root in enumerate(s['roots']):
                other,os=next(v for v in inc[root] if v[0]!=e);j=selected[other]['motif'];a=world[e,i,side];b=world[other,j,os]
                sq=norms[i,side]+norms[j,os]-2*kernel_sum(a,b)
                guard=1024*np.finfo(float).eps*max(1.,(sum(a[1])+sum(b[1]))**2)
                assert sq>=-guard;separated|=sq-guard>(2*radius)**2;boundary|=sq+guard>(2*radius)**2
            tested+=1
            if separated:rejected.add((e,i))
            elif boundary:uncertain.add((e,i))
            if i==s['motif']:assert not separated and not boundary;identities+=1
    assert rejected=={(v['edge'],v['motif']) for v in reported['exclusions']}
    assert uncertain=={(v['edge'],v['motif']) for v in reported['uncertain']}
    assert len(reported['exclusions'])==reported['rejected']==len(rejected)
    assert len(reported['uncertain'])==reported['unknown']==len(uncertain)
    assert reported['tested']==tested and reported['identitiesRetained']==identities
    row=dict(id=case['id'],tested=tested,rejected=len(rejected),unknown=len(uncertain),identitiesRetained=identities);rows.append(row);print(json.dumps(row),flush=True)
summary=dict(configurations=len(rows),**{k:sum(r[k] for r in rows) for k in ['tested','rejected','unknown','identitiesRetained']})
for k,v in summary.items():assert result['summary'][k]==v
report=dict(resultHash=sha(resultp),pairWitnessCheckHash=sha(checkp),verifierHash=sha(Path(__file__)),summary=summary,results=rows,limits='World-coordinate kernel evaluation with long-double summation and guarded comparisons, not an exact certificate. Verifies substitution identities/classifications, not stored distances or all-geometric negative connections. Radius chosen developmentally; no held-out or speedup claim.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(summary),flush=True)
