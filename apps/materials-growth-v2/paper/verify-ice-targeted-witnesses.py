"""Independent exact positive-cover and target-incidence audit of acquired witnesses."""
import json
from pathlib import Path
import sys
import networkx as nx

d=json.loads(Path(sys.argv[1]).read_text());byid={c['id']:c for c in d['configurations']}
folder=Path(sys.argv[2]);summary=json.loads((folder/'summary.json').read_text());count=0;atom_total=0
for path in sorted(folder.glob('witness-*.json')):
    a=json.loads(path.read_text());assert a['degreeHypothesis']==2 and a['sharedWeight']=='1/2';assert len(a['results'])==1
    r=a['results'][0];c=byid[r['id']];assert c['training'] and r['training'] and r['status']=='connected positive finite cover'
    selected=r['selected'];assert len(set(selected))==len(selected) and a['requiredOccurrence'] in selected
    assert c['occurrences'][a['requiredOccurrence']]['type']==a['targetType']
    totals=[0]*c['atoms'];g=nx.Graph();g.add_nodes_from(range(c['atoms']))
    for index in selected:
        o=c['occurrences'][index];assert o['matched'];ids=o['ids'];assert len(set(ids))==len(ids)
        for p in ids:totals[p]+=1
        g.add_edges_from((ids[0],p) for p in ids[1:])
    assert all(x==2 for x in totals) and nx.is_connected(g)
    count+=1;atom_total+=len(totals)
assert count==summary['acceptedWitnesses']
out={'verifiedTrainingWitnesses':count,'verifiedAtomIncidencesAcrossWitnesses':atom_total,
     'allRequestedOccurrencesIncluded':True,'allPositiveCoversConnected':True,'validationUsed':False,
     'scope':'Targeted degree-two finite training witnesses; not unrestricted occurrence/weight inference.'}
with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
