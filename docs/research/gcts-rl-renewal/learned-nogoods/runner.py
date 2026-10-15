"""Fresh finite failed-context learning and four-arm reused-catalogue pilot.

No learned clause, expected query answer or proof route is an input. Discovery
uses the original point model. Only complete exhausted query contexts propose
the negation of their WHOLE boundary prefix. A direct Boolean oracle certifies
original-context entailment before the first two new clauses can be selected.
"""
import time
BEGAN = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
import hashlib
import json
from pathlib import Path
import resource
import sys
import types


def need(value, message):
    if not value:
        raise ValueError(message)


def stamp():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def load_source(name, item):
    raw = Path(item['path']).read_bytes()
    need(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], 'frozen ' + name)
    if name == 'cases':
        return json.loads(raw)
    module = types.ModuleType('actual_nogood_' + name)
    module.__file__ = item['path']
    sys.modules[module.__name__] = module
    exec(compile(raw, item['path'], 'exec'), module.__dict__)
    return module


def satisfying_bits(clauses):
    return tuple(tuple((i, 1 if sign == 1 else 0) for i, sign in clause) for clause in clauses)


def canonical_clause(clause):
    return tuple(sorted(tuple(item) for item in clause))


def clause_true(clause, bits):
    return any(bits[i] == (1 if sign == 1 else 0) for i, sign in clause)


def main(plan_path):
    plan_raw = Path(plan_path).read_bytes()
    plan = json.loads(plan_raw)
    need(plan['schema'] == 'ROOT-certified-nogood-comparison-plan-v1', 'exact plan schema')
    output = Path(plan['output_directory'])
    need(output.is_dir() and not list(output.iterdir()), 'fresh actual output')
    modules = {key: load_source(key, item) for key, item in plan['inputs'].items()}
    engine, oracle, point_auditor = modules['engine'], modules['oracle'], modules['point_auditor']
    ordinary, verifier = modules['ordinary'], modules['verifier']
    declared = {case['id']: case for case in modules['cases']['cases']}
    document = {'schema': 'finite-certified-nogood-comparison-v1', 'cases': [],
        'config': plan, 'source_loading_complete_ns': stamp(),
        'measurement': 'One fresh suite; modules loaded once, every solver state/model fresh. Replayed catalogue, no held-out claim.'}
    arm_names = ('ordinary_no', 'ordinary_learned', 'point_no', 'point_learned')

    def deadline():
        need(stamp()-BEGAN < plan['worker_seconds']*10**9, 'whole worker budget')

    def boolean_check(result, seeds, accepted, point):
        if result['status'] == 'UNKNOWN':
            need(result['solution'] is None and result['trace_complete'] is False,
                 'UNKNOWN retains no accepted proof or countermodel')
            return
        extensions = [bits for bits in accepted if all(bits[i] == b for i, b in seeds)]
        expected = 'FOUND' if extensions else ('EXHAUSTED_FINITE_MARKED_MODEL' if point else 'EXHAUSTED_FINITE_CNF')
        # Each representation keeps its own exact finite-exhaustion label and
        # work units. Only the semantic query outcome is compared across them.
        need(result['status'] == expected and result['trace_complete'], 'whole query outcome against original F')
        if expected == 'FOUND':
            if point:
                marks = {(x, y): value for x, y, value in result['solution']['marks']}
                bits = [marks[6*i, 2] for i in range(len(accepted[0]))]
            else:
                bits = [b for _, b in result['solution']]
            need(bits in extensions, 'complete original-F countermodel')

    def run_point(n, clauses, active, seeds, accepted):
        deadline(); began = stamp()
        model = engine.build_cnf_model(n, satisfying_bits(clauses), active_guards=tuple(active),
            seed_bits=tuple(tuple(x) for x in seeds), maximum_candidates=plan['maximum_candidates'])
        built = stamp()
        result = engine.solve(model, **plan['point_limits'])
        solved = stamp()
        audit = point_auditor.audit_result(result, allow_unknown=result['status'] == 'UNKNOWN')
        boolean_check(result, seeds, accepted, True)
        checked = stamp()
        return result, audit, {'build_ns': built-began, 'solve_ns': solved-built,
            'check_ns': checked-solved, 'inclusive_ns': checked-began}

    def run_ordinary(n, clauses, seeds, accepted):
        deadline(); began = stamp()
        encoded = satisfying_bits(clauses)
        boundary = tuple(tuple(x) for x in seeds)
        built = stamp()
        result = ordinary.solve_cnf(n, encoded, boundary, **plan['ordinary_limits'])
        solved = stamp()
        audit = verifier.verify_ordinary_result(result)
        boolean_check(result, seeds, accepted, False)
        checked = stamp()
        return result, audit, {'build_ns': built-began, 'solve_ns': solved-built,
            'check_ns': checked-solved, 'inclusive_ns': checked-began}

    # Discovery is fully completed for both original contexts before replay.
    for case_id in plan['case_ids']:
        original = declared[case_id]
        n, clauses = original['variables'], original['clauses']
        case_began = stamp()
        oracle_began = stamp()
        truth = oracle.evaluate_case(original)
        accepted = truth['modes'][1]['accepted_assignments']
        need(bool(accepted), 'declared discovery contexts have a nonvacuous original model')
        oracle_end = stamp()
        queries = [{'i': i, 'j': j, 'b': b, 'c': c,
                    'seeds': sorted([[i, b], [j, 1-c]])}
                   for i in range(n) for j in range(n) if i != j for b in (0, 1) for c in (0, 1)]
        case = {'original': original, 'queries': queries, 'discovery': [], 'discovery_audits': [],
            'learned': [], 'proposal_log': [], 'arms': {name: [] for name in arm_names},
            'point_arm_audits': {name: [] for name in arm_names if name.startswith('point_')},
            'ordinary_arm_audits': {name: [] for name in arm_names if name.startswith('ordinary_')},
            'timings': {'oracle_ns': oracle_end-oracle_began, 'discovery': [],
                        'certification_ns': 0, 'replay': {name: [] for name in arm_names}},
            'original_oracle': truth, 'execution_order': []}
        original_keys = {canonical_clause(c) for c in clauses}
        seen = set()
        for index, query in enumerate(queries):
            result, audit, timing = run_point(n, clauses, range(len(clauses)), query['seeds'], accepted)
            case['discovery'].append(result); case['discovery_audits'].append(audit)
            case['timings']['discovery'].append(timing)
            if result['status'] != 'EXHAUSTED_FINITE_MARKED_MODEL':
                continue
            certify_began = stamp()
            candidate = canonical_clause([[i, 1 if bit == 0 else -1] for i, bit in query['seeds']])
            entailed = all(clause_true(candidate, bits) for bits in accepted)
            new = candidate not in original_keys and candidate not in seen
            selected = entailed and new and len(case['learned']) < plan['maximum_learned_clauses']
            case['proposal_log'].append({'discovery_query_index': index, 'clause': [list(x) for x in candidate],
                'is_original': candidate in original_keys, 'is_duplicate': candidate in seen,
                'entailed': entailed, 'selected': selected})
            need(entailed, 'failed full prefix must negate to an original-context consequence')
            if selected:
                case['learned'].append({'clause': [list(x) for x in candidate], 'discovery_query_index': index})
            seen.add(candidate)
            case['timings']['certification_ns'] += stamp()-certify_began
        case['timings']['whole_discovery_ns'] = stamp()-case_began
        document['cases'].append(case)

    # Selection is now frozen. Rotate arm order within each predeclared query;
    # no outcome, benefit, proof length or timing affects that order.
    discovery_finished = stamp()
    for case_index, case in enumerate(document['cases']):
        original = case['original']; n = original['variables']
        original_clauses = original['clauses']
        learned = [entry['clause'] for entry in case['learned']]
        combined = original_clauses + learned
        accepted = case['original_oracle']['modes'][1]['accepted_assignments']
        for query_index, query in enumerate(case['queries']):
            offset = (query_index+case_index) % len(arm_names)
            order = arm_names[offset:]+arm_names[:offset]
            case['execution_order'].append(list(order))
            for arm in order:
                if arm.startswith('point_'):
                    active = range(len(combined)) if arm.endswith('_learned') else range(len(original_clauses))
                    result, audit, timing = run_point(n, combined, active, query['seeds'], accepted)
                    case['point_arm_audits'][arm].append(audit)
                else:
                    clauses = combined if arm.endswith('_learned') else original_clauses
                    result, audit, timing = run_ordinary(n, clauses, query['seeds'], accepted)
                    case['ordinary_arm_audits'][arm].append(audit)
                case['arms'][arm].append(result)
                case['timings']['replay'][arm].append(timing)
        # The two point arms must preserve the entire decorated inventory except
        # the added guard markings, checked independently by the whole verifier.
    replay_finished = stamp()
    verification_began = stamp()
    independent = verifier.verify_experiment(document)
    verification_finished = stamp()
    document['independent_whole_verification'] = independent
    document['timing_boundaries'] = {'worker_began_ns': BEGAN, 'discovery_finished_ns': discovery_finished,
        'replay_finished_ns': replay_finished, 'whole_verification_began_ns': verification_began,
        'whole_verification_finished_ns': verification_finished}

    summaries = []
    for case in document['cases']:
        row = {'case_id': case['original']['id'], 'query_count': len(case['queries']),
            'learned': case['learned'], 'exhausted_discovery_queries': len(case['proposal_log']),
            'whole_discovery_ns': case['timings']['whole_discovery_ns'], 'arms': {}}
        for arm, results in case['arms'].items():
            counts = {'FOUND': 0, 'EXHAUSTED_FINITE_MARKED_MODEL': 0,
                      'EXHAUSTED_FINITE_CNF': 0, 'UNKNOWN': 0}
            for result in results:
                counts[result['status']] += 1
            row['arms'][arm] = {'outcomes': counts,
                'inclusive_ns': sum(x['inclusive_ns'] for x in case['timings']['replay'][arm]),
                'build_ns': sum(x['build_ns'] for x in case['timings']['replay'][arm]),
                'solve_ns': sum(x['solve_ns'] for x in case['timings']['replay'][arm]),
                'check_ns': sum(x['check_ns'] for x in case['timings']['replay'][arm]),
                'representation_counters':
                    ({key: sum(r['stats'][key] for r in results)
                      for key in ('branch_decisions', 'forced_placements', 'backtracks')}
                     if arm.startswith('point_') else
                     {key: sum(r['work_counts'][key] for r in results)
                      for key in ('branch_decisions', 'unit_decisions', 'conflicts',
                                  'assignments', 'restores', 'literal_checks')})}
        summaries.append(row)
    complete = all(result['status'] != 'UNKNOWN' for case in document['cases']
        for result in case['discovery'] + [r for results in case['arms'].values() for r in results])
    summary = {'schema': 'ROOT-certified-nogood-comparison-summary-v1', 'status': 'PASS' if complete else 'UNKNOWN',
        'cases': summaries, 'discovery_solves': sum(len(c['discovery']) for c in document['cases']),
        'replay_solves': sum(len(v) for c in document['cases'] for v in c['arms'].values()),
        'independent_verification': independent, 'plan_sha256': hashlib.sha256(plan_raw).hexdigest(),
        'whole_verification_ns': verification_finished-verification_began,
        'worker_began_ns': BEGAN, 'worker_before_output_ns': stamp(),
        'self_peak_before_output_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scope': 'Certified finite same-context propositional nogood learning and reused-query comparison',
        'RL_used': False, 'generalization_to_unseen_contexts': False, 'fixed_Wang_universality': False,
        'full_point_contract_qualified': False, 'Q_qualification_changed': False,
        'statistically_reproducible_speedup_established': False}
    written = 0
    for name, value in (('comparison-results.json', document), ('summary.json', summary)):
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()+b'\n'
        written += len(raw)
        need(written <= plan['maximum_output_bytes'], 'bounded complete result output')
        with (output/name).open('xb') as stream:
            stream.write(raw)
    print(json.dumps({'status': summary['status'], 'discovery_solves': summary['discovery_solves'],
        'replay_solves': summary['replay_solves'], 'output_bytes': written}, sort_keys=True), flush=True)


if __name__ == '__main__':
    need(len(sys.argv) == 2, 'sole frozen plan path')
    main(sys.argv[1])
