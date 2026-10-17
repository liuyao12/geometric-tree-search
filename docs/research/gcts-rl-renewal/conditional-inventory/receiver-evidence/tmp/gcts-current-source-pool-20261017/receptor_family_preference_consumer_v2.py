"""SOURCE ONLY: whole checked families supply primitive ordering preferences.

No imports of project modules, clocks, engine or result data. Caller authenticates
all injected Sources and original17/input2 authority. No proposed member is a fact,
degree, EOF, exclusion, atomic move or root proof. Each continuation is rebuilt.
"""
import hashlib
import json

VERSION = 'receptor-family-primitive-preference-consumer-v2-batch-collision-ledger'
BATCH_SCHEMA = 'receptor-family-primitive-preference-batch-v1'
REQUEST_SCHEMA = 'receptor-family-primitive-preference-request-v1'
FAMILY_SCHEMA = 'receptor-family-pending-primitive-instance-v1'
RECEIPT_SCHEMA = 'receptor-family-primitive-preference-check-v1'
INSTANCE_FIELDS = {'registry', 'family_id', 'host', 'substitution', 'port_bindings',
                   'proposal', 'row_assignment'}
FLAGS = ('logical_proof_accepted', 'exact_point_board_accepted',
    'degree_or_EOF_accepted', 'scheduler_accepted', 'complete_GCTS_model_accepted',
    'trajectory_accepted', 'learned_marking_accepted', 'RL_accepted', 'ROOT_resource_accepted')
REASONS = ('already_selected', 'branch_excluded_complete_key', 'whole_support_capacity',
           'whole_remote_or_metadata_mark_conflict')


def need(ok, reason):
    if not ok:
        raise ValueError('receptor preference consumer: ' + reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def family_identity(family):
    return digest({k: family[k] for k in ('binding', 'marking_id', 'initial_instance', 'member_keys')})


def consume_preferences(*, language, base_semantics, marked_semantics, producer,
                        expansion_checker, host_adapter, state, decision, request, tick):
    """Fresh whole-instance check, only after the engine's real global BRANCH.

    This endpoint validates the declared BRANCH shape, not its global authority.
    That authority belongs to engine decision(); component calls alone cannot
    certify it. No external errors are caught or reinterpreted as stale hints.
    """
    tick()
    offered_state, offered_request = state, request
    original_state, original_request = canonical(state), canonical(request)
    point = marked_semantics
    need(point.VERSION == 'unit-row-channel4-filtered-degree-semantics-v1'
         and point.base is base_semantics
         and producer.VERSION == 'receptor-family-typed-expander-v1'
         and expansion_checker.VERSION == 'receptor-family-independent-expansion-checker-v1'
         and host_adapter.VERSION == 'receptor-family-six-rule-point-adapter-v3-physical-call-sharing',
         'exact point/producer/checker/adapter APIs')
    state = point.tree(state, tick)
    request = point.tree(request, tick)
    decision = point.tree(decision, tick)
    need(type(decision) is dict and set(decision) == {'kind', 'row'}
         and decision['kind'] == 'BRANCH' and type(decision['row']) is int
         and 0 <= decision['row'] < 24, 'selected actual branch row shape')
    need(type(request) is dict and set(request) == {'schema', 'mode', 'payload'}
         and request['schema'] == REQUEST_SCHEMA
         and request['mode'] in ('BATCH', 'CONTINUATION'), 'explicit family request union')
    checked_state, totals, marks, selected, excluded, names = point.private_state(language, state, tick)
    need(canonical(checked_state) == canonical(state) and totals[(0, decision['row'])] == 0,
         'entire checked state and unfilled selected row')
    host = host_adapter.describe_host(language=language, tick=tick)
    entry = {'state': point.tree(state, tick), 'decision': point.tree(decision, tick),
             'read_occupancy': [[r, totals[(0, r)] == 1] for r in range(24)]}
    checks, invalidations = [], []

    def finish(status, selection=None):
        tick()
        need(canonical(host_adapter.describe_host(language=language, tick=tick)) == canonical(host)
             and canonical(checked_state) == original_state
             and canonical(request) == original_request
             and canonical(offered_state) == original_state
             and canonical(offered_request) == original_request, 'full entry state/request and authority unchanged')
        return {'schema': RECEIPT_SCHEMA, 'version': VERSION, 'mode': request['mode'],
            'binding': point.tree(language.binding, tick), 'marking_id': state['marking_id'],
            'state_sha256': digest(state), 'decision': point.tree(decision, tick),
            'request_sha256': digest(request), 'status': status, 'selection': selection,
            'entry': entry, 'checks': checks, 'invalidations': invalidations,
            **{k: False for k in FLAGS}}

    def adapt(instance):
        need(type(instance) is dict and set(instance) == INSTANCE_FIELDS, 'full ordinary family instance')
        result = host_adapter.adapt_expansion(language=language, base_semantics=base_semantics,
            marked_semantics=point, expansion_checker=expansion_checker,
            **point.tree(instance, tick), state=point.tree(state, tick), tick=tick)
        checks.append({'instance': point.tree(instance, tick), 'adaptation': result})
        need(result['status'] in ('READY_LOCAL_CLUSTER', 'UNKNOWN'), 'adapter result status')
        if result['status'] == 'READY_LOCAL_CLUSTER':
            need(result['local_member_membership_checked'] is True
                 and result['local_point_union_checked'] is True
                 and result['union_state_check']['marked_state_checked'] is True,
                 'full independent expansion/native membership/whole point union')
            # One full-preimage ledger spans ALL offered READY instances. Each
            # adapter also checks its own internal union and current-state ledger.
            for member in result['members']:
                tick()
                point.check_collision(member['tile'], names)
        return result

    def choose(family, result):
        need([m['tile']['placement_key'] for m in result['members']] == family['member_keys'],
             'same full original member-key sequence after fresh reconstruction')
        options = [m for m in result['members'] if not m['already_selected_in_input']
                   and m['tile']['placement_key']['translation'] == [0, decision['row']]]
        if not options:
            return None
        candidate = point.with_obligations(point.tree(options[0]['tile'], tick), totals, tick)
        need(point.legality(candidate, totals, marks, selected, excluded) is None,
             'next primitive member whole current legality')
        key = candidate['placement_key']
        lineage = family['lineage'] + [{'key': point.tree(key, tick), 'state_sha256': digest(state)}]
        need(len(lineage) <= 24, 'at most one installed preference per required row')
        family = dict(family, lineage=lineage)
        # The full family remains a preference. Installed exact members are only
        # recognized by current selected keys on the next independently checked call.
        return {'candidate': candidate, 'family': family}

    if request['mode'] == 'BATCH':
        batch = request['payload']
        need(type(batch) is dict and set(batch) == {'schema', 'status', 'binding', 'marking_id',
                'state_sha256', 'decision', 'instances'} and batch['schema'] == BATCH_SCHEMA
             and batch['status'] in ('READY', 'UNKNOWN')
             and canonical(batch['binding']) == canonical(language.binding)
             and batch['marking_id'] == state['marking_id']
             and batch['state_sha256'] == digest(state) and batch['decision'] == decision
             and type(batch['instances']) is list and len(batch['instances']) <= 8,
             'exact current finite preference batch, never a base domain')
        if batch['status'] == 'UNKNOWN':
            need(batch['instances'] == [], 'UNKNOWN has no partial family')
            return finish('UNKNOWN')
        complete = []
        # Check every offered READY instance before selecting any one of them.
        for instance in batch['instances']:
            tick()
            result = adapt(instance)
            if result['status'] == 'UNKNOWN':
                complete.append(None)
                continue
            family = {'schema': FAMILY_SCHEMA, 'binding': point.tree(language.binding, tick),
                'marking_id': state['marking_id'], 'initial_instance': point.tree(instance, tick),
                'current_instance': point.tree(instance, tick),
                'member_keys': point.tree(result['decorated_member_keys'], tick), 'lineage': []}
            family['family_instance_id'] = family_identity(family)
            complete.append((family, result))
        if any(v is None for v in complete):
            return finish('UNKNOWN')
        for family, result in complete:
            selection = choose(family, result)
            if selection is not None:
                return finish('READY', selection)
        return finish('NO_MATCH')

    family = request['payload']
    need(type(family) is dict and set(family) == {'schema', 'family_instance_id', 'binding',
            'marking_id', 'initial_instance', 'current_instance', 'member_keys', 'lineage'}
         and family['schema'] == FAMILY_SCHEMA
         and canonical(family['binding']) == canonical(language.binding)
         and family['marking_id'] == state['marking_id']
         and family['family_instance_id'] == family_identity(family)
         and type(family['member_keys']) is list and 0 < len(family['member_keys']) <= 24
         and len({canonical(k) for k in family['member_keys']}) == len(family['member_keys'])
         and type(family['lineage']) is list and len(family['lineage']) <= 24,
         'whole owned pending family identity/authority')
    initial = family['initial_instance']
    need(type(initial) is dict and set(initial) == INSTANCE_FIELDS, 'full initial family instance')
    # Only explicit ordinary legality results can abandon a pending hint. Rebuild,
    # membership, authority, collision, protocol and callback failures propagate.
    for key in family['member_keys']:
        tick()
        tile = point.rebuild_tile(language, key['type_preimage'], key['translation'], tick)
        need(canonical(tile['placement_key']) == canonical(key), 'full pending member key reconstruction')
        point.check_collision(tile, names)
        reason = point.legality(tile, totals, marks, selected, excluded)
        need(reason is None or reason in REASONS, 'known whole point legality result')
        if reason is not None and reason != 'already_selected':
            invalidations.append({'kind': 'MEMBER', 'key': point.tree(key, tick), 'reason': reason})
    original = point.base_state(language, state, tick)
    originals = {r['translation'][1]: {k: v for k, v in r.items() if k != 'generation'}
                 for r in original['selected']}
    refreshed = point.tree(initial, tick)
    for port in refreshed['port_bindings']['inputs']:
        tick()
        source = port['source']
        need(type(source) is dict and set(source) == {'schema', 'row', 'original_full_key'}
             and source['schema'] == 'receptor-family-six-rule-input-source-v1'
             and type(source['row']) is int and 0 <= source['row'] < 24,
             'frozen external input row provenance')
        row = source['row']
        if (1, row) in marks and marks[(1, row)] != ['formula', base_semantics.text(port['formula'])]:
            invalidations.append({'kind': 'INPUT', 'port_id': port['port_id'], 'row': row,
                'reason': 'whole_remote_or_metadata_mark_conflict'})
        port['occupied'] = totals[(0, row)] == 1
        port['fact_accepted'] = False
        port['source'] = {'schema': source['schema'], 'row': row,
                          'original_full_key': originals.get(row)}
    if invalidations:
        return finish('INVALIDATED')
    refreshed['host'] = point.tree(host, tick)
    refreshed['proposal'] = producer.expand_family(**{k: point.tree(refreshed[k], tick)
        for k in ('registry', 'family_id', 'host', 'substitution', 'port_bindings')}, tick=tick)
    if refreshed['proposal']['status'] == 'UNKNOWN':
        checks.append({'instance': refreshed, 'adaptation': None})
        return finish('UNKNOWN')
    result = adapt(refreshed)
    if result['status'] == 'UNKNOWN':
        return finish('UNKNOWN')
    family = dict(family, current_instance=refreshed)
    selection = choose(family, result)
    if selection is not None:
        return finish('READY', selection)
    # Completed exact members need no ongoing preference; canonical work elsewhere
    # may proceed while an unconsumed checked member remains on another row.
    pending = any(canonical(k) not in selected for k in family['member_keys'])
    return finish('NO_MATCH', {'candidate': None, 'family': family} if pending else None)
