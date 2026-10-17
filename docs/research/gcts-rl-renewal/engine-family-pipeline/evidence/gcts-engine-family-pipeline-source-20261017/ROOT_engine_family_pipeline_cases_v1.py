"""Prospective Root experiment; execute only within the reviewed native once.

The first ordinary selected child is the data source. No supplied proof route,
formula, primitive witness, family, row assignment or learned policy is used.
This deliberately small experiment establishes only a checked proposal path.
"""
import copy
import hashlib
import json

VERSION = 'ROOT-engine-selected-cell-family-pipeline-v1'
CASE = 'EP-01-first-ordinary-cell-to-fresh-branch-family-preference'
INTERRUPTION = 'declared native-first first-selected-child capture'


class DeclaredPrefixCapture(TimeoutError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def require(ok, why):
    if not ok:
        raise ValueError('Root engine-family pipeline: ' + why)


def run_pipeline(*, language, base_semantics, marked_semantics,
                 engine_module, router_module, legacy_proposer,
                 marked_aware_proposer, marked_aware_checker, fallback_module,
                 point_module, collector, miner, provider, consumer,
                 producer, expansion_checker, host_adapter, state, tick):
    tick()
    offered_state = canonical(state)
    log = {'queries': [], 'captures': []}
    result = {'schema': 'ROOT-engine-family-pipeline-evidence-v1', 'version': VERSION,
              'case': CASE, 'status': 'UNKNOWN', 'reason': None,
              'initial_state': copy.deepcopy(state), 'search': None,
              'search_log': log, 'root_before': None, 'root_after': None,
              'capture_trace_join': None, 'collection': None, 'mining': None,
              'fresh_branch': None, 'family_provider': None, 'consumption': None,
              'scope': 'one actual primitive cell, literal-family prefix, fresh branch proposal only',
              'human_proof_route_supplied': False,
              'human_family_or_substitution_supplied': False,
              'target_model_search_started': False, 'new_theorem_discovered': False,
              'proof_accepted': False, 'engine_activated': False,
              'family_library_activated': False, 'degree_or_EOF_accepted': False,
              'whole_engine_qualified': False, 'complete_GCTS_model_accepted': False,
              'RL_accepted': False, 'GCTS_advantage_claimed': False,
              'ROOT_resource_accepted': False}

    def finish(reason):
        tick()
        require(canonical(state) == offered_state, 'original supplied root state unchanged')
        result['reason'] = reason
        return result

    def make_engine(initial_state, capture):
        routed = router_module.RoutedMarkedSemantics(point_semantics=marked_semantics,
            legacy_proposer=legacy_proposer, marked_aware_proposer=marked_aware_proposer,
            marked_aware_checker=marked_aware_checker, tick=tick)

        def proposer(**kwargs):
            native_ns = tick()
            if capture and len(kwargs['state']['selected']) > len(initial_state['selected']):
                require(not log['captures'], 'one declared first-child capture only')
                log['captures'].append({'kind': INTERRUPTION, 'native_ns': native_ns,
                    'row': kwargs['row'], 'state': copy.deepcopy(kwargs['state']),
                    'state_sha256': digest(kwargs['state'])})
                raise DeclaredPrefixCapture(INTERRUPTION)
            value = routed.propose_degree(**kwargs)
            log['queries'].append({'capture_engine': capture, 'row': kwargs['row'],
                'state': copy.deepcopy(kwargs['state']), 'proposal': copy.deepcopy(value)})
            return value

        def fallback(**kwargs):
            return point_module.open_fallback(language=kwargs['language'],
                semantics=marked_semantics, state=kwargs['state'], row=kwargs['row'],
                base_fallback=fallback_module.open_fallback, tick=kwargs['tick'])

        def certify(**kwargs):
            return engine_module.certify_by_current_cover(**kwargs,
                degree_proposer=proposer, semantics=routed)

        return engine_module.LazyUnitRowEngine(language=language,
            degree_proposer=proposer, semantics=routed, fallback=fallback,
            certify_fallback=certify,
            transition_checker=router_module.RoutedMarkedTransition(), tick=tick,
            initial_state=copy.deepcopy(initial_state), maximum_nodes=128,
            maximum_events=2000, branch_tie='ROW')

    require(state['selected'] == [] and state['excluded'] == [],
            'empty native selected root and exclusions; no supplied proof cells or route')
    first = make_engine(state, True)
    result['root_before'] = first.state_snapshot()
    result['target_model_search_started'] = True
    searched = first.search()
    result['search'] = searched
    result['root_after'] = first.state_snapshot()
    require(canonical(result['root_before']) == canonical(result['root_after'])
            and searched['root_restored'] is searched['stack_restored'] is True,
            'actual search restores full root domain/cursor/point state')
    if not log['captures']:
        return finish('NO_FIRST_SELECTED_CHILD_CAPTURED; search outcome retained without substitution')
    require(len(log['captures']) == 1 and searched['status'] == 'UNKNOWN'
            and searched['reason'] == INTERRUPTION and searched['found'] is None,
            'exact declared interruption, never natural search exhaustion or a proof')
    capture = log['captures'][0]
    captured = copy.deepcopy(capture['state'])
    require(canonical(captured) == canonical(searched['last_observed_state'])
            and len(captured['selected']) == 1, 'capture equals actual returned child state')
    placements = [event for event in searched['events'] if event['kind'] == 'PLACE']
    tries = [event for event in searched['events'] if event['kind'] == 'TRY']
    decisions = [event for event in searched['events'] if event['kind'] == 'DECISION']
    require(len(placements) == len(tries) == 1 and decisions
            and decisions[0]['decision']['kind'] in ('BRANCH', 'FORCED')
            and placements[0]['row'] == tries[0]['row'] == decisions[0]['decision']['row']
            and canonical(placements[0]['key']) == canonical(tries[0]['key'])
            and not any(event['kind'] == 'EXCLUDE' for event in searched['events']),
            'one actual native placement and global decision, no unjustified exclusion')
    selected_key = {k: value for k, value in captured['selected'][0].items() if k != 'generation'}
    require(canonical(selected_key) == canonical(placements[0]['key']),
            'complete selected key equals actual PLACE key')
    result['capture_trace_join'] = {'capture_state_sha256': digest(captured),
        'search_state_sha256': digest(searched['last_observed_state']),
        'placement_event': copy.deepcopy(placements[0]), 'try_event': copy.deepcopy(tries[0]),
        'decision_event': copy.deepcopy(decisions[0]), 'full_selected_key': selected_key,
        'native_first_capture': True, 'root_and_stack_restored': True,
        'engine_generated_cell_joined': True, 'root_proof_accepted': False}
    collected = collector.collect_derivation(language=language,
        base_semantics=base_semantics, marked_semantics=marked_semantics,
        host_adapter=host_adapter, state=captured,
        origin={'schema': 'ROOT-current-actual-public-state-capture-v1',
                'trace_join': copy.deepcopy(result['capture_trace_join'])}, tick=tick)
    result['collection'] = collected
    if collected['status'] == 'UNKNOWN':
        return finish('COLLECTOR_FINITE_ALLOWANCE_UNKNOWN')
    require(collected['status'] == 'COLLECTED_CONDITIONAL_DAG'
            and len(collected['derivation']['nodes']) == 1
            and collected['checks']['every_selected_native_member_checked'] is True,
            'fresh checked one-cell DAG reconstructed from actual state')
    mined = miner.mine_families(host=collected['host'],
        derivation=collected['derivation'], tick=tick,
        limits={'cuts': 1, 'members': 1, 'families': 1})
    result['mining'] = mined
    if mined['status'] == 'UNKNOWN':
        return finish('NO_FAMILY_IN_DECLARED_LITERAL_ONE_CELL_PREFIX')
    require(mined['status'] == 'PROPOSALS' and len(mined['families']) == 1,
            'one automatic literal family; no supplied family or selected theorem')
    fresh = make_engine(captured, False)
    fresh_before = fresh.state_snapshot()
    decision = fresh.decision()
    fresh_after = fresh.state_snapshot()
    result['fresh_branch'] = {'before': fresh_before, 'decision': copy.deepcopy(decision),
        'after': fresh_after, 'events': copy.deepcopy(fresh.events), 'counts': dict(fresh.counts)}
    require(canonical(fresh_before['state']) == canonical(captured)
            and canonical(fresh_after['state']) == canonical(captured),
            'fresh global query preserves entire actual captured point state')
    if decision['kind'] != 'BRANCH':
        return finish('FRESH_GLOBAL_DECISION_NOT_BRANCH; no provider or consumer call')
    provided = provider.build_family_batch(language=language, base_semantics=base_semantics,
        marked_semantics=marked_semantics, producer=producer,
        expansion_checker=expansion_checker, host_adapter=host_adapter,
        mined=mined, state=captured, decision=decision, tick=tick)
    result['family_provider'] = provided
    request = {'schema': consumer.REQUEST_SCHEMA, 'mode': 'BATCH', 'payload': provided['batch']}
    consumed = consumer.consume_preferences(language=language, base_semantics=base_semantics,
        marked_semantics=marked_semantics, producer=producer,
        expansion_checker=expansion_checker, host_adapter=host_adapter,
        state=captured, decision=decision, request=request, tick=tick)
    result['consumption'] = consumed
    require(canonical(fresh.state_snapshot()['state']) == canonical(captured),
            'provider and consumer never install a hypothetical cluster')
    if consumed['status'] != 'READY':
        return finish('NO_READY_FAMILY_PREFERENCE; finite matching failure is not proof failure')
    preferred = consumed['selection']['candidate']
    require(preferred['placement_key']['translation'] == [0, decision['row']]
            and canonical(preferred['placement_key']) != canonical(selected_key),
            'fresh branch preference has a different actual physical full placement key')
    require(consumed['logical_proof_accepted'] is consumed['degree_or_EOF_accepted']
            is consumed['scheduler_accepted'] is consumed['RL_accepted'] is False,
            'checked preference has no stronger authority')
    result['status'] = 'CHECKED_FRESH_BRANCH_PREFERENCE'
    return finish('AUTOMATIC_CELL_TO_LITERAL_FAMILY_TO_FRESH_PHYSICAL_PREFERENCE; NOT_A_NEW_THEOREM')
