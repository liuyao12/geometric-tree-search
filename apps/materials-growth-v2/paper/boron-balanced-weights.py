"""Enumerate the integer family and maximize the minimum non-fixed weight.

Conditional regularization control, not a search-equivalent transformation.
"""
import copy
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

source, certpath, dest = map(Path, sys.argv[1:])
original = json.loads(source.read_text())
cert = json.loads(certpath.read_text())
assert cert['learningHash'] == hashlib.sha256(source.read_bytes()).hexdigest()
assert cert['nullity'] == 1
v = list(map(F,cert['nullspaceDirections'][0]['vector']))
assert all(x.denominator == 1 for x in v)
weights = original['result']['weightsByRole']
cap = original['result']['capacity']
f = cert['freeRoles'][0]
assert v[f] == 1
possibilities = []
for value in range(1,cap+1):
    delta = value-weights[f]
    candidate = [F(w)+delta*x for w,x in zip(weights,v)]
    if all(0 < w <= cap and w.denominator == 1 for w in candidate):
        candidate = list(map(int,candidate))
        assert all(sum(x*y for x,y in zip(row,candidate)) == cap for row in cert['equations'])
        possibilities.append((min(w for w,x in zip(candidate,v) if x),-abs(delta),candidate,delta))
_,_,best,delta = max(possibilities)
out = copy.deepcopy(original)
out['result']['weightsByRole'] = best
out['conditionalRefit'] = {'method':'Maximize minimum non-fixed site weight over certified one-dimensional integer family; nearest original parameter breaks ties.',
    'parentLearningHash':cert['learningHash'], 'feasibleGridMembers':len(possibilities),
    'parameterShift':delta, 'changedRoles':[i for i,(a,b) in enumerate(zip(weights,best)) if a!=b],
    'scope':'Same six selected witnesses, different t-model; inherited solver metadata describes parent fit, not this refit. No new geometry, occurrences or markings learned.'}
dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out['conditionalRefit'],indent=2))
