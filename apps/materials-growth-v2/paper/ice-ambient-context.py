"""Cover-independent local clouds on a frozen geometric component-neighbor graph.

Uses all neighbors in the existing training-derived geometric proposal graph,
not the two neighbors chosen by a half-weight cover. Components/species are
input geometry and opaque labels; no chemical coordination or formula is used.
Periodic semantics are one minimum-image displacement per component pair.
"""
import importlib.util
from pathlib import Path
import numpy as np
from ase.geometry import find_mic
spec=importlib.util.spec_from_file_location('junction',Path(__file__).with_name('ice-junction-clouds.py'))
junction=importlib.util.module_from_spec(spec);spec.loader.exec_module(junction)

def contexts(configuration,cover):
    c=configuration;parts=cover['components']
    assert all(c.get('pbc',[True,True,True]))
    assert sorted(i for p in parts for i in p)==list(range(len(c['positions'])))
    lifted=[];centers=[];groups=[];neighbors=[set() for _ in parts]
    for part in parts:
        ids=sorted(part,key=lambda i:(c['species'][i],i));x=junction.geometry.lift(c,ids);center=x.mean(axis=0)
        lifted.append(x-center);centers.append(center);groups.append([c['species'][i] for i in ids])
    centers=np.asarray(centers)
    for a,b in cover['componentPairs']:
        assert a!=b and b not in neighbors[a]
        neighbors[a].add(b);neighbors[b].add(a)
    for root,adjacent in enumerate(neighbors):
        order=sorted(adjacent,key=lambda i:(groups[i],i))
        shifts,_=find_mic(centers[order]-centers[root],c['cell'],pbc=True) if order else ([],[])
        yield dict(root=root,neighbors=order,groups=[groups[root],*[groups[i] for i in order]],
                   vectors=np.vstack([lifted[root],*[lifted[i]+shift for i,shift in zip(order,shifts)]]).tolist())
