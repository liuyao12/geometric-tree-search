"""SOURCE ONLY complete lazy six-rule candidate stream for the fixed unit rows.
EOF proposes completion, never certifies degree; pending reads are not facts.
Original language/state/tick are external and all incomplete work propagates.
"""
import hashlib
import json

VERSION = 'unit-row-complete-lazy-six-rule-fallback-v1'
PORTS = {'axiom': 0, 'assumption': 0, 'instantiate': 0,
         'eq_subst': 0, 'generalize': 1, 'mp': 2}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def clone(value, tick):
    tick()
    if type(value) in (str, int, bool) or value is None:
        return value
    if type(value) is list:
        return [clone(x, tick) for x in value]
    need(type(value) is dict and all(type(k) is str for k in value), 'builtin JSON tree only')
    return {k: clone(v, tick) for k, v in value.items()}


def pairs(raw, tick):
    need(type(raw) is list, 'complete point-value array')
    result = {}
    for entry in raw:
        tick()
        need(type(entry) is list and len(entry) == 2 and type(entry[0]) is list
             and len(entry[0]) == 2 and all(type(x) is int for x in entry[0]), 'literal integer point')
        point = tuple(entry[0])
        need(point not in result, 'duplicate state point')
        result[point] = entry[1]
    return result


def merge(markings, point, value):
    need(point not in markings or canonical(markings[point]) == canonical(value),
         'incompatible internal or selected markings')
    markings[point] = value


def prototype(language, witness, premises, offsets, row, tick):
    """Validate full primitive/ordered offsets and reconstruct unchanged point data."""
    tick()
    need(type(row) is int and 0 <= row < 24 and type(offsets) is list
         and all(type(d) is int and -23 <= d < 0 and 0 <= row+d < row for d in offsets),
         'strict prior nonnegative absolute rows; negative offsets only')
    member = language.primitive(witness, premises)
    need(witness['rule'] in PORTS and len(offsets) == PORTS[witness['rule']] == len(premises),
         'complete ordered physical ports')
    preimage = {'input_epoch': language.binding['language_epoch'],
                'primitive_witness': clone(witness, tick),
                'ordered_premise_formulas': clone(premises, tick),
                'ordered_offsets': list(offsets)}
    key = {'tile_type_id': 'bounded-point-tile-'+digest(preimage),
           'type_preimage': preimage, 'translation': [0, row]}
    local = [[[1, 0], ['formula', canonical(witness['formula'])]]]
    global_marks = [[[1, row], ['formula', canonical(witness['formula'])]]]
    for port, (formula, delta) in enumerate(zip(premises, offsets)):
        tick()
        value = ['formula', canonical(formula)]
        local.extend([[[1, delta], value], [[2+port, 0], ['offset', delta]]])
        global_marks.extend([[[1, row+delta], clone(value, tick)],
                             [[2+port, row], ['offset', delta]]])
    internal = {}
    for point, value in global_marks:
        merge(internal, tuple(point), value)
    return {'placement_key': key, 'selection_record': dict(key, generation=1),
            'local_t_values': [[[0, 0], 1]], 'local_m_values': local,
            'global_t_values': [[[0, row], 1]], 'global_m_values': global_marks,
            'membership': member}


def validate_state(language, state, tick):
    s = clone(state, tick)
    need(type(s) is dict and set(s) == {'schema', 'input_epoch', 'height', 't', 'm',
         'selected', 'excluded', 'generation'} and s['schema'] == 'unit-row-implicit-private-state-v1',
         'whole private state fields')
    epoch = language.binding['language_epoch']
    need(type(s['input_epoch']) is str and s['input_epoch'] == epoch
         and type(s['height']) is int and s['height'] == 24, 'current epoch/original height24')
    totals, marks, generations = pairs(s['t'], tick), pairs(s['m'], tick), pairs(s['generation'], tick)
    points = {(0, r) for r in range(24)}
    need(set(totals) == set(generations) == points
         and all(type(v) is int and v in (0, 1) for v in totals.values())
         and all(type(v) is int and v == 0 for v in generations.values()),
         'whole unit target/root generations; zero is assigned, not absent')
    need(type(s['selected']) is list and type(s['excluded']) is list, 'whole placement/exclusion inventories')
    rebuilt_t = {p: 0 for p in points}
    rebuilt_m = {(1, y): ['outside', epoch] for y in range(-23, 0)}
    rebuilt_m[(1, 23)] = ['formula', canonical(language.target)]
    identities, excluded, prototypes = set(), set(), {}

    def record(raw, selected):
        tick()
        fields = {'tile_type_id', 'type_preimage', 'translation'} | ({'generation'} if selected else set())
        need(type(raw) is dict and set(raw) == fields, 'full placement preimage/translation fields')
        if selected:
            need(type(raw['generation']) is int and raw['generation'] == 1, 'selected tile generation from root0')
        pre, transform = raw['type_preimage'], raw['translation']
        need(type(pre) is dict and set(pre) == {'input_epoch', 'primitive_witness',
             'ordered_premise_formulas', 'ordered_offsets'} and pre['input_epoch'] == epoch
             and type(transform) is list and len(transform) == 2
             and all(type(x) is int for x in transform) and transform[0] == 0,
             'current prototype and integer translation')
        tile = prototype(language, pre['primitive_witness'], pre['ordered_premise_formulas'],
                         pre['ordered_offsets'], transform[1], tick)
        expected = tile['selection_record'] if selected else tile['placement_key']
        need(canonical(raw) == canonical(expected), 'exact full prototype identity, not digest-only')
        name, value = raw['tile_type_id'], canonical(pre)
        need(name not in prototypes or prototypes[name] == value, 'prototype digest/preimage collision')
        prototypes[name] = value
        return tile, canonical(tile['placement_key'])

    for raw in s['selected']:
        tile, key = record(raw, True)
        need(key not in identities, 'selected shared key only once')
        identities.add(key)
        for point, weight in tile['global_t_values']:
            p = tuple(point)
            rebuilt_t[p] += weight
            need(rebuilt_t[p] <= 1, 'selected support overfill')
        for point, value in tile['global_m_values']:
            merge(rebuilt_m, tuple(point), value)
    for raw in s['excluded']:
        tile, key = record(raw, False)
        need(key not in excluded and key not in identities, 'unique branch exclusions disjoint from selected')
        excluded.add(key)
    need(canonical(sorted([[list(k), v] for k, v in totals.items()])) ==
         canonical(sorted([[list(k), v] for k, v in rebuilt_t.items()])), 'whole selected t recomposition')
    need(canonical(sorted([[list(k), v] for k, v in marks.items()])) ==
         canonical(sorted([[list(k), v] for k, v in rebuilt_m.items()])), 'whole fixed-plus-selected m recomposition')
    return s, totals, marks, identities, excluded, prototypes


def marked_formula(markings, row, language, tick):
    point = (1, row)
    if point not in markings:
        return None
    value = markings[point]
    need(type(value) is list and len(value) == 2 and value[0] == 'formula'
         and type(value[1]) is str, 'earlier/output formula marking, not an invented fact')
    def unique(items):
        d = {}
        for k, v in items:
            need(k not in d, 'duplicate formula JSON key')
            d[k] = v
        return d
    def reject(value):
        raise ValueError('no float/nonfinite formula marking')
    tick()
    formula = json.loads(value[1], object_pairs_hook=unique, parse_float=reject, parse_constant=reject)
    need(canonical(formula) == value[1], 'literal canonical formula label')
    language.formula(formula)
    return formula


def iter_syntax(*, language, kind, maximum_nodes, tick):
    """Lazy literal size-ordered carrier; no cache, quotient or partial-body gate."""
    need(kind in ('term', 'formula', 'universal', 'template'), 'declared syntax kind')
    bound = 12 if kind == 'term' else 44
    need(type(maximum_nodes) is int and 1 <= maximum_nodes <= bound, 'literal syntax node bound')
    outside = language.OutsideLanguage
    functions = tuple(sorted(language.theory['functions'].items()))
    predicates = tuple(sorted(language.theory['predicates'].items()))
    binders = tuple(sorted(language.binder_names))
    scope = frozenset(language.parameter_set) | ({language.hole} if kind == 'template' else set())

    def compositions(total, count):
        tick()
        if count == 0:
            if total == 0:
                yield ()
            return
        for first in range(1, total-count+2):
            for rest in compositions(total-first, count-1):
                yield (first,) + rest

    def children(sizes, names, term_children):
        tick()
        if not sizes:
            yield []
            return
        stream = terms if term_children else formulas
        for first in stream(sizes[0], names):
            for rest in children(sizes[1:], names, term_children):
                yield [first] + rest

    def terms(size, names):
        tick()
        if not 1 <= size <= 12:
            return
        if size == 1:
            for name in sorted(names):
                tick()
                yield ['var', name]
        for name, arity in functions:
            for sizes in compositions(size-1, arity):
                for args in children(sizes, names, True):
                    tick()
                    yield ['fun', name, args]

    def formulas(size, names):
        tick()
        if size == 1:
            yield ['bot']
        for name, arity in predicates:
            for sizes in compositions(size-1, arity):
                for args in children(sizes, names, True):
                    tick()
                    yield ['pred', name, args]
        for sizes in compositions(size-1, 2):
            for args in children(sizes, names, True):
                tick()
                yield ['eq', args[0], args[1]]
        if size >= 2:
            for body in formulas(size-1, names):
                tick()
                yield ['not', body]
            for name in binders:
                for body in formulas(size-1, names | {name}):
                    tick()
                    yield ['all', name, body]
        for tag in ('imp', 'and', 'or'):
            for sizes in compositions(size-1, 2):
                for args in children(sizes, names, False):
                    tick()
                    yield [tag, args[0], args[1]]

    def roots(size):
        if kind == 'term':
            yield from terms(size, scope)
        elif kind == 'formula':
            yield from formulas(size, scope)
        elif kind == 'universal':
            if size >= 2:
                for name in binders:
                    for body in formulas(size-1, scope | {name}):
                        tick()
                        yield ['all', name, body]
        else:
            for name, arity in predicates:
                for sizes in compositions(size-1, arity):
                    for args in children(sizes, scope, True):
                        tick()
                        yield ['pred', name, args]
            for sizes in compositions(size-1, 2):
                for args in children(sizes, scope, True):
                    tick()
                    yield ['eq', args[0], args[1]]

    validator = language.term if kind == 'term' else language.template if kind == 'template' else language.formula
    for size in range(1, maximum_nodes+1):
        for value in roots(size):
            tick()
            try:
                actual_size = validator(value)
            except outside:
                continue
            need(actual_size == size, 'complete literal constructor-size agreement')
            yield value


RULE_ORDER = ('axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize')


def _legal_reason(tile, totals, marks, selected, excluded):
    key = canonical(tile['placement_key'])
    if key in selected:
        return 'already_selected'
    if key in excluded:
        return 'branch_excluded_complete_key'
    if any(totals.get(tuple(p), 1)+v > 1 for p, v in tile['global_t_values']):
        return 'whole_support_capacity'
    if any(tuple(p) in marks and canonical(marks[tuple(p)]) != canonical(v)
           for p, v in tile['global_m_values']):
        return 'whole_remote_or_metadata_mark_conflict'
    return None


def _all_candidates(language, snapshot, row, tick):
    s, totals, marks, selected, excluded, names = validate_state(language, snapshot, tick)
    need(type(row) is int and 0 <= row < 24 and totals[(0, row)] == 0, 'queried unfilled required row')
    output = marked_formula(marks, row, language, tick)
    prior = [marked_formula(marks, k, language, tick) for k in range(row)]
    outside = language.OutsideLanguage
    stats = {'attempts_by_rule': {k: 0 for k in RULE_ORDER}, 'membership_exclusions': 0,
             'point_rejections': 0, 'MP_same_row_occurs_empty': 0, 'yielded_candidates': 0}

    def formulas(maximum):
        if maximum >= 1:
            yield from iter_syntax(language=language, kind='formula', maximum_nodes=maximum, tick=tick)

    def terms():
        yield from iter_syntax(language=language, kind='term', maximum_nodes=12, tick=tick)

    def descriptors(rule):
        if rule == 'axiom':
            for name, formula in sorted(language.theory['axioms'].items()):
                tick()
                if output is None or formula == output:
                    yield {'rule': rule, 'name': name, 'formula': formula}, [], []
        elif rule == 'assumption':
            for index, formula in enumerate(language.gamma):
                tick()
                if output is None or formula == output:
                    yield {'rule': rule, 'index': index, 'formula': formula}, [], []
        elif rule == 'instantiate':
            if output is None:
                universals = iter_syntax(language=language, kind='universal', maximum_nodes=42, tick=tick)
            elif output[0] == 'imp' and output[1][0] == 'all':
                universals = (output[1],)
            else:
                universals = ()
            for universal in universals:
                for term in terms():
                    tick()
                    try:
                        instance = language.substitute(universal[2], universal[1], term)
                    except outside:
                        yield None
                        continue
                    formula = ['imp', universal, instance]
                    yield {'rule': rule, 'universal': universal, 'term': term, 'formula': formula}, [], []
        elif rule == 'eq_subst':
            fixed = output is not None
            shape = fixed and output[0] == 'imp' and output[1][0] == 'eq' and output[2][0] == 'imp'
            lefts = (output[1][1],) if shape else terms() if not fixed else ()
            for left in lefts:
                rights = (output[1][2],) if shape else terms()
                for right in rights:
                    tick()
                    if shape:
                        maximum = min(language.formula(output[2][1]), language.formula(output[2][2]))
                    else:
                        maximum = (44-3-language.term(left)-language.term(right))//2
                    if maximum < 1:
                        continue
                    for template in iter_syntax(language=language, kind='template', maximum_nodes=maximum, tick=tick):
                        tick()
                        try:
                            a = language.substitute(template, language.hole, left)
                            b = language.substitute(template, language.hole, right)
                        except outside:
                            yield None
                            continue
                        formula = ['imp', ['eq', left, right], ['imp', a, b]]
                        yield {'rule': rule, 'variable': language.hole, 'template': template,
                               'left': left, 'right': right, 'formula': formula}, [], []
        elif rule == 'mp':
            for i, a in enumerate(prior):
                for j, implication in enumerate(prior):
                    tick()
                    if i == j:
                        stats['MP_same_row_occurs_empty'] += 1
                        continue
                    if implication is not None:
                        if implication[0] != 'imp' or (a is not None and a != implication[1]):
                            continue
                        antecedent, conclusion = implication[1], implication[2]
                        if output is None or output == conclusion:
                            yield {'rule': rule, 'formula': conclusion}, [antecedent, implication], [i, j]
                    elif a is not None:
                        conclusions = (output,) if output is not None else formulas(43-language.formula(a))
                        for conclusion in conclusions:
                            yield {'rule': rule, 'formula': conclusion}, [a, ['imp', a, conclusion]], [i, j]
                    else:
                        conclusions = (output,) if output is not None else formulas(42)
                        for conclusion in conclusions:
                            for antecedent in formulas(43-language.formula(conclusion)):
                                yield {'rule': rule, 'formula': conclusion}, [antecedent, ['imp', antecedent, conclusion]], [i, j]
        else:
            for variable in language.parameters:
                tick()
                if variable in language.forbidden or (output is not None and (output[0] != 'all' or output[1] != variable)):
                    continue
                for k, marked in enumerate(prior):
                    if output is not None:
                        bodies = (output[2],) if marked is None or marked == output[2] else ()
                    else:
                        bodies = (marked,) if marked is not None else formulas(43)
                    for body in bodies:
                        tick()
                        yield {'rule': rule, 'variable': variable, 'formula': ['all', variable, body]}, [body], [k]
        return ('RULE_COMPLETE', rule)

    streams = [(rule, descriptors(rule)) for rule in RULE_ORDER]
    completed = []
    while streams:
        remaining = []
        for rule, stream in streams:
            tick()
            try:
                descriptor = next(stream)
            except StopIteration as stopped:
                need(stopped.value == ('RULE_COMPLETE', rule), 'unfinished rule stream is not EOF')
                completed.append(rule)
                continue
            remaining.append((rule, stream))
            stats['attempts_by_rule'][rule] += 1
            if descriptor is None:
                stats['membership_exclusions'] += 1
                continue
            witness, premises, reads = descriptor
            try:
                tile = prototype(language, witness, premises, [k-row for k in reads], row, tick)
            except outside:
                stats['membership_exclusions'] += 1
                continue
            key = tile['placement_key']
            name, preimage = key['tile_type_id'], canonical(key['type_preimage'])
            need(name not in names or names[name] == preimage, 'current-state prototype digest/preimage collision')
            if _legal_reason(tile, totals, marks, selected, excluded) is not None:
                stats['point_rejections'] += 1
                continue
            tile['read_obligations'] = [{'row': k, 'formula': clone(f, tick),
                'occupied': totals[(0, k)] == 1, 'fact_accepted': False} for k, f in zip(reads, premises)]
            stats['yielded_candidates'] += 1
            yield tile
        streams = remaining
    tick()
    need(len(completed) == 6 and set(completed) == set(RULE_ORDER), 'all six complete rule streams')
    return {'marker': 'ALL_SIX_COMPLETE', 'rules_completed': list(RULE_ORDER), 'stats': stats}


class FallbackCursor:
    """Untrusted state-bound stream. Errors/abort can never become normal EOF."""
    def __init__(self, *, language, state, row, tick):
        self._tick, self._failed, self._done = tick, False, False
        self._yielded, self._completion = 0, None
        s, totals, _, _, _, _ = validate_state(language, state, tick)
        need(type(row) is int and 0 <= row < 24 and totals[(0, row)] == 0, 'queried unfilled required row')
        context = {'schema': 'unit-row-all-six-fallback-context-v1', 'version': VERSION,
            'input_epoch': s['input_epoch'], 'language_binding': clone(language.binding, tick),
            'row': row, 'state': s, 'state_sha256': digest(s)}
        context['context_sha256'] = digest(context)
        self._context = context
        self._stream = _all_candidates(language, s, row, tick)

    def context(self):
        if self._failed:
            raise RuntimeError('fallback cursor failed/aborted')
        try:
            return clone(self._context, self._tick)
        except BaseException:
            self._failed = True
            raise

    def abort(self):
        self._failed = True
        self._stream.close()

    def advance(self):
        if self._failed:
            raise RuntimeError('fallback cursor failed/aborted; completion unavailable')
        try:
            self._tick()
            if not self._done:
                try:
                    candidate = next(self._stream)
                except StopIteration as stopped:
                    token = stopped.value
                    need(type(token) is dict and token.get('marker') == 'ALL_SIX_COMPLETE'
                         and token.get('rules_completed') == list(RULE_ORDER)
                         and token['stats']['yielded_candidates'] == self._yielded,
                         'closed/failed stream is not completed generator EOF')
                    completion = {'schema': 'unit-row-all-six-fallback-completion-v1',
                        'version': VERSION, 'context_sha256': self._context['context_sha256'],
                        'state_sha256': self._context['state_sha256'], 'input_epoch': self._context['input_epoch'],
                        'row': self._context['row'], 'yielded_candidates': self._yielded,
                        'rules_completed': token['rules_completed'], 'stats': token['stats'],
                        'complete_fallback_proposed': True, 'independently_checked': False,
                        'degree_zero_or_singleton_accepted': False, 'complete_candidate_graph_accepted': False,
                        'scheduler_or_rollback_accepted': False, 'logical_proof_accepted': False,
                        'ROOT_resource_accepted': False}
                    self._completion = clone(completion, self._tick)
                    self._tick()
                    self._done = True
                else:
                    event = {'schema': 'unit-row-all-six-fallback-event-v1', 'kind': 'CANDIDATE',
                        'context_sha256': self._context['context_sha256'], 'ordinal': self._yielded,
                        'candidate': candidate, 'independently_checked': False}
                    self._yielded += 1
                    return clone(event, self._tick)
            return {'schema': 'unit-row-all-six-fallback-event-v1', 'kind': 'EOF',
                'context_sha256': self._context['context_sha256'],
                'completion': clone(self._completion, self._tick)}
        except BaseException:
            self._failed = True
            raise


def open_fallback(*, language, state, row, tick):
    return FallbackCursor(language=language, state=state, row=row, tick=tick)
