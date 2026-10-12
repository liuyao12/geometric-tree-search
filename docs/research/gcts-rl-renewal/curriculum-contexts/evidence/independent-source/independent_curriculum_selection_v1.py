"""Independent literal five-context specification and immutable document binding.

SOURCE ONLY. These routines have not been called. A future separately ROOT
owned static auditor supplies independent equality/digest helpers and documents
whose raw bytes are already pinned by its plan. No producer selector is used.
"""
import copy

SELECTORS = ('donor-two-guards', 'donor-two-equalities',
             'donor-repeated-guard', 'donor-repeated-equality',
             'heldout-mixed-guard-equality')
DOCUMENTS = {
    'reference': {'raw_pin': {'path': '.gcts-active/fixed-family-transfer-plan-20261012/next-experiment-v1.json',
        'sha256': 'f2f8c25b21dfee4966bdcfd6fe93d0dcaa4c4caf194a3a83462474cf9db5f24b', 'bytes': 25906},
        'canonical_sha256': '866af9ba7ef1befe0197be0241377d58d7cd042b06673f88f55bb9705b2b63b4'},
    'split': {'raw_pin': {'path': '.gcts-active/family-proposal-rl-small-source-20261012/donor-split-v1.json',
        'sha256': '7085af5ac8304faf3268ee7117bb9674c77f849cdb17b45899a9fc6c4eb0e4ed', 'bytes': 4811},
        'canonical_sha256': '80031da3781bd100c2b9a5dc0daf4f13e04a02b8d7cffff3e5ed00187c6de0a3'},
    'protocol': {'raw_pin': {'path': '.gcts-active/family-proposal-rl-small-source-20261012/protocol-v1.json',
        'sha256': '1669b1591aad9504d9415dce7ddc2eebd09eb2d9393685c796f585e3a605c8b5', 'bytes': 19813},
        'canonical_sha256': 'fd5554888ed03de13bb48aa663b6e841fbfa05a0e6baacbd5a62f546e771dd46'},
}
DOCUMENT_ROLES = {'reference': 'curriculum_reference', 'split': 'frozen_donor_split',
                  'protocol': 'frozen_RL_protocol'}
TRAINING = (
    ('d1-r1', SELECTORS[0], 1201201), ('d2-r1', SELECTORS[1], 1201202),
    ('d3-r1', SELECTORS[2], 1201203), ('d4-r1', SELECTORS[3], 1201204),
    ('d4-r2', SELECTORS[3], 1201214), ('d3-r2', SELECTORS[2], 1201213),
    ('d2-r2', SELECTORS[1], 1201212), ('d1-r2', SELECTORS[0], 1201211),
)
EVALUATION = (('base', 1, None), ('fixed', 1, None), ('untrained', 1, 1201291),
              ('trained', 1, 1201291), ('trained', 2, 1201292),
              ('untrained', 2, 1201292), ('fixed', 2, None), ('base', 2, None))


def problem(selector):
    """Independently authored literal theory and all five ordered sequents."""
    if type(selector) is not str or selector not in SELECTORS:
        raise ValueError('exact immutable five-context selector')
    def const(name): return ['fun', name, []]
    def var(name): return ['var', name]
    def pred(name, *terms): return ['pred', name, list(terms)]
    def guard(p, q, l, m):
        terms = [pred('Point', p), pred('Point', q), pred('Line', l), pred('Line', m),
                 ['not', ['eq', p, q]], pred('Incident', p, l), pred('Incident', q, l),
                 pred('Incident', p, m), pred('Incident', q, m)]
        tail = terms[-1]
        for item in reversed(terms[:-1]): tail = ['and', item, tail]
        return tail
    P, Q, R, l, m, n = map(const, ('P', 'Q', 'R', 'l', 'm', 'n'))
    a, b, u, v = map(var, ('point0', 'point1', 'line0', 'line1'))
    axiom = ['imp', guard(a, b, u, v), ['eq', u, v]]
    for name in reversed(('point0', 'point1', 'line0', 'line1')):
        axiom = ['all', name, axiom]
    theory = dict(functions={name: 0 for name in ('P', 'Q', 'R', 'l', 'm', 'n')},
        predicates={'Point': 1, 'Line': 1, 'Incident': 2}, schemas=[], axioms={'I.2-uniqueness': axiom})
    Hlm, Hmn = guard(P, Q, l, m), guard(P, Q, m, n)
    Elm, Emn, root = ['eq', l, m], ['eq', m, n], pred('Incident', R, l)
    gammas = ([Hlm, Hmn, root], [Elm, Emn, root], [Hlm, Hlm, root],
              [Elm, Elm, root], [Hlm, Emn, root])
    chosen = SELECTORS.index(selector)
    return dict(theory=theory, old_gamma=copy.deepcopy(gammas[0]), gamma=copy.deepcopy(gammas[chosen]),
        target=pred('Incident', R, m if chosen in (2, 3) else n))


def metadata_value(record, reference):
    """Own simple reference traversal; no compiler/theorem/proof decoder."""
    if type(record) is not dict:
        raise ValueError('literal metadata record')
    if set(record) == {'literal_ast'}:
        return copy.deepcopy(record['literal_ast'])
    if set(record) != {'metadata_reference'}:
        raise ValueError('one exact metadata-reference field')
    path = record['metadata_reference']
    if type(path) is not list or not path:
        raise ValueError('nonempty exact metadata path')
    at = reference
    for token in path:
        if type(token) is str and type(at) is dict and token in at:
            at = at[token]
        elif type(token) is int and type(at) is list and 0 <= token < len(at):
            at = at[token]
        else:
            raise ValueError('exact field/index metadata traversal; Boolean indices rejected')
    return copy.deepcopy(at)


def selected_binding(documents, plan, p, b):
    """Reconstruct complete binding from immutable sources, not caller hashes."""
    p.need(plan['schema'] == 'frozen-curriculum-family-preparation-plan-v1'
           and plan['selector'] in SELECTORS and type(plan['selector']) is str
           and plan['RL_full_pool_capacity'] == 64 and type(plan['RL_full_pool_capacity']) is int
           and plan['execution_authorized_by_source_freeze'] is False, 'exact source-only preparation contract')
    literal = {r['role']: {k:r[k] for k in ('path','sha256','bytes')} for r in plan['inputs']}
    for name, role in DOCUMENT_ROLES.items():
        b.equal(literal[role], DOCUMENTS[name]['raw_pin'], 'exact independently frozen document raw pin '+name)
        b.equal(p.digest(documents[role]), DOCUMENTS[name]['canonical_sha256'], 'independently frozen document content '+name)
    frozen = documents['frozen_selection_binding']
    b.equal(frozen, dict(schema='frozen-five-context-selection-v1', documents=DOCUMENTS,
        selectors=list(SELECTORS), execution_authorized=False,
        scope='Canonical hashes of literal metadata documents only; no context selector or compiler invoked.'),
        'complete immutable compiler selection-binding metadata')
    reference, split, protocol = (documents[DOCUMENT_ROLES[n]] for n in ('reference','split','protocol'))
    old, held = problem(SELECTORS[0]), problem(SELECTORS[-1])
    for name, value in [('theory_ast', old['theory']), ('original_ordered_hypotheses_ast', old['old_gamma']),
                        ('new_ordered_hypotheses_ast', held['gamma']), ('target_ast', held['target'])]:
        b.equal(reference[name], value, 'own literal reference AST '+name)
    p.need(split['schema'] == 'small-whole-family-context-split-v1'
           and split['execution_authorized'] is False and protocol['execution_authorized'] is False
           and protocol['schema'] == 'small-source-family-RL-protocol-v1', 'exact original split/protocol')
    b.equal(tuple(d['id'] for d in split['donors']), SELECTORS[:-1], 'complete ordered donor declaration')
    b.equal(split['held_out']['id'], SELECTORS[-1], 'exact heldout declaration')
    for i, declaration in enumerate(split['donors'] + [split['held_out']]):
        expected = problem(SELECTORS[i])
        hypotheses = (metadata_value(declaration['ordered_hypotheses'], reference) if i == 4 else
                      [metadata_value(r, reference) for r in declaration['ordered_hypotheses']])
        b.equal(hypotheses, expected['gamma'], 'literal independent ordered context '+SELECTORS[i])
        b.equal(metadata_value(declaration['target'], reference), expected['target'], 'literal independent target '+SELECTORS[i])
    b.equal([(r['id'],r['donor'],r['seed']) for r in protocol['curriculum']['training_episodes']],
            list(TRAINING), 'entire frozen chronological donor schedule')
    b.equal([(r['lane'],r['repeat'],r['seed']) for r in protocol['evaluation']['schedule']],
            list(EVALUATION), 'entire fixed heldout evaluation schedule')
    p.need(type(protocol['features']['count']) is int and protocol['features']['count'] == 31,
           'unchanged 31-feature version')
    boundary = split['common_boundary']
    b.equal([boundary['rows'], boundary['seed_rows'], boundary['target_row']], [24, [0,1,2], 23],
            'every fixed boundary dimension and ordered root seed')
    chosen = problem(plan['selector'])
    return dict(schema='frozen-five-context-selection-v1', selector=plan['selector'],
        partition='heldout' if plan['selector'] == SELECTORS[-1] else 'donor', rows=24,
        document_bindings=copy.deepcopy(DOCUMENTS),
        resolved_context_sha256=p.digest(dict(theory=chosen['theory'], ordered_hypotheses=chosen['gamma'],
                                             target=chosen['target'], rows=24)),
        ordered_hypotheses_sha256=p.digest(chosen['gamma']), target_sha256=p.digest(chosen['target']),
        holdout_scope='Context composition only; formula/primitive/source-family overlap retained.', source_only_selection=True)
