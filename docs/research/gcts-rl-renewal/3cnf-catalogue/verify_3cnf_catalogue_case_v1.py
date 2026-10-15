"""Unexecuted raw-wire catalogue verifier and same-prefix marking analysis.

No solver/point-engine imports, search, IO or clocks. Only original catalogue
construction is fixed. Truths, learned clauses and effect counts are computed
from each later supplied saved case; none are declared as expected outcomes.
"""
VERSION = 'independent-finite-3CNF-catalogue-verifier-v1'
_ARMS = ('ordinary_no', 'ordinary_learned', 'point_no', 'point_learned')


def _need(value, message):
    if not value:
        raise ValueError(message)


def _int(value, minimum=None):
    _need(type(value) is int and (minimum is None or value >= minimum), 'literal integer; Boolean is not integer')
    return value


def _fields(value, names):
    _need(type(value) is dict and all(name in value for name in names), 'required fields: ' + ','.join(names))


def _same(a, b):
    if type(a) is not type(b):
        return False
    if type(b) is dict:
        return set(a) == set(b) and all(_same(a[k], v) for k, v in b.items())
    if type(b) is list:
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return type(b) in (str, int, bool, type(None)) and a == b


def _contains(actual, expected):
    _fields(actual, expected)
    _need(all(_same(actual[k], v) for k, v in expected.items()), 'required report/proposal fields differ')


def _cnf(n, clauses):
    _need(0 <= _int(n) <= 4 and type(clauses) is list, 'finite at-most-four-variable CNF')
    for clause in clauses:
        _need(type(clause) is list, 'ordered clause list')
        seen = set()
        for literal in clause:
            _need(type(literal) is list and len(literal) == 2, 'signed literal [index,+/-1]')
            i, sign = _int(literal[0], 0), _int(literal[1])
            _need(i < n and sign in (-1, 1) and i not in seen, 'distinct valid literal ports')
            seen.add(i)


def _assignment(raw, n):
    _need(type(raw) is list, 'sorted assignment pairs')
    assignment = {}
    for pair in raw:
        _need(type(pair) is list and len(pair) == 2, 'assignment [index,bit]')
        i, bit = _int(pair[0], 0), _int(pair[1])
        _need(i < n and bit in (0, 1) and i not in assignment, 'distinct exact bit assignments')
        assignment[i] = bit
    _need(_same(raw, [[i, b] for i, b in sorted(assignment.items())]), 'assignment variable order')
    return assignment


def _truth(assignment, clause):
    return any(assignment[i] == (1 if sign == 1 else 0) for i, sign in clause)


def _models(n, clauses, seeds):
    given = _assignment(seeds, n)
    return [[(mask >> (n - 1 - i)) & 1 for i in range(n)] for mask in range(1 << n)
            if all(((mask >> (n - 1 - i)) & 1) == bit for i, bit in given.items())
            and all(any(((mask >> (n - 1 - i)) & 1) == (1 if sign == 1 else 0)
                        for i, sign in clause) for clause in clauses)]


def _normalized(clause):
    return [[i, sign] for i, sign in sorted(clause)]


def _point_model(n, clauses, seeds, active):
    """Independent complete finite bit/tuple/guard wire, never a builder call."""
    roots = [[6 * i, 0, 0] for i in range(n)]
    candidates = [{'name': 'B_' + str(i) + '_' + str(b), 't': [[6 * i, 0, 1]],
                   'm': [[6 * i, 2, b]]} for i in range(n) for b in (0, 1)]
    for c, clause in enumerate(clauses):
        roots.extend([[6 * c, 6, 0], [6 * c + 2, 6, 0]])
        for mask in range(1 << len(clause)):
            bits = [(mask >> (len(clause) - 1 - k)) & 1 for k in range(len(clause))]
            forbidden = all(bit != (1 if sign == 1 else 0) for bit, (_, sign) in zip(bits, clause))
            marks = [[6 * i, 2, bit] for (i, _), bit in zip(clause, bits)]
            marks.append([6 * c + 2, 8, int(forbidden)])
            candidates.append({'name': 'A_' + str(c) + '_' + ''.join(str(b) for b in bits),
                               't': [[6 * c, 6, 1]], 'm': marks})
        candidates.append({'name': 'R_' + str(c), 't': [[6 * c + 2, 6, 1]],
                           'm': [[6 * c + 2, 8, 0]] if c in active else []})
    return {'schema': 'finite-grounded-unit-point-model-v1',
            'marking_version': 'finite-grounded-unit-point-gcts-v1:guards=' + ','.join(str(i) for i in active),
            'transformations': 'identity_only', 'multiplicity': 'each_candidate_at_most_once',
            'roots': sorted(roots), 'fixed_marks': [[6 * i, 2, b] for i, b in seeds], 'candidates': candidates}


def _outcome(status, solution, models, point=False):
    exhausted = 'EXHAUSTED_FINITE_MARKED_MODEL' if point else 'EXHAUSTED_FINITE_CNF'
    _need(type(status) is str and status in ('FOUND', exhausted, 'UNKNOWN'), 'known result status')
    if status == 'FOUND':
        _need(type(solution) is list and any(_same(solution, row) for row in models), 'full satisfying witness under all original/query assumptions')
    elif status == exhausted:
        _need(solution is None and not models, 'complete refutation agrees with independent whole truth table')
    else:
        _need(solution is None, 'UNKNOWN supplies no accepted witness')


def _point_result(result, audit, model, n, models):
    _fields(result, ('schema', 'version', 'model', 'status', 'solution', 'root_state', 'trace_complete', 'trace', 'limits'))
    _need(result['schema'] == 'finite-unit-point-gcts-result-v1'
          and result['version'] == 'finite-grounded-unit-point-gcts-v1'
          and _same(result['model'], model), 'exact complete point inventory/epoch/boundary/guard wire')
    _need(_same(result['root_state'], {'placements': [], 'filled': [], 'marks': model['fixed_marks']}), 'fresh fixed-boundary point root')
    projection = None
    if result['status'] == 'FOUND':
        _fields(result['solution'], ('placements', 'filled', 'marks'))
        bits = {}
        _need(type(result['solution']['placements']) is list, 'complete selected placement list')
        bit_ids = {'B_' + str(i) + '_' + str(b): (i, b) for i in range(n) for b in (0, 1)}
        for pair in result['solution']['placements']:
            _need(type(pair) is list and len(pair) == 2 and type(pair[0]) is str and _int(pair[1]) == 1, 'actual generation-one placement')
            if pair[0] in bit_ids:
                i, bit = bit_ids[pair[0]]
                _need(i not in bits, 'unique variable bit witness')
                bits[i] = bit
        _need(len(bits) == n, 'every original Boolean variable has its bit tile')
        projection = [bits[i] for i in range(n)]
    if result['status'] != 'FOUND':
        _need(result['solution'] is None, 'point exhaustion/UNKNOWN has no accepted solution wire')
    _outcome(result['status'], projection, models, point=True)
    unknown = result['status'] == 'UNKNOWN'
    _need(result['trace_complete'] is (not unknown) and type(result['trace']) is list, 'point result completion')
    _contains(audit, {'schema': 'independent-unit-point-trace-audit-v1',
                      'auditor_version': 'independent-raw-unit-point-trace-auditor-v1',
                      'status': result['status'], 'valid_saved_trace': True, 'complete': not unknown,
                      'exact_solution_accepted': not unknown and result['status'] == 'FOUND',
                      'finite_exhaustion_accepted': not unknown and result['status'] == 'EXHAUSTED_FINITE_MARKED_MODEL',
                      'unknown_prefix_only': unknown, 'observed_events': len(result['trace'])})
    return result['status']


def _original_oracle(raw, original, models):
    n, clauses = original['variables'], original['clauses']
    all_bits = _models(n, [], [])
    _contains(raw, {'case_id': original['id'], 'variables': n,
                    'ordered_clause_occurrences': clauses, 'all_assignments': all_bits,
                    'clause_truth_rows': [[_truth(bits, clause) for clause in clauses] for bits in all_bits]})
    _fields(raw, ('modes',))
    _need(type(raw['modes']) is list and len(raw['modes']) == 2, 'both complete original truth-set modes')
    for mode, label, accepted in zip(raw['modes'], ('guards_unmarked', 'marked_guards_actually_placed'), (all_bits, models)):
        _contains(mode, {'mode': label, 'accepted_assignments': accepted, 'assignment_count': len(accepted)})


def _catalogue_original(index):
    _need(0 <= _int(index) < 70, 'catalogue index in the complete seventy-case declaration')
    subsets = [(a, b, c, d) for a in range(8) for b in range(a + 1, 8)
               for c in range(b + 1, 8) for d in range(c + 1, 8)]
    masks = subsets[index]
    clauses = [[[i, 1 if ((mask >> (2 - i)) & 1) else -1] for i in range(3)] for mask in masks]
    return {'id': 'T' + str(index).zfill(3), 'variables': 3, 'clauses': clauses, 'prefixes': []}


def _boundary_catalogue():
    return [[[i, bit]] for i in range(3) for bit in (0, 1)]


def _model_parts(model):
    roots = {tuple(row[:2]): row[2] for row in model['roots']}
    fixed = {tuple(row[:2]): row[2] for row in model['fixed_marks']}
    candidates = [(row['name'], tuple(row['t'][0][:2]),
                   {tuple(port[:2]): port[2] for port in row['m']}) for row in model['candidates']]
    return roots, fixed, candidates, {name: (base, ports) for name, base, ports in candidates}


def _recompose(model, placements):
    """Fold original candidate definitions; never reuse the marked state union."""
    roots, fixed, candidates, named = _model_parts(model)
    _need(type(placements) is list, 'complete chronological selected prefix')
    selected, filled, marks, origins = set(), set(), dict(fixed), {}
    for p, value in fixed.items():
        origins[p] = [{'kind': 'fixed_seed', 'value': value}]
    for row in placements:
        _need(type(row) is list and len(row) == 2 and type(row[0]) is str and row[0] in named,
              'actual original candidate ID/generation')
        name, generation = row
        base, ports = named[name]
        _need(name not in selected and base not in filled and _int(generation) == roots[base] + 1,
              'one selected candidate and exact unit t/generation')
        selected.add(name)
        filled.add(base)
        for p, value in ports.items():
            _need(p not in marks or marks[p] == value, 'whole selected m union agrees')
            marks[p] = value
            origins.setdefault(p, []).append({'kind': 'selected_candidate', 'candidate_id': name, 'value': value})
    wire = {'placements': [list(row) for row in placements], 'filled': [list(p) for p in sorted(filled)],
            'marks': [[p[0], p[1], value] for p, value in sorted(marks.items())]}
    return wire, filled, marks, origins


def _domains(model, filled, marks):
    roots, _, candidates, _ = _model_parts(model)
    domains = {p: [] for p in roots if p not in filled}
    reverse, dependencies = [], {}
    for name, base, ports in candidates:
        for p in set(ports) | {base}:
            dependencies.setdefault(p, []).append(name)
        if base not in filled and all(p not in marks or marks[p] == value for p, value in ports.items()):
            domains[base].append(name)
            reverse.append([name, [list(base)]])
    graph = {'point_candidates': [[list(p), names] for p, names in sorted(domains.items())],
             'candidate_points': reverse,
             'dependencies': [[list(p), names] for p, names in sorted(dependencies.items())],
             'frontier_generations': [[p[0], p[1], roots[p]] for p in sorted(domains)]}
    return domains, graph


def _shadow(result, baseline_model, marked_model, boundary_index, seeds):
    """Post-solve analysis at identical selected IDs, not two trajectory indexes."""
    counters = {'graph_observations': 0, 'baseline_legal_candidate_observations': 0,
                'marked_legal_candidate_observations': 0, 'additional_exclusion_observations': 0,
                'reduced_domain_observations': 0, 'zero_domains_created_observations': 0,
                'singletons_created_observations': 0, 'baseline_zero_domain_observations': 0,
                'marked_zero_domain_observations': 0, 'baseline_singleton_observations': 0,
                'marked_singleton_observations': 0}
    first_exclusion, first_effect = None, None
    _, _, ordered_candidates, _ = _model_parts(marked_model)
    _, _, _, baseline_named = _model_parts(baseline_model)
    for event_index, event in enumerate(result['trace']):
        _need(type(event) is dict and type(event.get('kind')) is str, 'complete raw point trace event')
        if event['kind'] != 'graph':
            continue
        _fields(event, ('state', 'point_candidates', 'candidate_points', 'dependencies', 'frontier_generations'))
        _fields(event['state'], ('placements', 'filled', 'marks'))
        prefix = event['state']['placements']
        baseline_state, baseline_filled, baseline_marks, _ = _recompose(baseline_model, prefix)
        marked_state, marked_filled, marked_marks, origins = _recompose(marked_model, prefix)
        _need(_same(event['state'], marked_state) and baseline_filled == marked_filled,
              'actual marked graph state and identical legal padded-baseline prefix')
        baseline, _ = _domains(baseline_model, baseline_filled, baseline_marks)
        marked, marked_graph = _domains(marked_model, marked_filled, marked_marks)
        for field, expected in marked_graph.items():
            _need(_same(event[field], expected), 'actual marked complete t/m graph in shadow: ' + field)
        _need(set(baseline) == set(marked), 'same selected t support gives the same complete frontier')
        counters['graph_observations'] += 1
        baseline_legal = {name for names in baseline.values() for name in names}
        marked_legal = {name for names in marked.values() for name in names}
        _need(marked_legal <= baseline_legal, 'additional guards cannot create a baseline-illegal candidate at identical prefix')
        excluded = baseline_legal - marked_legal
        counters['baseline_legal_candidate_observations'] += len(baseline_legal)
        counters['marked_legal_candidate_observations'] += len(marked_legal)
        counters['additional_exclusion_observations'] += len(excluded)
        if first_exclusion is None and excluded:
            name, base, ports = next(c for c in ordered_candidates if c[0] in excluded)
            p = next(p for p, value in sorted(ports.items()) if p in marked_marks and marked_marks[p] != value)
            baseline_ports = baseline_named[name][1]
            _need(p not in baseline_ports or p not in baseline_marks or baseline_marks[p] == baseline_ports[p],
                  'baseline candidate is compatible using its own actual port definition')
            first_exclusion = {'graph_event_index': event_index, 'candidate_id': name,
                'support_point': list(base), 'selected_prefix': [list(row) for row in prefix],
                'conflicting_m_port': list(p),
                'marked_candidate_port_assigned': True, 'marked_candidate_value': ports[p],
                'baseline_candidate_port_assigned': p in baseline_ports,
                'baseline_candidate_value': baseline_ports[p] if p in baseline_ports else None,
                'marked_state_port_assigned': True, 'marked_state_value': marked_marks[p],
                'baseline_port_assigned': p in baseline_marks,
                'baseline_state_value': baseline_marks[p] if p in baseline_marks else None,
                'marked_state_port_origins': origins[p],
                'baseline_prefix_state': baseline_state}
        for p in sorted(marked):
            before, after = len(baseline[p]), len(marked[p])
            counters['baseline_zero_domain_observations'] += int(before == 0)
            counters['marked_zero_domain_observations'] += int(after == 0)
            counters['baseline_singleton_observations'] += int(before == 1)
            counters['marked_singleton_observations'] += int(after == 1)
            counters['reduced_domain_observations'] += int(after < before)
            made_zero, made_singleton = before > 0 and after == 0, before > 1 and after == 1
            counters['zero_domains_created_observations'] += int(made_zero)
            counters['singletons_created_observations'] += int(made_singleton)
            if first_effect is None and (made_zero or made_singleton):
                first_effect = {'graph_event_index': event_index, 'point': list(p),
                    'baseline_candidates': list(baseline[p]), 'marked_candidates': list(marked[p]),
                    'kind': 'zero_created' if made_zero else 'singleton_created'}
    return {'boundary_index': boundary_index, 'seed_bits': seeds, 'point_learned_status': result['status'],
            'analysis_only': True, 'counts_are_repeated_observations': True,
            'counts_are_unique_candidates': False, 'counters': counters,
            'first_additional_exclusion': first_exclusion, 'first_zero_or_singleton_effect': first_effect,
            'unknown_trace_is_prefix_only': result['status'] == 'UNKNOWN',
            'claim_of_baseline_reaching_this_prefix': False}


def verify_case(case, ordinary_check):
    """One streamed case; caller supplies exact reviewed ordinary wire checker.

    Extra saved metadata is permitted. Root separately invokes the exact point
    raw trace auditor. This function never invokes a solver or point engine.
    """
    _need(callable(ordinary_check), 'trusted pinned ordinary checker supplied by ROOT')
    _fields(case, ('catalogue_index', 'original', 'discovery_boundaries', 'discovery', 'discovery_audits',
                   'proposal_log', 'learned', 'replay_boundaries', 'arms', 'point_arm_audits',
                   'ordinary_arm_audits', 'original_oracle'))
    index = _int(case['catalogue_index'], 0)
    original = _catalogue_original(index)
    _need(_same(case['original'], original), 'exact independent catalogue declaration for this index')
    n, clauses = original['variables'], original['clauses']
    _cnf(n, clauses)
    original_models = _models(n, clauses, [])
    _original_oracle(case['original_oracle'], original, original_models)
    discovery_boundaries = _boundary_catalogue()
    replay_boundaries = [[]] + discovery_boundaries
    _need(_same(case['discovery_boundaries'], discovery_boundaries)
          and _same(case['replay_boundaries'], replay_boundaries), 'all six discovery and seven replay boundaries in fixed order')
    _need(type(case['discovery']) is list and type(case['discovery_audits']) is list
          and len(case['discovery']) == len(case['discovery_audits']) == len(discovery_boundaries), 'all discovery wires/audits retained')
    original_keys = {tuple(tuple(lit) for lit in _normalized(clause)) for clause in clauses}
    selected, proposals, seen = [], [], set()
    point_limits, ordinary_limits = None, None
    discovery_counts = {'FOUND': 0, 'EXHAUSTED_FINITE_MARKED_MODEL': 0, 'UNKNOWN': 0}
    for boundary_index, (seeds, result, audit) in enumerate(zip(discovery_boundaries, case['discovery'], case['discovery_audits'])):
        expected = _point_model(n, clauses, seeds, list(range(len(clauses))))
        status = _point_result(result, audit, expected, n, _models(n, clauses, seeds))
        if point_limits is None:
            point_limits = result['limits']
        _need(_same(result['limits'], point_limits), 'one point count policy within this case')
        discovery_counts[status] += 1
        if status != 'EXHAUSTED_FINITE_MARKED_MODEL':
            continue
        clause = [[i, 1 if bit == 0 else -1] for i, bit in seeds]
        key = tuple(tuple(lit) for lit in clause)
        _need(all(_truth(bits, clause) for bits in original_models), 'negated entire exhausted boundary is original-F entailed')
        chosen = key not in original_keys and key not in seen and len(selected) < 2
        proposals.append({'discovery_boundary_index': boundary_index, 'clause': clause,
                          'is_original': key in original_keys, 'is_duplicate': key in seen,
                          'entailed': True, 'selected': chosen})
        if chosen:
            selected.append({'clause': clause, 'discovery_boundary_index': boundary_index})
        seen.add(key)
    _need(type(case['learned']) is list and len(case['learned']) == len(selected), 'exact first-two consequence selection')
    for actual, expected in zip(case['learned'], selected):
        _contains(actual, expected)
    _need(type(case['proposal_log']) is list and len(case['proposal_log']) == len(proposals), 'every exhausted proposal retained')
    for actual, expected in zip(case['proposal_log'], proposals):
        _contains(actual, expected)
    combined = clauses + [entry['clause'] for entry in selected]
    _need(_same(_models(n, combined, []), original_models), 'whole original satisfying set preserved by learned clauses')
    _need(type(case['arms']) is dict and set(case['arms']) == set(_ARMS), 'all four arms')
    for key, arms in (('point_arm_audits', ('point_no', 'point_learned')),
                      ('ordinary_arm_audits', ('ordinary_no', 'ordinary_learned'))):
        _need(type(case[key]) is dict and set(case[key]) == set(arms), 'complete replay audit maps')
        for arm in arms:
            _need(type(case[key][arm]) is list and len(case[key][arm]) == len(replay_boundaries), 'one raw audit per replay')
    replay_counts = {}
    for arm in _ARMS:
        _need(type(case['arms'][arm]) is list and len(case['arms'][arm]) == len(replay_boundaries), 'all seven replay results')
        counts = {'FOUND': 0, 'EXHAUSTED_FINITE_MARKED_MODEL' if arm.startswith('point') else 'EXHAUSTED_FINITE_CNF': 0, 'UNKNOWN': 0}
        for boundary_index, (seeds, result) in enumerate(zip(replay_boundaries, case['arms'][arm])):
            extensions = _models(n, clauses, seeds)
            if arm.startswith('point'):
                active = list(range(len(combined) if arm == 'point_learned' else len(clauses)))
                expected = _point_model(n, combined, seeds, active)
                status = _point_result(result, case['point_arm_audits'][arm][boundary_index], expected, n, extensions)
                _need(_same(result['limits'], point_limits), 'same point budgets in both replay arms/discovery')
            else:
                used = combined if arm == 'ordinary_learned' else clauses
                encoded = [[[i, int(sign == 1)] for i, sign in clause] for clause in used]
                _contains(result, {'variables': n, 'clauses': encoded, 'seed_bits': seeds})
                audit = ordinary_check(result)
                _contains(case['ordinary_arm_audits'][arm][boundary_index], audit)
                _fields(audit, ('schema', 'status', 'valid_saved_trace', 'complete', 'unknown_prefix_only',
                                'exact_solution_accepted', 'finite_exhaustion_accepted', 'full_truth_table_checked'))
                _contains(audit, {'schema': 'independent-ordinary-CNF-trace-audit-v1',
                    'verifier_version': 'independent-finite-certified-nogood-verifier-v1',
                    'status': result['status'], 'valid_saved_trace': True,
                    'complete': result['status'] != 'UNKNOWN', 'unknown_prefix_only': result['status'] == 'UNKNOWN',
                    'exact_solution_accepted': result['status'] == 'FOUND',
                    'finite_exhaustion_accepted': result['status'] == 'EXHAUSTED_FINITE_CNF', 'full_truth_table_checked': True})
                if ordinary_limits is None:
                    ordinary_limits = result['limits']
                _need(_same(result['limits'], ordinary_limits), 'same ordinary budget policy in both replay arms')
                status = result['status']
                solution = [bit for _, bit in result['solution']] if status == 'FOUND' else None
                _outcome(status, solution, extensions)
            counts[status] += 1
        replay_counts[arm] = counts
    shadows = []
    for boundary_index, (seeds, result) in enumerate(zip(replay_boundaries, case['arms']['point_learned'])):
        baseline = _point_model(n, combined, seeds, list(range(len(clauses))))
        marked = _point_model(n, combined, seeds, list(range(len(combined))))
        shadows.append(_shadow(result, baseline, marked, boundary_index, seeds))
    totals = {key: sum(row['counters'][key] for row in shadows) for key in shadows[0]['counters']}
    unknown_count = discovery_counts['UNKNOWN'] + sum(row['UNKNOWN'] for row in replay_counts.values())
    return {'schema': 'independent-3CNF-catalogue-case-audit-v1', 'version': VERSION,
            'valid_saved_case': True, 'all_boundaries_completed': unknown_count == 0,
            'catalogue_index': index, 'case_id': original['id'], 'original_solutions': original_models,
            'learned': selected, 'all_original_solutions_preserved': True,
            'discovery_outcomes': discovery_counts, 'replay_outcomes': replay_counts, 'unknown_count': unknown_count,
            'discovery_solves_checked': len(discovery_boundaries), 'replay_solves_checked': len(replay_boundaries) * len(_ARMS),
            'point_limits': point_limits, 'ordinary_limits': ordinary_limits,
            'marking_effect': {'analysis_only': True, 'identical_selected_prefixes': True,
                'counts_are_repeated_observations': True, 'counts_are_unique_candidates': False,
                'per_boundary': shadows, 'totals': totals},
            'point_trace_auditor_invocation_required_separately': True,
            'whole_cohort_order_coverage_required_separately': True,
            'timing_or_resource_admission': False, 'statistical_speedup': False,
            'full_point_contract_qualified': False, 'RL_accepted': False, 'original_Q_changed': False}
