"""Independent pure finite family-interface/binding/embedding reconstruction.

Synthetic invocation only under a separately ROOT-owned fixture gate. No graph,
producer, controller, registry factory, logical checker or model imports. Checked
source bodies and actual selected root anchors remain prerequisites in a later
production adapter; this module cannot certify those prerequisites itself.
"""
import copy
import itertools

from family_binding_oracle_v1 import canonical, digest, integer, project_binding, require


def declared_interface(body, projection):
    """Bind an explicit conclusion through the entire frozen projection digest.

Do not infer the conclusion from a body name, target formula or last-member
convention. The registered member need not be last in this pure interface gate.
"""
    require(type(body) is dict and type(projection) is dict, 'literal interface records')
    require(body.get('full_frozen_definition_sha256') == digest(projection), 'complete declared projection binding')
    for field in ('name', 'canonical_input_rows', 'premise_codes', 'source_body_sha256', 'mapped_body_sha256'):
        require(body.get(field) == projection.get(field), 'projection/body field: ' + field)
    projected = projection.get('primitive_members')
    require(type(projected) is list and bool(projected), 'complete projection primitive members')
    reduced = [{k: copy.deepcopy(m[k]) for k in ('row', 'recipe_id', 'formula_code', 'ordered_inputs')} for m in projected]
    require(canonical(reduced) == canonical(body['primitive_members']), 'exact projection/body member transport')
    row = integer(projection['canonical_conclusion_row'])
    code = integer(projection['conclusion_code'])
    require(row >= 0 and code >= 0, 'nonnegative declared conclusion')
    matches = [i for i, member in enumerate(body['primitive_members']) if member['row'] == row]
    require(len(matches) == 1, 'declared conclusion is one actual source member')
    index = matches[0]
    require(integer(body['primitive_members'][index]['formula_code']) == code, 'declared member output code')
    return dict(body=copy.deepcopy(body), projection_sha256=digest(projection),
                conclusion_member_index=index, canonical_conclusion_row=row, conclusion_code=code)


def transported_interface(interface, input_rows, member_rows, inventory, height):
    result = project_binding(interface['body'], input_rows, member_rows, inventory, height)
    index = integer(interface['conclusion_member_index'])
    require(0 <= index < len(result['members']), 'declared transported member index')
    require(interface['body']['primitive_members'][index]['row'] == interface['canonical_conclusion_row'], 'exact conclusion source row')
    require(interface['body']['primitive_members'][index]['formula_code'] == interface['conclusion_code'], 'exact conclusion source code')
    result['conclusion_row'] = result['members'][index][1]
    result['conclusion_formula_code'] = interface['conclusion_code']
    result['declared_conclusion_member_index'] = index
    result['projection_sha256'] = interface['projection_sha256']
    return result


def root_anchors(anchors, inventory, height):
    """Check a supplied selected-root projection, not proof or generation authority.

Future actual use must independently derive these entries from the point state.
Empty rows/assigned marks do not appear in this API. The synthetic caller cannot
bootstrap a production selected root merely by constructing one of these records.
"""
    integer(height); require(height > 0, 'positive boundary')
    require(type(anchors) is list, 'ordered selected-root projection')
    seen_rows, seen_keys, values = set(), set(), []
    for anchor in anchors:
        require(type(anchor) is dict and anchor.get('selected') is True, 'explicit selected root only')
        data = anchor['key']
        require(type(data) is list and len(data) == 3 and type(data[2]) is list, 'exact selected root key')
        recipe, row = integer(data[0]), integer(data[1])
        refs = tuple(integer(v) for v in data[2])
        require(0 <= recipe < len(inventory) and 0 <= row < height, 'root key in finite palette/boundary')
        require(all(0 <= r < row for r in refs) and len(refs) == len(inventory[recipe]['inputs']), 'root exact ordered strict-prior ports')
        require(integer(anchor['formula_code']) == integer(inventory[recipe]['output']), 'selected root formula identity')
        require(integer(anchor['generation']) == 0, 'declared actual initial root generation')
        key = (recipe, row, refs)
        require(row not in seen_rows and key not in seen_keys, 'distinct selected unit placements')
        seen_rows.add(row); seen_keys.add(key)
        values.append(dict(key=[recipe, row, list(refs)], formula_code=anchor['formula_code'], generation=0, selected=True))
    values.sort(key=lambda r: (r['key'][0], r['key'][1], tuple(r['key'][2])))
    return values


def canonical_embedding(interface, input_rows, inventory, height, assigned_keys):
    """One declared increasing proof-DAG embedding; not rigid translation.

Try the earliest full recipe/ordered-reference identity already assigned, only
strictly beyond this component's previous member and every input reference.
Otherwise allocate the earliest unused row beyond both. Retain every occurrence.
assigned_keys may contain selected roots or included earlier component outputs;
the caller must independently justify which it is. It never adds premise seeds.
"""
    integer(height); require(height > 0, 'positive finite boundary')
    body = interface['body']
    require(type(input_rows) is list and len(input_rows) == len(body['canonical_input_rows']), 'ordered complete binding')
    for row in input_rows:
        integer(row); require(0 <= row < height, 'receptor row in boundary')
    recipes = {r['id']: i for i, r in enumerate(inventory)}
    require(len(recipes) == len(inventory), 'distinct inventory recipe identities')
    allocated, available = {}, []
    for data in assigned_keys:
        require(type(data) is list and len(data) == 3 and type(data[2]) is list, 'literal assigned key')
        key = (integer(data[0]), integer(data[1]), tuple(integer(v) for v in data[2]))
        require(0 <= key[0] < len(inventory) and 0 <= key[1] < height, 'assigned key in palette/boundary')
        require(len(key[2]) == len(inventory[key[0]]['inputs']) and all(0 <= r < key[1] for r in key[2]), 'assigned exact ordered references')
        require(key[1] not in allocated or allocated[key[1]] == key, 'assigned distinct unit occupancy conflict')
        if key[1] not in allocated:
            allocated[key[1]] = key; available.append(key)
    mapping = dict(zip(body['canonical_input_rows'], input_rows))
    previous = -1
    member_rows = []
    for member in body['primitive_members']:
        require(member['recipe_id'] in recipes, 'literal source recipe')
        recipe = recipes[member['recipe_id']]
        refs = tuple(mapping[ref] for ref in member['ordered_inputs'])
        threshold = max((previous,) + refs)
        reusable = [k for k in available if k[0] == recipe and k[2] == refs and k[1] > threshold]
        if reusable:
            key = min(reusable, key=lambda k: k[1])
            row = key[1]
        else:
            unused = next((r for r in range(threshold + 1, height) if r not in allocated), None)
            require(unused is not None, 'canonical row exhaustion')
            row = unused
            key = (recipe, row, refs)
            allocated[row] = key; available.append(key)
        mapping[integer(member['row'])] = row
        member_rows.append(row); previous = row
    result = transported_interface(interface, input_rows, member_rows, inventory, height)
    result['embedding_scope'] = 'one canonical increasing proof-DAG transport; not rigid macro translation'
    return result


def enumerate_binding_grammar(interfaces, anchors, inventory, height):
    """Enumerate all declared single/pair type and formula-filtered bindings.

This function is pure and deliberately unbounded by a silently truncated pool.
A future owned caller must abort preparation as UNKNOWN if it cannot finish the
complete declared finite grammar. Such an abort must never restrict primitives.
It returns every visited binding, including rejected canonical embeddings. It
does not compile a controller descriptor or test current point-state legality.
"""
    roots = root_anchors(anchors, inventory, height)
    names = [i['body']['name'] for i in interfaces]
    require(len(set(names)) == len(names), 'distinct source interface identities')
    records, single_types, pair_types = [], [], []
    assigned = [r['key'] for r in roots]

    def root_options(code):
        return [dict(kind='root_anchor', index=i, row=r['key'][1]) for i, r in enumerate(roots) if r['formula_code'] == code]

    def emit(kind, indices, first_inputs, second_inputs=None):
        record = dict(kind=kind, interface_indices=list(indices), first_inputs=copy.deepcopy(first_inputs),
                      second_inputs=copy.deepcopy(second_inputs), embedding_accepted=False, rejection=None, components=[])
        try:
            first = canonical_embedding(interfaces[indices[0]], [b['row'] for b in first_inputs], inventory, height, assigned)
            record['components'].append(first)
            if second_inputs is not None:
                rows = [first['conclusion_row'] if b['kind'] == 'earlier_component_output' else b['row'] for b in second_inputs]
                second = canonical_embedding(interfaces[indices[1]], rows, inventory, height, assigned + first['members'])
                record['components'].append(second)
            record['embedding_accepted'] = True
        except (ValueError, KeyError) as exc:
            record['rejection'] = str(exc)
        records.append(record)

    for i, interface in enumerate(interfaces):
        single_types.append(i)
        choices = [root_options(code) for code in interface['body']['premise_codes']]
        for binding in itertools.product(*choices):
            emit('single', (i,), list(binding))
    for i, first in enumerate(interfaces):
        first_options = [root_options(code) for code in first['body']['premise_codes']]
        for j, second in enumerate(interfaces):
            pair_types.append([i, j])
            second_options = []
            for code in second['body']['premise_codes']:
                choices = root_options(code)
                if code == first['conclusion_code']:
                    choices = choices + [dict(kind='earlier_component_output', index=0)]
                second_options.append(choices)
            for first_binding in itertools.product(*first_options):
                for second_binding in itertools.product(*second_options):
                    if not any(b['kind'] == 'earlier_component_output' for b in second_binding):
                        continue
                    emit('pair', (i, j), list(first_binding), list(second_binding))
    return dict(ordered_single_types=single_types, ordered_pair_types=pair_types, bindings=records,
                root_anchors=roots, proof_accepted=False, native_accepted=False,
                scope='complete declared synthetic type/binding grammar; one increasing embedding per binding; embedding_accepted does not establish compatible joint aggregate, point-state legality or logical proof acceptance')
