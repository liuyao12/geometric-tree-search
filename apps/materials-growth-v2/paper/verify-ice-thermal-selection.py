"""Independent integer totals and positive-support connectivity for selected motifs."""
from collections import defaultdict,Counter
import json
from pathlib import Path
import sys
import networkx as nx
from fractions import Fraction

d=json.loads(Path(sys.argv[1]).read_text());s=json.loads(Path(sys.argv[2]).read_text())
meta={c['id']:c for c in json.loads(Path(sys.argv[3]).read_text())['configurations']}
byid={c['id']:c for c in d['configurations']};groups=defaultdict(Counter);verified=0
for r in s['results']:
    c=byid[r['id']];g=groups[(meta[r['id']]['phase'],'train' if r['training'] else 'test')];g['configurations']+=1
    g['candidateOccurrences']+=r['proposals']
    if r['status']!='connected positive finite cover':g[r['status']]+=1;continue
    assert len(set(r['selected']))==len(r['selected'])
    totals=[0]*c['atoms'];graph=nx.Graph();graph.add_nodes_from(range(c['atoms']));marks={}
    for index in r['selected']:
        o=c['occurrences'][index];assert o['matched'];ids=o['ids'];graph.add_edges_from((ids[0],p) for p in ids[1:])
        for p in ids:totals[p]+=1
        for u,j in enumerate(o['permutation']):
            p=ids[j];label=d['scalarLabels'][d['offsets'][o['type']]+u]
            if label is None:continue
            if p in marks:assert marks[p]==label
            marks[p]=label
    assert all(t==s['degreeHypothesis'] for t in totals) and nx.is_connected(graph)
    assert Fraction(s['sharedWeight'])*s['degreeHypothesis']==1
    g['verifiedConnectedCovers']+=1;g['exactlyFilledAtoms']+=c['atoms'];g['selectedMotifs']+=len(r['selected']);verified+=1
weights=[Fraction(x) for x in d['filling']['weights']]
zero_types=sum(all(w==0 for w in weights[a:b]) for a,b in zip(d['offsets'],d['offsets'][1:]))
out={'verifiedCovers':verified,'attemptedConfigurations':len(s['results']),'typeCount':d['typeCount'],
 'singletonTypes':d['singletonTypes'],'epsilonAngstrom':d['epsilonAngstrom'],'sharedPositiveWeight':s['sharedWeight'],
 'scalarClasses':d['scalarClasses'],'allOccurrenceFitZeroWeightSites':sum(w==0 for w in weights),
 'allOccurrenceFitTotalSites':len(weights),'allOccurrenceFitEmptyTypes':zero_types,
 'groups':[dict(phase=k[0],split=k[1],**v) for k,v in groups.items()],
 'scope':'Finite supplied-coordinate covers with a tested uniform-weight hypothesis. Specialized MILP, not reference tree search, learned t optimization, independent-trajectory validation or blind growth.'}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
