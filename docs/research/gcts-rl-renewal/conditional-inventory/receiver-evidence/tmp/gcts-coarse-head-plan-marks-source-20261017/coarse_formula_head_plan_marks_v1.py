"""Coarse descriptor-head markings for one advisory physical cluster plan.

No project imports, inference, source substitution, native state or proof checks.
A completed known conflict rejects this proposed layout only. Every pass/UNKNOWN
still requires full expansion, independent checking and native point validation.
"""
import hashlib
import json

VERSION = 'receptor-family-coarse-formula-head-plan-marks-v1'
SCHEMA = 'receptor-family-coarse-head-plan-check-v1'
DESCRIPTOR_SCHEMA = 'receptor-lemma-family-v2'
ROW_SCHEMA = 'receptor-family-six-rule-row-assignment-v1'
CHANNEL = 5
HEADS = ('bot', 'pred', 'eq', 'all', 'not', 'imp', 'and', 'or')
DEFAULT_LIMITS = {'work': 100000, 'depth': 128, 'input_bytes': 1048576,
                  'requirements': 4096}
FLAGS = {'advisory_cluster_plan_only': True, 'native_validation_required': True,
         'native_state_modified': False, 'native_membership_accepted': False,
         'point_union_accepted': False, 'base_candidate_pruning_accepted': False,
         'degree_or_EOF_accepted': False, 'engine_activated': False,
         'proof_accepted': False, 'universal_lemma_accepted': False,
         'runtime_qualified': False, 'speedup_claimed': False}


class PlanHeadError(ValueError):
    """Malformed input/protocol data; never an advisory conflict result."""
    def __init__(self, code, detail):
        self.code = code
        super().__init__('coarse plan heads ' + code + ': ' + detail)


class _Unfinished(Exception):
    pass


class _CallbackFailure(BaseException):
    def __init__(self, error):
        self.error = error


def require(ok, code, detail):
    if not ok:
        raise PlanHeadError(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def fields(value, keys):
    require(type(value) is dict and set(value) == set(keys), 'FIELDS', 'exact object fields')


def ident(value):
    require(type(value) is str and bool(value), 'IDENTIFIER', 'nonempty literal identifier')
    return value


class _Work:
    def __init__(self, tick, limits):
        require(callable(tick), 'TICK', 'caller-owned tick required')
        self.tick, self.steps = tick, 0
        self.limits = dict(DEFAULT_LIMITS)
        if limits is not None:
            require(type(limits) is dict and set(limits) <= set(self.limits), 'LIMITS', 'known fields')
            for key, value in limits.items():
                require(type(value) is int and 0 < value <= DEFAULT_LIMITS[key],
                        'LIMITS', 'positive bounded literal integer')
                self.limits[key] = value

    def step(self, depth=0):
        if self.steps >= self.limits['work'] or depth > self.limits['depth']:
            raise _Unfinished('OWN_WORK_OR_DEPTH_PREFIX')
        try:
            self.tick()
        except BaseException as error:
            raise _CallbackFailure(error) from error
        self.steps += 1

    def copy(self, value, depth=0):
        self.step(depth)
        if value is None or type(value) in (bool, int, str):
            if type(value) is str and len(value) > self.limits['input_bytes']:
                raise _Unfinished('OWN_INPUT_BYTE_PREFIX')
            return value
        if type(value) is list:
            return [self.copy(v, depth + 1) for v in value]
        require(type(value) is dict and all(type(k) is str for k in value),
                'JSON', 'strict builtin literal JSON only')
        return {k: self.copy(v, depth + 1) for k, v in value.items()}


def _formula_head(template, work):
    """Only the template's literal outer constructor, never an environment."""
    work.step()
    require(type(template) is dict and type(template.get('node')) is str,
            'TEMPLATE', 'formula template object')
    tag = template['node']
    if tag == 'formula_meta':
        fields(template, ('node', 'parameter', 'arguments'))
        ident(template['parameter'])
        require(type(template['arguments']) is list, 'TEMPLATE', 'meta arguments')
        return None
    expected = {'bot': ('node',), 'pred': ('node', 'symbol', 'arguments'),
                'eq': ('node', 'left', 'right'), 'all': ('node', 'binder_id', 'body'),
                'not': ('node', 'body'), 'imp': ('node', 'left', 'right'),
                'and': ('node', 'left', 'right'), 'or': ('node', 'left', 'right')}
    require(tag in expected, 'TEMPLATE', 'known formula outer constructor')
    fields(template, expected[tag])
    # Full typed children/arity/scope validation remains mandatory downstream.
    # For every valid such instantiation the concrete outer tag is unchanged.
    return tag


def _row_map(entries, ids, work):
    require(type(entries) is list, 'ASSIGNMENT', 'ordered row pairs')
    result = {}
    for pair in entries:
        work.step()
        require(type(pair) is list and len(pair) == 2 and type(pair[0]) is str
                and pair[0] not in result and type(pair[1]) is int and 0 <= pair[1] < 24,
                'ASSIGNMENT', 'unique original24row literal assignment')
        result[pair[0]] = pair[1]
    require(set(result) == set(ids), 'ASSIGNMENT', 'every exact node/input assigned once')
    return result


def _supported_requirements(descriptor, shape, assignment, work):
    """Full supported topology join before any conflict can be returned."""
    fields(descriptor, ('schema', 'family_id', 'origin', 'provenance', 'required_host_features',
                       'parameters', 'hypotheses', 'inputs', 'outputs', 'body',
                       'side_conditions', 'dependencies'))
    require(descriptor['schema'] == DESCRIPTOR_SCHEMA, 'DESCRIPTOR', 'descriptorV2')
    preimage = {k: v for k, v in descriptor.items() if k not in ('family_id', 'provenance')}
    require(descriptor['family_id'] == hashlib.sha256(canonical(preimage)).hexdigest(),
            'IDENTITY', 'whole original ASCII descriptor preimage')
    for key in ('hypotheses', 'inputs', 'outputs', 'body', 'dependencies'):
        require(type(descriptor[key]) is list, 'DESCRIPTOR', 'ordered descriptor lists')
    fields(shape, ('nodes', 'inputs', 'outputs'))
    require(all(type(shape[k]) is list for k in shape), 'LAYOUT', 'flat ordered lists')
    fields(assignment, ('schema', 'node_rows', 'input_rows'))
    require(assignment['schema'] == ROW_SCHEMA, 'ASSIGNMENT', 'existing native adapter row wire')
    if descriptor['dependencies'] or descriptor['hypotheses']:
        return None, 'UNSUPPORTED_CALL_OR_MATERIALIZED_HYPOTHESIS'
    if any(type(s) is not dict or s.get('kind') != 'PRIMITIVE' for s in descriptor['body']):
        return None, 'UNSUPPORTED_NONPRIMITIVE_BODY'
    for node in shape['nodes']:
        fields(node, ('id', 'rule', 'ordered_inputs', 'origin'))
        fields(node['origin'], ('family_id', 'call_path', 'step_id', 'hypothesis_port', 'gamma_index'))
        if node['origin']['call_path'] != [] or node['origin']['hypothesis_port'] is not None:
            return None, 'UNSUPPORTED_CALL_OR_MATERIALIZED_HYPOTHESIS'
    inputs, steps, outputs = {}, {}, {}
    for index, port in enumerate(descriptor['inputs']):
        work.step(); fields(port, ('id', 'formula', 'ordered_role', 'sharing'))
        pid = ident(port['id']); require(pid not in inputs, 'PORT', 'unique input IDs')
        inputs[pid] = (port['formula'], ['inputs', index, 'formula'])
    for index, step in enumerate(descriptor['body']):
        work.step(); fields(step, ('id', 'kind', 'rule', 'formula', 'ordered_inputs', 'arguments'))
        sid = ident(step['id']); require(sid not in steps, 'BODY', 'unique primitive step IDs')
        require(type(step['ordered_inputs']) is list, 'REFERENCE', 'ordered primitive reads')
        steps[sid] = (step, ['body', index, 'formula'])
    for index, output in enumerate(descriptor['outputs']):
        work.step(); fields(output, ('id', 'formula', 'source'))
        pid = ident(output['id']); require(pid not in outputs, 'PORT', 'unique output IDs')
        outputs[pid] = (output, ['outputs', index, 'formula'])
    require(bool(outputs), 'PORT', 'nonempty exposed outputs')
    require(shape['inputs'] == list(inputs), 'LAYOUT', 'exact ordered root input IDs')
    nodes, step_to_node = {}, {}
    for node in shape['nodes']:
        work.step(); nid = ident(node['id']); origin = node['origin']; sid = origin['step_id']
        require(nid not in nodes and type(sid) is str and sid in steps and sid not in step_to_node,
                'LAYOUT', 'one flat node per exact descriptor step origin')
        require(origin['family_id'] == descriptor['family_id'] and node['rule'] == steps[sid][0]['rule'],
                'LAYOUT', 'literal root family/rule origin join')
        require(type(node['ordered_inputs']) is list, 'REFERENCE', 'ordered flat reads')
        nodes[nid] = node; step_to_node[sid] = nid
    require(set(step_to_node) == set(steps), 'LAYOUT', 'complete root primitive origin map')
    node_rows = _row_map(assignment['node_rows'], nodes, work)
    input_rows = _row_map(assignment['input_rows'], inputs, work)
    positions = {nid: i for i, nid in enumerate(nodes)}

    def translate(ref, prior_steps=None):
        work.step(); require(type(ref) is dict and len(ref) == 1, 'REFERENCE', 'one exact source')
        if set(ref) == {'input'}:
            require(ref['input'] in inputs, 'REFERENCE', 'existing input')
            return {'input': ref['input']}
        require(set(ref) == {'step'} and ref['step'] in step_to_node
                and (prior_steps is None or ref['step'] in prior_steps),
                'REFERENCE', 'strict prior descriptor primitive source')
        return {'node': step_to_node[ref['step']]}

    prior = set()
    for sid, (step, unused) in steps.items():
        work.step(); nid = step_to_node[sid]; node = nodes[nid]
        expected = [translate(ref, prior) for ref in step['ordered_inputs']]
        require(node['ordered_inputs'] == expected, 'LAYOUT', 'every ordered/repeated read preserved')
        for ref in expected:
            work.step()
            if 'node' in ref:
                require(positions[ref['node']] < positions[nid], 'LAYOUT', 'flat dependency order')
                row = node_rows[ref['node']]
            else:
                row = input_rows[ref['input']]
            require(row < node_rows[nid], 'ASSIGNMENT', 'strict earlier physical read')
        prior.add(sid)
    expected_outputs = [{'port_id': pid, 'source': translate(output['source'])}
                        for pid, (output, unused) in outputs.items()]
    require(shape['outputs'] == expected_outputs, 'LAYOUT', 'all exact ordered exposed output refs')
    formulas = {('input', pid): pair for pid, pair in inputs.items()}
    for sid, (step, path) in steps.items():
        formulas[('node', step_to_node[sid])] = (step['formula'], path)
    requirements = []

    def add(kind, name, source, template_pair, row, ordered_index=None):
        work.step()
        if len(requirements) >= work.limits['requirements']:
            raise _Unfinished('OWN_REQUIREMENT_PREFIX')
        formula, path = template_pair; head = _formula_head(formula, work)
        requirements.append({'kind': kind, 'id': name, 'ordered_index': ordered_index,
            'source': dict(source), 'template_path': list(path), 'point': [CHANNEL, row],
            'head': head, 'mark': None if head is None else ['formula-head', head]})

    for pid, pair in inputs.items():
        add('ROOT_INPUT_INTERFACE', pid, {'input': pid}, pair, input_rows[pid])
    for nid, node in nodes.items():
        sid = node['origin']['step_id']
        add('PRIMITIVE_OUTPUT', nid, {'node': nid}, (steps[sid][0]['formula'], steps[sid][1]), node_rows[nid])
        for index, ref in enumerate(node['ordered_inputs']):
            kind, name = next(iter(ref.items()))
            row = node_rows[name] if kind == 'node' else input_rows[name]
            add('ORDERED_PREMISE_READ', nid, ref, formulas[(kind, name)], row, index)
    for pid, (output, path) in outputs.items():
        source = translate(output['source']); kind, name = next(iter(source.items()))
        row = node_rows[name] if kind == 'node' else input_rows[name]
        add('EXPOSED_OUTPUT_INTERFACE', pid, source, (output['formula'], path), row)
    return requirements, None


def check_plan_heads(*, descriptor, layout_shape, row_assignment, tick, limits=None):
    """Compile absent-or-exact channel5 heads; never infer a full formula."""
    work = _Work(tick, limits)
    request, request_sha256 = None, None
    try:
        request = work.copy({'descriptor': descriptor, 'layout_shape': layout_shape,
                             'row_assignment': row_assignment, 'limits': dict(work.limits)})
        raw = canonical(request)
        if len(raw) > work.limits['input_bytes']:
            raise _Unfinished('OWN_INPUT_BYTE_PREFIX')
        request_sha256 = hashlib.sha256(raw).hexdigest()
        requirements, reason = _supported_requirements(request['descriptor'], request['layout_shape'],
                                                     request['row_assignment'], work)
        if requirements is None:
            raise _Unfinished(reason)
        points, unknown = {}, []
        for index, item in enumerate(requirements):
            work.step()
            if item['head'] is None:
                unknown.append(index)
                continue
            heads = points.setdefault(item['point'][1], {})
            heads.setdefault(item['head'], []).append(index)
        known_marks, conflicts = [], []
        for row, heads in sorted(points.items()):
            work.step()
            values = [{'value': ['formula-head', head], 'requirement_indices': indices}
                      for head, indices in heads.items()]
            known_marks.append({'point': [CHANNEL, row], 'values': values})
            if len(heads) > 1:
                conflicts.append({'point': [CHANNEL, row], 'values': values})
        work.step()
        status = 'HEAD_CONFLICT' if conflicts else 'NO_KNOWN_HEAD_CONFLICT'
        return {'schema': SCHEMA, 'version': VERSION, 'status': status, 'reason': None,
            'scope': 'THIS_PHYSICAL_CLUSTER_PLAN_ONLY', 'request': request,
            'request_sha256': request_sha256, 'planning_channel': CHANNEL,
            'gate_completed': True, 'advisory_plan_rejected': bool(conflicts),
            'requirements': requirements, 'known_marks': known_marks,
            'conflicts': conflicts, 'unknown_requirement_indices': unknown,
            'work': {'steps': work.steps, 'limits': dict(work.limits)}, 'flags': dict(FLAGS)}
    except _CallbackFailure as failure:
        raise failure.error
    except _Unfinished as unfinished:
        return {'schema': SCHEMA, 'version': VERSION, 'status': 'UNKNOWN', 'reason': str(unfinished),
            'scope': 'THIS_PHYSICAL_CLUSTER_PLAN_ONLY', 'request': request,
            'request_sha256': request_sha256, 'planning_channel': CHANNEL,
            'gate_completed': False, 'advisory_plan_rejected': False,
            'requirements': [], 'known_marks': [], 'conflicts': [],
            'unknown_requirement_indices': [],
            'work': {'steps': work.steps, 'limits': dict(work.limits)}, 'flags': dict(FLAGS)}
