"""SOURCE ONLY frozen point data; external accepted certificates are inputs.

No project imports, rule search, clocks, state classifier or activation. The
caller authenticates accepted evidence; an independent verifier rebuilds base
tiles/state. This constructor's flags never accept that mathematical custody.
"""
import hashlib
import json

VERSION = 'unit-row-certified-row0-point-mark-decorator-v1'
PROJECTION_VERSION = 'unit-row-row-zero-rule-projection-v1'
RULES = ['axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize']
FLAGS = ('independently_checked', 'logical_proof_accepted', 'exact_point_board_accepted',
    'complete_GCTS_model_accepted', 'marking_activated', 'trajectory_accepted',
    'GCTS_advantage_accepted', 'RL_accepted', 'ROOT_resource_accepted')
PROJECTION_FLAGS = ('logical_proof_accepted', 'exact_point_board_accepted',
    'target_impossibility_accepted', 'complete_GCTS_model_accepted',
    'marking_activation_accepted', 'trajectory_accepted', 'GCTS_advantage_accepted',
    'RL_accepted', 'ROOT_resource_accepted')


def need(ok, reason):
    if not ok:
        raise ValueError('certified point marking: ' + reason)


def tree(value, tick):
    tick()
    if type(value) in (str, int, bool) or value is None:
        return value
    if type(value) is list:
        return [tree(v, tick) for v in value]
    need(type(value) is dict and all(type(k) is str for k in value), 'builtin JSON only')
    return {k: tree(v, tick) for k, v in value.items()}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf8')


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def certificate_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def freeze_marking(*, original_binding, certificates, projection_checks, tick):
    """Validate DATA joins, not external Root acceptance or the six-rule theorem."""
    binding = tree(original_binding, tick)
    certs, checks = tree(certificates, tick), tree(projection_checks, tick)
    need(type(certs) is list and type(checks) is list and len(certs) == len(checks)
         and len(certs) > 0, 'complete nonempty paired accepted evidence')
    evidence, literals, by_hash, authority = {}, {}, {}, None
    for cert, check in zip(certs, checks):
        tick()
        need(cert['schema'] == 'unit-row-row-zero-projection-certificate-v1'
             and check['schema'] == 'unit-row-row-zero-projection-check-v1'
             and cert['version'] == check['version'] == PROJECTION_VERSION
             and cert['status'] == 'FORBIDDEN' and type(cert['row']) is int and cert['row'] == 0
             and type(cert['height']) is int and cert['height'] == 24,
             'declared input-scoped row0 certificate data')
        need(check['projection_accepted'] is True and check['compared_full_certificate'] is True
             and check['independently_checked'] is True and cert['independently_checked'] is False
             and canonical(check['recomputed_certificate']) == canonical(cert)
             and all(cert[k] is False and check[k] is False for k in PROJECTION_FLAGS),
             'complete checked certificate data with no higher acceptance')
        full_authority, literal = cert['model_authority'], cert['literal']
        need(canonical(full_authority['binding']) == canonical(binding)
             and cert['model_authority_sha256'] == certificate_sha(full_authority)
             and type(full_authority['declaration']['height']) is int
             and full_authority['declaration']['height'] == 24,
             'same whole original model authority/binding/height')
        encoded_authority = canonical(full_authority)
        need(authority is None or authority == encoded_authority, 'one literal full input scope')
        authority = encoded_authority
        need(type(literal) is list and literal and type(literal[0]) is str and literal[0] != 'imp'
             and cert['literal_sha256'] == certificate_sha(literal), 'complete nonimp literal identity')
        need([v['rule'] for v in cert['rule_exclusions']] == RULES
             and all(v['excluded'] is True for v in cert['rule_exclusions'])
             and cert['projection'] == {
                 'kind': 'NO_ORIGINAL_TILE_AT_ROW_ZERO_WITH_THIS_OUTPUT_LITERAL',
                 'complete_exact_board_cannot_assign_this_literal_at_output_zero': True,
                 'remote_markings_used': False, 'selected_placements_used': False,
                 'branch_exclusions_used': False, 'saved_ZERO_receipts_used': False},
             'exact declared projection scope, not a context nogood')
        identity = certificate_sha(cert)
        need(check['certificate_sha256'] == identity, 'whole external certificate hash')
        entry = {'certificate': cert, 'projection_check': check}
        need(identity not in by_hash or by_hash[identity] == canonical(entry),
             'full certificate/evidence collision equality')
        by_hash[identity] = canonical(entry)
        evidence[identity] = entry
        literals[canonical(literal)] = literal
    definition = {'schema': 'unit-row-certified-row0-marking-definition-v1',
        'recipe_version': VERSION, 'original_binding': binding, 'height': 24,
        'original_model_authority_sha256': certificate_sha(certs[0]['model_authority']),
        'certified_literals': [literals[k] for k in sorted(literals)],
        'certificate_sha256': sorted(evidence),
        'point_domain': {'base_positive_channel': 0, 'base_mark_channels': [1, 2, 3],
            'new_mark_channel': 4, 'local_mark_offset_interval': [-23, 0],
            'global_mark_row_interval': [0, 23], 'required_t_points_unchanged': True},
        'action': {'allowed_translations': [[0, r] for r in range(24)],
            'point_action': '[channel,d] -> [channel,d+row]', 'value_action': 'IDENTITY',
            'rotations_or_reflections': False},
        'values': {'matched_original_formula_port': 1, 'fixed_boundary': [[[4, 0], 0]],
            'unmatched_port': 'ABSENT', 'fixed_formula_ports_decorated': False},
        'projection_scope': 'EXACT_BOARDS_OF_THIS_ORIGINAL_INPUT_ONLY_ROW0_OUTPUT_LEMMA',
        'evidence_custody': 'CALLER_AUTHENTICATES_PRIOR_ROOT_ACCEPTED_INPUTS; NO_PROOF_REPLAY_HERE'}
    return {'schema': 'unit-row-certified-row0-marking-v1', 'version': VERSION,
        'marking_id': 'row0-marking-' + sha(definition), 'definition': definition,
        'certificate_evidence': [evidence[k] for k in sorted(evidence)],
        **{k: False for k in FLAGS}}


def _marking(marking, tick):
    value = tree(marking, tick)
    entries = value['certificate_evidence']
    expected = freeze_marking(original_binding=value['definition']['original_binding'],
        certificates=[v['certificate'] for v in entries],
        projection_checks=[v['projection_check'] for v in entries], tick=tick)
    need(canonical(value) == canonical(expected), 'entire frozen marking definition/evidence/id')
    return value


def _points(entries, channels, tick):
    need(type(entries) is list, 'complete point-value array')
    values = {}
    for point, value in entries:
        tick()
        need(type(point) is list and len(point) == 2 and all(type(v) is int for v in point)
             and point[0] in channels, 'exact point and declared channel')
        key = tuple(point)
        need(key not in values or canonical(values[key]) == canonical(value), 'point agreement')
        values[key] = value
    return values


def decorate_prototype(*, marking, base_tile, tick):
    """Point-data construction only. Independent verification rebuilds base tile."""
    model, base = _marking(marking, tick), tree(base_tile, tick)
    need(set(base) == {'placement_key', 'selection_record', 'local_t_values', 'local_m_values',
        'global_t_values', 'global_m_values', 'membership'}, 'whole original bare c354 tile')
    key = base['placement_key']
    need(set(key) == {'tile_type_id', 'type_preimage', 'translation'}, 'original full base key')
    pre, translation = key['type_preimage'], key['translation']
    need(type(translation) is list and len(translation) == 2
         and all(type(v) is int for v in translation) and translation[0] == 0
         and 0 <= translation[1] < 24
         and pre['input_epoch'] == model['definition']['original_binding']['language_epoch']
         and key['tile_type_id'] == 'bounded-point-tile-' + sha(pre),
         'original translation/epoch/full prototype identity')
    need(base['selection_record'] == dict(key, generation=1)
         and base['local_t_values'] == [[[0, 0], 1]]
         and base['global_t_values'] == [[[0, translation[1]], 1]], 'unchanged unit positive support')
    _points(base['local_m_values'], (1, 2, 3), tick)
    _points(base['global_m_values'], (1, 2, 3), tick)
    translated = [[[p[0], p[1]+translation[1]], v] for p, v in base['local_m_values']]
    need(canonical(translated) == canonical(base['global_m_values']), 'whole original marking action')
    table = {canonical(v).decode('utf8') for v in model['definition']['certified_literals']}
    added = {}
    for point, value in base['local_m_values']:
        tick()
        need(-23 <= point[1] <= 0, 'original finite local support')
        if point[0] == 1:
            need(type(value) is list and len(value) == 2 and value[0] == 'formula'
                 and type(value[1]) is str, 'original literal formula port')
            if value[1] in table:
                added[(4, point[1])] = 1
    local = [[list(p), v] for p, v in sorted(added.items())]
    glob = [[[p[0], p[1]+translation[1]], v] for p, v in local]
    need(all(0 <= p[1] < 24 for p, v in glob), 'strict original absolute support')
    decorated_pre = {'schema': 'unit-row-row0-decorated-type-v1',
        'base_type_preimage': pre, 'marking_id': model['marking_id']}
    return {'schema': 'unit-row-row0-decorated-tile-v1', 'version': VERSION,
        'marking_id': model['marking_id'], 'base_tile': base,
        'placement_key': {'tile_type_id': 'row0-decorated-tile-' + sha(decorated_pre),
            'type_preimage': decorated_pre, 'translation': translation},
        'local_t_values': base['local_t_values'], 'global_t_values': base['global_t_values'],
        'local_m_values': base['local_m_values'] + local,
        'global_m_values': base['global_m_values'] + glob,
        'added_local_m_values': local, 'added_global_m_values': glob,
        **{k: False for k in FLAGS}}


def decorate_state(*, marking, base_state, decorated_selected, tick):
    """Compose actual assignments; a channel4 disagreement is ordinary conflict."""
    model = _marking(marking, tick)
    state, selected = tree(base_state, tick), tree(decorated_selected, tick)
    need(set(state) == {'schema', 'input_epoch', 'height', 't', 'm', 'selected', 'excluded', 'generation'}
         and state['schema'] == 'unit-row-implicit-private-state-v1'
         and type(state['height']) is int and state['height'] == 24
         and state['input_epoch'] == model['definition']['original_binding']['language_epoch'],
         'whole original projected state and epoch')
    need(type(selected) is list and len(selected) == len(state['selected']), 'all selected base projections')
    marks = _points(state['m'], (1, 2, 3), tick)
    extras = {(4, 0): 0}
    for record, packet in zip(state['selected'], selected):
        tick()
        expected = decorate_prototype(marking=model, base_tile=packet['base_tile'], tick=tick)
        need(canonical(packet) == canonical(expected)
             and canonical(packet['base_tile']['selection_record']) == canonical(record),
             'complete decorated packet and exact selected projection/order')
        for point, value in packet['added_global_m_values']:
            p = tuple(point)
            need(p not in extras or extras[p] == value, 'channel4 point-mark conflict')
            extras[p] = value
    need(not (set(marks) & set(extras)), 'fresh auxiliary channel, never base overwrite')
    full = dict(marks)
    full.update(extras)
    return {'schema': 'unit-row-row0-decorated-state-v1', 'version': VERSION,
        'marking_id': model['marking_id'], 'base_state': state, 'decorated_selected': selected,
        'global_t_values': state['t'],
        'global_m_values': [[list(p), v] for p, v in sorted(full.items())],
        'added_m_values': [[list(p), v] for p, v in sorted(extras.items())],
        **{k: False for k in FLAGS}}
