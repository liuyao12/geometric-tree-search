"""Independent integer filling / marking / connectivity audit of reference runs."""
import hashlib
import json
from pathlib import Path
import sys
from collections import defaultdict,Counter
import networkx as nx

raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);r=json.loads(Path(sys.argv[2]).read_text())
assert r['dictionaryHash']==hashlib.sha256(raw).hexdigest()
meta={c['id']:c for c in json.loads(Path(sys.argv[3]).read_text())['configurations']}
byid={c['id']:c for c in d['configurations']};groups=defaultdict(Counter);total=0;connected=0
assert {(x['id'],x['marked']) for x in r['results']}=={(c['id'],m) for c in d['configurations'] if not c['training'] for m in (False,True)}
for run in r['results']:
    c=byid[run['id']];totals=[0]*c['atoms'];marks={};graph=nx.Graph();graph.add_nodes_from(range(c['atoms']))
    assert len(set(run['selected']))==len(run['selected'])
    for index in run['selected']:
        o=c['occurrences'][int(index)];assert o['matched'];ids=o['ids'];graph.add_edges_from((ids[0],p) for p in ids[1:])
        for p in ids:totals[p]+=1
        if run['marked']:
            for u,j in enumerate(o['permutation']):
                p=ids[j];label=d['scalarLabels'][d['offsets'][o['type']]+u]
                if p in marks:assert marks[p]==label
                marks[p]=label
    assert all(t<=2 for t in totals);complete=all(t==2 for t in totals);assert complete==(run['status']=='exact finite cover')
    count=nx.number_connected_components(graph);g=groups[(meta[run['id']]['phase'],run['marked'])];g['runs']+=1
    g['complete']+=int(complete);g['connectedComplete']+=int(complete and count==1)
    g['positiveComponentsTotal']+=count;g['branches']+=run['stats']['branches'];g['backtracks']+=run['stats']['backtracks']
    total+=int(complete);connected+=int(complete and count==1)
out={'runs':len(r['results']),'verifiedFiniteCovers':total,'connectedFiniteCovers':connected,
 'groups':[dict(phase=k[0],marked=k[1],**v) for k,v in groups.items()],
 'scope':r['scope'],'kernelHash':r['kernelHash']}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
