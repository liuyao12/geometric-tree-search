"""Audit compiled anchor incidence; not an independent geometric quantizer."""
from collections import defaultdict, Counter
from itertools import combinations
import hashlib
import json
import sys
from pathlib import Path

inp,learned,compiled,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];a=json.loads(compiled.read_text())
assert a['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert a['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
checks=[]
for fold,(cfg,assignments) in enumerate(zip(d['configurations'],a['anchorAssignments'],strict=True)):
    assert len(assignments)==len(cfg['occurrences'])
    at=defaultdict(list);selected=set(r['selected'][fold]);training=defaultdict(list);atoms=defaultdict(list);ts=[]
    for j,(o,anchors) in enumerate(zip(cfg['occurrences'],assignments)):
        assert len({tuple(p) for p,_ in anchors})==len(anchors)
        ts.append({p:r['weightsByRole'][r['roleOfSite'][d['types'][o['type']]['offset']+u]] for u,p in enumerate(o['ids'])})
        for p,value in anchors:
            assert len(p)==3 and all(type(v) is int and 0<=v<10**9 for v in p)
            at[tuple(p)].append((j,value))
            if j in selected:training[tuple(p)].append((j,value))
        if j in selected:
            for p in o['ids']:atoms[p].append(j)
    overlaps=Counter()
    for group in atoms.values():
        for pair in combinations(sorted(group),2):overlaps[pair]+=1
    conflicts=set()
    for group in at.values():
        for (i,x),(j,y) in combinations(group,2):
            if x!=y:conflicts.add(tuple(sorted((i,j))))
    surviving=[]
    for i,j in conflicts:
        if all(v+ts[j].get(p,0)<=r['capacity'] for p,v in ts[i].items()):surviving.append((i,j))
    assert all(len({value for _,value in group})==1 for group in training.values())
    shared=sum(len({j for j,_ in group})>1 for group in training.values())
    claimed=a['results'][fold]
    assert len(at)==claimed['distinctAnchors'] and len(conflicts)==claimed['markConflictingPairs']
    assert sorted(surviving)==list(map(tuple,claimed['compatibleConflicts']))
    checks.append({'file':cfg['file'],'compiledAnchors':len(at),'selectedInterclusterSharedAnchors':shared,
                   'maximumSelectedAtomOverlap':max(overlaps.values(),default=0),
                   'markConflictingPairs':len(conflicts),'conflictsNotAlreadyCapacityForbidden':len(surviving),
                   'trainingAgreement':True})
out={'scope':'Independent compiled-incidence and t-capacity audit; midpoint generation, geometric snapping and role-learning are not independently reconstructed here.',
     'compiledHash':hashlib.sha256(compiled.read_bytes()).hexdigest(),'checks':checks}
dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
