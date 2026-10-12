"""Prospective independent fresh-context/license/body/pool reconstruction.

Standard-library import only. The caller supplies exact pinned INDEPENDENT
symbolic/point/source-expansion libraries after a separately reviewed ROOT
activation. No producer compiler, model builder, parser, ordering or decoder
is called as acceptance authority. These routines have not been executed.
"""
import copy
import hashlib
import math

MARKING = 'injective-formula-ordered-mp-offset-v1'
BODY_CLOSURE = ('all recursive source dependencies in pinned full expansion and its prior independent audit; '
                'fresh recipient projection pending independent audit')


from independent_curriculum_selection_v1 import problem, selected_binding


def relative_pin(pin):
    return {k: pin[k] for k in ('path', 'sha256', 'bytes')}


def fresh_data(source, compiled, plan, plan_pin, p, b, symbolic, documents):
    """Reconstruct all 229 records and license them under independently built Gamma.

    Prior source bytes fix the 226 retained witness records; new independent
    logical calls establish their licenses again. Old acceptance is provenance.
    All three occurrence licenses are rederived. The identical original context retains its exact semantic IDs.
    """
    expected = problem(plan['selector']); selection_binding = selected_binding(documents, plan, p, b); old_model = next(m for m in source['models'] if m['height'] == 24)
    old_context = dict(theory=expected['theory'], ordered_local_premises=expected['old_gamma'])
    context = dict(theory=expected['theory'], ordered_local_premises=expected['gamma'])
    b.equal(old_model['context'], old_context, 'independently declared donor Gamma and guarded theory')
    p.need(old_model['context_id'] == p.digest(old_context), 'original contextual identity')
    b.equal(source['authority']['recipient_theory_sha256'], p.digest(expected['theory']), 'source authority is theory-bound')
    # This establishes all donor licenses afresh, not just an old receipt hash.
    _, _, _, _, old_rules = p.validate_model(source, symbolic)
    registry = p.digest(source['formula_codes']); authority = source['authority']['epoch']
    codes = {p.canonical(f): i for i, f in enumerate(source['formula_codes'])}
    hypothesis_codes = [codes[p.canonical(f)] for f in expected['gamma']]
    target_code = codes[p.canonical(expected['target'])]
    p.need(all(type(c) is int and 0 <= c < 217 for c in hypothesis_codes + [target_code]), 'literal five-context registry relation')
    recipes, indices, licenses = [], {}, []
    for index, old in enumerate(source['recipes']):
        item = copy.deepcopy(old); witness = old['primitive_witness']; ports = old['ordered_premise_formulas']
        is_assumption = witness['rule'] == 'assumption'
        if is_assumption:
            occurrence = p.integer(witness['index'])
            p.need(occurrence in range(3) and occurrence not in indices and not ports, 'three ordered assumption occurrences')
            b.equal(witness['formula'], expected['old_gamma'][occurrence], 'original occurrence formula')
            indices[occurrence] = index
            item.update(primitive_witness=dict(rule='assumption', index=occurrence,
                    formula=copy.deepcopy(expected['gamma'][occurrence])))
            preimage = dict(recipe=dict(primitive_witness=item['primitive_witness'], ordered_premise_formulas=[]),
                primitive_authority_epoch=authority, recipient_theory_sha256=p.digest(expected['theory']),
                marking_version=MARKING, formula_registry_sha256=registry, local_context_id=p.digest(context))
            item.update(identity_preimage=preimage, id='primitive-recipe-' + p.digest(preimage))
            if context == old_context:
                b.equal(item, old, 'identical semantic context keeps exact occurrence record')
            else:
                p.need(item['id'] != old['id'], 'changed context regenerates every assumption identity')
        else:
            b.equal(item, old, 'all non-assumption complete source records retained verbatim')
        recipes.append(item)
        licenses.append(dict(index=index, kind='fresh_context_assumption' if is_assumption else 'literal_non_assumption_source_record',
            old_recipe_id=old['id'], new_recipe_id=item['id'], source_record_sha256=p.digest(old),
            new_record_sha256=p.digest(item), primitive_witness_sha256=p.digest(item['primitive_witness']),
            ordered_premise_sha256=p.digest(ports), native_accepted=False,
            fresh_independent_acceptance='pending; old audit binds source witness only'))
    p.need(set(indices) == {0, 1, 2} and len(recipes) == 229, 'entire 226 plus three fresh licenses')
    b.equal(compiled['recipes'], recipes, 'entire fresh primitive records and identity preimages')
    b.equal(compiled['recipe_licenses'], licenses, 'all 229 explicit fresh/retained license provenance fields')
    bindings = {r['role']: relative_pin(r) for r in plan['inputs']}
    p.need(len(bindings) == len(plan['inputs']), 'distinct preparation role names')
    bindings['fresh_context_compiler_plan'] = plan_pin
    source_pins = [plan_pin] + [relative_pin(r) for r in plan['sources'] + plan['inputs']]
    boundary = dict(required=[[0, r] for r in range(24)], root_generations=[[0, r, 0] for r in range(24)],
        fixed_exterior_m=[[1, r, -1] for r in range(-23, 0)], fixed_target_m=[[1, 23, target_code]],
        fixed_initial_local_seeds=[dict(recipe_id=recipes[indices[i]]['id'], row=i, generation=0) for i in range(3)],
        all_root_obligations_generation_zero=True)
    # No undocumented donor boundary fields or implicitly changed obligations.
    p.need(set(old_model['boundary']) == set(boundary), 'exact boundary field set')
    expected_fields = dict(schema='closed-frozen-curriculum-context-v1',
        status='compiled_frozen_curriculum_context_pending_independent_validation', height=24,
        context=context, context_id=p.digest(context), source_context_id=p.digest(old_context),
        theory=expected['theory'], target=expected['target'], formula_codes=source['formula_codes'],
        formula_registry_sha256=registry, authority=source['authority'],
        primitive_authority_epoch_policy='Exact inactive theory-bound source authority retained; semantic context/occurrence licenses and fresh compiler provenance/model/full-placement/body/pool bindings reconstructed.',
        recipes=recipes, recipe_licenses=licenses, assumption_recipe_indices=[indices[i] for i in range(3)],
        boundary=boundary, orientation='identity', marking_version=MARKING,
        source_bindings=bindings, source_pins=source_pins, curriculum_binding=selection_binding,
        hypothesis_codes=hypothesis_codes, target_code=target_code, non_assumption_records_preserved_verbatim=226,
        native_queries=0, native_accepted=False, model_constructed_by_compile_context=False,
        scope='Authored exact frozen curriculum context compilation; no proof search or logical checker acceptance.')
    p.need(set(compiled) == set(expected_fields) | {'compiler_seconds'}, 'exact fresh compiled payload field set')
    for name, value in expected_fields.items(): b.equal(compiled[name], value, 'complete compiled field ' + name)
    seconds = compiled['compiler_seconds']
    p.need(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0, 'saved compiler cost only, finite nonnegative')
    # Independent adapter to the unchanged literal point grammar; no production
    # compiler/model factory is called to construct acceptance data.
    model = dict(height=24, context=context, context_id=p.digest(context), authority_epoch=authority,
        boundary=boundary, orientation='identity', transform_grammar='vertical integer translation only',
        mp_offset_domain=[-23, -1], positive_support_alignment_domain=[0, 23],
        primitive_recipe_ids=[r['id'] for r in recipes])
    two_ports = sum(len(r['ordered_premise_formulas']) == 2 for r in recipes)
    p.need(all(len(r['ordered_premise_formulas']) in (0, 2) for r in recipes), 'complete zero/two ordered-port grammar')
    zero_ports = len(recipes) - two_ports
    unequal = sum(len(r['ordered_premise_formulas']) == 2 and
        r['ordered_premise_formulas'][0] != r['ordered_premise_formulas'][1] for r in recipes)
    model['counts'] = dict(raw_positive_support_alignments=24 * (zero_ports + two_ports * 23 ** 2),
        locally_consistent_strict_prior_bindings=zero_ports * 24 + two_ports * sum(r*r for r in range(24)) - unequal * sum(range(24)))
    data = dict(formula_codes=copy.deepcopy(source['formula_codes']), formula_registry_sha256=registry,
        recipes=recipes, authority=copy.deepcopy(source['authority']), models=[model])
    fresh_model, inventory, checker, seeds, fresh_rules = p.validate_model(data, symbolic)
    p.need(fresh_rules == old_rules and fresh_rules['assumption'] == 3, 'all unchanged rule counts with new licenses')
    fixed = sorted(boundary['fixed_exterior_m'] + boundary['fixed_target_m']); roots = [0] * 24
    epoch = p.digest(dict(height=24, context=context, registry=registry, authority=authority,
        recipes=[r['id'] for r in inventory], fixed_marks=fixed, roots=roots,
        seed_keys=[b.key_data(k) for k in seeds], marking_version=MARKING, fixture=False, source_bindings=bindings))
    state = p.State(24, inventory, fixed, roots, epoch)
    for key in seeds: state.apply(key, generation=0)
    binding = b.graph_binding(state, context, data['authority'], data['formula_codes'], bindings, seeds, fixed)
    return dict(data=data, model=fresh_model, state=state, binding=binding, problem=expected,
        source_bindings=bindings, source_pins=source_pins, primitive_rules=fresh_rules,
        curriculum_binding=selection_binding, hypothesis_codes=hypothesis_codes, target_code=target_code,
        assumptions=[dict(occurrence=i, recipe_index=indices[i], recipe_id=recipes[indices[i]]['id'],
            formula=expected['gamma'][i]) for i in range(3)], context_id=p.digest(context), model_epoch=epoch)


def fresh_pool_class(static):
    """Reuse independent exhaustive embedding/enumeration, not producer prepare."""
    class FreshPool(static.IndependentPool):
        def __init__(self, p, b, accepted, original_plan, certificate, schemas, projected, expansion):
            state, binding, data, model = accepted['state'], accepted['binding'], accepted['data'], accepted['model']
            self.p, self.b, self.s, self.binding = p, b, state, binding
            self.context, self.authority, self.formulas = model['context'], data['authority']['epoch'], data['formula_codes']
            self.registry = p.digest(self.formulas)
            self.bodies, self.source_counts, self.source_receipts = b.family_bodies(certificate, schemas, projected, data, expansion)
            old_pins = [relative_pin(r) for r in original_plan['inputs']]
            p.need(len(old_pins) == len({r['path'] for r in old_pins}) == 56, 'all original 56 unique source-body inputs')
            combined = {}
            for item in old_pins + accepted['source_pins']:
                previous = combined.setdefault(item['path'], item)
                b.equal(previous, item, 'no inconsistent duplicate source binding')
            self.original_sources = [combined[path] for path in sorted(combined)]
            for record in self.bodies:
                record['earlier_expansion_closure'] = BODY_CLOSURE
                record['ordered_receptor_ports'] = b.receptor_ports(record, state.recipes)
                for member in record['primitive_members']:
                    recipe = next(r for r in state.recipes if r['id'] == member['recipe_id'])
                    p.need(recipe['witness']['rule'] != 'assumption', 'canonical local aliases do not become global recipient seeds')
            self.original_epoch = p.digest(dict(graph=binding, sources=self.original_sources,
                bodies=[[r['name'], p.digest(r)] for r in self.bodies], version='whole-cluster-lifecycle-v1'))
            named = {r['name']: r for r in self.bodies}; self.interfaces = []
            for declaration in projected['definitions']:
                source = named[declaration['name']]
                p.need(source['full_frozen_definition_sha256'] == p.digest(declaration), 'complete independent projection digest')
                row, code = p.integer(declaration['canonical_conclusion_row']), p.integer(declaration['conclusion_code'])
                outputs = [m for m in source['primitive_members'] if m['row'] == row]
                p.need(len(outputs) == 1 and outputs[0]['formula_code'] == code, 'explicit non-last declared output binding')
                b.equal(self.formulas[code], declaration['conclusion_ast'], 'declared conclusion AST')
                b.equal([self.formulas[c] for c in source['premise_codes']], declaration['premise_ast'], 'ordered premise ASTs')
                self.interfaces.append(dict(name=source['name'], body_sha256=p.digest(source),
                    full_projection_sha256=p.digest(declaration), body=source, conclusion_row=row, conclusion_code=code))
            self.interfaces.sort(key=lambda r: p.canonical([r['name'], r['body_sha256']]))
            self.named = {r['name']: r for r in self.interfaces}
            self.anchors = []
            for key in state.order:
                recipe = state.recipes[key[0]]
                p.need(state.selected[key] == 0 and recipe['witness']['rule'] == 'assumption' and not key[2], 'new original Gamma seeds only')
                t, m = p.points(recipe, key[1], key[2], 24)
                self.anchors.append(dict(key=b.key_data(key), full_id=p.decorate(key, t, m, state.recipes,
                    self.context, self.authority, self.registry)['id'], formula_code=recipe['output'], generation=0))
            b.equal([r['formula_code'] for r in self.anchors], accepted['hypothesis_codes'], 'all three exact Gamma anchors in occurrence order')
            self.new_sources = copy.deepcopy(accepted['source_pins'])
            self.group_specs, self.preliminary, self.type_visits, self.rejected = [], [], [], []
            self.disconnected = 0
    return FreshPool


def audit_preparation(accepted, pool, evidence, p, b):
    """Check every saved root, body, interface, group and literal initial domain."""
    state = accepted['state']; model = accepted['model']; counts = {}
    fields = dict(schema='fresh-context-whole-family-pool-preparation-v1',
        status='complete_fresh_context_preparation_pending_independent_static_audit',
        context=model['context'], context_id=accepted['context_id'], formula_codes=pool.formulas,
        formula_registry_sha256=pool.registry, primitive_authority_epoch=pool.authority,
        model_epoch=state.epoch, graph_binding=accepted['binding'], initial_graph_semantic_state=state.semantic(),
        original_body_authority_epoch=pool.original_epoch, original_body_authority_graph_text=accepted['binding'],
        original_body_authority_source_bindings=pool.original_sources,
        all_source_bodies=[dict(name=r['name'], body=r) for r in pool.bodies], declared_interfaces=pool.interfaces,
        declared_interface_projection_sha256=p.digest(pool.interfaces), root_anchors=pool.anchors,
        group_authority_epoch=pool.epoch, groups=pool.groups, licenses=229, non_assumption_witnesses=226,
        source_body_count=171, recipes=229, formulas=217, height=24, model_constructions=1,
        recipient_seed_placements=3, Controller_calls=0, Executor_calls=0, target_searches=0,
        logical_checker_calls=0, native_queries=0, new_RL_training=False,
        curriculum_binding=accepted['curriculum_binding'], hypothesis_codes=accepted['hypothesis_codes'],
        target_code=accepted['target_code'], RL_full_pool_capacity=64,
        RL_full_pool_capacity_satisfied=len(pool.groups) <= 64,
        authority_scope='Fresh frozen-context finite point/body/pool preparation; old source receipts are provenance. Independent per-context static acceptance is mandatory before trajectories.')
    p.need(set(evidence) == set(fields) | {'plan','sources','inputs','compiled_context_pin',
        'complete_initial_domains','initial_complete_candidate_count','group_epoch_payload','preparation_counters','costs'},
        'complete exact curriculum preparation evidence field set')
    p.need(set(evidence['costs']) == {'context_compilation_seconds','scientific_import_seconds',
        'graph_construction_seconds','all_body_registration_seconds','complete_pool_preparation_seconds',
        'complete_initial_domain_census_seconds'}, 'exact producer setup and complete census cost fields')
    p.need(all(type(value) in (int,float) and math.isfinite(value) and value >= 0
               for value in evidence['costs'].values()), 'producer cost observations finite and nonnegative')
    for name, value in fields.items(): b.equal(evidence[name], value, 'complete fresh preparation field ' + name)
    payload = dict(version=pool.grammar['version'], grammar=pool.grammar, graph=accepted['binding'],
        original_authority_epoch=pool.original_epoch, interfaces=p.digest(pool.interfaces), root_anchors=pool.anchors,
        pool_specs=pool.group_specs, fixed_priorities=pool.priorities, source_bindings=pool.new_sources)
    b.equal(evidence['group_epoch_payload'], payload, 'entire frozen complete pool epoch preimage')
    rows, total = [], 0
    for row in range(24):
        stream = hashlib.sha256(); count = 0
        # Exhaust every declared raw negative-offset alignment; fixed exterior
        # marks perform the reduction. No sampled proposals supply graph counts.
        for key, t, m in state.raw_candidates(row):
            stream.update((p.canonical(dict(key=b.key_data(key), t=t, m=m)) + '\n').encode())
            count += 1
        rows.append(dict(row=row, count=count, key_t_m_stream_sha256=stream.hexdigest())); total += count
    b.equal(evidence['complete_initial_domains'], rows, 'all 24 exact raw key/t/m domain streams')
    b.equal(evidence['initial_complete_candidate_count'], total, 'full primitive initial candidate census')
    converted = dict(grammar=pool.grammar, root_anchors=evidence['root_anchors'], group_authority_epoch=evidence['group_authority_epoch'],
        original_body_authority_epoch=evidence['original_body_authority_epoch'], formula_codes=evidence['formula_codes'],
        formula_registry_sha256=evidence['formula_registry_sha256'], unchanged_model_epoch=evidence['model_epoch'],
        interface_summary=[{k:r[k] for k in ('name','body_sha256','full_projection_sha256','conclusion_row','conclusion_code')}
            | dict(ordered_premise_codes=r['body']['premise_codes'], canonical_input_rows=r['body']['canonical_input_rows'],
                primitive_member_count=len(r['body']['primitive_members'])) for r in evidence['declared_interfaces']],
        groups=evidence['groups'], counters=evidence['preparation_counters'])
    counts = pool.audit(converted)
    return dict(complete_census=counts, initial_rows=rows, initial_complete_candidates=total)


def context_controls(source, compiled, plan, plan_pin, p, b, symbolic, documents):
    """Guaranteed changed payloads; each is actually rechecked only under ROOT."""
    tests = []
    def add(name, mutate):
        item = copy.deepcopy(compiled); mutate(item)
        p.need(p.canonical(item) != p.canonical(compiled), 'each negative control really changes the payload')
        tests.append((name, item))
    add('changed-hypothesis-occurrence', lambda r:r['context']['ordered_local_premises'].__setitem__(0, ['bot']))
    add('changed-context-id', lambda r:r.__setitem__('context_id', 'invalid-context-identity'))
    add('missing-original-hypothesis', lambda r:r['context']['ordered_local_premises'].pop())
    add('zero-generation-changed', lambda r:r['boundary']['root_generations'][23].__setitem__(2, 1))
    add('required-row-omitted', lambda r:r['boundary']['required'].pop())
    add('exterior-zero-instead-of-negative-sentinel', lambda r:r['boundary']['fixed_exterior_m'][0].__setitem__(2, 0))
    add('wrong-target-code', lambda r:r['boundary']['fixed_target_m'][0].__setitem__(2, (r['target_code'] + 1) % 217))
    add('changed-contextual-assumption-id', lambda r:r['recipes'][r['assumption_recipe_indices'][0]].__setitem__('id', 'invalid-contextual-assumption'))
    add('boolean-assumption-occurrence', lambda r:r['recipes'][r['assumption_recipe_indices'][0]]['primitive_witness'].__setitem__('index', False))
    add('retained-witness-output-changed', lambda r:next(x for x in r['recipes'] if x['primitive_witness']['rule']=='eq_subst')['primitive_witness'].__setitem__('formula', ['bot']))
    add('missing-retained-rule', lambda r:r['recipes'].pop(0))
    add('changed-source-authority', lambda r:r['authority'].__setitem__('activated', True))
    add('source-local-premise-invented-as-global-root', lambda r:r['boundary']['fixed_initial_local_seeds'].append(copy.deepcopy(r['boundary']['fixed_initial_local_seeds'][0])))
    add('ordered-mp-ports-reversed', lambda r:next(x for x in r['recipes'] if x['primitive_witness']['rule']=='mp' and x['ordered_premise_formulas'][0] != x['ordered_premise_formulas'][1])['ordered_premise_formulas'].reverse())
    add('wrong-selector-binding', lambda r:r['curriculum_binding'].__setitem__('selector', 'unfrozen-context'))
    add('changed-donor-heldout-partition', lambda r:r['curriculum_binding'].__setitem__('partition', 'heldout' if r['curriculum_binding']['partition']=='donor' else 'donor'))
    add('changed-document-selfhash', lambda r:r['curriculum_binding']['document_bindings']['split'].__setitem__('canonical_sha256', '0'*64))
    add('missing-repeated-occurrence-license', lambda r:r['assumption_recipe_indices'].pop())
    add('changed-hypothesis-code', lambda r:r['hypothesis_codes'].__setitem__(0, (r['hypothesis_codes'][0]+1)%217))
    receipts = []
    for name, mutant in tests:
        try: fresh_data(source, mutant, plan, plan_pin, p, b, symbolic, documents)
        except (ValueError, KeyError, IndexError) as exc:
            receipts.append(dict(name=name, rejected=True, mutant_sha256=p.digest(mutant), reason=str(exc),
                scope='Actual changed payload rerun through independent frozen selection/context/license reconstruction'))
        else: raise ValueError('context mutant accepted: ' + name)
    return receipts
