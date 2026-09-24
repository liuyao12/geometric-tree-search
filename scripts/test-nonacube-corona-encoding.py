#!/usr/bin/env python3
"""Finite positive control plus rejection of a first-corona-only witness."""
import importlib.util,json
from pathlib import Path
from pysat.solvers import Glucose3
path=Path(__file__).with_name('search-nonacube-two-corona.py')
spec=importlib.util.spec_from_file_location('corona_search',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original=m.SHAPES
m.SHAPES=(((0,0,0),),)
data=m.build()
assert data['stats']['firstCandidates']==26
assert data['stats']['totalCandidates']==124
with Glucose3(bootstrap_with=data['clauses']) as solver:
    assert solver.solve()
    chosen=[s for i,s in enumerate(data['universe'],1) if i in set(solver.get_model())]
    witness=m.verify(data,chosen)
    assert len(witness['corona1'])==26 and len(witness['corona2'])==98
m.SHAPES=original
w=json.loads((path.parents[1]/'data/nonacube-cross-corona.json').read_text())
chosen=[]
for tile in w['corona']:
    center=tuple(sum(v[i] for v in tile)//9 for i in range(3))
    chosen.append(next((oi,center) for oi in range(3) if m.cells((oi,center))==frozenset(map(tuple,tile))))
try:m.verify({'root':frozenset(map(tuple,w['root']))},chosen)
except AssertionError as e:assert str(e)=='Incomplete second corona'
else:raise AssertionError('A first corona was misclassified as a second')
print('PASS: exact cube two-corona has 26 + 98 tiles; the known nonacube first corona is rejected as an incomplete two-corona.')
