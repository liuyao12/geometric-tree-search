"""Independent graph traversal check of frozen scalar equality classes."""
import hashlib
import json
from pathlib import Path
import sys

raw=Path(sys.argv[1]).read_bytes();data=json.loads(raw)
test_raw=Path(sys.argv[2]).read_bytes();test=json.loads(test_raw)
report=json.loads(Path(sys.argv[3]).read_text())
assert hashlib.sha256(raw).hexdigest()==report['trainingDictionaryHash']
assert hashlib.sha256(test_raw).hexdigest()==report['testDictionaryHash']
n=9*len(data['types']);adj=[set() for _ in range(n)]
def groups(f):
    points={}
    for o in f['occurrences']:
        assert o['matched']
        for u,j in enumerate(o['permutation']):points.setdefault(o['ids'][j],[]).append(9*o['type']+u)
    return points
for f in data['configurations']:
    if not f['training']:continue
    for g in groups(f).values():
        for a in g:adj[a].update(g)
labels=[None]*n;count=0
for p in range(n):
    if labels[p] is not None:continue
    todo=[p]
    while todo:
        a=todo.pop()
        if labels[a] is not None:continue
        labels[a]=count;todo.extend(adj[a])
    count+=1
species=[s for t in data['types'] for s in t['species']]
for a in range(n):
    for b in range(n):
        assert (labels[a]==labels[b])==(report['labels'][a]==report['labels'][b])
        assert (labels[a]==labels[b])==(species[a]==species[b])
for f in test['configurations']:
    assert all(len({labels[v] for v in g})==1 for g in groups(f).values())
assert count==report['summary']['classes']==2
print({'independentlyVerifiedVariables':n,'classes':count,'speciesOnly':True,'testConfigurations':len(test['configurations'])})
