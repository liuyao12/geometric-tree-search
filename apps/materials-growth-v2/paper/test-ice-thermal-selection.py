"""Tiny exhaustive controls, including the odd-degree single-bridge case."""
import importlib.util
from pathlib import Path
import itertools
import random
import networkx as nx
spec=importlib.util.spec_from_file_location('selection',Path(__file__).with_name('ice-thermal-selection.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rng=random.Random(8091)
for trial in range(30):
    n=5;edges=[e for e in itertools.combinations(range(n),2) if rng.random()<.6]
    exists=False
    for choice in itertools.combinations(edges,n):
        g=nx.Graph();g.add_nodes_from(range(n));g.add_edges_from(choice)
        if all(d==2 for _,d in g.degree) and nx.is_connected(g):exists=True;break
    result=m.select([[i] for i in range(n)],edges,list(range(len(edges))),2,2.)
    assert (result['status']=='connected positive finite cover')==exists,(trial,result,exists)
edges=[]
for offset in (0,5):
    edges.extend((a+offset,b+offset) for a,b in itertools.combinations(range(4),2) if (a,b)!=(0,1))
    edges.extend([(offset,offset+4),(offset+1,offset+4)])
edges.append((4,9))
result=m.select([[i] for i in range(10)],edges,list(range(len(edges))),3,2.)
assert result['status']=='connected positive finite cover'
print('30 exhaustive even-degree tests and one odd-degree bridge test passed')
