"""SOURCE ONLY: finite ground FOL declarations, never a supplied proof word.

ROOT may invoke this library only after independent source review. Every
generated license, complete registry and boundary still needs an independent
static/context and resource gate. No search, learner or native checker is here.
The declared finite grammar is a proper fragment of the unchanged FOL language.
"""
import copy
import hashlib
import json

VERSION = 'fresh-ground-cluster-context-declaration-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def term_names(term):
    if term[0] == 'var':
        return {term[1]}
    return set().union(*(term_names(t) for t in term[2]))


def free(formula):
    head = formula[0]
    if head == 'all':
        return free(formula[2]) - {formula[1]}
    if head in ('imp', 'and', 'or'):
        return free(formula[1]) | free(formula[2])
    if head == 'not':
        return free(formula[1])
    if head == 'bot':
        return set()
    terms = formula[2] if head == 'pred' else formula[1:]
    return set().union(*(term_names(t) for t in terms))


def substitute_term(term, variable, replacement):
    if term[0] == 'var':
        return copy.deepcopy(replacement if term[1] == variable else term)
    return ['fun', term[1], [substitute_term(t, variable, replacement) for t in term[2]]]


def substitute(formula, variable, replacement):
    """Only closed replacement terms enter this finite grammar."""
    if term_names(replacement):
        raise ValueError('closed substitution terms only; no capture shortcut')
    head = formula[0]
    if head == 'all':
        return copy.deepcopy(formula) if formula[1] == variable else [
            'all', formula[1], substitute(formula[2], variable, replacement)]
    if head == 'pred':
        return ['pred', formula[1], [substitute_term(t, variable, replacement) for t in formula[2]]]
    if head == 'eq':
        return ['eq', *(substitute_term(t, variable, replacement) for t in formula[1:])]
    if head in ('imp', 'and', 'or', 'not'):
        return [head, *(substitute(f, variable, replacement) for f in formula[1:])]
    return copy.deepcopy(formula)


def validate(theory, formula):
    def term(t):
        if type(t) is not list:
            raise ValueError('literal AST list required')
        if len(t) == 2 and t[0] == 'var' and type(t[1]) is str:
            return
        if (len(t) != 3 or t[0] != 'fun' or type(t[1]) is not str
                or type(t[2]) is not list or theory['functions'].get(t[1]) != len(t[2])):
            raise ValueError('declared function/arity required')
        for t0 in t[2]:
            term(t0)
    def visit(a):
        if type(a) is not list or not a:
            raise ValueError('literal formula AST required')
        head = a[0]
        if head == 'bot' and len(a) == 1:
            return
        if head == 'eq' and len(a) == 3:
            term(a[1]); term(a[2]); return
        if (head == 'pred' and len(a) == 3 and type(a[1]) is str
                and type(a[2]) is list and theory['predicates'].get(a[1]) == len(a[2])):
            for t0 in a[2]:
                term(t0)
            return
        if head == 'all' and len(a) == 3 and type(a[1]) is str:
            visit(a[2]); return
        if ((head in ('imp', 'and', 'or') and len(a) == 3)
                or (head == 'not' and len(a) == 2)):
            for f in a[1:]:
                visit(f)
            return
        raise ValueError('formula constructor/arity outside fixed FOL language')
    visit(formula)


def select_case(fixture, instance_id):
    if (fixture.get('schema') != 'fresh-ground-theorem-fixtures-v1'
            or fixture.get('source_only') is not True
            or fixture.get('execution_authorized') is not False):
        raise ValueError('exact source-only declaration fixture required')
    matches = [c for c in fixture['cases'] if c['id'] == instance_id]
    if len(matches) != 1:
        raise ValueError('one declared fresh instance only')
    case = copy.deepcopy(matches[0]); theory = copy.deepcopy(fixture['theories'][case['theory']])
    formulas = fixture['literal_formulas']
    premises = [copy.deepcopy(formulas[name]) for name in case['hypotheses']]
    target = copy.deepcopy(formulas[case['target']])
    if case['rows'] != 24 or len(premises) != 3:
        raise ValueError('all24 rows and three ordered occurrences retained')
    for formula in [*theory['axioms'].values(), *premises, target]:
        validate(theory, formula)
        if free(formula):
            raise ValueError('closed theory, premise and target formulas only')
    return {'instance_id': instance_id, 'split': case['split'], 'theory_key': case['theory'],
            'theory': theory, 'ordered_hypotheses': premises, 'target': target, 'rows': 24,
            'structural_tag': case['structural_tag']}


def compile_declaration(fixture, instance_id, source_bindings):
    """Complete declared catalog, not a model, target route or proof certificate.

    Each theory's syntactic vocabulary includes every train/evaluation statement
    before outcomes. Four simultaneous universal-instantiation rounds; equality
    schemes are one nonrecursive layer. All finite recipes are retained.
    """
    selected = select_case(fixture, instance_id); theory = selected['theory']
    grammar = fixture['finite_grammars'][selected['theory_key']]
    if grammar['instantiation_rounds'] != 4 or grammar['equality_layers'] != 1:
        raise ValueError('exact prospective finite grammar required')
    seeds = list(theory['axioms'].values()); names = set(); terms = {}; fs = {}
    for case in fixture['cases']:
        if case['theory'] == selected['theory_key']:
            context = select_case(fixture, case['id'])
            seeds.extend(context['ordered_hypotheses']); seeds.append(context['target'])
    def collect_term(t):
        if t[0] == 'var':
            names.add(t[1])
        else:
            if not term_names(t):
                terms[canonical(t)] = copy.deepcopy(t)
            for sub in t[2]:
                collect_term(sub)
    def add_formula(f):
        fs[canonical(f)] = copy.deepcopy(f)
        if f[0] == 'all':
            names.add(f[1]); add_formula(f[2])
        elif f[0] in ('imp', 'and', 'or', 'not'):
            for sub in f[1:]:
                add_formula(sub)
        elif f[0] in ('eq', 'pred'):
            for t in f[2] if f[0] == 'pred' else f[1:]:
                collect_term(t)
    for f in seeds:
        add_formula(f)
    # Freeze term pools before instantiation. No generated term or evaluation
    # outcome can expand the declared universe recursively.
    seed_terms = [terms[k] for k in sorted(terms)]
    def numeral(t):
        return (t == ['fun', 'zero', []] or t[0] == 'fun' and t[1] == 'succ'
                and len(t[2]) == 1 and numeral(t[2][0]))
    pools = {}
    for role, definition in sorted(grammar['term_roles'].items()):
        if definition == 'all_closed_seed_subterms':
            pools[role] = copy.deepcopy(seed_terms)
        elif definition == 'closed_seed_numerals':
            pools[role] = [copy.deepcopy(t) for t in seed_terms if numeral(t)]
        elif type(definition) is list:
            pools[role] = [copy.deepcopy(t) for t in seed_terms
                           if t[0] == 'fun' and not t[2] and t[1] in definition]
            if {t[1] for t in pools[role]} != set(definition):
                raise ValueError('complete declared parameter pool absent from seed terms')
        else:
            raise ValueError('unknown syntactic term role')
    binder_roles = grammar['binder_roles']; schemes = {}; rounds = []
    for round_index in range(4):
        before = len(schemes); universals = [fs[k] for k in sorted(fs) if fs[k][0] == 'all']
        for universal in universals:
            if universal[1] not in binder_roles:
                raise ValueError('undeclared finite binder role')
            for t in pools[binder_roles[universal[1]]]:
                formula = ['imp', universal, substitute(universal[2], universal[1], t)]
                command = {'rule': 'instantiate', 'formula': formula, 'universal': universal, 'term': t}
                schemes[canonical(command)] = command; add_formula(formula)
        rounds.append({'round': round_index, 'universal_count': len(universals),
                       'new_distinct_schemes': len(schemes) - before, 'scheme_count': len(schemes),
                       'formula_count': len(fs)})
    variable = 'hole0'; suffix = 0
    while variable in names:
        suffix += 1; variable = 'hole' + str(suffix)
    def replace(t, old):
        if t == old:
            return ['var', variable]
        if t[0] == 'var':
            return copy.deepcopy(t)
        return ['fun', t[1], [replace(sub, old) for sub in t[2]]]
    def contains(t, old):
        return t == old or t[0] == 'fun' and any(contains(sub, old) for sub in t[2])
    # Exact grammar: closed atomic subformulas after the four rounds, every
    # distinct closed subterm of that atom, all-occurrence abstraction, and
    # every ordered closed equality pair already in that formula registry.
    atoms = [copy.deepcopy(fs[k]) for k in sorted(fs) if fs[k][0] in ('eq', 'pred') and not free(fs[k])]
    pairs = {}; templates = {}
    for atom in atoms:
        if atom[0] == 'eq':
            pairs[canonical(atom[1:])] = copy.deepcopy(atom[1:])
        local_terms = {}
        def local(t):
            if not term_names(t):
                local_terms[canonical(t)] = t
            if t[0] == 'fun':
                for sub in t[2]:
                    local(sub)
        args = atom[2] if atom[0] == 'pred' else atom[1:]
        for t in args:
            local(t)
        for old in (local_terms[k] for k in sorted(local_terms)):
            if not any(contains(t, old) for t in args):
                raise ValueError('template abstraction must change an actual subterm')
            template = (['pred', atom[1], [replace(t, old) for t in args]] if atom[0] == 'pred'
                        else ['eq', *(replace(t, old) for t in args)])
            templates[canonical(template)] = template
    before_equality = len(schemes)
    for tk in sorted(templates):
        template = templates[tk]
        for pk in sorted(pairs):
            left, right = pairs[pk]
            formula = ['imp', ['eq', left, right], ['imp',
                       substitute(template, variable, left), substitute(template, variable, right)]]
            command = {'rule': 'eq_subst', 'formula': formula, 'variable': variable,
                       'template': template, 'left': left, 'right': right}
            schemes[canonical(command)] = command; add_formula(formula)
    formulas = [fs[k] for k in sorted(fs)]; codes = {canonical(f): i for i, f in enumerate(formulas)}
    registry = digest(formulas); context = {'theory': theory,
                                          'ordered_local_premises': selected['ordered_hypotheses']}
    context_id = digest(context)
    authority = {'activated': False, 'native_accepted': False,
                 'recipient_theory_sha256': digest(theory), 'declaration_schema': VERSION,
                 'finite_grammar_sha256': digest(grammar), 'source_bindings': copy.deepcopy(source_bindings),
                 'logical_qualification': 'pending independent complete witness/context gate'}
    authority['epoch'] = digest(authority)
    raw = []
    for name, formula in sorted(theory['axioms'].items()):
        raw.append(({'rule': 'axiom', 'name': name, 'formula': formula}, []))
    raw.extend((schemes[k], []) for k in sorted(schemes))
    raw.extend(({'rule': 'mp', 'formula': f[2]}, [f[1], f]) for f in formulas if f[0] == 'imp')
    for occurrence, formula in enumerate(selected['ordered_hypotheses']):
        raw.append(({'rule': 'assumption', 'index': occurrence, 'formula': formula}, []))
    raw.sort(key=lambda item: canonical([item[0], item[1]]))
    if len({canonical([w, p]) for w, p in raw}) != len(raw):
        raise ValueError('no duplicate primitive record identities')
    recipes = []; licenses = []; assumptions = {}
    for index, (witness, premises) in enumerate(raw):
        preimage = {'recipe': {'primitive_witness': witness, 'ordered_premise_formulas': premises},
                    'primitive_authority_epoch': authority['epoch'],
                    'recipient_theory_sha256': authority['recipient_theory_sha256'],
                    'marking_version': MARKING, 'formula_registry_sha256': registry}
        if witness['rule'] == 'assumption':
            preimage['local_context_id'] = context_id; assumptions[witness['index']] = index
        recipe = {'id': 'primitive-recipe-' + digest(preimage),
                  'primitive_witness': copy.deepcopy(witness),
                  'ordered_premise_formulas': copy.deepcopy(premises), 'identity_preimage': preimage}
        recipes.append(recipe)
        licenses.append({'recipe_index': index, 'recipe_id': recipe['id'], 'rule': witness['rule'],
                         'record_sha256': digest(recipe), 'logical_accepted': False,
                         'native_accepted': False, 'status': 'pending independent exact primitive license'})
    if set(assumptions) != {0, 1, 2}:
        raise ValueError('three exact distinct occurrence identities required')
    target_code = codes[canonical(selected['target'])]
    boundary = {'required': [[0, r] for r in range(24)],
                'root_generations': [[0, r, 0] for r in range(24)],
                'fixed_exterior_m': [[1, r, -1] for r in range(-23, 0)],
                'fixed_target_m': [[1, 23, target_code]],
                'fixed_initial_local_seeds': [{'recipe_id': recipes[assumptions[r]]['id'],
                    'row': r, 'generation': 0} for r in range(3)],
                'all_root_obligations_generation_zero': True}
    return {'schema': VERSION, 'status': 'complete_declared_catalog_pending_independent_qualification',
            'instance_id': instance_id, 'split': selected['split'], 'height': 24,
            'context': context, 'context_id': context_id, 'target': selected['target'],
            'formula_codes': formulas, 'formula_registry_sha256': registry,
            'recipes': recipes, 'recipe_licenses': licenses, 'authority': authority,
            'assumption_recipe_indices': [assumptions[r] for r in range(3)],
            'hypothesis_codes': [codes[canonical(f)] for f in selected['ordered_hypotheses']],
            'target_code': target_code, 'boundary': boundary, 'orientation': 'identity',
            'marking_version': MARKING, 'source_bindings': copy.deepcopy(source_bindings),
            'declaration_binding': {'fixture_sha256': digest(fixture), 'selected_sha256': digest(selected),
                                    'grammar_sha256': digest(grammar), 'theory_key': selected['theory_key']},
            'syntax_census': {'seed_terms': seed_terms, 'term_pools': pools, 'instantiation_rounds': rounds,
                             'template_variable': variable, 'closed_atomic_source_count': len(atoms),
                             'equality_pairs': [pairs[k] for k in sorted(pairs)],
                             'atomic_templates': [templates[k] for k in sorted(templates)],
                             'equality_scheme_count': len(schemes) - before_equality},
            'dimensions': {'logical_rows': 24, 'formula_count': len(formulas),
                           'primitive_license_count': len(recipes),
                           'non_assumption_witness_count': len(recipes) - 3,
                           'source_body_count': 0},
            'bodies': [], 'complete_cluster_inventory': [], 'target_searches': 0,
            'proof_certificates': 0, 'RNG_draws': 0, 'new_RL_training': False,
            'all_five_qualification': False, 'native_accepted': False,
            'scope': 'Fresh proper finite ground FOL grammar; complete declared syntax only. '
                     'Full theory/schema data retained; induction/generalization/tautology/reflexivity '
                     'commands outside this initial grammar. Empty initial cluster library, not learned reuse.'}
