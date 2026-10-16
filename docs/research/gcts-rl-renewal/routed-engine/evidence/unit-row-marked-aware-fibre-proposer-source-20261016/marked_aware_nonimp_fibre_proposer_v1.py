"""Untrusted marked-aware finite non-implication fibre evidence, Source only.

No project imports, clock, saved word, target route or checker delegation.
Caller authenticates original language and injected marked semantics separately.
"""
import hashlib
import json

VERSION = 'unit-row-marked-aware-nonimp-fibre-proposer-v1'
SEMANTICS_VERSION = 'unit-row-channel4-filtered-degree-semantics-v1'
SCOPE = 'Local marked-aware non-implication fibre evidence only; independent checking/global graph/fallback still required.'
FLAGS = ('complete_candidate_graph_accepted', 'scheduler_or_rollback_accepted',
         'logical_proof_accepted', 'ROOT_resource_accepted')


def need(value, reason):
    if not value:
        raise ValueError('marked-aware proposer: ' + reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


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
    need(type(maximum_nodes) is int and 0 <= maximum_nodes <= 44, 'whole formula size bound0..44')
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


def propose_degree(*, language, semantics, state, row, tick):
    """Untrusted full non-implication fibres; count only marked-legal members.

    An owning budget/callback/authority error propagates. Complete degree claims
    require a separately authored checker; a stream or transcript is no authority.
    """
    tick()
    need(semantics.VERSION == SEMANTICS_VERSION, 'exact injected marked point API')
    outside = language.OutsideLanguage
    s, totals, marks, selected, excluded, names = semantics.private_state(language, state, tick)
    base = semantics.base_state(language, s, tick)
    _, bt, bm, bs, be, bn = semantics.base.private_state(language, base, tick)
    need(all(name in names and names[name] == pre for name, pre in bn.items()),
         'both original and decorated full collision ledgers')
    need(type(row) is int and 0 <= row < 24 and totals[(0, row)] == 0,
         'queried unfilled original required row')
    output = marked_formula(marks, row, language, tick)
    earlier = [marked_formula(marks, k, language, tick) for k in range(row)]
    eligible = output is not None and output[0] != 'imp'
    all_assigned = all(f is not None for f in earlier)
    candidates, seen, root_rejections = [], set(), []
    fibres = None
    if eligible:
        nodes = language.formula(output)
        fibres = {'schema': 'unit-row-marked-aware-nonimp-fibres-v1', 'completed': False,
            'output_nodes': nodes, 'MP_antecedent_max_nodes': 43-nodes,
            'assigned_prior_rows': [k for k, f in enumerate(earlier) if f is not None],
            'absent_prior_rows': [k for k, f in enumerate(earlier) if f is None],
            'axiom_labels_seen': [], 'Gamma_occurrences_seen': [],
            'UG_fibres': [], 'ordered_MP_fibres': [],
            'carrier_order': 'size; bot,pred,eq,not,all,imp,and,or; literal names; positive size compositions',
            'carrier_materialized': False, 'independently_accepted': False,
            'UI_EqSubst_excluded_by_nonimp': True}

    def response(complete=False):
        tick()
        return {'schema': 'unit-row-marked-aware-nonimp-fibre-proposal-v1', 'version': VERSION,
            'kind': ('COMPLETE_NONIMP_FIBRE_COVER' if complete else
                     'TWO_LEGAL_WITNESSES' if len(candidates) >= 2 else 'UNKNOWN'),
            'state': s, 'state_sha256': digest(s),
            'original_state': base, 'original_state_sha256': digest(base),
            'input_epoch': s['input_epoch'], 'language_binding': semantics.tree(language.binding, tick),
            'marking_id': s['marking_id'], 'row': row, 'output_formula': output,
            'candidates': candidates, 'root_rejections': root_rejections, 'fibre_cover': fibres,
            'complete_cover_proposed': complete, 'untrusted': True, 'scope': SCOPE,
            **{k: False for k in FLAGS}}

    # The additive integration router keeps the old safe proposer/checker for
    # implication or absent output. This narrow module never calls that path or
    # a checker, and never asserts a complete six-rule cover in these domains.
    if not eligible:
        return response()

    def consider(witness, premises, reads):
        tick()
        pre = {'input_epoch': s['input_epoch'], 'primitive_witness': witness,
               'ordered_premise_formulas': premises, 'ordered_offsets': [k-row for k in reads]}
        transform = [0, row]
        # Catch definite original primitive exclusion ONLY. Errors while checking
        # marking authority or reconstructing decorated data are not exclusions.
        try:
            bare = semantics.base.rebuild_tile(language, pre, transform, tick)
        except outside as error:
            return {'rule': witness['rule'], 'reads': list(reads),
                    'reason': error.reason, 'kind': 'definite_membership_exclusion'}
        semantics.base.check_collision(bare, names)
        tile = semantics.rebuild_tile(language, {'schema': 'unit-row-row0-decorated-type-v1',
            'base_type_preimage': pre, 'marking_id': s['marking_id']}, transform, tick)
        need(canonical(tile['base_tile']) == canonical(bare), 'whole original candidate reconstruction')
        semantics.check_collision(tile, names)
        original_reason = semantics.base.legality(bare, bt, bm, bs, be)
        reason = semantics.legality(tile, totals, marks, selected, excluded)
        need(original_reason is None or reason == original_reason,
             'decorated point test preserves every original restriction')
        if reason is not None:
            return {'rule': witness['rule'], 'reads': list(reads), 'kind': reason,
                    'placement_key': tile['placement_key']}
        key = canonical(tile['placement_key'])
        if key in seen:
            return {'kind': 'duplicate_full_key'}
        seen.add(key)
        candidates.append(semantics.with_obligations(tile, totals, tick))
        return {'kind': 'new_survivor'}

    def stop_two():
        # Preserve the original fully assigned-prefix complete census/MANY path.
        # Missing-prefix early TWO is only a lower bound after full marked tests.
        return not all_assigned and len(candidates) >= 2

    for name, formula in sorted(language.theory['axioms'].items()):
        tick()
        fibres['axiom_labels_seen'].append(name)
        if formula == output:
            result = consider({'rule': 'axiom', 'name': name, 'formula': formula}, [], [])
            if result['kind'] not in ('new_survivor', 'duplicate_full_key'):
                root_rejections.append(result)
            if stop_two():
                return response()
    for index, formula in enumerate(language.gamma):
        tick()
        fibres['Gamma_occurrences_seen'].append(index)
        if formula == output:
            result = consider({'rule': 'assumption', 'index': index, 'formula': formula}, [], [])
            if result['kind'] not in ('new_survivor', 'duplicate_full_key'):
                root_rejections.append(result)
            if stop_two():
                return response()

    def fibre(witnesses, descriptor):
        transcript, decisions = hashlib.sha256(), hashlib.sha256()
        descriptor.update(completed=False, examined=0, new_survivors=0, rejections=0,
            examined_preimages_sha256=transcript.hexdigest(), decisions_sha256=decisions.hexdigest())
        for witness, premises, reads in witnesses:
            tick()
            transcript.update((canonical([witness, premises, reads])+'\n').encode('utf8'))
            result = consider(witness, premises, reads)
            decisions.update((canonical(result)+'\n').encode('utf8'))
            descriptor['examined'] += 1
            descriptor['new_survivors'] += result['kind'] == 'new_survivor'
            descriptor['rejections'] += result['kind'] not in ('new_survivor', 'duplicate_full_key')
            descriptor['examined_preimages_sha256'] = transcript.hexdigest()
            descriptor['decisions_sha256'] = decisions.hexdigest()
            if stop_two():
                return False
        descriptor['completed'] = True
        return True

    for k, marked in enumerate(earlier):
        tick()
        descriptor = {'row': k, 'inverse': 'UG'}
        fibres['UG_fibres'].append(descriptor)
        proposals = ()
        if output[0] == 'all' and (marked is None or marked == output[2]):
            descriptor['case'] = 'missing_or_matching_body'
            proposals = (({'rule': 'generalize', 'variable': output[1], 'formula': output},
                          [output[2]], [k]),)
        else:
            descriptor['case'] = 'not_universal_or_assigned_body_mismatch'
        if not fibre(proposals, descriptor):
            return response()
    for i, left in enumerate(earlier):
        for j, implication in enumerate(earlier):
            tick()
            descriptor = {'rows': [i, j], 'inverse': 'MP'}
            fibres['ordered_MP_fibres'].append(descriptor)
            if i == j:
                descriptor.update(case='FINITE_AST_OCCURS_CHECK_EMPTY',
                    equation=['A', ['imp', 'A', 'C']], positive_output_nodes=fibres['output_nodes'])
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
                maximum = fibres['MP_antecedent_max_nodes']
                proposals = (({'rule': 'mp', 'formula': output},
                    [a, ['imp', a, output]], [i, j]) for a in iter_bounded_formulas(
                        language=language, maximum_nodes=maximum, tick=tick)) if maximum >= 1 else ()
            if not fibre(proposals, descriptor):
                return response()
    tick()
    fibres['completed'] = True
    return response(complete=True)
