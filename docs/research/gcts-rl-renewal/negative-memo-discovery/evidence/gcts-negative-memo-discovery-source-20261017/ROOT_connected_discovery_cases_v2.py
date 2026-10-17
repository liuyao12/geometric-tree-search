"""Prospective connected-prefix discovery; Root measured once only.

No project import, target route, supplied witness, known family or learned
policy. The stopping rule observes selected read incidence, not formula names.
An interrupted query has NOT established viable frontier or a completed proof.
"""
import copy
import hashlib
import json

VERSION = 'ROOT-first-connected-selected-prefix-discovery-v2-exact-negative-memo'
CASE = 'CD-01-first-actual-selected-inference-edge'


class StructuralInspectionUnresolved(TimeoutError):
    pass


def require(ok, reason):
    if not ok:
        raise ValueError('Root connected discovery: '+reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


MEMO_MAXIMUM_NODES = 20000
MEMO_MAXIMUM_DEPTH = 128


class _MemoIncomplete(Exception):
    pass


def _memo_step(tick, budget, depth):
    tick()
    budget[0] += 1
    if budget[0] > MEMO_MAXIMUM_NODES or depth > MEMO_MAXIMUM_DEPTH:
        raise _MemoIncomplete()


def _memo_copy(value, tick, budget, depth=0):
    _memo_step(tick, budget, depth)
    kind = type(value)
    if value is None or kind in (bool, int, str):
        return value
    if kind is list:
        return [_memo_copy(item, tick, budget, depth+1) for item in value]
    if kind is tuple:
        return tuple(_memo_copy(item, tick, budget, depth+1) for item in value)
    if kind is dict:
        if any(type(key) is not str for key in value):
            raise _MemoIncomplete()
        return {key: _memo_copy(item, tick, budget, depth+1) for key, item in value.items()}
    raise _MemoIncomplete()


def _memo_equal(left, right, tick, budget, depth=0):
    _memo_step(tick, budget, depth)
    kind = type(left)
    if kind is not type(right):
        return False
    if left is None:
        return True
    if kind in (bool, int, str):
        return left == right
    if kind is list or kind is tuple:
        if len(left) != len(right):
            return False
        return all(_memo_equal(x, y, tick, budget, depth+1) for x, y in zip(left, right))
    if kind is dict:
        if len(left) != len(right):
            return False
        if any(type(key) is not str for key in left) or any(type(key) is not str for key in right):
            raise _MemoIncomplete()
        return all(key in right and _memo_equal(value, right[key], tick, budget, depth+1)
                   for key, value in left.items())
    raise _MemoIncomplete()


def run_discovery(*, language, marked_semantics, engine_module, router_module,
                  legacy_proposer, marked_aware_proposer, marked_aware_checker,
                  fallback_module, point_module, trace_helper, state,
                  latest_observations, phase, tick):
    tick()
    initial_literal = canonical(state)
    require(state['selected'] == [] and state['excluded'] == [],
            'exact fresh native root, no supplied proof cells or exclusions')
    require(set(latest_observations) == {'proposer','fallback','completion','validator'}
            and all(value is None for value in latest_observations.values()),
            'fixed initially empty external diagnostic scalar slots')
    captures = []
    result = {'schema':'ROOT-connected-prefix-discovery-evidence-v1', 'version':VERSION,
        'case':CASE, 'status':'UNKNOWN', 'reason':None, 'initial_state':copy.deepcopy(state),
        'captures':captures, 'search':None, 'root_before':None, 'root_after':None,
        'trace_join':None, 'target_model_search_started':False,
        'named_branch_tie':'ASSIGNED-OUTPUT-THEN-ROW',
        'capture_rule':'first public callback state with any selected-to-selected ordered read',
        'human_proof_route_supplied':False, 'human_family_or_substitution_supplied':False,
        'current_frontier_viability_checked':False, 'collector_or_family_pipeline_executed':False,
        'new_theorem_discovered':False, 'proof_accepted':False, 'engine_activated':False,
        'family_library_activated':False, 'degree_or_EOF_accepted':False,
        'whole_engine_qualified':False, 'complete_GCTS_model_accepted':False,
        'RL_accepted':False, 'GCTS_advantage_claimed':False, 'ROOT_resource_accepted':False}
    routed = router_module.RoutedMarkedSemantics(point_semantics=marked_semantics,
        legacy_proposer=legacy_proposer, marked_aware_proposer=marked_aware_proposer,
        marked_aware_checker=marked_aware_checker, tick=tick)

    # One private completed-negative data snapshot, never a helper receipt.
    # Root's pinned native tick and whole Source pre/post guard remain required.
    memo_entry = None
    memo_counts = {'lookups':0,'hits':0,'misses':0,'full_inspections':0}
    inspector = trace_helper.inspect_selected_edges
    require(type(inspector) is type(run_discovery) and type(tick) is type(run_discovery),
            'pinned Python helper and Root native tick functions')
    inspector_code,inspector_globals = inspector.__code__,inspector.__globals__
    inspector_defaults,inspector_kwdefaults = inspector.__defaults__,inspector.__kwdefaults__
    inspector_closure,inspector_version = inspector.__closure__,trace_helper.VERSION
    inspector_limits = trace_helper.DEFAULT_LIMITS
    native_tick = tick
    native_code,native_globals = tick.__code__,tick.__globals__
    native_defaults,native_kwdefaults,native_closure = tick.__defaults__,tick.__kwdefaults__,tick.__closure__

    def memo_guard():
        require(trace_helper.inspect_selected_edges is inspector
                and inspector.__code__ is inspector_code and inspector.__globals__ is inspector_globals
                and inspector_globals is trace_helper.__dict__
                and inspector.__defaults__ is inspector_defaults
                and inspector.__kwdefaults__ is inspector_kwdefaults
                and type(inspector_kwdefaults) is dict and set(inspector_kwdefaults) == {'limits'}
                and inspector_kwdefaults['limits'] is None and inspector.__closure__ is inspector_closure
                and type(trace_helper.VERSION) is str and trace_helper.VERSION == inspector_version
                and trace_helper.DEFAULT_LIMITS is inspector_limits
                and tick is native_tick and tick.__code__ is native_code and tick.__globals__ is native_globals
                and tick.__defaults__ is native_defaults and tick.__kwdefaults__ is native_kwdefaults
                and tick.__closure__ is native_closure,
                'same Source-bound observer/default configuration and original Root native authority')

    def observe(role, kwargs):
        nonlocal memo_entry
        native_ns = tick()
        current, row = kwargs['state'], kwargs['row']
        latest_observations[role] = (role.upper()+'_NATIVE_STEP',row,len(current['selected']),native_ns)
        memo_guard()
        memo_counts['lookups'] += 1
        context = {'state':current,'helper_limits':trace_helper.DEFAULT_LIMITS,
                   'original_binding':language.binding}
        hit = False
        if memo_entry is not None:
            try:
                hit = _memo_equal(memo_entry,context,tick,[0])
            except _MemoIncomplete:
                pass
        if hit:
            memo_counts['hits'] += 1
            return  # No fabricated observation/work report; original delegate follows.
        memo_counts['misses'] += 1
        memo_counts['full_inspections'] += 1
        memo_entry = None  # Clear old ownership before helper work or replacement copy.
        observation = trace_helper.inspect_selected_edges(state=current,tick=tick)
        require(observation['status'] in ('CONNECTED_PREFIX_CANDIDATE','NO_CONNECTED_EDGE','UNKNOWN'),
                'complete structural observation or own allowance UNKNOWN')
        if observation['status'] == 'NO_CONNECTED_EDGE':
            memo_guard()
            try:
                memo_entry = _memo_copy(context,tick,[0])
            except _MemoIncomplete:
                pass  # Complete negative remains usable now, but no memo is installed.
        if observation['status'] == 'UNKNOWN':
            raise StructuralInspectionUnresolved('connected-edge inspection allowance UNKNOWN; no firstness or absence claim')
        if observation['status'] == 'CONNECTED_PREFIX_CANDIDATE':
            require(captures == [], 'one first connected capture only')
            capture = {'schema':'receptor-family-connected-prefix-capture-v1',
                'capture_id':'first-connected-public-callback', 'callback_kind':role.upper(),
                'query_row':row, 'native_ns':native_ns, 'state':copy.deepcopy(current),
                'edge_report':observation}
            tick()
            captures.append(capture)
            phase('CAPTURED_CONNECTED')
            raise trace_helper.ConnectedPrefixCaptured(trace_helper.CAPTURE_REASON)

    def proposer(**kwargs):
        observe('proposer',kwargs)
        return routed.propose_degree(**kwargs)

    def fallback(**kwargs):
        observe('fallback',kwargs)
        return point_module.open_fallback(language=kwargs['language'],semantics=marked_semantics,
            state=kwargs['state'],row=kwargs['row'],base_fallback=fallback_module.open_fallback,
            tick=kwargs['tick'])

    def certify(**kwargs):
        observe('completion',kwargs)
        return engine_module.certify_by_current_cover(**kwargs,
            degree_proposer=proposer,semantics=routed)

    phase('BEFORE_ENGINE')
    engine = engine_module.LazyUnitRowEngine(language=language,
        degree_proposer=proposer,semantics=routed,fallback=fallback,
        certify_fallback=certify,transition_checker=router_module.RoutedMarkedTransition(),
        tick=tick,initial_state=copy.deepcopy(state),maximum_nodes=128,maximum_events=2000,
        branch_tie='ASSIGNED-OUTPUT-THEN-ROW')
    result['root_before'] = engine.state_snapshot()
    result['target_model_search_started'] = True
    phase('BEFORE_SEARCH')
    searched = engine.search()
    phase('AFTER_SEARCH')
    result['search'] = searched
    result['root_after'] = engine.state_snapshot()
    require(canonical(result['root_before']) == canonical(result['root_after'])
            and searched['root_restored'] is searched['stack_restored'] is True,
            'whole native search root, cursor and dependency restoration')
    if captures:
        require(len(captures)==1 and searched['status']=='UNKNOWN'
                and searched['reason']==trace_helper.CAPTURE_REASON and searched['found']is None,
                'exact intentional connected-prefix interruption')
        joined = trace_helper.join_active_search_trace(capture=captures[0],search_result=searched,
            root_before=result['root_before'],root_after=result['root_after'],tick=tick)
        result['trace_join'] = joined
        if joined['status']=='JOINED_ACTIVE_PREFIX':
            result['status']='CAPTURED_CONNECTED_PARTIAL_STATE'
            result['reason']='actual connected selected prefix; current global query interrupted, viability and proof unaccepted'
        else:
            require(joined['status']=='UNKNOWN','literal trace join status')
            result['reason']='trace-join finite allowance UNKNOWN; no provenance acceptance'
    else:
        result['reason']='no connected selected prefix captured; search reason: '+str(searched['reason'])
    phase('AFTER_TRACE_JOIN')
    require(canonical(state)==initial_literal,'entire supplied native root unchanged')
    result['structural_memo'] = dict(memo_counts)
    tick()
    return result
