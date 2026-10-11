"""Static primitive expansion only: no search, native request, or engine adapter.

The independently audited transported interfaces are inputs, not native authority.
Every local assumption occurrence remains an ordered zero-occupancy alias.
"""
import copy
import gzip
import hashlib
import json
import resource
import signal
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
VERSION = 'hilbert-primitive-aggregate-static-v1'
MARKING_VERSION = 'injective-formula-ordered-mp-offset-v1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_pin(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def save(path, value):
    data = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    if path.exists():
        raise ValueError('immutable output already exists: ' + str(path))
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == '.gz' else data)


def assert_bound(plan):
    for pin in plan['inputs'] + plan['sources']:
        expected = {k: pin[k] for k in ('path', 'sha256', 'bytes')}
        assert file_pin(ROOT / pin['path']) == expected, 'source/input changed: ' + pin['path']
    for pin in plan['preserved_files']:
        assert file_pin(ROOT / pin['path']) == pin, 'preserved evidence changed: ' + pin['path']


def recipe_key(command, ordered_formulas):
    witness = {k: copy.deepcopy(v) for k, v in command.items() if k not in ('antecedent', 'implication')}
    return {'primitive_witness': witness, 'ordered_premise_formulas': copy.deepcopy(ordered_formulas)}


def expand(record, by_name):
    definition = record['definition']
    nodes = {f'input:{k}': {'formula': copy.deepcopy(f), 'kind': 'ordered_local_assumption', 'index': k}
             for k, f in enumerate(definition['premises'])}
    leaves, aliases, calls = [], [], []

    def walk(name, supplied, stack, path):
        if name in stack:
            raise ValueError('cyclic source block dependency')
        block = by_name[name]['definition']
        assert len(supplied) == len(block['premises'])
        assert [nodes[x]['formula'] for x in supplied] == block['premises']
        local = []
        for index, original in enumerate(block['proof']):
            cmd = copy.deepcopy(original)
            source = {'definition': name, 'command_index': index, 'path': path + [index],
                      'source_body_sha256': by_name[name]['source_body_sha256'],
                      'mapped_body_sha256': by_name[name]['body_sha256']}
            if cmd['rule'] == 'assumption':
                k = cmd['index']
                assert type(k) is int and 0 <= k < len(supplied)
                node = supplied[k]
                assert nodes[node]['formula'] == cmd['formula']
                aliases.append({'source_occurrence': source, 'ordered_assumption_index': k,
                                'alias_to': node, 'formula': cmd['formula'], 't': [], 'm': [],
                                'new_occupancy': 0})
            elif cmd['rule'] == 'block':
                refs = cmd['inputs']
                assert all(type(r) is int and 0 <= r < index for r in refs)
                args = [local[r] for r in refs]
                assert cmd['name'] in by_name
                assert cmd['name'] in by_name[name]['dependencies']
                before = len(leaves)
                node = walk(cmd['name'], args, stack + [name], path + [index])
                assert nodes[node]['formula'] == cmd['formula']
                calls.append({'source_occurrence': source, 'dependency_name': cmd['name'],
                              'ordered_input_nodes': args, 'output_node': node,
                              'leaf_interval': [before, len(leaves)], 'new_macro_occupancy': 0})
            else:
                assert cmd['rule'] in ('axiom', 'instantiate', 'eq_subst', 'mp')
                refs = []
                if cmd['rule'] == 'mp':
                    refs = [cmd['antecedent'], cmd['implication']]
                    assert all(type(r) is int and 0 <= r < index for r in refs)
                inputs = [local[r] for r in refs]
                if inputs:
                    a, implication = [nodes[x]['formula'] for x in inputs]
                    assert implication == ['imp', a, cmd['formula']], 'literal ordered MP mismatch'
                node = f'leaf:{len(leaves)}'
                leaf = {'node': node, 'source_occurrence': source,
                        'primitive_witness': {k: v for k, v in cmd.items() if k not in ('antecedent', 'implication')},
                        'ordered_input_nodes': inputs,
                        'ordered_premise_formulas': [nodes[x]['formula'] for x in inputs],
                        'formula': cmd['formula']}
                leaves.append(leaf)
                nodes[node] = {'formula': cmd['formula'], 'kind': 'primitive_leaf'}
            assert nodes[node]['formula'] == cmd['formula']
            local.append(node)
        assert local and nodes[local[-1]]['formula'] == block['conclusion']
        return local[-1]

    output = walk(definition['name'], list(nodes), [], [])
    return {'definition_name': definition['name'], 'family': record['family'],
            'constant_map': record['constant_map'], 'source_block': record['source_block'],
            'source_body_sha256': record['source_body_sha256'], 'mapped_body_sha256': record['body_sha256'],
            'ordered_dependencies': record['dependencies'], 'ordered_local_premises': definition['premises'],
            'conclusion': definition['conclusion'], 'input_nodes': list(nodes)[:len(definition['premises'])],
            'leaves': leaves, 'assumption_aliases': aliases, 'recursive_calls': calls, 'output_node': output}


def point_data(command, ordered_rows, ordered_formulas, row, codes):
    marking = {(1, row): codes[canonical(command['formula'])]}
    ports = []
    for k, (source_row, formula) in enumerate(zip(ordered_rows, ordered_formulas)):
        assert type(source_row) is int and 0 <= source_row < row
        point, value = (1, source_row), codes[canonical(formula)]
        if point in marking and marking[point] != value:
            raise ValueError('inconsistent local marking assignment')
        marking[point] = value
        marking[(2 + k, row)] = source_row - row
        ports.append({'port_index': k, 'input_row': source_row, 'formula_code': value,
                      'receptor_point': [1, source_row], 'offset_mark_point': [2 + k, row],
                      'offset_value': source_row - row})
    return {'t': [[0, row, 1]], 'm': [[x, y, v] for (x, y), v in sorted(marking.items())],
            'ordered_ports': ports}


def decorate(command, ordered_rows, ordered_formulas, row, recipe, context_id, authority, codes, registry_sha):
    points = point_data(command, ordered_rows, ordered_formulas, row, codes)
    # Normalization translates points, not values: relative offsets are invariant.
    relative = {'t': [[x, y - row, v] for x, y, v in points['t']],
                'm': [[x, y - row, v] for x, y, v in points['m']]}
    prototype_preimage = {'recipe_id': recipe['id'], 'primitive_witness': recipe['primitive_witness'],
                          'ordered_premise_formulas': recipe['ordered_premise_formulas'],
                          'relative_ordered_input_offsets': [r - row for r in ordered_rows],
                          'orientation': 'identity', **relative, 'marking_version': MARKING_VERSION,
                          'formula_registry_sha256': registry_sha, 'authority_epoch': authority['epoch']}
    placement_preimage = {'prototype_id': 'primitive-prototype-' + digest(prototype_preimage),
                          'prototype_preimage': prototype_preimage, 'transform': [0, row],
                          'context_id': context_id, 'ordered_input_rows': ordered_rows,
                          'primitive_command': command, 't': points['t'], 'm': points['m'],
                          'authority_epoch': authority['epoch'], 'formula_registry_sha256': registry_sha}
    return {'id': 'aggregate-primitive-' + digest(placement_preimage), 'row': row, 'recipe_id': recipe['id'],
            'command': command, 'ordered_inputs': ordered_rows, **points,
            'identity_preimage': placement_preimage, 'donor_occurrence_provenance': []}


def aggregate(placements):
    by_id = {}
    for p in placements:
        if p['id'] in by_id:
            assert p['identity_preimage'] == by_id[p['id']]['identity_preimage']
        by_id[p['id']] = p
    total, marking = {}, {}
    for p in by_id.values():
        for x, y, value in p['t']:
            total[x, y] = total.get((x, y), 0) + value
            assert total[x, y] <= 1
        for x, y, value in p['m']:
            assert (x, y) not in marking or marking[x, y] == value
            marking[x, y] = value
    return {'constituent_ids': sorted(by_id), 't': [[x, y, v] for (x, y), v in sorted(total.items())],
            'm': [[x, y, v] for (x, y), v in sorted(marking.items())]}


def projected_ports(expansion, node_rows, placements):
    by_row = {p['row']: p for p in placements}
    result = []
    for k, node in enumerate(expansion['input_nodes']):
        source_row = node_rows[node]
        readers = []
        for leaf in expansion['leaves']:
            for primitive_port, input_node in enumerate(leaf['ordered_input_nodes']):
                if input_node == node:
                    reader_row = node_rows[leaf['node']]
                    p = by_row[reader_row]
                    readers.append({'reader_row': reader_row, 'primitive_input_port': primitive_port,
                                    'reader_placement_id': p['id'],
                                    **{a: b for a, b in p['ordered_ports'][primitive_port].items() if a != 'port_index'}})
        result.append({'high_level_port': k, 'input_node': node, 'input_row': source_row,
                       'formula': expansion['ordered_local_premises'][k], 'readers': readers,
                       'new_occupancy': 0, 'adds_macro_offset_mark': False})
    return result


def command_at(leaf, node_rows):
    cmd = copy.deepcopy(leaf['primitive_witness'])
    inputs = [node_rows[x] for x in leaf['ordered_input_nodes']]
    if cmd['rule'] == 'mp':
        cmd['antecedent'], cmd['implication'] = inputs
    return cmd, inputs


def build_canonical(expansion, theory, recipe_lookup, authority, codes, registry_sha):
    premises = expansion['ordered_local_premises']
    context = {'theory': theory, 'ordered_local_premises': premises}
    context_id = digest(context)
    node_rows = {x: k for k, x in enumerate(expansion['input_nodes'])}
    seeds = []
    for k, f in enumerate(premises):
        preimage = {'kind': 'fixed_local_context_seed', 'context_id': context_id,
                    'command': {'rule': 'assumption', 'index': k, 'formula': f},
                    'orientation': 'identity', 'transform': [0, k], 't': [[0, k, 1]],
                    'm': [[1, k, codes[canonical(f)]]], 'formula_registry_sha256': registry_sha,
                    'marking_version': MARKING_VERSION, 'authority_epoch': authority['epoch']}
        seeds.append({'id': 'local-boundary-seed-' + digest(preimage), 'identity_preimage': preimage,
                      'row': k, 'formula': f, 't': preimage['t'], 'm': preimage['m'], 'generation': 0,
                      'scope': 'this definition local context, not an added recipient axiom'})
    placements = []
    for leaf in expansion['leaves']:
        row = len(premises) + len(placements)
        cmd, refs = command_at(leaf, node_rows)
        key = recipe_key(cmd, leaf['ordered_premise_formulas'])
        p = decorate(cmd, refs, leaf['ordered_premise_formulas'], row, recipe_lookup[canonical(key)],
                     context_id, authority, codes, registry_sha)
        p['donor_occurrence_provenance'] = [leaf['source_occurrence']]
        placements.append(p)
        node_rows[leaf['node']] = row
    return {'context': context, 'context_id': context_id, 'ordered_input_seeds': seeds,
            'node_rows': node_rows, 'primitive_placements': placements,
            'cluster_aggregate': aggregate(placements),
            'ordered_receptor_ports': projected_ports(expansion, node_rows, placements),
            'conclusion_row': node_rows[expansion['output_node']],
            'local_boundary_rows': len(premises) + len(placements),
            'boundary_context_is_not_the_global_three_premise_recipient': True}


def example_from_expansions(expansions, original, theory, recipe_lookup, authority, codes, registry_sha):
    by_name = {e['definition_name']: e for e in expansions}
    context, context_id = original['context'], digest(original['context'])
    assert context['theory'] == theory
    placements, intern = [], {}
    for k, formula in enumerate(context['ordered_local_premises']):
        cmd = {'rule': 'assumption', 'index': k, 'formula': formula}
        key = recipe_key(cmd, [])
        p = decorate(cmd, [], [], k, recipe_lookup[canonical(key)], context_id, authority, codes, registry_sha)
        p['donor_occurrence_provenance'] = [{'kind': 'recipient_local_premise', 'index': k}]
        placements.append(p)
    clusters = []
    for old_cluster in original['clusters']:
        e = by_name[old_cluster['source_definition']]
        node_rows = dict(zip(e['input_nodes'], old_cluster['ordered_inputs']))
        assert [placements[r]['command']['formula'] for r in old_cluster['ordered_inputs']] == e['ordered_local_premises']
        members = []
        for leaf in e['leaves']:
            cmd, refs = command_at(leaf, node_rows)
            key = canonical({'command': cmd, 'context_id': context_id})
            if key in intern:
                row = intern[key]
                p = placements[row]
                assert p['command'] == cmd and p['ordered_inputs'] == refs
                p['donor_occurrence_provenance'].append(leaf['source_occurrence'])
            else:
                row = len(placements)
                p = decorate(cmd, refs, leaf['ordered_premise_formulas'], row,
                             recipe_lookup[canonical(recipe_key(cmd, leaf['ordered_premise_formulas']))],
                             context_id, authority, codes, registry_sha)
                p['donor_occurrence_provenance'] = [leaf['source_occurrence']]
                intern[key] = row
                placements.append(p)
            node_rows[leaf['node']] = row
            members.append(p)
        cluster = {'name': old_cluster['name'], 'definition_name': e['definition_name'],
                   'ordered_inputs': old_cluster['ordered_inputs'], 'node_rows': node_rows,
                   'conclusion_row': node_rows[e['output_node']], 'aggregate': aggregate(members),
                   'ordered_receptor_ports': projected_ports(e, node_rows, members),
                   'legacy_constituent_ids': old_cluster['constituent_ids']}
        assert cluster['conclusion_row'] == old_cluster['conclusion_row']
        assert cluster['aggregate']['t'] == old_cluster['t'] and cluster['aggregate']['m'] == old_cluster['m']
        clusters.append(cluster)
    assert len(placements) == len(original['primitive_placements']) == 24
    legacy = []
    for p, old in zip(placements, original['primitive_placements']):
        for field in ('row', 'command', 'ordered_inputs', 't', 'm'):
            assert p[field] == old[field], 'authored example mismatch ' + field
        old_id = 'primitive-' + digest({'command': p['command'], 'context_id': context_id}) + '@' + str(p['row'])
        assert old_id == old['id']
        legacy.append({'row': p['row'], 'legacy_id': old_id, 'full_decorated_id': p['id'],
                       'legacy_identity_scope': 'command/context and row only; not registry/authority'})
    a, b = [set(c['aggregate']['constituent_ids']) for c in clusters]
    joined = aggregate(placements[3:])
    assert joined['t'] == original['composition']['derived_aggregate']['t']
    assert joined['m'] == original['composition']['derived_aggregate']['m']
    return {'status': 'static_authored_example_reconstructed', 'context': context, 'context_id': context_id,
            'placements': placements, 'clusters': clusters, 'legacy_label_correspondence': legacy,
            'shared_constituent_ids': sorted(a & b), 'shared_rows': [p['row'] for p in placements if p['id'] in a & b],
            'first_units': len(a), 'second_units': len(b), 'distinct_derived_units': len(a | b),
            'new_second_units': len(b - a), 'derived_aggregate': joined,
            'full_aggregate_with_three_seeds': aggregate(placements),
            'authored_design_not_a_discovered_chained_proof': True,
            'native_acceptance': 'not_run', 'search_conformance': 'not_run'}


def grammar(height, recipes, codes, context, authority, registry_sha):
    mp = [r for r in recipes if r['primitive_witness']['rule'] == 'mp']
    zero = [r for r in recipes if r['primitive_witness']['rule'] != 'mp']
    raw = len(zero) + len(mp) * (height - 1) ** 2
    strict = len(zero) * height + len(mp) * sum(r * r for r in range(height))
    conflicts_per_diagonal = sum(r['ordered_premise_formulas'][0] != r['ordered_premise_formulas'][1] for r in mp)
    conflicts = conflicts_per_diagonal * sum(range(height))
    boundary = {'required': [[0, r] for r in range(height)], 'root_generations': [[0, r, 0] for r in range(height)],
                'fixed_initial_local_seeds': [{'recipe_id': r['id'], 'row': r['primitive_witness']['index'], 'generation': 0}
                                             for r in zero if r['primitive_witness']['rule'] == 'assumption'],
                'fixed_target_m': [[1, height - 1, codes[canonical(['pred', 'Incident', [['fun', 'R', []], ['fun', 'n', []]]])]]],
                'fixed_exterior_m': [[1, r, -1] for r in range(1 - height, 0)],
                'all_root_obligations_generation_zero': True}
    return {'height': height, 'context': context, 'context_id': digest(context), 'boundary': boundary,
            'primitive_recipe_ids': [r['id'] for r in recipes], 'orientation': 'identity',
            'transform_grammar': 'vertical integer translation only', 'prototype_origin': [0, 0],
            'mp_offset_domain': [1 - height, -1], 'mp_offset_order': ['antecedent', 'implication'],
            'positive_support_alignment_domain': [0, height - 1],
            'strict_prior_recipient_binding': '0 <= antecedent_row, implication_row < output_row < height',
            'assumption_availability': 'Only the three declared local hypotheses; each may be cited again at any row. No interface-specific hypotheses are added.',
            'prototype_identity_recipe': 'full recipe witness, ordered formulas/offsets, exact relative t/m, registry, orientation and authority',
            'placement_identity_recipe': 'prototype plus vertical transform, exact placed t/m, literal primitive command, ordered refs and recipient context',
            'counts': {'raw_prototypes': raw, 'raw_positive_support_alignments': raw * height,
                       'strict_prior_bindings_before_local_mark_agreement': strict,
                       'inconsistent_local_mark_functions': conflicts,
                       'locally_consistent_strict_prior_bindings': strict - conflicts},
            'counts_are_grammar_census_not_initial_legal_graph_degrees': True,
            'materialized_complete_placement_catalog': False,
            'initial_graph_and_t_m_dependency_indexes': 'not_constructed',
            'base_fallback': 'future executor must enumerate all recipes and both ordered prior references, no sampled or cluster-only domains',
            'authority_epoch': authority['epoch'], 'formula_registry_sha256': registry_sha,
            'semantic_relation_to_5_macro_rows': 'different primitive boundary, not an exact macro-board bijection',
            'conditional_padding_lift': {'maximum_leaf_count_per_old_macro': 13, 'old_macro_height': 5,
                                        'maximum_unshared_primitive_leaves': 65,
                                        'status': 'conditional one-way proposed lift only; not constructed or proved here',
                                        'conditions': ['macro certificate is valid', 'all used bodies are these expanded definitions',
                                                       'local premises preserved', 'all references rebased strictly prior',
                                                       'valid I.2 axiom padding inserted before final conclusion',
                                                       'recipient primitive inventory includes every expanded recipe']}}


def main():
    start = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('180 second static production alarm')))
    signal.alarm(180)
    plan_path = HERE / 'plan-v1.json'
    plan = load(plan_path)
    assert_bound(plan)
    roles = {p['role']: ROOT / p['path'] for p in plan['inputs']}
    cert, old = load(roles['transport_certificate']), load(roles['authored_example'])
    source_audit, catalog_audit = load(roles['transport_audit']), load(roles['row_catalog_audit'])
    assert source_audit['status'] == 'passed_finite_structural_audit'
    assert catalog_audit['status'] == 'passed_independent_finite_catalog_audit'
    assert source_audit['certificate_sha256'] == file_pin(roles['transport_certificate'])['sha256']
    assert catalog_audit['catalog_sha256'] == file_pin(roles['row_catalog'])['sha256']
    theory = cert['recipient_theory']
    by_name = {r['definition']['name']: r for r in cert['records']}
    assert len(by_name) == len(cert['records']) == 171
    # Exact source bodies and strict dependency declaration identities are kept.
    ranks = {r['definition']['name']: i for i, r in enumerate(cert['records'])}
    for r in cert['records']:
        body = {k: v for k, v in r['definition'].items() if k != 'name'}
        assert digest(body) == r['body_sha256']
        assert all(dep in by_name for dep in r['dependencies'])
        assert all(ranks[dep] < ranks[r['definition']['name']] for dep in r['dependencies'])
    expanded = [expand(r, by_name) for r in cert['records']]
    codes = copy.deepcopy(old['formula_codes'])
    keys = set(map(canonical, codes))
    assert len(keys) == len(codes)
    new_values = {}
    for e in expanded:
        for f in e['ordered_local_premises'] + [leaf['formula'] for leaf in e['leaves']]:
            key = canonical(f)
            if key not in keys:
                new_values[key] = f
    codes.extend(new_values[k] for k in sorted(new_values))
    code_lookup = {canonical(f): i for i, f in enumerate(codes)}
    registry_sha = digest(codes)
    authority = {'label': 'inactive_static_structural_transport', 'activated': False, 'native_accepted': False,
                 'source_primitive_soundness': 'requires independent logical audit for this finite inventory',
                 'source_certificate_pin': file_pin(roles['transport_certificate']),
                 'source_structural_audit_pin': file_pin(roles['transport_audit']),
                 'reviewed_source_argument_pin': file_pin(roles['source_argument']),
                 'reviewed_source_argument_review_pin': file_pin(roles['source_argument_review']),
                 'original_native_donor_binding': cert['source_native_binding'],
                 'recipient_theory_sha256': digest(theory),
                 'native_program_and_compiler_correspondence': 'open'}
    authority['epoch'] = digest(authority)
    recipes = {}
    for e in expanded:
        for leaf in e['leaves']:
            key = recipe_key(leaf['primitive_witness'], leaf['ordered_premise_formulas'])
            text = canonical(key)
            recipes.setdefault(text, {**key, 'source_occurrence_aliases': []})
            recipes[text]['source_occurrence_aliases'].append({'root_definition': e['definition_name'],
                                                             'leaf_node': leaf['node'], **leaf['source_occurrence']})
    for k, f in enumerate(old['context']['ordered_local_premises']):
        key = recipe_key({'rule': 'assumption', 'index': k, 'formula': f}, [])
        recipes[canonical(key)] = {**key, 'source_occurrence_aliases': [], 'scope': 'recipient ordered local premise only'}
    ordered_recipes = []
    for text in sorted(recipes):
        r = recipes[text]
        preimage = {'recipe': json.loads(text), 'primitive_authority_epoch': authority['epoch'],
                    'recipient_theory_sha256': digest(theory), 'marking_version': MARKING_VERSION,
                    'formula_registry_sha256': registry_sha}
        if r['primitive_witness']['rule'] == 'assumption':
            preimage['local_context_id'] = digest(old['context'])
        r['identity_preimage'] = preimage
        r['id'] = 'primitive-recipe-' + digest(preimage)
        ordered_recipes.append(r)
    lookup = {canonical(recipe_key(r['primitive_witness'], r['ordered_premise_formulas'])): r for r in ordered_recipes}
    for e in expanded:
        e['canonical_embedding'] = build_canonical(e, theory, lookup, authority, code_lookup, registry_sha)
        for leaf in e['leaves']:
            leaf['recipe_id'] = lookup[canonical(recipe_key(leaf['primitive_witness'], leaf['ordered_premise_formulas']))]['id']
    example = example_from_expansions(expanded, old, theory, lookup, authority, code_lookup, registry_sha)
    counts = {'named_definitions': len(expanded), 'source_body_leaf_occurrences': sum(len(e['leaves']) for e in expanded),
              'family_counts': dict(Counter(e['family'] for e in expanded)),
              'family_leaf_counts': {f: sorted({len(e['leaves']) for e in expanded if e['family'] == f}) for f in sorted({e['family'] for e in expanded})},
              'maximum_body_leaf_count': max(len(e['leaves']) for e in expanded),
              'primitive_recipe_types': len(ordered_recipes),
              'primitive_recipe_rules': dict(Counter(r['primitive_witness']['rule'] for r in ordered_recipes)),
              'formula_codes': len(codes), 'preserved_authored_formula_prefix': len(old['formula_codes']),
              'assumption_alias_occurrences': sum(len(e['assumption_aliases']) for e in expanded),
              'recursive_block_call_occurrences': sum(len(e['recursive_calls']) for e in expanded),
              'duplicate_premise_interfaces': sum(len(set(map(canonical, e['ordered_local_premises']))) < len(e['ordered_local_premises']) for e in expanded),
              'noninjective_constant_maps': sum(len(set(map(canonical, r['constant_map'].values()))) < len(r['constant_map']) for r in cert['records'])}
    models = [grammar(n, ordered_recipes, code_lookup, old['context'], authority, registry_sha) for n in (24, 65)]
    common = {'version': VERSION, 'plan_pin': file_pin(plan_path), 'authority': authority,
              'input_bindings': plan['inputs'], 'formula_registry_sha256': registry_sha}
    expansion_output = {**common, 'status': 'static_expansion_produced_pending_independent_audit',
                        'counts': counts, 'formula_codes': codes, 'records': expanded,
                        'original_dependency_aliases': cert['dependency_aliases']}
    model_output = {**common, 'status': 'declared_parametric_primitive_model_not_complete_graph',
                    'formula_codes': codes, 'recipes': ordered_recipes, 'models': models,
                    'primitive_palette_alias_rule': 'Full witness and ordered formula interface equality; all named source definitions and donor occurrences remain distinct records.',
                    'graph_required_before_any_search': ['enumerate complete placement universe and all t/m dependencies',
                                                         'compare independent graph and exact rollback',
                                                         'enforce global dead then forced then earliest generation',
                                                         'validate proposal continuation with same complete base fallback'],
                    'aggregate_family_embedding_obligations': ['ordered body-preserving primitive embeddings',
                                                              'local premises earlier than their actual readers, not necessarily before unrelated leaves',
                                                              'input aliases have no occupancy', 'shared full decorated placements counted once',
                                                              'a concrete family embedding translates rigidly only',
                                                              'complete finite embedding enumeration remains open']}
    save(HERE / 'expansions-v1.json.gz', expansion_output)
    save(HERE / 'model-v1.json.gz', model_output)
    save(HERE / 'example-correspondence-v1.json', {**common, **example})
    assert_bound(plan)
    elapsed = time.perf_counter() - start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        peak *= 1024
    receipt = {'status': 'static_production_complete_pending_independent_audit', 'plan_pin': file_pin(plan_path),
               'counts': counts, 'model_grammar_counts': {str(m['height']): m['counts'] for m in models},
               'output_pins': [file_pin(HERE / p) for p in ('expansions-v1.json.gz', 'model-v1.json.gz', 'example-correspondence-v1.json')],
               'production_seconds_before_receipt_write': elapsed, 'peak_rss_bytes': peak,
               'native_queries': 0, 'target_searches': 0, 'point_placement_graphs': 0, 'existing_engine_activation': False,
               'scope': 'Complete 171 static source-body expansions, exact canonical aggregates and authored shared example only; primitive logical soundness pending independent audit.',
               'remaining_gaps': ['complete primitive placement/catalog and graph', 'general aggregate embedding family enumeration',
                                  'scheduler and rollback implementation conformance', 'conditional 65 row lift construction',
                                  'formal compiler/native correspondence', 'whole native proof acceptance']}
    save(HERE / 'production-v1.json', receipt)
    signal.alarm(0)
    print(json.dumps({'status': receipt['status'], 'counts': counts, 'seconds': elapsed, 'peak_rss_bytes': peak}), flush=True)


if __name__ == '__main__':
    main()
