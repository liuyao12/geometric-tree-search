"""Bounded structural observation of a public native search callback state.

This module performs no native membership, point-union, degree, proof or search
check.  Its inputs are untrusted builtin data.  The later collector must freshly
reconstruct the captured state; the current global query was interrupted before
its viability was known.  Root authenticates the actual caller and clock.
"""
import hashlib
import json

VERSION = 'receptor-family-connected-prefix-observer-v2-native-ID-prefixes'
ENGINE_VERSION = 'lazy-unit-row-global-engine-v13-decision-local-checked-state'
CAPTURE_REASON = 'declared native-first connected selected-prefix capture'
DEFAULT_LIMITS = {'maximum_work': 2000000, 'maximum_depth': 128,
                  'maximum_events': 20000}
STATE_FIELDS = {'schema', 'input_epoch', 'height', 't', 'm', 'selected',
                'excluded', 'generation', 'marking_id'}
KEY_FIELDS = {'tile_type_id', 'type_preimage', 'translation'}


class ConnectedPrefixCaptured(TimeoutError):
    """The caller raises this only after saving a complete connected capture."""


class _Limit(Exception):
    pass


def _require(condition, reason):
    if not condition:
        raise ValueError('connected prefix observer: ' + reason)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode('utf8')).hexdigest()


class _Work:
    def __init__(self, tick, limits):
        _require(callable(tick), 'native tick callback')
        self.tick, self.steps = tick, 0
        self.limits = dict(DEFAULT_LIMITS)
        if limits is not None:
            _require(type(limits) is dict and set(limits) <= set(DEFAULT_LIMITS),
                     'declared finite limit names')
            for key, value in limits.items():
                _require(type(value) is int and 1 <= value <= DEFAULT_LIMITS[key],
                         'positive finite limit within the declared ceiling')
                self.limits[key] = value

    def step(self):
        self.tick()
        self.steps += 1
        if self.steps > self.limits['maximum_work']:
            raise _Limit('structural work ceiling; no partial join accepted')

    def tree(self, value, depth=0):
        """Validate and copy only builtin JSON data; never invoke object hooks."""
        self.step()
        if depth > self.limits['maximum_depth']:
            raise _Limit('structural depth ceiling; no partial join accepted')
        if value is None or type(value) in (bool, int, str):
            return value
        if type(value) is list:
            return [self.tree(item, depth + 1) for item in value]
        if type(value) is dict:
            _require(all(type(key) is str for key in value), 'literal string object keys')
            return {key: self.tree(item, depth + 1) for key, item in value.items()}
        raise ValueError('connected prefix observer: builtin JSON data only')

    def record(self):
        return {'steps': self.steps, 'limits': dict(self.limits),
                'mathematical_work_or_proof_cost': False}


def _scope():
    return {'structural_observation_only': True, 'unqualified_for_viability': True,
            'global_query_interrupted_before_complete_decision': True,
            'later_bridge_requires_fresh_full_global_decision': True,
            'fact_accepted': False, 'native_membership_checked': False,
            'point_union_checked': False, 'root_proof_accepted': False,
            'logical_proof_accepted': False, 'trajectory_accepted': False,
            'engine_qualification_accepted': False, 'GCTS_advantage_accepted': False,
            'RL_accepted': False, 'ROOT_resource_accepted': False}


def _hex(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _key(value, state, work, selected=False):
    expected = KEY_FIELDS | ({'generation'} if selected else set())
    _require(type(value) is dict and set(value) == expected, 'complete literal decorated key fields')
    if selected:
        _require(type(value['generation']) is int and value['generation'] == 1,
                 'original selected generation')
    _require(type(value['tile_type_id']) is str
             and value['tile_type_id'].startswith('row0-decorated-tile-')
             and _hex(value['tile_type_id'][len('row0-decorated-tile-'):]),
             'literal native prefixed decorated type ID')
    translation = value['translation']
    _require(type(translation) is list and len(translation) == 2
             and type(translation[0]) is int and translation[0] == 0
             and type(translation[1]) is int and 0 <= translation[1] < 24,
             'literal original row translation')
    pre = value['type_preimage']
    _require(type(pre) is dict and set(pre) == {'schema', 'base_type_preimage', 'marking_id'}
             and pre['schema'] == 'unit-row-row0-decorated-type-v1'
             and pre['marking_id'] == state['marking_id'], 'full decorated model identity')
    base = pre['base_type_preimage']
    _require(type(base) is dict and set(base) == {'input_epoch', 'primitive_witness',
             'ordered_premise_formulas', 'ordered_offsets'}
             and base['input_epoch'] == state['input_epoch'], 'original base preimage and epoch')
    witness = base['primitive_witness']
    _require(type(witness) is dict and type(witness.get('rule')) is str
             and type(witness.get('formula')) is list, 'preserved native witness syntax')
    premises, offsets = base['ordered_premise_formulas'], base['ordered_offsets']
    _require(type(premises) is list and type(offsets) is list
             and len(premises) == len(offsets), 'complete ordered read arrays')
    for premise, offset in zip(premises, offsets):
        work.step()
        _require(type(premise) is list and type(offset) is int
                 and 0 <= translation[1] + offset < translation[1],
                 'each ordered read is structurally strict prior')
    return {key: work.tree(value[key]) for key in ('tile_type_id', 'type_preimage', 'translation')}


def _state(value, work):
    state = work.tree(value)
    _require(type(state) is dict and set(state) == STATE_FIELDS
             and state['schema'] == 'unit-row-channel4-private-state-v1'
             and type(state['height']) is int and state['height'] == 24
             and _hex(state['input_epoch'])
             and type(state['marking_id']) is str
             and state['marking_id'].startswith('row0-marking-')
             and _hex(state['marking_id'][len('row0-marking-'):]),
             'full original-height marked state shape')
    _require(all(type(state[key]) is list for key in ('t', 'm', 'selected', 'excluded', 'generation')),
             'full point, selected, exclusion and generation arrays')
    _require(len(state['selected']) <= 24, 'at most one selected output per original row')
    return state


def _inspect(state, work):
    state = _state(state, work)
    nodes, by_row = [], {}
    for selected_index, record in enumerate(state['selected']):
        work.step()
        key = _key(record, state, work, True)
        row = key['translation'][1]
        _require(row not in by_row, 'unique selected output rows')
        by_row[row] = len(nodes)
        nodes.append({'selected_index': selected_index, 'row': row,
                      'selection_record': record, 'placement_key': key})
    edges = []
    for consumer_index in sorted(range(len(nodes)), key=lambda index: nodes[index]['row']):
        work.step()
        node = nodes[consumer_index]
        base = node['placement_key']['type_preimage']['base_type_preimage']
        for premise_index, (premise, offset) in enumerate(zip(
                base['ordered_premise_formulas'], base['ordered_offsets'])):
            work.step()
            source_row = node['row'] + offset
            if source_row in by_row:
                edges.append({'consumer_node_index': consumer_index,
                    'source_node_index': by_row[source_row], 'premise_index': premise_index,
                    'offset': offset, 'consumer_row': node['row'], 'source_row': source_row,
                    'premise_formula': work.tree(premise)})
    connected = len(nodes) >= 2 and bool(edges)
    return {'schema': 'receptor-family-connected-edge-observation-v1', 'version': VERSION,
            'status': 'CONNECTED_PREFIX_CANDIDATE' if connected else 'NO_CONNECTED_EDGE',
            'reason': None if connected else 'no selected-to-selected strict-prior ordered read observed',
            'state_sha256': _digest(state), 'input_epoch': state['input_epoch'],
            'marking_id': state['marking_id'], 'selected_count': len(nodes),
            'selected_rows': sorted(by_row), 'nodes': nodes, 'edges': edges,
            'work': work.record(), 'scope': _scope()}


def inspect_selected_edges(*, state, tick, limits=None):
    """No rule/formula/goal filter; an edge is structural, never a premise fact."""
    work = _Work(tick, limits)
    try:
        return _inspect(state, work)
    except _Limit as error:
        return {'schema': 'receptor-family-connected-edge-observation-v1', 'version': VERSION,
            'status': 'UNKNOWN', 'reason': str(error), 'state_sha256': None,
            'input_epoch': None, 'marking_id': None, 'selected_count': None,
            'selected_rows': [], 'nodes': [], 'edges': [], 'work': work.record(), 'scope': _scope()}


def _same(left, right, reason):
    _require(_canonical(left) == _canonical(right), reason)


def _join(capture, search, before, after, work):
    _require(type(capture) is dict and set(capture) == {'schema', 'capture_id', 'callback_kind',
             'query_row', 'native_ns', 'state', 'edge_report'}
             and capture['schema'] == 'receptor-family-connected-prefix-capture-v1',
             'exact complete capture fields')
    _require(type(capture['capture_id']) is str and 0 < len(capture['capture_id']) <= 128
             and type(capture['callback_kind']) is str
             and capture['callback_kind'] in ('PROPOSER', 'FALLBACK', 'COMPLETION')
             and type(capture['query_row']) is int and 0 <= capture['query_row'] < 24
             and type(capture['native_ns']) is int and 0 <= capture['native_ns'] < 2**63,
             'literal public callback observation metadata')
    observed = _inspect(capture['state'], work)
    _require(observed['status'] == 'CONNECTED_PREFIX_CANDIDATE', 'complete structural edge eligibility')
    report = work.tree(capture['edge_report'])
    _require(type(report) is dict and set(report) == set(observed), 'complete offered edge observation')
    _same({key: value for key, value in report.items() if key != 'work'},
          {key: value for key, value in observed.items() if key != 'work'}, 'fresh structural edge report join')
    state = capture['state']
    _require(type(before) is dict and type(after) is dict, 'full public root snapshots')
    # Whole builtin snapshots are kept by the caller.  Their full literal join,
    # not just a selected-key projection, is required here.
    before, after = work.tree(before), work.tree(after)
    _same(before, after, 'full root point/cursor/dependency/policy restoration')
    root = _state(before.get('state'), work)
    _require(root['selected'] == [] and root['excluded'] == [],
             'declared fresh empty selected/excluded discovery root')
    _require(root['input_epoch'] == state['input_epoch'] and root['marking_id'] == state['marking_id'],
             'captured state retains original epoch and frozen marking')
    _require(type(search) is dict and search.get('schema') == 'unit-row-channel4-routed-lazy-global-search-result-v1'
             and search.get('version') == ENGINE_VERSION and search.get('status') == 'UNKNOWN'
             and search.get('reason') == CAPTURE_REASON and search.get('found') is None
             and search.get('root_restored') is True and search.get('stack_restored') is True
             and search.get('trace_complete') is False and search.get('branch_advice_enabled') is False,
             'actual declared interrupted UNKNOWN, not proof or exhaustive trace')
    _require(before.get('version') == ENGINE_VERSION and after.get('version') == ENGINE_VERSION
             and search.get('input_epoch') == state['input_epoch']
             and search.get('marking_id') == state['marking_id'], 'current engine and original state identity')
    _same(work.tree(search.get('last_observed_state')), state, 'actual returned last state equals captured public state')
    root_digest = _digest(before)
    _require(search.get('root_snapshot_sha256') == search.get('final_snapshot_sha256') == root_digest,
             'both full snapshot digest joins')
    for flag in ('logical_proof_accepted', 'exact_point_board_accepted',
                 'complete_candidate_graph_accepted', 'trajectory_accepted',
                 'GCTS_advantage_accepted', 'RL_accepted', 'ROOT_resource_accepted'):
        _require(search.get(flag) is False, 'all broad search authority flags remain false')
    policy = before.get('scheduler_policy')
    _require(type(policy) is dict and policy.get('branch_tie') == 'ASSIGNED-OUTPUT-THEN-ROW',
             'existing declared assigned-output tie, no new scheduling policy')
    _same(work.tree(search.get('scheduler_policy')), policy, 'search and root full scheduler policy')
    events = search.get('events')
    _require(type(events) is list and bool(events), 'full recorded public event prefix')
    if len(events) > work.limits['maximum_events']:
        raise _Limit('public event ceiling; no partial active-path join accepted')
    stack, excluded, prior_exclusions = [], [], []
    last_decision, awaiting_exclusion = None, None
    for event_index, raw in enumerate(events):
        work.step()
        _require(type(raw) is dict and type(raw.get('event')) is int
                 and raw['event'] == event_index and type(raw.get('kind')) is str
                 and _hex(raw.get('state_sha256')), 'contiguous full public event identity')
        kind = raw['kind']
        _require(kind in ('DECISION', 'TRY', 'PLACE', 'RESTORE', 'EXCLUDE', 'INVALIDATE', 'FALLBACK', 'ADVICE'),
                 'known current public event kind')
        if kind == 'DECISION':
            _require(awaiting_exclusion is None, 'exhausted branch excluded before next global query')
            decision = raw.get('decision')
            _require(type(decision) is dict and type(decision.get('kind')) is str and decision.get('kind') in
                     ('DEAD', 'UNKNOWN', 'FORCED', 'BRANCH', 'SOLVED'), 'literal global decision')
            last_decision = {'event': event_index, 'decision': decision,
                             'state_sha256': raw['state_sha256'], 'used': False}
        elif kind == 'TRY':
            _require(awaiting_exclusion is None and last_decision is not None
                     and not last_decision['used'], 'TRY follows an unused actual global decision')
            decision = last_decision['decision']
            _require(type(raw.get('depth')) is int and raw['depth'] == len(stack)
                     and raw.get('mode') in ('FORCED', 'BRANCH')
                     and decision.get('kind') == raw['mode']
                     and type(raw.get('row')) is int and type(decision.get('row')) is int
                     and raw['row'] == decision['row']
                     and raw['state_sha256'] == last_decision['state_sha256'],
                     'TRY depth/row/mode/full parent state follows actual decision')
            key = _key(work.tree(raw.get('key')), state, work)
            _require(key['translation'][1] == raw['row'], 'TRY full key output row')
            if raw['mode'] == 'FORCED':
                _require(type(decision.get('candidate')) is dict, 'actual forced packet')
                _same(work.tree(decision['candidate'].get('placement_key')), key,
                      'forced TRY consumes exact actual sole key')
            stack.append({'depth': raw['depth'], 'row': raw['row'], 'placement_key': key,
                'try_event_index': event_index, 'place_event_index': None,
                'decision_event_index': last_decision['event'], 'mode': raw['mode'],
                'parent_state_sha256': raw['state_sha256'], 'excluded_snapshot': list(excluded)})
            last_decision['used'] = True
        elif kind == 'PLACE':
            _require(bool(stack) and stack[-1]['place_event_index'] is None
                     and type(raw.get('row')) is int and raw['row'] == stack[-1]['row'],
                     'PLACE completes the outstanding actual TRY')
            _same(work.tree(raw.get('key')), stack[-1]['placement_key'], 'PLACE full key equals TRY full key')
            stack[-1]['place_event_index'] = event_index
        elif kind == 'RESTORE':
            _require(bool(stack) and type(raw.get('depth')) is int
                     and raw['depth'] == len(stack) - 1 and type(raw.get('row')) is int
                     and raw['row'] == stack[-1]['row']
                     and stack[-1]['place_event_index'] is not None
                     and raw.get('child_status') in ('EXHAUSTED', 'UNKNOWN', 'POINT_BOARD_PROPOSAL')
                     and raw['state_sha256'] == stack[-1]['parent_state_sha256'],
                     'normal returned-child RESTORE joins the exact owned parent frame')
            frame = stack.pop()
            _same(work.tree(raw.get('key')), frame['placement_key'], 'RESTORE full key equals the exact TRY/PLACE')
            excluded = list(frame['excluded_snapshot'])
            awaiting_exclusion = frame if raw['child_status'] == 'EXHAUSTED' and frame['mode'] == 'BRANCH' else None
            last_decision = None
        elif kind == 'EXCLUDE':
            _require(awaiting_exclusion is not None and raw.get('reason') == 'CHILD_EXHAUSTED',
                     'only an actually exhausted returned branch authorizes this observed exclusion')
            excluded_key = work.tree(raw.get('key'))
            _same(excluded_key, awaiting_exclusion['placement_key'], 'EXCLUDE exact restored branch full key')
            _require(all(_canonical(key) != _canonical(excluded_key) for key in excluded),
                     'no duplicated active full-key exclusion')
            excluded.append(excluded_key)
            prior_exclusions.append(event_index)
            awaiting_exclusion = None
        elif kind == 'ADVICE':
            _require(False, 'discovery has branch_adviser=None; no advice event accepted')
    _require(awaiting_exclusion is None and bool(stack)
             and all(frame['place_event_index'] is not None for frame in stack),
             'capture inside fully placed active children, not an incomplete transaction')
    active = [frame['placement_key'] for frame in stack]
    _same(active, [node['placement_key'] for node in observed['nodes']],
          'all active full TRY/PLACE keys equal the captured selected array in insertion order')
    _same(excluded, state['excluded'], 'all and only current exclusions after nested checkpoint restoration')
    _require(events[-1]['state_sha256'] == observed['state_sha256'],
             'last recorded current public point state equals captured state')
    visible = [{key: frame[key] for key in ('depth', 'row', 'placement_key', 'try_event_index',
                'place_event_index', 'decision_event_index', 'mode')} for frame in stack]
    return {'schema': 'receptor-family-connected-active-trace-join-v1', 'version': VERSION,
            'status': 'JOINED_ACTIVE_PREFIX', 'reason': None, 'capture_id': capture['capture_id'],
            'callback_kind': capture['callback_kind'], 'query_row': capture['query_row'],
            'native_ns': capture['native_ns'], 'captured_state_sha256': observed['state_sha256'],
            'root_snapshot_sha256': root_digest, 'active_path': visible,
            'active_excluded_keys': excluded, 'edges': observed['edges'],
            'prior_exclusion_event_indices': prior_exclusions, 'trace_event_count': len(events),
            'work': work.record(), 'scope': _scope()}


def join_active_search_trace(*, capture, search_result, root_before, root_after, tick, limits=None):
    """Join returned data only; never replay search or infer a viable trajectory."""
    work = _Work(tick, limits)
    try:
        return _join(capture, search_result, root_before, root_after, work)
    except _Limit as error:
        return {'schema': 'receptor-family-connected-active-trace-join-v1', 'version': VERSION,
            'status': 'UNKNOWN', 'reason': str(error), 'capture_id': None,
            'callback_kind': None, 'query_row': None, 'native_ns': None,
            'captured_state_sha256': None, 'root_snapshot_sha256': None,
            'active_path': [], 'active_excluded_keys': [], 'edges': [],
            'prior_exclusion_event_indices': [], 'trace_event_count': None,
            'work': work.record(), 'scope': _scope()}
