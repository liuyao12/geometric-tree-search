#!/usr/bin/env python3
"""Pin the actual known control in the historical SMT encoding.

The UNSAT assertion is intentional: it catches the old benchmark's exclusion
of the known working marking, not an inability of the known marking to tile.
"""
import json
import sys
import z3
from a2_online_marking_sat import MarkingSolver
p=sys.argv[1] if len(sys.argv)>1 else '/tmp/a2-online-control/smt-control-input.json'
r=json.load(open(p))
s=MarkingSolver(r['n'],timeout_ms=5000)
for a,v,value in zip(s.assigned,s.values,r['values']):
    s.solver.add(a==(value is not None))
    if value is not None:s.solver.add(v==value)
for row in r['constraints']:
    if row['positive']:s.add(True,row['contacts'])
assert s.solver.check()==z3.sat
missed=0
for row in r['constraints']:
    if row['positive']:continue
    conflict=z3.Or(*[z3.And(s.assigned[i],s.assigned[j],s.values[i]!=sign*s.values[j]) for i,j,sign in row['contacts']])
    if s.solver.check(conflict)==z3.unsat:missed+=1
assert missed==13
# Allow the tree search to handle negatives that do not directly disagree.
# This merely checks admission of the control; it does not learn from it.
clauses=[z3.Or(*[z3.And(s.assigned[i],s.assigned[j],s.values[i]!=sign*s.values[j]) for i,j,sign in row['contacts']]) for row in r['constraints'] if not row['positive']]
assert s.solver.check(z3.PbGe([(c,1) for c in clauses],193))==z3.sat
assert s.solver.check(z3.And(*clauses))==z3.unsat
print('PASS known control is representable and passes all positive constraints; direct-reject-all incorrectly excludes it; admitting 193 direct rejections includes it.')
