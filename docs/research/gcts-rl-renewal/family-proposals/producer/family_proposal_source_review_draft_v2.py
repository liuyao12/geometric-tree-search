"""Prospective finite single/pair source-body proposal preparation; unexecuted.

No target, authored proof word, model loader, checker or search imports.  The
ROOT-gated worker passes the unchanged graph/lifecycle objects.  This module
does not select placements or mutate the graph or original body authority.
"""
import copy
import itertools
import json
import time
from dataclasses import dataclass

VERSION = 'finite-root-single-pair-whole-union-v2'
GRAMMAR = {
    'version': VERSION, 'components': [1, 2],
    'first_inputs': 'actual selected initial anchors with exact formula codes',
    'second_inputs': 'actual initial anchors or included first declared output; use output at least once',
    'bindings': 'complete formula-filtered ordered Cartesian products; repeated ports retained',
    'embedding': 'one canonical earliest exact-key reuse else earliest unused strict-prior row',
    'sharing': 'same complete primitive key/full decorated identity only; preserve component occurrences',
    'priority': 'decreasing distinct member count then canonical component-and-binding specification',
    'native_accepted': False,
}


class PreparationLimit(Exception):
    pass


class ProposalRejected(Exception):
    pass


def check_deadline(deadline):
    if time.perf_counter() >= deadline:
        raise PreparationLimit('complete preparation deadline; no partial active pool')


def interfaces(graph, authority, projection, core):
    """Rebind all full projection digests; no target-name or last-row inference."""
    authority.check_graph(graph)
    if (projection['status'] != 'read_only_projection_with_bound_passed_independent_finite_audit'
            or projection['native_accepted'] is not False
            or projection['formula_registry_sha256'] != graph.registry_sha
            or projection['formula_codes'] != graph.formulas):
        raise ValueError('projection relation or formula registry changed')
    declared = projection['definitions']
    names = [d['name'] for d in declared]
    if len(names) != 171 or len(set(names)) != 171 or set(names) != {n for n, _ in authority.bodies}:
        raise ValueError('all exact 171 source bodies required')
    records = []
    for d in declared:
        body = authority.body(d['name'])
        if body['full_frozen_definition_sha256'] != core.digest(d):
            raise ValueError('declared conclusion/premise projection not body-bound')
        members = [{k: m[k] for k in ('row', 'recipe_id', 'formula_code', 'ordered_inputs')}
                   for m in d['primitive_members']]
        for field, value in (('canonical_input_rows', d['canonical_input_rows']),
                             ('premise_codes', d['premise_codes']), ('primitive_members', members),
                             ('source_body_sha256', d['source_body_sha256']),
                             ('mapped_body_sha256', d['mapped_body_sha256'])):
            if body[field] != value:
                raise ValueError('projection differs from original registered body')
        conclusion_row = core.integer(d['canonical_conclusion_row'])
        conclusion_code = core.integer(d['conclusion_code'])
        conclusions = [m for m in members if m['row'] == conclusion_row]
        if (len(conclusions) != 1 or conclusions[0]['formula_code'] != conclusion_code
                or not 0 <= conclusion_code < len(graph.formulas)
                or graph.formulas[conclusion_code] != d['conclusion_ast']
                or [graph.formulas[c] for c in d['premise_codes']] != d['premise_ast']):
            raise ValueError('declared conclusion is not exact body output')
        records.append({'name': d['name'], 'body_sha256': core.digest(body),
                        'full_projection_sha256': core.digest(d), 'body': body,
                        'conclusion_row': conclusion_row, 'conclusion_code': conclusion_code})
    return tuple(sorted(records, key=lambda r: core.canonical([r['name'], r['body_sha256']])))


def root_anchors(graph, core):
    if graph.excluded != [set() for _ in range(graph.height)]:
        raise ValueError('only pristine root preparation, never branch-local hypotheses')
    result = []
    for key in graph.order:
        if key not in graph.selected or graph.selected[key] != 0:
            raise ValueError('actual initial generation-zero placement required')
        recipe = graph.recipes[key.recipe]
        if recipe.witness['rule'] != 'assumption' or key.refs:
            raise ValueError('only original recipient hypothesis placements may anchor root families')
        result.append({'key': key.data(), 'full_id': graph.decorate(key)['id'],
                       'formula_code': recipe.output, 'generation': graph.selected[key]})
    if len(result) != len(graph.context['ordered_local_premises']):
        raise ValueError('complete original hypothesis anchors required')
    # Exact distinct physical anchors are retained even when formulas coincide.
    if len({core.canonical(r['key']) for r in result}) != len(result):
        raise ValueError('duplicate selected root placement')
    return tuple(result)


def binding_choices(record, anchors, earlier=None):
    choices = []
    for code in record['body']['premise_codes']:
        values = [{'kind': 'root_anchor', 'index': i} for i, a in enumerate(anchors) if a['formula_code'] == code]
        if earlier is not None and earlier['conclusion_code'] == code:
            values.append({'kind': 'earlier_component_output', 'index': 0})
        choices.append(tuple(values))
    return itertools.product(*choices)


def canonical_embedding(graph, original, records, anchors, spec, life, deadline):
    """Construct one complete source-order embedding, with exact-key sharing."""
    core = life.core
    root_keys = tuple(core.Key(k['key'][0], k['key'][1], tuple(k['key'][2])) for k in anchors)
    occupied = {k.row: k for k in root_keys}
    prior_components, component_data, distinct = [], [], set()
    by_name = {r['name']: r for r in records}
    for component_index, component in enumerate(spec):
        check_deadline(deadline)
        record = by_name[component['name']]; body = record['body']
        bindings = component['ordered_inputs']
        if len(bindings) != len(body['premise_codes']):
            raise ValueError('incomplete ordered component receptor map')
        input_rows = []
        for binding, code in zip(bindings, body['premise_codes']):
            if set(binding) != {'kind', 'index'} or type(binding['index']) is not int:
                raise ValueError('literal ordered binding token required')
            index = binding['index']
            if binding['kind'] == 'root_anchor':
                if not 0 <= index < len(anchors) or anchors[index]['formula_code'] != code:
                    raise ValueError('root anchor token has wrong actual formula')
                input_rows.append(root_keys[index].row)
            elif binding['kind'] == 'earlier_component_output':
                if component_index != 1 or index != 0 or records_by_spec(records, spec[0])['conclusion_code'] != code:
                    raise ValueError('not an exact prior declared output-to-receptor link')
                input_rows.append(prior_components[index]['conclusion_row'])
            else:
                raise ValueError('unsupported invented receptor token')
        if component_index == 1 and not any(b['kind'] == 'earlier_component_output' for b in bindings):
            raise ValueError('pair must have an explicit prior output edge')
        mapping = dict(zip(body['canonical_input_rows'], input_rows))
        member_rows, keys, previous = [], [], -1
        for member in body['primitive_members']:
            check_deadline(deadline)
            refs = tuple(mapping[r] for r in member['ordered_inputs'])
            index = graph.recipe_index[member['recipe_id']]
            lower = max((previous, *refs))
            existing = sorted(k for row, k in occupied.items()
                              if row > lower and k.recipe == index and k.refs == refs)
            if existing:
                key = min(existing, key=lambda k: k.row)
            else:
                row = next((r for r in range(lower + 1, graph.height) if r not in occupied), None)
                if row is None:
                    raise ProposalRejected('canonical_embedding_boundary_exhaustion')
                key = core.Key(index, row, refs); occupied[row] = key
            if graph.recipes[key.recipe].output != member['formula_code']:
                raise ValueError('source member formula differs from primitive recipe')
            mapping[member['row']] = key.row
            keys.append(key); member_rows.append(key.row); distinct.add(key); previous = key.row
        expected = original.expected(graph, record['name'], input_rows, member_rows, 0)
        if expected['members'] != [k.data() for k in keys]:
            raise ValueError('canonical source transport differs from original authority')
        original.compile(graph, expected)
        component_record = {
            'name': record['name'], 'body_sha256': record['body_sha256'],
            'source_body_sha256': body['source_body_sha256'], 'mapped_body_sha256': body['mapped_body_sha256'],
            'full_projection_sha256': record['full_projection_sha256'],
            'dependency_bindings': body['dependency_bindings'], 'earlier_expansion_closure': body['earlier_expansion_closure'],
            'ordered_input_bindings': copy.deepcopy(bindings), 'ordered_input_rows': input_rows,
            'ordered_member_rows': member_rows, 'conclusion_code': record['conclusion_code'],
            'conclusion_row': mapping[record['conclusion_row']],
            'ordered_receptor_ports': expected['ordered_receptor_ports'],
            'members': expected['members'], 'full_member_ids': expected['full_member_ids'],
            'full_identity_preimage_sha256': [core.digest(x) for x in expected['full_identity_preimages']],
            'original_component_descriptor_sha256': core.digest(expected),
            'aggregate_t': expected['aggregate_t'], 'aggregate_m': expected['aggregate_m']}
        prior_components.append(component_record); component_data.append(component_record)
    if len(spec) not in (1, 2):
        raise ValueError('frozen single/pair grammar only')
    # Whole-group validity includes original state. It installs no receptor marks.
    try:
        graph.validate_cluster(sorted(distinct), model_epoch=graph.model_epoch)
    except ValueError as exc:
        raise ProposalRejected('whole_group_point_validation:' + str(exc)) from exc
    marks, totals = {}, {}
    for component in component_data:
        for x, y, value in component['aggregate_m']:
            point = (x, y)
            if point in marks and marks[point] != value:
                raise ProposalRejected('component_marking_union_conflict')
            marks[point] = value
    for key in sorted(distinct):
        for x, y, value in graph.point_data(key)[0]:
            totals[x, y] = totals.get((x, y), 0) + value
    if any(v > 1 for v in totals.values()):
        raise ProposalRejected('distinct_member_aggregate_overcapacity')
    for point, value in marks.items():
        if point in graph.marks and graph.marks[point] != value:
            raise ProposalRejected('aggregate_receptor_existing_mark_conflict')
    keys = tuple(sorted(distinct)); decorated = [graph.decorate(k) for k in keys]
    return {'components': component_data, 'members': [k.data() for k in keys],
            'full_member_ids': [d['id'] for d in decorated],
            'full_identity_preimage_sha256': [core.digest(d['identity_preimage']) for d in decorated],
            'aggregate_t': [[*p, v] for p, v in sorted(totals.items())],
            'aggregate_m': [[*p, v] for p, v in sorted(marks.items())],
            'component_member_occurrences': sum(len(c['members']) for c in component_data),
            'distinct_member_count': len(keys),
            'shared_member_count': sum(len(c['members']) for c in component_data) - len(keys)}


def records_by_spec(records, component):
    return next(r for r in records if r['name'] == component['name'])


@dataclass(frozen=True)
class GroupAuthority:
    """New immutable proposal relation wrapping unchanged original bodies.

    No source body or native authority is added. Each compile reconstructs its
    registered source embedding, ports and union; known-pool membership binds
    that reconstruction to the complete frozen grammar and root anchors.
    """
    graph_text: str
    epoch: str
    original: object
    life: object
    interface_text: str
    anchor_text: str
    spec_texts: tuple[str, ...]
    source_text: str

    def epoch_payload(self):
        return {'version': VERSION, 'grammar': GRAMMAR, 'graph': json.loads(self.graph_text),
                'original_authority_epoch': self.original.epoch, 'interfaces': self.life.core.digest(json.loads(self.interface_text)),
                'root_anchors': json.loads(self.anchor_text), 'pool_specs': [json.loads(t) for t in self.spec_texts],
                'source_bindings': json.loads(self.source_text)}

    def check_graph(self, graph):
        self.original.check_graph(graph)
        if (self.graph_text != self.original.graph_text or self.life.core.digest(self.epoch_payload()) != self.epoch):
            raise ValueError('stale group authority, pool, interfaces or original body binding')

    def expected(self, graph, index, priority, deadline=float('inf')):
        self.check_graph(graph)
        core = self.life.core; core.integer(index); core.integer(priority)
        if not 0 <= index < len(self.spec_texts) or priority < 0:
            raise ValueError('exact registered group index and nonnegative priority required')
        spec = json.loads(self.spec_texts[index])
        data = canonical_embedding(graph, self.original, tuple(json.loads(self.interface_text)),
                                   tuple(json.loads(self.anchor_text)), spec, self.life, deadline)
        data.update({'version': VERSION, 'relation': 'finite_source_body_composition_proposal_not_new_lemma',
                     'graph_binding': json.loads(self.graph_text), 'body_authority_epoch': self.epoch,
                     'original_body_authority_epoch': self.original.epoch, 'pool_index': index,
                     'binding_specification': spec, 'fixed_priority': priority,
                     'native_accepted': False, 'native_authority_activated': False})
        data['descriptor_id'] = 'whole-family-group-' + core.digest(data)
        return data

    def compile(self, graph, descriptor):
        if not isinstance(descriptor, dict):
            raise ValueError('literal complete group descriptor required')
        expected = self.expected(graph, descriptor['pool_index'], descriptor['fixed_priority'])
        core = self.life.core
        if core.canonical(expected) != core.canonical(descriptor):
            raise ValueError('group differs from registered original body embedding and union')
        keys = tuple(core.Key(k[0], k[1], tuple(k[2])) for k in expected['members'])
        return self.life.CompiledDescriptor(core.canonical(expected), keys,
                                           tuple(expected['full_member_ids']),
                                           tuple(tuple(v) for v in expected['aggregate_t']),
                                           tuple(tuple(v) for v in expected['aggregate_m']),
                                           expected['descriptor_id'], expected['fixed_priority'])


def prepare(graph, original, projection, life, source_bindings, deadline, counters):
    core = life.core; start = time.perf_counter(); initial = core.digest(graph.semantic_state())
    records = interfaces(graph, original, projection, core); check_deadline(deadline)
    anchors = root_anchors(graph, core); check_deadline(deadline)
    counters.update({'interfaces_checked': len(records), 'single_types_visited': 0, 'pair_types_visited': 0,
                     'binding_tuples_visited': 0, 'accepted_binding_specs': 0, 'rejections': {},
                     'rejected_binding_records': [], 'type_visits': [], 'disconnected_second_bindings_outside_grammar': 0})
    accepted, preliminary = [], []

    def visit(spec):
        check_deadline(deadline); counters['binding_tuples_visited'] += 1
        try:
            group = canonical_embedding(graph, original, records, anchors, spec, life, deadline)
        except ProposalRejected as exc:
            reason = str(exc); counters['rejections'][reason] = counters['rejections'].get(reason, 0) + 1
            counters['rejected_binding_records'].append({'specification': copy.deepcopy(spec), 'reason': reason})
            return
        accepted.append(core.canonical(spec)); preliminary.append(group['distinct_member_count'])
        counters['accepted_binding_specs'] += 1

    for first in records:
        check_deadline(deadline); counters['single_types_visited'] += 1
        counters['type_visits'].append({'names': [first['name']], 'binding_tuples': 0})
        for binding in binding_choices(first, anchors):
            counters['type_visits'][-1]['binding_tuples'] += 1
            visit([{'name': first['name'], 'ordered_inputs': list(binding)}])
    for first in records:
        for second in records:
            check_deadline(deadline); counters['pair_types_visited'] += 1
            counters['type_visits'].append({'names': [first['name'], second['name']], 'binding_tuples': 0})
            for left in binding_choices(first, anchors):
                for right in binding_choices(second, anchors, first):
                    if not any(b['kind'] == 'earlier_component_output' for b in right):
                        counters['disconnected_second_bindings_outside_grammar'] += 1
                        continue  # Outside the declared connected-pair grammar, not a rejected proof.
                    counters['type_visits'][-1]['binding_tuples'] += 1
                    visit([{'name': first['name'], 'ordered_inputs': list(left)},
                           {'name': second['name'], 'ordered_inputs': list(right)}])
    if counters['single_types_visited'] != 171 or counters['pair_types_visited'] != 171 ** 2:
        raise AssertionError('entire declared family type domain not visited')
    if len(set(accepted)) != len(accepted):
        raise AssertionError('enumerator must preserve occurrence identity and avoid repeated literal specs')
    text, anchors_text = core.canonical(records), core.canonical(anchors)
    authority = GroupAuthority(original.graph_text, '', original, life, text, anchors_text,
                               tuple(accepted), core.canonical(source_bindings))
    authority = GroupAuthority(authority.graph_text, core.digest(authority.epoch_payload()), original, life,
                               text, anchors_text, tuple(accepted), authority.source_text)
    priorities = {index: rank for rank, index in enumerate(sorted(range(len(accepted)),
                  key=lambda i: (-preliminary[i], accepted[i])))}
    groups = []
    for index in range(len(accepted)):
        check_deadline(deadline)
        descriptor = authority.expected(graph, index, priorities[index], deadline)
        authority.compile(graph, descriptor); check_deadline(deadline)
        groups.append(descriptor)
    # This is construction/validation only: Controller and Executor are not run.
    if core.digest(graph.semantic_state()) != initial:
        raise AssertionError('preparation mutated primitive graph semantics')
    counters.update({'registered_groups': len(groups), 'source_member_occurrences': sum(g['component_member_occurrences'] for g in groups),
                     'group_distinct_members': sum(g['distinct_member_count'] for g in groups),
                     'group_shared_members': sum(g['shared_member_count'] for g in groups),
                     'preparation_seconds': time.perf_counter() - start,
                     'initial_final_graph_semantic_sha256': initial})
    return authority, groups, anchors, records
