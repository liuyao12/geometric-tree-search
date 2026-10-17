"""SOURCE ONLY: bounded native conditional two-member component proposals.

No engine, search, provider decision, target route, loader or clock exists here.
The caller authenticates original Source17/input2 and every injected Source.
Component value states are hypothetical, never engine history or viable fronts.
"""
import hashlib
import json

VERSION = 'receptor-family-native-conditional-component-composer-v1'
RESULT_SCHEMA = 'receptor-family-native-component-composition-v1'
POINT_IMPLEMENTATION = 'unit-row-channel4-point-adapter-public-prefix-census-v5'
POINT_VERSION = 'unit-row-channel4-filtered-degree-semantics-v1'
FALLBACK_VERSION = 'unit-row-channel4-filtered-six-rule-fallback-v1'
BASE_VERSION = 'independent-unit-row-missing-mark-degree-check-v2'
BASE_FALLBACK_VERSION = 'unit-row-complete-lazy-six-rule-fallback-v1'
HOST_VERSION = 'receptor-family-six-rule-point-adapter-v3-physical-call-sharing'
RULES = ['axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize']
DEFAULT_LIMITS = {'work': 1000000, 'depth': 128, 'root_advances': 48,
                  'extension_advances': 96, 'heads_per_rule': 1,
                  'quantum': 8, 'components': 1}
FLAGS = {'proposal_only': True, 'engine_generated_accepted': False,
         'fact_accepted': False, 'proof_accepted': False,
         'target_completion_accepted': False, 'frontier_viability_checked': False,
         'degree_or_EOF_accepted': False, 'scheduler_or_rollback_accepted': False,
         'engine_activated': False, 'whole_engine_qualified': False,
         'complete_GCTS_model_accepted': False, 'RL_accepted': False,
         'GCTS_advantage_claimed': False, 'ROOT_resource_accepted': False}


class ComposerDataError(ValueError):
    def __init__(self, code, message):
        super().__init__('native component composer: '+code+': '+message)
        self.code = code


class _OwnLimit(Exception):
    pass


class _NativeFailure(BaseException):
    def __init__(self, error):
        self.error = error


def require(ok, code, message):
    if not ok:
        raise ComposerDataError(code, message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


class _Work:
    def __init__(self, tick, limits):
        self.native, self.steps = tick, 0
        self.limits = dict(DEFAULT_LIMITS)
        if limits is not None:
            require(type(limits) is dict and set(limits) <= set(self.limits), 'LIMITS', 'known fields')
            for key, value in limits.items():
                require(type(value) is int and 0 < value <= self.limits[key],
                        'LIMITS', 'positive exact integer not above declared cap')
                self.limits[key] = value

    def step(self, depth=0):
        try:
            self.native()
        except BaseException as error:
            raise _NativeFailure(error)
        if self.steps >= self.limits['work'] or depth > self.limits['depth']:
            raise _OwnLimit('OWN_WORK_OR_DEPTH_PREFIX')
        self.steps += 1

    def copy(self, value, depth=0):
        self.step(depth)
        if value is None or type(value) in (str, bool, int):
            return value
        if type(value) is list:
            return [self.copy(item, depth+1) for item in value]
        if type(value) is dict:
            require(all(type(k) is str for k in value), 'DATA', 'literal JSON keys')
            return {k: self.copy(v, depth+1) for k, v in value.items()}
        raise ComposerDataError('DATA', 'literal JSON values only')


def compose_components(*, language, base_semantics, marked_semantics,
                       point_module, base_fallback, host_adapter, tick, limits=None):
    """Construct checked conditional components; no engine decision is requested.

    Root and extension cursors alternate finite quanta. Cursor opening and every
    successful event are followed by full public census export+global merge.
    An own-bound interruption discards ALL operative components, even if prior
    complete records exist. Native/export/data/collision errors propagate.
    """
    w = _Work(tick, limits)
    point = marked_semantics
    host = binding = marking_check = root = None
    names, cursors, heads, components, order = {}, [], [], [], []
    component_names = {}
    root_calls = extension_calls = 0
    rule_heads = {rule: 0 for rule in RULES}
    dirty = False

    def merge(entries):
        require(type(entries) is list, 'CENSUS', 'full literal entry list')
        previous = None
        for pair in entries:
            w.step()
            require(type(pair) is list and len(pair) == 2
                    and type(pair[0]) is str and type(pair[1]) is str,
                    'CENSUS', 'full ID and canonical preimage text')
            name, preimage = pair
            require(previous is None or previous < name, 'CENSUS', 'sorted unique literal IDs')
            decoded = json.loads(preimage)
            require(type(decoded) is dict and canonical(decoded) == preimage,
                    'CENSUS', 'whole canonical literal preimage, not a digest')
            require(name not in names or names[name] == preimage, 'COLLISION', 'global full preimage equality')
            names[name] = preimage
            previous = name

    def state_record(value):
        s, totals, marks, selected, excluded, state_names = point.private_state(language, value, w.step)
        require(canonical(s) == canonical(value), 'STATE', 'whole fresh checked component state')
        merge([[k, v] for k, v in sorted(state_names.items())])
        original = point.base_state(language, s, w.step)
        packets = []
        for record in s['selected']:
            w.step()
            tile = point.rebuild_tile(language, record['type_preimage'], record['translation'], w.step)
            point.check_collision(tile, names)
            packets.append({k: v for k, v in tile.items() if k != 'selection_record'})
        packet = {'schema': 'unit-row-row0-decorated-state-v1',
            'version': point.decorator.VERSION, 'marking_id': s['marking_id'],
            'base_state': original, 'decorated_selected': packets,
            'global_t_values': s['t'], 'global_m_values': s['m'],
            'added_m_values': [entry for entry in s['m'] if entry[0][0] == 4],
            **{k: False for k in point.verifier.DATA_FLAGS}}
        checked = point.verifier.check_marked_state(language=language, semantics=base_semantics,
            marking=marking_check['marking'], state=packet, tick=w.step)
        require(checked['marked_state_checked'] is True and checked['marking_id'] == s['marking_id'],
                'STATE', 'fresh independent whole component union')
        return {'state': w.copy(s), 'original_state': w.copy(original),
                'state_sha256': digest(s), 'independent_state_packet': w.copy(packet),
                'independent_state_check': w.copy(checked)}, (s, totals, marks, selected, excluded, state_names)

    def insert(holder, tile):
        s, totals, marks, selected, excluded, unused = holder['checked']
        require(point.legality(tile, totals, marks, selected, excluded) is None,
                'MEMBER', 'native candidate whole current point legality')
        value = w.copy(s)
        new_totals = {p: v for p, v in totals.items()}
        new_marks = {p: w.copy(v) for p, v in marks.items()}
        for p, contribution in tile['global_t_values']:
            w.step();key = tuple(p)
            new_totals[key] = new_totals.get(key, 0)+contribution
            require(new_totals[key] <= 1, 'STATE', 'whole t capacity')
        for p, assigned in tile['global_m_values']:
            w.step();point.agree(new_marks, tuple(p), w.copy(assigned))
        value['selected'].append(w.copy(tile['selection_record']))
        value['t'] = [[list(p), v] for p, v in sorted(new_totals.items())]
        value['m'] = [[list(p), v] for p, v in sorted(new_marks.items())]
        # Explicit root generations are unchanged. Default member generations
        # are component data, not an engine chronology/scheduling claim.
        record, checked = state_record(value)
        return {'record': record, 'checked': checked}

    def export_cursor(task, event):
        nonlocal dirty
        dirty = True
        census = task['cursor'].prototype_census()
        census = w.copy(census)
        fields = {'schema','version','implementation_version','context','context_sha256',
            'input_epoch','marking_id','row','state_sha256','prototype_census',
            'original_yielded_candidates','yielded_candidates','marked_removed','eof_reached',
            'complete_prefix_census','scope','independently_checked','degree_zero_or_singleton_accepted'} | set(point_module.FLAGS)
        context = task['context']
        require(type(census) is dict and set(census) == fields
                and census['schema'] == 'unit-row-channel4-fallback-prototype-census-v1'
                and census['version'] == FALLBACK_VERSION
                and census['implementation_version'] == POINT_IMPLEMENTATION
                and canonical(census['context']) == canonical(context)
                and all(census[k] == context[k] for k in ('context_sha256','input_epoch','marking_id','row','state_sha256'))
                and census['complete_prefix_census'] is True
                and census['scope'] == 'CHECKED_STATE_AND_BASE_YIELDED_MARKED_CURSOR_PREFIX'
                and all(census[k] is False for k in ('independently_checked','degree_zero_or_singleton_accepted')+tuple(point_module.FLAGS)),
                'CENSUS', 'complete exact public current prefix')
        count_keys = ('original_yielded_candidates','yielded_candidates','marked_removed')
        require(all(type(census[k]) is int and census[k] >= 0 for k in count_keys)
                and type(census['eof_reached']) is bool
                and census['original_yielded_candidates'] == census['yielded_candidates']+census['marked_removed'],
                'CENSUS', 'exact raw/survivor/removed accounting')
        prior = task['record']['boundaries'][-1]['census'] if task['record']['boundaries'] else None
        entries = census['prototype_census']
        if prior is None:
            require(event is None and all(census[k] == 0 for k in count_keys)
                    and census['eof_reached'] is False, 'CENSUS', 'fresh open prefix')
        else:
            require(all(census[k] >= prior[k] for k in count_keys), 'CENSUS', 'monotone prefix')
            old = dict(prior['prototype_census']);new = dict(entries)
            require(all(k in new and new[k] == v for k, v in old.items()), 'CENSUS', 'whole prefix retained')
            expected = prior['yielded_candidates']+(1 if event['kind'] == 'CANDIDATE' else 0)
            require(census['yielded_candidates'] == expected
                    and census['eof_reached'] is (event['kind'] == 'EOF'), 'CENSUS', 'event-to-prefix join')
        state_names = task['holder']['checked'][5]
        as_dict = dict(entries)
        require(all(k in as_dict and as_dict[k] == v for k, v in state_names.items()),
                'CENSUS', 'full entry selected/excluded types retained')
        merge(entries)
        boundary = {'event': w.copy(event), 'census': census,
                    'global_join_complete': True, 'global_type_count_after': len(names)}
        task['record']['boundaries'].append(boundary)
        dirty = False
        return len(task['record']['boundaries'])-1

    def open_task(kind, holder, row, head_id=None):
        nonlocal dirty
        dirty = True
        cursor = point_module.open_fallback(language=language, semantics=point,
            state=w.copy(holder['record']['state']), row=row,
            base_fallback=base_fallback.open_fallback, tick=w.step)
        context = w.copy(cursor.context())
        s = holder['record']['state'];original = holder['record']['original_state']
        require(context['schema'] == 'unit-row-channel4-fallback-context-v1'
                and context['version'] == FALLBACK_VERSION
                and canonical(context['state']) == canonical(s)
                and canonical(context['language_binding']) == canonical(binding)
                and context['input_epoch'] == s['input_epoch'] and context['marking_id'] == s['marking_id']
                and type(context['row']) is int and context['row'] == row
                and context['state_sha256'] == digest(s)
                and context['context_sha256'] == digest({k:v for k,v in context.items() if k != 'context_sha256'})
                and canonical(context['original_context']['state']) == canonical(original),
                'CURSOR', 'whole native marked and original entry context')
        ident = 'cursor'+str(len(cursors))
        record = {'id': ident, 'kind': kind, 'head_id': head_id, 'row': row,
                  'context': context, 'boundaries': []}
        cursors.append(record)
        task = {'cursor': cursor, 'context': context, 'record': record,
                'holder': holder, 'ordinal': 0, 'done': False}
        export_cursor(task, None)
        order.append({'action': 'OPEN', 'cursor_id': ident, 'kind': kind, 'row': row, 'head_id': head_id})
        return task

    def advance(task):
        nonlocal dirty
        dirty = True
        event = w.copy(task['cursor'].advance())
        context = task['context']
        require(type(event) is dict and event.get('schema') == 'unit-row-channel4-fallback-event-v1'
                and event.get('context_sha256') == context['context_sha256']
                and event.get('kind') in ('CANDIDATE','EOF'), 'CURSOR', 'literal public event')
        if event['kind'] == 'CANDIDATE':
            require(set(event) == {'schema','kind','context_sha256','ordinal','candidate','independently_checked'}
                    and type(event['ordinal']) is int and event['ordinal'] == task['ordinal']
                    and event['independently_checked'] is False, 'CURSOR', 'exact candidate ordinal/authority')
        else:
            require(set(event) == {'schema','kind','context_sha256','completion'}, 'CURSOR', 'whole EOF event')
            completion = event['completion']
            require(completion['context_sha256'] == context['context_sha256']
                    and completion['state_sha256'] == context['state_sha256']
                    and completion['yielded_candidates'] == task['ordinal']
                    and completion['marking_id'] == context['marking_id']
                    and completion['independently_checked'] is False
                    and completion['degree_zero_or_singleton_accepted'] is False,
                    'CURSOR', 'untrusted EOF current prefix, never degree')
        boundary = export_cursor(task, event)
        if event['kind'] == 'EOF':
            completion = event['completion']
            census = task['record']['boundaries'][boundary]['census']
            completion_fields = {'schema','version','context_sha256','state_sha256','input_epoch',
                'marking_id','row','yielded_candidates','rules_completed','stats','original_completion',
                'complete_fallback_proposed','independently_checked','degree_zero_or_singleton_accepted'} | set(point_module.FLAGS)
            require(type(completion) is dict and set(completion) == completion_fields
                    and completion['schema'] == 'unit-row-channel4-fallback-completion-v1'
                    and completion['version'] == FALLBACK_VERSION
                    and completion['input_epoch'] == context['input_epoch']
                    and type(completion['row']) is int and completion['row'] == context['row']
                    and completion['rules_completed'] == RULES
                    and completion['stats'] == {'original_yielded_candidates': census['original_yielded_candidates'],
                                               'marked_removed': census['marked_removed']}
                    and completion['complete_fallback_proposed'] is True
                    and all(completion[k] is False for k in point_module.FLAGS),
                    'CURSOR', 'full untrusted marked completion and census accounting')
            original = completion['original_completion']
            require(original['schema'] == 'unit-row-all-six-fallback-completion-v1'
                    and original['version'] == BASE_FALLBACK_VERSION
                    and original['context_sha256'] == context['original_context']['context_sha256']
                    and original['state_sha256'] == context['original_context']['state_sha256']
                    and original['yielded_candidates'] == census['original_yielded_candidates']
                    and original['rules_completed'] == RULES and original['independently_checked'] is False,
                    'CURSOR', 'original full completion retained, not degree authority')
        order.append({'action': event['kind'], 'cursor_id': task['record']['id'],
                      'boundary': boundary, 'ordinal': task['ordinal']})
        if event['kind'] == 'EOF':
            task['done'] = True
            return None, boundary
        s, totals, marks, selected, excluded, unused = task['holder']['checked']
        supplied = event['candidate'];key = supplied['placement_key']
        require(key['translation'] == [0, context['row']], 'MEMBER', 'actual queried output row')
        tile = point.rebuild_tile(language, key['type_preimage'], key['translation'], w.step)
        tile = point.with_obligations(tile, totals, w.step)
        require(canonical(tile) == canonical(supplied), 'MEMBER', 'entire fresh rebuilt candidate packet')
        require(point.legality(tile, totals, marks, selected, excluded) is None,
                'MEMBER', 'full current point legality')
        point.check_collision(tile, names)
        pre = tile['base_tile']['placement_key']['type_preimage']
        membership = language.primitive(w.copy(pre['primitive_witness']), w.copy(pre['ordered_premise_formulas']))
        task['ordinal'] += 1
        return {'tile': w.copy(tile), 'native_membership': w.copy(membership),
                'cursor_id': task['record']['id'], 'boundary': boundary}, boundary

    def component(head, extension, holder):
        tiles = [head['member']['tile'], extension['tile']]
        row_tiles = {tile['placement_key']['translation'][1]: tile for tile in tiles}
        require(len(row_tiles) == 2 and len(holder['record']['state']['selected']) == 2,
                'CONNECTED', 'two distinct actual member placements')
        edges, inputs = [], {}
        for tile in tiles:
            row = tile['placement_key']['translation'][1]
            pre = tile['base_tile']['placement_key']['type_preimage']
            for index, (offset, formula) in enumerate(zip(pre['ordered_offsets'], pre['ordered_premise_formulas'])):
                w.step();source_row = row+offset
                use = {'consumer_key': w.copy(tile['placement_key']), 'ordered_index': index,
                       'row': source_row, 'formula': w.copy(formula), 'fact_accepted': False}
                if source_row in row_tiles:
                    source = row_tiles[source_row]
                    actual = source['base_tile']['placement_key']['type_preimage']['primitive_witness']['formula']
                    require(canonical(actual) == canonical(formula), 'CONNECTED', 'ordered selected source formula')
                    edges.append(dict(use, source_key=w.copy(source['placement_key']), occupied=True))
                else:
                    if source_row not in inputs:
                        inputs[source_row] = {'row': source_row, 'formula': w.copy(formula),
                            'sharing': 'ALLOW_SAME_EXACT_PRIOR_SOURCE', 'occupied': False,
                            'fact_accepted': False, 'ordered_uses': []}
                    require(canonical(inputs[source_row]['formula']) == canonical(formula),
                            'CONNECTED', 'one absent source literal shared exactly')
                    inputs[source_row]['ordered_uses'].append(use)
        require(bool(edges), 'CONNECTED', 'actual strict-prior internal read')
        preimage = {'binding': binding, 'marking_id': holder['record']['state']['marking_id'],
                    'member_keys': [tile['placement_key'] for tile in tiles],
                    'state': holder['record']['state']}
        ident = 'automatic-component-'+digest(preimage)
        text = canonical(preimage)
        require(ident not in component_names or component_names[ident] == text,
                'COLLISION', 'whole component identity preimage')
        component_names[ident] = text
        return {'component_id': ident, 'identity_preimage': w.copy(preimage),
            **holder['record'], 'members': w.copy([head['member'], extension]),
            'connected_edges': edges, 'input_ports': [inputs[k] for k in sorted(inputs)],
            'origin': {'kind': 'automatic_primitive_composition', 'version': VERSION,
                'head_id': head['id'], 'head_cursor_id': head['member']['cursor_id'],
                'head_boundary': head['member']['boundary'], 'extension_cursor_id': extension['cursor_id'],
                'extension_boundary': extension['boundary'], 'binding': w.copy(binding),
                'marking_id': holder['record']['state']['marking_id'],
                'state_sha256': holder['record']['state_sha256'],
                'engine_generated_accepted': False, 'root_proof_accepted': False},
            'checks': {'two_distinct_native_members': True, 'strict_prior_internal_edge': True,
                       'fresh_whole_point_union': True, 'public_prefix_global_census_joined': True},
            'flags': dict(FLAGS)}

    status, reason = 'UNKNOWN', 'DECLARED_PROPOSAL_PREFIX_ENDED_OR_NO_PAIR'
    try:
        w.step()
        require(base_semantics.VERSION == BASE_VERSION and point.VERSION == POINT_VERSION
                and point.base is base_semantics and type(point) is point_module.MarkedSemantics
                and point_module.VERSION == 'unit-row-channel4-point-adapter-v1'
                and point_module.IMPLEMENTATION_VERSION == POINT_IMPLEMENTATION
                and point_module.RULES == RULES
                and tuple(point_module.FLAGS) == ('complete_candidate_graph_accepted',
                    'scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted')
                and base_fallback.VERSION == BASE_FALLBACK_VERSION and host_adapter.VERSION == HOST_VERSION,
                'API', 'exact pinned original/native/marked public protocols')
        binding = w.copy(language.binding)
        require(binding.get('profile_name') == 'shared-bounded-six-rule-B12-N44-v2',
                'API', 'unchanged original bounded profile')
        host = w.copy(host_adapter.describe_host(language=language, tick=w.step))
        require(set(host['rules']) == set(RULES) and canonical(host['binding']) == canonical(binding),
                'API', 'actual original host all six rules')
        marking_check = w.copy(point.check_marking(language, w.step))
        initial = point.initial_state(language, w.step)
        root_record, root_checked = state_record(initial)
        root = {'record': root_record, 'checked': root_checked}
        require(initial['height'] == 24 and initial['selected'] == [] and initial['excluded'] == [],
                'STATE', 'unchanged full original empty root')
        root_queue = [{'row': row, 'task': None} for row in range(24)]
        extension_queue = []
        while ((root_queue and root_calls < w.limits['root_advances'])
               or (extension_queue and extension_calls < w.limits['extension_advances'])):
            w.step()
            if root_queue and root_calls < w.limits['root_advances']:
                item = root_queue.pop(0)
                task = item['task'] or open_task('ROOT', root, item['row'])
                item['task'] = task
                order.append({'action': 'QUANTUM', 'kind': 'ROOT', 'cursor_id': task['record']['id']})
                for unused in range(w.limits['quantum']):
                    if root_calls >= w.limits['root_advances'] or task['done']:break
                    root_calls += 1
                    member, boundary = advance(task)
                    if member is None:continue
                    rule = member['tile']['base_tile']['placement_key']['type_preimage']['primitive_witness']['rule']
                    require(rule in rule_heads, 'MEMBER', 'actual native rule')
                    if rule_heads[rule] >= w.limits['heads_per_rule']:continue
                    holder = insert(root, member['tile'])
                    head = {'id': 'head'+str(len(heads)), 'rule': rule, 'member': member,
                            **holder['record']}
                    heads.append(head);rule_heads[rule] += 1
                    head_row = member['tile']['placement_key']['translation'][1]
                    for row in range(head_row+1, 24):
                        extension_queue.append({'row': row, 'task': None, 'head': head, 'holder': holder})
                if not task['done']:root_queue.append(item)
            if extension_queue and extension_calls < w.limits['extension_advances']:
                item = extension_queue.pop(0)
                task = item['task'] or open_task('EXTENSION', item['holder'], item['row'], item['head']['id'])
                item['task'] = task
                order.append({'action': 'QUANTUM', 'kind': 'EXTENSION', 'cursor_id': task['record']['id']})
                for unused in range(w.limits['quantum']):
                    if extension_calls >= w.limits['extension_advances'] or task['done']:break
                    extension_calls += 1
                    member, boundary = advance(task)
                    if member is None:continue
                    tile = member['tile'];pre = tile['base_tile']['placement_key']['type_preimage']
                    head_row = item['head']['member']['tile']['placement_key']['translation'][1]
                    if not any(item['row']+offset == head_row for offset in pre['ordered_offsets']):continue
                    holder = insert(item['holder'], tile)
                    record = component(item['head'], member, holder)
                    require(not dirty, 'CENSUS', 'no unreconciled cursor boundary before proposal')
                    components.append(record)
                    if len(components) >= w.limits['components']:break
                if len(components) >= w.limits['components']:break
                if not task['done']:extension_queue.append(item)
        require(canonical(host_adapter.describe_host(language=language, tick=w.step)) == canonical(host)
                and canonical(language.binding) == canonical(binding), 'STABILITY', 'original host unchanged')
        fresh_marking = point.check_marking(language, w.step)
        require(canonical(fresh_marking['marking']) == canonical(marking_check['marking']),
                'STABILITY', 'full frozen marking unchanged')
        if components:
            status, reason = 'COMPONENT_PROPOSALS', 'DECLARED_COMPLETE_COMPONENT_CAP_OR_PREFIX'
    except _NativeFailure as failure:
        raise failure.error
    except _OwnLimit as limit:
        reason = str(limit)
        status = 'UNKNOWN'
    accepted = components if status == 'COMPONENT_PROPOSALS' and not dirty else []
    return {'schema': RESULT_SCHEMA, 'version': VERSION, 'status': status, 'reason': reason,
        'request': {'limits': dict(w.limits), 'allocation': 'ALTERNATING_ROOT_EXTENSION_QUANTA',
                    'component_size': 2, 'full_rows': 24, 'rule_order': list(RULES)},
        'binding': binding, 'host': host, 'marking_check': marking_check,
        'root': None if root is None else root['record'], 'heads': heads,
        'cursor_records': cursors, 'construction_order': order,
        'global_prototype_census': [[k, v] for k, v in sorted(names.items())],
        'operative_global_join_complete': status == 'COMPONENT_PROPOSALS' and not dirty,
        'components': accepted,
        'unaccepted_complete_components': components if not accepted else [],
        'work': {'steps': w.steps, 'root_advance_calls': root_calls,
                 'extension_advance_calls': extension_calls, 'retained_heads_by_rule': rule_heads},
        'scope': 'CONDITIONAL_COMPONENT_DATA_ONLY_NOT_ENGINE_HISTORY_OR_FRONTIER',
        'flags': dict(FLAGS)}
