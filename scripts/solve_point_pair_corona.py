#!/usr/bin/env python3
"""Research oracle: finite exact point constraints plus lazy frontier checks.

This is a separate PB/SAT control, not the reference graph scheduler. The finite
universe contains EVERY placement touching the seed support. See the projection
argument in docs/projects/3d-point-corona-sat.md before changing that universe.
"""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import z3


class Limit(Exception):
    pass


def solve(model, pair, time_ms=30000, max_candidates=100000, max_rounds=1000):
    started = time.perf_counter()
    deadline = started + time_ms / 1000
    capacity = model['capacity']
    if not isinstance(capacity, int) or capacity < 1:
        raise ValueError('Expected positive integer capacity')
    supports = []
    for orientation in model['orientations']:
        support = [(tuple(c['pos']), c['weight']) for c in orientation['cells']]
        if (not support or len({p for p, _ in support}) != len(support)
                or any(len(p) != 3 or any(type(x) is not int for x in p)
                       or type(w) is not int or not 0 < w <= capacity for p, w in support)):
            raise ValueError('Expected distinct integer support points and positive weights')
        supports.append(support)
    domain = model.get('placementDomain') or {}
    if domain.get('kind') not in (None, 'scaled_cubic', 'a2_slab'):
        raise ValueError('Unsupported translation domain')
    if domain.get('kind') == 'scaled_cubic' and (type(domain.get('translationStep')) is not int or domain['translationStep'] < 1):
        raise ValueError('Invalid translation step')

    def allowed(t):
        if any(type(x) is not int for x in t):
            return False
        if domain.get('kind') == 'scaled_cubic':
            return all(x % domain['translationStep'] == 0 for x in t)
        if domain.get('kind') == 'a2_slab':
            return sum(t) == 0 and (not domain.get('index3') or (t[0]-t[1]) % 3 == 0 and (t[1]-t[2]) % 3 == 0)
        return True

    def cells(spec):
        oi, translation = spec
        return [(tuple(p[i] + translation[i] for i in range(3)), w) for p, w in supports[oi]]

    def descriptor(spec):
        return {'oi': spec[0], 'translation': list(spec[1])}

    def check_time():
        if time.perf_counter() >= deadline:
            raise Limit('time budget')

    seeds = [(p['oi'], tuple(p['translation'])) for p in pair]
    if len(set(seeds)) != len(seeds) or any(not 0 <= oi < len(supports) or len(t) != 3 or not allowed(t) for oi, t in seeds):
        raise ValueError('Invalid seed placements')
    fixed = defaultdict(int)
    for seed in seeds:
        for p, w in cells(seed):
            fixed[p] += w
            if fixed[p] > capacity:
                raise ValueError('Overlapping seeds')
    core = set(fixed)
    candidates = {}
    nogoods = []
    rounds = 0
    stats = {'backend': 'z3-pb2bv-sat', 'solverVersion': z3.get_version_string(), 'scope': 'Finite seed-support corona with viable exposed frontier; research control, not reference scheduling'}
    result = {'status': 'unresolved', 'reason': None, 'placements': pair}
    try:
        # Adding the seeds first makes their identities stable in the receipt.
        for seed in seeds:
            candidates[seed] = cells(seed)
        seen = set(candidates)
        for at in sorted(core):
            check_time()
            for oi, support in enumerate(supports):
                for anchor, _ in support:
                    t = tuple(at[i] - anchor[i] for i in range(3))
                    spec = (oi, t)
                    if spec in seen or not allowed(t):
                        continue
                    seen.add(spec)
                    placed = cells(spec)
                    if any(fixed.get(p, 0) + w > capacity for p, w in placed):
                        continue
                    if len(candidates) >= max_candidates:
                        raise Limit('candidate budget')
                    candidates[spec] = placed
        specs = list(candidates)
        variables = [z3.Bool(f'p{i}') for i in range(len(specs))]
        by_point = defaultdict(list)
        for i, support in enumerate(candidates.values()):
            for p, w in support:
                by_point[p].append((variables[i], w))
        solver = z3.Then('simplify', 'propagate-values', 'pb-preprocess', 'pb2bv', 'sat').solver()
        for i in range(len(seeds)):
            solver.add(variables[i])
        for p, terms in by_point.items():
            check_time()
            solver.add(z3.PbEq(terms, capacity) if p in core else z3.PbLe(terms, capacity))
        stats.update(candidates=len(specs), points=len(by_point), corePoints=len(core), dependencies=sum(map(len, candidates.values())), preparationMs=(time.perf_counter()-started)*1000)

        for _ in range(max_rounds):
            check_time()
            solver.set(timeout=max(1, int((deadline-time.perf_counter())*1000)))
            answer = solver.check()
            rounds += 1
            if answer == z3.unsat:
                result.update(status='invalid', reason='complete finite point formula exhausted')
                break
            if answer != z3.sat:
                raise Limit('solver: ' + solver.reason_unknown())
            assignment = solver.model()
            selected = [i for i, v in enumerate(variables) if z3.is_true(assignment.eval(v, model_completion=True))]
            placed_specs = {specs[i] for i in selected}
            totals = defaultdict(int)
            for i in selected:
                for p, w in candidates[specs[i]]:
                    totals[p] += w
            assert all(n <= capacity for n in totals.values())
            assert all(totals[p] == capacity for p in core)
            dead = None
            legality = {}
            for p, n in totals.items():
                check_time()
                if n == capacity:
                    continue
                viable = False
                for oi, support in enumerate(supports):
                    for anchor, _ in support:
                        t = tuple(p[i] - anchor[i] for i in range(3))
                        spec = (oi, t)
                        if not allowed(t):
                            continue
                        if spec not in legality:
                            legality[spec] = spec not in placed_specs and all(totals.get(q, 0)+w <= capacity for q, w in cells(spec))
                        if legality[spec]:
                            viable = True
                            break
                    if viable:
                        break
                if not viable:
                    dead = p
                    break
            placements = [descriptor(specs[i]) for i in selected]
            result['placements'] = placements
            if dead is None:
                result.update(status='valid', reason=None, verification={'coreComplete': True, 'frontierViable': True})
                break
            # A dead frontier cannot be repaired by adding tiles: all placements
            # touching it are already selected or capacity-incompatible. Thus
            # every legal superset of this selected set is also impossible.
            # Remove irrelevant placements from the obstruction. Re-enumerate
            # every possible addition at this point, including ones outside the
            # finite core-covering SAT universe.
            incident = {}
            for oi, support in enumerate(supports):
                for anchor, _ in support:
                    t = tuple(dead[i]-anchor[i] for i in range(3))
                    spec = (oi, t)
                    if allowed(t) and spec not in incident:
                        incident[spec] = cells(spec)
            obstruction = set(selected)
            for i in selected:
                check_time()
                spec = specs[i]
                for p, w in candidates[spec]:
                    totals[p] -= w
                placed_specs.remove(spec)
                still_dead = totals[dead] > 0 and not any(
                    c not in placed_specs and all(totals.get(p, 0)+w <= capacity for p, w in support)
                    for c, support in incident.items())
                if still_dead:
                    obstruction.remove(i)
                else:
                    placed_specs.add(spec)
                    for p, w in candidates[spec]:
                        totals[p] += w
            nogoods.append({'deadPoint': list(dead), 'placements': [descriptor(specs[i]) for i in sorted(obstruction)]})
            solver.add(z3.Or([z3.Not(variables[i]) for i in sorted(obstruction)]))
        else:
            raise Limit('frontier refinement budget')
    except Limit as error:
        result.update(status='unresolved', reason=str(error))
    return {**result, 'stats': {**stats, 'rounds': rounds, 'frontierNogoods': len(nogoods), 'elapsedMs': (time.perf_counter()-started)*1000}, 'nogoods': nogoods}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--time-ms', type=int, default=30000)
    parser.add_argument('--max-candidates', type=int, default=100000)
    parser.add_argument('--max-rounds', type=int, default=1000)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text())
    result = solve(data['model'], data['pair'], args.time_ms, args.max_candidates, args.max_rounds)
    Path(args.output).write_text(json.dumps(result))
    print(json.dumps({k: v for k, v in result.items() if k not in ('placements', 'nogoods')}), flush=True)
