"""One bounded ROOT-owned finite calibration; no Q inputs or proof routes.

Run with an explicit frozen JSON plan. Source buffers are verified before
execution. Engine and truth oracle were independently authored before either
read the other's implementation. The raw-wire auditor never imports the engine.
"""
import time
BEGAN_NS = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
import hashlib
import itertools
import json
import os
from pathlib import Path
import resource
import sys
import types


def need(ok, message):
    if not ok:
        raise ValueError(message)


def pinned(item):
    raw = Path(item['path']).read_bytes()
    need(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'],
         'frozen input: ' + item['path'])
    return raw


def module(name, raw, path):
    value = types.ModuleType(name)
    value.__file__ = path
    sys.modules[name] = value
    exec(compile(raw, path, 'exec'), value.__dict__)
    return value


def decoded_bits(state, n):
    marks = {(x, y): value for x, y, value in state['marks']}
    return [[i, marks[6*i, 2]] for i in range(n) if (6*i, 2) in marks]


def inventory_check(result, case, marked, prefix):
    """Reconstruct expected whole inventory, including every forbidden tuple."""
    n, clauses = case['variables'], case['clauses']
    roots = sorted([[6*i, 0, 0] for i in range(n)] +
                   [[6*c+d, 6, 0] for c in range(len(clauses)) for d in (0, 2)])
    expected = []
    for i in range(n):
        for bit in (0, 1):
            expected.append({'name': 'B_'+str(i)+'_'+str(bit),
                             't': [[6*i, 0, 1]], 'm': [[6*i, 2, bit]]})
    for c, clause in enumerate(clauses):
        forbidden = tuple(0 if sign == 1 else 1 for _, sign in clause)
        for bits in itertools.product((0, 1), repeat=len(clause)):
            expected.append({'name': 'A_'+str(c)+'_'+''.join(map(str, bits)),
                't': [[6*c, 6, 1]],
                'm': [[6*i, 2, bit] for (i, _), bit in zip(clause, bits)] +
                     [[6*c+2, 8, int(bits == forbidden)]]})
        expected.append({'name': 'R_'+str(c), 't': [[6*c+2, 6, 1]],
                         'm': [[6*c+2, 8, 0]] if marked else []})
    actual = result['model']
    need(actual['roots'] == roots and actual['candidates'] == expected,
         'complete declared tuple inventory and required points')
    need(actual['fixed_marks'] == sorted([[6*i, 2, b] for i, b in prefix]),
         'fixed boundary is exactly the requested prefix')
    need(result['root_state'] == {'placements': [], 'filled': [],
                                  'marks': actual['fixed_marks']}, 'no preselected guards')
    return {'required_points': len(roots), 'candidates': len(expected),
            'all_forbidden_tuples_retained': True, 'seed_is_marking_only': True}


def main(plan_path):
    plan_raw = Path(plan_path).read_bytes()
    plan = json.loads(plan_raw)
    need(plan['schema'] == 'ROOT-finite-point-calibration-plan-v1', 'exact plan')
    output = Path(plan['output_directory'])
    need(output.is_dir() and not list(output.iterdir()), 'fresh empty actual directory')
    sources = {key: pinned(value) for key, value in plan['inputs'].items()}
    engine = module('finite_point_engine_actual_v1', sources['engine'], plan['inputs']['engine']['path'])
    oracle = module('independent_boolean_oracle_actual_v1', sources['oracle'], plan['inputs']['oracle']['path'])
    auditor = module('independent_raw_trace_auditor_actual_v1', sources['auditor'], plan['inputs']['auditor']['path'])
    declarations = json.loads(sources['cases'])
    oracle_result = oracle.evaluate_declarations(declarations)
    records, rows, controls = [], [], []
    solve_limits = plan['solve_limits']

    def solve(label, model, metadata, limits=None):
        need(time.clock_gettime_ns(time.CLOCK_MONOTONIC)-BEGAN_NS < plan['worker_seconds']*10**9,
             'whole finite calibration wall budget')
        began = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        result = engine.solve(model, **(solve_limits if limits is None else limits))
        elapsed = time.clock_gettime_ns(time.CLOCK_MONOTONIC)-began
        audit = auditor.audit_result(result, allow_unknown=result['status'] == 'UNKNOWN')
        records.append({'id': label, 'metadata': metadata, 'solve_elapsed_ns': elapsed,
                        'result': result, 'independent_trace_audit': audit})
        return result

    for case, truth in zip(declarations['cases'], oracle_result['results']):
        need(case['id'] == truth['case_id'], 'same ordered case identity')
        n = case['variables']
        clauses = tuple(tuple((i, 1 if sign == 1 else 0) for i, sign in clause)
                        for clause in case['clauses'])
        row = {'case_id': case['id'], 'variables': n, 'clauses': len(clauses), 'modes': []}
        for marked, truth_mode in zip((False, True), truth['modes']):
            accepted = {tuple(bits) for bits in truth_mode['accepted_assignments']}
            mode = truth_mode['mode']
            found_assignments, prefix_count = [], 0
            stats = {key: 0 for key in ('placements', 'forced_placements', 'branch_decisions',
                      'backtracks', 'restores', 'graph_rebuilds', 'marking_rejections')}
            def run_prefix(prefix, label, purpose):
                model = engine.build_cnf_model(n, clauses,
                    active_guards=tuple(range(len(clauses))) if marked else (),
                    seed_bits=tuple(tuple(item) for item in prefix),
                    maximum_candidates=plan['maximum_candidates'])
                result = solve(label, model, {'case_id': case['id'], 'mode': mode,
                                              'prefix': prefix, 'purpose': purpose})
                inventory_check(result, case, marked, prefix)
                need(result['status'] != 'UNKNOWN' and result['trace_complete'], 'complete finite case')
                extensions = {bits for bits in accepted if all(bits[i] == b for i, b in prefix)}
                need((result['status'] == 'FOUND') == bool(extensions), 'truth-table existence agreement')
                if result['status'] == 'FOUND':
                    pairs = decoded_bits(result['solution'], n)
                    need(len(pairs) == n and tuple(b for _, b in pairs) in extensions,
                         'independent Boolean acceptance of every solution projection')
                return result
            for index, bits in enumerate(truth['all_assignments']):
                prefix = [[i, b] for i, b in enumerate(bits)]
                result = run_prefix(prefix, case['id']+'/'+mode+'/assignment-'+str(index), 'whole-bit-assignment')
                if result['status'] == 'FOUND':
                    found_assignments.append(bits)
            need({tuple(bits) for bits in found_assignments} == accepted, 'entire finite projected solution set')
            for index, probe in enumerate(truth_mode['prefix_probes']):
                prefix_count += 1
                result = run_prefix(probe['prefix'], case['id']+'/'+mode+'/prefix-'+str(index), 'partial-boundary')
                stop = next(event for event in result['trace'] if event['kind'] in ('branch', 'dead', 'solution'))
                closure = probe['unit_closure']
                if closure['conflict']:
                    need(stop['kind'] == 'dead', 'unit conflict detected before any branch')
                else:
                    need(stop['kind'] != 'dead', 'nonconflicting unit closure remains feasible before branching')
                    need(decoded_bits(stop['state'], n) == closure['assignment'],
                         'point forced closure equals independent clause unit closure')
                for key in stats:
                    stats[key] += result['stats'][key]
            row['modes'].append({'mode': mode, 'accepted_assignments': found_assignments,
                'assignment_checks': len(truth['all_assignments']), 'prefix_checks': prefix_count,
                'prefix_stats': stats, 'truth_and_unit_closure_agree': True})
        rows.append(row)

    # Generic controls are independent of the propositional construction.
    C, M = engine.Candidate, engine.Model
    dead = M((((0, 0), 0), ((6, 0), 0)), (C('sole', (0, 0), ()),), (), 'control-global-dead')
    result = solve('control/global-dead-before-forced', dead, {'purpose': 'scheduler-control'})
    need(result['status'] == 'EXHAUSTED_FINITE_MARKED_MODEL' and result['stats']['placements'] == 0,
         'global dead precedes existing forced move')
    controls.append({'id': records[-1]['id'], 'pass': True})
    rollback = M((((0, 0), 0), ((6, 0), 0)),
        (C('bad', (0, 0), ((100, 100, 0),)), C('good', (0, 0), ((100, 100, 1),)),
         C('tail0', (6, 0), ((100, 100, 1), (106, 100, 0))),
         C('tail1', (6, 0), ((100, 100, 1), (106, 100, 1)))), (), 'control-real-rollback')
    result = solve('control/failed-branch-rollback', rollback, {'purpose': 'rollback-control'})
    need(result['status'] == 'FOUND' and result['stats']['backtracks'] >= 1, 'real failed branch and successful sibling')
    need([x[0] for x in result['solution']['placements']] == ['good', 'tail0'], 'bad marking removed on restore')
    controls.append({'id': records[-1]['id'], 'pass': True, 'backtracks': result['stats']['backtracks']})
    free = engine.build_cnf_model(2, (), active_guards=(), seed_bits=(), maximum_candidates=256)
    limits = dict(solve_limits, maximum_nodes=1)
    result = solve('control/node-budget-unknown', free, {'purpose': 'budget-control'}, limits)
    need(result['status'] == 'UNKNOWN' and result['solution'] is None and not result['trace_complete'],
         'no partial acceptance on node cutoff')
    controls.append({'id': records[-1]['id'], 'pass': True})
    empty = engine.build_cnf_model(0, (), active_guards=(), seed_bits=(), maximum_candidates=256)
    limits = dict(solve_limits, maximum_trace_events=2)
    result = solve('control/finished-trace-budget-unknown', empty, {'purpose': 'budget-control'}, limits)
    need(result['status'] == 'UNKNOWN' and result['solution'] is None and not result['trace_complete'],
         'missing terminal trace revokes even a discovered solution')
    controls.append({'id': records[-1]['id'], 'pass': True})
    try:
        engine.build_cnf_model(2, (), active_guards=(), seed_bits=(), maximum_candidates=1)
    except engine.BudgetExceeded:
        controls.append({'id': 'control/builder-rejects-cap-without-trimming', 'pass': True})
    else:
        raise ValueError('builder must reject whole oversized inventory')

    summary = {'schema': 'ROOT-finite-point-calibration-summary-v1', 'status': 'PASS',
        'case_count': len(rows), 'assignment_checks': sum(m['assignment_checks'] for r in rows for m in r['modes']),
        'prefix_checks': sum(m['prefix_checks'] for r in rows for m in r['modes']),
        'solves': len(records), 'controls': controls, 'cases': rows,
        'truth_sets_match': True, 'unit_closures_match': True, 'every_trace_independently_audited': True,
        'scope': 'finite identity-grounded singleton unit-point calibration',
        'learned_markings': False, 'RL_used': False, 'new_mathematical_theorems': 0,
        'fixed_universal_Wang_set': False, 'full_master_contract_qualification': False,
        'proof_search_advantage_established': False,
        'plan_sha256': hashlib.sha256(plan_raw).hexdigest(),
        'worker_began_ns': BEGAN_NS, 'worker_before_output_ns': time.clock_gettime_ns(time.CLOCK_MONOTONIC),
        'kernel_self_peak_before_output_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    payloads = {'oracle-results.json': oracle_result, 'calibration-results.json': {
        'schema': 'ROOT-finite-point-calibration-results-v1', 'records': records}, 'summary.json': summary}
    output_bytes = 0
    for name, value in payloads.items():
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()+b'\n'
        output_bytes += len(raw)
        need(output_bytes <= plan['maximum_output_bytes'], 'bounded complete output')
        with (output/name).open('xb') as stream:
            stream.write(raw)
    print(json.dumps({'status': 'PASS', 'solves': len(records), 'output_bytes': output_bytes}, sort_keys=True), flush=True)


if __name__ == '__main__':
    need(len(sys.argv) == 2, 'explicit sole frozen plan path')
    main(sys.argv[1])
