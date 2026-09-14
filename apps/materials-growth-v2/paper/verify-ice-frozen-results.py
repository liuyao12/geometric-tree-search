"""Independent point filling, marking and connectedness on frozen-validation runs."""
import hashlib
import json
from pathlib import Path
from collections import defaultdict,Counter
import sys
import networkx as nx

raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);result=json.loads(Path(sys.argv[2]).read_text())
meta={c['id']:c for c in json.loads(Path(sys.argv[3]).read_text())['configurations']};byid={c['id']:c for c in d['configurations']}
reference='kernelHash' in result
if reference:assert result['dictionaryHash']==hashlib.sha256(raw).hexdigest()
expected={(c['id'],m) for c in d['configurations'] for m in ((False,True) if reference else (False,))}
assert {(r['id'],r.get('marked',False)) for r in result['results']}==expected
groups=defaultdict(Counter)
for r in result['results']:
    c=byid[r['id']];assert not c['training'];totals=[0]*c['atoms'];g=nx.Graph();g.add_nodes_from(range(c['atoms']));marks={}
    assert len(set(r['selected']))==len(r['selected'])
    for index in r['selected']:
        o=c['occurrences'][int(index)];assert o['matched'] and o['type'] in d['admittedTypeIds'];ids=o['ids']
        for p in ids:totals[p]+=1
        g.add_edges_from((ids[0],p) for p in ids[1:])
        if r.get('marked',False):
            for u,j in enumerate(o['permutation']):
                p=ids[j];label=d['scalarLabels'][d['offsets'][o['type']]+u]
                if label is None:continue
                if p in marks:assert marks[p]==label
                marks[p]=label
    assert max(totals)<=2;complete=all(t==2 for t in totals);components=nx.number_connected_components(g)
    assert complete==(r['status'] in ('exact finite cover','connected positive finite cover'))
    if not reference and complete:assert components==1
    a=groups[(meta[c['id']]['phase'],r.get('marked',False))];a['runs']+=1;a['complete']+=int(complete);a['connectedComplete']+=int(complete and components==1)
    a['unknownOrIncomplete']+=int(not complete)
    if 'stats' in r:
        a['branches']+=r['stats']['branches'];a['backtracks']+=r['stats']['backtracks']
out={'source':'reference' if reference else 'connected-selection control','verifiedRuns':len(result['results']),
 'searchMode':result.get('mode','reference') if reference else 'connected-selection',
 'groups':[dict(phase=k[0],marked=k[1],**v) for k,v in groups.items()],
 'scope':'Remaining 300 author-validation frames, frozen admitted motifs. Finite supplied-coordinate reconstruction, not independent trajectories or blind growth.'}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
