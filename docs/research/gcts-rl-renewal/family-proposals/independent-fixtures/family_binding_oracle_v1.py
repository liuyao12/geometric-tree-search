"""Source-only independent finite family binding/composition projection.

No producer/controller/graph/model/logic imports, calls or activation. These
functions require separately checked literal source bodies and recipe inventory.
They do not infer a lemma, add premises or authorize a placement. Full logical
and dynamic state/rollback checks remain independent later gates.
"""
import copy
import hashlib
import json


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def integer(value):
    require(type(value) is int, 'exact integer; bool is not a row/code/priority')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def key_data(key):
    return [key[0], key[1], list(key[2])]


def project_binding(body, input_rows, member_rows, inventory, height):
    """Reconstruct exact registered-body transport, not arbitrary legal members.

    All member recipe IDs and canonical ordered reference occurrences come from
    the checked registry. Receptor aliases may coincide only with equal codes.
    Mapping to an internal earlier output is permitted if every literal read
    remains strict-prior; that is a composition dependency, not a new hypothesis.
    """
    integer(height); require(height > 0, 'positive finite boundary')
    require(type(body) is dict and body.get('native_accepted') is False, 'inactive exact body authority')
    require(type(body.get('name')) is str and bool(body['name']), 'literal named body')
    require(type(input_rows) is list and type(member_rows) is list, 'ordered literal row bindings')
    originals, codes, members = body['canonical_input_rows'], body['premise_codes'], body['primitive_members']
    require(len(originals) == len(codes) == len(input_rows) and len(members) == len(member_rows), 'complete ordered binding')
    require(len(set(originals)) == len(originals), 'distinct canonical premise occurrence aliases')
    for value in originals + codes + input_rows + member_rows:
        integer(value)
    require(all(v >= 0 for v in originals + codes), 'nonnegative source rows/formula codes')
    require(all(0 <= row < height for row in input_rows + member_rows), 'recipient finite rows')
    require(bool(members) and all(a < b for a, b in zip(member_rows, member_rows[1:])), 'nonempty strictly ordered member embedding')
    recipes = {}
    for index, recipe in enumerate(inventory):
        require(recipe['id'] not in recipes, 'distinct checked recipe identities')
        recipes[recipe['id']] = (index, recipe)
    source_formulas = dict(zip(originals, codes))
    mapping = dict(zip(originals, input_rows))
    recipient_values = {}
    for row, code in zip(input_rows, codes):
        require(row not in recipient_values or recipient_values[row] == code, 'noninjective receptor formula conflict')
        recipient_values[row] = code
    previous = -1
    for member, row in zip(members, member_rows):
        src = integer(member['row'])
        require(src > previous and src not in source_formulas, 'strict distinct source member order')
        previous = src
        require(member['recipe_id'] in recipes, 'member belongs to original checked primitive palette')
        _, recipe = recipes[member['recipe_id']]
        require(integer(member['formula_code']) == recipe['output'], 'registered source output equals recipe')
        refs = member['ordered_inputs']
        require(type(refs) is list and len(refs) == len(recipe['inputs']), 'full ordered primitive port multiplicity')
        for ref, code in zip(refs, recipe['inputs']):
            integer(ref); integer(code)
            require(0 <= ref < src and source_formulas.get(ref) == code, 'source body exact strict-prior formula dependency')
        source_formulas[src] = recipe['output']
        mapping[src] = row
    keys, ports = [], []
    for member, row in zip(members, member_rows):
        index, recipe = recipes[member['recipe_id']]
        refs = tuple(mapping[ref] for ref in member['ordered_inputs'])
        require(all(0 <= ref < row for ref in refs), 'recipient strict-prior reads, no cycles/forward dependencies')
        require(row not in recipient_values or recipient_values[row] == recipe['output'], 'receptor/internal output collision')
        recipient_values[row] = recipe['output']
        keys.append((index, row, refs))
    require(len(set(keys)) == len(keys), 'within-body occurrence erasure forbidden')
    for high_port, (source, row, code) in enumerate(zip(originals, input_rows, codes)):
        readers = []
        for member, reader_row in zip(members, member_rows):
            _, recipe = recipes[member['recipe_id']]
            for primitive_port, (ref, expected) in enumerate(zip(member['ordered_inputs'], recipe['inputs'])):
                if ref == source:
                    require(expected == code, 'ordered receptor reader formula')
                    readers.append(dict(reader_row=reader_row, primitive_input_port=primitive_port,
                                        formula_code=code, offset_value=row-reader_row))
        ports.append(dict(high_level_port=high_port, input_row=row, formula_code=code,
                          new_occupancy=0, readers=readers))
    return dict(body_name=body['name'], body_sha256=digest(body),
                ordered_input_rows=list(input_rows), ordered_member_rows=list(member_rows),
                members=[key_data(key) for key in keys], ordered_receptor_ports=ports,
                conclusion_formula_code=members[-1]['formula_code'], conclusion_row=member_rows[-1],
                receptor_only_assignments=[[1, row, code] for row, code in sorted(dict(zip(input_rows, codes)).items())],
                proof_accepted=False, native_accepted=False)


def composed_union(projections, reconstruct_identity, already_selected=()):
    """Exact primitive sharing with occurrence provenance; unit-row adaptation.

    reconstruct_identity must be the separately pinned independent literal point
    library bound to one unchanged recipient model/context/authority/registry.
    This function never obtains identity/t/m from a supplied descriptor alone.
    already_selected is an independently reconstructed set of full primitive
    keys; selected sharing has zero *additional* occupancy, not zero aggregate t.
    """
    require(type(projections) is list and bool(projections), 'finite nonempty composition')
    selected = set(already_selected)
    unique, aliases, marks, receptor_marks = {}, [], {}, {}
    for occurrence, projected in enumerate(projections):
        for triple in projected['receptor_only_assignments']:
            x, y, code = triple
            integer(x); integer(y); integer(code)
            point = (x, y)
            require(point not in receptor_marks or receptor_marks[point] == code, 'composed receptor formula conflict')
            receptor_marks[point] = code
        for member_occurrence, data in enumerate(projected['members']):
            require(type(data) is list and len(data) == 3 and type(data[2]) is list, 'complete member key')
            key = (integer(data[0]), integer(data[1]), tuple(integer(v) for v in data[2]))
            record = reconstruct_identity(key)
            require(record['key'] == key_data(key), 'independent identity preserves exact member key')
            require(record['id'] == 'aggregate-primitive-' + digest(record['identity_preimage']), 'full identity hash')
            require(record['identity_preimage']['t'] == record['t'] and record['identity_preimage']['m'] == record['m'], 'full identity support binding')
            require(record['identity_preimage']['primitive_command'] == record['command'], 'full identity logical command binding')
            if key in unique:
                require(canonical(unique[key]) == canonical(record), 'shared key needs exact full decorated identity')
            else:
                require(all(v['id'] != record['id'] for v in unique.values()), 'different keys may not share an identity')
                unique[key] = copy.deepcopy(record)
            aliases.append(dict(component_occurrence=occurrence, body_name=projected['body_name'],
                                member_occurrence=member_occurrence, key=key_data(key),
                                full_identity=record['id']))
    total, additional = {}, {}
    for key, record in unique.items():
        for x, y, value in record['t']:
            integer(x); integer(y); integer(value)
            require(value == 1, 'declared current unit primitive support only; no generic fractional claim')
            point = (x, y); total[point] = total.get(point, 0) + value
            require(total[point] <= 1, 'distinct placements overfill composed physical aggregate')
            if key not in selected:
                additional[point] = additional.get(point, 0) + value
        for x, y, value in record['m']:
            integer(x); integer(y); integer(value)
            point = (x, y)
            require(point not in marks or marks[point] == value, 'composed primitive remote mark conflict')
            marks[point] = value
    for point, code in receptor_marks.items():
        require(point not in marks or marks[point] == code, 'receptor/body aggregate marking conflict')
        marks[point] = code
    return dict(distinct_members=[key_data(k) for k in unique],
                full_identities=[r['id'] for r in unique.values()], occurrence_provenance=aliases,
                aggregate_t=[[*p, v] for p, v in sorted(total.items())],
                additional_t=[[*p, v] for p, v in sorted(additional.items())],
                aggregate_m=[[*p, v] for p, v in sorted(marks.items())],
                proof_accepted=False, native_accepted=False,
                scope='Checked source transports and exact compatible unit-row aggregate only; no state legality, scheduler, hypothesis closure or mathematical proof acceptance.')
