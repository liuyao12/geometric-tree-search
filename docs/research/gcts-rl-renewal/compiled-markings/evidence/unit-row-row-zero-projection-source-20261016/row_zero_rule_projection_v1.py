"""SOURCE ONLY: input-scoped row-zero six-rule projection certificates.

No search, carrier, point-state mutation, clocks or project imports. The caller
authenticates original input bytes/Source17 separately from current execution.
This structural certificate is distinct from c354's full-context ZERO receipt.
"""
import hashlib
import json

VERSION = 'unit-row-row-zero-rule-projection-v1'
PROFILE_NAME = 'shared-bounded-six-rule-B12-N44-v2'
PROFILE_SHA256 = '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'
KERNEL_VERSION = 'arithmetic-open-parameter-six-rule-Q-v1'
ORIGINAL_SOURCES = {
    'kernel': ('43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9', 10323),
    'membership': ('5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332', 20112),
    'degree_checker': ('c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d', 27553)}
ARITIES = {'axiom': 0, 'assumption': 0, 'instantiate': 0,
           'eq_subst': 0, 'mp': 2, 'generalize': 1}
FALSE_FLAGS = ('logical_proof_accepted', 'exact_point_board_accepted',
    'target_impossibility_accepted', 'complete_GCTS_model_accepted',
    'marking_activation_accepted', 'trajectory_accepted', 'GCTS_advantage_accepted',
    'RL_accepted', 'ROOT_resource_accepted')


def need(ok, reason):
    if not ok:
        raise ValueError('row-zero projection: ' + reason)


def tree(value, tick):
    tick()
    if type(value) in (str, int, bool) or value is None:
        return value
    if type(value) is list:
        return [tree(v, tick) for v in value]
    need(type(value) is dict and all(type(k) is str for k in value),
         'literal builtin JSON authority/certificate without floats')
    return {k: tree(v, tick) for k, v in value.items()}


def canonical(value):
    # Same ASCII canonical hash convention as original bounded membership.
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _check_authority(language, authority, tick):
    tick()
    need(type(authority) is dict and set(authority) ==
         {'declaration', 'policy', 'source_bindings', 'binding'},
         'private original authority fields')
    declaration, policy, sources, binding = (authority[k] for k in
        ('declaration', 'policy', 'source_bindings', 'binding'))
    actual = {k: tree(getattr(language, k), tick) for k in authority}
    need(canonical(actual) == canonical(authority),
         'entire original declaration/policy/Source17/binding equality')
    need(type(declaration['height']) is int and declaration['height'] == 24,
         'original height24, not Boolean or altered height')
    need(policy['schema'] == 'ROOT-shared-bounded-six-rule-language-policy-v2'
         and policy['profile_name'] == PROFILE_NAME
         and policy['syntax']['maximum_term_nodes'] == 12
         and policy['syntax']['maximum_whole_formula_nodes'] == 44,
         'original bounded syntax profile')
    need(set(binding) == {'profile_name', 'profile_sha256', 'declaration_sha256',
         'logical_input_sha256', 'source_bindings_sha256', 'language_epoch'}
         and binding['profile_name'] == PROFILE_NAME
         and binding['profile_sha256'] == PROFILE_SHA256,
         'original binding fields and exact raw policy pin')
    need(type(sources) is dict and len(sources) == 17, 'entire original Source17 map')
    for role, (sha256, size) in ORIGINAL_SOURCES.items():
        tick()
        capsule = sources[role]
        need(type(capsule) is dict and capsule['sha256'] == sha256
             and type(capsule['bytes']) is int and capsule['bytes'] == size,
             'original pinned six-rule/point-inventory source ' + role)
    need(language.kernel_module.VERSION == KERNEL_VERSION
         and language.kernel_module.ARITIES == ARITIES,
         'actual original six-rule kernel and arities')
    fields = {'theory': declaration['theory'], 'parameters': declaration['parameters'],
              'gamma': declaration['ordered_Gamma'], 'target': declaration['target']}
    for name, value in fields.items():
        need(canonical(tree(getattr(language, name), tick)) == canonical(value),
             'effective original language field ' + name)
    need(language.parameter_set == frozenset(declaration['parameters'])
         and type(language.parameter_set) is frozenset,
         'effective declared parameter scope')
    kernel = language.kernel
    need(canonical(tree(kernel.theory, tick)) == canonical(declaration['theory'])
         and type(kernel.parameters) is tuple
         and list(kernel.parameters) == declaration['parameters']
         and canonical(tree(kernel.gamma, tick)) == canonical(declaration['ordered_Gamma']),
         'actual kernel original theory/parameters/ordered Gamma')
    logical_input = {'theory': fields['theory'], 'parameters': fields['parameters'],
        'ordered_Gamma': fields['gamma'], 'target': fields['target'], 'height': 24}
    need(binding['logical_input_sha256'] == digest(logical_input)
         and binding['source_bindings_sha256'] == digest(sources),
         'recomputed whole logical input and Source17 bindings')
    preimage = {k: v for k, v in binding.items() if k != 'language_epoch'}
    need(binding['language_epoch'] == digest(preimage), 'recomputed original language epoch')
    tick()


def certify_row_zero_projection(*, language, authority, literal, tick):
    """Propose the complete finite structural argument; no old ZERO is input.

    authority is caller-private, from authenticated original raw inputs/map.
    An original AX/Gamma match or implication returns NOT_CERTIFIED, not ZERO.
    Membership/kernel/native failures propagate; no catch turns them into proof.
    """
    authority, literal = tree(authority, tick), tree(literal, tick)
    _check_authority(language, authority, tick)
    demand_bytes = canonical(literal)
    nodes = language.formula(literal)
    need(type(nodes) is int and 1 <= nodes <= 44, 'completed in-profile whole formula')
    nonimp = literal[0] != 'imp'
    axioms, gamma = [], []
    for name in sorted(authority['declaration']['theory']['axioms']):
        tick()
        formula = tree(authority['declaration']['theory']['axioms'][name], tick)
        witness = {'rule': 'axiom', 'name': name, 'formula': formula}
        member = language.primitive(witness, [])
        axioms.append({'name': name, 'formula': formula,
            'equals_demand': canonical(formula) == demand_bytes,
            'primitive_membership': tree(member, tick)})
    for index, original in enumerate(authority['declaration']['ordered_Gamma']):
        tick()
        formula = tree(original, tick)
        witness = {'rule': 'assumption', 'index': index, 'formula': formula}
        member = language.primitive(witness, [])
        gamma.append({'index': index, 'formula': formula,
            'equals_demand': canonical(formula) == demand_bytes,
            'primitive_membership': tree(member, tick)})
    ax_matches = [v['name'] for v in axioms if v['equals_demand']]
    gamma_matches = [v['index'] for v in gamma if v['equals_demand']]
    rules = [
        {'rule': 'axiom', 'ordered_arity': 0, 'excluded': not ax_matches,
         'reason': 'COMPLETE_NAMED_AXIOM_CENSUS', 'matching_names': ax_matches},
        {'rule': 'assumption', 'ordered_arity': 0, 'excluded': not gamma_matches,
         'reason': 'COMPLETE_OCCURRENCE_ORDERED_GAMMA_CENSUS', 'matching_indices': gamma_matches},
        {'rule': 'instantiate', 'ordered_arity': 0, 'excluded': nonimp,
         'reason': 'PINNED_UI_CONCLUSION_HAS_OUTER_IMP', 'required_outer_tag': 'imp'},
        {'rule': 'eq_subst', 'ordered_arity': 0, 'excluded': nonimp,
         'reason': 'PINNED_EQUALITY_TRANSPORT_CONCLUSION_HAS_OUTER_IMP', 'required_outer_tag': 'imp'},
        {'rule': 'mp', 'ordered_arity': 2, 'excluded': True,
         'reason': 'NO_NONNEGATIVE_STRICT_PRIOR_ABSOLUTE_ROW', 'allowed_read_rows': []},
        {'rule': 'generalize', 'ordered_arity': 1, 'excluded': True,
         'reason': 'NO_NONNEGATIVE_STRICT_PRIOR_ABSOLUTE_ROW', 'allowed_read_rows': []}]
    forbidden = all(v['excluded'] for v in rules)
    _check_authority(language, authority, tick)
    need(canonical(literal) == demand_bytes, 'literal unchanged across original delegates')
    certificate = {'schema': 'unit-row-row-zero-projection-certificate-v1',
        'version': VERSION, 'status': 'FORBIDDEN' if forbidden else 'NOT_CERTIFIED',
        'reason': ('ALL_SIX_PRIMITIVE_FIBRES_EMPTY' if forbidden else
            'IMPLICATION_LITERAL_OUTSIDE_PROJECTION_FAMILY' if not nonimp else
            'ORIGINAL_AXIOM_OR_GAMMA_OCCURRENCE_MATCHES'),
        'model_authority': authority, 'model_authority_sha256': digest(authority),
        'literal': literal, 'literal_sha256': digest(literal), 'row': 0, 'height': 24,
        'assumptions': {'original_source_pins': {
                role: {'sha256': sha256, 'bytes': size}
                for role, (sha256, size) in ORIGINAL_SOURCES.items()},
            'six_rules_and_ordered_arities': dict(ARITIES),
            'whole_formula_nodes': nodes, 'outer_tag': literal[0], 'nonimplication': nonimp,
            'unit_positive_support': [[[0, 0], 1]], 'translation': [0, 0],
            'read_offset_bounds': [-23, -1], 'strict_prior_reads': True,
            'nonnegative_absolute_reads': True, 'available_prior_absolute_rows': [],
            'point_read_condition': '0 <= row + offset < row; row = 0',
            'point_inventory_scope': 'Original pinned c354 unit-row translation/arity contract'},
        'named_axiom_census': axioms, 'ordered_Gamma_census': gamma, 'rule_exclusions': rules,
        'projection': {'kind': 'NO_ORIGINAL_TILE_AT_ROW_ZERO_WITH_THIS_OUTPUT_LITERAL',
            'complete_exact_board_cannot_assign_this_literal_at_output_zero': forbidden,
            'remote_markings_used': False, 'selected_placements_used': False,
            'branch_exclusions_used': False, 'saved_ZERO_receipts_used': False},
        'independently_checked': False, **{key: False for key in FALSE_FLAGS}}
    tick()
    return certificate


def check_row_zero_projection(*, language, authority, literal, certificate, tick):
    """Freshly recompute every assumption/census/exclusion and compare FULL data."""
    supplied = tree(certificate, tick)
    expected = certify_row_zero_projection(language=language, authority=authority,
                                            literal=literal, tick=tick)
    need(canonical(supplied) == canonical(expected),
         'complete certificate matches original authority/literal/census/six-rule reasons')
    tick()
    return {'schema': 'unit-row-row-zero-projection-check-v1', 'version': VERSION,
        'certificate_sha256': digest(supplied), 'compared_full_certificate': True,
        'recomputed_certificate': expected, 'projection_accepted': expected['status'] == 'FORBIDDEN',
        'independently_checked': True, **{key: False for key in FALSE_FLAGS}}
