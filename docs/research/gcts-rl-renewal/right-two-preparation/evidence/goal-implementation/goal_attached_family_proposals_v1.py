"""SOURCE ONLY provisional goal-family guidance; no graph mutation or proof authority.

Consumes the actual mined e499 data schema. The catalogue/Source/library raw
admission and cold caller are separate gates. No target term, proof word or
donor row assignment is present here. Pending inputs never become facts.
"""
import copy
import hashlib
import itertools
import json

VERSION = 'Q-goal-attached-atomic-family-proposal-Source-v1'
SYNTAX_LIMITS = {'context_nodes': 64, 'term_nodes': 64,
                'term_depth': 16, 'context_parameters': 32}
ROLES = ('s', 't')

class NoInstance(ValueError):
    """No licensed/compatible instance; all original base alternatives remain."""

class OutsideSyntax(NoInstance):
    """Declared family bound/type mismatch, distinct from delegated failures."""

def syntax_need(ok, message):
    if not ok:
        raise OutsideSyntax(message)

def need(ok, message):
    if not ok:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()

def integer(value, lower=0, upper=None):
    need(type(value) is int and value >= lower and (upper is None or value < upper),
         'literal bounded integer; Boolean is not an index')
    return value

def term(value, theory, parameters, tick):
    """Bounded nominal term; bounds restrict this advice, never base grammar."""
    pending, nodes = [(value, 0)], 0
    while pending:
        tick()
        node, depth = pending.pop()
        nodes += 1
        syntax_need(nodes <= SYNTAX_LIMITS['term_nodes'] and depth <= SYNTAX_LIMITS['term_depth'],
             'outside fixed family term node/depth bounds')
        syntax_need(type(node) is list and node, 'literal term AST')
        if node[0] == 'var':
            syntax_need(len(node) == 2 and type(node[1]) is str and node[1] in parameters,
                 'term variable is an original declared parameter')
        else:
            syntax_need(len(node) == 3 and node[0] == 'fun' and type(node[1]) is str
                 and type(node[2]) is list and node[1] in theory['functions']
                 and type(theory['functions'][node[1]]) is int
                 and len(node[2]) == theory['functions'][node[1]], 'original term signature')
            pending.extend((child, depth + 1) for child in reversed(node[2]))
    return copy.deepcopy(value)

def atomic_shape(atom, hole, theory, parameters, tick):
    """Validate the fixed finite atomic syntax; retain every hole occurrence.

    Context has at most 64 AST nodes (atom included), depth at most 16 in each
    term, and no binder/connective. Function/predicate names are nominal.
    A single hole name may occur repeatedly, always with one simultaneous term.
    """
    tick()
    syntax_need(type(atom) is list and atom, 'literal atomic context')
    if atom[0] == 'eq':
        syntax_need(len(atom) == 3, 'binary equality atom')
        args = atom[1:]
    else:
        syntax_need(len(atom) == 3 and atom[0] == 'pred' and type(atom[1]) is str
             and type(atom[2]) is list and atom[1] in theory['predicates']
             and type(theory['predicates'][atom[1]]) is int
             and len(atom[2]) == theory['predicates'][atom[1]],
             'declared predicate signature and exact arity')
        args = atom[2]
    pending, nodes, holes = [(a, 0) for a in reversed(args)], 1, 0
    while pending:
        tick()
        node, depth = pending.pop()
        nodes += 1
        syntax_need(nodes <= SYNTAX_LIMITS['context_nodes']
             and depth <= SYNTAX_LIMITS['term_depth'], 'outside atomic-context bounds')
        syntax_need(type(node) is list and node, 'literal atomic-context term')
        if node[0] == 'var':
            syntax_need(len(node) == 2 and type(node[1]) is str
                 and (node[1] == hole or node[1] in parameters), 'free context variable scope')
            holes += int(node[1] == hole)
        else:
            syntax_need(len(node) == 3 and node[0] == 'fun' and type(node[1]) is str
                 and type(node[2]) is list and node[1] in theory['functions']
                 and type(theory['functions'][node[1]]) is int
                 and len(node[2]) == theory['functions'][node[1]], 'typed context function')
            pending.extend((a, depth + 1) for a in reversed(node[2]))
    return {'nodes': nodes, 'hole_occurrences': holes}

def fill_context(value, replacement):
    """Replace every one-hole marker simultaneously, without revisiting terms."""
    if value == ['family-hole']:
        return copy.deepcopy(replacement)
    if type(value) is list:
        return [fill_context(v, replacement) for v in value]
    return copy.deepcopy(value)

def ground(value, terms, hole):
    if value == ['family-hole']:
        return ['var', hole]
    if value == ['family-hole-name']:
        return hole
    if type(value) is list and len(value) == 2 and value[0] == 'family-term':
        need(value[1] in terms, 'declared bound family role')
        return copy.deepcopy(terms[value[1]])
    if type(value) is list:
        return [ground(v, terms, hole) for v in value]
    if type(value) is dict:
        return {k: ground(v, terms, hole) for k, v in value.items()}
    return copy.deepcopy(value)


def _ports(member):
    result = []
    for value in member['ordered_ports']:
        if value.startswith('input:'):
            need(value in ('input:equality', 'input:formula'), 'exact ordered external port')
            result.append(['input', 0 if value == 'input:equality' else 1])
        else:
            need(value in ('member:0', 'member:1'), 'strict-prior internal member port')
            result.append(['member', int(value[-1])])
    return result


def _family_shape(family, tick):
    """Validate generic mined structure, never a particular context or donor."""
    tick()
    shape = family['shape']
    need(type(shape) is dict and set(shape) == {
        'slice', 'syntax_limits', 'roles', 'atomic_context',
        'input_receptors', 'members', 'output'}, 'exact mined e499 family shape')
    roles = shape['roles']
    need(shape['slice'] == 'bounded-typed-atomic-context'
         and shape['syntax_limits'] == SYNTAX_LIMITS
         and type(roles) is list and roles[:2] == list(ROLES)
         and roles[2:] == ['u'+str(i) for i in range(len(roles)-2)]
         and len(roles) <= 2 + SYNTAX_LIMITS['context_parameters'],
         'bounded typed family role ABI')
    need(family['family_id'] == 'atomic-context-family-' + digest(shape),
         'actual shape identity, not a family name as authority')
    pattern = shape['atomic_context']
    pending, holes, used, nodes = [(pattern, True, 0)], 0, set(), 0
    while pending:
        tick()
        node, atom, depth = pending.pop()
        nodes += 1
        need(nodes <= SYNTAX_LIMITS['context_nodes']
             and depth <= SYNTAX_LIMITS['term_depth'] + 1
             and type(node) is list and node, 'bounded literal family pattern')
        if node == ['family-hole']:
            need(not atom, 'hole occurs inside an atomic term')
            holes += 1
        elif node[0] == 'family-term':
            need(not atom and len(node) == 2 and node[1] in roles,
                 'one declared correlated term role')
            used.add(node[1])
        elif atom:
            if node[0] == 'eq':
                need(len(node) == 3, 'binary equality context')
                pending.extend((v, False, depth + 1) for v in reversed(node[1:]))
            else:
                need(len(node) == 3 and node[0] == 'pred'
                     and type(node[1]) is str and type(node[2]) is list,
                     'literal predicate atomic context')
                pending.extend((v, False, depth + 1) for v in reversed(node[2]))
        else:
            need(len(node) == 3 and node[0] == 'fun' and type(node[1]) is str
                 and type(node[2]) is list, 'nominal context function')
            pending.extend((v, False, depth + 1) for v in reversed(node[2]))
    need(holes > 0 and used <= set(roles), 'actual one-name hole context')
    a, b = ['family-term', 's'], ['family-term', 't']
    left = fill_context(pattern, a)
    right = fill_context(pattern, b)
    expected = [
        {'witness': {'rule': 'eq_subst', 'formula': ['imp', ['eq', a, b], ['imp', left, right]],
                     'variable': ['family-hole-name'], 'template': pattern, 'left': a, 'right': b},
         'ordered_ports': []},
        {'witness': {'rule': 'mp', 'formula': ['imp', left, right]},
         'ordered_ports': ['input:equality', 'member:0']},
        {'witness': {'rule': 'mp', 'formula': right},
         'ordered_ports': ['input:formula', 'member:1']}]
    need(shape['input_receptors'] == [['eq', a, b], left]
         and shape['output'] == right and shape['members'] == expected,
         'exact three primitive members and ordered receptors, no new rule')
    return shape


def _match(pattern, value, roles, terms, context, tick):
    tick()
    if type(pattern) is list and len(pattern) == 2 and pattern[0] == 'family-term':
        need(pattern[1] in roles, 'declared output role')
        try:
            checked = term(value, context['theory'], context['parameters'], tick)
        except OutsideSyntax:
            return False
        if pattern[1] in terms:
            return terms[pattern[1]] == checked
        terms[pattern[1]] = checked
        return True
    if type(pattern) is list:
        return (type(value) is list and len(value) == len(pattern)
                and all(_match(a, b, roles, terms, context, tick)
                        for a, b in zip(pattern, value)))
    return type(value) is type(pattern) and value == pattern


class GoalFamilyIndex:
    """Read-only raw-catalogue view, shared by ordinary and point consumers.

    Input is the existing preparation['catalogue'], not a new parse or grammar.
    The term-role pool is exactly the canonical distinct well-typed left/right
    operands of ALL licensed eq_subst records. UI-only terms do not get promoted
    into the equality operand grammar. This view is not a catalogue admission.
    """
    def __init__(self, *, catalogue, binding, tick):
        tick()
        need(type(binding) is dict and set(binding) == {
            'declaration_sha256', 'model_epoch', 'primitive_authority_epoch',
            'formula_registry_sha256'} and all(type(v) is str and len(v) == 64
            and all(c in '0123456789abcdef' for c in v) for v in binding.values()),
            'caller-authenticated exact recipient four-digest binding')
        spec = catalogue['declaration']
        need(catalogue['height'] == spec['height'] == 24 and spec['ordered_Gamma'] == []
             and len(spec['parameters']) == 1
             and catalogue['context'] == {'theory': spec['theory'],
                 'ordered_local_premises': spec['ordered_Gamma']},
             'same Q arithmetic profile, not a new theorem or Gamma')
        self.catalogue = catalogue
        self.binding = copy.deepcopy(binding)
        self.context = {'theory': spec['theory'], 'parameters': spec['parameters'],
                        'ordered_Gamma': spec['ordered_Gamma'], 'target': spec['target']}
        self.formulas = catalogue['formula_codes']
        self.records = catalogue['recipes']
        self.counts = {'records_indexed': 0, 'licensed_operand_terms': 0,
            'output_matches': 0, 'role_bindings_tried': 0,
            'licensed_instances': 0, 'point_embeddings_considered': 0,
            'point_proposals_emitted': 0}
        self.codes = {canonical(f): i for i, f in enumerate(self.formulas)}
        need(len(self.codes) == len(self.formulas)
             and digest(self.formulas) == catalogue['formula_registry_sha256']
             == binding['formula_registry_sha256']
             and catalogue['authority']['epoch'] == binding['primitive_authority_epoch'],
             'whole original registry and primitive authority')
        boundary = catalogue['boundary']
        need(boundary['seed_keys'] == [], 'same original empty-Gamma seed inventory')
        fixed = {}
        for x, y, value in boundary['fixed_marks']:
            need((x, y) not in fixed or fixed[(x, y)] == value,
                 'consistent original fixed marks')
            fixed[(x, y)] = value
        original_epoch = {'height': catalogue['height'], 'context': catalogue['context'],
            'registry': catalogue['formula_registry_sha256'],
            'authority': catalogue['authority']['epoch'],
            'recipes': [r['id'] for r in self.records],
            'fixed_marks': [[*p, v] for p, v in sorted(fixed.items())],
            'roots': boundary['roots'], 'seed_keys': boundary['seed_keys'],
            'marking_version': 'injective-formula-ordered-primitive-offset-Q-v1',
            'fixture': False, 'source_bindings': catalogue['authority']['source_bindings']}
        need(digest(original_epoch) == binding['model_epoch'],
             'same original graph epoch; declaration raw hash is caller custody')
        authority = catalogue['authority']
        need(digest({k: v for k, v in authority.items() if k != 'epoch'}) == authority['epoch']
             and authority['recipient_theory_sha256'] == digest(spec['theory']),
             'same original primitive authority preimage')
        context_id = digest(catalogue['context'])
        self.lookup, self.by_output, self.outputs, self.inputs = {}, {}, [], []
        pool, holes = {}, []
        for index, record in enumerate(self.records):
            tick()
            self.counts['records_indexed'] += 1
            w, premises = record['primitive_witness'], record['ordered_premise_formulas']
            rule = w['rule']
            need(rule in ('axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize'),
                 'same original six-rule recipe inventory')
            arity = 2 if rule == 'mp' else 1 if rule == 'generalize' else 0
            need(type(premises) is list and len(premises) == arity
                 and not any(k in w for k in ('source', 'antecedent', 'implication')),
                 'recipe witness without physical references')
            if rule == 'mp':
                need(premises[1] == ['imp', premises[0], w['formula']], 'ordered original MP')
            if rule == 'generalize':
                need(w['formula'] == ['all', w['variable'], premises[0]], 'original unary recipe')
            preimage = {'recipe': {'primitive_witness': w, 'ordered_premise_formulas': premises},
                'primitive_authority_epoch': authority['epoch'],
                'recipient_theory_sha256': authority['recipient_theory_sha256'],
                'marking_version': 'injective-formula-ordered-primitive-offset-Q-v1',
                'formula_registry_sha256': catalogue['formula_registry_sha256'],
                'local_context_id': context_id}
            need(record['identity_preimage'] == preimage
                 and record['id'] == 'primitive-recipe-' + digest(preimage),
                 'exact original whole recipe identity preimage')
            signature = canonical([w, premises])
            need(signature not in self.lookup, 'unique original complete recipe signature')
            self.lookup[signature] = index
            output = self.codes[canonical(w['formula'])]
            inputs = [self.codes[canonical(f)] for f in premises]
            self.outputs.append(output)
            self.inputs.append(inputs)
            self.by_output.setdefault(output, []).append(index)
            if rule == 'eq_subst':
                hole = w['variable']
                need(type(hole) is str and hole and hole not in spec['parameters'],
                     'current licensed distinct substitution hole')
                if hole not in holes:
                    holes.append(hole)
                for operand in (w['left'], w['right']):
                    try:
                        value = term(operand, spec['theory'], spec['parameters'], tick)
                    except OutsideSyntax:
                        continue  # Family bound only; original records remain.
                    pool[canonical(value)] = value
        self.pool = tuple(pool[k] for k in sorted(pool))
        self.counts['licensed_operand_terms'] = len(self.pool)
        self.holes = tuple(holes)  # Original recipe order, not target benefit.
        self.height = catalogue['height']
        self.fixed = fixed
        self.roots = catalogue['boundary']['roots']
        tick()

    def goal_codes(self, *, goal_code, tick):
        integer(goal_code, 0, len(self.formulas))
        order, seen, cursor = [goal_code], {goal_code}, 0
        while cursor < len(order):
            tick()
            code = order[cursor]
            cursor += 1
            for recipe in self.by_output.get(code, ()):
                tick()
                for premise in self.inputs[recipe]:
                    if premise not in seen:
                        seen.add(premise)
                        order.append(premise)
        return order

    def iter_instances(self, *, goal_formula, family, tick):
        """Complete canonical unbound-role enumeration; may be stopped as advice.

        No sampling/top-k completes a domain. Consumers may take the first
        preference because no proposal contributes to dead/forced degree counts.
        A budget exception propagates; it never means NoInstance/exhaustion.
        """
        shape = _family_shape(family, tick)
        if canonical(goal_formula) not in self.codes:
            return
        try:
            atomic_shape(goal_formula, None, self.context['theory'],
                         self.context['parameters'], tick)
        except OutsideSyntax:
            return
        bound = {}
        if not _match(shape['output'], goal_formula, shape['roles'], bound, self.context, tick):
            return
        self.counts['output_matches'] += 1
        unbound = [r for r in shape['roles'] if r not in bound]
        for values in itertools.product(self.pool, repeat=len(unbound)):
            tick()
            self.counts['role_bindings_tried'] += 1
            terms = {r: copy.deepcopy(bound[r]) for r in shape['roles'] if r in bound}
            terms.update((r, copy.deepcopy(v)) for r, v in zip(unbound, values))
            # The same bindings fill every occurrence, without sequential rewrite.
            for hole in self.holes:
                tick()
                witnesses = [ground(m['witness'], terms, hole) for m in shape['members']]
                inputs = ground(shape['input_receptors'], terms, hole)
                try:
                    atomic_shape(witnesses[0]['template'], hole, self.context['theory'],
                                 self.context['parameters'], tick)
                    for atom in [*inputs, goal_formula]:
                        atomic_shape(atom, None, self.context['theory'],
                                     self.context['parameters'], tick)
                except OutsideSyntax:
                    continue
                premise_sets = [[], [inputs[0], witnesses[0]['formula']],
                                [inputs[1], witnesses[1]['formula']]]
                indices = [self.lookup.get(canonical([w, ps]))
                           for w, ps in zip(witnesses, premise_sets)]
                if any(i is None for i in indices):
                    continue
                need(witnesses[2]['formula'] == goal_formula,
                     'same output and simultaneous grounded binding')
                input_codes = [self.codes[canonical(f)] for f in inputs]
                members = [{'recipe_index': i, 'recipe_id': self.records[i]['id'],
                            'ordered_ports': _ports(member),
                            'primitive_witness': copy.deepcopy(w)}
                           for i, member, w in zip(indices, shape['members'], witnesses)]
                self.counts['licensed_instances'] += 1
                yield {'schema': 'goal-attached-logical-instance-v1',
                    'recipient_binding': copy.deepcopy(self.binding),
                    'family_id': family['family_id'],
                    'output_code': self.codes[canonical(goal_formula)],
                    'goal_formula': copy.deepcopy(goal_formula),
                    'role_terms': copy.deepcopy(terms), 'licensed_hole': hole,
                    'ordered_input_codes': input_codes, 'members': members,
                    'input_obligations': [{'port': i, 'formula_code': c,
                        'formula': copy.deepcopy(inputs[i]), 'status': 'PENDING',
                        'fact_accepted': False} for i, c in enumerate(input_codes)],
                    'status': 'PENDING_INPUTS', 'logical_accepted': False,
                    'new_primitive_rule': False, 'ROOT_library_admitted': False}
        tick()


def primitive_goal_order(*, index, goal_code, tick):
    """Full recipe permutation: inverse-goal preference then canonical fallback."""
    result, seen = [], set()
    for code in index.goal_codes(goal_code=goal_code, tick=tick):
        for recipe in index.by_output.get(code, ()):
            tick()
            if recipe not in seen:
                seen.add(recipe)
                result.append(recipe)
    for recipe in range(len(index.records)):
        tick()
        if recipe not in seen:
            result.append(recipe)
    need(len(result) == len(index.records) and len(set(result)) == len(result),
         'every original recipe exactly once, no backcone pruning')
    return result


def _key(raw, index):
    need(type(raw) is list and len(raw) == 3 and type(raw[2]) is list,
         'original primitive [recipe,row,ordered_refs]')
    recipe = integer(raw[0], 0, len(index.records))
    row = integer(raw[1], 0, index.height)
    refs = tuple(integer(r, 0, row) for r in raw[2])
    need(len(refs) == len(index.inputs[recipe]), 'original ordered port arity')
    return recipe, row, refs


def _raw(key):
    return [key[0], key[1], list(key[2])]


def _union(keys, index, tick):
    totals, marks, counts, seen = [0]*index.height, dict(index.fixed), {}, set()
    counts.update((p, 1) for p in marks)
    for raw in keys:
        tick()
        key = _key(raw, index)
        need(key not in seen, 'shared key counted once')
        seen.add(key)
        recipe, row, refs = key
        totals[row] += 1
        if totals[row] > 1:
            raise NoInstance('different positive placements overlap')
        local = {(1, row): index.outputs[recipe]}
        for port, (ref, code) in enumerate(zip(refs, index.inputs[recipe])):
            if (1, ref) in local and local[(1, ref)] != code:
                raise NoInstance('conflicting repeated source marks')
            local[(1, ref)] = code
            local[(2+port, row)] = ref-row
        for point, value in local.items():
            if point in marks and marks[point] != value:
                raise NoInstance('current/fixed assigned markings disagree')
            marks[point] = value
            counts[point] = counts.get(point, 0)+1
    return totals, marks, counts


def point_view(*, index, state, tick):
    """Small full t/m/order/exclusion view only; not a full-domain certificate."""
    need(state['model_epoch'] == index.binding['model_epoch']
         and canonical(state['roots']) == canonical(list(index.roots))
         and len(state['excluded']) == index.height, 'same original point context')
    selected = {}
    for raw in state['order']:
        key = _key(raw, index)
        need(key[1] not in selected, 'one actual selected key per physical row')
        selected[key[1]] = key
    totals, marks, counts = _union(state['order'], index, tick)
    need(canonical(totals) == canonical(state['totals']) and canonical(state['marks']) == canonical([
        [*p, marks[p], counts[p]] for p in sorted(marks)]), 'exact typed current union/refcounts')
    excluded = [{_key(k, index) for k in row} for row in state['excluded']]
    need(all(len(keys) == len(raw) for keys, raw in zip(excluded, state['excluded'])),
         'no duplicate parent exclusion normalization')
    need(all(k[1] == r for r, row in enumerate(excluded) for k in row)
         and all(k not in excluded[r] for r, k in selected.items()), 'current parent-local exclusions')
    complete = set()
    for row, key in sorted(selected.items()):
        tick()
        if all(ref in complete for ref in key[2]):
            complete.add(row)
    return selected, marks, excluded, complete


def iter_point_proposals(*, index, instance, state, goal_row, tick, branch_row=None):
    """All strict-prior five-node embeddings; no mutation, reservations or macro.

    The two external input occurrences remain separate even if they share one
    compatible row. Every returned member is an ORIGINAL recipe/key. New input
    facts are NOT manufactured. Existing selected members may be shared exactly.
    """
    integer(goal_row, 0, index.height)
    integer(instance['output_code'], 0, len(index.formulas))
    if branch_row is not None:
        integer(branch_row, 0, index.height)
    need(instance['recipient_binding'] == index.binding
         and instance['status'] == 'PENDING_INPUTS'
         and instance['logical_accepted'] is False, 'same provisional instance')
    selected, marks, excluded, complete = point_view(index=index, state=state, tick=tick)
    if (1, goal_row) in marks and marks[(1, goal_row)] != instance['output_code']:
        return
    if goal_row < 2:
        return
    need(type(instance['members']) is list and len(instance['members']) == 3
         and type(instance['ordered_input_codes']) is list
         and len(instance['ordered_input_codes']) == 2, 'whole ordered provisional body')
    indices = [integer(m['recipe_index'], 0, len(index.records)) for m in instance['members']]
    codes = [integer(c, 0, len(index.formulas)) for c in instance['ordered_input_codes']]
    need(all(m['primitive_witness'] == index.records[i]['primitive_witness']
             and m['recipe_id'] == index.records[i]['id']
             for m, i in zip(instance['members'], indices))
         and [m['ordered_ports'] for m in instance['members']] ==
             [[], [['input', 0], ['member', 0]], [['input', 1], ['member', 1]]]
         and index.inputs[indices[0]] == []
         and index.inputs[indices[1]] == [codes[0], index.outputs[indices[0]]]
         and index.inputs[indices[2]] == [codes[1], index.outputs[indices[1]]]
         and index.outputs[indices[2]] == instance['output_code']
         and index.formulas[instance['output_code']] == instance['goal_formula'],
         'exact original witnesses and ordered input/output preimages')
    for r0 in range(goal_row-1):
        for r1 in range(r0+1, goal_row):
            rows = (r0, r1, goal_row)
            if branch_row is not None and branch_row not in rows:
                continue
            for a in range(r1):
                for b in range(goal_row):
                    tick()
                    index.counts['point_embeddings_considered'] += 1
                    if a == b and codes[0] != codes[1]:
                        continue
                    if any((1, row) in marks and marks[(1, row)] != code
                           for row, code in zip((a, b), codes)):
                        continue
                    keys = [(indices[0], r0, ()), (indices[1], r1, (a, r0)),
                            (indices[2], goal_row, (b, r1))]
                    if any(k in excluded[k[1]] or
                           (k[1] in selected and selected[k[1]] != k) for k in keys):
                        continue
                    added = [k for k in keys if k[1] not in selected]
                    if branch_row is not None and not any(k[1] == branch_row for k in added):
                        continue
                    whole = state['order'] + [_raw(k) for k in added]
                    try:
                        _union(whole, index, tick)
                    except NoInstance:
                        continue
                    obligations = []
                    for port, (row, code) in enumerate(zip((a, b), codes)):
                        actual = selected.get(row)
                        status = ('DEPENDENCY_COMPLETE_SELECTED' if row in complete else
                                  'SELECTED_PENDING' if actual is not None else 'PENDING')
                        obligations.append({'port': port, 'formula_code': code,
                            'formula': copy.deepcopy(index.formulas[code]), 'physical_row': row,
                            'status': status, 'selected_key_or_null': None if actual is None else _raw(actual),
                            'fact_accepted': False})
                    primitive_members = []
                    for key, member in zip(keys, instance['members']):
                        command = copy.deepcopy(member['primitive_witness'])
                        if command['rule'] == 'mp':
                            command.update(antecedent=key[2][0], implication=key[2][1])
                        primitive_members.append({'key': _raw(key), 'physical_command': command})
                    index.counts['point_proposals_emitted'] += 1
                    yield {'schema': 'goal-attached-point-proposal-v1',
                        'recipient_binding': copy.deepcopy(index.binding),
                        'family_id': instance['family_id'], 'goal_row': goal_row,
                        'goal_formula': copy.deepcopy(instance['goal_formula']),
                        'source_point_view_sha256': digest(state),
                        'role_terms': copy.deepcopy(instance['role_terms']),
                        'ordered_input_codes': list(codes),
                        'ordered_obligations': obligations,
                        'member_keys': [_raw(k) for k in keys],
                        'new_primitive_keys': [_raw(k) for k in added],
                        'primitive_members': primitive_members,
                        'primitive_commands_are_complete_word': False,
                        'status': 'PENDING_INPUTS', 'logical_accepted': False,
                        'graph_changed': False, 'macro_executed': False,
                        'ROOT_library_admitted': False}


def first_point_preference(*, index, families, state, branch_row, goal_code, tick):
    """First compatible branch-local member; no assertion of complete advice."""
    integer(branch_row, 0, index.height)
    _, marks, _, _ = point_view(index=index, state=state, tick=tick)
    demanded = {}
    for (x, row), code in sorted(marks.items()):
        if x == 1 and 0 <= row < index.height and 0 <= code < len(index.formulas):
            demanded.setdefault(code, []).append(row)
    for code in index.goal_codes(goal_code=goal_code, tick=tick):
        if code not in demanded:
            continue
        for family in families:
            for instance in index.iter_instances(goal_formula=index.formulas[code], family=family, tick=tick):
                for row in demanded[code]:
                    for proposal in iter_point_proposals(index=index, instance=instance,
                            state=state, goal_row=row, branch_row=branch_row, tick=tick):
                        for raw in proposal['new_primitive_keys']:
                            if raw[1] == branch_row:
                                return {'preferred_key': raw, 'proposal': proposal}
    tick()
    return None
