"""Independent compiled-domain, equality, filling and geometric-residual audit."""
from collections import defaultdict
from itertools import combinations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

inp,learned,folder,proposalpath,compiled,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];h=json.loads(proposalpath.read_text());a=json.loads(compiled.read_text())
assert a['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest() and a['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
assert a['proposalsHash']==hashlib.sha256(proposalpath.read_bytes()).hexdigest()
offsets=[];n=len(r['weightsByRole'])
for typ in h['types']:offsets.append(n);n+=len(typ.get('anchors',[]))
parent=list(range(n))
def root(v):
    while parent[v]!=v:v=parent[v]
    return v
def union(group):
    for v in group[1:]:parent[root(v)]=root(group[0])
def conflicts(candidates,channel):
    at=defaultdict(list)
    for c in candidates:
        for x in c['m']:
            if x['channel']==channel:at[x['point']].append((c['id'],x['lo']))
    return {tuple(sorted((i,j))) for group in at.values() for (i,x),(j,y) in combinations(group,2) if i!=j and x!=y}
checks=[]
for fold,(cfg,model) in enumerate(zip(d['configurations'],a['models'],strict=True)):
    raw=(folder/f'{fold}-1.15-3.json').read_bytes();src=json.loads(raw);assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
    cell=np.array(src['cell']);pos=np.array(src['positions']);inverse=np.linalg.inv(cell);g=model['geometryWitness']
    assert np.array_equal(cell,np.array(g['cell']))
    fractions=np.array(g['fractionalPoints']);identities=g['identityOfPoint'];reps=g['representatives'];eps=a['epsilonAngstrom']
    assert len(fractions)==len(identities)
    for p,pid in enumerate(identities):
        ref=reps[pid];assert identities[ref]==pid
        delta=fractions[p]-fractions[ref];delta-=np.round(delta);assert np.linalg.norm(delta@cell)<=eps+1e-8
    delta=fractions[:cfg['atoms']]-(pos@inverse)%1;delta-=np.round(delta);assert np.max(np.abs(delta))<1e-10
    assert identities[:cfg['atoms']]==[str(p) for p in range(cfg['atoms'])]
    cursor=cfg['atoms'];training=defaultdict(list);selected=set(model['trainingSelected']);ts={}
    assert selected=={str(j).zfill(6) for j in r['selected'][fold]}
    assert model['required']==[str(p) for p in range(cfg['atoms'])] and model['capacity']==r['capacity']
    for j,(o,c,domain) in enumerate(zip(cfg['occurrences'],model['candidates'],model['haloDomains'],strict=True)):
        assert c['id']==str(j).zfill(6);typ=d['types'][o['type']];local=defaultdict(set)
        expected_t=[];old=[]
        for u,p in enumerate(o['ids']):
            role=r['roleOfSite'][typ['offset']+u];local[str(p)].add(role)
            expected_t.append({'point':str(p),'value':r['weightsByRole'][role]})
            old.append({'point':str(p),'channel':'0','lo':r['scalarLabelsByRole'][role],'hi':r['scalarLabelsByRole'][role]})
        anchors=h['types'][o['type']].get('anchors',[])
        if anchors:
            comp=src['components'][o['component']];shifts=dict(zip(comp['ids'],comp['imageOffsets']))
            x=np.array([pos[p]+np.array(shifts[p])@cell for p in o['ids']]);p=np.array(typ['positions']);pc=p.mean(0);xc=x.mean(0)
            rot,_=Rotation.align_vectors(x-xc,p-pc)
            for u,anchor in enumerate(anchors):
                expected=(rot.apply(np.array(anchor['position'])-pc)+xc)@inverse
                delta=fractions[cursor]-expected;delta-=np.round(delta);assert np.linalg.norm(delta@cell)<1e-8
                local[identities[cursor]].add(offsets[o['type']]+u);cursor+=1
        assert sorted((p,v) for p,vs in local.items() for v in vs)==sorted(map(tuple,domain))
        for values in local.values():union(list(values))
        if c['id'] in selected:
            for p,vs in local.items():training[p].extend(vs)
        assert c['t']==expected_t and [x for x in c['m'] if x['channel']=='0']==old
        expected_halo={p:a['labels'][next(iter(vs))] for p,vs in local.items()}
        assert all(len({a['labels'][v] for v in vs})==1 for vs in local.values())
        actual={x['point']:x['lo'] for x in c['m'] if x['channel']=='halo'}
        assert actual==expected_halo and all(x['lo']==x['hi'] for x in c['m'])
        ts[c['id']]={x['point']:x['value'] for x in c['t']}
    assert cursor==len(fractions),'halo locations dropped or inserted'
    for values in training.values():union(values)
    totals=defaultdict(int);marks={}
    for c in model['candidates']:
        if c['id'] not in selected:continue
        for p,w in ts[c['id']].items():totals[p]+=w
        for x in c['m']:
            key=(x['point'],x['channel'])
            if key in marks:assert marks[key]==x['lo']
            marks[key]=x['lo']
    assert all(totals[p]==r['capacity'] for p in model['required'])
    oldbad=conflicts(model['candidates'],'0');newbad=conflicts(model['candidates'],'halo')
    added=[(i,j) for i,j in newbad-oldbad if all(w+ts[j].get(p,0)<=r['capacity'] for p,w in ts[i].items())]
    checks.append({'file':cfg['file'],'trainingFillingVerified':True,'haloConflictingPairs':len(newbad),
                   'newCapacityCompatibleConflictPairs':len(added),'newConflictPairs':sorted(added),**model['geometryAudit']})
assert n==a['variables'] and len(a['labels'])==n
assert all((root(i)==root(j))==(a['labels'][i]==a['labels'][j]) for i in range(n) for j in range(n))
out={'scope':__doc__,'compiledHash':hashlib.sha256(compiled.read_bytes()).hexdigest(),'variables':n,'classes':len({root(i) for i in range(n)}),'checks':checks}
dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({**out,'checks':[{k:v for k,v in row.items() if k!='newConflictPairs'} for row in checks]},indent=2))
