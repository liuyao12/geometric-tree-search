"""Independent union-find, pose, variant, filling and conflict-graph checks."""
import hashlib
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import numpy as np

inp,learned,compiled,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];out=json.loads(compiled.read_text())
assert out['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert out['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
n=sum(len(t['positions']) for t in d['types']);parent=list(range(n))
def root(p):
    while parent[p]!=p:p=parent[p]
    return p
def union(a,b):parent[root(a)]=root(b)
for cfg,chosen in zip(d['configurations'],r['selected']):
    at=defaultdict(list)
    for j in chosen:
        o=cfg['occurrences'][j]
        for u,p in enumerate(o['ids']):at[p].append(d['types'][o['type']]['offset']+u)
    for group in at.values():
        for v in group[1:]:union(group[0],v)
labels=out['siteLabels']
assert len(labels)==n
assert all((root(a)==root(b))==(labels[a]==labels[b]) for a in range(n) for b in range(n))
site_classes=len({root(i) for i in range(n)})
poses=0;maximum=0
for t in d['types']:
    pos=np.array(t['positions'])
    for fit in t['selfFits']:
        perm=fit['permutation'];rot=np.array(fit['rotationRow']);shift=np.array(fit['translation'])
        assert sorted(perm)==list(range(len(pos)))
        assert np.max(np.abs(rot.T@rot-np.eye(3)))<1e-8 and abs(np.linalg.det(rot)-1)<1e-8
        error=float(np.linalg.norm(pos@rot+shift-pos[perm],axis=1).max())
        assert error<=d['epsilonAngstrom']+1e-8
        maximum=max(maximum,error);poses+=1
    for a,b in t['ties']:union(t['offset']+a,t['offset']+b)
old=[r['scalarLabelsByRole'][q] for q in r['roleOfSite']]
assert all((root(a)==root(b))==(old[a]==old[b]) for a in range(n) for b in range(n))
def conflicts(candidates):
    at=defaultdict(list)
    for c in candidates:
        for x in c['m']:at[x['point']].append((c['id'],x['lo']))
    return {tuple(sorted((a[0],b[0]))) for group in at.values() for a,b in combinations(group,2) if a[1]!=b[1]}
checks=[]
for fold,(cfg,model) in enumerate(zip(d['configurations'],out['models'],strict=True)):
    assert model['capacity']==r['capacity'] and model['required']==[str(p) for p in range(cfg['atoms'])]
    expected_base=[];expected_decorations=defaultdict(set);original=[]
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']];off=typ['offset'];count=len(o['ids'])
        t=[{'point':str(p),'value':r['weightsByRole'][r['roleOfSite'][off+u]]} for u,p in enumerate(o['ids'])]
        base={'id':str(j).zfill(6),'t':t,'m':[]};expected_base.append(base)
        original.append({**base,'m':[{'point':str(p),'lo':old[off+u]} for u,p in enumerate(o['ids'])]})
        perms=[list(range(count))]+[w['permutation'] for w in typ['selfFits']]
        if typ['kind']!='finite-face':perms.append([1,0])
        for perm in perms:expected_decorations[j].add(tuple(sorted((str(o['ids'][v]),labels[off+u]) for u,v in enumerate(perm))))
    assert model['unmarked']==expected_base
    actual=defaultdict(set)
    for c in model['marked']:
        j=int(c['id'].split(':')[0]);assert c['t']==expected_base[j]['t']
        assert all(x['lo']==x['hi'] for x in c['m'])
        key=tuple(sorted((x['point'],x['lo']) for x in c['m']))
        assert key not in actual[j];actual[j].add(key)
    assert dict(actual)==dict(expected_decorations)
    byid={c['id']:c for c in model['marked']};assert len(byid)==len(model['marked'])
    totals=defaultdict(int);marks={}
    selected=model['trainingSelected'];assert len(set(selected))==len(selected)
    assert {int(i.split(':')[0]) for i in selected}==set(r['selected'][fold])
    for cid in selected:
        c=byid[cid]
        for x in c['t']:totals[x['point']]+=x['value']
        for x in c['m']:
            if x['point'] in marks:assert marks[x['point']]==x['lo']
            marks[x['point']]=x['lo']
    assert all(totals[p]==r['capacity'] for p in model['required'])
    before=conflicts(original);after=conflicts(model['marked'])
    bijective=all(len(v)==1 for v in actual.values())
    same=bijective and before=={tuple(x.split(':')[0] for x in pair) for pair in after}
    checks.append({'file':cfg['file'],'physicalCandidates':len(expected_base),'decoratedCandidates':len(model['marked']),
                   'oldConflictingPairs':len(before),'newConflictingPairs':len(after),
                   'oneVariantPerPhysicalCandidate':bijective,'identicalPartialLegalityAfterProjection':same,
                   'trainingFillingVerified':True})
result={'scope':'Witnessed self-pose pool only; proper-registration residuals numerical, atom-ID filling exact. Hard-model conflict equality proves unchanged partial legality, not complete continuous poses.',
        'compiledHash':hashlib.sha256(compiled.read_bytes()).hexdigest(),'siteVariables':n,'siteClasses':site_classes,
        'tiedClasses':len({root(i) for i in range(n)}),'selfPoseWitnessesChecked':poses,'maximumSelfPoseResidual':maximum,'checks':checks}
dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
