"""Source-only independent literal receptor matcher; no engine imports.

This is an independently proposed bounded feature contract, not an accepted
copy of the eventual producer score. No call to this module has been executed.
Unsupported grammar receives neutral advice; no verdict is logical acceptance.
"""

class Unsupported(Exception):
    pass


def exact_list(value, length=None):
    if type(value) is not list or not value or (length is not None and len(value) != length):
        raise Unsupported('unsupported or malformed AST shape')


def symbol(value):
    if type(value) is not str or not value:
        raise Unsupported('nonliteral symbol')
    return value


def term_tokens(value, variables):
    exact_list(value)
    if value[0] == 'var':
        exact_list(value, 2)
        name = symbol(value[1])
        if name not in variables:
            raise Unsupported('free term outside peeled binder prefix')
        return [('slot', name)]
    if value[0] == 'fun':
        exact_list(value, 3)
        name = symbol(value[1])
        if type(value[2]) is not list or value[2]:
            raise Unsupported('first gate supports only closed zero-arity terms')
        return [('constant', name)]
    raise Unsupported('unknown term constructor')


def formula_tokens(value, variables):
    exact_list(value)
    tag = value[0]
    if tag == 'pred':
        exact_list(value, 3)
        name = symbol(value[1])
        if type(value[2]) is not list:
            raise Unsupported('predicate argument list')
        result = [('predicate', name, len(value[2]))]
        for term in value[2]:
            result.extend(term_tokens(term, variables))
        return result
    if tag == 'eq':
        exact_list(value, 3)
        return [('equality',)] + term_tokens(value[1], variables) + term_tokens(value[2], variables)
    if tag == 'not':
        exact_list(value, 2)
        return [('negation',)] + formula_tokens(value[1], variables)
    if tag in ('and', 'imp'):
        exact_list(value, 3)
        return [(tag,)] + formula_tokens(value[1], variables) + formula_tokens(value[2], variables)
    if tag == 'bot':
        exact_list(value, 1)
        return [('contradiction',)]
    # In particular, do not strip a nested quantifier or reinterpret its scope.
    raise Unsupported('quantified or unknown receptor formula')


def receptor_pattern(formula):
    """Peel only leading all-binders, then the immediate implication guard."""
    try:
        variables = []
        while type(formula) is list and formula and formula[0] == 'all':
            exact_list(formula, 3)
            name = symbol(formula[1])
            if name in variables:
                raise Unsupported('shadowed or repeated prefix binder is neutral in this gate')
            variables.append(name)
            formula = formula[2]
        exact_list(formula, 3)
        if formula[0] != 'imp':
            raise Unsupported('no immediate implication receptor')
        tokens = formula_tokens(formula[1], frozenset(variables))
        return {'status': 'supported', 'binders': variables, 'tokens': tokens}
    except (Unsupported, RecursionError) as exc:
        return {'status': 'neutral', 'reason': str(exc)}


def match_one(pattern, recipient):
    """Literal ordered matching; repeated slots retain one exact constant."""
    if pattern['status'] != 'supported':
        return {'status': 'neutral', 'reason': 'unsupported pattern'}
    try:
        actual = formula_tokens(recipient, frozenset())
    except (Unsupported, RecursionError) as exc:
        return {'status': 'neutral', 'reason': str(exc)}
    wanted = pattern['tokens']
    if len(wanted) != len(actual):
        return {'status': 'miss', 'bindings': {}}
    assigned = {}
    for p, r in zip(wanted, actual):
        if p[0] == 'slot':
            if r[0] != 'constant':
                return {'status': 'miss', 'bindings': {}}
            if p[1] in assigned and assigned[p[1]] != r[1]:
                return {'status': 'miss', 'bindings': {}}
            assigned[p[1]] = r[1]
        elif p != r:
            return {'status': 'miss', 'bindings': {}}
    return {'status': 'match', 'bindings': {k: ['fun', v, []] for k, v in assigned.items()}}


def receptor_feature(formula, selected_formulas):
    """Caller must independently bind selected_formulas to occupied placements."""
    pattern = receptor_pattern(formula)
    if pattern['status'] != 'supported':
        return {'status': 'neutral', 'eligible_recipients': 0, 'matches': []}
    supported, matches = 0, []
    for occurrence, formula in enumerate(selected_formulas):
        answer = match_one(pattern, formula)
        if answer['status'] != 'neutral':
            supported += 1
        if answer['status'] == 'match':
            # Retain every ordered occurrence. Do not merge equal premise rows.
            matches.append({'selected_occurrence': occurrence, 'bindings': answer['bindings']})
    status = 'match' if matches else ('miss' if supported else 'neutral')
    return {'status': status, 'eligible_recipients': supported, 'matches': matches}


def complete_permutation(keys, score_records, match_priority):
    """Pure ordering check; callers supply independently reconstructed records.

    Readiness remains the first field. Exact match_priority and relevant recipe
    extraction await the producer's frozen feature contract. Forced/dead/global
    point selection is outside this helper and must remain unchanged.
    """
    if len(keys) != len(set(keys)) or set(keys) != set(score_records):
        raise ValueError('records must cover every distinct complete domain key')
    if set(match_priority) != {'match', 'neutral', 'miss'}:
        raise ValueError('three advice categories must have declared priorities')
    def score(key):
        record = score_records[key]
        return (record['readiness'], match_priority[record['receptor_status']],
                record['ast_size'], record['canonical_witness'], key[0], key[2])
    ordered = sorted(keys, key=score)
    if len(ordered) != len(keys) or set(ordered) != set(keys):
        raise ValueError('advice must preserve complete fallback')
    return ordered
