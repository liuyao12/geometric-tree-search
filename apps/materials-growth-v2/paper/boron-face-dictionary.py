"""Greedy geometric dictionary of finite face components; no fallback pair fitting.

All six 3x3x3 configurations at radius scale 1.15 construct this diagnostic
dictionary. No held-out generalization, fractional filling, or growth claim.
"""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import networkx as nx
spec=importlib.util.spec_from_file_location('match',Path(__file__).with_name('rigid-cluster-match.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
types=[];configs=[];eps=.03
for fold in range(6):
    raw=(Path(sys.argv[1])/f'{fold}-1.15-3.json').read_bytes();data=json.loads(raw);occurrences=[]
    for index,group in enumerate(data['components']):
        if group['windingVectors']:continue
        positions=np.array(group['positions']);found=None
        for t in types:
            if len(t['positions'])!=len(positions):continue
            fit=m.match(t['positions'],positions,eps)
            if fit is not None:found=(t,fit);break
        if found is None:
            center=positions.mean(axis=0)
            t={'id':len(types),'positions':(positions-center).tolist(),'occurrences':0}
            types.append(t);found=(t,{'permutation':list(range(len(positions))),'rotationRow':np.eye(3).tolist(),'translation':center.tolist(),'residual':0.})
        t,fit=found;t['occurrences']+=1
        graph=nx.Graph();graph.add_nodes_from(group['ids']);graph.add_edges_from(group['edges'])
        icosahedral=len(positions)==12 and nx.is_isomorphic(graph,nx.icosahedral_graph())
        occurrences.append({'component':index,'type':t['id'],'icosahedralGraph':icosahedral,**fit})
    summary={'fold':fold,'file':data['summary']['file'],'finiteOccurrences':len(occurrences),
        'icosahedralGraphOccurrences':sum(o['icosahedralGraph'] for o in occurrences),'typesSoFar':len(types)}
    configs.append({**summary,'sourceHash':hashlib.sha256(raw).hexdigest(),'occurrences':occurrences})
    print(json.dumps(summary),flush=True)
out={'scope':__doc__,'epsilonAngstrom':eps,'types':types,'configurations':configs,
     'summary':{'typesBySize':dict(sorted(collections.Counter(len(t['positions']) for t in types).items())),
                'totalTypes':len(types),'singleOccurrenceTypes':sum(t['occurrences']==1 for t in types)}}
with Path(sys.argv[2]).open('x') as f:json.dump(out,f)
print(json.dumps(out['summary']),flush=True)
