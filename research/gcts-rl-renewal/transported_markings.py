"""Transport certified positional failures through a closing-flow boundary.

This module constructs proposals, not a validity oracle. A separate checker
validates every transport before the unchanged point-value search consumes it.
Only signature bijections (variables unchanged) and enlarged bounds are used.
"""
import copy
import hashlib

import movable_proof_regions as M
import quantified_receptors as Q
from serialized_kernel import canonical


def rename(a, mapping):
    a = M.freeze(a)
    tag = a[0]
    if tag == 'var' or tag == 'bot':
        return a
    if tag in ('fun', 'pred'):
        kind = 'functions' if tag == 'fun' else 'predicates'
        return (tag, mapping[kind][a[1]], tuple(rename(t, mapping) for t in a[2]))
    if tag == 'all':
        return ('all', a[1], rename(a[2], mapping))
    return (tag,)+tuple(rename(v, mapping) for v in a[1:])


def rule(r, mapping):
    parameters = copy.deepcopy(r['parameters'])
    for key in ('universal', 'term'):
        if key in parameters:
            parameters[key] = rename(parameters[key], mapping)
    if r['kind'] == 'family':
        raise ValueError('transport study uses primitive donor inventories')
    return dict(r, inputs=tuple(rename(a, mapping) for a in r['inputs']),
                output=rename(r['output'], mapping), parameters=parameters)


def vocabulary(spec, changed):
    names = {'P': 'Supports', 'Q': 'Follows', 'S': 'Ambient',
             'Inc': 'Related', 'Point': 'Item', 'Line': 'Carrier',
             'zero': 'origin', 'add': 'join', 'succ': 'step'}
    return {kind: {name: names[name] if changed else name for name in spec['theory'][kind]}
            for kind in ('functions', 'predicates')}


def recipient(source, changed, extra):
    spec = copy.deepcopy(source['spec'])
    mapping = vocabulary(spec, changed)
    theory = spec['theory']
    for kind in ('functions', 'predicates'):
        theory[kind] = {mapping[kind][name]: arity for name, arity in theory[kind].items()}
    theory['axioms'] = {name: rename(a, mapping) for name, a in theory['axioms'].items()}
    for key in ('hypotheses', 'terms'):
        spec[key] = tuple(rename(a, mapping) for a in spec[key])
    spec['target'] = rename(spec['target'], mapping)
    spec['bound'] += extra
    spec['id'] += '-'+('renamed' if changed else 'extended')
    spec['title'] += ' · '+('renamed vocabulary' if changed else 'larger region')
    return spec, mapping


def propose(source, spec, catalog, mapping):
    index = {canonical(r): i for i, r in enumerate(catalog['rules'])}
    forward = [index[canonical(rule(r, mapping))] for r in source['catalog']['rules']]
    certificates = []
    for i, cert in enumerate(source['certified']):
        pair = [(j, forward[rid] if rid >= 0 else rid, tuple(refs))
                for j, rid, refs in cert['pair']]
        closing = [j if rid == M.END else j-1 for j, rid, refs in pair if rid < 0]
        certificates.append(dict(source_index=i, pair=pair,
                                 maximum_endpoint=min(closing) if closing else None))
    model = M.Model(catalog, spec['target'], spec['bound'], spec['hypotheses'])
    return dict(source_id=source['spec']['id'], source_context=source['context_hash'],
                target_context=model.context_hash(), mapping=mapping,
                rule_map=forward, certificates=certificates,
                theorem='closing-prefix-restriction-v1',
                scope='Symbol bijection, unchanged variables and grammar, bound enlarged. '
                      'Each seed pair fixes an end no later than the donor bound. '
                      'Any recipient completion would crop and inverse-rename to a donor completion.')


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def inventory(spec):
    spec = M.freeze(spec)
    return Q.inventory(spec['theory'], spec['hypotheses'], spec['terms'], spec['variables'],
                       spec['rounds'], generalization_rounds=spec['generalization_rounds'])
