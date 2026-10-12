"""Frozen five-context compiler library. SOURCE ONLY until ROOT activation.

The selector is a literal metadata resolver, not a theorem generator. All
non-assumption records and all conditional bodies are preserved. No model,
checker or policy is imported here; deferred callers provide the pinned core.
An identical semantic Gamma may keep its original contextual assumption IDs.
Repeated premises always retain their distinct ordered occurrence licenses.
"""
import copy
import hashlib
import json
import time

VERSION = 'closed-frozen-curriculum-context-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'
SELECTORS = ('donor-two-guards', 'donor-two-equalities',
             'donor-repeated-guard', 'donor-repeated-equality',
             'heldout-mixed-guard-equality')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def integer(value):
    if type(value) is not int:
        raise ValueError('exact integer required')
    return value


def compile_context(source, selected, reference, source_bindings, source_pins):
    """Compile one exact pre-resolved frozen context without any proof word.

    The future worker must first verify the exact plan/document/selector pins
    and invoke the frozen selection module. Independent acceptance must repeat
    the literal selection and license reconstruction with its own code.
    """
    started = time.perf_counter()
    if (type(selected) is not dict or selected.get('id') not in SELECTORS
            or selected.get('rows') != 24 or type(selected['rows']) is not int
            or selected.get('split') != ('heldout' if selected['id'] == SELECTORS[-1] else 'donor')):
        raise ValueError('one exact frozen donor/heldout selector required')
    binding = selected['binding']
    if (binding['schema'] != 'frozen-five-context-selection-v1'
            or binding['selector'] != selected['id'] or binding['partition'] != selected['split']
            or binding['rows'] != 24 or binding['source_only_selection'] is not True):
        raise ValueError('exact frozen metadata selection binding required')
    semantic = {k: selected[k] for k in ('theory', 'ordered_hypotheses', 'target', 'rows')}
    if (binding['resolved_context_sha256'] != digest(semantic)
            or binding['ordered_hypotheses_sha256'] != digest(selected['ordered_hypotheses'])
            or binding['target_sha256'] != digest(selected['target'])):
        raise ValueError('complete selected context binding changed')
    for role, metadata_role in (('reference', 'curriculum_reference'),
                                ('split', 'frozen_donor_split'),
                                ('protocol', 'frozen_RL_protocol')):
        if binding['document_bindings'][role]['raw_pin'] != source_bindings[metadata_role]:
            raise ValueError('exact curriculum document source binding: ' + role)
    if len(source['formula_codes']) != 217 or len(source['recipes']) != 229:
        raise ValueError('complete original finite palette required')
    codes = {canonical(f): i for i, f in enumerate(source['formula_codes'])}
    if len(codes) != 217 or digest(source['formula_codes']) != source['formula_registry_sha256']:
        raise ValueError('injective exact formula registry')
    old_models = [m for m in source['models'] if m['height'] == 24]
    if len(old_models) != 1:
        raise ValueError('unique original 24-row model required')
    old = old_models[0]; old_context = old['context']
    if (old_context['theory'] != reference['theory_ast']
            or old_context['ordered_local_premises'] != reference['original_ordered_hypotheses_ast']
            or old['context_id'] != digest(old_context)
            or selected['theory'] != reference['theory_ast']):
        raise ValueError('exact retained original Gamma and theory binding')
    premises = copy.deepcopy(selected['ordered_hypotheses'])
    if type(premises) is not list or len(premises) != 3:
        raise ValueError('three ordered original hypothesis occurrences required')
    premise_codes = [codes.get(canonical(f)) for f in premises]
    target_code = codes.get(canonical(selected['target']))
    if any(type(code) is not int for code in premise_codes + [target_code]):
        raise ValueError('every frozen hypothesis/target must occur in the exact registry')
    if selected['id'] == SELECTORS[-1] and (premise_codes != [11, 42, 52] or target_code != 54):
        raise ValueError('unchanged frozen mixed heldout registry relation')
    context = {'theory': copy.deepcopy(old_context['theory']), 'ordered_local_premises': premises}
    context_id = digest(context)
    authority = copy.deepcopy(source['authority'])
    if (authority.get('activated') is not False or authority.get('native_accepted') is not False
            or digest({k: v for k, v in authority.items() if k != 'epoch'}) != authority['epoch']
            or authority['recipient_theory_sha256'] != digest(context['theory'])):
        raise ValueError('inactive exact theory-bound primitive authority required')
    recipes = []; licenses = []; assumption_indices = {}; identities = set(); retained = 0
    for index, raw in enumerate(source['recipes']):
        item = copy.deepcopy(raw); witness = item['primitive_witness']; ports = item['ordered_premise_formulas']
        preimage = {'recipe': {'primitive_witness': witness, 'ordered_premise_formulas': ports},
            'primitive_authority_epoch': authority['epoch'],
            'recipient_theory_sha256': authority['recipient_theory_sha256'],
            'marking_version': MARKING, 'formula_registry_sha256': source['formula_registry_sha256']}
        is_assumption = witness['rule'] == 'assumption'
        if is_assumption:
            preimage['local_context_id'] = old['context_id']
        if raw['identity_preimage'] != preimage or raw['id'] != 'primitive-recipe-' + digest(preimage):
            raise ValueError('source record identity/witness is not exact')
        if is_assumption:
            occurrence = integer(witness['index'])
            if (occurrence not in range(3) or occurrence in assumption_indices or ports
                    or witness['formula'] != old_context['ordered_local_premises'][occurrence]):
                raise ValueError('exact distinct ordered hypothesis occurrence license')
            assumption_indices[occurrence] = index
            item['primitive_witness'] = {'rule': 'assumption', 'index': occurrence,
                                         'formula': copy.deepcopy(premises[occurrence])}
            item['ordered_premise_formulas'] = []
            new_preimage = copy.deepcopy(preimage)
            new_preimage['recipe']['primitive_witness'] = copy.deepcopy(item['primitive_witness'])
            new_preimage['local_context_id'] = context_id
            item['identity_preimage'] = new_preimage
            item['id'] = 'primitive-recipe-' + digest(new_preimage)
            # Identity is semantic. A same-context record MUST remain the same;
            # source/provenance freshness lives in graph bindings, not fake IDs.
            if context_id == old['context_id'] and item != raw:
                raise ValueError('identical semantic context must retain the exact assumption record')
            if context_id != old['context_id'] and item['id'] == raw['id']:
                raise ValueError('changed Gamma cannot reuse a stale assumption identity')
        else:
            retained += 1
            if item != raw or witness['rule'] not in ('axiom', 'instantiate', 'eq_subst', 'mp'):
                raise ValueError('all complete non-assumption witnesses retained verbatim')
        if item['id'] in identities:
            raise ValueError('duplicate recipe identity, including repeated assumption occurrences')
        identities.add(item['id'])
        if (canonical(item['primitive_witness']['formula']) not in codes
                or any(canonical(f) not in codes for f in item['ordered_premise_formulas'])):
            raise ValueError('every exact licensed interface stays in the complete formula registry')
        recipes.append(item)
        licenses.append({'index': index,
            'kind': 'fresh_context_assumption' if is_assumption else 'literal_non_assumption_source_record',
            'old_recipe_id': raw['id'], 'new_recipe_id': item['id'],
            'source_record_sha256': digest(raw), 'new_record_sha256': digest(item),
            'primitive_witness_sha256': digest(item['primitive_witness']),
            'ordered_premise_sha256': digest(ports), 'native_accepted': False,
            'fresh_independent_acceptance': 'pending; old audit binds source witness only'})
    if retained != 226 or set(assumption_indices) != {0, 1, 2}:
        raise ValueError('entire 226 plus three occurrence licenses required')
    boundary = copy.deepcopy(old['boundary'])
    expected_boundary = {'required': [[0, r] for r in range(24)],
        'root_generations': [[0, r, 0] for r in range(24)],
        'fixed_exterior_m': [[1, r, -1] for r in range(-23, 0)],
        'fixed_target_m': [[1, 23, codes[canonical(reference['target_ast'])]]],
        'fixed_initial_local_seeds': [{'recipe_id': source['recipes'][assumption_indices[k]]['id'],
                                      'row': k, 'generation': 0} for k in range(3)],
        'all_root_obligations_generation_zero': True}
    if boundary != expected_boundary:
        raise ValueError('entire original point boundary, including every root obligation')
    boundary['fixed_target_m'] = [[1, 23, target_code]]
    boundary['fixed_initial_local_seeds'] = [{'recipe_id': recipes[assumption_indices[k]]['id'],
                                            'row': k, 'generation': 0} for k in range(3)]
    return {'schema': VERSION, 'status': 'compiled_frozen_curriculum_context_pending_independent_validation',
        'height': 24, 'context': context, 'context_id': context_id, 'source_context_id': old['context_id'],
        'theory': copy.deepcopy(context['theory']), 'target': copy.deepcopy(selected['target']),
        'formula_codes': copy.deepcopy(source['formula_codes']),
        'formula_registry_sha256': source['formula_registry_sha256'], 'authority': authority,
        'primitive_authority_epoch_policy': 'Exact inactive theory-bound source authority retained; semantic context/occurrence licenses and fresh compiler provenance/model/full-placement/body/pool bindings reconstructed.',
        'recipes': recipes, 'recipe_licenses': licenses,
        'assumption_recipe_indices': [assumption_indices[k] for k in range(3)],
        'boundary': boundary, 'orientation': 'identity', 'marking_version': MARKING,
        'source_bindings': copy.deepcopy(source_bindings), 'source_pins': copy.deepcopy(source_pins),
        'curriculum_binding': copy.deepcopy(binding), 'hypothesis_codes': premise_codes, 'target_code': target_code,
        'non_assumption_records_preserved_verbatim': 226, 'compiler_seconds': time.perf_counter() - started,
        'native_queries': 0, 'native_accepted': False, 'model_constructed_by_compile_context': False,
        'scope': 'Authored exact frozen curriculum context compilation; no proof search or logical checker acceptance.'}


def construct_graph(compiled, core):
    """Future gated PointGraph construction; only three licensed gen-zero seeds."""
    if (compiled['schema'] != VERSION
            or compiled['status'] != 'compiled_frozen_curriculum_context_pending_independent_validation'
            or compiled['marking_version'] != core.MARKING_VERSION or compiled['orientation'] != 'identity'):
        raise ValueError('exact unchanged point grammar and compiled context schema')
    seeds = tuple(core.Key(index, k) for k, index in enumerate(compiled['assumption_recipe_indices']))
    graph = core.PointGraph(height=24, formulas=compiled['formula_codes'], recipe_data=compiled['recipes'],
        context=compiled['context'], authority=compiled['authority'],
        fixed_marks=compiled['boundary']['fixed_exterior_m'] + compiled['boundary']['fixed_target_m'],
        roots=[0] * 24, seed_keys=seeds, source_bindings=compiled['source_bindings'])
    if (graph.context_id != compiled['context_id'] or graph.registry_sha != compiled['formula_registry_sha256']
            or [graph.recipes[k.recipe].output for k in graph.initial_selected] != compiled['hypothesis_codes']):
        raise ValueError('exact context-bound ordered seed relation differs')
    return graph


def construct_family_authority(graph, projection, life, source_pins):
    """Preserve all 171 conditional source bodies; no local aliases become roots."""
    core = life.core
    if (projection['formula_codes'] != graph.formulas or projection['authority_epoch'] != graph.authority_epoch
            or projection['native_accepted'] is not False):
        raise ValueError('exact retained theory-source projection relation')
    bodies = []
    for definition in projection['definitions']:
        body = {'kind': 'finite_source_body_structurally_certified_not_native_accepted',
            'name': definition['name'], 'canonical_input_rows': copy.deepcopy(definition['canonical_input_rows']),
            'premise_codes': copy.deepcopy(definition['premise_codes']),
            'primitive_members': [{k: copy.deepcopy(member[k]) for k in
                ('row', 'recipe_id', 'formula_code', 'ordered_inputs')} for member in definition['primitive_members']],
            'source_body_sha256': definition['source_body_sha256'],
            'mapped_body_sha256': definition['mapped_body_sha256'],
            'dependency_bindings': [], 'native_accepted': False,
            'earlier_expansion_closure': 'all recursive source dependencies in pinned full expansion and its prior independent audit; fresh recipient projection pending independent audit',
            'full_frozen_definition_sha256': core.digest(definition)}
        for member in body['primitive_members']:
            recipe = graph.recipes[graph.recipe_index[member['recipe_id']]]
            if recipe.witness['rule'] == 'assumption':
                raise ValueError('source-local aliases cannot become global hypothesis recipes')
        body['ordered_receptor_ports'] = life.receptor_ports(body, graph)
        bodies.append(body)
    if len(bodies) != 171 or len({b['name'] for b in bodies}) != 171:
        raise ValueError('all 171 distinct conditional declarations required')
    unique = {}
    for pin in source_pins:
        literal = {k: pin[k] for k in ('path', 'sha256', 'bytes')}
        if literal['path'] in unique and unique[literal['path']] != literal:
            raise ValueError('inconsistent exact source pin alias')
        unique[literal['path']] = literal
    return life.BodyAuthority.build(graph, [unique[path] for path in sorted(unique)], bodies)
