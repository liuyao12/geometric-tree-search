"""SOURCE ONLY: bounded literal-ground mined-family physical preferences.

The caller authenticates all injected Sources and original Source17/input2.
No engine, search, degree, cursor, clock, saved result or project import exists.
A finite proposal prefix is never a candidate-domain or absence certificate.
"""
import hashlib
import json

VERSION = 'receptor-family-literal-ground-physical-provider-v1'
RESULT_SCHEMA = 'receptor-family-mined-physical-provider-v1'
BATCH_SCHEMA = 'receptor-family-primitive-preference-batch-v1'
MINER_VERSION = 'receptor-family-primitive-DAG-miner-v1'
PRODUCER_VERSION = 'receptor-family-typed-expander-v1'
CHECKER_VERSION = 'receptor-family-independent-expansion-checker-v1'
ADAPTER_VERSION = 'receptor-family-six-rule-point-adapter-v3-physical-call-sharing'
POINT_VERSION = 'unit-row-channel4-filtered-degree-semantics-v1'
SOURCE_SCHEMA = 'receptor-family-six-rule-input-source-v1'
ROW_SCHEMA = 'receptor-family-six-rule-row-assignment-v1'
DEFAULT_LIMITS = {'work': 1000000, 'depth': 128, 'input_bytes': 4194304,
                  'records': 16, 'row_trials': 256, 'instances': 8}
FLAGS = {'proposal_only': True, 'matching_complete': False, 'fact_accepted': False,
         'degree_or_EOF_accepted': False, 'engine_activated': False,
         'scheduler_accepted': False, 'pruning_accepted': False,
         'proof_accepted': False, 'trajectory_accepted': False,
         'RL_accepted': False, 'runtime_qualified': False}
LEGAL_REASONS = ('branch_excluded_complete_key', 'whole_support_capacity',
                 'whole_remote_or_metadata_mark_conflict')


class ProviderDataError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__('mined family provider ' + code + ': ' + detail)


class _Unfinished(Exception):
    pass


class _CallbackFailure(BaseException):
    def __init__(self, error):
        self.error = error


def require(ok, code, detail):
    if not ok:
        raise ProviderDataError(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def ascii_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=True, allow_nan=False).encode('ascii')
    return hashlib.sha256(raw).hexdigest()


def fields(value, names, code):
    require(type(value) is dict and set(value) == set(names), code, 'exact object fields')


class _Work:
    def __init__(self, tick, limits):
        require(callable(tick), 'TICK', 'caller cumulative native-first callback')
        self.tick = tick
        self.steps = 0
        self.trials = 0
        self.limits = dict(DEFAULT_LIMITS)
        if limits is not None:
            require(type(limits) is dict and set(limits) <= set(self.limits), 'LIMITS', 'known fields only')
            for key, value in limits.items():
                require(type(value) is int and 0 < value <= self.limits[key], 'LIMITS', 'bounded positive exact integer')
                self.limits[key] = value

    def native(self):
        try:
            self.tick()
        except BaseException as error:
            raise _CallbackFailure(error) from error

    def step(self, depth=0):
        if self.steps >= self.limits['work'] or depth > self.limits['depth']:
            raise _Unfinished('OWN_WORK_OR_DEPTH_PREFIX')
        self.native()
        self.steps += 1

    def trial(self):
        self.step()
        if self.trials >= self.limits['row_trials']:
            raise _Unfinished('OWN_PHYSICAL_ROW_TRIAL_PREFIX')
        self.trials += 1

    def copy(self, value, depth=0):
        self.step(depth)
        if value is None or type(value) in (str, bool, int):
            return value
        if type(value) is list:
            return [self.copy(v, depth+1) for v in value]
        require(type(value) is dict and all(type(k) is str for k in value), 'JSON', 'strict builtin JSON only')
        return {k: self.copy(v, depth+1) for k, v in value.items()}


def _key(record):
    return {k: v for k, v in record.items() if k != 'generation'}


def _ready_checked(checked, proposal):
    require(checked['schema'] == 'receptor-family-conditional-expansion-check-v1'
            and checked['version'] == CHECKER_VERSION, 'CHECK_PROTOCOL', 'fresh checker schema/version')
    if checked['status'] == 'UNKNOWN':
        require(checked['conditional_expansion_checked'] is False and checked['expansion'] is None,
                'CHECK_PROTOCOL', 'UNKNOWN carries no partial expansion')
        return False
    require(checked['status'] == 'CONDITIONAL_EXPANSION_CHECKED'
            and checked['conditional_expansion_checked'] is True
            and canonical(checked['expansion']) == canonical(proposal),
            'CHECK_PROTOCOL', 'full fresh independent expansion equality')
    return True


def _ground_roundtrip(record, mined, expansion, work):
    """Join the entire cut's grounded primitive/edge/boundary/output data.

    This is a data roundtrip, not authentication of the source DAG's origin or
    a source proof. Native primitive admission still happens separately.
    """
    dag = mined['request']['derivation']
    require(dag['schema'] == 'receptor-family-primitive-derivation-DAG-v1'
            and canonical(dag['host_binding']) == canonical(mined['request']['host']['binding']),
            'DAG', 'full original host binding')
    source_nodes = {}
    for node in dag['nodes']:
        work.step()
        require(type(node['id']) is str and node['id'] not in source_nodes, 'DAG', 'unique source nodes')
        source_nodes[node['id']] = node
    selected = record['cut']['selected_node_ids']
    require(type(selected) is list and selected and len(selected) == len(set(selected))
            and all(n in source_nodes for n in selected)
            and selected == [n['id'] for n in dag['nodes'] if n['id'] in set(selected)],
            'CUT', 'full topologically ordered selected source IDs')
    require(record['cut']['anchor'] in selected
            and record['cut']['source_DAG_sha256'] == ascii_digest(dag), 'CUT', 'complete source DAG preimage')
    maps = record['source_node_map']
    require(type(maps) is list and [m['source_node_id'] for m in maps] == selected
            and len({m['descriptor_step_id'] for m in maps}) == len(maps),
            'ROUNDTRIP', 'complete unique original node to descriptor-step map')
    step_ids = {m['source_node_id']: m['descriptor_step_id'] for m in maps}
    expanded = {}
    root_hypotheses = {p['port_id']: p for p in expansion['hypothesis_ports']}
    for node in expansion['primitive_nodes']:
        work.step()
        origin = node['origin']
        if origin['call_path'] == [] and origin['step_id'] is not None:
            require(origin['step_id'] not in expanded, 'ROUNDTRIP', 'unique root primitive step')
            expanded[origin['step_id']] = node
    require(set(expanded) == set(step_ids.values()), 'ROUNDTRIP', 'whole root body without hidden extra primitive steps')
    boundary = {}
    source_inputs = {p['id']: p for p in dag['inputs']}
    source_hypotheses = {p['id']: p for p in dag['hypotheses']}
    for item in record['boundary_source_map']:
        work.step()
        ref = item['original_reference']
        name = canonical(ref)
        require(name not in boundary and type(ref) is dict and len(ref) == 1,
                'ROUNDTRIP', 'one unique full boundary reference')
        if 'node' in ref:
            require(ref['node'] in source_nodes and ref['node'] not in selected, 'ROUNDTRIP', 'cut-out source node')
            source = source_nodes[ref['node']]
        elif 'input' in ref:
            require(ref['input'] in source_inputs, 'ROUNDTRIP', 'original input port')
            source = source_inputs[ref['input']]
        else:
            require(set(ref) == {'hypothesis'} and ref['hypothesis'] in source_hypotheses,
                    'ROUNDTRIP', 'original indexed hypothesis port')
            source = source_hypotheses[ref['hypothesis']]
        kind, pid = item['port_kind'], item['port_id']
        expected_kind = 'hypothesis' if ('hypothesis' in ref or 'node' in ref and source['rule'] == 'assumption') else 'input'
        require(kind == expected_kind, 'ROUNDTRIP', 'actual indexed hypothesis versus conditional input kind')
        original_sharing = (source['sharing'] if 'input' in ref else 'DISTINCT_SOURCE_REQUIRED') if kind == 'input' else None
        expected_item = {'port_kind': kind, 'port_id': pid, 'original_reference': ref,
            'source_node_id': ref.get('node'), 'source_input_id': ref.get('input'),
            'source_hypothesis_id': ref.get('hypothesis'), 'source_formula': source['formula'],
            'original_origin': source.get('origin'), 'original_sharing': original_sharing}
        require(canonical(item) == canonical(expected_item),
                'ROUNDTRIP', 'full boundary formula/reference/sharing/opaque origin')
        if kind == 'hypothesis':
            require(pid in root_hypotheses, 'ROUNDTRIP', 'materialized actual Gamma port')
            actual = root_hypotheses[pid]
            index = source['gamma_index'] if 'hypothesis' in ref else source['arguments']['index']
            require(actual['gamma_index'] == index and actual['formula'] == source['formula'],
                    'ROUNDTRIP', 'same original Gamma occurrence')
            rebuilt_ref = actual['source']
        else:
            require(kind == 'input', 'ROUNDTRIP', 'explicit boundary kind')
            ports = [p for p in expansion['input_ports'] if p['port_id'] == pid]
            require(len(ports) == 1 and ports[0]['formula'] == source['formula'],
                    'ROUNDTRIP', 'full ground input port')
            rebuilt_ref = {'input': pid}
        boundary[name] = (kind, pid, rebuilt_ref)
    edges = []
    used_boundary = set()
    for source_id in selected:
        work.step()
        original = source_nodes[source_id]
        rebuilt = expanded[step_ids[source_id]]
        require(all(canonical(original[k]) == canonical(rebuilt[k]) for k in ('rule', 'formula', 'arguments')),
                'ROUNDTRIP', 'same complete native primitive witness')
        expected_refs = []
        for index, ref in enumerate(original['ordered_inputs']):
            work.step()
            if 'node' in ref and ref['node'] in step_ids:
                expected_refs.append({'node': expanded[step_ids[ref['node']]]['id']})
                descriptor_ref = {'step': step_ids[ref['node']]}
            else:
                name = canonical(ref)
                require(name in boundary, 'ROUNDTRIP', 'every cut edge has a boundary map')
                kind, pid, new_ref = boundary[name]
                expected_refs.append(new_ref)
                descriptor_ref = {kind: pid}
                used_boundary.add(name)
            edges.append({'source_node_id': source_id, 'ordered_index': index,
                          'original_reference': ref, 'descriptor_reference': descriptor_ref})
        require(rebuilt['ordered_inputs'] == expected_refs, 'ROUNDTRIP', 'all ordered/repeated edge uses')
    require(used_boundary == set(boundary) and canonical(edges) == canonical(record['boundary_edge_map']),
            'ROUNDTRIP', 'complete boundary edge census')
    output_map = record['output_map']
    expected_outputs = []
    for source_id in selected:
        work.step()
        uses = [{'consumer_node_id': n['id'], 'ordered_index': i}
                for n in dag['nodes'] if n['id'] not in selected
                for i, ref in enumerate(n['ordered_inputs']) if ref == {'node': source_id}]
        labels = [p['id'] for p in dag['outputs'] if p['source'] == {'node': source_id}]
        if source_id == record['cut']['anchor'] or uses or labels:
            expected_outputs.append({'port_id': 'o'+str(len(expected_outputs)), 'source_node_id': source_id,
                                     'source_output_ids': labels, 'outgoing_uses': uses})
    require(canonical(output_map) == canonical(expected_outputs)
            and [v['port_id'] for v in output_map] == [v['port_id'] for v in expansion['outputs']],
            'ROUNDTRIP', 'complete ordered output/outgoing-use map')
    for item, output in zip(output_map, expansion['outputs']):
        work.step()
        source_id = item['source_node_id']
        require(source_id in step_ids and output['source'] == {'node': expanded[step_ids[source_id]]['id']}
                and output['formula'] == source_nodes[source_id]['formula'], 'ROUNDTRIP', 'full exposed output formula/source')
    return {'source_DAG_sha256': ascii_digest(dag), 'selected_node_ids': selected,
            'primitive_nodes_checked': len(selected), 'ordered_edges_checked': len(edges),
            'boundary_references_checked': len(boundary), 'outputs_checked': len(output_map),
            'source_origin_authenticated': False, 'source_proof_accepted': False}


def _constraints(expansion, anchor, branch_row, work):
    """Full24 row domains with only strict-prior and the actual anchor fixed."""
    ids = [('input', p['port_id']) for p in expansion['input_ports']]
    ids += [('node', n['id']) for n in expansion['primitive_nodes']]
    domains = {key: [0, 23] for key in ids}
    domains[('node', anchor)] = [branch_row, branch_row]
    edges = []
    for node in expansion['primitive_nodes']:
        for ref in node['ordered_inputs']:
            edges.append(((next(iter(ref)), next(iter(ref.values()))), ('node', node['id'])))
    # Each strict edge can move a bound at most23 times. Fixpoint, not a heuristic
    # row cap: every removed row violates an actual ordered primitive read.
    changed = True
    while changed:
        work.step(); changed = False
        for source, target in edges:
            low, high = domains[target][0], domains[source][1]
            new_low = max(low, domains[source][0]+1)
            new_high = min(high, domains[target][1]-1)
            if new_low != low:
                domains[target][0] = new_low; changed = True
            if new_high != high:
                domains[source][1] = new_high; changed = True
            if any(a > b for a, b in domains.values()):
                return None
    return domains


def build_family_batch(*, language, base_semantics, marked_semantics, producer,
                       expansion_checker, host_adapter, mined, state, decision,
                       tick, limits=None):
    """Offer fresh ordinary family instances; never restrict canonical fallback.

    Only own work-prefix exceptions are handled. Every injected/native/data/
    collision error propagates, including native rejection of a mined witness.
    The caller must supply a real engine-selected global BRANCH. This endpoint
    checks its literal shape, not scheduler authority.
    """
    work = _Work(tick, limits)
    instances, records, rejections, offers = [], [], [], []
    names, seen_instances, family_names = {}, set(), {}
    input_raw = None
    host = None
    checked_state = None
    original_state = None
    binding = None
    marking_id = None
    reason = 'LITERAL_GROUND_FINITE_PREFIX_ENDED'
    try:
        work.step()
        input_request = {'mined': mined, 'state': state, 'decision': decision}
        input_raw = canonical(input_request)
        binding = json.loads(canonical(language.binding))
        marking_id = state['marking_id']
        fields(decision, ('kind', 'row'), 'DECISION')
        require(decision['kind'] == 'BRANCH' and type(decision['row']) is int
                and 0 <= decision['row'] < 24, 'DECISION', 'actual BRANCH shape only')
        if len(input_raw.encode('utf8')) > work.limits['input_bytes']:
            raise _Unfinished('OWN_INPUT_BYTE_PREFIX')
        offered = work.copy(input_request)
        point = marked_semantics
        require(base_semantics.VERSION == 'independent-unit-row-missing-mark-degree-check-v2'
                and point.VERSION == POINT_VERSION and point.base is base_semantics
                and producer.VERSION == PRODUCER_VERSION
                and expansion_checker.VERSION == CHECKER_VERSION
                and host_adapter.VERSION == ADAPTER_VERSION, 'API', 'exact injected component versions')
        mined, state, decision = offered['mined'], offered['state'], offered['decision']
        binding = work.copy(language.binding)
        marking_id = state['marking_id']
        fields(decision, ('kind', 'row'), 'DECISION')
        require(decision['kind'] == 'BRANCH' and type(decision['row']) is int
                and 0 <= decision['row'] < 24, 'DECISION', 'actual BRANCH shape only')
        checked_state, totals, marks, selected, excluded, names = point.private_state(language, state, work.step)
        require(canonical(checked_state) == canonical(state) and totals[(0, decision['row'])] == 0,
                'STATE', 'full exact checked state and unoccupied actual branch row')
        original_state = point.base_state(language, state, work.step)
        originals = {r['translation'][1]: _key(r) for r in original_state['selected']}
        host = host_adapter.describe_host(language=language, tick=work.step)
        fields(mined, ('schema','version','status','request','families','cut_attempts','duplicate_cuts',
                       'mining_complete','work','reason','flags'), 'MINED')
        require(mined['schema'] == 'receptor-family-mining-prefix-v1'
                and mined['version'] == MINER_VERSION and mined['mining_complete'] is False
                and type(mined['families']) is list
                and mined['status'] == ('PROPOSALS' if mined['families'] else 'UNKNOWN'),
                'MINED', 'whole untrusted mining-prefix packet')
        if mined['request'] is None:
            require(mined['status'] == 'UNKNOWN' and mined['families'] == [], 'MINED', 'no partial unvalidated source request')
            raise _Unfinished('MINER_HAS_NO_VALIDATED_STRUCTURAL_REQUEST')
        require(canonical(mined['request']['host']) == canonical(host), 'HOST', 'same entire current original host')
        fields(mined['request'], ('host', 'derivation'), 'MINED')

        def reject(stage, reason_value, assignment, node_id=None, row=None, key=None):
            work.step()
            rejections.append({'stage': stage, 'reason': reason_value, 'record_index': active_record,
                'anchor_node': active_anchor, 'node_id': node_id, 'row': row,
                'assignment': [[list(k), v] for k, v in assignment.items()], 'placement_key': key,
                'scope': 'THIS_PHYSICAL_GROUND_ASSIGNMENT_ONLY', 'pruning_accepted': False})

        def literal_agrees(row, formula, current_marks):
            return (1, row) not in current_marks or current_marks[(1, row)] == ['formula', base_semantics.text(formula)]

        def physical_sharing(expansion, assignment):
            descriptors = {d['family_id']: d for d in active_registry}
            for frame in expansion['call_frames']:
                policy = {p['id']: p['sharing'] for p in descriptors[frame['family_id']]['inputs']}
                resolved = []
                for port in frame['inputs']:
                    work.step()
                    ref = port['source']; key = (next(iter(ref)), next(iter(ref.values())))
                    if key not in assignment:
                        continue
                    row = assignment[key]
                    for other_row, other_formula, other_policy in resolved:
                        if row == other_row and not (policy[port['port_id']] == other_policy == 'ALLOW_SAME_EXACT_PRIOR_SOURCE'
                                                     and port['formula'] == other_formula):
                            return False
                    resolved.append((row, port['formula'], policy[port['port_id']]))
            return True

        def offer(expansion, assignment, native_members):
            work.step()
            ports = {'hypotheses': work.copy(active_record_data['source_port_bindings']['hypotheses']),
                     'inputs': [], 'outputs': work.copy(active_record_data['source_port_bindings']['outputs'])}
            for port in expansion['input_ports']:
                row = assignment[('input', port['port_id'])]
                ports['inputs'].append({'port_id': port['port_id'], 'formula': work.copy(port['formula']),
                    'source': {'schema': SOURCE_SCHEMA, 'row': row, 'original_full_key': originals.get(row)},
                    'occupied': totals[(0, row)] == 1, 'fact_accepted': False})
            receptors = work.copy(ports)
            match = producer.match_family(registry=work.copy(active_registry), family_id=active_record_data['family_id'],
                host=work.copy(host), receptors=receptors,
                candidate_bindings=[work.copy(active_record_data['substitution'])], tick=work.step)
            matched = work.copy(match)
            record_observation['physical_matches'].append(matched)
            require(matched['schema'] == 'receptor-family-matching-prefix-v1'
                    and matched['version'] == PRODUCER_VERSION and matched['matching_complete'] is False,
                    'MATCH_PROTOCOL', 'fresh simultaneous all-port matching prefix')
            # A wholly grounded, independently checked environment and equal
            # receptor formulas must not be silently converted to an invalid-data gap.
            require(matched['rejected_bindings'] == [], 'MATCH_PROTOCOL', 'no masked ground binding rejection')
            if matched['status'] == 'UNKNOWN':
                require(matched['proposals'] == [], 'MATCH_PROTOCOL', 'UNKNOWN has no completed match')
                return
            require(matched['status'] == 'PROPOSALS' and len(matched['proposals']) == 1,
                    'MATCH_PROTOCOL', 'one explicit ground environment')
            proposal = matched['proposals'][0]
            checked = expansion_checker.check_expansion(registry=work.copy(active_registry),
                family_id=active_record_data['family_id'], host=work.copy(host),
                substitution=work.copy(active_record_data['substitution']), port_bindings=work.copy(ports),
                proposal=work.copy(proposal), tick=work.step)
            checked = work.copy(checked)
            record_observation['physical_checks'].append(checked)
            if not _ready_checked(checked, proposal):
                return
            row_assignment = {'schema': ROW_SCHEMA,
                'node_rows': [[n['id'], assignment[('node', n['id'])]] for n in expansion['primitive_nodes']],
                'input_rows': [[p['port_id'], assignment[('input', p['port_id'])]] for p in expansion['input_ports']]}
            instance = {'registry': work.copy(active_registry), 'family_id': active_record_data['family_id'],
                'host': work.copy(host), 'substitution': work.copy(active_record_data['substitution']),
                'port_bindings': ports, 'proposal': proposal, 'row_assignment': row_assignment}
            raw = canonical(instance)
            if raw in seen_instances:
                return
            adaptation = host_adapter.adapt_expansion(language=language, base_semantics=base_semantics,
                marked_semantics=point, expansion_checker=expansion_checker, **work.copy(instance),
                state=work.copy(state), tick=work.step)
            adaptation = work.copy(adaptation)
            record_observation['adaptations'].append(adaptation)
            require(adaptation['status'] in ('READY_LOCAL_CLUSTER', 'UNKNOWN'), 'ADAPT_PROTOCOL', 'whole native adapter result')
            if adaptation['status'] == 'UNKNOWN':
                return
            require(adaptation['local_member_membership_checked'] is True
                    and adaptation['local_point_union_checked'] is True
                    and adaptation['union_state_check']['marked_state_checked'] is True,
                    'ADAPT_PROTOCOL', 'fresh full native/marked union admission')
            require([m['tile']['placement_key'] for m in adaptation['members']] == native_members,
                    'ADAPT_PROTOCOL', 'same full preflight/native member key order')
            for member in adaptation['members']:
                point.check_collision(member['tile'], names)
            require(any(not m['already_selected_in_input'] and m['tile']['placement_key']['translation'] == [0, decision['row']]
                        for m in adaptation['members']), 'ANCHOR', 'actual BRANCH incident new primitive member')
            seen_instances.add(raw)
            instances.append(instance)
            offers.append({'instance_index': len(instances)-1, 'record_index': active_record,
                'anchor_node': active_anchor, 'adaptation_index': len(record_observation['adaptations'])-1,
                'fact_accepted': False})
            if len(instances) >= work.limits['instances']:
                raise _Unfinished('OWN_COMPLETED_INSTANCE_PREFIX')

        for active_record, active_record_data in enumerate(mined['families']):
            work.step()
            if active_record >= work.limits['records']:
                raise _Unfinished('OWN_RECORD_PREFIX')
            fields(active_record_data, ('schema','cut','descriptor','family_preimage','family_id','substitution',
                'source_port_bindings','source_node_map','boundary_source_map','abstraction_map',
                'boundary_edge_map','output_map','fragment_generalization','costs','flags'), 'EXTRACTION')
            require(active_record_data['schema'] == 'receptor-family-mined-extraction-v1', 'EXTRACTION', 'ordinary mined record')
            descriptor = active_record_data['descriptor']
            preimage = {k: v for k, v in descriptor.items() if k not in ('family_id','provenance')}
            require(descriptor['schema'] == 'receptor-lemma-family-v2'
                    and descriptor['dependencies'] == []
                    and all(s['kind'] == 'PRIMITIVE' for s in descriptor['body'])
                    and preimage == active_record_data['family_preimage']
                    and descriptor['family_id'] == active_record_data['family_id'] == ascii_digest(preimage),
                    'EXTRACTION', 'whole literal primitive-cut descriptor and full identity')
            fid, pre = descriptor['family_id'], canonical(preimage)
            require(fid not in family_names or family_names[fid] == pre, 'COLLISION', 'family full-preimage census')
            family_names[fid] = pre
            active_registry = [descriptor]
            ground = producer.expand_family(registry=work.copy(active_registry), family_id=fid, host=work.copy(host),
                substitution=work.copy(active_record_data['substitution']),
                port_bindings=work.copy(active_record_data['source_port_bindings']), tick=work.step)
            ground = work.copy(ground)
            record_observation = {'record_index': active_record, 'record': work.copy(active_record_data),
                'ground_proposal': ground, 'ground_check': None, 'roundtrip': None,
                'native_membership': [], 'anchors': [], 'physical_matches': [],
                'physical_checks': [], 'adaptations': []}
            records.append(record_observation)
            if ground['status'] == 'UNKNOWN':
                continue
            require(ground['status'] == 'READY_PROPOSAL', 'EXPAND_PROTOCOL', 'whole ground expansion status')
            checked = expansion_checker.check_expansion(registry=work.copy(active_registry), family_id=fid,
                host=work.copy(host), substitution=work.copy(active_record_data['substitution']),
                port_bindings=work.copy(active_record_data['source_port_bindings']), proposal=work.copy(ground), tick=work.step)
            checked = work.copy(checked); record_observation['ground_check'] = checked
            if not _ready_checked(checked, ground):
                continue
            expansion = checked['expansion']
            record_observation['roundtrip'] = _ground_roundtrip(active_record_data, mined, expansion, work)
            nodes = expansion['primitive_nodes']
            require(bool(nodes), 'EXTRACTION', 'nonempty primitive cut')
            if len(nodes) > 24:
                raise _Unfinished('OWN_EXPANDED_MEMBER_PREFIX')
            formulas = {('input', p['port_id']): p['formula'] for p in expansion['input_ports']}
            for node in nodes:
                work.step()
                premises = [formulas[(next(iter(ref)), next(iter(ref.values())))] for ref in node['ordered_inputs']]
                witness = {'rule': node['rule'], 'formula': work.copy(node['formula']), **work.copy(node['arguments'])}
                membership = language.primitive(witness, premises)
                record_observation['native_membership'].append({'node_id': node['id'], 'witness': witness,
                    'ordered_premise_formulas': work.copy(premises), 'membership': work.copy(membership)})
                formulas[('node', node['id'])] = node['formula']
            keys_in_order = [('input', p['port_id']) for p in expansion['input_ports']]
            keys_in_order += [('node', n['id']) for n in nodes]
            node_table = {n['id']: n for n in nodes}
            for active_anchor in [n['id'] for n in nodes]:
                work.step()
                domains = _constraints(expansion, active_anchor, decision['row'], work)
                record_observation['anchors'].append({'node_id': active_anchor, 'row': decision['row'],
                    'strict_prior_domains': None if domains is None else [[list(k), v] for k, v in domains.items()]})
                if domains is None:
                    continue

                def visit(index, assignment, local_t, local_m, local_selected, built, member_keys):
                    work.step()
                    if index == len(keys_in_order):
                        for key, row in assignment.items():
                            if not literal_agrees(row, formulas[key], local_m):
                                reject('FINAL_INTERFACE', 'literal_final_interface_mark_conflict', assignment, row=row)
                                return
                        offer(expansion, assignment, member_keys)
                        return
                    key = keys_in_order[index]
                    low, high = domains[key]
                    for row in range(low, high+1):
                        work.trial()
                        if not literal_agrees(row, formulas[key], local_m):
                            reject('PORT_OR_OUTPUT', 'literal_assigned_formula_mark_conflict', assignment, key[1], row)
                            continue
                        current = dict(assignment); current[key] = row
                        if not physical_sharing(expansion, current):
                            reject('SHARING', 'physical_call_input_sharing_policy', current, key[1], row)
                            continue
                        if key[0] == 'input':
                            visit(index+1, current, local_t, local_m, local_selected, built, member_keys)
                            continue
                        node = node_table[key[1]]
                        refs = [(next(iter(r)), next(iter(r.values()))) for r in node['ordered_inputs']]
                        reads = [current[r] for r in refs]
                        if any(r >= row for r in reads):
                            reject('ORDERED_READS', 'strict_earlier_row', current, key[1], row)
                            continue
                        required_marks = {}
                        conflict = False
                        for rkey, rrow in [(key, row)] + list(zip(refs, reads)):
                            value = ['formula', base_semantics.text(formulas[rkey])]
                            if ((1, rrow) in required_marks and required_marks[(1, rrow)] != value
                                    or (1, rrow) in local_m and local_m[(1, rrow)] != value):
                                conflict = True; break
                            required_marks[(1, rrow)] = value
                        if conflict:
                            reject('ORDERED_READS', 'literal_repeated_or_remote_formula_mark_conflict', current, key[1], row)
                            continue
                        witness = {'rule': node['rule'], 'formula': work.copy(node['formula']), **work.copy(node['arguments'])}
                        preimage = {'input_epoch': language.binding['language_epoch'], 'primitive_witness': witness,
                            'ordered_premise_formulas': [work.copy(formulas[r]) for r in refs],
                            'ordered_offsets': [r-row for r in reads]}
                        tile = point.rebuild_tile(language, {'schema': 'unit-row-row0-decorated-type-v1',
                            'base_type_preimage': preimage, 'marking_id': marking_id}, [0,row], work.step)
                        point.check_collision(tile, names)
                        rawkey = base_semantics.text(tile['placement_key'])
                        if rawkey in built:
                            require(canonical(tile) == canonical(built[rawkey]), 'COLLISION', 'shared full placement packet')
                            visit(index+1, current, local_t, local_m, local_selected, built, member_keys)
                            continue
                        legality = point.legality(tile, local_t, local_m, local_selected, excluded)
                        if legality == 'already_selected':
                            require(rawkey in selected, 'POINT_PROTOCOL', 'only exact original selected member reuse')
                        elif legality is not None:
                            require(legality in LEGAL_REASONS, 'POINT_PROTOCOL', 'explicit ordinary legality result')
                            reject('POINT', legality, current, key[1], row, tile['placement_key'])
                            continue
                        new_t, new_m, new_selected, new_built = dict(local_t), dict(local_m), set(local_selected), dict(built)
                        if legality is None:
                            for p, value in tile['global_t_values']:
                                new_t[tuple(p)] = new_t.get(tuple(p),0)+value
                            for p, value in tile['global_m_values']:
                                point.agree(new_m, tuple(p), value)
                            new_selected.add(rawkey)
                        new_built[rawkey] = tile
                        visit(index+1, current, new_t, new_m, new_selected, new_built, member_keys+[tile['placement_key']])

                visit(0, {}, dict(totals), dict(marks), set(selected), {}, [])
    except _CallbackFailure as error:
        raise error.error
    except _Unfinished as error:
        reason = str(error)
    # No native/resource exception is handled here. Final assembly is bounded by
    # the already copied input/finite prefix and remains charged to the same tick.
    try:
        work.native()
        require(input_raw is not None and canonical(input_request) == input_raw,
                'STABILITY', 'whole caller input unchanged')
        require(binding is not None and canonical(language.binding) == canonical(binding),
                'STABILITY', 'same complete original language binding')
        if host is not None:
            require(canonical(host_adapter.describe_host(language=language, tick=work.native)) == canonical(host),
                    'STABILITY', 'full original host authority unchanged')
        if checked_state is not None:
            require(canonical(state) == canonical(checked_state), 'STABILITY', 'whole entry checked state unchanged')
        # The result must always meet the consumer wire, including own-prefix
        # UNKNOWN before point checking. In that case use the original literal
        # state/decision/binding only; no instance or checked-state claim exists.
        batch = {'schema': BATCH_SCHEMA, 'status': 'READY' if instances else 'UNKNOWN',
            'binding': json.loads(canonical(binding)), 'marking_id': marking_id,
            'state_sha256': digest(input_request['state']),
            'decision': json.loads(canonical(input_request['decision'])), 'instances': instances}
        report = {'schema': RESULT_SCHEMA, 'version': VERSION, 'batch': batch,
            'request': json.loads(input_raw), 'host': host, 'original_state': original_state,
            'checked_state': checked_state, 'records': records, 'row_rejections': rejections,
            'offers': offers, 'prototype_census': [[k,v] for k,v in sorted(names.items())],
            'reason': reason, 'work': {'steps': work.steps, 'row_trials': work.trials,
                'limits': dict(work.limits), 'completed_instances': len(instances)},
            'scope': 'LITERAL_GROUND_ORDERING_PREFIX_ONLY', 'flags': dict(FLAGS)}
        work.native()
        return {'batch': batch, 'report': report}
    except _CallbackFailure as error:
        raise error.error
