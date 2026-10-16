"""SOURCE ONLY local degree proposals. Pending reads are obligations, not facts.
Whole private state/language/tick are external; incomplete work propagates.
"""
import hashlib
import json

VERSION = 'unit-row-implicit-degree-evidence-v3-missing-marks'
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


def iter_bounded_formulas(*, language, maximum_nodes, tick):
    """Lazy literal size-ordered carrier; no cache, quotient or partial-body gate."""
    need(type(maximum_nodes) is int and 1 <= maximum_nodes <= 44, 'whole formula size bound1..44')
    outside = language.OutsideLanguage
    functions = tuple(sorted(language.theory['functions'].items()))
    predicates = tuple(sorted(language.theory['predicates'].items()))
    binders = tuple(sorted(language.binder_names))
    scope = frozenset(language.parameter_set)

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

    for size in range(1, maximum_nodes+1):
        for formula in formulas(size, scope):
            tick()
            try:
                actual_size = language.formula(formula)
            except outside:
                continue
            need(actual_size == size, 'complete literal constructor-size agreement')
            yield formula


def propose_degree(*, language, state, row, tick):
    """Return two legal witnesses, an untrusted restricted cover, or UNKNOWN.

    Callback/typing budgets propagate. No zero/singleton decision, graph update,
    pruning, placement, branch preference or rollback is performed by this API.
    """
    outside = language.OutsideLanguage
    s, totals, marks, selected, excluded, prototypes = validate_state(language, state, tick)
    need(type(row) is int and 0 <= row < 24 and totals[(0, row)] == 0, 'queried unfilled required row')
    output = marked_formula(marks, row, language, tick)
    earlier = [marked_formula(marks, r, language, tick) for r in range(row)]
    cover = output is not None and output[0] != 'imp' and all(f is not None for f in earlier)
    missing_cover = output is not None and output[0] != 'imp' and not cover
    missing_complete = False
    fibre_cover = None
    if missing_cover:
        output_nodes = language.formula(output)
        fibre_cover = {'schema': 'unit-row-missing-mark-fibres-v1', 'completed': False,
            'output_nodes': output_nodes, 'MP_antecedent_max_nodes': 43-output_nodes,
            'assigned_prior_rows': [k for k, f in enumerate(earlier) if f is not None],
            'absent_prior_rows': [k for k, f in enumerate(earlier) if f is None],
            'axiom_labels_seen': [], 'Gamma_occurrences_seen': [],
            'UG_fibres': [], 'ordered_MP_fibres': [],
            'carrier_order': 'size; bot,pred,eq,not,all,imp,and,or; literal names; positive size compositions',
            'carrier_materialized': False, 'independently_accepted': False}
    candidates, seen, rejections = [], set(), []
    coverage = {'axiom_labels_seen': [], 'Gamma_occurrences_seen': [],
                'UG_prior_rows_seen': [], 'ordered_MP_pairs_seen': []}

    def consider(witness, premises, reads, retain_rejection=True):
        tick()
        try:
            tile = prototype(language, witness, premises, [r-row for r in reads], row, tick)
        except outside as error:
            result = {'rule': witness['rule'], 'reads': list(reads),
                      'reason': error.reason, 'kind': 'definite_membership_exclusion'}
            if retain_rejection:
                rejections.append(result)
            return result
        key = canonical(tile['placement_key'])
        name = tile['placement_key']['tile_type_id']
        pre = canonical(tile['placement_key']['type_preimage'])
        need(name not in prototypes or prototypes[name] == pre, 'prototype digest/preimage collision')
        # Full preimage is identity. Do not cache a carrier of rejected keys.
        if not missing_cover:
            prototypes[name] = pre
        reason = None
        if key in selected:
            reason = 'already_selected'
        elif key in excluded:
            reason = 'branch_excluded_complete_key'
        elif any(totals.get(tuple(p), 1)+v > 1 for p, v in tile['global_t_values']):
            reason = 'whole_support_capacity'
        elif any(tuple(p) in marks and canonical(marks[tuple(p)]) != canonical(v)
                 for p, v in tile['global_m_values']):
            reason = 'whole_remote_or_metadata_mark_conflict'
        if reason:
            result = {'rule': witness['rule'], 'reads': list(reads), 'kind': reason,
                      'placement_key': tile['placement_key']}
            if retain_rejection:
                rejections.append(result)
            return result
        if key not in seen:
            seen.add(key)
            prototypes[name] = pre
            tile['read_obligations'] = [{'row': r, 'formula': clone(f, tick),
                 'occupied': totals[(0, r)] == 1, 'fact_accepted': False} for r, f in zip(reads, premises)]
            candidates.append(tile)
            return {'kind': 'new_survivor'}
        return {'kind': 'duplicate_full_key'}

    def finished():
        return not cover and len(candidates) >= 2

    def response():
        tick()
        kind = ('NON_IMP_ASSIGNED_PREFIX_COVER' if cover else
                'NON_IMP_MISSING_MARK_COVER' if missing_complete else
                'TWO_LEGAL_WITNESSES' if len(candidates) >= 2 else 'UNKNOWN')
        return {'schema': 'unit-row-degree-evidence-proposal-v2', 'version': VERSION,
                'kind': kind, 'state': s, 'state_sha256': digest(s),
                'input_epoch': s['input_epoch'], 'language_binding': clone(language.binding, tick),
                'row': row, 'candidates': candidates if cover else candidates[:2],
                'coverage': coverage if cover else None, 'rejections': rejections,
                'complete_cover_proposed': cover or missing_complete, 'fibre_cover': fibre_cover, 'untrusted': True,
                'degree_zero_or_singleton_accepted': False, 'degree_ge_two_accepted': False,
                'complete_candidate_graph_accepted': False, 'scheduler_or_rollback_accepted': False,
                'logical_proof_accepted': False, 'ROOT_resource_accepted': False,
                'scope': 'Local evidence only; independent checker/global graph/fallback still required.'}

    for name, formula in sorted(language.theory['axioms'].items()):
        tick()
        if cover:
            coverage['axiom_labels_seen'].append(name)
        if missing_cover:
            fibre_cover['axiom_labels_seen'].append(name)
        if output is None or formula == output:
            consider({'rule': 'axiom', 'name': name, 'formula': formula}, [], [])
            if finished():
                return response()
    for index, formula in enumerate(language.gamma):
        tick()
        if cover:
            coverage['Gamma_occurrences_seen'].append(index)
        if missing_cover:
            fibre_cover['Gamma_occurrences_seen'].append(index)
        if output is None or formula == output:
            consider({'rule': 'assumption', 'index': index, 'formula': formula}, [], [])
            if finished():
                return response()
    if missing_cover:
        def fibre(witnesses, descriptor):
            examined, rejected, legal_before = 0, 0, len(candidates)
            transcript, decisions = hashlib.sha256(), hashlib.sha256()
            for witness, premises, reads in witnesses:
                tick()
                transcript.update((canonical([witness, premises, reads])+'\n').encode('utf8'))
                examined += 1
                result = consider(witness, premises, reads, False)
                decisions.update((canonical(result)+'\n').encode('utf8'))
                rejected += result['kind'] not in ('new_survivor', 'duplicate_full_key')
                if finished():
                    return False
            descriptor.update(completed=True, examined=examined,
                new_survivors=len(candidates)-legal_before, rejections=rejected,
                examined_preimages_sha256=transcript.hexdigest(),
                decisions_sha256=decisions.hexdigest())
            return True

        for k, marked in enumerate(earlier):
            tick()
            descriptor = {'row': k, 'inverse': 'UG', 'completed': False}
            fibre_cover['UG_fibres'].append(descriptor)
            proposals = ()
            if output[0] == 'all' and (marked is None or marked == output[2]):
                proposals = (({'rule': 'generalize', 'variable': output[1],
                              'formula': output}, [output[2]], [k]),)
                descriptor['case'] = 'missing_or_matching_body'
            else:
                descriptor['case'] = 'not_universal_or_assigned_body_mismatch'
            if not fibre(proposals, descriptor):
                return response()
        for i, left in enumerate(earlier):
            for j, implication in enumerate(earlier):
                tick()
                descriptor = {'rows': [i, j], 'inverse': 'MP', 'completed': False}
                fibre_cover['ordered_MP_fibres'].append(descriptor)
                if i == j:
                    descriptor.update(case='FINITE_AST_OCCURS_CHECK_EMPTY',
                        equation=['A', ['imp', 'A', 'C']], positive_output_nodes=output_nodes)
                    proposals = ()
                elif left is not None:
                    descriptor['case'] = 'antecedent_assigned'
                    required = ['imp', left, output]
                    proposals = (({'rule': 'mp', 'formula': output}, [left, required], [i, j]),) if implication is None or implication == required else ()
                elif implication is not None:
                    descriptor['case'] = 'only_implication_assigned'
                    proposals = (({'rule': 'mp', 'formula': output}, [implication[1], implication], [i, j]),) if implication[0] == 'imp' and implication[2] == output else ()
                else:
                    descriptor['case'] = 'both_absent_full_scoped_carrier'
                    maximum = fibre_cover['MP_antecedent_max_nodes']
                    proposals = (({'rule': 'mp', 'formula': output},
                                  [a, ['imp', a, output]], [i, j])
                        for a in iter_bounded_formulas(language=language,
                            maximum_nodes=maximum, tick=tick)) if maximum >= 1 else ()
                if not fibre(proposals, descriptor):
                    return response()
        tick()
        missing_complete = True
        fibre_cover['completed'] = True
        return response()

    for r, formula in enumerate(earlier):
        tick()
        if cover and output[0] == 'all':
            coverage['UG_prior_rows_seen'].append(r)
        if not cover and output is not None and output[0] == 'all':
            formula = output[2]
        if formula is None:
            continue
        for variable in language.parameters:
            conclusion = ['all', variable, formula]
            if output is None or conclusion == output:
                consider({'rule': 'generalize', 'variable': variable, 'formula': conclusion}, [formula], [r])
                if finished():
                    return response()
    for i, left in enumerate(earlier):
        for j, implication in enumerate(earlier):
            tick()
            if cover:
                coverage['ordered_MP_pairs_seen'].append([i, j])
            if left is None:
                continue
            if implication is None:
                if output is None:
                    continue
                conclusion, premise = output, ['imp', left, output]
            elif implication[0] == 'imp' and implication[1] == left:
                conclusion, premise = implication[2], implication
                if output is not None and conclusion != output:
                    continue
            else:
                continue
            consider({'rule': 'mp', 'formula': conclusion}, [left, premise], [i, j])
            if finished():
                return response()
    # UI/transport licences have outer imp; other incomplete queries stay UNKNOWN.
    return response()
