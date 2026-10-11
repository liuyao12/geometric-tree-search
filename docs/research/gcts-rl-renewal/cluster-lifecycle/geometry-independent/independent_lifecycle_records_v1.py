"""Independent source-body/point/hint record reconstruction. No producer imports.

Prospective tiny adapter only. A separate freeze/owner is required before main
or any actual artifact acceptance. It does not load the actual Hilbert model.
"""
import copy
import itertools
from lifecycle_oracle_v2 import FiniteOracle, canonical, integer, key, points, sha

MARKING = 'injective-formula-ordered-mp-offset-v1'
VERSION = 'whole-cluster-lifecycle-v1'
CORE_SHA = 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'


def need(test, message):
    if not test:
        raise ValueError(message)


def json_equal(a, b):
    return canonical(a) == canonical(b)


def literal_model(record):
    """Enumerate the complete strict-prior unit-row fixture universe directly."""
    saved = record['state']['graph']
    height = len(saved['roots'])
    formulas = record['formulas']
    codes = {canonical(f): i for i, f in enumerate(formulas)}
    need(len(codes) == len(formulas), 'injective formula registry')
    context = {'ordered_local_premises': [], 'fixture': True}
    authority = {'label': 'synthetic_point_fixture_not_logic', 'activated': False, 'native_accepted': False}
    authority['epoch'] = sha(authority)
    registry_sha, context_sha = sha(formulas), sha(context)
    recipes, placements, palette = record['recipes'], [], []
    for i, recipe in enumerate(recipes):
        witness, premises = recipe['primitive_witness'], recipe['ordered_premise_formulas']
        rule = witness['rule']
        need(len(premises) in (0, 2), 'zero or two ordered fixture ports')
        if rule == 'mp':
            need(len(premises) == 2 and premises[1] == ['imp', premises[0], witness['formula']],
                 'point consistency is insufficient for literal MP')
        elif premises:
            need(rule == 'opaque_pair', 'nonlogical pair must be explicitly synthetic')
        else:
            need(rule == 'fixture_zero', 'no production primitive assumed in this toy adapter')
        out, inputs = codes[canonical(witness['formula'])], [codes[canonical(f)] for f in premises]
        palette.append({'id': recipe['id'], 'witness': witness, 'premises': premises, 'output': out, 'inputs': inputs})
        for row in range(height):
            for refs in itertools.product(range(row), repeat=len(inputs)):
                marks = {(1, row): out}
                for port, (source, code) in enumerate(zip(refs, inputs)):
                    if (1, source) in marks and marks[1, source] != code:
                        break
                    marks[1, source] = code
                    marks[2 + port, row] = source - row
                else:
                    t = [[0, row, 1]]
                    m = [[*p, v] for p, v in sorted(marks.items())]
                    command = copy.deepcopy(witness)
                    if rule == 'mp':
                        command.update(antecedent=refs[0], implication=refs[1])
                    elif inputs:
                        command['ordered_refs'] = list(refs)
                    prototype = {'recipe_id': recipe['id'], 'primitive_witness': witness,
                        'ordered_premise_formulas': premises,
                        'relative_ordered_input_offsets': [s - row for s in refs],
                        'orientation': 'identity', 't': [[x, y-row, v] for x, y, v in t],
                        'm': [[x, y-row, v] for x, y, v in m], 'marking_version': MARKING,
                        'formula_registry_sha256': registry_sha, 'authority_epoch': authority['epoch']}
                    identity = {'prototype_id': 'primitive-prototype-' + sha(prototype),
                        'prototype_preimage': prototype, 'transform': [0, row], 'context_id': context_sha,
                        'ordered_input_rows': list(refs), 'primitive_command': command, 't': t, 'm': m,
                        'authority_epoch': authority['epoch'], 'formula_registry_sha256': registry_sha}
                    placements.append({'key': [i, row, list(refs)], 't': t, 'm': m, 'identity': identity,
                                       'id': 'aggregate-primitive-' + sha(identity)})
    placements.sort(key=lambda p: key(p['key']))
    roots = [integer(v) for v in saved['roots']]
    initial = record['initial_marks']
    model_epoch = sha({'height': height, 'context': context, 'registry': registry_sha,
        'authority': authority['epoch'], 'recipes': [r['id'] for r in recipes],
        'fixed_marks': initial, 'roots': roots, 'seed_keys': [], 'marking_version': MARKING,
        'fixture': True, 'source_bindings': {}})
    binding = {'model_epoch': model_epoch, 'context_id': context_sha,
        'formula_registry_sha256': registry_sha, 'authority_epoch': authority['epoch'],
        'primitive_palette_sha256': sha(palette),
        'boundary_sha256': sha({'height': height, 'roots': roots, 'fixed_marks': initial, 'initial_selected': []}),
        'source_bindings_sha256': sha({}), 'marking_version': MARKING, 'orientation': 'identity',
        'core_sha256': CORE_SHA, 'native_accepted': False, 'engine_authority_activated': False}
    oracle = FiniteOracle([[0, r] for r in range(height)], [([0, r], roots[r]) for r in range(height)],
                          placements, initial, binding, {})
    need(model_epoch == saved['model_epoch'], 'complete independently reconstructed model epoch')
    return oracle, binding, placements, palette


AUTHORED_MEMBERS = {
    'later-p': [(0, 2, ())], 'two-p': [(0, 1, ()), (0, 2, ())],
    'mp-continuation': [(2, 1, ()), (4, 2, (0, 1))],
    'first': [(0, 0, ()), (0, 1, ())], 'second': [(0, 0, ()), (2, 2, ())],
    'repeated-ports': [(5, 2, (0, 1))], 'p-body': [(0, 1, ())],
    'mp': [(4, 2, (0, 1))], 'r-control': [(0, 0, ()), (0, 1, ())],
    'late-p': [(0, 2, ())],
}


def expected_body(name, palette):
    """Expected named toy body authored in pinned fixture source, not descriptor."""
    need(name in AUTHORED_MEMBERS, 'unknown authored toy body')
    keys = AUTHORED_MEMBERS[name]
    occupied = {k[1] for k in keys}
    inputs = sorted({r for k in keys for r in k[2] if r not in occupied})
    input_values, members = {}, []
    for index, row, refs in keys:
        recipe = palette[index]
        need(len(refs) == len(recipe['inputs']), 'body exact ordered references')
        for source, code in zip(refs, recipe['inputs']):
            if source in inputs:
                need(source not in input_values or input_values[source] == code, 'body receptor conflict')
                input_values[source] = code
        members.append({'row': row, 'recipe_id': recipe['id'], 'formula_code': recipe['output'],
                        'ordered_inputs': list(refs)})
    ports = []
    for i, row in enumerate(inputs):
        readers = []
        for index, member in zip((k[0] for k in keys), members):
            for port, source in enumerate(member['ordered_inputs']):
                if source == row:
                    readers.append({'reader_row': member['row'], 'primitive_input_port': port,
                                    'formula_code': input_values[row]})
        ports.append({'high_level_port': i, 'input_row': row, 'formula_code': input_values[row],
                      'new_occupancy': 0, 'readers': readers})
    body = {'kind': 'authored_primitive_proposal_not_closed_lemma', 'name': name,
        'canonical_input_rows': inputs, 'premise_codes': [input_values[r] for r in inputs],
        'primitive_members': members, 'dependency_bindings': [], 'native_accepted': False,
        'ordered_receptor_ports': ports}
    body['source_body_sha256'] = sha(body)
    body['mapped_body_sha256'] = body['source_body_sha256']
    return body


def expected_descriptor(descriptor, authority_record, oracle, palette, placements):
    need(json_equal(authority_record['graph_binding'], oracle.binding), 'authority binds full recipient graph')
    bodies = authority_record['bodies']
    need(len({n for n, _ in bodies}) == len(bodies), 'distinct body declaration identities')
    for name, body in bodies:
        need(json_equal(expected_body(name, palette), body), 'registry literal source body differs')
    source_bindings = authority_record['source_bindings']
    epoch = sha({'graph': oracle.binding, 'sources': source_bindings,
                 'bodies': [[n, sha(body)] for n, body in bodies], 'version': VERSION})
    need(epoch == authority_record['epoch'], 'complete body authority epoch')
    body = dict(bodies)[descriptor['body_name']]
    input_rows = descriptor['ordered_input_rows']; member_rows = descriptor['ordered_member_rows']
    need(len(input_rows) == len(body['canonical_input_rows']) and
         len(member_rows) == len(body['primitive_members']), 'complete source transport')
    height = len(oracle.required)
    for row in input_rows + member_rows:
        need(type(row) is int and 0 <= row < height, 'exact boundary row')
    need(all(a < b for a, b in zip(member_rows, member_rows[1:])), 'strict source body ordering')
    mapping = dict(zip(body['canonical_input_rows'], input_rows))
    mapping.update((m['row'], r) for m, r in zip(body['primitive_members'], member_rows))
    ids = {r['id']: i for i, r in enumerate(palette)}
    keys = tuple((ids[m['recipe_id']], row, tuple(mapping[s] for s in m['ordered_inputs']))
                 for m, row in zip(body['primitive_members'], member_rows))
    by_key = {key(p['key']): p for p in placements}
    total, marks, decorated = {}, {}, []
    for k in keys:
        p = by_key[k]; decorated.append(p)
        for point, value in points(p['t'], additive=True).items():
            total[point] = total.get(point, 0) + value
            need(total[point] <= 1, 'whole distinct occupancy')
        for point, value in points(p['m'], additive=False).items():
            need(point not in marks or marks[point] == value, 'whole marking agreement')
            marks[point] = value
    ports = []
    for port, row, code in zip(body['ordered_receptor_ports'], input_rows, body['premise_codes']):
        readers = [{'reader_row': mapping[r['reader_row']], 'primitive_input_port': r['primitive_input_port'],
                    'formula_code': code, 'offset_value': row - mapping[r['reader_row']]} for r in port['readers']]
        ports.append({'high_level_port': port['high_level_port'], 'input_row': row,
                      'formula_code': code, 'new_occupancy': 0, 'readers': readers})
        need((1, row) not in marks or marks[1, row] == code, 'noninjective receptor alias agreement')
        marks[1, row] = code
    priority = integer(descriptor['fixed_priority']); need(priority >= 0, 'fixed priority')
    expected = {'version': VERSION, 'relation': body['kind'], 'graph_binding': oracle.binding,
        'source_bindings': source_bindings, 'body_authority_epoch': epoch, 'body_name': body['name'],
        'body_sha256': sha(body), 'source_body_sha256': body['source_body_sha256'],
        'mapped_body_sha256': body['mapped_body_sha256'], 'dependency_bindings': [],
        'ordered_input_rows': input_rows, 'ordered_member_rows': member_rows,
        'ordered_receptor_ports': ports, 'fixed_priority': priority,
        'members': [[i, row, list(refs)] for i, row, refs in keys],
        'full_member_ids': [p['id'] for p in decorated],
        'full_identity_preimages': [p['identity'] for p in decorated],
        'aggregate_t': [[*p, v] for p, v in sorted(total.items())],
        'aggregate_m': [[*p, v] for p, v in sorted(marks.items())],
        'native_accepted': False, 'native_authority_activated': False}
    expected['descriptor_id'] = 'whole-cluster-' + sha(expected)
    need(json_equal(expected, descriptor), 'descriptor must instantiate exact registered source body')
    return {'members': keys, 'total': total, 'marks': marks}


def check_graph_state(oracle, saved, palette):
    excludes = [k for row in saved['excluded'] for k in row]
    state = oracle.state(saved['order'], excludes)
    need(saved['totals'] == [state['total'][0, r] for r in range(len(oracle.required))], 'exact occupancy totals')
    marks = [[*p, v, state['mark_refs'][p]] for p, v in sorted(state['marks'].items())]
    need(saved['marks'] == marks, 'assigned marks and reference counts, including zero')
    generations = [[list(k[:2]) + [list(k[2])], state['generations'][k]] for k in sorted(state['selected'])]
    need(json_equal(saved['selected_generations'], generations), 'exact selected generations')
    domains = []
    for row, raw in enumerate(saved['domains']):
        factors = []
        if state['total'][0, row] == 0:
            for i, recipe in enumerate(palette):
                if (1, row) in state['marks'] and state['marks'][1, row] != recipe['output']:
                    continue
                if not recipe['inputs']:
                    factors.append([i, 0, 0, False, 1]); continue
                masks = []
                for port, code in enumerate(recipe['inputs']):
                    mask = 0
                    for source in range(row):
                        if ((1, source) not in state['marks'] or state['marks'][1, source] == code) and (
                            (2 + port, row) not in state['marks'] or state['marks'][2 + port, row] == source-row):
                            mask |= 1 << source
                    masks.append(mask)
                a, b = masks; different = recipe['inputs'][0] != recipe['inputs'][1]
                count = bin(a).count('1') * bin(b).count('1') - (bin(a & b).count('1') if different else 0)
                if count:
                    factors.append([i, a, b, different, count])
        base = oracle.state(saved['order'])['domains'].get((0, row), [])
        removed = sorted(k for k in state['excluded'] if k in base)
        expected = {'factors': factors, 'base_count': len(base),
                    'excluded_legal': [[i, r, list(refs)] for i, r, refs in removed],
                    'count': len(state['domains'].get((0, row), []))}
        need(json_equal(expected, raw), 'complete factor/count/exclusion reconstruction')
        domains.append(expected)
    kind, point = state['decision']
    row = point[1] if point is not None else None
    decision = [kind, row, len(state['domains'].get(point, ())) if point is not None else 0,
                oracle.roots[point] if point is not None else None]
    return state, decision


def check_snapshot(record, authorities):
    oracle, binding, placements, palette = literal_model(record)
    saved = record['state']
    state, decision = check_graph_state(oracle, saved['graph'], palette)
    compiled, descriptors = [], record['descriptors']
    need(saved['descriptor_ids'] == [d['descriptor_id'] for d in descriptors], 'exact fixed descriptor registry')
    need(type(saved['hint_revision']) is int and saved['hint_revision'] >= 0, 'hint revision exact nonnegative')
    need(len(saved['hint_states']) == len(descriptors), 'whole lifecycle state census')
    for descriptor, hint in zip(descriptors, saved['hint_states']):
        authority_record = authorities[descriptor['body_authority_epoch']]
        c = expected_descriptor(descriptor, authority_record, oracle, palette, placements)
        compiled.append(c)
        view = oracle.hint_view(c, state)
        need(hint['status'] == view['status'] and
             json_equal(hint['eligible'], [[i, r, list(refs)] for i, r, refs in view['eligible']]),
             'independent whole-cluster lifecycle view')
        need(hint['decision'] == decision and hint['revision'] == saved['hint_revision'], 'current decision/cache revision')
        if view['status'] == 'retired':
            need(hint['reason'] == 'pending_member_illegal', 'whole retirement reason')
        else:
            need(hint['reason'] is None, 'valid hint has no invalidation reason')
    raw = [[list(k[:2]) + [list(k[2])] for k in state['domains'].get((0, r), ())]
           for r in range(len(oracle.required))]
    need(json_equal(raw, record['complete_domains']), 'every ordered complete primitive domain')
    ordered = oracle.ordered_domain(state, compiled)
    if decision[0] in ('branch', 'forced'):
        need(set(ordered) == set(state['domains'][0, decision[1]]) and
             len(ordered) == len(state['domains'][0, decision[1]]), 'complete preferred-plus-fallback permutation')
    return {'oracle': oracle, 'state': state, 'compiled': compiled, 'decision': decision,
            'placements': len(placements), 'current_candidates': sum(map(len, state['domains'].values())),
            'descriptors': len(descriptors), 'ordered': ordered}
