"""Rebuild training equality graphs independently; missing sites are unconstrained."""
import hashlib
import json
from pathlib import Path
import sys
from collections import defaultdict,Counter
import networkx as nx

raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);m=json.loads(Path(sys.argv[2]).read_text())
assert hashlib.sha256(raw).hexdigest()==m['dictionaryHash']
meta={c['id']:c for c in json.loads(Path(sys.argv[3]).read_text())['configurations']}
selections=[];hashes=[]
for path in sys.argv[5:]:
    r=Path(path).read_bytes();selections.append({x['id']:x for x in json.loads(r)['results']});hashes.append(hashlib.sha256(r).hexdigest())
assert hashes==m.get('trainingSelectionHashes',[m['selectionHash']])
g=nx.Graph();observed=set()
for c in d['configurations']:
    if not c['training']:continue
    for source in selections:
        points=defaultdict(list)
        for i in source[c['id']]['selected']:
            o=c['occurrences'][i]
            for u,j in enumerate(o['permutation']):points[o['ids'][j]].append(d['offsets'][o['type']]+u)
        for values in points.values():g.add_nodes_from(values);g.add_edges_from((values[0],v) for v in values[1:]);observed.update(values)
parts=list(nx.connected_components(g));labels=m['labels'];used=set()
for part in parts:
    values={labels[v] for v in part};assert len(values)==1 and None not in values and not(used&values);used.update(values)
assert all((labels[i] is not None)==(i in observed) for i in range(len(labels)))
assert len(parts)==m['classes'] and len(labels)-len(observed)==m['unassignedSites']
groups=defaultdict(Counter)
for c in d['configurations']:
    points=defaultdict(list)
    for i in selections[0][c['id']]['selected']:
        o=c['occurrences'][i]
        for u,j in enumerate(o['permutation']):
            label=labels[d['offsets'][o['type']]+u]
            if label is not None:points[o['ids'][j]].append(label)
    conflicts=sum(len(set(v))>1 for v in points.values());r=next(r for r in m['results'] if r['id']==c['id']);assert conflicts==r['conflictingPoints']
    if c['training']:assert conflicts==0
    a=groups[(meta[c['id']]['phase'],'train' if c['training'] else 'test')];a['configurations']+=1;a['conflictingPoints']+=conflicts;a['coversWithConflicts']+=int(conflicts>0)
out={'verifiedTrainingWitnessSets':len(selections),'classes':len(parts),'unassignedSites':m['unassignedSites'],
 'classSizes':sorted(map(len,parts),reverse=True),'groups':[dict(phase=k[0],split=k[1],**v) for k,v in groups.items()],
 'scope':'Selected-cover scalar equalities; validation uses first selected cover only, not existential reconstruction or independent-trajectory generalization.'}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
