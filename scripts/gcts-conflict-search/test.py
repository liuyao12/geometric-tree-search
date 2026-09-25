#!/usr/bin/env python3
"""Independent exhaustive finite-model, rollback, scheduler and proof controls."""
import argparse
import itertools
import json
from pathlib import Path
import random
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--solver', required=True)
p.add_argument('--drat-trim', required=True)
a = p.parse_args()
rng = random.Random(240926)
totals = dict(cases=0, sat=0, unsat=0, proofChecks=0, conflicts=0, backjumps=0)
with tempfile.TemporaryDirectory() as tmp:
    stem = Path(tmp) / 'control'
    for trial in range(150):
        n = rng.randrange(5, 11)
        pairs = [pair for pair in itertools.combinations(range(1, n + 1), 2) if rng.random() < .22]
        points = []
        for i in range(rng.randrange(3, 15)):
            cover = sorted(rng.sample(range(1, n + 1), rng.randrange(1, min(n, 5))))
            outside = sorted(set(range(1, n + 1)) - set(cover))
            seed = int(rng.random() < .7)
            triggers = [] if seed else rng.sample(outside, rng.randrange(1, len(outside) + 1))
            points.append((rng.randrange(4), seed, cover, triggers))
        clauses = [[-x, -y] for x, y in pairs]
        for generation, seed, cover, triggers in points:
            if seed:
                clauses.append(cover)
            clauses.extend([[-t, *cover] for t in triggers])
        stem.with_suffix('.cnf').write_text(f'p cnf {n} {len(clauses)}\n' + ''.join(' '.join(map(str, c)) + ' 0\n' for c in clauses))
        stem.with_suffix('.points').write_text(f'{n} {len(points)}\n' + ''.join(' '.join(map(str, [i, 0, 0, g, seed, len(c), len(t), *c, *t])) + '\n' for i, (g, seed, c, t) in enumerate(points)))
        # Independent semantics, not evaluation of the solver's CNF.
        def valid(s):
            return (not any(x in s and y in s for x, y in pairs)
                    and all(not (seed or s.intersection(t)) or s.intersection(c)
                            for g, seed, c, t in points))
        truth = any(valid({i + 1 for i in range(n) if mask & (1 << i)}) for mask in range(1 << n))
        run = subprocess.run([a.solver, str(stem.with_suffix('.cnf')), str(stem.with_suffix('.points')), str(stem.with_suffix('.drup')), '10', '--audit'], capture_output=True, text=True)
        assert run.returncode == 0, (trial, run.stderr)
        result = json.loads(run.stdout)
        assert result['status'] == ('SAT' if truth else 'UNSAT'), (trial, result)
        if truth:
            assert valid(set(result['selected']))
            totals['sat'] += 1
        else:
            check = subprocess.run([a.drat_trim, str(stem.with_suffix('.cnf')), str(stem.with_suffix('.drup'))], capture_output=True, text=True)
            assert check.returncode == 0 and 's VERIFIED' in check.stdout, (trial, check.stdout, check.stderr)
            totals['unsat'] += 1
            totals['proofChecks'] += 1
        totals['cases'] += 1
        for key in ('conflicts', 'backjumps'):
            totals[key] += result[key]
    assert totals['conflicts'] and totals['backjumps'] and totals['sat'] and totals['unsat']
print(json.dumps(totals, indent=2))

# Eleven mutually disjoint tiles must choose ten secondary capacity points.
# This larger UNSAT instance exercises restarts and learned-clause deletion.
with tempfile.TemporaryDirectory() as tmp:
    stem = Path(tmp) / 'pigeonhole'
    pigeons, holes = 11, 10
    variable = lambda p, h: p * holes + h + 1
    covers = [[variable(p, h) for h in range(holes)] for p in range(pigeons)]
    clauses = list(covers)
    for cover in covers:
        clauses.extend([[-x, -y] for x, y in itertools.combinations(cover, 2)])
    for h in range(holes):
        clauses.extend([[-variable(x, h), -variable(y, h)] for x, y in itertools.combinations(range(pigeons), 2)])
    stem.with_suffix('.cnf').write_text(f'p cnf {pigeons * holes} {len(clauses)}\n' + ''.join(' '.join(map(str, c)) + ' 0\n' for c in clauses))
    stem.with_suffix('.points').write_text(f'{pigeons * holes} {pigeons}\n' + ''.join(' '.join(map(str, [p, 0, 0, 0, 1, holes, 0, *c])) + '\n' for p, c in enumerate(covers)))
    run = subprocess.run([a.solver, str(stem.with_suffix('.cnf')), str(stem.with_suffix('.points')), str(stem.with_suffix('.drup')), '60', '--audit'], capture_output=True, text=True, check=True)
    result = json.loads(run.stdout)
    assert result['status'] == 'UNSAT', result
    assert result['restarts'] > 0 and result['deletedConstraints'] > 0, result
    check = subprocess.run([a.drat_trim, str(stem.with_suffix('.cnf')), str(stem.with_suffix('.drup'))], capture_output=True, text=True)
    assert check.returncode == 0 and 's VERIFIED' in check.stdout, check.stdout
    print(json.dumps({'pigeonhole': result, 'proofVerified': True}, indent=2))
