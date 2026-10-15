"""UNEXECUTED Source: full current-Q / current-Hilbert recipe data adapters.

No project imports or grammar regeneration. A future trusted caller injects the
exact authenticated preparation/SelectedWire plus original graph source map.
Normalization preserves recipe order, every preimage, formula code and epoch.
"""
import copy
import hashlib
import json

VERSION = 'current-keyed-equality-catalogue-adapters-Source-v1'
Q_MARKING = 'injective-formula-ordered-primitive-offset-Q-v1'
H_MARKING = 'injective-formula-ordered-mp-offset-v1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def integer(value, low=0, high=None):
    need(type(value) is int and value >= low and (high is None or value < high),
         'literal bounded integer, never Boolean')
    return value


def build_catalogue(*, profile, logical_context, original_context, authority,
                    formulas, records, fixed_marks, roots, seed_keys, height,
                    source_bindings, binding, marking, tick):
    """Reproduce the ORIGINAL model-epoch preimage, never an advice epoch."""
    tick()
    integer(height, 1)
    need(type(formulas) is list and type(records) is list and records,
         'whole original formula and primitive inventories')
    need(type(roots) is list and len(roots) == height
         and all(type(x) is int and x >= 0 for x in roots), 'complete original roots')
    need(authority.get('activated') is False and authority.get('native_accepted') is False,
         'no native authority substitution')
    need(authority['recipient_theory_sha256'] == digest(logical_context['theory'])
         and original_context == {'theory': logical_context['theory'],
                                  'ordered_local_premises': logical_context['ordered_Gamma']},
         'unchanged original theory and full Gamma')
    need(digest({k: v for k, v in authority.items() if k != 'epoch'}) == authority['epoch'],
         'original authority epoch')
    registry, context_id = digest(formulas), digest(original_context)
    need(binding['primitive_authority_epoch'] == authority['epoch']
         and binding['formula_registry_sha256'] == registry
         and binding['local_context_id'] == context_id
         and set(binding) == {'model_epoch', 'primitive_authority_epoch',
                             'formula_registry_sha256', 'local_context_id'},
         'exact original four-field epoch binding')
    codes = {canonical(f): i for i, f in enumerate(formulas)}
    need(len(codes) == len(formulas), 'injective original formula registry')
    recipes, ids, lookup = [], set(), set()
    for index, record in enumerate(records):
        tick()
        w, premises = record['primitive_witness'], record['ordered_premise_formulas']
        rule = w['rule']
        need(rule in ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption', 'generalize')
             and not (profile == 'Hilbert-five-rule-ground' and rule == 'generalize'),
             'profile-specific original primitive rules')
        arity = 2 if rule == 'mp' else 1 if rule == 'generalize' else 0
        need(type(premises) is list and len(premises) == arity
             and not any(k in w for k in ('antecedent', 'implication', 'source')),
             'original witness has exact ordered recipe ports, not physical refs')
        if rule == 'mp':
            need(premises[1] == ['imp', premises[0], w['formula']], 'ordered MP interface')
        if rule == 'generalize':
            need(w['formula'] == ['all', w['variable'], premises[0]], 'original unary interface')
        if rule == 'assumption':
            occurrence = integer(w['index'], 0, len(logical_context['ordered_Gamma']))
            need(w['formula'] == logical_context['ordered_Gamma'][occurrence],
                 'original Gamma occurrence, not formula deduplication')
        raw_recipe = {'primitive_witness': w, 'ordered_premise_formulas': premises}
        preimage = {'recipe': raw_recipe, 'primitive_authority_epoch': authority['epoch'],
                    'recipient_theory_sha256': authority['recipient_theory_sha256'],
                    'marking_version': marking, 'formula_registry_sha256': registry}
        if profile == 'Q-six-rule-open-parameter' or rule == 'assumption':
            preimage['local_context_id'] = context_id
        need(record['identity_preimage'] == preimage, 'exact original recipe identity preimage')
        identifier = 'primitive-recipe-' + digest(preimage)
        signature = canonical([w, premises])
        need(record['id'] == identifier and identifier not in ids and signature not in lookup,
             'original unique recipe identity and ordered interface')
        ids.add(identifier)
        lookup.add(signature)
        need(canonical(w['formula']) in codes
             and all(canonical(f) in codes for f in premises), 'all original formula code preimages')
        recipes.append({'index': index, 'id': identifier, 'witness': copy.deepcopy(w),
                        'premises': copy.deepcopy(premises),
                        'output': codes[canonical(w['formula'])],
                        'inputs': [codes[canonical(f)] for f in premises],
                        'original_record_sha256': digest(record),
                        'identity_preimage': copy.deepcopy(preimage)})
    # Original PointGraph stores fixed assignments once, with one refcount.
    fixed = {}
    for triple in fixed_marks:
        need(type(triple) is list and len(triple) == 3, 'literal original fixed mark')
        x, y, v = triple
        integer(x); integer(y, 1-height, height); integer(v, -1)
        need((x, y) not in fixed or fixed[(x, y)] == v, 'consistent original fixed marking')
        fixed[(x, y)] = v
    fixed = [[*p, v] for p, v in sorted(fixed.items())]
    need(len(seed_keys) == len(logical_context['ordered_Gamma']),
         'every original Gamma occurrence has its own seed')
    for occurrence, raw in enumerate(seed_keys):
        need(type(raw) is list and len(raw) == 3 and raw[1:] == [occurrence, []],
             'original occurrence row and zero ordered ports')
        integer(raw[1], 0, height)
        recipe = recipes[integer(raw[0], 0, len(recipes))]
        need(recipe['witness'] == {'rule': 'assumption', 'index': occurrence,
                                  'formula': logical_context['ordered_Gamma'][occurrence]},
             'same indexed Gamma recipe, including duplicate formulas')
    epoch_preimage = {'height': height, 'context': original_context, 'registry': registry,
        'authority': authority['epoch'], 'recipes': [r['id'] for r in recipes],
        'fixed_marks': fixed, 'roots': roots, 'seed_keys': seed_keys,
        'marking_version': marking, 'fixture': False, 'source_bindings': source_bindings}
    need(digest(epoch_preimage) == binding['model_epoch'], 'exact original model epoch')
    tick()
    return {'schema': 'current-keyed-family-catalogue-v1', 'profile': profile,
        'context': copy.deepcopy(logical_context), 'original_context': copy.deepcopy(original_context),
        'formulas': copy.deepcopy(formulas), 'recipes': recipes, 'height': height,
        'fixed_marks': fixed, 'roots': copy.deepcopy(roots), 'seed_keys': copy.deepcopy(seed_keys),
        'marking_version': marking, 'binding': copy.deepcopy(binding),
        'original_source_bindings': copy.deepcopy(source_bindings),
        'model_epoch_preimage_sha256': digest(epoch_preimage),
        'new_encoding': False, 'ROOT_catalogue_admitted_by_this_adapter': False}


def catalogue_from_q(*, prepared_catalogue, original_graph_source_bindings, binding, tick):
    """Input is the exact existing parsed preparation['catalogue'], no new parse."""
    tick()
    before = digest(prepared_catalogue)
    data, spec = prepared_catalogue, prepared_catalogue['declaration']
    need(data['height'] == 24 and spec['height'] == 24 and spec['ordered_Gamma'] == []
         and type(spec['parameters']) is list and len(spec['parameters']) == 1,
         'current original Q profile, no silent context/height broadening')
    need(original_graph_source_bindings == data['authority']['source_bindings'],
         'same original seven-role Q provenance in graph and authority')
    need(data['context'] == {'theory': spec['theory'],
                            'ordered_local_premises': spec['ordered_Gamma']},
         'original declaration and occurrence-ordered Q context')
    need(data['formula_registry_sha256'] == digest(data['formula_codes']),
         'original Q formula registry')
    logical = {'theory': spec['theory'], 'parameters': spec['parameters'],
               'ordered_Gamma': spec['ordered_Gamma'], 'target': spec['target']}
    result = build_catalogue(profile='Q-six-rule-open-parameter', logical_context=logical,
        original_context=data['context'], authority=data['authority'], formulas=data['formula_codes'],
        records=data['recipes'], fixed_marks=data['boundary']['fixed_marks'],
        roots=data['boundary']['roots'], seed_keys=data['boundary']['seed_keys'],
        height=data['height'], source_bindings=original_graph_source_bindings,
        binding=binding, marking=Q_MARKING, tick=tick)
    need(digest(prepared_catalogue) == before, 'no producer catalogue mutation')
    tick()
    return result


def catalogue_from_hilbert(*, header, selected_wire, binding, tick):
    """Use exact current c8 SelectedWire, supplied/guarded by the future caller.

    SelectedWire retains its own complete stream/EOF authentication and original
    three-occurrence ABI. This adapter does not widen that reader to new cohorts.
    It materializes the WHOLE licensed catalogue; future resource fit is unknown.
    """
    tick()
    before = digest(header)
    formulas = []
    for code in range(integer(selected_wire.formula_count, 1)):
        tick()
        formulas.append(selected_wire.formula(code))
    records = []
    for index in range(integer(selected_wire.count, 1)):
        tick()
        record = selected_wire.recipe(index)
        need(record['index'] == index, 'original selected-wire index')
        w, premises = record['witness'], record['premises']
        preimage = {'recipe': {'primitive_witness': w, 'ordered_premise_formulas': premises},
            'primitive_authority_epoch': header['authority']['epoch'],
            'recipient_theory_sha256': header['authority']['recipient_theory_sha256'],
            'marking_version': H_MARKING, 'formula_registry_sha256': header['formula_registry_sha256']}
        if w['rule'] == 'assumption':
            preimage['local_context_id'] = header['context_id']
        original = {'id': record['id'], 'primitive_witness': w,
                    'ordered_premise_formulas': premises, 'identity_preimage': preimage}
        integer(record['output'], 0, len(formulas))
        for code in record['inputs']:
            integer(code, 0, len(formulas))
        need(record['record_sha256'] == digest(original)
             and record['output'] < len(formulas)
             and formulas[record['output']] == w['formula']
             and [formulas[c] for c in record['inputs']] == premises,
             'original full selected-wire record digest and formula-code relation')
        records.append(original)
    need(header['context_id'] == digest(header['context'])
         and header['formula_registry_sha256'] == digest(formulas)
         and type(header['height']) is int and header['height'] == 24
         and len(header['context']['ordered_local_premises']) == 3
         and header['orientation'] == 'identity'
         and header['marking_version'] == H_MARKING
         and header['dimensions']['source_body_count'] == 0,
         'exact current Hilbert header/context/registry/height')
    logical = {'theory': header['context']['theory'], 'parameters': [],
               'ordered_Gamma': header['context']['ordered_local_premises'],
               'target': header['target']}
    result = build_catalogue(profile='Hilbert-five-rule-ground', logical_context=logical,
        original_context=header['context'], authority=header['authority'], formulas=formulas,
        records=records, fixed_marks=header['boundary']['fixed_exterior_m'] +
                                    header['boundary']['fixed_target_m'],
        roots=[0]*24, seed_keys=[[i, row, []] for row, i in enumerate(header['assumption_recipe_indices'])],
        height=24, source_bindings=header['source_bindings'], binding=binding,
        marking=H_MARKING, tick=tick)
    need(binding['model_epoch'] == selected_wire.model_epoch() and digest(header) == before,
         'original selected reader epoch and unchanged whole header')
    tick()
    return result
