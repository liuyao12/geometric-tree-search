"""SOURCE ONLY: incomplete conventional known-fact search in an implicit language.

No donor, family, recipe inventory, coordinates, saved word or intermediate input.
Every macro expands to the original primitives. Search limits are heuristic work
bounds, never finite-language exhaustion or a negative mathematical certificate.
"""
import copy
import json

VERSION = 'untrusted-bounded-known-fact-producer-v2'
SEARCH_LIMITS = {'maximum_rounds': 32, 'maximum_facts': 2048,
                 'maximum_parameter_terms': 256, 'maximum_proposals': 50000,
                 'maximum_atomic_templates_per_pair': 64, 'maximum_word_commands': 24}
STRONG_FLAGS = ('Root_resource_accepted', 'proof_accepted', 'point_model_accepted',
                'complete_ground_counts_accepted', 'legacy_embedding_accepted',
                'GCTS_advantage_accepted', 'RL_accepted')


class SearchStopped(Exception):
    pass


def _key(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def _size(value):
    if type(value) is not list or not value:
        return 0
    if value[0] == 'var' or value[0] == 'bot':
        return 1
    if value[0] in ('fun', 'pred'):
        return 1 + sum(_size(child) for child in value[2])
    if value[0] == 'all':
        return 1 + _size(value[2])
    return 1 + sum(_size(child) for child in value[1:])


def _term_occurrences(formula):
    # Extract syntax hints only. Each is separately validated as a parameter term.
    def terms(term):
        yield term
        if term[0] == 'fun':
            for child in term[2]:
                yield from terms(child)
    tag = formula[0]
    if tag == 'eq':
        for term in formula[1:]:
            yield from terms(term)
    elif tag == 'pred':
        for term in formula[2]:
            yield from terms(term)
    elif tag == 'all':
        yield from _term_occurrences(formula[2])
    elif tag != 'bot':
        for child in formula[1:]:
            yield from _term_occurrences(child)


def _atomic_templates(formula, left, hole, maximum, tick):
    """Single occurrences and the simultaneous all-occurrence context, not all subsets."""
    paths = []
    def walk(term, path):
        tick()
        if term == left:
            paths.append(path)
        if term[0] == 'fun':
            for index, child in enumerate(term[2]):
                walk(child, path + (2, index))
    if formula[0] == 'eq':
        walk(formula[1], (1,))
        walk(formula[2], (2,))
    elif formula[0] == 'pred':
        for index, term in enumerate(formula[2]):
            walk(term, (2, index))
    seen = set()
    for selected in [(path,) for path in paths] + ([tuple(paths)] if paths else []):
        tick()
        # Replace outer paths before inner paths; a replaced subtree needs no later edit.
        chosen = []
        for path in sorted(selected, key=lambda item: (len(item), item)):
            if not any(path[:len(parent)] == parent for parent in chosen):
                chosen.append(path)
        template = copy.deepcopy(formula)
        for path in chosen:
            parent = template
            for port in path[:-1]:
                parent = parent[port]
            parent[path[-1]] = ['var', hole]
        key = _key(template)
        if key not in seen:
            seen.add(key)
            yield template
            if len(seen) >= maximum:
                return


def propose_word(*, language, tick):
    """Return an unverified <=24-command candidate, or explicitly incomplete UNKNOWN."""
    limits = copy.deepcopy(SEARCH_LIMITS)
    counters = {'rounds': 0, 'proposals': 0, 'membership_rejections': 0,
                'facts_added': 0, 'facts_improved': 0, 'terms_added': 0,
                'term_limit_omissions': 0, 'word_bound_omissions': 0,
                'ui_proposals': 0, 'mp_proposals': 0, 'ug_proposals': 0,
                'transport_proposals': 0, 'primitive_commands_constructed': 0}
    facts, terms = {}, {}
    serial = [0]
    attempted_ui, attempted_mp, attempted_ug, attempted_transport = set(), set(), set(), set()
    stop = 'heuristic worklist quiet; implicit syntax carrier not exhausted'
    # Capture the exact language-defined definite exclusion class once.
    # Resource/callback/programming failures are not membership exclusions.
    outside_language = language.OutsideLanguage
    target_key = _key(language.target)
    target_terms = {_key(term) for term in _term_occurrences(language.target)}

    def ticked():
        tick()

    def proof_nodes(node):
        collected, pending = {}, [node]
        while pending:
            ticked()
            current = pending.pop()
            if current[0] not in collected:
                collected[current[0]] = current
                pending.extend(current[3])
        return collected

    def cost(node):
        return len(proof_nodes(node))

    def priority(node):
        formula = node[2]
        similarity = sum(_key(term) in target_terms for term in _term_occurrences(formula))
        return (0 if _key(formula) == target_key else 1, cost(node), -similarity, _size(formula), _key(formula))

    def add_terms(formula):
        for term in _term_occurrences(formula):
            ticked()
            key = _key(term)
            if key in terms:
                continue
            try:
                language.term(term)
            except outside_language:
                continue
            if len(terms) >= limits['maximum_parameter_terms']:
                counters['term_limit_omissions'] += 1
                continue
            terms[key] = copy.deepcopy(term)
            counters['terms_added'] += 1

    def node(witness, premises):
        ticked()
        if counters['proposals'] >= limits['maximum_proposals']:
            raise SearchStopped('maximum_proposals')
        counters['proposals'] += 1
        try:
            language.primitive(witness, [prior[2] for prior in premises])
        except outside_language:
            counters['membership_rejections'] += 1
            return None
        serial[0] += 1
        result = (serial[0], copy.deepcopy(witness), copy.deepcopy(witness['formula']), tuple(premises))
        counters['primitive_commands_constructed'] += 1
        if cost(result) > 24:
            counters['word_bound_omissions'] += 1
            return None
        return result

    def add(result):
        if result is None:
            return False
        key = _key(result[2])
        prior = facts.get(key)
        if prior is not None and cost(prior) <= cost(result):
            return False
        if prior is None and len(facts) >= limits['maximum_facts']:
            raise SearchStopped('maximum_facts')
        facts[key] = result
        counters['facts_added' if prior is None else 'facts_improved'] += 1
        add_terms(result[2])
        return True

    def mp(antecedent, implication):
        if implication is None or antecedent is None:
            return None
        formula = implication[2]
        if formula[0] != 'imp' or formula[1] != antecedent[2]:
            return None
        counters['mp_proposals'] += 1
        return node({'rule': 'mp', 'formula': copy.deepcopy(formula[2])}, [antecedent, implication])

    def candidate():
        if target_key not in facts:
            return None
        root = facts[target_key]
        ordered = sorted(proof_nodes(root).values(), key=lambda item: item[0])
        index = {item[0]: row for row, item in enumerate(ordered)}
        commands = []
        for item in ordered:
            ticked()
            command = copy.deepcopy(item[1])
            if command['rule'] == 'mp':
                command.update(antecedent=index[item[3][0][0]], implication=index[item[3][1][0]])
            elif command['rule'] == 'generalize':
                command['source'] = index[item[3][0][0]]
            commands.append(command)
        if not (0 < len(commands) <= 24 and commands[-1]['formula'] == language.target):
            raise ValueError('producer ancestry extraction defect')
        return {'schema': 'shared-bounded-ordinary-word-candidate-v1',
                'binding': copy.deepcopy(language.binding), 'commands': commands,
                'origin': 'untrusted-on-demand-known-fact-search', 'full_word_not_prefix': True}

    def result(found, reason):
        ticked()
        return dict({'schema': 'shared-bounded-ordinary-proposal-v1', 'version': VERSION,
                     'status': 'CANDIDATE_NOT_VERIFIED' if found is not None else 'UNKNOWN',
                     'candidate': found, 'binding': copy.deepcopy(language.binding),
                     'counters': copy.deepcopy(counters), 'search_limits': limits,
                     'incompleteness': {
                         'stop_reason': reason, 'complete_language_enumeration': False,
                         'negative_certificate': False,
                         'parameter_terms': 'input and actually known-fact subterms only, bounded cache',
                         'UI': 'known universals and retained parameter terms only',
                         'transport': 'known oriented equality and known atom; single/all occurrence holes only',
                         'proof_selection': 'one lowest encountered DAG cost per literal formula; no bounded completeness',
                         'word_bound': 24, 'template_cap_per_pair': limits['maximum_atomic_templates_per_pair']},
                     'logical_acceptance': False}, **{key: False for key in STRONG_FLAGS})

    try:
        ticked()
        for formula in list(language.theory['axioms'].values()) + language.gamma + [language.target]:
            add_terms(formula)
        for name in sorted(language.theory['axioms']):
            add(node({'rule': 'axiom', 'name': name,
                      'formula': copy.deepcopy(language.theory['axioms'][name])}, []))
        for index, formula in enumerate(language.gamma):
            add(node({'rule': 'assumption', 'index': index, 'formula': copy.deepcopy(formula)}, []))
        for round_index in range(limits['maximum_rounds']):
            counters['rounds'] = round_index + 1
            found = candidate()
            if found is not None:
                return result(found, 'actual known target ancestry; independent check still required')
            changed = False
            current = sorted(list(facts.values()), key=priority)
            # All existing literal implications, with actual known ordered antecedents.
            for implication in current:
                ticked()
                formula = implication[2]
                if formula[0] != 'imp' or _key(formula[1]) not in facts:
                    continue
                antecedent = facts[_key(formula[1])]
                pair = (antecedent[0], implication[0])
                if pair not in attempted_mp:
                    attempted_mp.add(pair)
                    changed = add(mp(antecedent, implication)) or changed
            # New universals can come from any prior rule, including UG.
            ordered_terms = sorted(terms.values(), key=lambda term: (_size(term), _key(term)))
            for universal in current:
                if universal[2][0] != 'all':
                    continue
                for term in ordered_terms:
                    ticked()
                    pair = (universal[0], _key(term))
                    if pair in attempted_ui:
                        continue
                    attempted_ui.add(pair)
                    counters['ui_proposals'] += 1
                    try:
                        instance = language.substitute(universal[2][2], universal[2][1], term)
                        license_node = node({'rule': 'instantiate', 'universal': copy.deepcopy(universal[2]),
                                             'term': copy.deepcopy(term),
                                             'formula': ['imp', copy.deepcopy(universal[2]), instance]}, [])
                    except outside_language:
                        counters['membership_rejections'] += 1
                        continue
                    changed = add(mp(universal, license_node)) or changed
                    if target_key in facts:
                        return result(candidate(), 'actual known target ancestry; independent check still required')
            current = sorted(list(facts.values()), key=priority)
            equalities = [item for item in current if item[2][0] == 'eq']
            atoms = [item for item in current if item[2][0] in ('eq', 'pred')]
            for equality in equalities:
                left, right = equality[2][1:]
                if left == right:
                    continue
                for atom in atoms:
                    pair = (equality[0], atom[0])
                    if pair in attempted_transport:
                        continue
                    attempted_transport.add(pair)
                    for template in _atomic_templates(atom[2], left, language.hole,
                                                      limits['maximum_atomic_templates_per_pair'], ticked):
                        ticked()
                        counters['transport_proposals'] += 1
                        try:
                            transported = language.substitute(template, language.hole, right)
                            license_node = node({'rule': 'eq_subst', 'variable': language.hole,
                                                 'template': template, 'left': copy.deepcopy(left),
                                                 'right': copy.deepcopy(right), 'formula': ['imp',
                                                 copy.deepcopy(equality[2]), ['imp', copy.deepcopy(atom[2]), transported]]}, [])
                        except outside_language:
                            counters['membership_rejections'] += 1
                            continue
                        intermediate = mp(equality, license_node)
                        changed = add(mp(atom, intermediate)) or changed
            # Whole-formula UG is never an atomic-only rule. Only original parameters.
            for prior in sorted(list(facts.values()), key=priority):
                for variable in language.parameters:
                    ticked()
                    if variable in language.forbidden or variable not in language.free(prior[2]):
                        # Vacuous UG is a permitted primitive but omitted by this heuristic.
                        continue
                    pair = (prior[0], variable)
                    if pair not in attempted_ug:
                        attempted_ug.add(pair)
                        counters['ug_proposals'] += 1
                        changed = add(node({'rule': 'generalize', 'variable': variable,
                                            'formula': ['all', variable, copy.deepcopy(prior[2])]}, [prior])) or changed
            found = candidate()
            if found is not None:
                return result(found, 'actual known target ancestry; independent check still required')
            if not changed:
                break
        else:
            stop = 'maximum_rounds'
    except SearchStopped as error:
        stop = str(error)
    # TimeoutError deliberately propagates: it is unresolved work, never a negative proof.
    return result(None, stop)
