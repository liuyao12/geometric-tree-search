"""SOURCE ONLY: checked conditional expansions to original six-rule point data.

No project imports, source loader, clock, search, engine or advice activation.
The caller authenticates a fresh original Source17/input2 language and all
injected modules. The hypothetical cluster union never mutates its input state.
"""
import hashlib
import json

VERSION = 'receptor-family-six-rule-point-adapter-v3-physical-call-sharing'
CHECKER_VERSION = 'receptor-family-independent-expansion-checker-v1'
CHECK_SCHEMA = 'receptor-family-conditional-expansion-check-v1'
HOST_SCHEMA = 'receptor-family-host-v1'
ROW_SCHEMA = 'receptor-family-six-rule-row-assignment-v1'
INPUT_SOURCE_SCHEMA = 'receptor-family-six-rule-input-source-v1'
RESULT_SCHEMA = 'receptor-family-six-rule-local-cluster-v1'
KERNEL_VERSION = 'arithmetic-open-parameter-six-rule-Q-v1'
BASE_VERSION = 'independent-unit-row-missing-mark-degree-check-v2'
MARKED_VERSION = 'unit-row-channel4-filtered-degree-semantics-v1'
VERIFIER_VERSION = 'unit-row-independent-channel4-state-verifier-v1'
PROFILE_SHA256 = '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'
ORIGINAL_CODE = {
    'kernel': ('43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9', 10323),
    'membership': ('5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332', 20112),
    'degree_checker': ('c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d', 27553)}
RULES = {
    'axiom': {'input_count': 0, 'arguments': {'name': 'LITERAL'}},
    'assumption': {'input_count': 0, 'arguments': {'index': 'LITERAL'}},
    'instantiate': {'input_count': 0, 'arguments': {'universal': 'FORMULA', 'term': 'TERM'}},
    'eq_subst': {'input_count': 0, 'arguments': {'variable': 'VARIABLE', 'template': 'FORMULA',
                                              'left': 'TERM', 'right': 'TERM'}},
    'mp': {'input_count': 2, 'arguments': {}},
    'generalize': {'input_count': 1, 'arguments': {'variable': 'VARIABLE'}}}
FLAGS = ('proof_accepted', 'root_proof_accepted', 'degree_or_EOF_accepted',
         'scheduler_or_rollback_accepted', 'engine_activated', 'marking_activated',
         'complete_GCTS_model_accepted', 'trajectory_accepted', 'RL_accepted',
         'GCTS_advantage_accepted', 'ROOT_resource_accepted', 'host_membership_accepted',
         'point_union_accepted', 'pruning_accepted', 'runtime_qualified')


def require(ok, reason):
    if not ok:
        raise ValueError('six-rule receptor adapter: ' + reason)


def tree(value, tick):
    tick()
    if type(value) in (str, int, bool) or value is None:
        return value
    if type(value) is list:
        return [tree(v, tick) for v in value]
    require(type(value) is dict and all(type(k) is str for k in value), 'builtin JSON only')
    return {k: tree(v, tick) for k, v in value.items()}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def describe_host(*, language, tick):
    """Derive syntax-host data; raw Source/input custody remains the caller's.

    Features advertise admitted dialect forms, not acceptance of an instance.
    Every ground member still calls the real language.primitive in adaptation.
    """
    tick()
    require(language.kernel_module.VERSION == KERNEL_VERSION, 'original kernel API')
    values = {k: tree(getattr(language, k), tick) for k in
              ('declaration', 'policy', 'source_bindings', 'binding', 'theory',
               'parameters', 'gamma', 'target', 'hole')}
    declaration, binding = values['declaration'], values['binding']
    require(len(values['source_bindings']) == 17 and type(declaration['height']) is int
            and declaration['height'] == 24 and binding['profile_sha256'] == PROFILE_SHA256,
            'original Source17 height/profile')
    for role, (sha, size) in ORIGINAL_CODE.items():
        ref = values['source_bindings'][role]
        require(ref['sha256'] == sha and type(ref['bytes']) is int and ref['bytes'] == size,
                'original primitive Source pin')
    for name, key in (('theory', 'theory'), ('parameters', 'parameters'),
                      ('gamma', 'ordered_Gamma'), ('target', 'target')):
        require(canonical(values[name]) == canonical(declaration[key]), 'effective original ' + name)
    require(canonical(language.kernel.theory) == canonical(values['theory'])
            and type(language.kernel.parameters) is tuple
            and list(language.kernel.parameters) == values['parameters']
            and canonical(language.kernel.gamma) == canonical(values['gamma']),
            'effective original kernel authority')
    names = {}
    for key in ('parameter_set', 'input_names', 'binder_names', 'forbidden'):
        value = getattr(language, key)
        require(type(value) is frozenset and all(type(n) is str for n in value),
                'effective finite name census')
        names[key] = sorted(value)
    require(names['parameter_set'] == sorted(values['parameters']), 'effective parameter scope')
    logical = {'theory': values['theory'], 'parameters': values['parameters'],
               'ordered_Gamma': values['gamma'], 'target': values['target'], 'height': 24}
    require(set(binding) == {'profile_name', 'profile_sha256', 'declaration_sha256',
                'logical_input_sha256', 'source_bindings_sha256', 'language_epoch'}
            and binding['logical_input_sha256'] == digest(logical)
            and binding['source_bindings_sha256'] == digest(values['source_bindings'])
            and binding['language_epoch'] == digest({k: v for k, v in binding.items()
                                                   if k != 'language_epoch'}),
            'full original binding without epoch rebasing')
    authority = dict(values, effective_names=names, kernel_version=KERNEL_VERSION,
                     semantic_model_source_count=17, height=24)
    tick()
    return {'schema': HOST_SCHEMA, 'host_id': 'original-Source17-unit-row-arithmetic',
            'dialect': KERNEL_VERSION, 'binding': tree(binding, tick), 'authority': authority,
            'functions': tree(values['theory']['functions'], tick),
            'predicates': tree(values['theory']['predicates'], tick),
            'variable_names': sorted(set(names['binder_names']) | {values['hole']}),
            'features': sorted(['FORMULA', 'TERM', 'VARIABLE', 'PREDICATE_SYMBOL',
                'IMPLICATION', 'EQUALITY', 'QUANTIFIER', 'ORDERED_MP', 'NAMED_AXIOM',
                'INDEXED_ASSUMPTION', 'INSTANTIATION', 'ATOMIC_EQ_SUBST', 'GENERALIZATION']),
            'rules': tree(RULES, tick), 'ordered_Gamma': tree(values['gamma'], tick)}


def rows(entries, identities, tick):
    require(type(entries) is list, 'row assignment list')
    result = {}
    for item in entries:
        tick()
        require(type(item) is list and len(item) == 2 and type(item[0]) is str
                and item[0] not in result and type(item[1]) is int and 0 <= item[1] < 24,
                'exact unique node/input row assignment')
        result[item[0]] = item[1]
    require(set(result) == set(identities), 'complete node/input row assignment')
    return result


def _key(record):
    return {k: v for k, v in record.items() if k != 'generation'}


def adapt_expansion(*, language, base_semantics, marked_semantics, expansion_checker,
                    registry, family_id, host, substitution, port_bindings, proposal,
                    state, row_assignment, tick):
    """Fresh conditional check, real membership and hypothetical whole point union.

    No offered receipt is trusted and no engine/state is modified. Errors from
    the checker, native membership, point verifier or tick propagate unchanged.
    """
    tick()
    request = {'registry': registry, 'family_id': family_id, 'host': host,
               'substitution': substitution, 'port_bindings': port_bindings,
               'proposal': proposal, 'state': state, 'row_assignment': row_assignment}
    input_raw = canonical(tree(request, tick))
    actual_host = describe_host(language=language, tick=tick)
    require(canonical(host) == canonical(actual_host), 'exact actual original host')
    before_visits = language.kernel.visits
    require(type(before_visits) is int, 'native cumulative visit counter')
    require(base_semantics.VERSION == BASE_VERSION and marked_semantics.VERSION == MARKED_VERSION
            and marked_semantics.base is base_semantics
            and marked_semantics.verifier.VERSION == VERIFIER_VERSION,
            'actual original and marked point APIs')
    require(expansion_checker.VERSION == CHECKER_VERSION, 'independent expansion checker API')
    checked = expansion_checker.check_expansion(registry=tree(registry, tick), family_id=family_id,
        host=tree(actual_host, tick), substitution=tree(substitution, tick),
        port_bindings=tree(port_bindings, tick), proposal=tree(proposal, tick), tick=tick)
    checked = tree(checked, tick)
    require(checked['schema'] == CHECK_SCHEMA and checked['version'] == CHECKER_VERSION,
            'fresh conditional checker protocol')
    common = {'schema': RESULT_SCHEMA, 'version': VERSION, 'host': actual_host,
              'expansion_check': checked, 'state': tree(state, tick),
              'row_assignment': tree(row_assignment, tick), 'input_sha256': digest(request),
              'proposal_only': True, 'state_is_hypothetical_only': True,
              **{k: False for k in FLAGS}}
    if checked['status'] == 'UNKNOWN':
        require(checked['conditional_expansion_checked'] is False and checked['expansion'] is None,
                'no partial independent expansion')
        require(canonical(describe_host(language=language, tick=tick)) == canonical(actual_host)
                and canonical(request) == input_raw, 'original authority and all adapter inputs unchanged')
        return dict(common, status='UNKNOWN', reason='INDEPENDENT_EXPANSION_UNRESOLVED',
                    members=[], node_map=[], input_ports=[], output_ports=[],
                    union_state=None, union_state_check=None, dependencies=None, costs=None,
                    local_member_membership_checked=False, local_point_union_checked=False,
                    physical_call_input_bindings=[])
    require(checked['status'] == 'CONDITIONAL_EXPANSION_CHECKED'
            and checked['conditional_expansion_checked'] is True,
            'fresh conditional expansion required')
    expansion = checked['expansion']
    require(canonical(expansion['request']) == canonical({'registry': registry,
            'host': host, 'substitution': substitution, 'port_bindings': port_bindings})
            and expansion['family_id'] == family_id,
            'full checked expansion request and family')
    marking_check = marked_semantics.check_marking(language, tick)
    s, totals, marks, selected, excluded, names = marked_semantics.private_state(language, state, tick)
    original_state = marked_semantics.base_state(language, s, tick)
    initial_totals, initial_marks = dict(totals), dict(marks)
    require(type(row_assignment) is dict and set(row_assignment) == {'schema', 'node_rows', 'input_rows'}
            and row_assignment['schema'] == ROW_SCHEMA, 'row assignment protocol')
    nodes, ports = expansion['primitive_nodes'], expansion['input_ports']
    require(type(nodes) is list and type(ports) is list, 'full checked primitive nodes and input ports')
    node_rows = rows(row_assignment['node_rows'], [n['id'] for n in nodes], tick)
    input_rows = rows(row_assignment['input_rows'], [p['port_id'] for p in ports], tick)
    require(len(node_rows) == len(nodes) and len(input_rows) == len(ports), 'unique expansion identifiers')
    original_selected = {v['translation'][1]: _key(v) for v in original_state['selected']}
    inputs, input_records = {}, []
    for port in ports:
        tick()
        ident, formula = port['port_id'], port['formula']
        row = input_rows[ident]
        require(type(port['occupied']) is bool and port['occupied'] is (totals[(0, row)] == 1)
                and port['fact_accepted'] is False, 'actual input occupancy without fact authority')
        expected_source = {'schema': INPUT_SOURCE_SCHEMA, 'row': row,
                           'original_full_key': original_selected.get(row)}
        require(canonical(port['source']) == canonical(expected_source), 'exact actual input source')
        language.formula(formula)
        if (1, row) in marks:
            require(canonical(marks[(1, row)]) == canonical(['formula', base_semantics.text(formula)]),
                    'literal external input marking')
        inputs[ident] = {'row': row, 'formula': tree(formula, tick)}
        input_records.append(dict(tree(port, tick), row=row, fact_accepted=False))
    root_descriptor = expansion['family_preimage']
    sharing = {v['id']: v['sharing'] for v in root_descriptor['inputs']}
    for i, p in enumerate(input_records):
        for q in input_records[:i]:
            tick()
            if p['row'] == q['row']:
                require(sharing[p['port_id']] == sharing[q['port_id']] == 'ALLOW_SAME_EXACT_PRIOR_SOURCE'
                        and canonical(p['formula']) == canonical(q['formula'])
                        and canonical(p['source']) == canonical(q['source']), 'physical input sharing policy')
    descriptors = {d['family_id']: d for d in registry}
    physical_call_inputs = []
    for frame in expansion['call_frames']:
        tick()
        policy = {p['id']: p['sharing'] for p in descriptors[frame['family_id']]['inputs']}
        resolved = []
        for port in frame['inputs']:
            tick()
            ref = port['source']
            require(type(ref) is dict and set(ref) in ({'node'}, {'input'}), 'call input physical reference')
            row = node_rows[ref['node']] if 'node' in ref else input_rows[ref['input']]
            value = {'port_id': port['port_id'], 'source': tree(ref, tick), 'row': row,
                     'formula': tree(port['formula'], tick), 'sharing': policy[port['port_id']],
                     'fact_accepted': False}
            for other in resolved:
                tick()
                if row == other['row']:
                    require(value['sharing'] == other['sharing'] == 'ALLOW_SAME_EXACT_PRIOR_SOURCE'
                            and canonical(value['formula']) == canonical(other['formula']),
                            'physical call input sharing policy')
            resolved.append(value)
        physical_call_inputs.append({'call_path': tree(frame['call_path'], tick),
            'family_id': frame['family_id'], 'inputs': resolved})
    union = tree(s, tick)
    union_selected = set(selected)
    members, node_map, processed, by_key = [], [], {}, {}
    point_nodes, ordered_edges, reused_existing = {}, 0, set()
    for node in nodes:
        tick()
        ident, rule, formula, arguments = node['id'], node['rule'], node['formula'], node['arguments']
        require(type(rule) is str and rule in RULES and type(arguments) is dict
                and set(arguments) == set(RULES[rule]['arguments'])
                and len(node['ordered_inputs']) == RULES[rule]['input_count'], 'host primitive rule and argument fields')
        row, premises, reads, edge_records = node_rows[ident], [], [], []
        for index, ref in enumerate(node['ordered_inputs']):
            tick()
            require(type(ref) is dict and set(ref) in ({'node'}, {'input'}), 'primitive ordered reference')
            source = processed.get(ref['node']) if 'node' in ref else inputs.get(ref['input'])
            require(source is not None and type(source['row']) is int and 0 <= source['row'] < row,
                    'strict earlier actual primitive read')
            premises.append(tree(source['formula'], tick)); reads.append(source['row']); ordered_edges += 1
            edge_records.append({'ordered_index': index, 'source': tree(ref, tick), 'row': source['row'],
                'formula': tree(source['formula'], tick),
                'occupied_in_input': initial_totals[(0, source['row'])] == 1, 'fact_accepted': False})
        witness = {'rule': rule, 'formula': tree(formula, tick), **tree(arguments, tick)}
        membership = language.primitive(witness, premises)
        preimage = {'input_epoch': language.binding['language_epoch'], 'primitive_witness': witness,
                    'ordered_premise_formulas': premises, 'ordered_offsets': [r-row for r in reads]}
        bare = base_semantics.rebuild_tile(language, preimage, [0, row], tick)
        decorated_preimage = {'schema': 'unit-row-row0-decorated-type-v1',
                             'base_type_preimage': preimage, 'marking_id': marked_semantics.marking_id}
        tile = marked_semantics.rebuild_tile(language, decorated_preimage, [0, row], tick)
        require(canonical(tile['base_tile']) == canonical(bare), 'complete original member projection')
        marked_semantics.check_collision(tile, names)
        key = base_semantics.text(tile['placement_key'])
        duplicate = by_key.get(key)
        if duplicate is not None:
            require(canonical(duplicate['tile']) == canonical(tile), 'shared placement full packet identity')
        else:
            reason = marked_semantics.legality(tile, totals, marks, union_selected, excluded)
            if key in union_selected:
                require(reason == 'already_selected' and key in selected,
                        'only exact current selected member reuse')
                reused_existing.add(key)
            else:
                require(reason is None, 'current whole point legality: ' + str(reason))
                for p, value in tile['global_t_values']:
                    point = tuple(p); totals[point] += value
                    require(totals[point] <= 1, 'complete union t capacity')
                for p, value in tile['global_m_values']:
                    marked_semantics.agree(marks, tuple(p), value)
                union_selected.add(key); union['selected'].append(tree(tile['selection_record'], tick))
            entry = {'first_node': ident, 'tile': tile, 'base_tile': bare,
                     'already_selected_in_input': key in selected}
            by_key[key] = entry; members.append(entry)
        for point, value in tile['global_t_values'] + tile['global_m_values']:
            tick(); point_nodes.setdefault(tuple(point), []).append(ident)
        node_map.append({'node_id': ident, 'row': row, 'membership': membership,
            'original_key': tree(bare['placement_key'], tick), 'decorated_key': tree(tile['placement_key'], tick),
            'shared_with_node': None if duplicate is None else duplicate['first_node'],
            'already_selected_in_input': key in selected, 'ordered_reads': edge_records})
        processed[ident] = {'row': row, 'formula': tree(formula, tick), 'key': tile['placement_key']}
    union['t'] = [[list(p), v] for p, v in sorted(totals.items())]
    union['m'] = [[list(p), v] for p, v in sorted(marks.items())]
    checked_union = marked_semantics.private_state(language, union, tick)[0]
    base_union = marked_semantics.base_state(language, checked_union, tick)
    decorated_selected = []
    for record in checked_union['selected']:
        tile = marked_semantics.rebuild_tile(language, record['type_preimage'], record['translation'], tick)
        decorated_selected.append({k: v for k, v in tile.items() if k != 'selection_record'})
    full_packet = {'schema': 'unit-row-row0-decorated-state-v1',
        'version': marked_semantics.decorator.VERSION, 'marking_id': marked_semantics.marking_id,
        'base_state': base_union, 'decorated_selected': decorated_selected,
        'global_t_values': checked_union['t'], 'global_m_values': checked_union['m'],
        'added_m_values': [[list(p), v] for p, v in sorted(marks.items()) if p[0] == 4],
        **{k: False for k in marked_semantics.verifier.DATA_FLAGS}}
    union_check = marked_semantics.verifier.check_marked_state(language=language, semantics=base_semantics,
        marking=marking_check['marking'], state=full_packet, tick=tick)
    require(union_check['marked_state_checked'] is True, 'fresh independent whole union check')
    outputs = []
    for output in expansion['outputs']:
        ref = output['source']; source = processed[ref['node']] if 'node' in ref else inputs[ref['input']]
        require(canonical(output['formula']) == canonical(source['formula']), 'literal output node binding')
        output_row = source['row']
        if (1, output_row) in marks:
            require(canonical(marks[(1, output_row)]) == canonical(
                ['formula', base_semantics.text(output['formula'])]), 'literal final output marking')
        outputs.append(dict(tree(output, tick), row=output_row,
            occupied_in_input=initial_totals[(0, output_row)] == 1,
            occupied_in_hypothetical_union=totals[(0, output_row)] == 1,
            formula_mark_assigned_in_hypothetical_union=(1, output_row) in marks,
            unresolved_in_hypothetical_union=totals[(0, output_row)] == 0, fact_accepted=False))
    for node in node_map:
        for edge in node['ordered_reads']:
            edge['occupied_in_hypothetical_union'] = totals[(0, edge['row'])] == 1
    for port in input_records:
        input_row = port['row']
        if (1, input_row) in marks:
            require(canonical(marks[(1, input_row)]) == canonical(
                ['formula', base_semantics.text(port['formula'])]), 'literal final external input marking')
        port['occupied_in_hypothetical_union'] = totals[(0, input_row)] == 1
        port['formula_mark_assigned_in_hypothetical_union'] = (1, input_row) in marks
        port['unresolved_in_hypothetical_union'] = totals[(0, input_row)] == 0
    original_union_keys = {v['translation'][1]: _key(v) for v in base_union['selected']}
    decorated_union_keys = {v['translation'][1]: _key(v) for v in checked_union['selected']}
    for frame in physical_call_inputs:
        for port in frame['inputs']:
            port['original_full_key_in_hypothetical_union'] = original_union_keys.get(port['row'])
            port['decorated_full_key_in_hypothetical_union'] = decorated_union_keys.get(port['row'])
            port['unresolved_in_hypothetical_union'] = totals[(0, port['row'])] == 0
    after_visits = language.kernel.visits
    require(type(after_visits) is int and after_visits >= before_visits, 'monotone native visits')
    require(canonical(describe_host(language=language, tick=tick)) == canonical(actual_host)
            and canonical(request) == input_raw, 'original authority and all adapter inputs unchanged')
    tick()
    return dict(common, status='READY_LOCAL_CLUSTER', reason=None,
        local_member_membership_checked=True, local_point_union_checked=True,
        original_state=original_state, marking_check=marking_check, members=members, node_map=node_map,
        input_ports=input_records, hypothesis_ports=tree(expansion['hypothesis_ports'], tick),
        output_ports=outputs, physical_call_input_bindings=physical_call_inputs,
        union_state=checked_union, union_packet=full_packet, union_state_check=union_check,
        original_member_keys=[m['base_tile']['placement_key'] for m in members],
        decorated_member_keys=[m['tile']['placement_key'] for m in members],
        dependencies={'current_state_sha256': digest(s), 'host_sha256': digest(actual_host),
            'marking_id': marked_semantics.marking_id,
            'all_member_support': [{'point': list(p), 'node_ids': ids} for p, ids in sorted(point_nodes.items())],
            'external_input_support': [{'port_id': p['port_id'], 'points': [[0, p['row']], [1, p['row']]]}
                                       for p in input_records], 'engine_graph_or_retention_accepted': False},
        costs={'expanded_nodes': len(nodes), 'unique_member_placements': len(members),
            'new_placements_in_hypothetical_union': len(checked_union['selected'])-len(s['selected']),
            'reused_existing_placements': len(reused_existing), 'duplicate_node_placements': len(nodes)-len(members),
            'ordered_edge_uses': ordered_edges,
            'physical_call_frames_checked': len(physical_call_inputs),
            'physical_call_input_uses': sum(len(f['inputs']) for f in physical_call_inputs),
            'direct_expansion_checker_calls': 1,
            'direct_language_primitive_calls': len(nodes), 'direct_base_rebuild_calls': len(nodes),
            'direct_marked_rebuild_calls': len(nodes)+len(checked_union['selected']),
            'direct_marked_private_state_calls': 2, 'direct_base_projection_calls': 2,
            'direct_independent_union_check_calls': 1,
            'native_kernel_visits_before': before_visits, 'native_kernel_visits_after': after_visits,
            'native_kernel_visits_delta': after_visits-before_visits,
            'direct_counts_exclude_nested_delegations': True,
            'point_data_bytes': len(canonical([members, full_packet]).encode('ascii'))})
