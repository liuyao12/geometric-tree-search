"""Independently replay binary variants and exact physical point totals."""
import hashlib
import json
from pathlib import Path
from collections import Counter,defaultdict
import sys
import networkx as nx
raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);mr=Path(sys.argv[2]).read_bytes();m=json.loads(mr);r=json.loads(Path(sys.argv[3]).read_text())
assert r['dictionaryHash']==hashlib.sha256(raw).hexdigest() and r['markingHash']==hashlib.sha256(mr).hexdigest()
meta={c['id']:c for c in json.loads(Path(sys.argv[4]).read_text())['configurations']};byid={c['id']:c for c in d['configurations']};groups=defaultdict(Counter)
assert {c['id'] for c in r['results']}==set(byid) and len(r['results'])==len(byid)
for run in r['results']:
    c=byid[run['id']];totals=[0]*c['atoms'];marks={};used=set();g=nx.Graph();g.add_nodes_from(range(c['atoms']));parity=defaultdict(list)
    for identifier in run['selected']:
        fields=list(map(int,identifier.split(':')));index=fields[0];flip=fields[1] if len(fields)==2 else None
        if r.get('mode','expanded')=='expanded':assert flip in (0,1)
        else:assert len(fields)==1
        assert index not in used;used.add(index)
        o=c['occurrences'][index];assert o['matched'];ids=o['ids'];bits=m['ports'][str(o['type'])]
        for p in ids:totals[p]+=1
        g.add_edges_from((ids[0],p) for p in ids[1:])
        entries=[(ids[j],bits[u]*m['contrasts'][str(o['type'])]) for u,j in enumerate(o['permutation'])]
        for p,bit in entries:
            a,b=entries[0];parity[a].append((p,b^bit));parity[p].append((a,b^bit))
            if flip is not None:
                v=flip^bit
                if p in marks:assert marks[p]==v
                marks[p]=v
    coloring={}
    for root in parity:
        if root in coloring:continue
        coloring[root]=0;queue=[root]
        for a in queue:
            for b,bit in parity[a]:
                if b not in coloring:coloring[b]=coloring[a]^bit;queue.append(b)
                else:assert coloring[b]==coloring[a]^bit
    assert max(totals)<=2;complete=all(v==2 for v in totals);assert complete==(run['status']=='exact finite cover')
    a=groups[meta[c['id']]['phase']];a['runs']+=1;a['complete']+=int(complete);a['connectedComplete']+=int(complete and nx.is_connected(g))
    a['unknownOrIncomplete']+=int(not complete);a['branches']+=run['stats']['branches'];a['backtracks']+=run['stats']['backtracks']
out={'mode':r.get('mode','expanded'),'groups':[dict(phase=k,**v) for k,v in groups.items()],'verifiedRuns':len(r['results']),'scope':r['scope']}
with Path(sys.argv[5]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
