"""Fit equality markings to selected training tilings, not all geometric candidates."""
import json
import hashlib
from pathlib import Path
import sys
from collections import defaultdict

raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);sraw=Path(sys.argv[2]).read_bytes();selection=json.loads(sraw)
chosen={r['id']:r for r in selection['results']};n=d['offsets'][-1];parent=list(range(n));observed=set()
sources=[chosen];selection_hashes=[hashlib.sha256(sraw).hexdigest()]
if len(sys.argv)>5:
    extra=Path(sys.argv[5]).read_bytes();sources.append({r['id']:r for r in json.loads(extra)['results']})
    selection_hashes.append(hashlib.sha256(extra).hexdigest())
def root(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for c in d['configurations']:
    if not c['training']:continue
    for source in sources:
        r=source[c['id']];assert r['status']=='connected positive finite cover';points=defaultdict(list)
        for index in r['selected']:
            o=c['occurrences'][index]
            for u,j in enumerate(o['permutation']):
                v=d['offsets'][o['type']]+u;points[o['ids'][j]].append(v);observed.add(v)
        assert len(points)==c['atoms']
        for group in points.values():
            for v in group[1:]:parent[root(v)]=root(group[0])
labels=[root(i) if i in observed else None for i in range(n)]
results=[]
for c in d['configurations']:
    points=defaultdict(list)
    for index in chosen[c['id']]['selected']:
        o=c['occurrences'][index]
        for u,j in enumerate(o['permutation']):
            value=labels[d['offsets'][o['type']]+u]
            if value is not None:points[o['ids'][j]].append(value)
    conflicts=sum(len(set(v))>1 for v in points.values())
    if c['training']:assert conflicts==0
    results.append({'id':c['id'],'training':c['training'],'conflictingPoints':conflicts})
out={'scope':__doc__,'dictionaryHash':hashlib.sha256(raw).hexdigest(),'selectionHash':hashlib.sha256(sraw).hexdigest(),
     'trainingSelectionHashes':selection_hashes,
     'labels':labels,'classes':len({x for x in labels if x is not None}),'unassignedSites':sum(x is None for x in labels),'results':results}
with Path(sys.argv[3]).open('x') as f:json.dump(out,f)
d['scalarLabels']=labels;d['scalarClasses']=out['classes'];d['selectedMarkingProvenance']={k:v for k,v in out.items() if k not in ('labels','results')}
with Path(sys.argv[4]).open('x') as f:json.dump(d,f)
print(json.dumps({k:v for k,v in out.items() if k not in ('labels','results')}))
print(json.dumps({'trainingConflictingPoints':sum(r['conflictingPoints'] for r in results if r['training']),
                  'testConflictingPoints':sum(r['conflictingPoints'] for r in results if not r['training'])}))
