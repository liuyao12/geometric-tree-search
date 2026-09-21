#!/usr/bin/env python3
"""Independent exhaustive one-dimensional controls for the research oracle."""
from itertools import combinations, product

from solve_point_pair_corona import solve


def exhaustive(weights, shift, capacity=3):
    # Enumerate translations by an interval, independently of support alignment.
    core = set(range(len(weights))) | set(range(shift, shift+len(weights)))
    fixed = [0, shift]
    fixed_totals = {p: sum(weights[p-t] for t in fixed if 0 <= p-t < len(weights)) for p in core}
    if max(fixed_totals.values()) > capacity:
        return None
    candidates = [t for t in range(min(core)-len(weights)+1, max(core)+1) if t not in fixed]
    candidates = [t for t in candidates if all(fixed_totals.get(t+i, 0)+w <= capacity for i, w in enumerate(weights))]
    for count in range(len(candidates)+1):
        for subset in combinations(candidates, count):
            selected = [*fixed, *subset]
            totals = {}
            for t in selected:
                for i, w in enumerate(weights):
                    totals[t+i] = totals.get(t+i, 0)+w
            if any(n > capacity for n in totals.values()) or any(totals.get(p) != capacity for p in core):
                continue
            def viable(p):
                return any(t not in selected and all(totals.get(t+i, 0)+w <= capacity for i, w in enumerate(weights))
                           for t in range(p-len(weights)+1, p+1))
            if all(n == capacity or viable(p) for p, n in totals.items()):
                return True
    return False


count = 0
for size in [2, 3, 4]:
    for weights in product([1, 2], repeat=size):
        for shift in range(1, size):
            expected = exhaustive(weights, shift)
            if expected is None:
                continue
            model = {'capacity': 3, 'orientations': [{'cells': [{'pos': [i, 0, 0], 'weight': w} for i, w in enumerate(weights)]}]}
            pair = [{'oi': 0, 'translation': [0, 0, 0]}, {'oi': 0, 'translation': [shift, 0, 0]}]
            result = solve(model, pair, time_ms=5000)
            assert result['status'] == ('valid' if expected else 'invalid'), (weights, shift, expected, result)
            # Independently check every reduced obstruction recorded by the SAT
            # oracle. It need not contain the fixed seeds or complete the core.
            for nogood in result['nogoods']:
                selected = [p['translation'][0] for p in nogood['placements']]
                totals = {}
                for t in selected:
                    for i, w in enumerate(weights):
                        totals[t+i] = totals.get(t+i, 0)+w
                p = nogood['deadPoint'][0]
                assert 0 < totals[p] < 3
                assert all(t in selected or any(totals.get(t+i, 0)+w > 3 for i, w in enumerate(weights)) for t in range(p-size+1, p+1))
            count += 1
assert solve(model, pair, time_ms=0)['status'] == 'unresolved'
assert solve(model, pair, max_candidates=1)['status'] == 'unresolved'
assert solve(model, pair, max_rounds=0)['status'] == 'unresolved'
print(f'PASS {count} exhaustive interval controls, reduced dead-frontier obstructions, and unknown budgets.')
