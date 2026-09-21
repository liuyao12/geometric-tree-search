#!/usr/bin/env python3
"""Exhaustive small projection checks for the optional compact voxel encoding."""
from itertools import product
from pysat.solvers import Glucose3
from certify_voxel_obstruction import construct
from solve_voxel_pair_corona import solve_window
from test_voxel_frontier_window import model,point_replay

assignments=0
# Distinct placement identities that all cover one voxel: enforce exactly one.
# n >= 6 activates the sequential prefix encoding.
for n in range(1,10):
    data={'model':model([[[0,0,0]]] * n),'fixed':[]}
    pairwise,pv,_=construct(data);compact,cv,_=construct(data,amo='sequential')
    assert pv==cv
    with Glucose3(bootstrap_with=pairwise.clauses) as a,Glucose3(bootstrap_with=compact.clauses) as b:
        for bits in product([False,True],repeat=n):
            assumptions=[v if bit else -v for v,bit in zip(pv.values(),bits)]
            assert a.solve(assumptions=assumptions)==b.solve(assumptions=assumptions)==(sum(bits)==1)
            assignments+=1
    if n>=6:assert len(compact.clauses)<=len(pairwise.clauses)
# Multiple voxel constraints must compose while auxiliary variables stay distinct.
for shape in [[[0,0,0]],[[0,0,0],[1,0,0]],[[0,0,0],[0,1,0],[1,0,0]]]:
    data={'model':model([shape]),'fixed':[{'oi':0,'translation':[0,0,0]}]}
    data['model']['required']=[{'pos':[0,0,0]},{'pos':[1,1,1]}]
    for encoding in ['pairwise','sequential']:
        result=solve_window(data,amo=encoding,time_ms=5000)
        assert result['status']=='valid';point_replay(data,result)
print('PASS',assignments,'exhaustive Boolean projections and composed multi-voxel frontier witnesses for both encodings.')
