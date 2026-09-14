"""Proposed geometric pair-midpoint m-domain on the fixed observed torus.

Anchors are proposed, not freely learned. Scalar labels are trained on selected
fillings. Fractional coordinates snapped at 1e-9 define this finite identity
control; it is not tolerance-complete continuous-space matching.
"""
from collections import defaultdict
from itertools import combinations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

inp,learned,folder,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result']
pairs=[];offsets=[];n=0
for t in d['types']:
    q=list(combinations(range(len(t['positions'])),2));offsets.append(n);n+=len(q);pairs.append(q)
parent=list(range(n))
def root(a):
    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
    return a
def merge(group):
    if group:
        for a in group[1:]:parent[root(a)]=root(group[0])
for k,t in enumerate(d['types']):
    index={pair:j for j,pair in enumerate(pairs[k])}
    for w in t['selfFits']:
        perm=w['permutation']
        for j,(a,b) in enumerate(pairs[k]):merge([offsets[k]+j,offsets[k]+index[tuple(sorted((perm[a],perm[b])))]] )
records=[];shared=[0]*n
for fold,cfg in enumerate(d['configurations']):
    raw=(folder/f'{fold}-1.15-3.json').read_bytes();src=json.loads(raw)
    assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
    positions=np.array(src['positions']);cell=np.array(src['cell']);inverse=np.linalg.inv(cell)
    candidates=[];selected=set(r['selected'][fold]);training=defaultdict(list)
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']]
        if typ['kind']=='finite-face':
            component=src['components'][o['component']]
            lift=dict(zip(component['ids'],component['imageOffsets']))
            xyz=np.array([positions[p]+np.array(lift[p])@cell for p in o['ids']])
        else:xyz=np.array([positions[o['ids'][0]],positions[o['ids'][1]]+np.array(o['imageShift'])@cell])
        anchors=defaultdict(list)
        for u,(a,b) in enumerate(pairs[o['type']]):
            frac=((xyz[a]+xyz[b])/2)@inverse
            key=tuple((np.rint((frac%1)*1_000_000_000).astype(np.int64)%1_000_000_000).tolist())
            anchors[key].append(offsets[o['type']]+u)
        for roles in anchors.values():merge(roles) # a marking must be single-valued inside a candidate
        candidates.append(anchors)
        if j in selected:
            for key,roles in anchors.items():training[key].append((j,roles))
    for group in training.values():
        roles=[v for _,vs in group for v in vs];merge(roles)
        if len(group)>1:
            for v in roles:shared[v]+=1
    records.append(candidates)
labels=[root(j) for j in range(n)];results=[];compiled=[]
for fold,(cfg,candidates) in enumerate(zip(d['configurations'],records)):
    at=defaultdict(list);training=defaultdict(set);selected=set(r['selected'][fold]);tvalues=[]
    for j,(o,anchors) in enumerate(zip(cfg['occurrences'],candidates)):
        tvalues.append({p:r['weightsByRole'][r['roleOfSite'][d['types'][o['type']]['offset']+u]] for u,p in enumerate(o['ids'])})
        for key,roles in anchors.items():
            values={labels[v] for v in roles};assert len(values)==1
            value=next(iter(values));at[key].append((j,value))
            if j in selected:training[key].add(value)
    assert all(len(v)==1 for v in training.values())
    conflicts=set()
    for group in at.values():
        for (a,x),(b,y) in combinations(group,2):
            if x!=y:conflicts.add((min(a,b),max(a,b)))
    compatible=[(a,b) for a,b in conflicts if all(w+tvalues[b].get(p,0)<=r['capacity'] for p,w in tvalues[a].items())]
    summary={'fold':fold,'file':cfg['file'],'distinctAnchors':len(at),'markConflictingPairs':len(conflicts),
             'globallyCapacityCompatibleConflicts':len(compatible),'trainingMarkAgreement':True,
             'compatibleConflicts':sorted(compatible)}
    results.append(summary);print(json.dumps({k:v for k,v in summary.items() if k!='compatibleConflicts'}),flush=True)
    compiled.append([[[list(key),labels[roles[0]]] for key,roles in anchors.items()] for anchors in candidates])
out={'scope':__doc__,'inputHash':hashlib.sha256(inp.read_bytes()).hexdigest(),'learningHash':hashlib.sha256(learned.read_bytes()).hexdigest(),
     'anchorVariables':n,'labelClasses':len(set(labels)),'neverSharedTrainingVariables':sum(v==0 for v in shared),
     'labels':labels,'results':results,'anchorAssignments':compiled}
dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('anchorVariables','labelClasses','neverSharedTrainingVariables')}))
