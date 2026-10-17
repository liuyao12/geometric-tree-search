"""SOURCE ONLY: reuse a frozen inventory at a genuinely searched receiver.

The original full mathematical model, exact frozen marking and native bounds
belong to Root's authenticated caller. This is an advisory two-node search
probe with a reused library, not a new theorem or a cold construction benchmark.
"""
import hashlib
import json

VERSION = 'ROOT-receiver-inference-cases-v1'
RESULT_SCHEMA = 'ROOT-receiver-inference-evidence-v1'
BRANCH_TIE = 'ASSIGNED-OUTPUT-THEN-ROW'
MAXIMUM_NODES = 2
MAXIMUM_EVENTS = 256
POOL_POLICY = 'FIRST_QUALIFIED_OPEN_POOL_THEN_NATIVE_FALLBACK'
PROVIDER_LIMITS = {'work': 1000000, 'depth': 128, 'input_bytes': 4194304,
                   'records': 2, 'row_trials': 64, 'instances': 1}


def require(ok, reason):
    if not ok:
        raise ValueError('receiver inference case: ' + reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def run_receiver(*, language, base_semantics, marked_semantics, modules,
                 frozen_inventory, matching_mode, tick, phase):
    """The same existing scheduler and full fallback run in both matched arms."""
    tick()
    require(matching_mode in ('VISIBLE_RECEPTOR', 'LITERAL_GROUND'), 'declared comparison arm')
    point = marked_semantics

    def copy(value):
        return point.tree(value, tick)

    origin = canonical(frozen_inventory)
    require(frozen_inventory['schema'] == 'ROOT-native-productive-conditional-inventory-evidence-v1'
            and frozen_inventory['status'] == 'CHECKED_CONDITIONAL_INVENTORY'
            and len(frozen_inventory['qualified_records']) == 4
            and all(x['status'] == 'CHECKED_SOURCE_GROUND_CONDITIONAL_RECORD'
                    for x in frozen_inventory['qualified_records']), 'whole qualified frozen source pool')
    pools = frozen_inventory['minings']
    require(len(pools) == 2 and {x['slot'] for x in pools} == {'closed', 'open'}
            and all(x['status'] == 'PROPOSALS' for x in pools), 'both saved alternatives retained')
    pool = next(x for x in pools if x['slot'] == 'open')
    mined = copy(pool['mining'])
    require(len(mined['families']) == 2, 'literal and abstract records in chosen open pool')
    pool_identity = digest(mined)
    router = modules['degree_router']
    routed = router.RoutedMarkedSemantics(point_semantics=point,
        legacy_proposer=modules['proposer'],
        marked_aware_proposer=modules['marked_aware_proposer'],
        marked_aware_checker=modules['marked_aware_checker'], tick=tick)
    initial = point.initial_state(language, tick)
    require(initial['height'] == 24 and initial['selected'] == initial['excluded'] == [],
            'actual original empty24row root; no supplied proof or receiver')
    observations = {'degree_queries': [], 'provider_calls': [], 'consumer_calls': []}
    provider_started = False

    def degree_proposer(**kw):
        tick()
        value = routed.propose_degree(**kw)
        observations['degree_queries'].append({'row': kw['row'],
            'state': copy(kw['state']), 'proposal': copy(value)})
        return value

    def filtered_fallback(**kw):
        return modules['marked_adapter'].open_fallback(language=kw['language'],
            semantics=point, state=kw['state'], row=kw['row'],
            base_fallback=modules['fallback'].open_fallback, tick=kw['tick'])

    def certify_fallback(**kw):
        return modules['family_engine'].certify_by_current_cover(**kw,
            degree_proposer=degree_proposer, semantics=routed)

    def family_proposer(*, state, decision, tick):
        # Called only by the real engine after its completed global BRANCH.
        nonlocal provider_started
        first_call = not provider_started
        if first_call:
            phase('BEFORE_PROVIDER')
            provider_started = True
        supplied = {'state': copy(state), 'decision': copy(decision)}
        value = modules['receiver_provider'].build_family_batch(
            language=language, base_semantics=base_semantics, marked_semantics=point,
            producer=modules['producer'], expansion_checker=modules['expansion_checker'],
            host_adapter=modules['host_adapter'], membership_module=modules['membership'],
            residual_policy=modules['residual_policy'], mined=copy(mined),
            state=copy(state), decision=copy(decision), matching_mode=matching_mode,
            limits=dict(PROVIDER_LIMITS), tick=tick)
        value = copy(value)
        if first_call:
            phase('AFTER_PROVIDER')
        # The engine retains the complete report in its literal check envelope.
        # This observation joins to that data without serializing it twice.
        require(type(value) is dict and set(value) == {'batch', 'report'}
                and canonical(value['batch']) == canonical(value['report']['batch']),
                'literal complete provider envelope')
        observations['provider_calls'].append(dict(supplied, report_sha256=digest(value['report'])))
        return value

    def family_consumer(*, state, decision, request, tick):
        value = modules['family_consumer'].consume_preferences(language=language,
            base_semantics=base_semantics, marked_semantics=point,
            producer=modules['producer'], expansion_checker=modules['expansion_checker'],
            host_adapter=modules['host_adapter'], state=state, decision=decision,
            request=request, tick=tick)
        observations['consumer_calls'].append({'state_sha256': digest(state),
            'decision': copy(decision), 'request_sha256': digest(request),
            'receipt_sha256': digest(value), 'status': value['status']})
        return value

    phase('BEFORE_ENGINE')
    engine = modules['family_engine'].LazyUnitRowEngine(language=language,
        degree_proposer=degree_proposer, semantics=routed,
        fallback=filtered_fallback, certify_fallback=certify_fallback,
        transition_checker=router.RoutedMarkedTransition(), tick=tick,
        initial_state=copy(initial), maximum_nodes=MAXIMUM_NODES,
        maximum_events=MAXIMUM_EVENTS, branch_tie=BRANCH_TIE,
        family_proposer=family_proposer, family_consumer=family_consumer,
        initial_prototype_census=copy(frozen_inventory['census']))
    before = engine.state_snapshot()
    result = engine.search()
    after = engine.state_snapshot()
    require(canonical(before) == canonical(after) and result['root_restored'] is True
            and result['stack_restored'] is True, 'exact engine-owned root restoration')
    require(canonical(frozen_inventory) == origin and digest(mined) == pool_identity,
            'same frozen pool before and after receiver exposure')
    phase('AFTER_ENGINE')
    return {'schema': RESULT_SCHEMA, 'version': VERSION,
        'status': 'RECEIVER_PROBE_RECORDED', 'matching_mode': matching_mode,
        'pool_policy': POOL_POLICY, 'frozen_open_pool_sha256': pool_identity,
        'inventory_reused': True, 'inventory_construction_charged_in_this_window': False,
        'source_pool_component_id': pool['component_id'],
        'source_pool_families': [x['family_id'] for x in mined['families']],
        'initial_state': initial, 'branch_tie': BRANCH_TIE,
        'maximum_nodes': MAXIMUM_NODES, 'maximum_events': MAXIMUM_EVENTS,
        'provider_limits': dict(PROVIDER_LIMITS),
        'engine_result': result, 'observations': observations,
        'root_restored': True, 'logical_proof_accepted': False,
        'useful_transfer_accepted': False, 'whole_engine_qualified': False,
        'complete_GCTS_model_accepted': False, 'RL_accepted': False,
        'GCTS_advantage_claimed': False, 'ROOT_resource_accepted': False}
