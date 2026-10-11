"""Independent source families and exact descriptor transports; no producer imports.

The only executable libraries are our pinned prior symbolic/expansion auditors.
No authored 24-row word is read. Loading actual data needs a frozen root gate.
"""
import copy
from full_point_oracle_v1 import canonical, digest, integer, need, points, decorate

VERSION = 'whole-cluster-lifecycle-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'
CORE_SHA = 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'


def equal(a, b, label):
    need(canonical(a) == canonical(b), label)


def key(value):
    need(type(value) is list and len(value) == 3 and type(value[2]) is list, 'literal key')
    return integer(value[0]), integer(value[1]), tuple(integer(v) for v in value[2])


def key_data(value):
    return [value[0], value[1], list(value[2])]


def graph_binding(state, context, authority, formulas, source_bindings, seeds, fixed):
    palette = [dict(id=r['id'], witness=r['witness'], premises=r['premises'],
                    output=r['output'], inputs=list(r['inputs'])) for r in state.recipes]
    return dict(model_epoch=state.epoch, context_id=digest(context),
        formula_registry_sha256=digest(formulas), authority_epoch=authority['epoch'],
        primitive_palette_sha256=digest(palette),
        boundary_sha256=digest(dict(height=state.height, roots=state.roots,
            fixed_marks=sorted(fixed), initial_selected=[key_data(k) for k in seeds])),
        source_bindings_sha256=digest(source_bindings), marking_version=MARKING,
        orientation='identity', core_sha256=CORE_SHA,
        native_accepted=False, engine_authority_activated=False)


def projection(expansion, embedding, codes):
    """Derive the compact projection from an independently expanded source body."""
    members = []
    for placement in embedding['primitive_placements']:
        command = placement['command']
        witness = {k: copy.deepcopy(v) for k, v in command.items()
                   if k not in ('formula', 'antecedent', 'implication')}
        if 'universal' in witness:
            witness['universal_formula_code'] = codes[canonical(witness.pop('universal'))]
        members.append(dict(row=placement['row'], rule=command['rule'],
            formula_code=codes[canonical(command['formula'])],
            ordered_inputs=placement['ordered_inputs'], command_witness=witness,
            t=placement['t'], m=placement['m'], full_id=placement['id'],
            recipe_id=placement['recipe_id']))
    ports = [{k: copy.deepcopy(p[k]) for k in
        ('high_level_port', 'input_node', 'input_row', 'new_occupancy', 'adds_macro_offset_mark', 'readers')}
        for p in embedding['ordered_receptor_ports']]
    return dict(name=expansion['definition_name'], family=expansion['family'],
        premise_ast=expansion['ordered_local_premises'], conclusion_ast=expansion['conclusion'],
        premise_codes=[codes[canonical(f)] for f in expansion['ordered_local_premises']],
        conclusion_code=codes[canonical(expansion['conclusion'])], primitive_member_count=len(members),
        canonical_boundary_rows=embedding['local_boundary_rows'], canonical_context_id=embedding['context_id'],
        canonical_conclusion_row=embedding['conclusion_row'],
        canonical_input_rows=[s['row'] for s in embedding['ordered_input_seeds']],
        canonical_seed_ids=[s['id'] for s in embedding['ordered_input_seeds']],
        ordered_receptor_ports=ports, primitive_members=members,
        aggregate_t=embedding['cluster_aggregate']['t'], aggregate_m=embedding['cluster_aggregate']['m'],
        assumption_alias_occurrences=len(expansion['assumption_aliases']),
        source_body_sha256=expansion['source_body_sha256'], mapped_body_sha256=expansion['mapped_body_sha256'])


def receptor_ports(body, inventory):
    ids = {r['id']: r for r in inventory}
    result = []
    for index, (row, code) in enumerate(zip(body['canonical_input_rows'], body['premise_codes'])):
        integer(row); integer(code)
        readers = []
        for member in body['primitive_members']:
            recipe = ids[member['recipe_id']]
            for port, (source, expected) in enumerate(zip(member['ordered_inputs'], recipe['inputs'])):
                if source == row:
                    need(code == expected, 'receptor formula matches ordered primitive input')
                    readers.append(dict(reader_row=member['row'], primitive_input_port=port, formula_code=code))
        result.append(dict(high_level_port=index, input_row=row, formula_code=code, new_occupancy=0, readers=readers))
    return result


def family_bodies(certificate, schemas, projected, data, expansion_checker):
    """Rebuild all 171 literal source families without reading expansion output."""
    checker, records, source_receipts = expansion_checker.symbolic_source_gate(certificate, schemas)
    equal(checker.theory, next(m['context']['theory'] for m in data['models'] if m['height']==24),
          'literal source relation uses the exact recipient theory')
    codes = {canonical(f): i for i, f in enumerate(data['formula_codes'])}
    embedding_codes = {expansion_checker.base.canonical(f): i for i, f in enumerate(data['formula_codes'])}
    need(len(codes) == len(data['formula_codes']), 'injective formula registry')
    recipes = {expansion_checker.canonical(expansion_checker.recipe_key(
        r['primitive_witness'], r['ordered_premise_formulas'])): r for r in data['recipes']}
    need(len(recipes) == len(data['recipes']), 'recipe witness identity is injective')
    need(len(projected['definitions']) == len(records) == 171, 'full declaration inventory')
    equal(projected['formula_codes'], data['formula_codes'], 'projection registry')
    equal(projected['authority_epoch'], data['authority']['epoch'], 'projection authority')
    result, counts = [], dict(leaves=0, aliases=0, recursive_calls=0)
    for record, supplied in zip(certificate['records'], projected['definitions']):
        expansion = expansion_checker.literal_expansion(record, records)
        embedding = expansion_checker.canonical_embedding(expansion, checker, recipes, data['authority'],
            embedding_codes, digest(data['formula_codes']))
        rebuilt = projection(expansion, embedding, codes)
        equal(supplied, rebuilt, 'every full compact source-definition field')
        body = dict(kind='finite_source_body_structurally_certified_not_native_accepted', name=rebuilt['name'],
            canonical_input_rows=rebuilt['canonical_input_rows'], premise_codes=rebuilt['premise_codes'],
            primitive_members=[{k: m[k] for k in ('row', 'recipe_id', 'formula_code', 'ordered_inputs')}
                               for m in rebuilt['primitive_members']],
            source_body_sha256=rebuilt['source_body_sha256'], mapped_body_sha256=rebuilt['mapped_body_sha256'],
            dependency_bindings=[], native_accepted=False,
            earlier_expansion_closure='all recursive source dependencies in pinned full expansion and its independent audit',
            full_frozen_definition_sha256=digest(rebuilt))
        # Canonical local input seeds are aliases, not global recipient assumptions.
        counts['leaves'] += len(expansion['leaves'])
        counts['aliases'] += len(expansion['assumption_aliases'])
        counts['recursive_calls'] += len(expansion['recursive_calls'])
        result.append(body)
    need(counts == dict(leaves=1845, aliases=630, recursive_calls=216), 'complete source expansion census')
    return result, counts, source_receipts


def authored_body(name, keys, state):
    need(keys and len(set(keys)) == len(keys), 'distinct primitive member identities')
    need(all(a[1] < b[1] for a, b in zip(keys, keys[1:])), 'strict source member order')
    rows = {k[1] for k in keys}
    inputs = sorted({r for k in keys for r in k[2] if r not in rows})
    values, members, aggregate = {}, [], {}
    for k in keys:
        recipe = state.recipes[k[0]]
        _, marks = points(recipe, k[1], k[2], state.height)
        for x, y, value in marks:
            need((x, y) not in aggregate or aggregate[x, y] == value, 'fixed body point conflict')
            aggregate[x, y] = value
        for source, code in zip(k[2], recipe['inputs']):
            if source in inputs:
                need(source not in values or values[source] == code, 'fixed body receptor conflict')
                values[source] = code
        members.append(dict(row=k[1], recipe_id=recipe['id'], formula_code=recipe['output'], ordered_inputs=list(k[2])))
    body = dict(kind='authored_primitive_proposal_not_closed_lemma', name=name, canonical_input_rows=inputs,
        premise_codes=[values[r] for r in inputs], primitive_members=members, dependency_bindings=[], native_accepted=False)
    body['ordered_receptor_ports'] = receptor_ports(body, state.recipes)
    body['source_body_sha256'] = digest(body)
    body['mapped_body_sha256'] = body['source_body_sha256']
    return body


def descriptor(body, input_rows, member_rows, priority, binding, sources, epoch, state, context, authority, registry):
    """Transport the registered literal body; arbitrary valid members are insufficient."""
    integer(priority); need(priority >= 0, 'priority')
    need(len(input_rows) == len(body['canonical_input_rows']) and
         len(member_rows) == len(body['primitive_members']), 'complete body transport')
    for row in input_rows + member_rows:
        integer(row); need(0 <= row < state.height, 'finite row')
    need(all(a < b for a, b in zip(member_rows, member_rows[1:])), 'ordered distinct member rows')
    mapping = dict(zip(body['canonical_input_rows'], input_rows))
    mapping.update((m['row'], r) for m, r in zip(body['primitive_members'], member_rows))
    indices = {r['id']: i for i, r in enumerate(state.recipes)}
    keys = [(indices[m['recipe_id']], row, tuple(mapping[s] for s in m['ordered_inputs']))
            for m, row in zip(body['primitive_members'], member_rows)]
    need(len(set(keys)) == len(keys), 'no erased source occurrence')
    decorated, total, marks = [], {}, {}
    for k in keys:
        recipe = state.recipes[k[0]]
        need(recipe['output'] == body['primitive_members'][len(decorated)]['formula_code'], 'source palette formula')
        t, m = points(recipe, k[1], k[2], state.height)
        decorated.append(decorate(k, t, m, state.recipes, context, authority, registry))
        for x, y, value in t:
            p = (x, y); total[p] = total.get(p, 0) + value; need(total[p] <= 1, 'aggregate capacity')
        for x, y, value in m:
            p = (x, y); need(p not in marks or marks[p] == value, 'aggregate mark conflict'); marks[p] = value
    ports = []
    for port, row, code in zip(body['ordered_receptor_ports'], input_rows, body['premise_codes']):
        readers = [dict(reader_row=mapping[r['reader_row']], primitive_input_port=r['primitive_input_port'],
                        formula_code=code, offset_value=row-mapping[r['reader_row']]) for r in port['readers']]
        ports.append(dict(high_level_port=port['high_level_port'], input_row=row, formula_code=code, new_occupancy=0, readers=readers))
        need((1, row) not in marks or marks[1, row] == code, 'noninjective receptor conflict'); marks[1, row] = code
    result = dict(version=VERSION, relation=body['kind'], graph_binding=binding, source_bindings=sources,
        body_authority_epoch=epoch, body_name=body['name'], body_sha256=digest(body),
        source_body_sha256=body['source_body_sha256'], mapped_body_sha256=body['mapped_body_sha256'],
        dependency_bindings=body['dependency_bindings'], ordered_input_rows=input_rows, ordered_member_rows=member_rows,
        ordered_receptor_ports=ports, fixed_priority=priority, members=[key_data(k) for k in keys],
        full_member_ids=[p['id'] for p in decorated], full_identity_preimages=[p['identity_preimage'] for p in decorated],
        aggregate_t=[[*p, v] for p, v in sorted(total.items())], aggregate_m=[[*p, v] for p, v in sorted(marks.items())],
        native_accepted=False, native_authority_activated=False)
    result['descriptor_id'] = 'whole-cluster-' + digest(result)
    return result
