"""Generate alternative connected half-weight covers of unchanged training atoms.

Deterministic two-edge swaps use only matched observed pair supports. They preserve
degree two, are accepted only if connected, and never consult learned m-values.
This is a specialized decomposition control, not reference GCTS tree search.
"""
import hashlib
import json
from pathlib import Path
import random
import sys

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
cover_path,dictionary_path,selection_path,output=sys.argv[1:]
cover,dictionary,selection=[json.loads(Path(p).read_text()) for p in [cover_path,dictionary_path,selection_path]]
assert dictionary['coverHash']==sha(cover_path)
cv={r['id']:r for r in cover['results']};ss={r['id']:r for r in selection['results']}
results=[]
for d in dictionary['configurations']:
    if not d['training']:continue
    cid=d['id'];c=cv[cid];pairs=c['componentPairs'];n=len(c['components'])
    edge_of={tuple(sorted(pair)):i for i,pair in enumerate(pairs) if d['occurrences'][i]['matched']}
    assert len(edge_of)==sum(o['matched'] for o in d['occurrences'])
    initial=set(ss[cid]['selected']);chosen=set(initial)
    seed=int(hashlib.sha256(cid.encode()).hexdigest()[:16],16);rng=random.Random(seed)
    def valid(edges):
        adjacency=[set() for _ in range(n)]
        for e in edges:
            a,b=pairs[e];adjacency[a].add(b);adjacency[b].add(a)
        if any(len(row)!=2 for row in adjacency):return False
        seen={0};todo=[0]
        while todo:
            for v in adjacency[todo.pop()]-seen:seen.add(v);todo.append(v)
        return len(seen)==n
    assert valid(chosen)
    swaps=[]
    for attempt in range(20*n):
        e,f=rng.sample(sorted(chosen),2);a,b=pairs[e];u,v=pairs[f]
        if len({a,b,u,v})!=4:continue
        if rng.randrange(2):u,v=v,u
        g=edge_of.get(tuple(sorted((a,u))));h=edge_of.get(tuple(sorted((b,v))))
        if g is None or h is None or g in chosen or h in chosen:continue
        proposed=(chosen-{e,f})|{g,h}
        if valid(proposed):
            chosen=proposed;swaps.append(dict(remove=[e,f],add=[g,h]))
    # Verify the actual atom-level t sum, not just the component graph.
    totals=[0]*d['atoms']
    for e in chosen:
        assert d['occurrences'][e]['matched']
        for atom in d['occurrences'][e]['ids']:totals[atom]+=1
    assert all(t==2 for t in totals)
    row=dict(id=cid,training=True,selected=sorted(chosen),swaps=swaps,seed=seed,
             acceptedSwaps=len(swaps),differentEdges=len(chosen-initial),unchanged=chosen==initial,
             status='connected positive finite cover',atoms=d['atoms'])
    results.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ['selected','swaps']}),flush=True)
data=dict(scope=__doc__,coverHash=sha(cover_path),dictionaryHash=sha(dictionary_path),originalSelectionHash=sha(selection_path),
          codeHash=sha(__file__),results=results,summary=dict(configurations=len(results),changed=sum(not r['unchanged'] for r in results),
          totalDifferentEdges=sum(r['differentEdges'] for r in results)),
          limits='Same coordinates and existing matched supports; t-valid decomposition alternatives are not certified compatible with the original learned markings or a physical formation mechanism.')
with Path(output).open('x') as f:json.dump(data,f)
print(json.dumps(data['summary']),flush=True)
