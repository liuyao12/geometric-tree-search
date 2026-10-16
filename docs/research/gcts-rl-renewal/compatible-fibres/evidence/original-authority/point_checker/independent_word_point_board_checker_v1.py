"""SOURCE ONLY independent exact point-board reconstruction and union check.

The caller supplies its private ORIGINAL word/height/epoch, not packet authority.
No converter, point engine or logical checker is imported/called. Whole padded
primitive membership and original-Gamma/target word checking remain external.
"""
import hashlib
import json

VERSION = 'independent-bounded-word-point-board-check-v1'
PROPOSAL = 'untrusted-bounded-word-to-translated-point-board-v1'
PORTS = {'axiom': (), 'assumption': (), 'instantiate': (), 'eq_subst': (),
         'mp': ('antecedent', 'implication'), 'generalize': ('source',)}
DETAILS = {'axiom': ('name',), 'assumption': ('index',),
           'instantiate': ('universal', 'term'),
           'eq_subst': ('variable', 'template', 'left', 'right'),
           'mp': ('antecedent', 'implication'),
           'generalize': ('variable', 'source')}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def private_copy(value, tick):
    """Separate builtin JSON tree, without pickle/JSON roundtrip or coercion."""
    tick()
    kind = type(value)
    if kind in (str, int, bool) or value is None:
        return value
    if kind is list:
        return [private_copy(item, tick) for item in value]
    require(kind is dict and all(type(k) is str for k in value),
            'only exact builtin JSON trees, no float/custom object')
    return {k: private_copy(v, tick) for k, v in value.items()}


def exact(actual, expected, tick):
    """Recursive type identity precedes equality: bool never equals int."""
    tick()
    require(type(actual) is type(expected), 'exact packet value type')
    if type(expected) is dict:
        require(set(actual) == set(expected) and all(type(k) is str for k in actual),
                'exact packet dictionary fields')
        for name in expected:
            exact(actual[name], expected[name], tick)
    elif type(expected) is list:
        require(len(actual) == len(expected), 'exact packet ordered array length')
        for a, e in zip(actual, expected):
            exact(a, e, tick)
    else:
        require(type(expected) in (str, int, bool) or expected is None,
                'expected builtin scalar')
        require(actual == expected, 'exact packet scalar value')


def command_ports(command, row):
    require(type(command) is dict and type(command.get('rule')) is str
            and command['rule'] in PORTS, 'exact declared primitive rule')
    rule = command['rule']
    require(set(command) == {'rule', 'formula'} | set(DETAILS[rule])
            and all(type(k) is str for k in command), 'exact primitive fields')
    refs = [command[name] for name in PORTS[rule]]
    require(all(type(i) is int and 0 <= i < row for i in refs),
            'strict-prior original ordered integer ports')
    return refs


def check_point_board(*, commands, height, input_epoch, packet, tick):
    """Rebuild from private inputs; compare all data; then check full t/m union.

    A successful receipt establishes the exact positive point-board projection
    only. It does not validate any primitive rule, bounded-language membership,
    mathematical theorem, complete domain, search scheduling or trajectory.
    """
    tick()
    require(type(height) is int and 1 <= height <= 24, 'private finite height')
    require(type(input_epoch) is str and len(input_epoch) == 64
            and all(c in '0123456789abcdef' for c in input_epoch),
            'private exact input epoch')
    require(type(commands) is list and 0 < len(commands) <= height,
            'private original word fits declared height')
    original = private_copy(commands, tick)
    for index, command in enumerate(original):
        tick()
        command_ports(command, index)
    require(not PORTS[original[0]['rule']], 'first original primitive has zero ports')
    filler_count = height - len(original)
    padded = []
    # Construct each absolute row directly, independently of converter loops.
    for row in range(height):
        tick()
        is_filler = row < filler_count
        command = private_copy(original[0 if is_filler else row-filler_count], tick)
        if not is_filler:
            for field in PORTS[command['rule']]:
                command[field] = command[field] + filler_count
        command_ports(command, row)
        padded.append(command)
    tiles = []
    for row in range(height):
        tick()
        command = padded[row]
        fields = PORTS[command['rule']]
        refs = [command[field] for field in fields]
        witness = {k: private_copy(v, tick) for k, v in command.items() if k not in fields}
        inputs = [private_copy(padded[ref]['formula'], tick) for ref in refs]
        delta = [ref-row for ref in refs]
        preimage = {'input_epoch':input_epoch, 'primitive_witness':witness,
                    'ordered_premise_formulas':inputs, 'ordered_offsets':delta}
        local = [[[1, 0], ['formula', canonical(command['formula'])]]]
        translated = [[[1, row], ['formula', canonical(command['formula'])]]]
        for port in range(len(refs)):
            tick()
            value = ['formula', canonical(inputs[port])]
            local.append([[1, delta[port]], private_copy(value, tick)])
            local.append([[2+port, 0], ['offset', delta[port]]])
            translated.append([[1, refs[port]], private_copy(value, tick)])
            translated.append([[2+port, row], ['offset', delta[port]]])
        tiles.append({'tile_type_id':'bounded-point-tile-'+sha(preimage),
                      'type_preimage':preimage, 'translation':[0,row],
                      'local_t_values':[[[0,0],1]], 'local_m_values':local,
                      'global_t_values':[[[0,row],1]], 'global_m_values':translated})
    fixed = [[[1,y], ['outside',input_epoch]] for y in range(1-height,0)]
    fixed.append([[1,height-1], ['formula',canonical(original[-1]['formula'])]])
    expected = {'schema':PROPOSAL, 'input_epoch':input_epoch, 'height':height,
        'source_word_sha256':sha(original), 'source_word_length':len(original),
        'padding_rows':filler_count, 'padded_commands':padded,
        'padded_commands_sha256':sha(padded),
        'required_points':[[0,row] for row in range(height)],
        'fixed_markings':fixed, 'tiles':tiles,
        'transformations':'integer translations only; marking values unchanged',
        'inventory':'all bounded-language primitives with ordered strict-prior offsets',
        'logical_proof_accepted':False, 'exact_point_board_accepted':False,
        'complete_candidate_graph_accepted':False, 'trajectory_accepted':False,
        'GCTS_advantage_accepted':False, 'RL_accepted':False,
        'native_Wang_palette_accepted':False, 'ROOT_resource_accepted':False}
    exact(packet, expected, tick)
    totals = {(0,row):0 for row in range(height)}
    values, multiplicity, placements, prototypes = {}, {}, set(), {}
    occurrences = 0
    # Re-accumulate ACTUAL compared packet data; duplicates must agree literally.
    all_mark_sources = [packet['fixed_markings']]
    for tile in packet['tiles']:
        tick()
        type_id = tile['tile_type_id']
        if type_id in prototypes:
            exact(tile['type_preimage'], prototypes[type_id], tick)
        else:
            prototypes[type_id] = private_copy(tile['type_preimage'], tick)
        identity = (tile['tile_type_id'], tuple(tile['translation']))
        require(identity not in placements, 'selected placement identity repeated')
        placements.add(identity)
        for point, value in tile['global_t_values']:
            tick()
            coordinate = tuple(point)
            require(coordinate in totals and type(value) is int and value > 0,
                    'positive support inside complete required target')
            totals[coordinate] += value
            require(totals[coordinate] <= 1, 'unit target overfill')
        all_mark_sources.append(tile['global_m_values'])
    for marks in all_mark_sources:
        for point, value in marks:
            tick()
            coordinate = tuple(point)
            if coordinate in values:
                exact(value, values[coordinate], tick)
            else:
                values[coordinate] = private_copy(value, tick)
            multiplicity[coordinate] = multiplicity.get(coordinate, 0) + 1
            occurrences += 1
    require(all(total == 1 for total in totals.values()), 'whole target exactly filled')
    require(len(placements) == height, 'one distinct placement per absolute row')
    receipt = {'schema':VERSION, 'input_epoch':input_epoch, 'height':height,
        'source_word_sha256':sha(original), 'source_word_length':len(original),
        'padding_rows':filler_count, 'padded_commands_sha256':sha(padded),
        'packet_sha256':sha(packet), 'tile_count':len(packet['tiles']),
        'placement_identity_count':len(placements),
        'prototype_identity_count':len(prototypes),
        'required_point_count':len(totals), 'fixed_mark_occurrences':len(fixed),
        'marking_point_count':len(values), 'marking_occurrence_count':occurrences,
        'unit_totals':[[list(p),totals[p]] for p in sorted(totals)],
        'marking_union':[[list(p),values[p],multiplicity[p]] for p in sorted(values)],
        'checked_padded_commands':padded,
        'exact_point_board_accepted':True, 'whole_unit_target_verified':True,
        'literal_marking_union_verified':True,
        'logical_proof_accepted':False, 'bounded_primitive_membership_accepted':False,
        'complete_candidate_graph_accepted':False, 'trajectory_accepted':False,
        'GCTS_advantage_accepted':False, 'RL_accepted':False,
        'native_Wang_palette_accepted':False, 'ROOT_resource_accepted':False,
        'scope':'Exact translated point-board projection of private original word only; logical/bounded primitive checks and resources remain external.'}
    canonical(receipt)
    tick()
    return receipt
