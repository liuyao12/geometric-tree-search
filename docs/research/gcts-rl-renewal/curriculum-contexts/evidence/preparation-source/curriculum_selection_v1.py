"""Frozen literal curriculum selection only; SOURCE ONLY until ROOT review.

No engine, compiler, model, checker, policy, RNG or proof-word input. Future
callers must verify the exact document pins before passing decoded documents.
The binding document is itself frozen; this is not a security API accepting
arbitrary caller-created bindings.
"""
import copy
import hashlib
import json

VERSION = 'frozen-five-context-selection-v1'
DONOR_IDS = ('donor-two-guards', 'donor-two-equalities',
             'donor-repeated-guard', 'donor-repeated-equality')
HELDOUT_ID = 'heldout-mixed-guard-equality'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def resolve_literal(record, reference):
    if type(record) is not dict:
        raise ValueError('literal curriculum field record required')
    if set(record) == {'literal_ast'}:
        return copy.deepcopy(record['literal_ast'])
    if set(record) != {'metadata_reference'}:
        raise ValueError('only exact literal/reference fields are supported')
    path = record['metadata_reference']
    if type(path) is not list or not path:
        raise ValueError('nonempty literal metadata path required')
    value = reference
    for token in path:
        if type(token) is int:
            if type(value) is not list or not 0 <= token < len(value):
                raise ValueError('exact nonnegative metadata occurrence index')
        elif type(token) is str:
            if type(value) is not dict or token not in value:
                raise ValueError('exact metadata field name')
        else:
            raise ValueError('Boolean/path coercions are unsupported')
        value = value[token]
    return copy.deepcopy(value)


def select_context(reference, split, protocol, frozen_binding, selector):
    """Return one exact frozen context, not an arbitrary Gamma or target.

    Semantic context equality deliberately omits selector/provenance. Repeated
    hypothesis occurrences remain in order. Context holdout does not imply
    unseen primitive witnesses, formulas, constants or conditional lemmas.
    """
    documents = {'reference': reference, 'split': split, 'protocol': protocol}
    if frozen_binding.get('schema') != VERSION:
        raise ValueError('exact frozen curriculum binding schema required')
    for role, document in documents.items():
        if digest(document) != frozen_binding['documents'][role]['canonical_sha256']:
            raise ValueError('frozen curriculum document changed: ' + role)
    if (split.get('schema') != 'small-whole-family-context-split-v1'
            or split.get('execution_authorized') is not False
            or protocol.get('schema') != 'small-source-family-RL-protocol-v1'
            or protocol.get('execution_authorized') is not False):
        raise ValueError('exact unexecuted frozen split/protocol required')
    donors = split['donors']
    if (type(donors) is not list or tuple(d['id'] for d in donors) != DONOR_IDS
            or split['held_out']['id'] != HELDOUT_ID):
        raise ValueError('all four original donors and one original heldout only')
    boundary = split['common_boundary']
    if (type(boundary['rows']) is not int or boundary['rows'] != 24
            or boundary['seed_rows'] != [0, 1, 2]
            or any(type(r) is not int for r in boundary['seed_rows'])
            or type(boundary['target_row']) is not int or boundary['target_row'] != 23):
        raise ValueError('unchanged exact 24-row boundary required')
    if (type(protocol['features']['count']) is not int
            or protocol['features']['count'] != 31
            or len(protocol['curriculum']['training_episodes']) != 8
            or len(protocol['evaluation']['schedule']) != 8):
        raise ValueError('frozen feature count and episode/evaluation schedule')
    contexts = []
    for item in donors:
        premises = [resolve_literal(r, reference) for r in item['ordered_hypotheses']]
        target = resolve_literal(item['target'], reference)
        contexts.append({'id': item['id'], 'split': 'donor',
                         'theory': copy.deepcopy(reference['theory_ast']),
                         'ordered_hypotheses': premises, 'target': target, 'rows': 24})
    held = split['held_out']
    contexts.append({'id': held['id'], 'split': 'heldout',
                     'theory': copy.deepcopy(reference['theory_ast']),
                     'ordered_hypotheses': resolve_literal(held['ordered_hypotheses'], reference),
                     'target': resolve_literal(held['target'], reference), 'rows': 24})
    semantic = lambda c: canonical({k: c[k] for k in
                                   ('theory', 'ordered_hypotheses', 'target', 'rows')})
    if len({semantic(c) for c in contexts}) != 5:
        raise ValueError('distinct donor contexts and context-disjoint heldout')
    if any(type(c['ordered_hypotheses']) is not list or len(c['ordered_hypotheses']) != 3
           for c in contexts):
        raise ValueError('all three ordered hypothesis occurrences required')
    if type(selector) is not str or selector not in DONOR_IDS + (HELDOUT_ID,):
        raise ValueError('only a frozen curriculum context ID may be selected')
    training = protocol['curriculum']['training_episodes']
    if (len({r['id'] for r in training}) != 8
            or any(sum(r['donor'] == d for r in training) != 2 for d in DONOR_IDS)
            or any(r['donor'] not in DONOR_IDS for r in training)):
        raise ValueError('exact two declared episodes per donor; no heldout training')
    selected = copy.deepcopy(next(c for c in contexts if c['id'] == selector))
    selected['binding'] = {'schema': VERSION, 'selector': selector,
        'partition': selected['split'], 'rows': 24,
        'document_bindings': copy.deepcopy(frozen_binding['documents']),
        'resolved_context_sha256': digest({k: selected[k] for k in
                                  ('theory', 'ordered_hypotheses', 'target', 'rows')}),
        'ordered_hypotheses_sha256': digest(selected['ordered_hypotheses']),
        'target_sha256': digest(selected['target']),
        'holdout_scope': 'Context composition only; formula/primitive/source-family overlap retained.',
        'source_only_selection': True}
    return selected
