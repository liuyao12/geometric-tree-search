"""UNEXECUTED independent finite Boolean oracle; no point-engine imports.

Literal wire [variable_index, sign], sign=+1 or -1; bits are integer 0/1.
All assignments are evaluated directly. No point coordinates, t/m legality,
candidate inventory, proof word, search heuristic or expected answer is input.
Unit closure below is a clause-level oracle, not a procedural filter permitted
inside the point engine. Its marked mode assumes guards ACTUALLY placed.
"""
from itertools import product

VERSION = 'independent-Boolean-CNF-truth-table-oracle-Source-v1'
MAXIMUM_VARIABLES = 4


def require(condition, message):
    if condition is not True:
        raise ValueError(message)


def bit(value):
    require(type(value) is int and value in (0, 1), 'strict integer bit; zero is assigned')
    return value


def declaration(case):
    require(type(case) is dict and set(case) == {'id', 'variables', 'clauses', 'prefixes'}, 'whole case declaration')
    require(type(case['id']) is str and 0 < len(case['id']) <= 80, 'literal case identity')
    n = case['variables']
    require(type(n) is int and 0 <= n <= MAXIMUM_VARIABLES, 'finite declared n <= 4; no Boolean count')
    require(type(case['clauses']) is list and len(case['clauses']) <= 8, 'complete bounded clause occurrences')
    clauses = []
    for clause in case['clauses']:
        require(type(clause) is list and len(clause) <= n, 'whole clause; empty clause allowed')
        row, seen = [], set()
        for literal in clause:
            require(type(literal) is list and len(literal) == 2, 'exact literal wire')
            variable, sign = literal
            require(type(variable) is int and 0 <= variable < n and variable not in seen, 'distinct variable ports within clause')
            require(type(sign) is int and sign in (-1, 1), 'exact signed literal, no Boolean sign')
            seen.add(variable)
            row.append((variable, sign))
        clauses.append(tuple(row))
    require(type(case['prefixes']) is list and len(case['prefixes']) <= 32, 'whole bounded requested prefixes')
    prefixes = []
    for prefix in case['prefixes']:
        require(type(prefix) is list, 'explicit partial assignment; absence is omitted pair')
        values = {}
        for entry in prefix:
            require(type(entry) is list and len(entry) == 2, 'exact assigned variable/bit pair')
            variable, value = entry
            require(type(variable) is int and 0 <= variable < n and variable not in values, 'unique partial assignment index')
            values[variable] = bit(value)
        prefixes.append(tuple(sorted(values.items())))
    return n, tuple(clauses), tuple(prefixes)


def clause_true(clause, assignment):
    return any(assignment[variable] == (1 if sign == 1 else 0) for variable, sign in clause)


def unit_closure(n, clauses, prefix):
    """Whole clause scan for conflict precedes any next unit consequence.

    This does not compute every semantic consequence. An empty satisfying set
    may remain unresolved by unit propagation. No vacuous forced-bit claim.
    """
    values = dict(prefix)
    trail = []
    for _ in range(n + 1):
        units = []
        for index, clause in enumerate(clauses):
            if any(variable in values and values[variable] == (1 if sign == 1 else 0)
                   for variable, sign in clause):
                continue
            missing = [(variable, sign) for variable, sign in clause if variable not in values]
            if not missing:
                return {'conflict': True, 'conflict_clause': index,
                        'assignment': [list(x) for x in sorted(values.items())], 'derived': trail}
            if len(missing) == 1:
                variable, sign = missing[0]
                units.append((index, variable, 1 if sign == 1 else 0))
        if not units:
            return {'conflict': False, 'conflict_clause': None,
                    'assignment': [list(x) for x in sorted(values.items())], 'derived': trail}
        index, variable, value = units[0]
        values[variable] = value
        trail.append({'clause_occurrence': index, 'variable': variable, 'bit': value})
    raise ValueError('finite unit closure bound violated')


def evaluate_case(case):
    n, clauses, requested = declaration(case)
    assignments = tuple(tuple(bits) for bits in product((0, 1), repeat=n))
    clause_values = tuple(tuple(clause_true(clause, bits) for clause in clauses) for bits in assignments)
    satisfying = tuple(bits for bits, truths in zip(assignments, clause_values) if all(truths))
    # Prefix probes are generated from DECLARATIONS, not from a point engine or
    # a supplied successful route. Keep every clause occurrence as provenance.
    probes = {(): [{'kind': 'root'}]}
    for index, prefix in enumerate(requested):
        probes.setdefault(prefix, []).append({'kind': 'declared_prefix', 'index': index})
    for index, clause in enumerate(clauses):
        forbidden = tuple((variable, 0 if sign == 1 else 1) for variable, sign in clause)
        for omitted, (variable, _) in enumerate(clause):
            prefix = tuple(sorted(pair for j, pair in enumerate(forbidden) if j != omitted))
            probes.setdefault(prefix, []).append({'kind': 'all_but_one_forbidden',
                'clause_occurrence': index, 'remaining_variable': variable})
    modes = []
    for marked in (False, True):
        accepted = satisfying if marked else assignments
        rows = []
        for prefix, origins in sorted(probes.items()):
            extensions = tuple(bits for bits in accepted if all(bits[i] == value for i, value in prefix))
            fixed = dict(prefix)
            forced = []
            if extensions:
                for variable in range(n):
                    values = {bits[variable] for bits in extensions}
                    if variable not in fixed and len(values) == 1:
                        forced.append([variable, next(iter(values))])
            unit = unit_closure(n, clauses if marked else (), prefix)
            # Independent complete truth-table consistency of derived unit data.
            require(not unit['conflict'] or not extensions, 'unit conflict must have no satisfying extension')
            require(all(all(bits[item['variable']] == item['bit'] for bits in extensions)
                        for item in unit['derived']), 'every actual unit consequence is truth-table sound')
            rows.append({'prefix': [list(x) for x in prefix], 'origins': origins,
                'satisfying_extensions': [list(bits) for bits in extensions],
                'extension_count': len(extensions), 'contradiction': not bool(extensions),
                'semantic_forced_unassigned_bits': forced, 'unit_closure': unit})
        modes.append({'mode': 'marked_guards_actually_placed' if marked else 'guards_unmarked',
            'accepted_assignments': [list(bits) for bits in accepted], 'assignment_count': len(accepted),
            'prefix_probes': rows})
    return {'schema': 'independent-Boolean-CNF-oracle-result-v1', 'version': VERSION,
        'case_id': case['id'], 'variables': n,
        'ordered_clause_occurrences': [[[i, sign] for i, sign in clause] for clause in clauses],
        'all_assignments': [list(bits) for bits in assignments],
        'clause_truth_rows': [list(values) for values in clause_values], 'modes': modes,
        'assignment_order': 'lexicographic bit vector; component i is variable i',
        'semantic_forcing_is_not_unit_forcing': True,
        'point_engine_conformance_accepted': False, 'learned_clause_soundness_accepted': False,
        'original_Q_changed': False, 'ROOT_resource_accepted': False, 'RL_accepted': False}


def evaluate_declarations(document):
    require(type(document) is dict and set(document) == {'schema', 'cases'}, 'whole finite case inventory')
    require(document['schema'] == 'independent-Boolean-CNF-oracle-cases-v1'
            and type(document['cases']) is list and 0 < len(document['cases']) <= 16, 'exact finite declaration schema')
    require(all(type(case) is dict and type(case.get('id')) is str for case in document['cases']), 'literal case identities before intake')
    names = [case['id'] for case in document['cases']]
    require(all(type(name) is str for name in names) and len(set(names)) == len(names), 'distinct complete case identities')
    return {'schema': 'independent-Boolean-CNF-oracle-inventory-result-v1', 'version': VERSION,
        'case_count': len(names), 'results': [evaluate_case(case) for case in document['cases']],
        'scope': 'direct finite propositional truth and unit consequences only; no point-engine or ownership admission',
        'point_engine_conformance_accepted': False, 'original_Q_changed': False,
        'ROOT_resource_accepted': False, 'RL_accepted': False}
