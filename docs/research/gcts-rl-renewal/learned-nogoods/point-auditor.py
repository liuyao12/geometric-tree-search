"""Source-only independent auditor for saved finite unit-point solve wires.

No engine imports, search, CNF builder, IO, clock or resource authority. The
checker rebuilds only states and graphs explicitly present in the saved trace.
An UNKNOWN trace is a checked prefix, never a solution/exhaustion certificate.
"""
VERSION = 'independent-raw-unit-point-trace-auditor-v1'
_STATS = ('graph_rebuilds', 'placements', 'forced_placements', 'branch_decisions',
          'backtracks', 'restores', 'capacity_rejections', 'marking_rejections',
          'maximum_frontier_points', 'maximum_candidate_nodes',
          'maximum_incidence_edges', 'complete_solutions_checked')


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, minimum=None):
    _need(type(value) is int and (minimum is None or value >= minimum),
          'literal integer required; Boolean is not an integer')
    return value


def _keys(value, names):
    _need(type(value) is dict and all(type(k) is str for k in value)
          and set(value) == set(names), 'exact object fields: ' + ','.join(names))


def _same(actual, expected):
    """Typed wire equality: in particular True must never equal integer one."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return set(actual) == set(expected) and all(_same(actual[k], v) for k, v in expected.items())
    if type(expected) is list:
        return len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    return type(expected) in (str, int, bool, type(None)) and actual == expected


def _point(row):
    _need(type(row) is list and len(row) == 2, 'point is an integer pair')
    return (_integer(row[0]), _integer(row[1]))


def _marks(rows):
    _need(type(rows) is list, 'complete sparse marking list')
    out = {}
    for row in rows:
        _need(type(row) is list and len(row) == 3, 'marking triple')
        p = _point(row[:2])
        _need(p not in out, 'one assigned value per marking point')
        out[p] = _integer(row[2])
    return out


def _model(raw):
    _keys(raw, ('schema', 'marking_version', 'transformations', 'multiplicity',
                'roots', 'fixed_marks', 'candidates'))
    _need(raw['schema'] == 'finite-grounded-unit-point-model-v1'
          and raw['transformations'] == 'identity_only'
          and raw['multiplicity'] == 'each_candidate_at_most_once', 'supported finite unit model')
    _need(type(raw['marking_version']) is str and bool(raw['marking_version']), 'explicit marking epoch')
    _need(type(raw['roots']) is list and type(raw['candidates']) is list, 'complete original inventories')
    roots = {}
    for row in raw['roots']:
        _need(type(row) is list and len(row) == 3, 'root triple')
        p = _point(row[:2])
        _need(_integer(row[2]) == 0 and p not in roots, 'unique generation-zero required roots')
        roots[p] = row[2]
    fixed = _marks(raw['fixed_marks'])
    candidates, by_name = [], {}
    for row in raw['candidates']:
        _keys(row, ('name', 't', 'm'))
        name = row['name']
        _need(type(name) is str and bool(name) and name not in by_name, 'unique nonempty candidate ID')
        _need(type(row['t']) is list and len(row['t']) == 1
              and type(row['t'][0]) is list and len(row['t'][0]) == 3, 'singleton positive unit support')
        base = _point(row['t'][0][:2])
        _need(_integer(row['t'][0][2]) == 1 and base in roots, 'unit support inside original roots')
        c = (name, base, _marks(row['m']))
        candidates.append(c)
        by_name[name] = c
    return roots, fixed, candidates, by_name


def _compose(placements, roots, fixed, by_name):
    _need(type(placements) is list, 'chronological placement list')
    filled, marks, selected = set(), dict(fixed), set()
    out = []
    for row in placements:
        _need(type(row) is list and len(row) == 2, 'placement ID/generation pair')
        name, generation = row
        _need(type(name) is str and name in by_name and name not in selected, 'original distinct placement ID')
        _, base, ports = by_name[name]
        _need(_integer(generation) == roots[base] + 1 and base not in filled, 'exact generation and unit capacity')
        for p, value in ports.items():
            _need(p not in marks or marks[p] == value, 'all current/fixed marking overlaps agree')
            marks[p] = value
        filled.add(base)
        selected.add(name)
        out.append([name, generation])
    return {'placements': out, 'filled': [list(p) for p in sorted(filled)],
            'marks': [[p[0], p[1], v] for p, v in sorted(marks.items())]}, filled, marks


def _state(raw, roots, fixed, by_name):
    _keys(raw, ('placements', 'filled', 'marks'))
    expected, filled, marks = _compose(raw['placements'], roots, fixed, by_name)
    _need(_same(raw, expected), 'complete state differs from original-candidate/fixed-mark recomposition')
    return expected, filled, marks


def _graph(state, roots, candidates):
    filled = {tuple(p) for p in state['filled']}
    marks = {tuple(row[:2]): row[2] for row in state['marks']}
    frontier = {p: [] for p in roots if p not in filled}
    reverse, dependencies, capacity, marking = [], {}, 0, 0
    for name, base, ports in candidates:  # Original inventory order is significant.
        for p in set(ports) | {base}:
            dependencies.setdefault(p, []).append(name)
        if base in filled:
            capacity += 1
        elif any(p in marks and marks[p] != v for p, v in ports.items()):
            marking += 1
        else:
            frontier[base].append(name)
            reverse.append([name, [list(base)]])
    wire = {'point_candidates': [[list(p), ids] for p, ids in sorted(frontier.items())],
            'candidate_points': reverse,
            'dependencies': [[list(p), ids] for p, ids in sorted(dependencies.items())],
            'frontier_generations': [[p[0], p[1], roots[p]] for p in sorted(frontier)]}
    return wire, frontier, capacity, marking


def _frame(state):
    return {'state': state, 'stage': 'graph', 'outcome': None, 'menu': [],
            'index': 0, 'kind': None, 'active': None, 'frontier': None}


def audit_result(result, allow_unknown=False):
    """Return a small data-only audit report; raise ValueError on a defect.

    With allow_unknown=True a valid interrupted prefix may pass, but its report
    grants neither a solution nor finite exhaustion. No unrecorded restoration,
    runtime identity, external resource bound or CNF equivalence is certified.
    """
    _need(type(allow_unknown) is bool, 'literal allow_unknown Boolean')
    _keys(result, ('schema', 'version', 'status', 'unknown_reason', 'model', 'solution',
                   'root_state', 'root_state_persistent', 'limits', 'work_counts', 'stats',
                   'trace', 'trace_complete', 'scope', 'independent_oracle_checked',
                   'full_contract_qualified', 'learned_clause_soundness_qualified', 'resource_qualified'))
    _need(result['schema'] == 'finite-unit-point-gcts-result-v1'
          and result['version'] == 'finite-grounded-unit-point-gcts-v1'
          and result['scope'] == 'finite_identity_grounded_single_unit_support_only', 'exact result scope/version')
    status = result['status']
    _need(type(status) is str and status in ('FOUND', 'EXHAUSTED_FINITE_MARKED_MODEL', 'UNKNOWN'), 'known status')
    unknown = status == 'UNKNOWN'
    _need(not unknown or allow_unknown, 'UNKNOWN requires explicit prefix-audit permission')
    _need(result['trace_complete'] is (not unknown) and result['root_state_persistent'] is True,
          'truthful completion/restoration declarations')
    for flag in ('independent_oracle_checked', 'full_contract_qualified',
                 'learned_clause_soundness_qualified', 'resource_qualified'):
        _need(result[flag] is False, 'no inherited wider qualification: ' + flag)
    limits, counts, stats = result['limits'], result['work_counts'], result['stats']
    _keys(limits, ('root_points', 'nodes', 'candidate_checks', 'trace_events'))
    _need(_integer(limits['root_points']) == 128, 'unchanged root ceiling')
    _keys(counts, ('nodes', 'candidate_checks', 'trace_events'))
    for key in counts:
        _integer(limits[key], 1)
        _need(0 <= _integer(counts[key]) <= limits[key], 'work count inside declared limit')
    _keys(stats, _STATS)
    for value in stats.values():
        _integer(value, 0)
    roots, fixed, candidates, by_name = _model(result['model'])
    root, _, _ = _compose([], roots, fixed, by_name)
    _state(result['root_state'], roots, fixed, by_name)
    _need(_same(result['root_state'], root), 'exact original empty-placement root')
    trace = result['trace']
    _need(type(trace) is list and counts['trace_events'] == len(trace), 'all emitted events retained')
    reason = result['unknown_reason']
    if unknown:
        _need(result['solution'] is None and type(reason) is str, 'UNKNOWN has no accepted solution')
        reason_keys = {'declared nodes limit': 'nodes', 'declared candidate_checks limit': 'candidate_checks',
                       'declared trace_events limit': 'trace_events'}
        if reason == 'declared root-point calibration ceiling':
            _need(len(roots) > 128 and not trace and all(v == 0 for v in counts.values())
                  and all(v == 0 for v in stats.values()), 'root-ceiling UNKNOWN before search')
        else:
            _need(reason in reason_keys and counts[reason_keys[reason]] == limits[reason_keys[reason]],
                  'actual declared exhausted work counter')
            _need(len(roots) <= 128, 'root ceiling precedes search budgets')
    else:
        _need(reason is None and len(roots) <= 128, 'complete result within root scope')
    observed = {key: 0 for key in _STATS}
    stack, found, finished, interrupted = [_frame(root)], None, False, False
    event_fields = {
        'graph': ('point_candidates', 'candidate_points', 'dependencies', 'frontier_generations'),
        'dead': ('points',), 'forced': ('point', 'candidates', 'generation'),
        'branch': ('point', 'candidates', 'generation'), 'place': ('candidate', 'parent_state'),
        'restore': ('from_candidate',), 'solution': (), 'finished': ('status',)}
    for event_index, event in enumerate(trace):
        _need(type(event) is dict and type(event.get('kind')) is str and event['kind'] in event_fields,
              'known complete event object')
        kind = event['kind']
        _keys(event, ('kind', 'state') + event_fields[kind])
        state, filled, _ = _state(event['state'], roots, fixed, by_name)
        _need(not finished and (not interrupted or kind == 'restore'), 'no continuation after interrupted unwind/finish')
        top = stack[-1]
        if kind == 'place':
            _need(top['stage'] == 'next' and top['index'] < len(top['menu']), 'placement at next parent menu entry')
            name = top['menu'][top['index']]
            _need(type(event['candidate']) is str and event['candidate'] == name
                  and _same(event['parent_state'], top['state']), 'ordered original menu and exact parent')
            child, _, _ = _compose(top['state']['placements'] + [[name, roots[by_name[name][1]] + 1]],
                                   roots, fixed, by_name)
            _need(_same(state, child), 'exact single-candidate child')
            top['index'] += 1
            top['active'], top['stage'] = name, 'child'
            observed['placements'] += 1
            observed['forced_placements'] += int(top['kind'] == 'forced')
            stack.append(_frame(child))
            continue
        if kind == 'restore':
            _need(len(stack) > 1, 'restore has actual outstanding child')
            parent = stack[-2]
            _need(parent['stage'] == 'child' and type(event['from_candidate']) is str
                  and event['from_candidate'] == parent['active'] and _same(state, parent['state']),
                  'exact full parent restore and matching child ID')
            if top['stage'] != 'done':
                _need(unknown, 'complete traversal cannot restore an unfinished child')
                interrupted = True
                outcome = 'unknown'
            else:
                outcome = top['outcome']
            stack.pop()
            observed['restores'] += 1
            if outcome is True:
                parent['stage'], parent['outcome'] = 'done', True
            elif outcome is False:
                observed['backtracks'] += 1
                if parent['index'] < len(parent['menu']):
                    parent['stage'] = 'next'
                else:
                    parent['stage'], parent['outcome'] = 'done', False
            else:
                _need(unknown, 'interrupted restore only in UNKNOWN')
                interrupted = True
                parent['stage'], parent['outcome'] = 'done', 'unknown'
            continue
        _need(_same(state, top['state']), 'event belongs to current stack state')
        if kind == 'graph':
            _need(top['stage'] == 'graph', 'one exhaustive graph per entered node')
            expected, frontier, capacity, marking = _graph(state, roots, candidates)
            for key, value in expected.items():
                _need(_same(event[key], value), 'complete graph/reverse/dependency field: ' + key)
            top['frontier'] = frontier
            top['stage'] = 'dead' if any(not ids for ids in frontier.values()) else ('solution' if not frontier else 'decision')
            observed['graph_rebuilds'] += 1
            observed['capacity_rejections'] += capacity
            observed['marking_rejections'] += marking
            observed['maximum_frontier_points'] = max(observed['maximum_frontier_points'], len(frontier))
            observed['maximum_candidate_nodes'] = max(observed['maximum_candidate_nodes'], len(expected['candidate_points']))
            observed['maximum_incidence_edges'] = max(observed['maximum_incidence_edges'], len(expected['candidate_points']))
        elif kind == 'dead':
            _need(top['stage'] == 'dead' and _same(event['points'],
                  [list(p) for p, ids in sorted(top['frontier'].items()) if not ids]), 'all global dead points before any move')
            top['stage'], top['outcome'] = 'done', False
        elif kind in ('forced', 'branch'):
            _need(top['stage'] == 'decision', 'decision only after full live frontier graph')
            frontier = top['frontier']
            singles = [(p, ids) for p, ids in frontier.items() if len(ids) == 1]
            p, ids = min(singles or list(frontier.items()), key=lambda item: (roots[item[0]], len(item[1]), item[0]))
            expected_kind = 'forced' if singles else 'branch'
            _need(kind == expected_kind and _same(event['point'], list(p))
                  and _same(event['candidates'], ids) and _integer(event['generation']) == roots[p],
                  'global forced then earliest generation/degree/point order; original candidate menu')
            top['kind'], top['menu'], top['stage'] = kind, list(ids), 'next'
            observed['branch_decisions'] += int(kind == 'branch')
        elif kind == 'solution':
            _need(top['stage'] == 'solution' and filled == set(roots) and found is None, 'one exact whole-domain solution')
            found = state
            observed['complete_solutions_checked'] += 1
            top['stage'], top['outcome'] = 'done', True
        elif kind == 'finished':
            _need(not unknown and event_index == len(trace) - 1 and len(stack) == 1
                  and top['stage'] == 'done' and type(top['outcome']) is bool
                  and event['status'] == status and _same(state, root), 'complete root unwind then terminal event')
            _need((status == 'FOUND') is top['outcome'], 'terminal traversal outcome agrees')
            finished = True
    graphs = observed['graph_rebuilds']
    solution_checks = sum(len(e['state']['placements']) for e in trace if e['kind'] == 'solution')
    check_lower_bound = len(candidates) * (1 + graphs) + solution_checks if graphs else 0
    if unknown:
        _need(counts['nodes'] >= graphs and counts['candidate_checks'] >= check_lower_bound,
              'UNKNOWN counters cover all observed complete work')
        for key, value in observed.items():
            _need(stats[key] >= value, 'UNKNOWN statistics cover observed prefix: ' + key)
    else:
        _need(finished and len(stack) == 1, 'complete terminal event and entire restoration stack')
        _need(counts['nodes'] == graphs and counts['candidate_checks'] == len(candidates) * (1 + graphs) + solution_checks,
              'exact complete node/validation/full-scan/solution work counts')
        _need(_same(stats, observed), 'exact complete statistics independently reconstructed from trace')
        if status == 'FOUND':
            _need(found is not None and _same(result['solution'], found), 'exact final independently recomposed solution')
        else:
            _need(found is None and result['solution'] is None, 'full finite exhaustion has no solution')
    return {'schema': 'independent-unit-point-trace-audit-v1', 'auditor_version': VERSION,
            'status': status, 'valid_saved_trace': True, 'complete': not unknown,
            'exact_solution_accepted': not unknown and status == 'FOUND',
            'finite_exhaustion_accepted': not unknown and status == 'EXHAUSTED_FINITE_MARKED_MODEL',
            'unknown_prefix_only': unknown, 'observed_events': len(trace), 'observed_graphs': graphs,
            'observed_restores': observed['restores'], 'unresolved_recorded_stack_depth': len(stack) - 1,
            'unrecorded_runtime_restoration_certified': False,
            'full_contract_qualified': False, 'resource_qualified': False,
            'CNF_equivalence_qualified': False, 'Q_or_theorem_acceptance': False}
