"""Training-only witness acquisition targeting unconstrained template sites.

Require one occurrence containing a neglected role, then solve the declared
connected degree-two control. No validation geometry or outcomes select targets.
"""
import importlib.util
import json
from pathlib import Path
import sys
from collections import defaultdict
import networkx as nx

spec=importlib.util.spec_from_file_location('selection',Path(__file__).with_name('ice-thermal-selection.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads(Path(sys.argv[1]).read_text());cover=json.loads(Path(sys.argv[2]).read_text());prior=json.loads(Path(sys.argv[3]).read_text())
out=Path(sys.argv[4]);out.mkdir();byid={c['id']:c for c in cover['results']};g=nx.Graph()
for row in prior['equations']:g.add_edge(*row['sites'])
training=[c for c in d['configurations'] if c['training']];locations=defaultdict(list)
for c in training:
    for i,o in enumerate(c['occurrences']):
        if o['matched']:locations[o['type']].append((c,i))
attempted=set();trials=[];accepted=0
while True:
    forced=set().union(*(set(part) for part in nx.connected_components(g) if not nx.is_bipartite(g.subgraph(part))))
    unresolved=set(range(d['offsets'][-1]))-forced
    target_types=[i for i,(a,b) in enumerate(zip(d['offsets'],d['offsets'][1:])) if set(range(a,b))&unresolved]
    proposal=next(((ti,c,index) for ti in target_types for c,index in locations[ti] if (c['id'],index) not in attempted),None)
    if proposal is None or len(trials)>=200:break
    ti,c,index=proposal;attempted.add((c['id'],index));source=byid[c['id']];allowed=[i for i,o in enumerate(c['occurrences']) if o['matched']]
    r=m.select(source['components'],source['componentPairs'],allowed,2,5.,required=[allowed.index(index)])
    before=len(forced)
    if r['status']=='connected positive finite cover':
        assert index in r['selected'];rows=defaultdict(list)
        for j in r['selected']:
            o=c['occurrences'][j]
            for u,v in enumerate(o['permutation']):rows[o['ids'][v]].append(d['offsets'][o['type']]+u)
        assert len(rows)==c['atoms'] and all(len(v)==2 for v in rows.values())
        for a,b in rows.values():g.add_edge(a,b)
        accepted+=1
        artifact={'degreeHypothesis':2,'sharedWeight':'1/2','marked':False,'targetType':ti,'requiredOccurrence':index,
                  'results':[dict(id=c['id'],training=True,atoms=c['atoms'],proposals=len(allowed),**r)]}
        (out/f'witness-{accepted:03d}.json').write_text(json.dumps(artifact))
    trial={'configuration':c['id'],'targetType':ti,'requiredOccurrence':index,'status':r['status'],'previousForcedSites':before}
    trials.append(trial);print(json.dumps(trial),flush=True)
forced=set().union(*(set(part) for part in nx.connected_components(g) if not nx.is_bipartite(g.subgraph(part))))
summary={'attempts':len(trials),'acceptedWitnesses':accepted,'forcedSites':len(forced),'siteVariables':d['offsets'][-1],
 'unobservedSites':len(set(range(d['offsets'][-1]))-set(g)),'remainingNonForcedSites':d['offsets'][-1]-len(forced),
 'scope':__doc__,'trials':trials}
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='trials'}),flush=True)
