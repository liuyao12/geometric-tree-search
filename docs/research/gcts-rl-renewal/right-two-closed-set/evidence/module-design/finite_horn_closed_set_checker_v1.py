"""SOURCE ONLY finite-Horn closed-set checker and immutable view preparation.

No expected target answer or closure is bundled. Primitive/grammar validity is
an external whole-catalogue audit assumption. This checker establishes only a
closed formula-label set omitting the declared target in that exact finite graph.
The caller retains the original view and private authority after preparation;
only the deeply immutable view is passed to the untrusted closure producer.
"""
import hashlib
import json

VERSION = 'audited-finite-Horn-closed-set-checker-Source-v1'
VIEW = 'audited-finite-horn-view-v1'
BIT_ORDER = 'lsb0-formula-code'
BINDING_KEYS = ('declaration_sha256', 'model_epoch',
                'primitive_authority_epoch', 'formula_registry_sha256')
CANDIDATE_FIELDS = {'schema', 'binding', 'formula_count', 'recipe_count',
                    'target_code', 'bit_order', 'bits_hex', 'relation_sha256'}
MARKING_VERSION = 'injective-formula-ordered-primitive-offset-Q-v1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def text(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value, tick):
    """Whole canonical traversal, bounded accumulation; no full-model string."""
    h, buffered = hashlib.sha256(), 0
    encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'),
                              ensure_ascii=False, allow_nan=False)
    for piece in encoder.iterencode(value):
        raw = piece.encode('utf8')
        h.update(raw)
        buffered += len(raw)
        if buffered >= 65536:
            tick()
            buffered = 0
    tick()
    return h.hexdigest()


def binding_pairs(value):
    need(type(value) is dict and set(value) == set(BINDING_KEYS),
         'exact caller-authenticated four-field binding')
    for name in BINDING_KEYS:
        v = value[name]
        need(type(v) is str and len(v) == 64
             and all(c in '0123456789abcdef' for c in v), 'literal lower-case SHA256')
    return tuple((name, value[name]) for name in BINDING_KEYS)


def unique(pairs):
    result = {}
    for name, value in pairs:
        need(name not in result, 'duplicate declaration JSON key')
        result[name] = value
    return result


def no_number(value):
    raise ValueError('declaration has no float or nonfinite number')


def registry_digest(strings, tick):
    h = hashlib.sha256()
    h.update(b'[')
    for i, value in enumerate(strings):
        tick()
        need(type(value) is str, 'immutable canonical formula string')
        if i:
            h.update(b',')
        h.update(value.encode('utf8'))
    h.update(b']')
    tick()
    return h.hexdigest()


def relation_line(index, identifier, output, inputs):
    return (text([index, identifier, output, list(inputs)]) + '\n').encode('utf8')


def prepare_view(*, catalogue, declaration_raw, expected_binding, declared_target, tick):
    """Authenticate full Q data, then retain only immutable strings/ints/tuples.

    declaration_raw is the exact small original declaration buffer, not a Q
    preparation parse. The caller authenticates the complete preparation raw
    pin/EOF and the independent primitive/grammar admission before this call.
    No mutable catalogue, declaration, authority or input Source is exposed to
    the closure producer through the returned view.
    """
    tick()
    pairs = binding_pairs(expected_binding)
    need(type(declaration_raw) is bytes and 0 < len(declaration_raw) <= 1048576,
         'whole bounded immutable declaration bytes')
    h = hashlib.sha256()
    for start in range(0, len(declaration_raw), 65536):
        tick()
        h.update(declaration_raw[start:start+65536])
    need(h.hexdigest() == expected_binding['declaration_sha256'], 'original raw declaration pin')
    declaration = json.loads(declaration_raw.decode('utf8'), object_pairs_hook=unique,
                             parse_float=no_number, parse_constant=no_number)
    need(type(catalogue) is dict and type(declaration) is dict
         and text(catalogue['declaration']) == text(declaration)
         and text(declaration['target']) == text(declared_target),
         'same private declaration and exact declared target')
    formulas, records = catalogue['formula_codes'], catalogue['recipes']
    need(type(formulas) is list and formulas and type(records) is list,
         'whole original formula registry and every recipe array')
    strings = []
    codes = {}
    for code, formula in enumerate(formulas):
        tick()
        raw = text(formula)
        need(raw not in codes, 'injective complete formula registry')
        codes[raw] = code
        strings.append(raw)
    strings = tuple(strings)
    registry = registry_digest(strings, tick)
    need(registry == catalogue['formula_registry_sha256']
         == expected_binding['formula_registry_sha256'], 'complete original formula registry hash')
    target = codes.get(text(declared_target))
    need(type(target) is int, 'declared target belongs to complete registry')
    context = {'theory': declaration['theory'],
               'ordered_local_premises': declaration['ordered_Gamma']}
    need(text(catalogue['context']) == text(context), 'whole original occurrence-ordered Gamma')
    authority = catalogue['authority']
    need(authority.get('activated') is False and authority.get('native_accepted') is False
         and digest({k:v for k,v in authority.items() if k != 'epoch'}, tick) == authority['epoch']
         == expected_binding['primitive_authority_epoch']
         and authority['recipient_theory_sha256'] == digest(declaration['theory'], tick)
         and authority['declaration_sha256'] == digest(declaration, tick),
         'original authority/context/declaration value preimages')
    context_id = digest(context, tick)
    relation, identifiers, relation_hash = [], set(), hashlib.sha256()
    for index, record in enumerate(records):
        tick()
        w, premises = record['primitive_witness'], record['ordered_premise_formulas']
        need(type(w) is dict and type(premises) is list,
             'complete literal original witness and ordered premises')
        preimage = {'recipe': {'primitive_witness': w, 'ordered_premise_formulas': premises},
            'primitive_authority_epoch': authority['epoch'],
            'recipient_theory_sha256': authority['recipient_theory_sha256'],
            'marking_version': MARKING_VERSION, 'formula_registry_sha256': registry,
            'local_context_id': context_id}
        need(text(record['identity_preimage']) == text(preimage),
             'entire original recipe identity preimage')
        identifier = 'primitive-recipe-' + digest(preimage, tick)
        need(record['id'] == identifier and identifier not in identifiers,
             'unique original recipe ID, no omitted/duplicate substitution')
        identifiers.add(identifier)
        output = codes[text(w['formula'])]
        inputs = tuple(codes[text(f)] for f in premises)
        relation.append((identifier, output, inputs))
        relation_hash.update(relation_line(index, identifier, output, inputs))
    boundary, fixed = catalogue['boundary'], {}
    for x, y, value in boundary['fixed_marks']:
        tick()
        need(all(type(v) is int for v in (x,y,value))
             and ((x,y) not in fixed or fixed[(x,y)] == value), 'exact consistent original fixed marking')
        fixed[(x,y)] = value
    model = {'height': catalogue['height'], 'context': context, 'registry': registry,
        'authority': authority['epoch'], 'recipes': [r[0] for r in relation],
        'fixed_marks': [[*p,v] for p,v in sorted(fixed.items())],
        'roots': boundary['roots'], 'seed_keys': boundary['seed_keys'],
        'marking_version': MARKING_VERSION, 'fixture': False,
        'source_bindings': authority['source_bindings']}
    need(digest(model, tick) == expected_binding['model_epoch'], 'entire exact original model binding')
    # Every descendant is a builtin tuple/str/int; no mutable input is retained.
    view = (VIEW, pairs, digest(declaration, tick), strings, tuple(relation),
            target, relation_hash.hexdigest())
    tick()
    return view


def check_closed_set(*, view, expected_binding, declared_target, candidate, tick):
    """One complete relation scan; no saturation, search or expected answers.

    The caller passes its ORIGINAL prepare_view return, not any producer-returned
    model. This is ordinary reviewed-code isolation, not a hostile Python/OS VM.
    """
    tick()
    pairs = binding_pairs(expected_binding)
    need(type(view) is tuple and len(view) == 7 and view[0] == VIEW
         and view[1] == pairs and type(view[2]) is str
         and type(view[3]) is tuple and type(view[4]) is tuple,
         'original deeply immutable checker-owned view')
    strings, recipes, target, declared_relation = view[3:]
    need(type(target) is int and 0 <= target < len(strings)
         and strings[target] == text(declared_target)
         and registry_digest(strings, tick) == expected_binding['formula_registry_sha256'],
         'same private target and immutable registry')
    need(type(candidate) is dict and set(candidate) == CANDIDATE_FIELDS
         and candidate['schema'] == 'finite-horn-closed-set-candidate-v1'
         and binding_pairs(candidate['binding']) == pairs
         and candidate['bit_order'] == BIT_ORDER,
         'exact candidate schema and actual caller authority')
    n, m = len(strings), len(recipes)
    need(type(candidate['formula_count']) is int and candidate['formula_count'] == n
         and type(candidate['recipe_count']) is int and candidate['recipe_count'] == m
         and type(candidate['target_code']) is int and candidate['target_code'] == target,
         'complete counts/target, no Boolean indices or truncated arrays')
    wire = candidate['bits_hex']
    size = (n+7)//8
    need(type(wire) is str and len(wire) == 2*size
         and all(c in '0123456789abcdef' for c in wire),
         'canonical exact-length lower-case bitvector')
    bits = bytes.fromhex(wire)
    need(not n%8 or bits[-1] >> (n%8) == 0, 'zero high padding bits')
    need(not ((bits[target//8] >> (target%8)) & 1), 'declared target bit must be false')
    relation_hash, seen, zero_ports = hashlib.sha256(), set(), 0
    for index, row in enumerate(recipes):
        tick()
        need(type(row) is tuple and len(row) == 3, 'immutable complete Horn recipe row')
        identifier, output, inputs = row
        need(type(identifier) is str and identifier not in seen
             and type(output) is int and 0 <= output < n and type(inputs) is tuple
             and all(type(code) is int and 0 <= code < n for code in inputs),
             'every ordered premise occurrence and original output code')
        seen.add(identifier)
        relation_hash.update(relation_line(index, identifier, output, inputs))
        antecedent = True
        for code in inputs:
            tick()
            antecedent = antecedent and bool((bits[code//8] >> (code%8)) & 1)
        if not inputs:
            zero_ports += 1
        need(not antecedent or bool((bits[output//8] >> (output%8)) & 1),
             'Horn closure violation at original recipe ' + str(index))
    actual_relation = relation_hash.hexdigest()
    need(actual_relation == declared_relation == candidate['relation_sha256'],
         'complete original ordered relation hash and EOF, no partial-prefix acceptance')
    members = 0
    for value in bits:
        tick()
        members += bin(value).count('1')
    receipt = {'schema':'finite-horn-closed-set-check-result-v1','version':VERSION,
        'binding':dict(pairs),'formula_count':n,'recipe_count':m,'target_code':target,
        'set_member_count':members,'zero_port_records_checked':zero_ports,
        'closure_relations_checked':m,'relation_sha256':actual_relation,
        'candidate_sha256':digest(candidate,tick),'whole_supplied_recipe_array_checked':True,
        'closed_set_verified':True,'target_excluded':True,'finite_horn_unreachable':True,
        'scope':'Exact audited finite Horn recipe graph at any word length only; not arithmetic nonprovability, bounded search exhaustion or point trajectory.',
        'original_target_proved':False,'arithmetic_nonprovability_accepted':False,
        'point_state_accepted':False,'trajectory_accepted':False,'full24_accepted':False,
        'native_accepted':False,'ROOT_resource_accepted':False,'RL_accepted':False}
    text(receipt)
    tick()
    return receipt
