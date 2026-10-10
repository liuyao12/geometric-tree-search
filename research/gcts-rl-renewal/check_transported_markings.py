"""Independent transport checker; no producer/model/search imports.

The proof obligation is a solution map, not an assertion that two hashes match.
Complete target tilings containing a mapped pair crop to the old closed prefix
and invert a checked signature bijection, contradicting the donor exhaustion.
"""
import hashlib

import check_movable_regions as A

need, freeze, packed = A.need, A.freeze, A.A.packed


def translate(node, functions, predicates):
    node = freeze(node)
    if node[0] in ('var', 'bot'):
        return node
    if node[0] == 'fun':
        return ('fun', functions[node[1]], tuple(translate(t, functions, predicates) for t in node[2]))
    if node[0] == 'pred':
        return ('pred', predicates[node[1]], tuple(translate(t, functions, predicates) for t in node[2]))
    if node[0] == 'all':
        return ('all', node[1], translate(node[2], functions, predicates))
    need(node[0] in ('eq', 'imp', 'and', 'or', 'not'), 'supported syntax')
    return (node[0],)+tuple(translate(t, functions, predicates) for t in node[1:])


def verify(source, spec, catalog, proposal, donor_checks):
    old, new, cert = freeze(source['spec']), freeze(spec), freeze(proposal)
    need(cert['theorem'] == 'closing-prefix-restriction-v1', 'transfer theorem version')
    need(cert['source_id'] == old['id'] and cert['source_context'] == A.context_hash(source['catalog'], old), 'exact donor context')
    need(cert['target_context'] == A.context_hash(catalog, new), 'exact recipient context')
    need(type(new['bound']) is int and new['bound'] >= old['bound'], 'enlarged boundary')
    need(source['family'] is None and not source['bindings'], 'primitive donor')
    mapping = cert['mapping']
    need(set(mapping) == {'functions', 'predicates'}, 'signature map domains')
    for kind in mapping:
        before, after = old['theory'][kind], new['theory'][kind]
        need(set(mapping[kind]) == set(before) and len(set(mapping[kind].values())) == len(before), 'symbol bijection')
        need({mapping[kind][n]: arity for n, arity in before.items()} == after, 'exact arity-preserving signature')
    tr = lambda a: translate(a, mapping['functions'], mapping['predicates'])
    for key in ('variables', 'rounds', 'generalization_rounds'):
        need(old[key] == new[key], 'unchanged '+key)
    need(new['theory']['schemas'] == old['theory']['schemas'] == (), 'no induction-schema transport')
    need(new['theory']['axioms'] == {n: tr(a) for n, a in old['theory']['axioms'].items()}, 'mapped axioms')
    need(new['hypotheses'] == tuple(tr(a) for a in old['hypotheses']), 'mapped open hypotheses')
    need(new['terms'] == tuple(tr(a) for a in old['terms']) and new['target'] == tr(old['target']), 'mapped terms and target')
    old_rules, old_forms = A.A.inventory(old)
    rules, forms = A.A.inventory(new)
    for cat, declared in ((source['catalog'], old), (catalog, new)):
        for key in ('variables', 'terms', 'rounds', 'generalization_rounds'):
            need(freeze(cat[key]) == declared[key], 'whole grammar metadata '+key)
    need(freeze(source['catalog']['rules']) == freeze(old_rules) and freeze(source['catalog']['formulas']) == freeze(old_forms), 'complete donor grammar')
    need(freeze(catalog['rules']) == freeze(rules) and freeze(catalog['formulas']) == freeze(forms), 'complete recipient grammar')
    need(set(forms) == {tr(a) for a in old_forms}, 'formula-port bijection')
    forward = cert['rule_map']
    need(all(type(i) is int for i in forward) and len(forward) == len(old_rules) == len(rules)
         and sorted(forward) == list(range(len(rules))), 'complete rule permutation')
    for i, r in enumerate(old_rules):
        parameters = dict(r['parameters'])
        for key in ('universal', 'term'):
            if key in parameters:
                parameters[key] = tr(parameters[key])
        expected = dict(r, inputs=tuple(tr(a) for a in r['inputs']), output=tr(r['output']), parameters=parameters)
        need(freeze(rules[forward[i]]) == freeze(expected), 'rule meanings, guards and parameter map')
    need(len(cert['certificates']) == len(source['certified']) == len(donor_checks), 'all resolved donor samples')
    pairs = []
    for i, (item, donor, checked) in enumerate(zip(cert['certificates'], source['certified'], donor_checks)):
        need(checked['status'] == 'accepted_complete_tree' and checked['outcome'] is False, 'independently exhausted donor')
        # Checks passed by a caller must be bound to this exact pair/tree/context.
        need(checked['certificate_sha256'] == hashlib.sha256(packed(dict(context=cert['source_context'], pair=donor['pair'], tree=donor['tree']))).hexdigest(), 'donor certificate identity')
        pair = tuple((j, forward[rid] if rid >= 0 else rid, refs) for j, rid, refs in freeze(donor['pair']))
        need(item['source_index'] == i and item['pair'] == pair and len(pair) == 2 and pair[0] != pair[1], 'exact transported pair')
        ends = [j if rid == A.END else j-1 for j, rid, _ in pair if rid in (A.END, A.PAD)]
        need(ends and 0 <= min(ends) <= old['bound'], 'closing seed bounds every possible proof end')
        need(item['maximum_endpoint'] == min(ends), 'derived end bound')
        # Legal seeds and their actual flow values are checked in each context.
        A.state(old_rules, old, donor['pair'])
        A.state(rules, new, pair)
        pairs.append(pair)
    return dict(status='accepted_solution_map', pairs=pairs,
                source_bound=old['bound'], target_bound=new['bound'],
                changed_rule_ids=sum(i != j for i, j in enumerate(forward)),
                theorem='Any completion containing a pair closes within the donor region; '
                        'crop padding and inverse-rename complete formula ports and rules.')


def certify_donor(source):
    spec = freeze(source['spec'])
    rules, forms = A.A.inventory(spec)
    need(freeze(source['catalog']['rules']) == freeze(rules) and freeze(source['catalog']['formulas']) == freeze(forms), 'donor inventory')
    context = A.context_hash(source['catalog'], spec)
    checks = []
    for cert in source['certified']:
        result = A.tree(rules, spec, seeds=cert['pair'], node=cert['tree'])
        need(result['outcome'] is False, 'failed donor pair')
        result['certificate_sha256'] = hashlib.sha256(packed(dict(context=context, pair=cert['pair'], tree=cert['tree']))).hexdigest()
        checks.append(result)
    return checks


def crop(source, spec, catalog, proposal, result):
    """Counterfactual construction, executed on valid positive prefix witnesses.

    For a negative pair there is no completion to pass here. Tests use valid
    closing seeds to exercise the same capacity/marking-preserving map.
    """
    old = freeze(source['spec'])
    keys = freeze(result['placements'])
    need(result['endpoint'] <= old['bound'], 'prefix closes inside donor')
    inverse = {rid: j for j, rid in enumerate(proposal['rule_map'])}
    out = tuple((j, inverse[rid] if rid >= 0 else rid, refs) for j, rid, refs in keys if j <= old['bound'])
    A.state(source['catalog']['rules'], old, out)
    need({k[0] for k in out} == set(range(old['bound']+1)), 'cropped exact coverage')
    need(any(k[0] == result['endpoint'] and k[1] == A.END for k in out), 'cropped end')
    return out
