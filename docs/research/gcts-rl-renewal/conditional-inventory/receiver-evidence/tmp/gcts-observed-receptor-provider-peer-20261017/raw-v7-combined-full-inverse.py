"""SOURCE ONLY: bounded current-receptor transfer of mined primitive families.

The caller authenticates all injected Sources and original Source17/input2.
Source-ground evidence is separate from freshly checked current instantiations.
No engine, search, degree, cursor, clock, saved result or project import exists.
A finite advisory prefix never restricts native candidate domains or fallback.
"""
import hashlib
import json

VERSION = 'receptor-family-visible-receptor-transfer-provider-v3'
RESULT_SCHEMA = 'receptor-family-receptor-transfer-provider-v1'
BATCH_SCHEMA = 'receptor-family-primitive-preference-batch-v1'
MINER_VERSION = 'receptor-family-primitive-DAG-miner-v2-connected-cut-selection'
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


def _layout(expansion, work):
    """Topology only, not origin formulas, witnesses or current proof authority."""
    work.step()
    return {'nodes': [{k: work.copy(n[k]) for k in ('id', 'rule', 'ordered_inputs', 'origin')}
                      for n in expansion['primitive_nodes']],
            'inputs': [p['port_id'] for p in expansion['input_ports']],
            'outputs': [{'port_id': p['port_id'], 'source': work.copy(p['source'])}
                        for p in expansion['outputs']]}


def _preflight(expansion, assignment, language, base, point, state_parts, names, work):
    """Fresh full transferred primitive/point checks; only exact conflicts abstain."""
    totals, marks, selected, excluded = state_parts
    local_t, local_m, local_selected = dict(totals), dict(marks), set(selected)
    formulas = {('input', p['port_id']): p['formula'] for p in expansion['input_ports']}
    built, tiles, memberships, member_keys = {}, [], [], []
    result = {'status': 'INCOMPATIBLE_ASSIGNMENT', 'reason': None, 'node_id': None,
              'row': None, 'membership': memberships, 'tiles': tiles, 'member_keys': member_keys}
    for node in expansion['primitive_nodes']:
        work.step()
        key = ('node', node['id']); row = assignment[key]
        refs = [(next(iter(r)), next(iter(r.values()))) for r in node['ordered_inputs']]
        reads = [assignment[r] for r in refs]
        require(all(r < row for r in reads), 'LAYOUT', 'checked strict-prior structural assignment')
        premises = [work.copy(formulas[r]) for r in refs]
        witness = {'rule': node['rule'], 'formula': work.copy(node['formula']), **work.copy(node['arguments'])}
        # Native rejection is NOT caught as an advisory mismatch.
        membership = language.primitive(witness, premises)
        memberships.append({'node_id': node['id'], 'witness': witness,
                            'ordered_premise_formulas': premises, 'membership': work.copy(membership)})
        required_marks = {}
        for rrow, formula in [(row, node['formula'])] + list(zip(reads, premises)):
            value = ['formula', base.text(formula)]
            if ((1, rrow) in required_marks and required_marks[(1, rrow)] != value
                    or (1, rrow) in local_m and local_m[(1, rrow)] != value):
                result.update(reason='literal_repeated_or_remote_formula_mark_conflict',
                              node_id=node['id'], row=row)
                return result
            required_marks[(1, rrow)] = value
        pre = {'input_epoch': language.binding['language_epoch'], 'primitive_witness': witness,
               'ordered_premise_formulas': premises, 'ordered_offsets': [r-row for r in reads]}
        tile = point.rebuild_tile(language, {'schema': 'unit-row-row0-decorated-type-v1',
            'base_type_preimage': pre, 'marking_id': point.marking_id}, [0, row], work.step)
        # Includes removed/failed alternatives; never merge their point unions.
        point.check_collision(tile, names)
        tiles.append(work.copy(tile))
        formulas[key] = node['formula']
        rawkey = base.text(tile['placement_key'])
        if rawkey in built:
            require(canonical(tile) == canonical(built[rawkey]), 'COLLISION', 'shared full placement packet')
            continue
        legality = point.legality(tile, local_t, local_m, local_selected, excluded)
        if legality == 'already_selected':
            require(rawkey in selected, 'POINT_PROTOCOL', 'only exact current selected member reuse')
        elif legality is not None:
            require(legality in LEGAL_REASONS, 'POINT_PROTOCOL', 'explicit ordinary legality result')
            result.update(reason=legality, node_id=node['id'], row=row)
            return result
        else:
            for p, value in tile['global_t_values']:
                local_t[tuple(p)] = local_t.get(tuple(p), 0) + value
            for p, value in tile['global_m_values']:
                point.agree(local_m, tuple(p), value)
            local_selected.add(rawkey)
        built[rawkey] = tile
        member_keys.append(work.copy(tile['placement_key']))
    for key, row in assignment.items():
        work.step()
        if ((1, row) in local_m and
                local_m[(1, row)] != ['formula', base.text(formulas[key])]):
            result.update(reason='literal_final_interface_mark_conflict', node_id=key[1], row=row)
            return result
    result.update(status='CHECKED_ASSIGNMENT')
    return result


def build_family_batch(*, language, base_semantics, marked_semantics, producer,
                       expansion_checker, host_adapter, mined, state, decision,
                       tick, limits=None, matching_mode='VISIBLE_RECEPTOR'):
    """Joint current-receptor transfer, or its explicit literal-environment ablation.

    A real engine-selected BRANCH is required externally; this endpoint checks
    its shape, full state and current output, not global scheduler authority.
    Own prefixes/matcher residuals never restrict native domains or fallback.
    """
    require(type(matching_mode) is str and matching_mode in ('VISIBLE_RECEPTOR', 'LITERAL_GROUND'),
            'MATCHING_MODE', 'explicit current-receptor or literal matched control')
    work = _Work(tick, limits)
    instances, records, rejections, offers = [], [], [], []
    names, seen_instances, family_names = {}, set(), {}
    input_raw = None
    host = checked_state = original_state = binding = marking_id = branch_formula = None
    reason = 'FINITE_RECEPTOR_ASSIGNMENT_PREFIX_ENDED'
    try:
        work.step()
        input_request = {'mined': mined, 'state': state, 'decision': decision, 'matching_mode': matching_mode}
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
            require(mined['status'] == 'UNKNOWN' and mined['families'] == [], 'MINED', 'no partial source request')
            raise _Unfinished('MINER_HAS_NO_VALIDATED_STRUCTURAL_REQUEST')
        fields(mined['request'], ('host', 'derivation'), 'MINED')
        require(canonical(mined['request']['host']) == canonical(host), 'HOST', 'same entire original host')
        row_formulas = {r: base_semantics.formula_at(language, marks, r, work.step) for r in range(24)}
        branch_formula = row_formulas[decision['row']]
        if branch_formula is None:
            raise _Unfinished('NO_ASSIGNED_BRANCH_OUTPUT_RECEPTOR')

        def reject(stage, detail, assignment, record_index, output_id, extra=None):
            work.step()
            rejections.append({'stage': stage, 'reason': detail, 'record_index': record_index,
                'output_port': output_id, 'assignment': [[list(k), v] for k, v in assignment.items()],
                'detail': extra, 'scope': 'THIS_ADVISORY_ASSIGNMENT_ONLY', 'pruning_accepted': False})

        for record_index, record in enumerate(mined['families']):
            work.step()
            if record_index >= work.limits['records']:
                raise _Unfinished('OWN_RECORD_PREFIX')
            fields(record, ('schema','cut','descriptor','family_preimage','family_id','substitution',
                'source_port_bindings','source_node_map','boundary_source_map','abstraction_map',
                'boundary_edge_map','output_map','fragment_generalization','costs','flags'), 'EXTRACTION')
            require(record['schema'] == 'receptor-family-mined-extraction-v1', 'EXTRACTION', 'ordinary mined record')
            descriptor = record['descriptor']
            preimage = {k: v for k, v in descriptor.items() if k not in ('family_id','provenance')}
            require(descriptor['schema'] == 'receptor-lemma-family-v2'
                    and descriptor['dependencies'] == []
                    and all(s['kind'] == 'PRIMITIVE' for s in descriptor['body'])
                    and preimage == record['family_preimage']
                    and descriptor['family_id'] == record['family_id'] == ascii_digest(preimage),
                    'EXTRACTION', 'whole primitive-cut descriptor/preimage identity')
            fid, pre = descriptor['family_id'], canonical(preimage)
            require(fid not in family_names or family_names[fid] == pre, 'COLLISION', 'family full-preimage census')
            family_names[fid] = pre
            registry = [descriptor]
            ground = producer.expand_family(registry=work.copy(registry), family_id=fid, host=work.copy(host),
                substitution=work.copy(record['substitution']),
                port_bindings=work.copy(record['source_port_bindings']), tick=work.step)
            ground = work.copy(ground)
            observation = {'record_index': record_index, 'record': work.copy(record),
                'source_ground_proposal': ground, 'source_ground_check': None,
                'source_roundtrip': None, 'source_native_membership': [],
                'anchors': [], 'matches': [], 'checks': [], 'preflights': [], 'adaptations': []}
            records.append(observation)
            if ground['status'] == 'UNKNOWN':
                continue
            require(ground['status'] == 'READY_PROPOSAL', 'EXPAND_PROTOCOL', 'whole source-ground expansion')
            checked = expansion_checker.check_expansion(registry=work.copy(registry), family_id=fid,
                host=work.copy(host), substitution=work.copy(record['substitution']),
                port_bindings=work.copy(record['source_port_bindings']), proposal=work.copy(ground), tick=work.step)
            checked = work.copy(checked); observation['source_ground_check'] = checked
            if not _ready_checked(checked, ground):
                continue
            layout_origin = checked['expansion']
            observation['source_roundtrip'] = _ground_roundtrip(record, mined, layout_origin, work)
            nodes = layout_origin['primitive_nodes']
            require(bool(nodes), 'EXTRACTION', 'nonempty primitive cut')
            if len(nodes) > 24:
                raise _Unfinished('OWN_EXPANDED_MEMBER_PREFIX')
            # Origin-native checking authenticates a conditional primitive relation,
            # never the generating search/proof and never a transferred environment.
            source_formulas = {('input', p['port_id']): p['formula'] for p in layout_origin['input_ports']}
            for node in nodes:
                work.step()
                premises = [work.copy(source_formulas[(next(iter(r)), next(iter(r.values())))])
                            for r in node['ordered_inputs']]
                witness = {'rule': node['rule'], 'formula': work.copy(node['formula']), **work.copy(node['arguments'])}
                member = language.primitive(witness, premises)
                observation['source_native_membership'].append({'node_id': node['id'], 'witness': witness,
                    'ordered_premise_formulas': premises, 'membership': work.copy(member)})
                source_formulas[('node', node['id'])] = node['formula']
            layout_shape = _layout(layout_origin, work)
            keys = [('input', p['port_id']) for p in layout_origin['input_ports']]
            keys += [('node', n['id']) for n in nodes]
            node_table = {n['id']: n for n in nodes}
            input_policy = {p['id']: p['sharing'] for p in descriptor['inputs']}
            hypotheses = []
            for p in layout_origin['hypothesis_ports']:
                index = p['gamma_index']
                require(type(index) is int and 0 <= index < len(host['ordered_Gamma']), 'GAMMA', 'original occurrence')
                hypotheses.append({'port_id': p['port_id'], 'gamma_index': index,
                                   'formula': work.copy(host['ordered_Gamma'][index])})

            for output in layout_origin['outputs']:
                work.step()
                fields(output['source'], ('node',), 'ANCHOR')
                anchor = output['source']['node']
                require(anchor in node_table, 'ANCHOR', 'actual exposed primitive output')
                domains = _constraints(layout_origin, anchor, decision['row'], work)
                observation['anchors'].append({'output_port': output['port_id'], 'node_id': anchor,
                    'row': decision['row'], 'current_formula': work.copy(branch_formula),
                    'strict_prior_domains': None if domains is None else [[list(k), v] for k, v in domains.items()]})
                if domains is None:
                    continue

                def complete(assignment):
                    work.step()
                    ports = {'hypotheses': work.copy(hypotheses), 'inputs': [], 'outputs': []}
                    for port in layout_origin['input_ports']:
                        row = assignment[('input', port['port_id'])]
                        require(row_formulas[row] is not None, 'RECEPTOR', 'only assigned current input formulas')
                        ports['inputs'].append({'port_id': port['port_id'], 'formula': work.copy(row_formulas[row]),
                            'source': {'schema': SOURCE_SCHEMA, 'row': row, 'original_full_key': work.copy(originals.get(row))},
                            'occupied': totals[(0, row)] == 1, 'fact_accepted': False})
                    for port in layout_origin['outputs']:
                        row = assignment[('node', port['source']['node'])]
                        if row_formulas[row] is not None:
                            ports['outputs'].append({'port_id': port['port_id'], 'formula': work.copy(row_formulas[row])})
                    require(any(p['port_id'] == output['port_id'] and p['formula'] == branch_formula
                                for p in ports['outputs']), 'RECEPTOR', 'actual output receptor included jointly')
                    initial = {} if matching_mode == 'VISIBLE_RECEPTOR' else work.copy(record['substitution'])
                    match = producer.match_family(registry=work.copy(registry), family_id=fid, host=work.copy(host),
                        receptors=work.copy(ports), candidate_bindings=[initial], tick=work.step)
                    match = work.copy(match)
                    attempt = {'output_port': output['port_id'], 'assignment': [[list(k), v] for k, v in assignment.items()],
                        'receptors': work.copy(ports), 'initial_binding': initial,
                        'origin_binding_used_as_initializer': matching_mode == 'LITERAL_GROUND', 'match': match}
                    observation['matches'].append(attempt)
                    require(match['schema'] == 'receptor-family-matching-prefix-v1' and match['version'] == PRODUCER_VERSION
                            and match['matching_complete'] is False and type(match['binding_attempts']) is int
                            and 0 <= match['binding_attempts'] <= 1, 'MATCH_PROTOCOL', 'one finite joint binding attempt')
                    for rejected in match['rejected_bindings']:
                        require(rejected['code'] in ('PORT_MISMATCH', 'OUTPUT_MISMATCH', 'UNBOUND_UNKNOWN'),
                                'MATCH_REJECTION', 'unexpected data/scope/authority rejection is not an advisory mismatch')
                    if match['status'] == 'UNKNOWN':
                        require(match['proposals'] == [], 'MATCH_PROTOCOL', 'UNKNOWN has no completed expansion')
                        reject('MATCH', 'UNRESOLVED_OR_MISMATCHED_RECEPTORS', assignment,
                               record_index, output['port_id'], work.copy(match['rejected_bindings']))
                        return
                    require(match['status'] == 'PROPOSALS' and match['rejected_bindings'] == []
                            and len(match['proposals']) == 1, 'MATCH_PROTOCOL', 'one complete inferred expansion')
                    proposal = match['proposals'][0]
                    require(proposal['status'] == 'READY_PROPOSAL' and proposal['family_id'] == fid
                            and canonical(proposal['request']['registry']) == canonical(registry)
                            and canonical(proposal['request']['host']) == canonical(host)
                            and canonical(proposal['request']['port_bindings']) == canonical(ports),
                            'MATCH_PROTOCOL', 'full current request bound to inferred proposal')
                    env = work.copy(proposal['request']['substitution'])
                    require(type(env) is dict and set(env) == {p['id'] for p in descriptor['parameters']},
                            'MATCH_PROTOCOL', 'fully ground simultaneous substitution')
                    if matching_mode == 'LITERAL_GROUND':
                        require(canonical(env) == canonical(record['substitution']), 'MATCH_PROTOCOL', 'literal ablation environment')
                    attempt['inferred_substitution'] = work.copy(env)
                    attempt['nonidentity_transfer'] = canonical(env) != canonical(record['substitution'])
                    independent = expansion_checker.check_expansion(registry=work.copy(registry), family_id=fid,
                        host=work.copy(host), substitution=work.copy(env), port_bindings=work.copy(ports),
                        proposal=work.copy(proposal), tick=work.step)
                    independent = work.copy(independent); observation['checks'].append(independent)
                    if not _ready_checked(independent, proposal):
                        return
                    current = independent['expansion']
                    require(canonical(_layout(current, work)) == canonical(layout_shape),
                            'LAYOUT', 'same fixed primitive topology; origin formulas are not constraints')
                    preflight = _preflight(current, assignment, language, base_semantics, point,
                                           (totals, marks, selected, excluded), names, work)
                    observation['preflights'].append(preflight)
                    if preflight['status'] == 'INCOMPATIBLE_ASSIGNMENT':
                        reject('POINT', preflight['reason'], assignment, record_index, output['port_id'],
                               {'node_id': preflight['node_id'], 'row': preflight['row']})
                        return
                    require(preflight['status'] == 'CHECKED_ASSIGNMENT', 'POINT_PROTOCOL', 'complete native preflight')
                    row_assignment = {'schema': ROW_SCHEMA,
                        'node_rows': [[n['id'], assignment[('node', n['id'])]] for n in current['primitive_nodes']],
                        'input_rows': [[p['port_id'], assignment[('input', p['port_id'])]] for p in current['input_ports']]}
                    instance = {'registry': work.copy(registry), 'family_id': fid, 'host': work.copy(host),
                        'substitution': env, 'port_bindings': ports, 'proposal': proposal, 'row_assignment': row_assignment}
                    raw = canonical(instance)
                    if raw in seen_instances:
                        return
                    adaptation = host_adapter.adapt_expansion(language=language, base_semantics=base_semantics,
                        marked_semantics=point, expansion_checker=expansion_checker, **work.copy(instance),
                        state=work.copy(state), tick=work.step)
                    adaptation = work.copy(adaptation); observation['adaptations'].append(adaptation)
                    require(adaptation['status'] in ('READY_LOCAL_CLUSTER', 'UNKNOWN'), 'ADAPT_PROTOCOL', 'native adapter result')
                    if adaptation['status'] == 'UNKNOWN':
                        return
                    require(adaptation['local_member_membership_checked'] is True
                            and adaptation['local_point_union_checked'] is True
                            and adaptation['union_state_check']['marked_state_checked'] is True,
                            'ADAPT_PROTOCOL', 'fresh complete membership and marked union')
                    require([m['tile']['placement_key'] for m in adaptation['members']] == preflight['member_keys'],
                            'ADAPT_PROTOCOL', 'same full preflight/native member order')
                    for member in adaptation['members']:
                        point.check_collision(member['tile'], names)
                    require(any(not m['already_selected_in_input'] and m['tile']['placement_key']['translation'] == [0, decision['row']]
                                for m in adaptation['members']), 'ANCHOR', 'new legal primitive at current BRANCH')
                    seen_instances.add(raw); instances.append(instance)
                    offers.append({'instance_index': len(instances)-1, 'record_index': record_index,
                        'output_port': output['port_id'], 'match_index': len(observation['matches'])-1,
                        'adaptation_index': len(observation['adaptations'])-1,
                        'inferred_substitution': work.copy(env), 'nonidentity_transfer': attempt['nonidentity_transfer'],
                        'fact_accepted': False})
                    if len(instances) >= work.limits['instances']:
                        raise _Unfinished('OWN_COMPLETED_INSTANCE_PREFIX')

                def visit(index, assignment):
                    work.step(index)
                    if index == len(keys):
                        complete(assignment)
                        return
                    key = keys[index]; low, high = domains[key]
                    for row in range(low, high+1):
                        work.trial()
                        current = dict(assignment); current[key] = row
                        if key[0] == 'input':
                            if row_formulas[row] is None:
                                reject('INPUT_RECEPTOR', 'ABSENT_FORMULA_UNRESOLVED', current, record_index, output['port_id'])
                                continue
                            incompatible = False
                            for other, other_row in assignment.items():
                                if other[0] == 'input' and other_row == row:
                                    if not (input_policy[key[1]] == input_policy[other[1]] == 'ALLOW_SAME_EXACT_PRIOR_SOURCE'):
                                        incompatible = True; break
                            if incompatible:
                                reject('SHARING', 'physical_root_input_sharing_policy', current, record_index, output['port_id'])
                                continue
                        else:
                            refs = [(next(iter(r)), next(iter(r.values()))) for r in node_table[key[1]]['ordered_inputs']]
                            if any(current[r] >= row for r in refs):
                                reject('ORDERED_READS', 'strict_earlier_row', current, record_index, output['port_id'])
                                continue
                        visit(index+1, current)

                visit(0, {})
    except _CallbackFailure as error:
        raise error.error
    except _Unfinished as error:
        reason = str(error)
    try:
        work.native()
        require(input_raw is not None and canonical(input_request) == input_raw,
                'STABILITY', 'whole caller input/mode unchanged')
        require(binding is not None and canonical(language.binding) == canonical(binding),
                'STABILITY', 'same complete original binding')
        if host is not None:
            require(canonical(host_adapter.describe_host(language=language, tick=work.native)) == canonical(host),
                    'STABILITY', 'full original host authority unchanged')
        if checked_state is not None:
            require(canonical(state) == canonical(checked_state), 'STABILITY', 'whole entry state unchanged')
        batch = {'schema': BATCH_SCHEMA, 'status': 'READY' if instances else 'UNKNOWN',
            'binding': json.loads(canonical(binding)), 'marking_id': marking_id,
            'state_sha256': digest(input_request['state']),
            'decision': json.loads(canonical(input_request['decision'])), 'instances': instances}
        report = {'schema': RESULT_SCHEMA, 'version': VERSION, 'matching_mode': matching_mode, 'batch': batch,
            'request': json.loads(input_raw), 'host': host, 'original_state': original_state,
            'checked_state': checked_state, 'branch_output_receptor': branch_formula,
            'records': records, 'row_rejections': rejections, 'offers': offers,
            'prototype_census': [[k, v] for k, v in sorted(names.items())],
            'reason': reason, 'work': {'steps': work.steps, 'row_trials': work.trials,
                'limits': dict(work.limits), 'completed_instances': len(instances)},
            'scope': 'CURRENT_RECEPTOR_GROUND_ORDERING_PREFIX_ONLY', 'flags': dict(FLAGS)}
        work.native()
        return {'batch': batch, 'report': report}
    except _CallbackFailure as error:
        raise error.error
