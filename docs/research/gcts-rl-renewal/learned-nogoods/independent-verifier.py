"""Independent saved-wire Boolean/ordinary-trace verifier; unexecuted Source.

No imports, solver, point-engine call, IO or clock. Original declarations alone
are fixed below. Learned clauses and their truth sets are never supplied here.
"""
VERSION = 'independent-finite-certified-nogood-verifier-v1'
_ORIGINALS = [
    {'id': 'B07-long-range-shared-four', 'variables': 4,
     'clauses': [[[0, 1], [3, -1]], [[3, 1], [1, -1]], [[1, 1], [2, 1]], [[2, -1], [0, -1]]],
     'prefixes': [[], [[0, 0], [1, 1]], [[3, 1]]]},
    {'id': 'B08-three-port-and-shared-chain', 'variables': 4,
     'clauses': [[[0, 1], [2, -1], [3, 1]], [[0, -1], [1, 1]], [[1, -1], [2, 1]], [[3, -1], [1, -1]]],
     'prefixes': [[], [[0, 0], [2, 1]], [[1, 0]]]}
]
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


def _queries(n):
    return [{'i': i, 'j': j, 'b': b, 'c': c,
             'seeds': [[k, value] for k, value in sorted(((i, b), (j, 1 - c)))]}
            for i in range(n) for j in range(n) if i != j for b in (0, 1) for c in (0, 1)]


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


def _scan(assignment, clauses):
    return [{'index': ci, 'satisfied': any(i in assignment and assignment[i] == bit for i, bit in clause),
             'unassigned': [[i, bit] for i, bit in clause if i not in assignment]}
            for ci, clause in enumerate(clauses)]


def verify_ordinary_result(result):
    """Audit ordinary saved scan/tree/restore wire and complete truth semantics.

    UNKNOWN is a checked, exactly restored prefix, never a refutation/witness.
    The point engine and the ordinary implementation are not imported/called.
    """
    _fields(result, ('schema', 'variables', 'clauses', 'seed_bits', 'root_state', 'status', 'solution',
                     'trace', 'trace_complete', 'exhaustion_complete', 'root_restored', 'budget_stop',
                     'limits', 'work_counts', 'ordinary_origin', 'point_engine_conformance', 'learned_constraints_generated'))
    _need(result['schema'] == 'ordinary-finite-CNF-DPLL-result-v1'
          and result['ordinary_origin'] == 'chronological-clause-DPLL-first-solution', 'ordinary wire/version')
    n, clauses = result['variables'], result['clauses']
    _need(0 <= _int(n) <= 4 and type(clauses) is list and len(clauses) <= 8, 'ordinary finite complete clause list')
    signed = []
    for clause in clauses:
        _need(type(clause) is list, 'ordered ordinary clause')
        converted = []
        for pair in clause:
            _need(type(pair) is list and len(pair) == 2 and _int(pair[1]) in (0, 1), 'literal satisfying-bit pair')
            converted.append([_int(pair[0], 0), 1 if pair[1] == 1 else -1])
        signed.append(converted)
    _cnf(n, signed)
    _need(type(result['seed_bits']) is list, 'complete seed wire')
    root_dict = {}
    for pair in result['seed_bits']:
        _need(type(pair) is list and len(pair) == 2, 'seed pair')
        i, b = _int(pair[0], 0), _int(pair[1])
        _need(i < n and b in (0, 1) and i not in root_dict, 'unique valid seed')
        root_dict[i] = b
    root = [[i, b] for i, b in sorted(root_dict.items())]
    _need(_same(result['root_state'], root) and result['root_restored'] is True, 'exact original root restoration')
    _need(result['point_engine_conformance'] is False and result['learned_constraints_generated'] is False,
          'ordinary control has no point or discovery authority')
    status, unknown = result['status'], result['status'] == 'UNKNOWN'
    _need(status in ('FOUND', 'EXHAUSTED_FINITE_CNF', 'UNKNOWN')
          and result['trace_complete'] is (not unknown)
          and result['exhaustion_complete'] is (status == 'EXHAUSTED_FINITE_CNF'), 'truthful ordinary status flags')
    limits, counts, trace = result['limits'], result['work_counts'], result['trace']
    limit_names = ('maximum_nodes', 'maximum_literal_checks', 'maximum_trace_events')
    count_names = ('nodes', 'scans', 'literal_checks', 'unit_decisions', 'branch_decisions',
                   'assignments', 'restores', 'conflicts', 'solutions', 'trace_events')
    _fields(limits, limit_names)
    _fields(counts, count_names)
    _need(set(limits) == set(limit_names) and set(counts) == set(count_names), 'exact ordinary counter schemas')
    for key in limits:
        _int(limits[key], 1)
    for key in counts:
        _int(counts[key], 0)
    for ck, lk in (('nodes', 'maximum_nodes'), ('literal_checks', 'maximum_literal_checks'), ('trace_events', 'maximum_trace_events')):
        _need(counts[ck] <= limits[lk], 'ordinary work inside its declared count bound')
    _need(type(trace) is list and len(trace) == counts['trace_events'], 'entire emitted ordinary trace retained')
    _need((unknown and result['budget_stop'] in limit_names) or (not unknown and result['budget_stop'] is None), 'declared budget stop only for UNKNOWN')
    if unknown and result['budget_stop'] != 'maximum_trace_events':
        key = 'nodes' if result['budget_stop'] == 'maximum_nodes' else 'literal_checks'
        _need(counts[key] == limits[result['budget_stop']], 'actually exhausted ordinary work counter')
    observed = {key: 0 for key in count_names}
    def frame(state):
        return {'state': state, 'stage': 'enter', 'outcome': None, 'menu': [], 'index': 0, 'reason': None, 'scan': None}
    stack, found, interrupted, finished, failure = [frame(root)], None, False, False, None
    fields = {'enter': (), 'scan': ('clauses',), 'dead': ('clause_index',),
              'unit': ('clause_index', 'literal'), 'branch': ('variable', 'values'),
              'assign': ('parent_state', 'candidate', 'reason'), 'restore': ('from_assignment',),
              'solution': (), 'finished': ('status',)}
    event_counter = {'enter': 'nodes', 'scan': 'scans', 'dead': 'conflicts', 'unit': 'unit_decisions',
                     'branch': 'branch_decisions', 'assign': 'assignments', 'restore': 'restores', 'solution': 'solutions'}
    for index, event in enumerate(trace):
        _fields(event, ('event_index', 'kind', 'state'))
        _need(_int(event['event_index']) == index and type(event['kind']) is str and event['kind'] in fields, 'sequential ordinary event index/kind')
        kind = event['kind']
        if kind not in ('restore', 'finished'):
            reserved = len(stack) - 1 + int(kind == 'assign')
            _need(index + 1 + reserved + 1 <= limits['maximum_trace_events'], 'normal event leaves every restore and final slot reserved')
        _need(set(event) == set(('event_index', 'kind', 'state') + fields[kind]), 'complete exact ordinary event fields')
        _need(not finished and (not interrupted or kind in ('restore', 'finished')), 'no forward continuation after incomplete unwind')
        state = _assignment(event['state'], n)
        top = stack[-1]
        if kind in event_counter:
            observed[event_counter[kind]] += 1
        if kind == 'assign':
            _need(top['stage'] == 'next' and top['index'] < len(top['menu']), 'next ordinary parent alternative')
            pair = top['menu'][top['index']]
            _need(_same(event['candidate'], pair) and _same(event['parent_state'], top['state'])
                  and event['reason'] == top['reason'], 'original ordered assignment alternative/reason')
            parent = _assignment(top['state'], n)
            _need(pair[0] not in parent, 'assignment adds exactly one unset variable')
            parent[pair[0]] = pair[1]
            child = [[i, b] for i, b in sorted(parent.items())]
            _need(_same(event['state'], child), 'exact complete ordinary child state')
            top['index'] += 1
            top['stage'] = 'child'
            stack.append(frame(child))
            continue
        if kind == 'restore':
            _need(len(stack) > 1 and stack[-2]['stage'] == 'child'
                  and _same(event['from_assignment'], top['state'])
                  and _same(event['state'], stack[-2]['state']), 'exact ordinary parent restore from actual child')
            if top['stage'] != 'done':
                _need(unknown, 'complete ordinary run cannot return an unfinished child')
                if failure is None:
                    failure = {'stage': top['stage'], 'index': index, 'depth': len(stack) - 1}
                outcome, interrupted = 'unknown', True
            else:
                outcome = top['outcome']
            stack.pop()
            parent = stack[-1]
            if outcome is True:
                parent['stage'], parent['outcome'] = 'done', True
            elif outcome is False:
                if parent['index'] < len(parent['menu']):
                    parent['stage'] = 'next'
                else:
                    parent['stage'], parent['outcome'] = 'done', False
            else:
                _need(unknown, 'interrupted return only UNKNOWN')
                parent['stage'], parent['outcome'], interrupted = 'done', 'unknown', True
            continue
        _need(_same(event['state'], top['state']), 'ordinary event belongs to current stack node')
        if kind == 'enter':
            _need(top['stage'] == 'enter', 'one entry per ordinary node')
            top['stage'] = 'scan'
        elif kind == 'scan':
            _need(top['stage'] == 'scan', 'whole scan after node entry')
            rows = _scan(state, clauses)
            _need(_same(event['clauses'], rows), 'all clauses/literals scanned in original order, including satisfied occurrences')
            top['scan'] = rows
            conflicts = [row for row in rows if not row['satisfied'] and not row['unassigned']]
            units = [row for row in rows if not row['satisfied'] and len(row['unassigned']) == 1]
            top['stage'] = 'dead' if conflicts else ('unit' if units else ('solution' if len(state) == n else 'branch'))
        elif kind == 'dead':
            rows = top['scan']
            _need(top['stage'] == 'dead' and _int(event['clause_index']) == next(row['index'] for row in rows if not row['satisfied'] and not row['unassigned']), 'first global conflict before any unit')
            top['stage'], top['outcome'] = 'done', False
        elif kind == 'unit':
            _need(top['stage'] == 'unit', 'unit after whole conflict-free scan')
            row = next(row for row in top['scan'] if not row['satisfied'] and len(row['unassigned']) == 1)
            _need(_int(event['clause_index']) == row['index'] and _same(event['literal'], row['unassigned'][0]), 'first original unit clause/literal')
            top['menu'], top['reason'], top['stage'] = [row['unassigned'][0]], 'unit', 'next'
        elif kind == 'branch':
            _need(top['stage'] == 'branch', 'branch only after global conflict/unit checks')
            variable = min(i for i in range(n) if i not in state)
            _need(_int(event['variable']) == variable and _same(event['values'], [0, 1]), 'smallest unassigned variable; zero before one')
            top['menu'], top['reason'], top['stage'] = [[variable, 0], [variable, 1]], 'branch', 'next'
        elif kind == 'solution':
            _need(top['stage'] == 'solution' and len(state) == n and found is None
                  and all(_truth(state, clause) for clause in signed), 'one complete ordinary satisfying assignment')
            found = event['state']
            top['stage'], top['outcome'] = 'done', True
        elif kind == 'finished':
            _need(index == len(trace) - 1 and len(stack) == 1 and _same(event['state'], root)
                  and event['status'] == status, 'ordinary final event only after full root restoration')
            if unknown and failure is None:
                _need(top['stage'] != 'done', 'no ordinary budget revocation after a completed return')
                failure = {'stage': top['stage'], 'index': index, 'depth': 0}
            if not unknown:
                _need(top['stage'] == 'done' and type(top['outcome']) is bool
                      and top['outcome'] is (status == 'FOUND'), 'complete ordinary traversal outcome')
            finished = True
    _need(finished and len(stack) == 1, 'ordinary reserved final event and exact root unwind, even UNKNOWN')
    observed['trace_events'] = len(trace)
    for key in count_names:
        if key != 'literal_checks':
            _need(counts[key] == observed[key], 'ordinary exact emitted counter: ' + key)
    literal_total = sum(len(clause) for clause in clauses)
    full_scan_checks = literal_total * observed['scans']
    _need(counts['literal_checks'] == full_scan_checks if not unknown else
          full_scan_checks <= counts['literal_checks'] <= full_scan_checks + literal_total,
          'ordinary full scans and at most one interrupted scan, with actual partial literal charges')
    if unknown:
        _need(failure is not None and found is None, 'ordinary UNKNOWN has actual interrupted location, no reserved successful return')
        hidden = counts['literal_checks'] - full_scan_checks
        stop, stage = result['budget_stop'], failure['stage']
        if stop == 'maximum_nodes':
            _need(stage == 'enter' and hidden == 0, 'node cutoff precedes entry and any new scan')
        elif stop == 'maximum_literal_checks':
            _need(stage == 'scan' and hidden < literal_total, 'literal cutoff interrupts an unfinished full scan')
        else:
            extra_reservation = int(stage == 'next')
            _need(stage in ('enter', 'scan', 'dead', 'unit', 'branch', 'solution', 'next')
                  and failure['index'] + 1 + failure['depth'] + extra_reservation + 1 > limits['maximum_trace_events']
                  and hidden == (literal_total if stage == 'scan' else 0),
                  'actual next emission fails its original restore/final reservation, without a shifted cutoff')
    if status == 'FOUND':
        _need(found is not None and _same(result['solution'], found), 'exact first complete ordinary solution wire')
        solution = [bit for _, bit in found]
    else:
        _need(result['solution'] is None, 'no solution accepted under exhaustion or UNKNOWN')
        solution = None
    _outcome(status, solution, _models(n, signed, root))
    return {'schema': 'independent-ordinary-CNF-trace-audit-v1', 'verifier_version': VERSION,
            'status': status, 'valid_saved_trace': True, 'complete': not unknown,
            'unknown_prefix_only': unknown, 'exact_solution_accepted': status == 'FOUND',
            'finite_exhaustion_accepted': status == 'EXHAUSTED_FINITE_CNF',
            'root_restore_checked': True, 'observed_events': len(trace),
            'observed_nodes': observed['nodes'], 'observed_scans': observed['scans'],
            'full_truth_table_checked': True, 'resource_qualified': False,
            'point_engine_conformance': False, 'RL_accepted': False}


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


def verify_experiment(document):
    """Check the complete frozen catalogue, discovered provenance and four arms.

    Extra metadata is allowed, but has no timing/resource authority here. Root
    must obtain every supplied point audit by its separate direct raw-auditor
    call on the corresponding immutable result. Ordinary audits are recomputed.
    """
    _fields(document, ('schema', 'cases'))
    _need(document['schema'] == 'finite-certified-nogood-comparison-v1'
          and type(document['cases']) is list and len(document['cases']) == len(_ORIGINALS), 'complete two-context experiment')
    reports, point_limits, ordinary_limits = [], None, None
    total_unknown = 0
    for case, original in zip(document['cases'], _ORIGINALS):
        _fields(case, ('original', 'queries', 'discovery', 'discovery_audits', 'learned', 'arms',
                       'point_arm_audits', 'ordinary_arm_audits', 'timings', 'original_oracle', 'proposal_log'))
        _need(_same(case['original'], original), 'unchanged original declaration and case order')
        n, clauses = original['variables'], original['clauses']
        _cnf(n, clauses)
        original_models = _models(n, clauses, [])
        _need(bool(original_models), 'original discovery context is not vacuously inconsistent')
        _original_oracle(case['original_oracle'], original, original_models)
        queries = _queries(n)
        _need(_same(case['queries'], queries), 'complete ordered i,j,b,c catalogue and both exact root assumptions')
        _need(type(case['discovery']) is list and type(case['discovery_audits']) is list
              and len(case['discovery']) == len(queries) == len(case['discovery_audits']), 'every discovery solve/audit retained')
        selected, proposals, seen = [], [], set()
        original_keys = {tuple(tuple(lit) for lit in _normalized(clause)) for clause in clauses}
        discovery_counts = {'FOUND': 0, 'EXHAUSTED_FINITE_MARKED_MODEL': 0, 'UNKNOWN': 0}
        for index, (query, result, audit) in enumerate(zip(queries, case['discovery'], case['discovery_audits'])):
            extensions = [bits for bits in original_models if all(bits[i] == b for i, b in query['seeds'])]
            expected_model = _point_model(n, clauses, query['seeds'], list(range(len(clauses))))
            status = _point_result(result, audit, expected_model, n, extensions)
            if point_limits is None:
                point_limits = result['limits']
            _need(_same(result['limits'], point_limits), 'one declared point count policy across discovery/replays')
            discovery_counts[status] += 1
            if status != 'EXHAUSTED_FINITE_MARKED_MODEL':
                continue
            clause = [[i, 1 if bit == 0 else -1] for i, bit in query['seeds']]
            key = tuple(tuple(lit) for lit in clause)
            entailed = all(_truth(bits, clause) for bits in original_models)
            _need(entailed, 'negated entire failed prefix is independently original-F entailed')
            chosen = key not in original_keys and key not in seen and len(selected) < 2
            proposals.append({'discovery_query_index': index, 'clause': clause,
                              'is_original': key in original_keys, 'is_duplicate': key in seen,
                              'entailed': True, 'selected': chosen})
            if chosen:
                selected.append({'clause': clause, 'discovery_query_index': index})
            seen.add(key)
        _need(type(case['learned']) is list and len(case['learned']) == len(selected), 'exact first-two new distinct consequence count')
        for actual, expected in zip(case['learned'], selected):
            _contains(actual, expected)
        _need(type(case['proposal_log']) is list and len(case['proposal_log']) == len(proposals), 'all exhausted proposals retained, including originals/duplicates/unselected')
        for actual, expected in zip(case['proposal_log'], proposals):
            _contains(actual, expected)
        combined = clauses + [entry['clause'] for entry in selected]
        _need(_same(_models(n, combined, []), original_models), 'all original satisfying assignments preserved exactly by learned clauses')
        _need(type(case['arms']) is dict and set(case['arms']) == set(_ARMS), 'all four matched replay arms')
        for key, names in (('point_arm_audits', ('point_no', 'point_learned')),
                           ('ordinary_arm_audits', ('ordinary_no', 'ordinary_learned'))):
            _need(type(case[key]) is dict and set(case[key]) == set(names), 'complete audit arm map')
            for name in names:
                _need(type(case[key][name]) is list and len(case[key][name]) == len(queries), 'one whole audit for every replay query')
        replay_counts = {}
        for arm in _ARMS:
            results = case['arms'][arm]
            _need(type(results) is list and len(results) == len(queries), 'all replay queries retained')
            counts = {'FOUND': 0, 'EXHAUSTED_FINITE_MARKED_MODEL' if arm.startswith('point') else 'EXHAUSTED_FINITE_CNF': 0, 'UNKNOWN': 0}
            for index, (query, result) in enumerate(zip(queries, results)):
                extensions = [bits for bits in original_models if all(bits[i] == b for i, b in query['seeds'])]
                if arm.startswith('point'):
                    active = list(range(len(combined) if arm == 'point_learned' else len(clauses)))
                    expected_model = _point_model(n, combined, query['seeds'], active)
                    status = _point_result(result, case['point_arm_audits'][arm][index], expected_model, n, extensions)
                    _need(_same(result['limits'], point_limits), 'same point budget policy; no recipient-only increase')
                else:
                    used = combined if arm == 'ordinary_learned' else clauses
                    encoded = [[[i, int(sign == 1)] for i, sign in clause] for clause in used]
                    _contains(result, {'variables': n, 'clauses': encoded, 'seed_bits': query['seeds']})
                    independent = verify_ordinary_result(result)
                    _contains(case['ordinary_arm_audits'][arm][index], independent)
                    if ordinary_limits is None:
                        ordinary_limits = result['limits']
                    _need(_same(result['limits'], ordinary_limits), 'one declared ordinary count policy across replay arms')
                    status = result['status']
                    solution = [b for _, b in result['solution']] if status == 'FOUND' else None
                    _outcome(status, solution, extensions)
                counts[status] += 1
            replay_counts[arm] = counts
        case_unknown = discovery_counts['UNKNOWN'] + sum(row['UNKNOWN'] for row in replay_counts.values())
        total_unknown += case_unknown
        reports.append({'case_id': original['id'], 'original_solutions': original_models,
                        'learned': selected, 'all_original_solutions_preserved': True,
                        'discovery_query_count': len(queries), 'discovery_outcomes': discovery_counts,
                        'replay_outcomes': replay_counts, 'unknown_count': case_unknown})
    return {'schema': 'independent-finite-certified-nogood-comparison-audit-v1', 'version': VERSION,
            'valid_saved_experiment': True, 'all_queries_completed': total_unknown == 0,
            'unknown_count': total_unknown, 'discovery_solves_checked': 96, 'replay_solves_checked': 384,
            'original_truth_sets_and_entailment_checked': True, 'ordinary_traces_replayed': True,
            'point_inventory_and_supplied_trace_reports_matched': True,
            'point_trace_auditor_invocation_required_separately': True, 'cases': reports,
            'query_catalogue_reused': True, 'held_out_generalization': False,
            'timing_or_resource_admission': False, 'statistical_speedup': False,
            'full_point_contract_qualified': False, 'RL_accepted': False, 'original_Q_changed': False}
