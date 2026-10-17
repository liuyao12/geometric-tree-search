"""SOURCE ONLY independent generic five-rule FOL/catalog authority.

No producer/compiler/core/search/policy/native imports or dispatch. The caller
supplies exact original fixture/source bytes and, for graph reconstruction,
the pinned independent point-state library. This is not an actual receipt.
"""
import copy
import hashlib
import json

MARKING = 'injective-formula-ordered-mp-offset-v1'
DECLARATION = 'fresh-ground-cluster-context-declaration-v1'

# SOURCE-only literal profile; retained old cases are syntax seeds only.
FIXTURE_SCHEMA = 'hilbert-next-ground-theorem-fixtures-v1'
RECIPIENT_IDS = ('next-inc-equality-line-chain', 'next-inc-two-uniqueness', 'next-inc-derived-middle-guard')
SEED_CASE_IDS = ('train-pa-right-zero', 'train-pa-right-one', 'train-inc-line', 'train-inc-point', 'train-inc-uniqueness', 'eval-pa-chain', 'eval-pa-nested', 'eval-inc-both-arguments', 'eval-inc-uniqueness-point')


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canon(value).encode('utf8')).hexdigest()


def need(value, label):
    if not value:
        raise ValueError(label)


def name(value):
    return type(value) is str and bool(value)


def variables(value, bound=frozenset()):
    tag = value[0]
    if tag == 'var':
        return set() if value[1] in bound else {value[1]}
    if tag in ('fun', 'pred'):
        return set().union(*(variables(v, bound) for v in value[2]))
    if tag == 'all':
        return variables(value[2], bound | {value[1]})
    return set().union(*(variables(v, bound) for v in value[1:]))


def closed_replace(value, variable, term):
    if value[0] == 'var':
        return copy.deepcopy(term if value[1] == variable else value)
    if value[0] in ('fun', 'pred'):
        return [value[0], value[1], [closed_replace(v, variable, term) for v in value[2]]]
    if value[0] == 'all':
        return copy.deepcopy(value) if value[1] == variable else [
            'all', value[1], closed_replace(value[2], variable, term)]
    return [value[0]] + [closed_replace(v, variable, term) for v in value[1:]]


class GroundChecker:
    """Generic signature, five exact rules; induction metadata is retained only.

    No induction/generalization/reflexivity/tautology/conjunction rule is added.
    A proof is a ground consequence of the original ordered Gamma and named
    theory. This checker provides host symbolic checking, not native authority.
    """
    def __init__(self, theory):
        need(type(theory) is dict and set(theory) == {'functions', 'predicates', 'axioms', 'schemas'}, 'exact original theory grammar')
        need(theory['schemas'] in ([], ['nat-induction']), 'only retained unused declared schema metadata')
        for table in ('functions', 'predicates'):
            need(type(theory[table]) is dict, 'signature dictionary')
            need(all(name(n) and type(a) is int and a >= 0 for n, a in theory[table].items()), 'literal declared nonnegative arities')
        need(type(theory['axioms']) is dict and all(name(n) for n in theory['axioms']), 'named original axiom dictionary')
        self.theory = copy.deepcopy(theory)
        for formula in theory['axioms'].values():
            self.formula(formula); need(not variables(formula), 'closed original named axioms')

    def term(self, value):
        need(type(value) is list and value, 'literal term list')
        if value[0] == 'var':
            need(len(value) == 2 and name(value[1]), 'variable grammar'); return
        need(len(value) == 3 and value[0] == 'fun' and name(value[1])
             and type(value[2]) is list and value[1] in self.theory['functions']
             and len(value[2]) == self.theory['functions'][value[1]], 'exact function signature/arity')
        for subterm in value[2]:
            self.term(subterm)

    def formula(self, value):
        need(type(value) is list and value, 'literal formula list')
        tag = value[0]
        if tag == 'bot':
            need(len(value) == 1, 'bottom grammar')
        elif tag == 'eq':
            need(len(value) == 3, 'equality grammar'); self.term(value[1]); self.term(value[2])
        elif tag == 'pred':
            need(len(value) == 3 and name(value[1]) and type(value[2]) is list
                 and value[1] in self.theory['predicates']
                 and len(value[2]) == self.theory['predicates'][value[1]], 'exact predicate signature/arity')
            for term in value[2]:
                self.term(term)
        elif tag == 'all':
            need(len(value) == 3 and name(value[1]), 'universal grammar'); self.formula(value[2])
        else:
            need((tag == 'not' and len(value) == 2) or (tag in ('imp', 'and', 'or') and len(value) == 3), 'exact formula constructor')
            for formula in value[1:]:
                self.formula(formula)

    def command(self, command, prior, gamma):
        need(type(command) is dict, 'literal primitive command')
        rule = command.get('rule'); formula = command.get('formula'); self.formula(formula)
        fields = {'axiom': {'name'}, 'assumption': {'index'}, 'instantiate': {'universal', 'term'},
                  'eq_subst': {'variable', 'template', 'left', 'right'},
                  'mp': {'antecedent', 'implication'}}
        need(rule in fields and set(command) == fields[rule] | {'rule', 'formula'}, 'exact five-rule primitive fields')
        if rule == 'axiom':
            need(name(command['name']) and self.theory['axioms'].get(command['name']) == formula, 'original named axiom only')
        elif rule == 'assumption':
            k = command['index']; need(type(k) is int and 0 <= k < len(gamma) and gamma[k] == formula, 'exact indexed original hypothesis occurrence')
        elif rule == 'instantiate':
            universal, term = command['universal'], command['term']
            self.formula(universal); self.term(term)
            need(universal[0] == 'all' and not variables(term), 'universal and closed replacement required')
            need(formula == ['imp', universal, closed_replace(universal[2], universal[1], term)], 'exact capture-free instantiation schema')
        elif rule == 'eq_subst':
            variable, template = command['variable'], command['template']
            self.formula(template); self.term(command['left']); self.term(command['right'])
            need(name(variable) and template[0] in ('eq', 'pred') and variables(template) <= {variable}, 'declared atomic one-hole equality template')
            need(not variables(command['left']) and not variables(command['right']), 'closed equality operands')
            left, right = command['left'], command['right']
            need(formula == ['imp', ['eq', left, right], ['imp',
                 closed_replace(template, variable, left), closed_replace(template, variable, right)]], 'exact equality transport schema')
        else:
            a, b = command['antecedent'], command['implication']
            need(type(a) is int and type(b) is int and 0 <= a < len(prior) and 0 <= b < len(prior), 'exact ordered strict-prior MP references')
            need(prior[b] == ['imp', prior[a], formula], 'literal ordered modus ponens')
        return copy.deepcopy(formula)

    def proof(self, commands, gamma, target):
        for formula in [*gamma, target]:
            self.formula(formula); need(not variables(formula), 'original closed Gamma/target')
        prior = []
        for command in commands:
            prior.append(self.command(command, prior, gamma))
        need(prior and prior[-1] == target, 'original final target, no changed statement')
        return {'rows': len(prior), 'original_ground_sequent_accepted': True,
                'native_accepted': False, 'induction_commands': 0}


def subformulas(formula):
    yield formula
    if formula[0] == 'all':
        yield from subformulas(formula[2])
    elif formula[0] in ('not', 'and', 'or', 'imp'):
        for child in formula[1:]:
            yield from subformulas(child)


def subterms(term):
    yield term
    if term[0] == 'fun':
        for child in term[2]:
            yield from subterms(child)


def atom_terms(formula):
    if formula[0] in ('eq', 'pred'):
        for term in formula[2] if formula[0] == 'pred' else formula[1:]:
            yield from subterms(term)


def audit_catalog(compiled, fixture, instance_id, source_bindings):
    """Re-derive the complete catalog using no producer helper or expected trace.

    This first stage accepts an empty initial body inventory only. Every zero
    witness is also checked by the independent generic logical relation above.
    Whole point/model/state reconstruction is a separate caller-owned step.
    """
    need(type(fixture) is dict and fixture.get('schema') == FIXTURE_SCHEMA
         and type(instance_id) is str and instance_id in RECIPIENT_IDS
         and fixture.get('recipient_case_ids') == list(RECIPIENT_IDS)
         and fixture.get('source_only_seed_case_ids') == list(SEED_CASE_IDS)
         and [case['id'] for case in fixture['cases']] == list(SEED_CASE_IDS + RECIPIENT_IDS),
         'three fresh recipients; complete nine original syntax seeds required')
    need(fixture['schema'] == FIXTURE_SCHEMA
         and fixture['source_only'] is True and fixture['execution_authorized'] is False,
         'exact original source declaration fixture')
    matches = [case for case in fixture['cases'] if case['id'] == instance_id]
    need(len(matches) == 1, 'unique exact original instance')
    case = matches[0]; theory = fixture['theories'][case['theory']]
    checker = GroundChecker(theory)
    gamma = [fixture['literal_formulas'][n] for n in case['hypotheses']]
    target = fixture['literal_formulas'][case['target']]
    need(case['rows'] == 24 and len(gamma) == 3, 'original24 rows/3occurrences')
    selected = dict(instance_id=instance_id, split=case['split'], theory_key=case['theory'],
                    theory=theory, ordered_hypotheses=gamma, target=target, rows=24,
                    structural_tag=case['structural_tag'])
    grammar = fixture['finite_grammars'][case['theory']]
    need(grammar['instantiation_rounds'] == 4 and grammar['equality_layers'] == 1, 'exact finite syntax grammar')
    seeds = list(theory['axioms'].values())
    for item in fixture['cases']:
        if item['theory'] == case['theory']:
            seeds += [fixture['literal_formulas'][n] for n in item['hypotheses']]
            seeds.append(fixture['literal_formulas'][item['target']])
    known = {}; term_set = {}; names = set()
    for formula in seeds:
        checker.formula(formula); need(not variables(formula), 'closed declared original seed')
        for part in subformulas(formula):
            known[canon(part)] = copy.deepcopy(part)
            if part[0] == 'all':
                names.add(part[1])
            for term in atom_terms(part):
                if term[0] == 'var':
                    names.add(term[1])
                if not variables(term):
                    term_set[canon(term)] = copy.deepcopy(term)
    frozen_terms = [term_set[k] for k in sorted(term_set)]

    def is_numeral(term):
        while term[0] == 'fun' and term[1] == 'succ' and len(term[2]) == 1:
            term = term[2][0]
        return term == ['fun', 'zero', []]

    pools = {}
    for role, specification in sorted(grammar['term_roles'].items()):
        if specification == 'all_closed_seed_subterms':
            pool = frozen_terms
        elif specification == 'closed_seed_numerals':
            pool = [t for t in frozen_terms if is_numeral(t)]
        else:
            need(type(specification) is list, 'declared fixed syntactic constant role')
            pool = [t for t in frozen_terms if t[0] == 'fun' and not t[2] and t[1] in specification]
            need({t[1] for t in pool} == set(specification), 'complete named parameter pool')
        pools[role] = copy.deepcopy(pool)
    schemes = {}; rounds = []

    def insert(formula):
        for sub in subformulas(formula):
            known[canon(sub)] = copy.deepcopy(sub)

    for round_index in range(4):
        snapshot = [known[k] for k in sorted(known) if known[k][0] == 'all']
        before = len(schemes)
        for universal in snapshot:
            need(universal[1] in grammar['binder_roles'], 'every generated binder has a frozen role')
            for term in pools[grammar['binder_roles'][universal[1]]]:
                output = ['imp', universal, closed_replace(universal[2], universal[1], term)]
                command = dict(rule='instantiate', formula=output, universal=universal, term=term)
                checker.command(command, [], gamma)
                schemes[canon(command)] = copy.deepcopy(command); insert(output)
        rounds.append(dict(round=round_index, universal_count=len(snapshot),
                           new_distinct_schemes=len(schemes) - before,
                           scheme_count=len(schemes), formula_count=len(known)))
    hole = next('hole' + str(i) for i in range(len(names) + 1) if 'hole' + str(i) not in names)
    atoms = [known[k] for k in sorted(known) if known[k][0] in ('eq', 'pred') and not variables(known[k])]
    pairs = {canon(atom[1:]): atom[1:] for atom in atoms if atom[0] == 'eq'}
    templates = {}

    def abstract(value, old):
        if value == old:
            return ['var', hole]
        if value[0] == 'fun':
            return ['fun', value[1], [abstract(child, old) for child in value[2]]]
        return copy.deepcopy(value)

    for atom in atoms:
        terms = {canon(term): term for term in atom_terms(atom) if not variables(term)}
        args = atom[2] if atom[0] == 'pred' else atom[1:]
        for key in sorted(terms):
            old = terms[key]
            template = ['pred', atom[1], [abstract(t, old) for t in args]] if atom[0] == 'pred' else ['eq', *[abstract(t, old) for t in args]]
            need(template != atom, 'actual all-occurrence subterm abstraction')
            templates[canon(template)] = template
    before_equality = len(schemes)
    for template in [templates[k] for k in sorted(templates)]:
        for left, right in [pairs[k] for k in sorted(pairs)]:
            output = ['imp', ['eq', left, right], ['imp',
                      closed_replace(template, hole, left), closed_replace(template, hole, right)]]
            command = dict(rule='eq_subst', formula=output, variable=hole,
                           template=template, left=left, right=right)
            checker.command(command, [], gamma)
            schemes[canon(command)] = copy.deepcopy(command); insert(output)
    formulas = [known[k] for k in sorted(known)]; codes = {canon(f): i for i, f in enumerate(formulas)}
    context = dict(theory=theory, ordered_local_premises=gamma); context_id = sha(context)
    authority = dict(activated=False, native_accepted=False, recipient_theory_sha256=sha(theory),
                     declaration_schema=DECLARATION, finite_grammar_sha256=sha(grammar),
                     source_bindings=copy.deepcopy(source_bindings),
                     logical_qualification='pending independent complete witness/context gate')
    authority['epoch'] = sha(authority)
    witnesses = [(dict(rule='axiom', name=n, formula=f), []) for n, f in sorted(theory['axioms'].items())]
    witnesses += [(schemes[k], []) for k in sorted(schemes)]
    witnesses += [(dict(rule='mp', formula=f[2]), [f[1], f]) for f in formulas if f[0] == 'imp']
    witnesses += [(dict(rule='assumption', index=i, formula=f), []) for i, f in enumerate(gamma)]
    witnesses.sort(key=lambda item: canon(list(item)))
    need(len({canon(list(item)) for item in witnesses}) == len(witnesses), 'complete distinct primitive licenses')
    recipes = []; licenses = []; assumptions = {}
    for i, (witness, premises) in enumerate(witnesses):
        if premises:
            need(witness['rule'] == 'mp' and premises[1] == ['imp', premises[0], witness['formula']], 'exact ordered MP interface')
        else:
            checker.command(witness, [], gamma)
        preimage = dict(recipe=dict(primitive_witness=witness, ordered_premise_formulas=premises),
                        primitive_authority_epoch=authority['epoch'], recipient_theory_sha256=sha(theory),
                        marking_version=MARKING, formula_registry_sha256=sha(formulas))
        if witness['rule'] == 'assumption':
            preimage['local_context_id'] = context_id; assumptions[witness['index']] = i
        record = dict(id='primitive-recipe-' + sha(preimage), primitive_witness=witness,
                      ordered_premise_formulas=premises, identity_preimage=preimage)
        recipes.append(record)
        licenses.append(dict(recipe_index=i, recipe_id=record['id'], rule=witness['rule'],
                             record_sha256=sha(record), logical_accepted=False, native_accepted=False,
                             status='pending independent exact primitive license'))
    expected = dict(instance_id=instance_id, split=case['split'], height=24, context=context,
                    context_id=context_id, target=target, formula_codes=formulas,
                    formula_registry_sha256=sha(formulas), recipes=recipes, recipe_licenses=licenses,
                    authority=authority, assumption_recipe_indices=[assumptions[i] for i in range(3)],
                    hypothesis_codes=[codes[canon(f)] for f in gamma], target_code=codes[canon(target)],
                    source_bindings=source_bindings, orientation='identity', marking_version=MARKING,
                    declaration_binding=dict(fixture_sha256=sha(fixture), selected_sha256=sha(selected),
                                             grammar_sha256=sha(grammar), theory_key=case['theory']),
                    syntax_census=dict(seed_terms=frozen_terms, term_pools=pools,
                                      instantiation_rounds=rounds, template_variable=hole,
                                      closed_atomic_source_count=len(atoms),
                                      equality_pairs=[pairs[k] for k in sorted(pairs)],
                                      atomic_templates=[templates[k] for k in sorted(templates)],
                                      equality_scheme_count=len(schemes) - before_equality),
                    dimensions=dict(logical_rows=24, formula_count=len(formulas),
                                    primitive_license_count=len(recipes), non_assumption_witness_count=len(recipes) - 3,
                                    source_body_count=0))
    boundary = dict(required=[[0, r] for r in range(24)], root_generations=[[0, r, 0] for r in range(24)],
                    fixed_exterior_m=[[1, r, -1] for r in range(-23, 0)], fixed_target_m=[[1, 23, codes[canon(target)]]],
                    fixed_initial_local_seeds=[dict(recipe_id=recipes[assumptions[r]]['id'], row=r, generation=0) for r in range(3)],
                    all_root_obligations_generation_zero=True)
    expected.update(boundary=boundary, schema=DECLARATION,
                    status='complete_declared_catalog_pending_independent_qualification', bodies=[],
                    complete_cluster_inventory=[], target_searches=0, proof_certificates=0,
                    RNG_draws=0, new_RL_training=False, all_five_qualification=False, native_accepted=False)
    need(set(compiled) == set(expected) | {'scope', 'unchanged_model_epoch'}, 'exact complete prepared catalog field set')
    for field, value in expected.items():
        need(canon(compiled[field]) == canon(value), 'independent complete catalog differs: ' + field)
    need(compiled['scope'] == 'Fresh proper finite ground FOL grammar; complete declared syntax only. Full theory/schema data retained; induction/generalization/tautology/reflexivity commands outside this initial grammar. Empty initial cluster library, not learned reuse.', 'exact initial declared scope')
    return dict(status='independent_complete_fresh_catalog_licenses_rederived_pending_resources',
                instance_id=instance_id, context_id=context_id,
                formula_registry_sha256=sha(formulas), dimensions=expected['dimensions'],
                all_zero_port_licenses_symbolically_checked=True, all_ordered_MP_licenses_rederived=True,
                all_original_occurrences_retained=True, complete_catalog_accepted=True,
                original_five_context_qualification=False, proof_certificates=0,
                native_accepted=False, resource_accepted=False)


def audit_initial_graph(evidence, point):
    """Exact independent graph/identity/domain reconstruction from licensed data.

    The caller must first accept audit_catalog on these exact bytes. The pinned
    independent State derives literal reference domains and t/m updates, not
    producer masks, constructors or model helpers. No target search occurs.
    """
    compiled = evidence['compiled_context']
    need(type(compiled) is dict and type(compiled.get('instance_id')) is str
         and compiled['instance_id'] in RECIPIENT_IDS, 'only fresh recipient initial graph audit')
    codes = {canon(f): i for i, f in enumerate(compiled['formula_codes'])}
    recipes = [dict(id=r['id'], witness=r['primitive_witness'], premises=r['ordered_premise_formulas'],
                    output=codes[canon(r['primitive_witness']['formula'])],
                    inputs=tuple(codes[canon(f)] for f in r['ordered_premise_formulas']))
               for r in compiled['recipes']]
    boundary = compiled['boundary']; fixed = boundary['fixed_exterior_m'] + boundary['fixed_target_m']
    seeds = [(index, row, ()) for row, index in enumerate(compiled['assumption_recipe_indices'])]
    epoch = sha(dict(height=24, context=compiled['context'], registry=compiled['formula_registry_sha256'],
                     authority=compiled['authority']['epoch'], recipes=[r['id'] for r in recipes],
                     fixed_marks=sorted(fixed), roots=[0] * 24,
                     seed_keys=[[i, row, list(refs)] for i, row, refs in seeds],
                     marking_version=MARKING, fixture=False, source_bindings=compiled['source_bindings']))
    need(epoch == compiled['unchanged_model_epoch'], 'complete independent model epoch')
    state = point.State(24, recipes, fixed, [0] * 24, epoch)
    for key in seeds:
        state.apply(key, generation=0)
    full = state.semantic()
    need(canon(full) == canon(evidence['initial_graph_semantic_state']), 'every independent initial domain/mark/refcount/generation/occupancy')
    placements = [point.decorate(key, *point.points(recipes[key[0]], key[1], key[2], 24),
                                recipes, compiled['context'], compiled['authority']['epoch'],
                                compiled['formula_registry_sha256']) for key in seeds]
    need(canon(placements) == canon(evidence['initial_selected_full_placements']), 'all3full ordered occurrence identities')
    total = sum(domain['count'] for domain in full['domains'])
    need(type(evidence['complete_initial_candidate_count']) is int
         and total == evidence['complete_initial_candidate_count'], 'complete independent initial census')
    need(canon(evidence['dimensions']) == canon(compiled['dimensions']), 'complete source-derived dimensions')
    need(evidence['bodies'] == [] and evidence['groups'] == []
         and evidence['complete_pool_count'] == 0 and evidence['pool_capacity'] == 64,
         'complete empty initial library, no partial pool or RL selection claim')
    projection = dict(formula_codes=compiled['formula_codes'], formula_registry_sha256=compiled['formula_registry_sha256'],
                      definitions=[], declared_source_body_count=0,
                      status='complete_empty_initial_library_pending_independent_qualification', native_accepted=False)
    need(canon(evidence['projection']) == canon(projection), 'exact empty initial full-registry projection')
    for field in ('target_searches', 'point_certificates', 'RNG_draws', 'native_queries'):
        need(type(evidence[field]) is int and evidence[field] == 0, 'no '+field)
    for field in ('new_RL_training', 'logical_accepted', 'static_resource_qualified', 'all_five_qualification'):
        need(evidence[field] is False, 'no producer acceptance '+field)
    return dict(complete_initial_candidate_count=total, model_epoch=epoch, graph_accepted=True,
                seed_occurrences=3, complete_required_rows=24, proof_certificates=0,
                complete_pool_count=0, native_accepted=False, resource_accepted=False)
