"""Separate certificate, literal-point and full search replay.

Imports no producer marking, factor-domain, search or logic routines.
"""
import collections
import hashlib
import itertools
import json

import check_movable_regions as A

F, N = A.freeze, A.need


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def certificate(rules, spec, cert):
    rules, spec = F(rules), F(spec)
    parser = A.A.parser(spec['theory'])
    bad = set().union(*(parser.free(a) for a in spec['hypotheses']))
    forms = set(spec['hypotheses']) | {spec['target']}
    for rule in rules:
        forms.add(rule['output'])
        forms.update(rule['inputs'])
    forms = sorted(forms, key=packed)
    ids = {a: i for i, a in enumerate(forms)}
    given = {ids[a] for a in spec['hypotheses']}
    universe = set(range(len(forms))) - given
    eligible = [i for i, rule in enumerate(rules) if not bad.intersection(rule['guards'])]
    context = dict(rules=rules, target=spec['target'], hypotheses=spec['hypotheses'],
                   bound=spec['bound'], forbidden=sorted(bad), transformations='identity', capacity=12)
    N(cert['version'] == 'dependency-budget-certificate-001' and
      cert['context_sha256'] == hashlib.sha256(packed(context)).hexdigest(), 'exact certificate context')
    N(F(cert['formulas']) == F(forms) and cert['given'] == sorted(given) and
      cert['eligible_rules'] == eligible and cert['target'] == ids[spec['target']], 'whole formula and rule domains')
    current = [set() if i in given else universe.copy() for i in range(len(forms))]
    expected = [[sorted(row) for row in current]]
    while True:
        after = []
        for i, formula in enumerate(forms):
            if i in given:
                after.append(set())
                continue
            common = universe.copy()
            for rid in eligible:
                rule = rules[rid]
                if rule['output'] == formula:
                    needed = set()
                    for premise in rule['inputs']:
                        needed.update(current[ids[premise]])
                    common.intersection_update(needed)
            after.append({i} | common)
        if after == current:
            break
        N(all(b <= a for a, b in zip(current, after)), 'descending certificate derivation')
        current = after
        expected.append([sorted(row) for row in current])
    N(cert['rounds'] == expected and cert['required'] == [len(row) for row in current], 'every fixed-point update and final cardinality')
    for rid in eligible:
        rule = rules[rid]
        permitted = {ids[rule['output']]}
        for premise in rule['inputs']:
            permitted.update(current[ids[premise]])
        N(current[ids[rule['output']]] <= permitted, 'local implication for proof-prefix induction')
    return {formula: len(current[i]) for i, formula in enumerate(forms)}


def initial(spec, required):
    values = A.initial(spec)
    if required is not None:
        values.update(((-3000, j), 0) for j in range(spec['bound']+1))
    return values


def tile(rules, spec, key, required):
    out = A.tile(rules, spec, key)
    if required is None:
        return out
    j, rid, refs = F(key)
    bindings = ([(j, rules[rid]['output'])] + list(zip(refs, rules[rid]['inputs']))
                if rid >= 0 else [(j-1, F(spec['target']))] if rid == -1 else [])
    values = dict(out['marks'])
    for i, formula in bindings:
        if i >= 0:
            p, v = (-3000, i), int(required[F(formula)] > i+1)
            N(p not in values or values[p] == v, 'single-valued distant budget marking')
            values[p] = v
    return dict(out, marks=tuple(sorted(values.items())))


def state(rules, spec, chosen, required):
    values = initial(spec, required)
    filled = set()
    for key in F(chosen):
        N(key[0] not in filled, 'one placement per unit cell')
        filled.add(key[0])
        for p, value in tile(rules, spec, key, required)['marks']:
            N(p not in values or values[p] == value, 'literal global marking agreement')
            values[p] = value
    return filled, values


def domains(rules, spec, chosen, required):
    raw = A.domains(rules, spec, chosen)
    if required is None:
        return raw
    # Explicit point assignments, not the producer's integer reference masks.
    filled, values = state(rules, spec, chosen, required)
    def fits(key):
        j, rid, refs = key
        bindings = ([(j, rules[rid]['output'])]+list(zip(refs, rules[rid]['inputs']))
                    if rid >= 0 else [(j-1, F(spec['target']))] if rid == -1 else [])
        assignments = [((-3000, i), int(required[F(formula)] > i+1))
                       for i, formula in bindings if i >= 0]
        return all(values.get(p, value) == value for p, value in assignments)
    return {p: [key for key in keys if fits(key)] for p, keys in raw.items()}


def replay(rules, spec, result, required):
    rules, spec = F(rules), F(spec)
    totals = collections.Counter()
    leaf = None
    def visit(node, chosen):
        nonlocal leaf
        ds = domains(rules, spec, chosen, required)
        kind, p, keys = A.decide(ds)
        totals['nodes'] += 1
        totals['peak_candidates'] = max(totals['peak_candidates'], sum(map(len, ds.values())))
        N((node['kind'], F(node['point'])) == (kind, p), 'global dead/forced/generation decision')
        N(F(node['census']) == tuple((q, len(v), 0) for q, v in sorted(ds.items())), 'all frontier point/candidate counts and root generations')
        if node.get('cutoff') == 'entry_wall':
            N(not node['children'], 'entry cutoff has no executed child')
            return None
        if kind == 'dead':
            totals['dead'] += 1
            return False
        if kind == 'empty':
            leaf = chosen
            return True
        totals[kind] += 1
        # Domain iterator: padding, end, then rule/reference products.
        ordered = sorted(keys, key=lambda key: (0 if key[1] == -2 else 1 if key[1] == -1 else 2, key[1], key[2]))
        answer = False
        for i, child in enumerate(node['children']):
            N(answer is False and F(child['key']) == ordered[i], 'literal complete base alternative order')
            totals['attempts'] += 1
            answer = visit(child['tree'], chosen+(F(child['key']),))
            if answer is False:
                totals['backtracks'] += 1
        if node.get('cutoff') == 'before_placement':
            N(answer is False and len(node['children']) < len(ordered), 'cutoff retains a pending legal alternative')
            return None
        N(answer is not False or len(node['children']) == len(ordered), 'all alternatives before finite exhaustion')
        return answer
    outcome = visit(result['search_tree'], ())
    N(result['status'] == ('finite_exact_proof_region' if outcome else
                          'unknown_search_budget' if outcome is None else 'exhausted_finite_region'), 'tri-state outcome')
    for name, value in totals.items():
        N(result['metrics'].get(name, 0) == value, 'exact tree counter '+name)
    N(all(g == 1 for g in result['tile_generations']), 'placements are one beyond root generation')
    if outcome:
        N(leaf == F(result['placements']), 'actual discovered positive leaf')
        stripped = [dict(t, marks=[(p, v) for p, v in t['marks'] if p[0] != -3000]) for t in result['tiles']]
        A.certificate(rules, spec, result, stripped)
        N(F(result['tiles']) == tuple(tile(rules, spec, k, required) for k in leaf), 'complete decorated tile values')
        filled, values = state(rules, spec, leaf, required)
        N(filled == set(range(spec['bound']+1)), 'complete original point capacities')
    return dict(status='passed', nodes=totals['nodes'], outcome=outcome)
