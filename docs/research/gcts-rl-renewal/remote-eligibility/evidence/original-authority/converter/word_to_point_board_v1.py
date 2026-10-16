"""Untrusted translation-only point-board proposal from a primitive proof word.

No logical acceptance or search is performed here. A fresh independent word
checker and an independently authored exact point checker must validate output.
The implicit inventory is supplied by the bounded-language policy, not enumerated
by this converter. This is not a GCTS trajectory or an adjacency-only Wang palette.
"""
import copy
import hashlib
import json

VERSION = 'untrusted-bounded-word-to-translated-point-board-v1'
ZERO_RULES = frozenset(('axiom', 'assumption', 'instantiate', 'eq_subst'))
FIELDS = {'axiom': {'name'}, 'assumption': {'index'},
          'instantiate': {'universal', 'term'},
          'eq_subst': {'variable', 'template', 'left', 'right'},
          'mp': {'antecedent', 'implication'},
          'generalize': {'variable', 'source'}}


def need(condition, label):
    if not condition:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def references(command):
    rule = command.get('rule')
    need(rule in FIELDS and set(command) == {'rule', 'formula'} | FIELDS[rule],
         'exact primitive command fields')
    return ([command['antecedent'], command['implication']] if rule == 'mp'
            else [command['source']] if rule == 'generalize' else [])


def propose_point_board(*, commands, height, input_epoch, tick):
    """Copy and expand only; caller supplies authenticated private authority.

    Every filler copies the original first zero-input primitive. The original
    word is shifted intact, preserving all strict-prior references. A reviewer
    must check the shifted word's language membership and logical acceptance.
    """
    tick()
    need(type(height) is int and 1 <= height <= 24, 'finite declared height')
    need(type(input_epoch) is str and len(input_epoch) == 64
         and all(c in '0123456789abcdef' for c in input_epoch), 'literal input epoch')
    need(type(commands) is list and 0 < len(commands) <= height,
         'whole nonempty source word fits target')
    source = copy.deepcopy(commands)
    for row, command in enumerate(source):
        tick()
        for index in references(command):
            need(type(index) is int and 0 <= index < row, 'strict-prior original port')
    need(source[0]['rule'] in ZERO_RULES, 'first primitive has no premise ports')
    padding = height - len(source)
    shifted = [copy.deepcopy(source[0]) for _ in range(padding)]
    for command in source:
        new = copy.deepcopy(command)
        if new['rule'] == 'mp':
            new['antecedent'] += padding
            new['implication'] += padding
        elif new['rule'] == 'generalize':
            new['source'] += padding
        shifted.append(new)
    tiles = []
    for row, command in enumerate(shifted):
        tick()
        refs = references(command)
        need(all(type(ref) is int and 0 <= ref < row for ref in refs),
             'strict-prior shifted ports')
        witness = copy.deepcopy(command)
        for name in ('antecedent', 'implication', 'source'):
            witness.pop(name, None)
        premises = [copy.deepcopy(shifted[ref]['formula']) for ref in refs]
        offsets = [ref - row for ref in refs]
        preimage = {'input_epoch': input_epoch, 'primitive_witness': witness,
                    'ordered_premise_formulas': premises, 'ordered_offsets': offsets}
        local_marks = [[[1, 0], ['formula', canonical(command['formula'])]]]
        for port, (offset, premise) in enumerate(zip(offsets, premises)):
            local_marks.extend([[[1, offset], ['formula', canonical(premise)]],
                                [[2 + port, 0], ['offset', offset]]])
        global_marks = [[[point[0], point[1] + row], copy.deepcopy(value)]
                        for point, value in local_marks]
        tiles.append({'tile_type_id': 'bounded-point-tile-' + digest(preimage),
                      'type_preimage': preimage, 'translation': [0, row],
                      'local_t_values': [[[0, 0], 1]], 'local_m_values': local_marks,
                      'global_t_values': [[[0, row], 1]], 'global_m_values': global_marks})
    target = copy.deepcopy(source[-1]['formula'])
    fixed = [[[1, row], ['outside', input_epoch]] for row in range(1 - height, 0)]
    fixed.append([[1, height - 1], ['formula', canonical(target)]])
    result = {'schema': VERSION, 'input_epoch': input_epoch, 'height': height,
              'source_word_sha256': digest(source), 'source_word_length': len(source),
              'padding_rows': padding, 'padded_commands': shifted,
              'padded_commands_sha256': digest(shifted),
              'required_points': [[0, row] for row in range(height)],
              'fixed_markings': fixed, 'tiles': tiles,
              'transformations': 'integer translations only; marking values unchanged',
              'inventory': 'all bounded-language primitives with ordered strict-prior offsets',
              'logical_proof_accepted': False, 'exact_point_board_accepted': False,
              'complete_candidate_graph_accepted': False, 'trajectory_accepted': False,
              'GCTS_advantage_accepted': False, 'RL_accepted': False,
              'native_Wang_palette_accepted': False, 'ROOT_resource_accepted': False}
    canonical(result)
    tick()
    return result
