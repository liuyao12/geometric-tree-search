"""Independent source-only receptor advice; no producer or engine imports.

Version 1 remains immutable. Version 2 distinguishes rigid compound syntax
from unsupported compound variable-slot images and uses the announced MP
ordered-antecedent extraction. No code here has been scientifically executed.
"""
import copy


class Unsupported(Exception):
    pass


def shape(node, length=None):
    if type(node) is not list or not node or (length is not None and len(node) != length):
        raise Unsupported('malformed literal AST')


def name(value):
    if type(value) is not str or not value:
        raise Unsupported('nonliteral symbol')
    return value


def term(node, slots):
    shape(node)
    if node[0] == 'var':
        shape(node, 2)
        if name(node[1]) not in slots:
            raise Unsupported('free variable outside the peeled prefix')
        return
    shape(node, 3)
    if node[0] != 'fun' or type(node[2]) is not list:
        raise Unsupported('unknown term constructor')
    name(node[1])
    for argument in node[2]:
        term(argument, slots)


def formula(node, slots):
    shape(node)
    tag = node[0]
    if tag == 'pred':
        shape(node, 3)
        name(node[1])
        if type(node[2]) is not list:
            raise Unsupported('predicate argument list')
        for argument in node[2]:
            term(argument, slots)
    elif tag == 'eq':
        shape(node, 3)
        term(node[1], slots)
        term(node[2], slots)
    elif tag == 'not':
        shape(node, 2)
        formula(node[1], slots)
    elif tag in ('and', 'imp'):
        shape(node, 3)
        formula(node[1], slots)
        formula(node[2], slots)
    elif tag == 'bot':
        shape(node, 1)
    else:
        raise Unsupported('nested quantified or unsupported receptor')


def extract_receptor(witness, ordered_premises=()):
    """Recipe syntax only; prior independent logical validation is separate."""
    try:
        if type(witness) is not dict:
            raise Unsupported('witness dictionary required')
        rule = witness.get('rule')
        slots = []
        if rule == 'instantiate':
            asserted = witness['formula']
            shape(asserted, 3)
            if asserted[0] != 'imp':
                raise Unsupported('no instantiation implication')
            residual = asserted[2]
            while type(residual) is list and residual and residual[0] == 'all':
                shape(residual, 3)
                variable = name(residual[1])
                if variable in slots:
                    raise Unsupported('shadowed or repeated leading binder')
                slots.append(variable)
                residual = residual[2]
            shape(residual, 3)
            if residual[0] != 'imp':
                raise Unsupported('no immediate consequent guard')
            guard = residual[1]
        elif rule == 'mp':
            if type(ordered_premises) not in (tuple, list) or len(ordered_premises) != 2:
                raise Unsupported('ordered MP interface required')
            guard = ordered_premises[0]
            if ordered_premises[1] != ['imp', guard, witness['formula']]:
                raise Unsupported('ordered MP formula interface differs')
        else:
            raise Unsupported('rule has no receptor feature')
        formula(guard, frozenset(slots))
        return {'status': 'supported', 'slots': slots, 'guard': copy.deepcopy(guard)}
    except (Unsupported, RecursionError, KeyError) as exc:
        return {'status': 'neutral', 'reason': str(exc)}


def compare_term(pattern, recipient, assigned):
    if pattern[0] == 'var':
        # Recipient syntax was validated first. Its literal compound constructor
        # may be supported elsewhere, but cannot be this gate's slot image.
        if recipient[0] != 'fun' or recipient[2]:
            return False, True
        variable = pattern[1]
        if variable in assigned:
            return assigned[variable] != recipient, False
        assigned[variable] = copy.deepcopy(recipient)
        return False, False
    if pattern[0] != recipient[0] or pattern[1] != recipient[1] or len(pattern[2]) != len(recipient[2]):
        return True, False
    # Scan all aligned siblings. Definite structural mismatch takes precedence
    # over an unsupported slot image elsewhere; otherwise that image is neutral.
    answers = [compare_term(a, b, assigned) for a, b in zip(pattern[2], recipient[2])]
    return any(a[0] for a in answers), any(a[1] for a in answers)


def compare_formula(pattern, recipient, assigned):
    if pattern[0] != recipient[0]:
        return True, False
    tag = pattern[0]
    if tag == 'pred':
        if pattern[1] != recipient[1] or len(pattern[2]) != len(recipient[2]):
            return True, False
        answers = [compare_term(a, b, assigned) for a, b in zip(pattern[2], recipient[2])]
        return any(a[0] for a in answers), any(a[1] for a in answers)
    if tag == 'eq':
        answers = [compare_term(pattern[i], recipient[i], assigned) for i in (1, 2)]
        return any(a[0] for a in answers), any(a[1] for a in answers)
    if tag == 'not':
        return compare_formula(pattern[1], recipient[1], assigned)
    if tag in ('and', 'imp'):
        answers = [compare_formula(pattern[i], recipient[i], assigned) for i in (1, 2)]
        return any(a[0] for a in answers), any(a[1] for a in answers)
    if tag == 'bot':
        return False, False
    raise Unsupported('unsupported formula comparison')


def literal_match(pattern, recipient):
    if pattern.get('status') != 'supported':
        return {'status': 'neutral', 'bindings': {}}
    try:
        formula(pattern['guard'], frozenset(pattern['slots']))
        formula(recipient, frozenset())
        assigned = {}
        mismatch, unsupported = compare_formula(pattern['guard'], recipient, assigned)
        status = 'nonmatch' if mismatch else ('neutral' if unsupported else 'match')
        return {'status': status, 'bindings': assigned if status == 'match' else {}}
    except (Unsupported, RecursionError, KeyError) as exc:
        return {'status': 'neutral', 'bindings': {}, 'reason': str(exc)}


def evaluate_selected(pattern, selected_formulas):
    supported, matches = 0, []
    if pattern.get('status') != 'supported':
        return {'status': 'neutral', 'matches': [], 'eligible_recipients': 0}
    for occurrence, output in enumerate(selected_formulas):
        answer = literal_match(pattern, output)
        if answer['status'] != 'neutral':
            supported += 1
        if answer['status'] == 'match':
            matches.append({'selected_occurrence': occurrence, 'bindings': answer['bindings']})
    return {'status': 'match' if matches else ('nonmatch' if supported else 'neutral'),
            'matches': matches, 'eligible_recipients': supported}


def complete_permutation(keys, records):
    if len(keys) != len(set(keys)) or set(keys) != set(records):
        raise ValueError('exact complete domain records required')
    priority = {'match': 0, 'neutral': 1, 'nonmatch': 2}
    def score(key):
        item = records[key]
        return (item['readiness'], priority[item['receptor_status']],
                item['ast_size'], item['canonical_witness'], key[0], key[2])
    answer = sorted(keys, key=score)
    if len(answer) != len(keys) or set(answer) != set(keys):
        raise ValueError('complete fallback permutation required')
    return answer
