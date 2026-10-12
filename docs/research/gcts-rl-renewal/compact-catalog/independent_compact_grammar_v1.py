"""SOURCE ONLY: independent complete original grammar with shared immutable ASTs.

No compiler/decoder/graph/search/policy imports or calls. ROOT alone may supply
the separately pinned independent GroundChecker for a future owned static audit.
This module preserves the original canonical formula and primitive order and
hash preimages. It does not construct a proof, search, or accept resources.
"""
import hashlib
import json

DECLARATION = 'fresh-ground-cluster-context-declaration-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'


def need(condition, label):
    if not condition:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def thaw(value):
    """Only one current logical record is expanded, never the entire catalog."""
    return [thaw(v) for v in value] if type(value) is tuple else value


class Arena:
    """Independent structural tuple interning; no producer node IDs are used."""
    def __init__(self):
        self.values = {}

    def intern(self, value):
        if type(value) in (tuple, list):
            key = tuple(self.intern(v) for v in value)
            return self.values.setdefault(key, key)
        need(type(value) in (str, int) and type(value) is not bool,
             'exact AST/name/finite integer only')
        return value

    def node(self, *items):
        # Children were already interned by the closed constructors. Rewalking
        # their entire shared subtrees would create unnecessary temporary
        # tuples at every equality pair; only this new parent is interned.
        key = tuple(items)
        return self.values.setdefault(key, key)


def free(value, bound=frozenset()):
    tag = value[0]
    if tag == 'var':
        return set() if value[1] in bound else {value[1]}
    if tag in ('fun', 'pred'):
        return set().union(*(free(v, bound) for v in value[2]))
    if tag == 'all':
        return free(value[2], bound | {value[1]})
    return set().union(*(free(v, bound) for v in value[1:]))


def formulas(value):
    yield value
    if value[0] == 'all':
        yield from formulas(value[2])
    elif value[0] in ('not', 'imp', 'and', 'or'):
        for child in value[1:]:
            yield from formulas(child)


def terms(value):
    yield value
    if value[0] == 'fun':
        for child in value[2]:
            yield from terms(child)


def atom_terms(value):
    if value[0] in ('eq', 'pred'):
        for term in value[2] if value[0] == 'pred' else value[1:]:
            yield from terms(term)


class CompleteGrammar:
    """Complete original finite catalog, independently regenerated from fixture.

    Tuple sharing removes repeated nested list copies. Sorting temporarily holds
    original canonical strings; no fitting-under-budget promise follows from the
    source. Every cutoff/exception in the future owned worker remains UNKNOWN.
    """
    def __init__(self, fixture, instance_id, source_bindings, checker_class):
        need(fixture['schema'] == 'fresh-ground-theorem-fixtures-v1'
             and fixture['source_only'] is True
             and fixture['execution_authorized'] is False, 'literal frozen fixture')
        cases = [c for c in fixture['cases'] if c['id'] == instance_id]
        need(len(cases) == 1, 'one exact declared selector')
        case = cases[0]
        need(case['rows'] == 24 and len(case['hypotheses']) == 3,
             '24 rows and three ordered hypothesis occurrences')
        self.arena = arena = Arena()
        self.theory = fixture['theories'][case['theory']]
        self.theory_sha = digest(self.theory)
        self.checker = checker_class(self.theory)
        self.gamma = [fixture['literal_formulas'][k] for k in case['hypotheses']]
        self.target = fixture['literal_formulas'][case['target']]
        self.instance_id, self.split = instance_id, case['split']
        grammar = fixture['finite_grammars'][case['theory']]
        need(grammar['instantiation_rounds'] == 4 and grammar['equality_layers'] == 1,
             'original four simultaneous rounds and one equality layer')
        known, frozen_terms, names = set(), set(), set()
        seed_formulas = list(self.theory['axioms'].values())
        for other in fixture['cases']:
            if other['theory'] == case['theory']:
                seed_formulas += [fixture['literal_formulas'][k] for k in other['hypotheses']]
                seed_formulas.append(fixture['literal_formulas'][other['target']])
        for raw in seed_formulas:
            self.checker.formula(raw)
            value = arena.intern(raw)
            need(not free(value), 'original closed theory/Gamma/target seeds')
            for part in formulas(value):
                known.add(part)
                if part[0] == 'all':
                    names.add(part[1])
                for term in atom_terms(part):
                    if term[0] == 'var':
                        names.add(term[1])
                    if not free(term):
                        frozen_terms.add(term)
        self.seed_terms = tuple(sorted(frozen_terms, key=canonical))

        def numeral(term):
            while term[0] == 'fun' and term[1] == 'succ' and len(term[2]) == 1:
                term = term[2][0]
            return term == ('fun', 'zero', ())

        pools = {}
        for role, spec in sorted(grammar['term_roles'].items()):
            if spec == 'all_closed_seed_subterms':
                pool = self.seed_terms
            elif spec == 'closed_seed_numerals':
                pool = tuple(t for t in self.seed_terms if numeral(t))
            else:
                need(type(spec) is list, 'frozen role declaration')
                pool = tuple(t for t in self.seed_terms if t[0] == 'fun'
                             and not t[2] and t[1] in spec)
                need({t[1] for t in pool} == set(spec), 'complete named role pool')
            pools[role] = pool
        self.term_pools = pools

        def replace(value, variable, term):
            if value[0] == 'var':
                return term if value[1] == variable else value
            if value[0] in ('fun', 'pred'):
                return arena.node(value[0], value[1],
                                  tuple(replace(v, variable, term) for v in value[2]))
            if value[0] == 'all':
                return value if value[1] == variable else arena.node(
                    'all', value[1], replace(value[2], variable, term))
            return arena.node(value[0], *(replace(v, variable, term) for v in value[1:]))

        schemes, rounds = set(), []
        for number in range(4):
            snapshot = sorted((f for f in known if f[0] == 'all'), key=canonical)
            before = len(schemes)
            for universal in snapshot:
                need(universal[1] in grammar['binder_roles'], 'every frozen binder role')
                for term in pools[grammar['binder_roles'][universal[1]]]:
                    output = arena.node('imp', universal,
                                        replace(universal[2], universal[1], term))
                    schemes.add(('instantiate', output, universal, term))
                    known.update(formulas(output))
            rounds.append(dict(round=number, universal_count=len(snapshot),
                               new_distinct_schemes=len(schemes)-before,
                               scheme_count=len(schemes), formula_count=len(known)))
        hole = next('hole'+str(i) for i in range(len(names)+1)
                    if 'hole'+str(i) not in names)
        atoms = sorted((f for f in known if f[0] in ('eq', 'pred') and not free(f)),
                       key=canonical)
        pairs = sorted({f[1:] for f in atoms if f[0] == 'eq'}, key=canonical)
        templates = set()

        def abstract(term, old):
            if term == old:
                return arena.node('var', hole)
            if term[0] == 'fun':
                return arena.node('fun', term[1], tuple(abstract(t, old) for t in term[2]))
            return term

        for atom in atoms:
            args = atom[2] if atom[0] == 'pred' else atom[1:]
            local = {t for t in atom_terms(atom) if not free(t)}
            for old in sorted(local, key=canonical):
                changed = tuple(abstract(t, old) for t in args)
                template = arena.node('pred', atom[1], changed) if atom[0] == 'pred' \
                    else arena.node('eq', *changed)
                need(template != atom, 'all-occurrence abstraction changes an actual subterm')
                templates.add(template)
        templates = tuple(sorted(templates, key=canonical))
        before = len(schemes)
        for template in templates:
            for left, right in pairs:
                output = arena.node('imp', arena.node('eq', left, right),
                    arena.node('imp', replace(template, hole, left), replace(template, hole, right)))
                schemes.add(('eq_subst', output, hole, template, left, right))
                known.update(formulas(output))
        self.formulas = tuple(sorted(known, key=canonical))
        self.codes = {f:i for i,f in enumerate(self.formulas)}
        self.registry_sha = self.registry_hash()
        records = set(schemes)
        records.update(('axiom', arena.intern(f), n) for n,f in self.theory['axioms'].items())
        records.update(('mp', f[2], f[1], f) for f in self.formulas if f[0] == 'imp')
        records.update(('assumption', arena.intern(f), i) for i,f in enumerate(self.gamma))
        self.records = tuple(sorted(records, key=lambda r:canonical(self.witness_and_premises(r))))
        need(len(self.records) == len(schemes)+len(self.theory['axioms'])
             +sum(f[0]=='imp' for f in self.formulas)+3, 'complete distinct primitive inventory')
        self.context = dict(theory=self.theory, ordered_local_premises=self.gamma)
        self.context_id = digest(self.context)
        self.source_bindings = source_bindings
        self.authority = dict(activated=False,native_accepted=False,
            recipient_theory_sha256=self.theory_sha,declaration_schema=DECLARATION,
            finite_grammar_sha256=digest(grammar),source_bindings=source_bindings,
            logical_qualification='pending independent complete witness/context gate')
        self.authority['epoch'] = digest(self.authority)
        selected = dict(instance_id=instance_id,split=case['split'],theory_key=case['theory'],
                        theory=self.theory,ordered_hypotheses=self.gamma,target=self.target,
                        rows=24,structural_tag=case['structural_tag'])
        self.declaration_binding = dict(fixture_sha256=digest(fixture),selected_sha256=digest(selected),
            grammar_sha256=digest(grammar),theory_key=case['theory'])
        self.syntax_census = dict(seed_terms=self.seed_terms,term_pools=pools,
            instantiation_rounds=rounds,template_variable=hole,closed_atomic_source_count=len(atoms),
            equality_pairs=pairs,atomic_templates=templates,equality_scheme_count=len(schemes)-before)
        self.dimensions = dict(logical_rows=24,formula_count=len(self.formulas),
            primitive_license_count=len(self.records),non_assumption_witness_count=len(self.records)-3,
            source_body_count=0)
        self.assumptions = [next(i for i,r in enumerate(self.records)
                                if r[0]=='assumption' and r[2]==occurrence) for occurrence in range(3)]
        self.target_code = self.codes[arena.intern(self.target)]

    def registry_hash(self):
        h = hashlib.sha256(); h.update(b'[')
        for i,formula in enumerate(self.formulas):
            if i: h.update(b',')
            h.update(canonical(formula).encode('utf8'))
        h.update(b']'); return h.hexdigest()

    def witness_and_premises(self, record):
        rule,output = record[:2]
        command = dict(rule=rule,formula=output); premises=[]
        if rule=='axiom': command['name']=record[2]
        elif rule=='assumption': command['index']=record[2]
        elif rule=='instantiate': command.update(universal=record[2],term=record[3])
        elif rule=='eq_subst':
            command.update(variable=record[2],template=record[3],left=record[4],right=record[5])
        else:
            need(rule=='mp','five original primitive rules only'); premises=[record[2],record[3]]
        return [command,premises]

    def recipe(self, index, logical_check=True):
        record=self.records[index]; witness,premises=self.witness_and_premises(record)
        if logical_check:
            command={k:thaw(v) for k,v in witness.items()}
            if premises: command.update(antecedent=0,implication=1)
            self.checker.command(command,[thaw(p) for p in premises],self.gamma)
        preimage=dict(recipe=dict(primitive_witness=witness,ordered_premise_formulas=premises),
            primitive_authority_epoch=self.authority['epoch'],recipient_theory_sha256=self.theory_sha,
            marking_version=MARKING,formula_registry_sha256=self.registry_sha)
        if record[0]=='assumption': preimage['local_context_id']=self.context_id
        identifier='primitive-recipe-'+digest(preimage)
        recipe=dict(id=identifier,primitive_witness=witness,ordered_premise_formulas=premises,
                    identity_preimage=preimage)
        return recipe,digest(recipe),self.codes[record[1]],tuple(self.codes[p] for p in premises)
