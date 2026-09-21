#!/usr/bin/env python3
from itertools import product
from random import Random
from pysat.solvers import Glucose3
from certify_voxel_obstruction import construct
from lib.check_rup import RUPChecker

def sat(clauses,n):
    return any(all(any((bits[abs(x)-1] if x>0 else not bits[abs(x)-1]) for x in c) for c in clauses) for bits in product([False,True],repeat=n))
assert not RUPChecker([[1,2]]).implied([1])
try: RUPChecker([[1,2]]).verify(['1 0','0']);raise AssertionError('Accepted bogus proof')
except ValueError: pass
rng=Random(193)
for _ in range(100):
    clauses=[rng.sample([-3,-2,-1,1,2,3],rng.randrange(1,4)) for _ in range(rng.randrange(1,20))]
    expected=sat(clauses,3)
    with Glucose3(bootstrap_with=clauses,with_proof=True) as solver:
        assert solver.solve()==expected
        if not expected: assert RUPChecker(clauses).verify(solver.get_proof())['verified']
    checker=RUPChecker(clauses)
    for c in [[1],[-1],[2,3],[-2,3],[]]:
        if checker.implied(c): assert not sat(clauses+[[-x] for x in c],3)
base={'capacity':8,'placementDomain':{'kind':'scaled_cubic','translationStep':2},'orientations':[{'voxels':[[0,0,0]]}],'required':[{'pos':[1,1,1]},{'pos':[3,1,1]}]}
pair=[{'oi':0,'translation':[0,0,0]},{'oi':0,'translation':[2,0,0]}]
for mode in ['window','pair','forbidden']:
    data={'model':base,'fixed':[pair[0]]}
    if mode=='pair': data['pair']=pair
    if mode=='forbidden': data['pairExclusions']=[pair]
    f,variables,stats=construct(data,[[-2,0,0],[6,4,4]] if mode=='pair' else None)
    with Glucose3(bootstrap_with=f.clauses,with_proof=True) as solver:
        answer=solver.solve();assert answer==(mode!='forbidden')
        if not answer: assert RUPChecker(f.clauses).verify(solver.get_proof())['verified']
        else:
            selected=set(solver.get_model());occupied=set()
            for (oi,t),v in variables.items():
                if v not in selected: continue
                for cell in base['orientations'][oi]['voxels']:
                    q=tuple(cell[i]+t[i] for i in range(3));assert q not in occupied;occupied.add(q)
            assert {(0,0,0),(1,0,0)}.issubset(occupied)
print('PASS 100 truth-table SAT/RUP controls, rejected bogus proof, independent voxel windows, outside-pool frontier and pair-exclusion controls.')
