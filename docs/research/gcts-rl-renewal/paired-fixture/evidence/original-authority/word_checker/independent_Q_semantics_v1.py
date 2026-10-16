"""Independent SOURCE-only six-rule checker and complete finite-Q auditor.

No producer/project imports. ROOT alone may activate this source after peer
review and an exact cold raw-byte wrapper. Counts are reconstructed, not supplied
acceptance constants. Catalogue admission, a checked primitive word, physical
point state, native/full-board/trajectory acceptance are different scopes.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import time
import types

VERSION = 'independent-complete-finite-Q-semantics-v1'
PRODUCER_PROFILE = 'arithmetic-empty-Gamma-unary-generalize-finite-catalog-v1'
MARKING = 'injective-formula-ordered-primitive-offset-Q-v1'
DECLARATION_RAW_SHA256 = 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'
DECLARATION_VALUE_SHA256 = 'f6ca72af011a9343f4661b5092d54565f668a978fd020734072267b76f89b7a3'
GRAMMAR = {'term_node_bound': 3, 'target_and_axiom_open_subterms': True,
    'instantiation_rounds': 2, 'hole_context_node_bound': 2,
    'equality_template_other_terms': 'complete_operand_pool',
    'equality_operand_pairs': 'all_ordered_pairs',
    'generalization_sources': 'all_resulting_parameter_scoped_equality_atoms',
    'target_seed_is_formula_only': True}
LIMITS = {'maximum_formulas': 50000, 'maximum_recipes': 20000, 'maximum_visits': 5000000}
FROZEN_PRODUCER_BINDINGS = {'catalogue': {'bytes': 10187, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_catalog_v1.py', 'sha256': '2db11af0d7206afd4e1c10b53b97c16f98064c14fd1e57a9a2ca34c0a602348a'}, 'controls': {'bytes': 19742, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_v3.py', 'sha256': '4e28fadd9c76ba6664e485fa2c5aa97beaa08639986b6d56aae50395b006e638'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'master': {'bytes': 21657, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md', 'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}, 'payload': {'bytes': 5435, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/q_preparation_owned_graph_v3.py', 'sha256': 'ee2088bf60709f6c0c5a78297841bd0684674369fa9d3c08119b96a59caa88ad'}, 'point_graph': {'bytes': 28531, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py', 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'}, 'worker': {'bytes': 37266, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_worker_v7.py', 'sha256': '75d5d80701a0815d78e182a5cb7eb99412bff5b48a5b936a8850b625743de48d'}}
RULE_FIELDS = {'axiom': {'name'}, 'assumption': {'index'},
    'instantiate': {'universal', 'term'},
    'eq_subst': {'variable', 'template', 'left', 'right'},
    'mp': {'antecedent', 'implication'}, 'generalize': {'variable', 'source'}}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value):
    need(type(value) is int, 'literal integer; a Boolean is not an index/code')
    return value


def symbol(value):
    need(type(value) is str and value and len(value.encode('utf8')) <= 64,
         'bounded nonempty variable/symbol')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def callback_state(function):
    need(type(function) is types.FunctionType, 'exact cold caller source-guard function')
    return (function, function.__code__, id(function.__defaults__),
            tuple(id(v) for v in function.__defaults__ or ()), id(function.__kwdefaults__),
            tuple((k, id(v)) for k, v in sorted((function.__kwdefaults__ or {}).items())),
            tuple((id(cell), id(cell.cell_contents)) for cell in function.__closure__ or ()))


class Unresolved(TimeoutError):
    """Complete audit/check did not resolve inside the declared finite limits."""


class Boundary:
    """Original callback/code authority plus one shared finite inner deadline.

    Outer cold worker must also raw-bind this whole module, every actual method
    and its own loaders/guards. This callable cannot issue ROOT resource custody.
    """
    def __init__(self, source_guard, deadline, maximum_visits=5000000):
        need(type(deadline) in (int, float) and math.isfinite(deadline), 'finite absolute deadline')
        need(type(maximum_visits) is int and 0 < maximum_visits <= 5000000, 'unchanged visit ceiling')
        self.deadline, self.maximum_visits, self.visits = deadline, maximum_visits, 0
        self.guard = source_guard
        self._callback_state = callback_state
        self._state_code = callback_state.__code__
        self._need, self._need_code = need, need.__code__
        self._clock = time.perf_counter
        self.anchor = callback_state(source_guard)
        self.check()

    def check(self):
        # Direct rejection precedes every delegated validator invocation.
        if callback_state is not self._callback_state or callback_state.__code__ is not self._state_code:
            raise ValueError('own callback validator changed')
        if need is not self._need or need.__code__ is not self._need_code:
            raise ValueError('own rejection predicate changed')
        if time.perf_counter is not self._clock:
            raise ValueError('original clock endpoint changed')
        if self._callback_state(self.guard) != self.anchor:
            raise ValueError('original delegated authority/default/closure changed')
        if self._clock() >= self.deadline:
            raise Unresolved('complete independent Q work exceeded its deadline')
        self.guard()
        if self._callback_state(self.guard) != self.anchor:
            raise ValueError('delegated authority changed during guard')
        if self._clock() >= self.deadline:
            raise Unresolved('complete independent Q boundary exceeded its deadline')

    def tick(self, depth=0):
        self.visits += 1
        if depth > 64 or self.visits > self.maximum_visits or self._clock() >= self.deadline:
            raise Unresolved('whole independent Q syntax/closure/domain work unfinished')
        if self.visits % 1024 == 0:
            self.check()


class Semantics:
    """Separately authored nominal AST kernel using interned immutable nodes.

    It checks all six literal primitives, not a supplied proof constructor.
    Gamma is occurrence-ordered and generalization uses every original premise.
    Equality/UI are zero-premise implication licences; only MP applies them.
    """
    def __init__(self, theory, parameters, original_Gamma, boundary):
        self.b = boundary
        need(type(theory) is dict and set(theory) == {'functions', 'predicates', 'axioms', 'schemas'},
             'complete exact original theory')
        need(theory['schemas'] == [], 'no induction or extra proof schema')
        self.signature = {}
        for kind in ('functions', 'predicates'):
            need(type(theory[kind]) is dict, 'literal signature map')
            self.signature[kind] = {}
            for name, arity in theory[kind].items():
                symbol(name); integer(arity)
                need(0 <= arity <= 4, 'bounded literal arity')
                self.signature[kind][name] = arity
        need(type(parameters) is list and len(parameters) <= 4, 'finite parameter list')
        self.parameters = tuple(symbol(p) for p in parameters)
        need(len(set(self.parameters)) == len(self.parameters), 'distinct parameters')
        self.pool, self.free_cache, self.names_cache = {}, {}, {}
        need(type(theory['axioms']) is dict and type(original_Gamma) is list, 'axioms and original Gamma')
        self.axioms = {}
        for label, raw in theory['axioms'].items():
            symbol(label)
            node = self.formula(raw)
            need(not self.free(node), 'every named original axiom closed')
            self.axioms[label] = node
        self.gamma = tuple(self.formula(raw) for raw in original_Gamma)
        self.parameter_set = frozenset(self.parameters)
        need(all(self.free(node) <= self.parameter_set for node in self.gamma), 'whole Gamma parameter scope')
        self.forbidden = frozenset().union(*(self.free(node) for node in self.gamma))
        self.b.check()

    def node(self, value):
        return self.pool.setdefault(value, value)

    def term(self, raw, depth=0):
        self.b.tick(depth)
        need(type(raw) is list and raw, 'literal term array')
        if raw[0] == 'var':
            need(len(raw) == 2, 'exact variable fields')
            return self.node(('var', symbol(raw[1])))
        need(len(raw) == 3 and raw[0] == 'fun' and type(raw[2]) is list, 'exact function fields')
        name = symbol(raw[1])
        need(name in self.signature['functions'] and len(raw[2]) == self.signature['functions'][name],
             'declared function and exact arity')
        return self.node(('fun', name, tuple(self.term(child, depth + 1) for child in raw[2])))

    def formula(self, raw, depth=0):
        self.b.tick(depth)
        need(type(raw) is list and raw and type(raw[0]) is str, 'literal formula array')
        tag = raw[0]
        if tag == 'bot':
            need(len(raw) == 1, 'bottom fields')
            value = ('bot',)
        elif tag == 'eq':
            need(len(raw) == 3, 'equality fields')
            value = ('eq', self.term(raw[1], depth + 1), self.term(raw[2], depth + 1))
        elif tag == 'pred':
            need(len(raw) == 3 and type(raw[2]) is list, 'predicate fields')
            name = symbol(raw[1])
            need(name in self.signature['predicates'] and len(raw[2]) == self.signature['predicates'][name],
                 'declared predicate and exact arity')
            value = ('pred', name, tuple(self.term(child, depth + 1) for child in raw[2]))
        elif tag == 'all':
            need(len(raw) == 3, 'universal fields')
            value = ('all', symbol(raw[1]), self.formula(raw[2], depth + 1))
        else:
            need((tag == 'not' and len(raw) == 2) or (tag in ('imp', 'and', 'or') and len(raw) == 3),
                 'known connective/arity only')
            value = (tag,) + tuple(self.formula(child, depth + 1) for child in raw[1:])
        return self.node(value)

    def term_names(self, node):
        self.b.tick()
        if node not in self.names_cache:
            if node[0] == 'var':
                names = frozenset((node[1],))
            else:
                names = frozenset().union(*(self.term_names(child) for child in node[2]))
            self.names_cache[node] = names
        return self.names_cache[node]

    def free(self, node):
        self.b.tick()
        if node not in self.free_cache:
            tag = node[0]
            if tag == 'all':
                names = self.free(node[2]) - {node[1]}
            elif tag == 'eq':
                names = self.term_names(node[1]) | self.term_names(node[2])
            elif tag == 'pred':
                names = frozenset().union(*(self.term_names(t) for t in node[2]))
            elif tag == 'bot':
                names = frozenset()
            else:
                names = frozenset().union(*(self.free(child) for child in node[1:]))
            self.free_cache[node] = names
        return self.free_cache[node]

    def all_names(self, node):
        self.b.tick()
        tag = node[0]
        if tag == 'all':
            return self.all_names(node[2]) | {node[1]}
        if tag == 'eq':
            return self.term_names(node[1]) | self.term_names(node[2])
        if tag == 'pred':
            return frozenset().union(*(self.term_names(t) for t in node[2]))
        if tag == 'bot':
            return frozenset()
        return frozenset().union(*(self.all_names(child) for child in node[1:]))

    def term_replace(self, term, variable, replacement):
        self.b.tick()
        if term[0] == 'var':
            return replacement if term[1] == variable else term
        return self.node(('fun', term[1], tuple(self.term_replace(t, variable, replacement) for t in term[2])))

    def substitute(self, formula, variable, replacement):
        """Capture avoidance with the exact declared literal fresh-name policy.

        Inner binders of the same name stop free renaming. No alpha-equivalence
        quotient, hidden sort, fresh-name truncation or strengthened rule.
        """
        self.b.tick()
        tag = formula[0]
        if tag == 'all':
            binder, body = formula[1], formula[2]
            if binder == variable or variable not in self.free(body):
                return formula
            if binder in self.term_names(replacement):
                used = self.all_names(body) | self.term_names(replacement) | {variable, binder}
                for suffix in range(32):
                    self.b.tick()
                    fresh = 'fresh' + str(suffix)
                    if fresh not in used:
                        break
                else:
                    raise Unresolved('complete capture-safe fresh namespace unresolved')
                body = self.substitute(body, binder, self.node(('var', fresh)))
                binder = fresh
            return self.node(('all', binder, self.substitute(body, variable, replacement)))
        if tag == 'eq':
            return self.node(('eq', self.term_replace(formula[1], variable, replacement),
                              self.term_replace(formula[2], variable, replacement)))
        if tag == 'pred':
            return self.node(('pred', formula[1], tuple(self.term_replace(t, variable, replacement) for t in formula[2])))
        if tag == 'bot':
            return formula
        return self.node((tag,) + tuple(self.substitute(f, variable, replacement) for f in formula[1:]))

    def command(self, raw, prior):
        self.b.tick()
        need(type(raw) is dict and raw.get('rule') in RULE_FIELDS, 'declared six primitive rules only')
        rule = raw['rule']
        need(set(raw) == {'rule', 'formula'} | RULE_FIELDS[rule], 'exact primitive command fields')
        out = self.formula(raw['formula'])
        need(self.free(out) <= self.parameter_set, 'only declared free output parameters')
        def previous(index):
            integer(index)
            need(0 <= index < len(prior), 'strict-prior ordered reference')
            return prior[index]
        if rule == 'axiom':
            need(self.axioms.get(symbol(raw['name'])) == out, 'exact named original axiom')
        elif rule == 'assumption':
            index = integer(raw['index'])
            need(0 <= index < len(self.gamma) and self.gamma[index] == out, 'original indexed Gamma occurrence')
        elif rule == 'instantiate':
            universal, replacement = self.formula(raw['universal']), self.term(raw['term'])
            need(universal[0] == 'all' and self.free(universal) <= self.parameter_set
                 and self.term_names(replacement) <= self.parameter_set, 'open-parameter universal instance scope')
            expected = self.node(('imp', universal, self.substitute(universal[2], universal[1], replacement)))
            need(out == expected, 'exact capture-safe universal-instantiation implication')
        elif rule == 'eq_subst':
            variable = symbol(raw['variable'])
            template = self.formula(raw['template'])
            left, right = self.term(raw['left']), self.term(raw['right'])
            need(variable not in self.parameter_set and template[0] in ('eq', 'pred')
                 and self.free(template) <= self.parameter_set | {variable}
                 and self.term_names(left) <= self.parameter_set and self.term_names(right) <= self.parameter_set,
                 'atomic equality hole and declared open operand scope')
            expected = self.node(('imp', self.node(('eq', left, right)),
                self.node(('imp', self.substitute(template, variable, left), self.substitute(template, variable, right)))))
            need(out == expected, 'exact atomic equality-substitution implication')
        elif rule == 'mp':
            antecedent, implication = previous(raw['antecedent']), previous(raw['implication'])
            need(implication == ('imp', antecedent, out), 'ordered literal modus ponens')
        else:
            variable = symbol(raw['variable'])
            need(variable in self.parameter_set and variable not in self.forbidden,
                 'generalization fresh for every original undischarged Gamma occurrence')
            need(out == ('all', variable, previous(raw['source'])), 'genuine unary universal introduction')
        return out

    def recipe(self, witness, premises):
        need(type(witness) is dict and type(premises) is list, 'raw primitive recipe and ordered premise ports')
        rule = witness.get('rule')
        refs = {'mp': {'antecedent', 'implication'}, 'generalize': {'source'}}.get(rule, set())
        need(rule in RULE_FIELDS and set(witness) == {'rule', 'formula'} | (RULE_FIELDS[rule] - refs),
             'recipe witness has no physical prior-row reference')
        expected_arity = 2 if rule == 'mp' else 1 if rule == 'generalize' else 0
        need(len(premises) == expected_arity, 'exact ordered primitive arity')
        prior = tuple(self.formula(f) for f in premises)
        command = dict(witness)
        if rule == 'mp':
            command.update(antecedent=0, implication=1)
        elif rule == 'generalize':
            command.update(source=0)
        return self.command(command, prior), prior


def check_primitive_word(*, theory, parameters, original_Gamma, commands, target, source_guard,
                         deadline, maximum_visits=5000000):
    """Complete arbitrary saved primitive word, independent of producer checker.

    This logical certificate needs no catalogue/placement planner. It creates no
    proof word and claims no native/full24/current-state/trajectory acceptance.
    Strict prior rows preserve repeated ports; full original Gamma controls UG.
    """
    began = time.perf_counter()
    b = Boundary(source_guard, deadline, maximum_visits)
    k = Semantics(theory, parameters, original_Gamma, b)
    need(type(commands) is list and commands, 'complete nonempty primitive word')
    if len(commands) > 20000:
        raise Unresolved('whole primitive word exceeds its disclosed checking ceiling')
    goal = k.formula(target)
    need(not k.free(goal), 'closed exact final target')
    prior, rows = [], []
    for row, command in enumerate(commands):
        out = k.command(command, prior)
        rule = command['rule']
        refs = [command['antecedent'], command['implication']] if rule == 'mp' else (
            [command['source']] if rule == 'generalize' else [])
        prior.append(out)
        rows.append({'row': row, 'rule': rule, 'formula_sha256': digest(out), 'ordered_prior_rows': refs})
    need(prior[-1] == goal, 'final conclusion is the exact original target')
    essential, consumed, pending = set(), set(), [len(rows) - 1]
    while pending:
        b.tick()
        row = pending.pop()
        if row in essential:
            continue
        essential.add(row); pending.extend(rows[row]['ordered_prior_rows'])
        if commands[row]['rule'] == 'assumption':
            consumed.add(commands[row]['index'])
    result = {'schema': 'independent-Q-primitive-word-certificate-v1', 'completed': True,
        'original_Gamma_target_sequent_accepted': True, 'rows': rows,
        'original_ordered_Gamma': original_Gamma, 'parameters': parameters, 'target': target,
        'theory_sha256': digest(theory), 'commands_sha256': digest(commands),
        'essential_rows': sorted(essential),
        'consumed_original_occurrence_indices': sorted(consumed),
        'native_accepted': False, 'full24_accepted': False, 'current_state_point_union_accepted': False,
        'full_trajectory_accepted': False, 'induction_accepted': False, 'full_PA_accepted': False,
        'universal_compiler_accepted': False, 'ROOT_resource_accepted': False}
    canonical(result); b.check()
    result['visits'] = b.visits; result['elapsed_seconds_before_final_guard'] = time.perf_counter() - began
    canonical(result); b.check()
    return result


def formula_nodes(node):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        tag = current[0]
        if tag == 'all':
            stack.append(current[2])
        elif tag in ('not', 'imp', 'and', 'or'):
            stack.extend(reversed(current[1:]))


def term_nodes(node):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        if current[0] == 'fun':
            stack.extend(reversed(current[2]))


def term_size(node):
    return sum(1 for _ in term_nodes(node))


def reconstruct_grammar(k, declaration):
    """Complete language reconstruction from the frozen finite specification.

    A monotone structural term pool, immutable DAG formula registry and raw
    recipe-key set differ from the producer's copied-layer/host-kernel path.
    Counts are derived after closure; no observed count or target backcone gate.
    """
    b = k.b
    need(declaration['grammar'] == GRAMMAR and declaration['limits'] == LIMITS,
         'entire frozen finite grammar and ceilings, no favorable trims')
    need(declaration['ordered_Gamma'] == [] and declaration['height'] == 24
         and len(k.parameters) == 1 and k.signature['predicates'] == {}, 'same empty-Gamma Q calibration profile')
    target = k.formula(declaration['target'])
    need(not k.free(target), 'closed declared target syntax only')
    operands = {k.node(('var', name)) for name in k.parameters}
    operands.update(k.node(('fun', name, ())) for name, arity in k.signature['functions'].items() if arity == 0)
    # Complete least structural closure up to the stated term-node size.
    for _ in range(GRAMMAR['term_node_bound']):
        snapshot = tuple(operands)
        additions = set()
        for name, arity in sorted(k.signature['functions'].items()):
            if arity == 0:
                continue
            for children in itertools.product(snapshot, repeat=arity):
                b.tick()
                if 1 + sum(term_size(t) for t in children) <= GRAMMAR['term_node_bound']:
                    additions.add(k.node(('fun', name, tuple(children))))
        fresh = additions - operands
        operands.update(additions)
        if not fresh:
            break
    seed_formulas = [target, *k.axioms.values()]
    basis, raw_recipes = set(), set()
    def register(formula):
        for sub in formula_nodes(formula):
            b.tick()
            if k.free(sub) <= k.parameter_set:
                basis.add(sub)
                if len(basis) > LIMITS['maximum_formulas']:
                    raise Unresolved('complete formula closure exceeds its fixed ceiling')
    def recipe(witness, premises):
        b.tick()
        raw_recipes.add(canonical({'primitive_witness': witness, 'ordered_premise_formulas': premises}))
        if len(raw_recipes) > LIMITS['maximum_recipes']:
            raise Unresolved('complete primitive universe exceeds its fixed ceiling')
        register(witness['formula'])
    for formula in seed_formulas:
        register(formula)
        for sub in formula_nodes(formula):
            if sub[0] == 'eq':
                for side in sub[1:]:
                    for term in term_nodes(side):
                        b.tick()
                        if k.term_names(term) <= k.parameter_set:
                            operands.add(term)
    values = sorted(operands, key=canonical)
    for name, formula in sorted(k.axioms.items()):
        recipe({'rule': 'axiom', 'name': name, 'formula': formula}, [])
    rounds = []
    for round_index in range(GRAMMAR['instantiation_rounds']):
        universals = sorted((f for f in basis if f[0] == 'all'), key=canonical)
        before = len(raw_recipes)
        for universal in universals:
            for term in values:
                b.tick()
                instance = k.substitute(universal[2], universal[1], term)
                recipe({'rule': 'instantiate', 'universal': universal, 'term': term,
                        'formula': k.node(('imp', universal, instance))}, [])
        rounds.append({'round': round_index, 'universals': len(universals),
                       'new_recipes': len(raw_recipes) - before, 'recipes': len(raw_recipes)})
        b.check()
    used = set(k.parameters)
    for formula in seed_formulas:
        used.update(k.all_names(formula))
    suffix = 0
    while 'hole' + str(suffix) in used:
        b.tick(); suffix += 1
    hole = 'hole' + str(suffix)
    contexts = [k.node(('var', hole))]
    contexts.extend(k.node(('fun', name, (k.node(('var', hole)),)))
                    for name, arity in sorted(k.signature['functions'].items()) if arity == 1)
    templates = set()
    for context, other in itertools.product(contexts, values):
        templates.add(k.node(('eq', context, other))); templates.add(k.node(('eq', other, context)))
    generated = 0
    for template in sorted(templates, key=canonical):
        for left, right in itertools.product(values, repeat=2):
            b.tick()
            formula = k.node(('imp', k.node(('eq', left, right)),
                k.node(('imp', k.substitute(template, hole, left), k.substitute(template, hole, right)))))
            recipe({'rule': 'eq_subst', 'variable': hole, 'template': template,
                    'left': left, 'right': right, 'formula': formula}, [])
            generated += 1
    atoms = sorted((f for f in basis if f[0] == 'eq'), key=canonical)
    parameter = k.parameters[0]
    for atom in atoms:
        recipe({'rule': 'generalize', 'variable': parameter, 'formula': k.node(('all', parameter, atom))}, [atom])
    implications = sorted((f for f in basis if f[0] == 'imp'), key=canonical)
    for implication in implications:
        recipe({'rule': 'mp', 'formula': implication[2]}, [implication[1], implication])
    b.check()
    census = {'operands': len(values), 'hole_contexts': len(contexts), 'atomic_templates': len(templates),
        'generated_equality_schemes_before_dedup': generated, 'formulas': len(basis),
        'recipes': len(raw_recipes), 'generalization_sources': len(atoms), 'instantiation_rounds': rounds}
    return sorted(basis, key=canonical), sorted(raw_recipes), census


def parse_key(raw, primitives, height):
    need(type(raw) is list and len(raw) == 3 and type(raw[2]) is list, 'exact physical recipe/row/ordered references')
    recipe, row = integer(raw[0]), integer(raw[1])
    refs = tuple(integer(ref) for ref in raw[2])
    need(0 <= recipe < len(primitives) and 0 <= row < height, 'whole primitive/required-row universe')
    inputs = primitives[recipe][1]
    need(len(refs) == len(inputs) and all(0 <= ref < row for ref in refs), 'strict-prior physical ordered ports')
    return recipe, row, refs


def literal_points(key, primitives):
    recipe, row, refs = key
    out, inputs = primitives[recipe]
    assignments = {(1, row): out}
    for port, (ref, code) in enumerate(zip(refs, inputs)):
        point = (1, ref)
        need(point not in assignments or assignments[point] == code, 'shared source row must have one formula value')
        assignments[point] = code
        assignments[2 + port, row] = ref - row
    return [[0, row, 1]], [[x, y, value] for (x, y), value in sorted(assignments.items())]


def independent_domain(row, *, primitives, totals, marks, exclusions, b):
    """All zero/unary/binary candidates by direct point incidence relation.

    It reads no graph/domain/production-factor method. The explicit port masks
    and Cartesian count retain repeated ports while rejecting unequal shared
    assignments. No candidate is removed except literal marks or exclusions.
    """
    factors, masks = [], {}
    def port_mask(code, port):
        index = code, port
        if index not in masks:
            mask = 0
            for ref in range(row):
                b.tick()
                if (1, ref) in marks and marks[1, ref] != code:
                    continue
                if (2 + port, row) in marks and marks[2 + port, row] != ref - row:
                    continue
                mask |= 1 << ref
            masks[index] = mask
        return masks[index]
    if totals[row] == 0:
        for index, (out, inputs) in enumerate(primitives):
            b.tick()
            if (1, row) in marks and marks[1, row] != out:
                continue
            if not inputs:
                left, right, different, count = 0, 0, False, 1
            elif len(inputs) == 1:
                left, right, different = port_mask(inputs[0], 0), 0, False
                count = bin(left).count('1')
            else:
                left, right = port_mask(inputs[0], 0), port_mask(inputs[1], 1)
                different = inputs[0] != inputs[1]
                count = bin(left).count('1') * bin(right).count('1')
                if different:
                    count -= bin(left & right).count('1')
            if count:
                factors.append([index, left, right, different, count])
    by_recipe = {f[0]: f for f in factors}
    removed = []
    for key in sorted(exclusions):
        index, key_row, refs = key
        need(key_row == row, 'branch-local excluded row')
        factor = by_recipe.get(index)
        if factor is None:
            continue
        allowed = not refs or bool((factor[1] >> refs[0]) & 1)
        if len(refs) == 2:
            allowed = allowed and bool((factor[2] >> refs[1]) & 1) and (not factor[3] or refs[0] != refs[1])
        if allowed:
            removed.append([index, row, list(refs)])
    count = sum(f[4] for f in factors)
    return {'factors': factors, 'base_count': count, 'excluded_legal': removed, 'count': count - len(removed)}


def canonical_blocks(value):
    """Bounded complete stdlib encoding, keeping all byte/EOF comparisons."""
    parts, characters = [], 0
    for piece in json.JSONEncoder(sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                                  allow_nan=False).iterencode(value):
        parts.append(piece); characters += len(piece)
        if characters >= 16384:
            yield ''.join(parts)
            parts, characters = [], 0
    if parts:
        yield ''.join(parts)


def compare_owned_chunks(chunks, record, b):
    """Whole byte + SHA/length + EOF against an already cold-closed named pin."""
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'exact named raw witness pin')
    path = Path(record['path'])
    need(path.is_absolute() and not path.is_symlink() and path == path.resolve(), 'canonical nonsymlink witness')
    need(type(record['bytes']) is int and 0 <= record['bytes'] <= 64 * 1024 * 1024, 'bounded complete witness')
    before = path.stat(); h = hashlib.sha256(); size = 0
    with path.open('rb') as source:
        for chunk in chunks:
            b.tick()
            encoded = chunk.encode('utf8')
            need(source.read(len(encoded)) == encoded, 'full independent/raw witness byte equality')
            h.update(encoded); size += len(encoded)
        need(source.read(1) == b'', 'no omitted suffix/extra field/trailing witness bytes')
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'stable whole witness file')
    need(size == record['bytes'] and h.hexdigest() == record['sha256'], 'actual raw witness length/SHA')
    b.check()


def check_point_state(*, state, catalogue, primitives, epoch, b, require_initial=False,
                      oracle_record=None, state_record=None):
    """Independent full physical union/domain relation for a saved snapshot.

    Pending strict-prior readers are physical obligations, not logical ancestry
    acceptance. Exclusions are compared as saved branch metadata; this function
    does not prove search exhaustion, learned pruning or trajectory correctness.
    """
    fields = {'domains', 'excluded', 'marks', 'model_epoch', 'order', 'roots', 'selected_generations', 'totals'}
    need(type(state) is dict and set(state) == fields and state['model_epoch'] == epoch, 'complete epoch-bound state')
    height = catalogue['height']
    need(type(state['totals']) is list and len(state['totals']) == height
         and all(type(t) is int and t in (0, 1) for t in state['totals']), 'every exact occupancy total')
    need(canonical(state['roots']) == canonical(catalogue['boundary']['roots']), 'exact original root generations')
    need(type(state['order']) is list and type(state['marks']) is list
         and type(state['excluded']) is list and len(state['excluded']) == height, 'complete state arrays')
    keys = [parse_key(raw, primitives, height) for raw in state['order']]
    need(len(keys) == len(set(keys)), 'shared physical constituents included once')
    totals, marks, counts = [0] * height, {}, {}
    for x, y, value in catalogue['boundary']['fixed_marks']:
        point = integer(x), integer(y); integer(value)
        need(point not in marks, 'unique fixed marking point')
        marks[point], counts[point] = value, 1
    for key in keys:
        b.tick()
        t, m = literal_points(key, primitives)
        for _, row, value in t:
            totals[row] += value
            need(totals[row] <= 1, 'no physical support over-occupancy')
        for x, y, value in m:
            point = x, y
            need(point not in marks or marks[point] == value, 'complete fixed/current t/m union agreement')
            marks[point] = value; counts[point] = counts.get(point, 0) + 1
    expected_marks = [[x, y, value, counts[x, y]] for (x, y), value in sorted(marks.items())]
    need(state['totals'] == totals and canonical(state['marks']) == canonical(expected_marks),
         'all support totals and assigned marks/refcounts exact, including assigned zero')
    generations = state['selected_generations']
    need(type(generations) is list and len(generations) == len(keys), 'all selected generation records')
    recovered = []
    for raw, generation in generations:
        key = parse_key(raw, primitives, height); integer(generation)
        need(generation == 1 + state['roots'][key[1]], 'exact nonseed placement generation under the original root-zero model')
        recovered.append(key)
    need(recovered == sorted(keys), 'generation keys match every selected physical placement')
    excluded = []
    for row, raw_keys in enumerate(state['excluded']):
        need(type(raw_keys) is list, 'all excluded sets explicit')
        values = [parse_key(raw, primitives, height) for raw in raw_keys]
        need(values == sorted(set(values)) and all(k[1] == row for k in values), 'canonical unique branch-local exclusions')
        excluded.append(values)
    if require_initial:
        need(not keys and generations == [] and totals == [0] * height
             and state['excluded'] == [[] for _ in range(height)], 'genuine complete empty initial state, no seed/proof')
    need(type(state['domains']) is list and len(state['domains']) == height, 'all required row domains')
    row_digests, domain_counts = [], []
    def chunks():
        yield '['
        for row in range(height):
            expected = independent_domain(row, primitives=primitives, totals=totals,
                marks=marks, exclusions=excluded[row], b=b)
            need(canonical(expected) == canonical(state['domains'][row]), 'every exact factor/count/removal in required row')
            row_digests.append(digest(expected)); domain_counts.append(expected['count'])
            if row:
                yield ','
            yield canonical(expected)
        yield ']'
    if oracle_record is not None:
        compare_owned_chunks(chunks(), oracle_record, b)
    else:
        for _ in chunks():
            pass
    if state_record is not None:
        compare_owned_chunks(canonical_blocks(state), state_record, b)
    frontier = [row for row in range(height) if totals[row] == 0]
    dead = [row for row in frontier if domain_counts[row] == 0]
    forced = [row for row in frontier if domain_counts[row] == 1]
    if dead:
        chosen, kind = min(dead), 'dead'
    elif forced:
        chosen, kind = min(forced), 'forced'
    elif not frontier:
        chosen, kind = None, 'complete'
    else:
        chosen = min(frontier, key=lambda row: (state['roots'][row], domain_counts[row], row))
        kind = 'branch'
    decision = {'kind': kind, 'row': chosen, 'count': domain_counts[chosen] if chosen is not None else 0,
                'generation': state['roots'][chosen] if chosen is not None else None}
    b.check()
    return {'all_rows': height, 'domain_sha256_by_row': row_digests, 'domain_counts': domain_counts,
            'point_decision': decision,
            'complete_candidate_count': sum(domain_counts), 'selected_physical_keys': len(keys),
            'exact_saved_point_union_accepted': True, 'full_trajectory_accepted': False,
            'logical_proof_accepted': False, 'full24_accepted': False}


def audit_saved_profile(*, declaration, preparation, expected_source_bindings, source_guard, deadline,
                        initial_state_record, initial_oracle_record):
    """Reconstruct whole formula/recipe language then audit every initial domain.

    ROOT's future worker authenticates one raw preparation buffer and its exact
    declaration, seven provenance roles and original resource-closed producer
    inputs before this API. All producer roles remain RAW-ONLY. This function
    imports no producer kernel, compiler, graph, control or serializer.
    """
    began = time.perf_counter()
    b = Boundary(source_guard, deadline)
    need(type(declaration) is dict and set(declaration) ==
        {'schema', 'theory', 'ordered_Gamma', 'target', 'parameters', 'height', 'grammar', 'limits'}
        and declaration['schema'] == 'arithmetic-empty-Gamma-Q-declaration-v1', 'same complete literal declaration')
    need(type(preparation) is dict and type(preparation.get('catalogue')) is dict, 'whole saved preparation payload')
    catalogue = preparation['catalogue']
    need(digest(declaration) == DECLARATION_VALUE_SHA256, 'exact frozen declaration value, no target/axiom substitution')
    need(catalogue['schema'] == PRODUCER_PROFILE and canonical(catalogue['declaration']) == canonical(declaration),
         'producer catalogue has exact original declared profile')
    k = Semantics(declaration['theory'], declaration['parameters'], declaration['ordered_Gamma'], b)
    formulas, raw_recipes, census = reconstruct_grammar(k, declaration)
    saved_formulas = catalogue['formula_codes']
    need(type(saved_formulas) is list and len(saved_formulas) == len(formulas), 'whole reconstructed formula registry size')
    for expected, raw in zip(formulas, saved_formulas):
        need(k.formula(raw) == expected, 'every formula in exact canonical-code order, none missing or extra')
    registry = digest(formulas)
    need(catalogue['formula_registry_sha256'] == registry, 'injective full registry hash')
    codes = {node: code for code, node in enumerate(formulas)}
    context = {'theory': declaration['theory'], 'ordered_local_premises': declaration['ordered_Gamma']}
    need(canonical(catalogue['context']) == canonical(context), 'entire original ordered context')
    need(type(expected_source_bindings) is dict and set(expected_source_bindings) ==
         {'kernel', 'catalogue', 'point_graph', 'payload', 'controls', 'worker', 'master'}, 'complete original seven raw roles')
    need(canonical(expected_source_bindings) == canonical(FROZEN_PRODUCER_BINDINGS),
         'exact unchanged original producer provenance ledger, not arbitrary caller sources')
    authority_base = {'activated': False, 'native_accepted': False,
        'recipient_theory_sha256': digest(declaration['theory']), 'profile': PRODUCER_PROFILE,
        'declaration_sha256': digest(declaration), 'scope': 'Q finite six-rule open-parameter grammar only',
        'source_bindings': expected_source_bindings}
    authority = dict(authority_base, epoch=digest(authority_base))
    need(canonical(catalogue['authority']) == canonical(authority), 'whole original raw source/theory/grammar authority preimage')
    saved_recipes = catalogue['recipes']
    need(type(saved_recipes) is list and len(saved_recipes) == len(raw_recipes), 'complete reconstructed primitive universe size')
    primitives, ids = [], []
    arities = {'0': 0, '1': 0, '2': 0}
    rule_counts = {rule: 0 for rule in RULE_FIELDS}
    for index, (expected, record) in enumerate(zip(raw_recipes, saved_recipes)):
        b.tick()
        need(type(record) is dict and set(record) == {'primitive_witness', 'ordered_premise_formulas', 'id', 'identity_preimage'},
             'exact complete raw primitive record')
        raw = {'primitive_witness': record['primitive_witness'], 'ordered_premise_formulas': record['ordered_premise_formulas']}
        need(canonical(raw) == expected, 'every allowed primitive in exact complete canonical order')
        out, inputs = k.recipe(record['primitive_witness'], record['ordered_premise_formulas'])
        need(out in codes and all(f in codes for f in inputs), 'all output and ordered ports in full registry')
        preimage = {'recipe': raw, 'primitive_authority_epoch': authority['epoch'],
            'recipient_theory_sha256': authority['recipient_theory_sha256'], 'marking_version': MARKING,
            'formula_registry_sha256': registry, 'local_context_id': digest(context)}
        need(canonical(record['identity_preimage']) == canonical(preimage) and record['id'] == 'primitive-recipe-' + digest(preimage),
             'every raw recipe/source/context/marking identity preimage exact')
        ids.append(record['id']); primitives.append((codes[out], tuple(codes[f] for f in inputs)))
        arities[str(len(inputs))] += 1; rule_counts[record['primitive_witness']['rule']] += 1
    need(len(set(ids)) == len(ids), 'no duplicate primitive identity')
    census['arity_counts'] = arities
    census['unconstrained_key_universe_upper_bound'] = sum(arities['0'] + arities['1'] * row
        + arities['2'] * row * row for row in range(declaration['height']))
    need(canonical(catalogue['census']) == canonical(census) and canonical(preparation['census']) == canonical(census),
         'producer census equals reconstruction; observed counts are not acceptance constants')
    target = k.formula(declaration['target'])
    boundary = {'required': [[0, row] for row in range(24)], 'roots': [0] * 24, 'seed_keys': [],
        'fixed_marks': [[1, row, -1] for row in range(-23, 0)] + [[1, 23, codes[target]]]}
    need(type(catalogue['height']) is int and catalogue['height'] == 24 and canonical(catalogue['boundary']) == canonical(boundary), 'all required points/fixed boundary/no dummy seeds')
    for name in ('first_primitive_search_accepted', 'independent_catalogue_accepted', 'native_accepted',
                 'full_PA_accepted', 'universal_compiler_accepted'):
        need(catalogue[name] is False, 'producer has not granted independent/stronger mathematical authority')
    epoch = digest({'height': 24, 'context': context, 'registry': registry, 'authority': authority['epoch'],
        'recipes': ids, 'fixed_marks': boundary['fixed_marks'], 'roots': boundary['roots'], 'seed_keys': [],
        'marking_version': MARKING, 'fixture': False, 'source_bindings': expected_source_bindings})
    b.check()
    point_result = check_point_state(state=preparation['initial_state'], catalogue=catalogue,
        primitives=primitives, epoch=epoch, b=b, require_initial=True,
        state_record=initial_state_record, oracle_record=initial_oracle_record)
    need(canonical(preparation['initial_legal_domain_counts']) == canonical(point_result['domain_counts'])
         and type(preparation['initial_legal_candidate_count']) is int
         and preparation['initial_legal_candidate_count'] == point_result['complete_candidate_count'],
         'whole preparation summaries equal all independently checked domains')
    need(canonical(preparation['initial_decision']) == canonical(point_result['point_decision']),
         'global dead then forced then earliest generation with candidate-count tie break')
    # Endpoint record is completed before the final deadline boundary. No prefix
    # certificate is returned if any check, EOF, code guard or ceiling fails.
    result = {'schema': 'independent-complete-Q-catalogue-point-audit-v1', 'completed': True,
        'all_catalogue_primitive_and_initial_domains_accepted': True,
        'bounded_grammar_complete': True, 'grammar': GRAMMAR, 'original_Gamma': declaration['ordered_Gamma'],
        'declaration_sha256': digest(declaration), 'source_bindings': expected_source_bindings,
        'formula_registry_sha256': registry, 'primitive_authority_epoch': authority['epoch'],
        'model_epoch': epoch, 'census': census, 'primitive_rule_counts': rule_counts,
        'initial_point_domains': point_result,
        'actual_primitive_semantic_checks': len(primitives),
        'FOL_complete': False, 'full_PA_accepted': False, 'induction_accepted': False,
        'universal_compiler_accepted': False, 'native_accepted': False, 'full24_accepted': False,
        'full_trajectory_accepted': False, 'target_proof_discovered': False,
        'searches': 0, 'RL_updates': 0, 'ROOT_admission_issued': False, 'ROOT_resource_accepted': False}
    canonical(result); b.check()
    result['visits'] = b.visits; result['elapsed_seconds_before_final_guard'] = time.perf_counter() - began
    canonical(result); b.check()
    return result
