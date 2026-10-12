"""SOURCE ONLY conditional tiny qualification helpers; no loader/worker/CLI.

All caller objects and tiny raw receipts require separate ROOT/independent source
and resource admission. The author has not imported or called any function.
No search, RNG, certificate checking, native call or acceptance promotion occurs
here. Arbitrary authored bodies are mechanism controls, never mined lemmas.
"""
from __future__ import annotations
import copy
import itertools
import json


def require_tiny_graph(graph):
    header = graph.catalog.header
    if (header.get('synthetic_mechanism_control') is not True
            or header.get('production_theorem_admission') is not False
            or header.get('split') != 'mechanism-control'
            or header.get('height') != 24 or len(header['context']['ordered_local_premises']) != 3):
        raise ValueError('synthetic24-row mechanism graph only; never production activation')
    return header


def locate_recipe(graph, *, rule, formula, ordered_formulas=(), name=None):
    require_tiny_graph(graph); matches = []
    for index in range(len(graph.recipes)):
        witness = graph.catalog.witness(index)
        if (witness['rule'] == rule and witness['formula'] == formula
                and graph.catalog.premises(index) == list(ordered_formulas)
                and (name is None or witness.get('name') == name)):
            matches.append(index)
    if len(matches) != 1:
        raise ValueError('exact full tiny command/ordered-premise witness, not formula-only lookup')
    return matches[0]


def declare_mechanism_bodies(graph, life, *, inventory_mode):
    """Future authored canonical templates only, no placement or proof route.

    Canonical source rows are abstract aliases; they are not seeded into this
    recipient. ROOT must independently audit these full raw body definitions
    before promoting the projection or invoking the complete proposer.
    """
    header = require_tiny_graph(graph)
    if inventory_mode not in ('ports-and-sharing', 'capacity64', 'overfull65'):
        raise ValueError('exact declared prospective tiny inventory')
    head = header['context']['ordered_local_premises'][0]
    implication = header['context']['ordered_local_premises'][2]; output = implication[2]
    if implication != ['imp', head, output]: raise ValueError('genuine declared tiny MP receptor pair')
    zero = locate_recipe(graph, rule='axiom', formula=head, name='head-' + head[0])
    mp = locate_recipe(graph, rule='mp', formula=output, ordered_formulas=(head, implication))
    if graph.catalog.recipe_meta(mp)['inputs'][0] == graph.catalog.recipe_meta(mp)['inputs'][1]:
        raise ValueError('equal-code generic FactorStream control is not genuine MP')
    core = life.core
    if inventory_mode == 'ports-and-sharing':
        specifications = [('control-replenish', [core.Key(zero, 2)]),
            ('control-MP', [core.Key(mp, 2, (0, 1))]),
            ('control-redundant-share', [core.Key(zero, 2), core.Key(mp, 3, (0, 1))])]
    else:
        count = 64 if inventory_mode == 'capacity64' else 65
        specifications = [('capacity-control-' + str(index), [core.Key(zero, 2)]) for index in range(count)]
    before = core.digest(graph.semantic_state()); bodies = []; definitions = []
    for name, keys in specifications:
        body = life.primitive_body(graph, name, keys)
        conclusion_row = keys[-1].row; conclusion_code = graph.recipes[keys[-1].recipe].output
        definition = {'name': name, 'canonical_input_rows': body['canonical_input_rows'],
            'premise_codes': body['premise_codes'], 'primitive_members': copy.deepcopy(body['primitive_members']),
            'source_body_sha256': body['source_body_sha256'], 'mapped_body_sha256': body['mapped_body_sha256'],
            'canonical_conclusion_row': conclusion_row, 'conclusion_code': conclusion_code,
            'conclusion_ast': graph.formulas[conclusion_code],
            'premise_ast': [graph.formulas[code] for code in body['premise_codes']],
            'synthetic_mechanism_control': True, 'production_theorem_admission': False,
            'closed_lemma': False, 'automatically_discovered': False, 'native_accepted': False,
            'fixture_instance_id': header['instance_id'], 'inventory_mode': inventory_mode}
        body['full_frozen_definition_sha256'] = core.digest(definition)
        body['earlier_expansion_closure'] = {'kind': 'synthetic_authored_primitive_control_not_closed_proof',
            'primitive_members': copy.deepcopy(body['primitive_members']), 'recursive_named_body_dependencies': [],
            'accepted_training_proof_pins': [], 'production_theorem_admission': False}
        bodies.append(body); definitions.append(definition)
    if core.digest(graph.semantic_state()) != before:
        raise ValueError('canonical body declaration cannot mutate recipient graph')
    draft = {'status': 'pending_independent_synthetic_body_projection_audit_not_production',
        'native_accepted': False, 'formula_registry_sha256': graph.registry_sha,
        'declared_source_body_count': len(bodies), 'definitions': definitions,
        'synthetic_mechanism_control': True, 'production_theorem_admission': False,
        'inventory_mode': inventory_mode}
    return bodies, draft


def prepare_qualified_tiny_pool(graph, authority, admitted_projection, life, proposal,
                                source_bindings, deadline, counters, *, qualified_registry_binding):
    """Only after ROOT authenticates actual complete tiny body/registry audit pins.

    No helper promotes the pending projection status. Complete65 construction
    is preserved as a refusal control; no truncation or source subset is applied.
    """
    require_tiny_graph(graph)
    if (admitted_projection.get('synthetic_mechanism_control') is not True
            or admitted_projection.get('production_theorem_admission') is not False
            or admitted_projection.get('status') != 'read_only_projection_with_bound_passed_independent_finite_audit'):
        raise ValueError('actual admitted tiny-only projection, never a producer status waiver')
    return proposal.prepare(graph, authority, admitted_projection, life, source_bindings,
                            deadline, counters, qualified_registry_binding=qualified_registry_binding)


def literal_specs(reference, admitted_interfaces):
    """Complete root binding/pair spec reference, independent of proposer helpers.

    ROOT's prior body gate must check these definitions against the declaration;
    this function is not that gate. All duplicate occurrence anchors remain.
    """
    anchor_codes = [reference.recipes[key[0]]['output'] for key in reference.initial]
    definitions = [{'name': item['name'], 'body_sha256': item['body_sha256'],
                    'premise_codes': item['body']['premise_codes'],
                    'conclusion_code': item['conclusion_code']} for item in admitted_interfaces]
    definitions.sort(key=lambda item: json.dumps([item['name'], item['body_sha256']], sort_keys=True, separators=(',', ':')))
    accepted = []
    def choices(definition, first=None):
        columns = []
        for code in definition['premise_codes']:
            tokens = [{'kind': 'root_anchor', 'index': index} for index, current in enumerate(anchor_codes) if current == code]
            if first is not None and first['conclusion_code'] == code:
                tokens.append({'kind': 'earlier_component_output', 'index': 0})
            columns.append(tokens)
        return itertools.product(*columns)
    for first in definitions:
        for ports in choices(first):
            accepted.append([{'name': first['name'], 'ordered_inputs': list(ports)}])
    disconnected = 0
    for first in definitions:
        for second in definitions:
            for left in choices(first):
                for right in choices(second, first):
                    if not any(token['kind'] == 'earlier_component_output' for token in right):
                        disconnected += 1; continue
                    accepted.append([{'name': first['name'], 'ordered_inputs': list(left)},
                        {'name': second['name'], 'ordered_inputs': list(right)}])
    return accepted, {'single_types_visited': len(definitions), 'pair_types_visited': len(definitions) ** 2,
                      'disconnected_second_bindings_outside_grammar': disconnected}


def compare_entire_tiny_pool(literal, admitted_interfaces, actual_groups, counters, reference_module):
    """Independent earliest-key embedding and full point/port union for every spec.

    This checks completeness relative to the separately admitted authored tiny
    body definitions. It is not a body-discovery or production-library gate.
    """
    if literal.order != list(literal.initial) or any(literal.excluded):
        raise ValueError('whole root pool admission requires pristine three-occurrence state; later hints use current-state observers')
    expected_specs, visits = literal_specs(literal, admitted_interfaces)
    if [group['binding_specification'] for group in actual_groups] != expected_specs:
        raise ValueError('entire single/pair/root occurrence binding domain, no subset')
    for field, value in visits.items():
        if counters[field] != value: raise ValueError('all tiny source types/bindings visited:' + field)
    by_name = {item['name']: item for item in admitted_interfaces}
    recipe_indices = {item['record']['id']: index for index, item in enumerate(literal.recipes)}
    expected_sizes = []
    for spec, group in zip(expected_specs, actual_groups):
        occupied = {key[1]: key for key in literal.initial}; components = []; whole = set()
        for position, token in enumerate(spec):
            interface = by_name[token['name']]; body = interface['body']; inputs = []
            if len(token['ordered_inputs']) != len(body['premise_codes']): raise ValueError('all ordered external aliases')
            for binding, code in zip(token['ordered_inputs'], body['premise_codes']):
                if binding['kind'] == 'root_anchor':
                    row = literal.initial[binding['index']][1]
                elif binding['kind'] == 'earlier_component_output' and position == 1 and binding['index'] == 0:
                    row = components[0]['conclusion_row']
                else: raise ValueError('literal source root/output receptor only')
                if (position == 1 and binding['kind'] == 'earlier_component_output'
                        and components[0]['conclusion_code'] != code): raise ValueError('prior output exact code')
                if binding['kind'] == 'root_anchor' and literal.recipes[literal.initial[binding['index']][0]]['output'] != code:
                    raise ValueError('occurrence anchor has exact formula')
                inputs.append(row)
            mapping = dict(zip(body['canonical_input_rows'], inputs)); members = []; previous = -1
            for member in body['primitive_members']:
                index = recipe_indices[member['recipe_id']]; refs = tuple(mapping[r] for r in member['ordered_inputs'])
                lower = max((previous, *refs)); reuse = sorted(k for r, k in occupied.items() if r > lower and k[0] == index and k[2] == refs)
                if reuse: key = min(reuse, key=lambda k: k[1])
                else:
                    choices = [row for row in range(lower + 1, 24) if row not in occupied]
                    if not choices: raise ValueError('tiny complete embedding unexpectedly exceeds24; no salvage')
                    key = (index, choices[0], refs); occupied[key[1]] = key
                if literal.recipes[index]['output'] != member['formula_code']: raise ValueError('full licensed body output')
                mapping[member['row']] = key[1]; members.append(key); whole.add(key); previous = key[1]
            component = group['components'][position]
            wanted_ports = []
            for alias, (canonical_row, physical_row, code) in enumerate(zip(body['canonical_input_rows'], inputs, body['premise_codes'])):
                readers = []
                for member in body['primitive_members']:
                    recipe = literal.recipes[recipe_indices[member['recipe_id']]]
                    for port, (source_row, expected_code) in enumerate(zip(member['ordered_inputs'], recipe['inputs'])):
                        if source_row == canonical_row:
                            if expected_code != code: raise ValueError('literal ordered reader code')
                            reader_row = mapping[member['row']]
                            readers.append({'reader_row': reader_row, 'primitive_input_port': port,
                                'formula_code': code, 'offset_value': physical_row - reader_row})
                wanted_ports.append({'high_level_port': alias, 'input_row': physical_row, 'formula_code': code,
                                     'new_occupancy': 0, 'readers': readers})
            conclusion_row = mapping[interface['conclusion_row']]
            expected = {'members': [reference_module.key_data(k) for k in members],
                'ordered_input_rows': inputs, 'ordered_member_rows': [k[1] for k in members],
                'conclusion_row': conclusion_row, 'conclusion_code': interface['conclusion_code'],
                'ordered_input_bindings': token['ordered_inputs'], 'ordered_receptor_ports': wanted_ports,
                'full_member_ids': [literal.decorate(k)['id'] for k in members],
                'full_identity_preimage_sha256': [reference_module.sha(literal.decorate(k)['identity_preimage']) for k in members]}
            for field, value in expected.items():
                if component[field] != value: raise ValueError('entire independent component embedding/ports:' + field)
            components.append(expected)
        keys = sorted(whole); decoded = [literal.decorate(k) for k in keys]; t = {}; m = {}
        for item in decoded:
            if not literal.legal(item['key']): raise ValueError('whole synthetic proposal remains a legal original-root obligation')
            for x, y, value in item['t']: t[x, y] = t.get((x, y), 0) + value
            for x, y, value in item['m']:
                if (x, y) in m and m[x, y] != value: raise ValueError('whole mark union conflict')
                m[x, y] = value
        occurrences = sum(len(c['members']) for c in components)
        expected = {'members': [reference_module.key_data(k) for k in keys],
            'full_member_ids': [item['id'] for item in decoded],
            'full_identity_preimage_sha256': [reference_module.sha(item['identity_preimage']) for item in decoded],
            'aggregate_t': [[*p, v] for p, v in sorted(t.items())], 'aggregate_m': [[*p, v] for p, v in sorted(m.items())],
            'component_member_occurrences': occurrences, 'distinct_member_count': len(keys), 'shared_member_count': occurrences - len(keys)}
        for field, value in expected.items():
            if group[field] != value: raise ValueError('full independent union/identity relation:' + field)
        if any(value > 1 for value in t.values()): raise ValueError('shared exact key once, no distinct overcapacity')
        expected_sizes.append(len(keys))
    rank = {index: priority for priority, index in enumerate(sorted(range(len(expected_specs)),
        key=lambda i: (-expected_sizes[i], reference_module.text(expected_specs[i]))))}
    if [group['fixed_priority'] for group in actual_groups] != [rank[i] for i in range(len(actual_groups))]:
        raise ValueError('all fixed priorities from complete grammar, no tuned order')
    return {'schema': 'independent-whole-synthetic-proposal-pool-v1', 'full_pool_pass': True,
            'registered_groups': len(actual_groups), 'visits': visits, 'production_theorem_admission': False}


def compare_complete_graph(graph, literal):
    """Future full tiny-state/point/factor comparison, including every final key."""
    require_tiny_graph(graph); actual = graph.semantic_state(); expected = literal.state()
    for field, value in expected.items():
        if actual[field] != value: raise ValueError('literal full point state differs:' + field)
    key_count = 0; factor_count = 0
    for row in range(24):
        base = literal.candidates(row, ignore_exclusion=True); legal = literal.candidates(row)
        observed = [tuple([key.recipe, key.row, tuple(key.refs)]) for key in graph.candidates(row)]
        if observed != legal: raise ValueError('every complete candidate/key order through EOF must match')
        key_count += len(observed)
        for key in legal:
            actual_key = graph._bound_core.Key(key[0], key[1], key[2])
            if graph.point_data(actual_key) != literal.point_data(key): raise ValueError('all literal t/m points, not adjacent sample')
            if graph.decorate(actual_key) != literal.decorate(key): raise ValueError('full primitive placement identity and preimage')
        domain = actual['domains'][row]
        excluded_legal = [key for key in sorted(literal.excluded[row]) if literal.legal(key, ignore_exclusion=True)]
        if (domain['base_count'] != len(base) or domain['count'] != len(legal)
                or domain['excluded_legal'] != [[k[0], k[1], list(k[2])] for k in excluded_legal]):
            raise ValueError('base/current/excluded domain counts independently exhausted')
        relevant = [[*p, v] for p, v in sorted(literal.marks.items())
            if (p[0] == 1 and 0 <= p[1] <= row) or (p[0] in (2, 3) and p[1] == row)]
        relation = domain['factor_relation']
        if (relation['all_relevant_assigned_marks'] != relevant or relation['positive_total'] != literal.totals[row]
                or relation['recipe_order'] != 'all_original_recipe_indices'
                or relation['reference_order'] != 'all_ordered_strict_prior_row_pairs'
                or relation['unequal_input_codes_disallow_same_reference'] is not True):
            raise ValueError('full remote dependency relation, including assigned zero and absent marks')
        want = []
        for index, recipe in enumerate(literal.recipes):
            keys = [key for key in base if key[0] == index]
            if not keys: continue
            inputs = recipe['inputs']
            if not inputs: left = right = 0; different = False
            else:
                # Independent literal single-port compatibility; total count is
                # the exhaustively checked joint point-assignment relation.
                allowed = []
                for position, code in enumerate(inputs):
                    allowed.append([ref for ref in range(row)
                        if ((1, ref) not in literal.marks or literal.marks[1, ref] == code)
                        and ((2 + position, row) not in literal.marks or literal.marks[2 + position, row] == ref - row)])
                left = sum(1 << ref for ref in allowed[0]); right = sum(1 << ref for ref in allowed[1]); different = inputs[0] != inputs[1]
            want.append((index, left, right, different, len(keys)))
        got = [(f.recipe, f.left, f.right, f.different, f.count) for f in graph.domains[row].factors]
        if got != want: raise ValueError('complete factor records/masks/counts independently reconstructed')
        factor_count += len(got)
    decision = graph.decision()
    if [decision.kind, decision.row, decision.count, decision.generation] != literal.decision():
        raise ValueError('global dead then forced then earliest-generation/count decision')
    return {'schema': 'tiny-whole-point-state-observation-v1', 'literal_keys_observed': key_count,
        'literal_factors_observed': factor_count, 'rows_observed': 24, 'tiny_relation_pass': True,
        'production_theorem_admission': False, 'proof_accepted': False, 'resource_accepted': False}


def compare_complete_order(graph, literal, *, preferred_keys=()):
    require_tiny_graph(graph); decision = graph.decision(); expected_decision = literal.decision()
    if decision.kind not in ('branch', 'forced') or [decision.kind, decision.row, decision.count, decision.generation] != expected_decision:
        raise ValueError('fresh current global choice only')
    keys = [tuple([k[0], k[1], tuple(k[2])]) for k in preferred_keys]
    if decision.kind == 'forced' and keys: raise ValueError('forced has no advice permutation')
    if any(k not in literal.candidates(decision.row) for k in keys): raise ValueError('all preference keys actually legal')
    actual = graph.ordered_domain(decision, tuple(graph._bound_core.Key(k[0], k[1], k[2]) for k in keys))
    seen = set(); expect = []
    for key in keys + literal.candidates(decision.row):
        if key not in seen: seen.add(key); expect.append(key)
    observed = [(key.recipe, key.row, tuple(key.refs)) for key in actual]
    if observed != expect or len(actual) != len(expect): raise ValueError('entire preferred/canonical fallback permutation including EOF')
    descriptor = actual.descriptor()
    if (descriptor['complete_count'] != len(expect) or descriptor['decision'] != expected_decision
            or descriptor['preferred_keys'] != [[k[0], k[1], list(k[2])] for k in dict.fromkeys(keys)]
            or descriptor['full_stream_hash_measured'] is not False):
        raise ValueError('descriptor relation and honest observation/hash fields')
    return {'whole_order_pass': True, 'literal_order_keys_observed': len(expect),
            'descriptor': descriptor, 'production_theorem_admission': False}


def compare_lifecycle_and_features(controller, literal_lifecycle, feature_module, reference_module):
    """ROOT supplies separately admitted registry and the independent reference module."""
    graph = controller.graph; require_tiny_graph(graph)
    records = [json.loads(d.text) for d in controller.descriptors]
    if records != literal_lifecycle.descriptors or controller.revision != literal_lifecycle.revision:
        raise ValueError('same full ordered admitted registry and hint revision')
    actual_hints = [hint.data() for hint in controller.states]
    if actual_hints != literal_lifecycle.hints: raise ValueError('whole literal statuses/eligible members/retirement/consumption')
    decision = literal_lifecycle.point.decision()
    if decision[0] != 'branch':
        if any(hint['eligible'] for hint in actual_hints): raise ValueError('forced/dead controller cannot offer a branch preference')
        return {'branch': False, 'whole_hint_pass': True, 'feature_vectors_observed': 0,
                'production_theorem_admission': False}
    feature_graph = {'height': 24, 'totals': list(graph.totals),
        'marks': [[*p, v, graph.mark_refs[p]] for p, v in sorted(graph.marks.items())],
        'selected_keys': [key.data() for key in graph.order],
        'initial_selected_keys': [key.data() for key in graph.initial_selected]}
    recipes, heads = graph.feature_views()
    actual = feature_module.menu_features(feature_graph, recipes, heads, records, actual_hints, decision)
    expected = reference_module.literal_feature_menu(literal_lifecycle.point, records, actual_hints, decision)
    if actual != expected or tuple(feature_module.FEATURE_NAMES) != reference_module.FEATURES:
        raise ValueError('all31 features/full NULL menu independently interpreted')
    return {'branch': True, 'whole_hint_pass': True, 'feature_vectors_observed': len(actual['feature_vectors']),
            'complete_menu': actual, 'production_theorem_admission': False}


def compare_paired_overlay_prepared(*, eager_overlay, streamed_overlay, literal_draw):
    """Two separately cold identical tiny graphs/pools, not one double-resynced object.

    literal_draw is a ROOT-supplied diagnostic scalar, not an RNG draw generated
    here. No search/proof route is run. Each caller graph/hint snapshot must be
    independently compared before and after using the preceding helpers.
    """
    old_graph, new_graph = eager_overlay.graph, streamed_overlay.graph
    require_tiny_graph(old_graph); require_tiny_graph(new_graph)
    if old_graph is new_graph or eager_overlay.control is streamed_overlay.control:
        raise ValueError('separate identical cold graph/controller instances required')
    old_decision, new_decision = old_graph.decision(), new_graph.decision()
    if old_decision != new_decision or old_decision.kind not in ('branch', 'forced'):
        raise ValueError('same whole scheduled choice')
    old = eager_overlay.prepare(old_decision); new = streamed_overlay.prepare(new_decision)
    for key in ('decision', 'menu', 'needs_one_draw', 'pool_epoch', 'weight_sha256'):
        if old[key] != new[key]: raise ValueError('whole exact prepared policy business differs:' + key)
    # Prepared state hashes legitimately differ by the new consumer binding.
    draw = literal_draw if new['needs_one_draw'] else None
    old_order, old_record = eager_overlay.choose_prepared(old, draw)
    new_order, new_record = streamed_overlay.choose_prepared(new, draw)
    old_keys = [key.data() for key in old_order]; new_keys = [key.data() for key in new_order]
    if old_keys != new_keys: raise ValueError('eager/literal complete order and new full stream differ')
    for key in ('decision', 'pool_epoch', 'weight_sha256', 'policy', 'active_descriptor_id',
                'complete_base_count', 'preferred_keys', 'actual_first_key', 'changed_first', 'continuation', 'pending_scope'):
        if old_record[key] != new_record[key]: raise ValueError('selection/distribution/gradient/active preference differs:' + key)
    return {'schema': 'tiny-eager-streamed-overlay-comparison-v1', 'complete_order_keys_observed': len(new_keys),
            'policy_business_pass': True, 'source_versions_distinct': True,
            'scientific_RNG_draws': 0, 'proof_accepted': False, 'production_theorem_admission': False}


def compare_repeated_port_feature_projection(*, graph, literal, feature_module,
                                            reference_module, admitted_single_descriptor, hint):
    """Scalar-only deliberately disconnected projection; NEVER register/advice it.

    Duplicate component occurrences test repeated receptor and shared-occurrence
    arithmetic. This value is outside the connected-pair proposal grammar. It
    cannot be used by Controller, overlay, DFS, mining, certificate or learning.
    """
    require_tiny_graph(graph); core = graph._bound_core
    if len(admitted_single_descriptor['components']) != 1:
        raise ValueError('one actual admitted single component to echo in pure feature control')
    projection = copy.deepcopy(admitted_single_descriptor)
    component = projection['components'][0]
    if not component['ordered_receptor_ports']:
        raise ValueError('nonempty receptor feature control')
    projection['components'] = [copy.deepcopy(component), copy.deepcopy(component)]
    count = len(projection['members'])
    projection['component_member_occurrences'] = 2 * count; projection['shared_member_count'] = count
    projection['relation'] = 'synthetic_scalar_feature_projection_outside_registered_pool_grammar'
    projection['production_theorem_admission'] = False; projection['closed_lemma'] = False
    projection['descriptor_id'] = 'synthetic-feature-only-' + core.digest(projection)
    feature_graph = {'height': 24, 'totals': list(graph.totals),
        'marks': [[*p, v, graph.mark_refs[p]] for p, v in sorted(graph.marks.items())],
        'selected_keys': [key.data() for key in graph.order],
        'initial_selected_keys': [key.data() for key in graph.initial_selected]}
    decision = graph.decision(); d = [decision.kind, decision.row, decision.count, decision.generation]
    if decision.kind != 'branch': raise ValueError('scalar branch-feature control only')
    recipes, heads = graph.feature_views()
    observed = feature_module.menu_features(feature_graph, recipes, heads, [projection], [hint], d)
    expected = reference_module.literal_feature_menu(literal, [projection], [hint], d)
    if observed != expected: raise ValueError('independent repeated-port/shared component31-feature arithmetic')
    return {'schema': 'synthetic-scalar-feature-control-v1', 'feature_comparison_pass': True,
            'projection': projection, 'registered': False, 'advice_activated': False,
            'closed_lemma': False, 'production_theorem_admission': False, 'complete_menu': observed}


def require_stale_after_placement_and_rollback(graph):
    """Future graph transaction probe only, not a search or exhaustion certificate."""
    require_tiny_graph(graph); core = graph._bound_core; before = core.digest(graph.semantic_state())
    decision = graph.decision()
    if decision.kind not in ('branch', 'forced'): raise ValueError('legal current tiny transaction probe')
    cp = graph.checkpoint(); order = graph.ordered_domain(decision); key = order.first()
    graph._apply_legal(key)  # Mechanism transaction API; no proof-search or child-pruning claim.
    try:
        try: order.descriptor()
        except ValueError: pass
        else: raise ValueError('suspended order must be stale after placement')
    finally: graph.rollback(cp)
    try: order.descriptor()
    except ValueError: pass
    else: raise ValueError('old order stays stale even after exact rollback')
    if core.digest(graph.semantic_state()) != before: raise ValueError('complete graph restoration after stale probe')
    return {'placement_stale_rejected': True, 'rollback_stale_rejected': True,
            'exact_graph_restored': True, 'proof_accepted': False, 'production_theorem_admission': False}


def compare_paired_transaction_roundtrip(*, controller, literal_lifecycle, features31,
                                        reference_module, literal_key):
    """One caller-declared legal transaction, including non-earliest mechanism probes.

    This is not Executor/DFS scheduling, target search or child exhaustion. All
    caller objects must already carry the actual tiny-only source/receipt gates.
    Low-level pending-reader probes are labeled explicitly in the returned wire.
    """
    graph = controller.graph; literal = literal_lifecycle.point; require_tiny_graph(graph)
    raw = reference_module.key_tuple(literal_key)
    key = graph._bound_core.Key(raw[0], raw[1], raw[2])
    if not graph.legal(key) or not literal.legal(raw): raise ValueError('same complete legal primitive key')
    old_graph = graph._bound_core.digest(graph.semantic_state())
    old_controller = graph._bound_core.digest(controller.semantic_state())
    old_literal = copy.deepcopy(literal.state()); old_hints = copy.deepcopy(literal_lifecycle.hints)
    old_revision = literal_lifecycle.revision
    cp = controller.checkpoint(); lp = literal_lifecycle.checkpoint(); events = []
    try:
        graph._apply_legal(key); literal.apply(raw)
        controller.resync(); literal_lifecycle.resync()
        events.append({'kind': 'post_legal_mechanism_transaction',
            'point': compare_complete_graph(graph, literal),
            'lifecycle_and_features': compare_lifecycle_and_features(controller, literal_lifecycle,
                features31, reference_module), 'whole_point_state': graph.semantic_state(),
            'whole_hints': [hint.data() for hint in controller.states]})
    finally:
        controller.rollback(cp); literal_lifecycle.rollback(lp)
    if (graph._bound_core.digest(graph.semantic_state()) != old_graph
            or graph._bound_core.digest(controller.semantic_state()) != old_controller
            or literal.state() != old_literal or literal_lifecycle.hints != old_hints
            or literal_lifecycle.revision != old_revision):
        raise ValueError('complete paired point/hint/authority rollback')
    events.append({'kind': 'paired_rollback', 'point': compare_complete_graph(graph, literal),
        'lifecycle_and_features': compare_lifecycle_and_features(controller, literal_lifecycle,
            features31, reference_module), 'whole_point_state': graph.semantic_state(),
        'whole_hints': [hint.data() for hint in controller.states]})
    return {'schema': 'synthetic-paired-transaction-roundtrip-v1', 'literal_key': reference_module.key_data(raw),
        'events': events, 'paired_restore_pass': True, 'scheduler_search_action': False,
        'child_exhaustion_certificate': False, 'production_theorem_admission': False,
        'proof_accepted': False, 'resource_accepted': False, 'scientific_RNG_draws': 0}


def observe_qualified_case(*, graph, literal, controller, literal_lifecycle,
                           features31, reference_module, admitted_interfaces,
                           complete_groups, preparation_counters, preferred_keys=()):
    """Conditional public case observer, not a loader/worker/qualification oracle.

    ROOT supplies exact source-gated objects and separately authenticated tiny
    raw/body/full-pool receipts. This observes one pristine root state; it does not
    execute a sequence of transactions or certify the twelve case obligations.
    The returned complete snapshots are mechanical controls only. ROOT owns
    actual resource disposition and stores every result/event without elision.
    """
    header = require_tiny_graph(graph)
    if controller.graph is not graph or literal_lifecycle.point is not literal:
        raise ValueError('one paired tiny point/lifecycle context per observation')
    events = []
    def record(kind, value):
        events.append({'sequence': len(events), 'kind': kind, 'observation': value,
            'production_theorem_admission': False, 'proof_accepted': False})
    record('entire_authored_pool', compare_entire_tiny_pool(literal, admitted_interfaces,
        complete_groups, preparation_counters, reference_module))
    record('whole24_point_state', compare_complete_graph(graph, literal))
    record('whole_lifecycle_and31features', compare_lifecycle_and_features(controller,
        literal_lifecycle, features31, reference_module))
    decision = graph.decision()
    if decision.kind in ('branch', 'forced'):
        record('entire_order_and_fallback', compare_complete_order(graph, literal,
            preferred_keys=preferred_keys))
    elif preferred_keys:
        raise ValueError('dead/complete has no advice order')
    return {'schema': 'synthetic-current-case-observation-v1', 'instance_id': header['instance_id'],
        'events': events, 'point_state': graph.semantic_state(),
        'literal_point_state': literal.state(),
        'ordered_descriptors': [json.loads(item.text) for item in controller.descriptors],
        'hints': [hint.data() for hint in controller.states], 'tiny_observation_pass': True,
        'complete_twelve_case_qualification': False, 'full_independent_DFS_replay_accepted': False,
        'production_theorem_admission': False, 'proof_accepted': False,
        'resource_accepted': False, 'closed_lemma': False, 'native_accepted': False,
        'new_RL_training': False, 'scientific_RNG_draws': 0,
        'scope': 'One observed mechanical state only; future owned case transactions, full trace gates and terminal resource admission remain separate.'}


def inspect_unknown_trace_boundary(result):
    """Negative saved-data check only; not a replacement for full DFS replay.

    ROOT must obtain actual complete raw traces in separately admitted future
    qualification runs. No returned producer status proves child exhaustion.
    """
    if not result['status'].startswith('unknown_'): raise ValueError('actual UNKNOWN control result required')
    if (result.get('point_certificate') is not None or result.get('primitive_certificate_accepted') is not False
            or result.get('independent_full_replay_accepted') is not False or result.get('training_updates') != 0):
        raise ValueError('UNKNOWN cannot become an accepted proof or learner update')
    for event in result['events']:
        if event['kind'] in ('before_exhausted_child_exclusion', 'parent_local_exhausted_child_exclusion'):
            if event.get('child_status') != 'exhausted_finite_marked_subtree':
                raise ValueError('UNKNOWN child is never a parent-local exclusion reason')
    return {'schema': 'synthetic-UNKNOWN-negative-trace-scope-v1', 'negative_status_fields_pass': True,
            'full_independent_DFS_replay_accepted': False, 'production_theorem_admission': False,
            'scope': 'Actual child exhaustion and chronology still require complete independent replay, not a status string.'}
