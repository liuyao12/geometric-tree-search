"""Periodic-locked variant of joint training; not a blind growth algorithm.

Use integer image lifts to group translated occurrences, retaining type and
symmetry-tied site roles. Select complete primitive-cell translation orbits.
The compact training solution is expanded to all original supercell occurrences
and checked there. This is a restricted learning hypothesis, not general search.
"""
from collections import defaultdict
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import networkx as nx
spec=importlib.util.spec_from_file_location('joint',Path(__file__).with_name('boron-face-joint-selection.py'))
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)

def compact(d,folder):
    compact=copy.deepcopy(d);role=j.roles(d);orbit_lists=[];summaries=[]
    for c,small in zip(d['configurations'],compact['configurations']):
        raw=(Path(folder)/f"{c['fold']}-1.15-3.json").read_bytes();src=json.loads(raw)
        assert hashlib.sha256(raw).hexdigest()==c['sourceHash']
        assert c['atoms']%27==0;n=c['atoms']//27;orbits=defaultdict(list)
        for oi,o in enumerate(c['occurrences']):
            t=d['types'][o['type']]
            if t['kind']=='finite-face':
                g=src['components'][o['component']];shifts=dict(zip(g['ids'],g['imageOffsets']))
                lifts=[np.array(shifts[p]) for p in o['ids']]
            else:lifts=[np.zeros(3,dtype=int),np.array(o['imageShift'])]
            images=[tuple((np.array(np.unravel_index(p//n,(3,3,3)))+3*s).tolist()) for p,s in zip(o['ids'],lifts)]
            anchor=np.array(min(images));key=(o['type'],tuple(sorted((p%n,role[t['offset']+u],tuple((np.array(image)-anchor).tolist()))
                for u,(p,image) in enumerate(zip(o['ids'],images)))))
            orbits[key].append(oi)
        assert all(len(group)==27 for group in orbits.values()),'Translation orbits did not have the expected multiplicity'
        groups=list(orbits.values());orbit_lists.append(groups);small['atoms']=n
        small['occurrences']=[{**c['occurrences'][group[0]],'ids':[p%n for p in c['occurrences'][group[0]]['ids']]} for group in groups]
        summaries.append({'file':c['file'],'originalOccurrences':len(c['occurrences']),'translationOrbits':len(groups)})
    return compact,orbit_lists,summaries

if __name__=='__main__':
    raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw)
    small,orbits,summaries=compact(d,sys.argv[2]);print(json.dumps(summaries),flush=True)
    capacity=int(sys.argv[4]) if len(sys.argv)>4 else 12;seconds=float(sys.argv[5]) if len(sys.argv)>5 else 30
    connected=len(sys.argv)>6 and sys.argv[6]=='connected';cuts=set();attempts=[]
    for iteration in range(12 if connected else 1):
        r=j.train(small,capacity,seconds,sorted(cuts))
        if 'selected' in r:
            selected=[sorted(i for o in chosen for i in groups[o]) for chosen,groups in zip(r['selected'],orbits)]
            r.update(j.evaluate(d,r['roleOfSite'],r['weightsByRole'],selected,r['capacity']))
        attempts.append({'iteration':iteration,'connectivityCuts':len(cuts),'seconds':r['seconds'],'status':r['status'],
                         'components':[c['positiveComponents'] for c in r.get('checks',[])]})
        print(json.dumps(attempts[-1]),flush=True)
        if not connected or 'selected' not in r or all(c['positiveComponents']==1 for c in r['checks']):break
        for ci,(c,selected,groups) in enumerate(zip(d['configurations'],r['selected'],orbits)):
            graph=nx.Graph();graph.add_nodes_from(range(c['atoms']))
            for oi in selected:
                ids=c['occurrences'][oi]['ids'];graph.add_edges_from((ids[0],p) for p in ids[1:])
            parts=list(nx.connected_components(graph))
            if len(parts)==1:continue
            memberships={p:k for k,part in enumerate(parts) for p in part};crossings=[set() for _ in parts]
            for oi,group in enumerate(groups):
                for original in group:
                    touched={memberships[p] for p in c['occurrences'][original]['ids']}
                    if len(touched)>1:
                        for k in touched:crossings[k].add(oi)
            for group in crossings:cuts.add((ci,tuple(sorted(group))))
    out={'scope':__doc__,'inputHash':hashlib.sha256(raw).hexdigest(),'orbitSummaries':summaries,'result':r,
         'requireConnected':connected,'attempts':attempts,
         'connectedGatePassed':bool(r.get('checks')) and all(c['positiveComponents']==1 for c in r['checks'])}
    with Path(sys.argv[3]).open('x') as f:json.dump(out,f)
    print(json.dumps({k:v for k,v in r.items() if k not in ('selected','roleOfSite','scalarLabelsByRole','weightsByRole')},indent=2))
