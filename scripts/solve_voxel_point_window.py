#!/usr/bin/env python3
"""Specialized finite-window PB/SAT control, separate from reference scheduling.

The validated center/corner reduction is the same as the pair-corona oracle.
No exposed-frontier condition is added: this matches the v2 finite point target.
"""
import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
import z3
from solve_point_pair_corona import voxel_core_domain


def solve(model, time_ms=20000, marked=False, max_candidates=100000):
    start = time.perf_counter()
    deadline = start + time_ms/1000
    def budget():
        if time.perf_counter() >= deadline:
            raise TimeoutError('time budget')
    if not model.get('required') or any(len(p['pos']) != 3 or any(type(x) is not int for x in p['pos']) for p in model['required']):
        raise ValueError('Expected a nonempty integer point target')
    for o in model['orientations']:
        if len({tuple(c['pos']) for c in o['cells']}) != len(o['cells']) or any(type(c['weight']) is not int for c in o['cells']):
            raise ValueError('Expected distinct point sites with integer weights')
    core = {tuple(p['pos']) for p in model['required']}
    target = voxel_core_domain(model, core)
    by_point, by_mark = defaultdict(list), defaultdict(lambda: defaultdict(list))
    specs, seen = [], set()
    solver = z3.Then('simplify', 'propagate-values', 'pb-preprocess', 'pb2bv', 'sat').solver()
    result = {'result': 'unknown', 'reason': None, 'placements': [], 'stats': {'marked': marked, 'backend': 'z3-pb2bv-sat', 'solverVersion': z3.get_version_string(), 'scope': 'Validated voxel reduction of a finite point target, no frontier viability; nonreference SAT scheduling'}}
    try:
        for p in sorted(core):
            budget()
            for oi, o in enumerate(model['orientations']):
                for c in o['cells']:
                    t = tuple(p[k]-c['pos'][k] for k in range(3))
                    spec = (oi, t)
                    if any(x % 2 for x in t) or spec in seen:
                        continue
                    seen.add(spec)
                    if len(specs) >= max_candidates:
                        raise TimeoutError('candidate budget')
                    variable = z3.Bool(f'p{len(specs)}')
                    specs.append((spec, variable))
                    for v in o['voxels']:
                        q = tuple(2*v[k]+1+t[k] for k in range(3))
                        by_point[q].append((variable, 1))
                    if marked:
                        for m in o.get('marks', []):
                            if m['value'] is None or m['value'] == '*':
                                continue
                            if isinstance(m['value'], (list, dict)):
                                raise ValueError('This control requires scalar marking entries')
                            k = (tuple(m['pos'][i]+t[i] for i in range(3)), m.get('component', 0))
                            by_mark[k][json.dumps(m['value'])].append(variable)
        for p, terms in by_point.items():
            budget()
            solver.add(z3.PbEq(terms, 1) if p in target else z3.PbLe(terms, 1))
        if not target.issubset(by_point):
            solver.add(z3.BoolVal(False))
        for index, groups in enumerate(by_mark.values()):
            budget()
            if len(groups) < 2:
                continue
            labels = []
            for j, terms in enumerate(groups.values()):
                label = z3.Bool(f'm{index}_{j}')
                labels.append((label, 1))
                for v in terms:
                    solver.add(z3.Implies(v, label))
            solver.add(z3.PbLe(labels, 1))
        result['stats'].update(candidates=len(specs), targetPoints=len(core), targetVoxels=len(target), markingSites=len(by_mark), preparationMs=(time.perf_counter()-start)*1000)
        budget()
        solver.set(timeout=max(1, int((deadline-time.perf_counter())*1000)))
        status = solver.check()
        if status == z3.sat:
            assignment = solver.model()
            result.update(result='finite_exact', placements=[{'oi': oi, 'translation': list(t)} for (oi, t), v in specs if z3.is_true(assignment.eval(v))])
        elif status == z3.unsat:
            result.update(result='restricted_model_failure' if marked else 'exhausted_finite', reason='complete finite formula UNSAT; trusted solver, no exported proof')
        else:
            result['reason'] = solver.reason_unknown()
    except TimeoutError as e:
        result['reason'] = str(e)
    result['stats']['elapsedMs'] = (time.perf_counter()-start)*1000
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--time-ms', type=int, default=20000)
    parser.add_argument('--marked', action='store_true')
    args = parser.parse_args()
    if args.time_ms < 1:
        parser.error('time must be positive')
    raw = Path(args.input).read_bytes()
    result = solve(json.loads(raw)['model'], args.time_ms, args.marked)
    result['inputSha256'] = hashlib.sha256(raw).hexdigest()
    result['sourceSha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    Path(args.output).write_text(json.dumps(result))
    print(json.dumps({k: v for k, v in result.items() if k != 'placements'}))
