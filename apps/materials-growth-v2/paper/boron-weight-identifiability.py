"""Exact conditional identifiability of shared t roles; no search or physics.

Usage: python boron-weight-identifiability.py INPUT LEARNING OUTPUT
Fixes the supplied selected fillings, not the occurrence-learning problem.
"""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path


def rref(rows, width):
    basis = {}
    for row in rows:
        v = list(map(F, row))
        for p, b in sorted(basis.items()):
            if v[p]:
                z = v[p]
                v = [x - z*y for x, y in zip(v, b)]
        p = next((j for j in range(width) if v[j]), None)
        if p is None:
            if any(v[width:]):
                raise ValueError('inconsistent equations')
            continue
        z = v[p]
        v = [x/z for x in v]
        for q, b in list(basis.items()):
            if b[p]:
                z = b[p]
                basis[q] = [x-z*y for x, y in zip(b, v)]
        basis[p] = v
    return basis


def audit(d, r):
    n = len(r['weightsByRole'])
    weights = r['weightsByRole']
    capacity = r['capacity']
    rows, folds, per_fold = set(), [], []
    for cfg, selected in zip(d['configurations'], r['selected'], strict=True):
        assert len(selected) == len(set(selected))
        eq = [[0]*n for _ in range(cfg['atoms'])]
        for oi in selected:
            occurrence = cfg['occurrences'][oi]
            offset = d['types'][occurrence['type']]['offset']
            for site, atom in enumerate(occurrence['ids']):
                eq[atom][r['roleOfSite'][offset+site]] += 1
        assert all(sum(a*b for a,b in zip(row, weights)) == capacity for row in eq)
        unique = set(map(tuple, eq))
        per_fold.append(unique)
        rows.update(unique)
        folds.append({'file': cfg['file'], 'atomEquations': len(eq),
                      'uniqueEquations': len(unique)})
    ordered = sorted(rows)
    basis = rref([list(row)+[capacity] for row in ordered], n)
    free = [j for j in range(n) if j not in basis]
    nullspace = []
    for f in free:
        v = [F(0)]*n
        v[f] = F(1)
        for p, b in basis.items():
            v[p] = -b[f]
        assert all(sum(a*b for a,b in zip(row,v)) == 0 for row in ordered)
        nullspace.append(v)
    fixed = [j for j in range(n) if all(v[j] == 0 for v in nullspace)]
    # Equality freedom need not survive positivity/capacity bounds. Find exact
    # allowable intervals on each basis direction through the learned witness.
    directions = []
    for f, v in zip(free, nullspace):
        lo, hi = None, None
        for w, delta in zip(weights, v):
            if not delta:
                continue
            a, b = sorted((F(-w)/delta, F(capacity-w)/delta))
            lo = a if lo is None else max(lo, a)
            hi = b if hi is None else min(hi, b)
        directions.append({'freeRole': f, 'vector': list(map(str,v)),
                           'closedCapacityInterval': [str(lo),str(hi)]})
    leave_out = []
    for excluded in range(len(per_fold)):
        retained = set().union(*(s for i,s in enumerate(per_fold) if i != excluded))
        b = rref([list(row)+[capacity] for row in sorted(retained)], n)
        leave_out.append({'excluded': excluded, 'rank':len(b), 'nullity':n-len(b)})
    return {'scope': 'Exact rational equality audit conditional on fixed selected training fillings; bounds 0<t<=1 are separate; no held-out or blind-growth claim.',
            'roles': n, 'folds': folds, 'uniqueEquations': len(rows),
            'rank': len(basis), 'nullity': len(free), 'fixedRoles': fixed,
            'freeRoles': free, 'nullspaceDirections': directions,
            'capacity': capacity, 'weightsByRole': weights, 'leaveOneConfigurationOut':leave_out,
            'equations': ordered}


if __name__ == '__main__':
    inp, learned, dest = map(Path, sys.argv[1:])
    output = audit(json.loads(inp.read_text()), json.loads(learned.read_text())['result'])
    output.update(inputHash=hashlib.sha256(inp.read_bytes()).hexdigest(),
                  learningHash=hashlib.sha256(learned.read_bytes()).hexdigest())
    dest.write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in
                      ('equations','weightsByRole','nullspaceDirections','fixedRoles','freeRoles')}, indent=2))
