"""Independent matcher payload and complete order reconstruction.

No producer matcher, ForwardOrder, controller, graph or decoder import. Literal
pair outcomes are independently computed by the pinned tree oracle; a separate
iterative scan reconstructs the declared diagnostic/export schema.
"""
import copy
import hashlib
import json
from literal_receptor_oracle_v2 import literal_match

BUCKET = {'match': 0, 'neutral': 1, 'nonmatch': 2}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def first_reason(value, slots):
    todo = [('formula', value)]
    while todo:
        kind, node = todo.pop()
        if type(node) is not list or not node:
            return 'unsupported-' + ('term' if kind == 'term' else 'formula') + '-shape'
        tag = node[0]
        if kind == 'term':
            if tag == 'var':
                if len(node) != 2 or type(node[1]) is not str or not node[1]:
                    return 'unsupported-variable-shape'
                if node[1] not in slots:
                    return 'free-or-out-of-scope-variable'
            else:
                if tag != 'fun' or len(node) != 3 or type(node[1]) is not str or not node[1] or type(node[2]) is not list:
                    return 'unsupported-term-constructor'
                todo.extend(('term', a) for a in reversed(node[2]))
        elif tag == 'all':
            return 'quantified-formula-outside-scope'
        elif tag == 'bot':
            if len(node) != 1:
                return 'unsupported-bottom-shape'
        elif tag == 'pred':
            if len(node) != 3 or type(node[1]) is not str or not node[1] or type(node[2]) is not list:
                return 'unsupported-predicate-shape'
            todo.extend(('term', a) for a in reversed(node[2]))
        elif tag == 'eq':
            if len(node) != 3:
                return 'unsupported-equality-shape'
            todo.extend([('term', node[2]), ('term', node[1])])
        elif tag == 'not':
            if len(node) != 2:
                return 'unsupported-negation-shape'
            todo.append(('formula', node[1]))
        elif tag in ('and', 'imp'):
            if len(node) != 3:
                return 'unsupported-connective-shape'
            todo.extend([('formula', node[2]), ('formula', node[1])])
        else:
            return 'unsupported-formula-constructor'
    return None


def pattern_record(recipe):
    witness, premises = recipe['witness'], recipe['premises']
    rule, out = witness.get('rule'), witness.get('formula')
    source = 'mp-ordered-antecedent' if rule == 'mp' else ('instantiate-consequent' if rule == 'instantiate' else str(rule))
    def neutral(reason):
        return dict(schema='literal-receptor-pattern-v1', source=source, status='neutral',
                    reason=reason, prefix_binders=[], guard=None)
    binders = []
    if rule == 'mp':
        if len(premises) != 2 or premises[1] != ['imp', premises[0], out]:
            return neutral('unsupported-ordered-MP-interface')
        guard = premises[0]
    elif rule == 'instantiate':
        if type(out) is not list or len(out) != 3 or out[0] != 'imp' or out[1] != witness.get('universal'):
            return neutral('unsupported-instantiation-interface')
        residual = out[2]
        while type(residual) is list and residual and residual[0] == 'all':
            if len(residual) != 3 or type(residual[1]) is not str or not residual[1]:
                return neutral('unsupported-prefix-binder-shape')
            binders.append(residual[1])
            residual = residual[2]
        if len(binders) != len(set(binders)):
            return neutral('repeated-or-shadowed-prefix-binder')
        if type(residual) is not list or len(residual) != 3 or residual[0] != 'imp':
            return neutral('no-immediate-implication-guard')
        guard = residual[1]
    else:
        return neutral('rule-outside-matching-scope')
    reason = first_reason(guard, set(binders))
    return dict(schema='literal-receptor-pattern-v1', source=source,
                status='supported' if reason is None else 'neutral', reason=reason,
                prefix_binders=binders, guard=copy.deepcopy(guard))


def pair_record(pattern, recipient):
    if pattern['status'] != 'supported':
        return dict(status='neutral', bucket=1, bindings={}, reason=pattern['reason'] or 'unsupported-pattern')
    reason = first_reason(recipient, set())
    if reason is not None:
        return dict(status='neutral', bucket=1, bindings={}, reason=reason)
    semantic = literal_match(dict(status='supported', slots=pattern['prefix_binders'], guard=pattern['guard']), recipient)
    assignments, reasons = {}, []
    pending = [('formula', pattern['guard'], recipient)]
    while pending:
        kind, p, r = pending.pop()
        if kind == 'term':
            if p[0] == 'var':
                if r[0] != 'fun' or r[2]:
                    reasons.append('unsupported-compound-slot-image')
                elif p[1] in assignments and assignments[p[1]] != r:
                    reasons.append('inconsistent-repeated-slot-image')
                else:
                    assignments[p[1]] = copy.deepcopy(r)
            elif p[0] != r[0] or p[1] != r[1] or len(p[2]) != len(r[2]):
                reasons.append('literal-term-constructor-symbol-or-arity-mismatch')
            else:
                pending.extend(('term', a, b) for a, b in reversed(list(zip(p[2], r[2]))))
        elif p[0] != r[0]:
            reasons.append('literal-formula-constructor-or-polarity-mismatch')
        elif p[0] == 'pred':
            if p[1] != r[1] or len(p[2]) != len(r[2]):
                reasons.append('literal-predicate-symbol-or-arity-mismatch')
            else:
                pending.extend(('term', a, b) for a, b in reversed(list(zip(p[2], r[2]))))
        elif p[0] == 'eq':
            pending.extend([('term', p[2], r[2]), ('term', p[1], r[1])])
        elif p[0] == 'not':
            pending.append(('formula', p[1], r[1]))
        elif p[0] in ('and', 'imp'):
            pending.extend([('formula', p[2], r[2]), ('formula', p[1], r[1])])
    definite = any(v != 'unsupported-compound-slot-image' for v in reasons)
    status = 'nonmatch' if definite else ('neutral' if reasons else 'match')
    if status != semantic['status'] or (status == 'match' and assignments != semantic['bindings']):
        raise ValueError('independent tree outcome and iterative export scan disagree')
    return dict(status=status, bucket=BUCKET[status], bindings=assignments if status == 'match' else {},
                reason=None if status == 'match' else sorted(set(reasons)),
                interpretation='literal structural advice, not inference or candidate legality')


def feature_record(pattern, selected):
    comparisons = []
    if pattern['status'] == 'supported':
        for value in selected:
            comparisons.append(dict(key=copy.deepcopy(value['key']), formula_code=value['formula_code'],
                                    **pair_record(pattern, value['formula'])))
    matches = [v for v in comparisons if v['status'] == 'match']
    status = 'match' if matches else ('nonmatch' if any(v['status'] == 'nonmatch' for v in comparisons) else 'neutral')
    return dict(status=status, bucket=BUCKET[status], pattern_status=pattern['status'],
                pattern_reason=pattern['reason'], comparisons=comparisons, matches=matches,
                scope='supported selected output subset only; nonmatch does not mean impossible')


def ast_size(node):
    if type(node) is not list:
        return 0
    tag = node[0]
    if tag in ('var', 'bot'):
        return 1
    if tag in ('fun', 'pred'):
        return 1 + sum(ast_size(v) for v in node[2])
    if tag == 'all':
        return 1 + ast_size(node[2])
    return 1 + sum(ast_size(v) for v in node[1:])


def stream_sha(keys):
    tape = '\n'.join(canonical([k[0], k[1], list(k[2])]) for k in keys) + '\n'
    return hashlib.sha256(tape.encode()).hexdigest()


def reconstruct_order(state, formulas, choice, mode):
    keys = list(state.candidates(choice[1]))
    if len(keys) != choice[2] or len(keys) != len(set(keys)):
        raise ValueError('complete distinct independent chosen-point domain required')
    if choice[0] == 'forced':
        return keys, keys, None, []
    if choice[0] != 'branch' or mode not in ('fixed-forward', 'fixed-forward-receptor'):
        raise ValueError('unchanged branch scheduler and declared mode required')
    selected = [dict(key=[k[0], k[1], list(k[2])], formula_code=state.recipes[k[0]]['output'],
                     formula=formulas[state.recipes[k[0]]['output']]) for k in state.selected]
    selected_outputs = {v['formula_code'] for v in selected}
    selected_rows = {k[1] for k in state.selected}
    index = {canonical(f): i for i, f in enumerate(formulas)}
    features = {}
    if mode == 'fixed-forward-receptor':
        features = {i: feature_record(pattern_record(state.recipes[i]), selected) for i in sorted({k[0] for k in keys})}
    scores = []
    for k in keys:
        recipe, witness = state.recipes[k[0]], state.recipes[k[0]]['witness']
        rule = witness['rule']
        universal = index.get(canonical(witness['universal'])) if rule == 'instantiate' else None
        equality = index.get(canonical(witness['formula'][1])) if rule == 'eq_subst' else None
        antecedent = index.get(canonical(witness['formula'][2][1])) if rule == 'eq_subst' else None
        if recipe['output'] in selected_outputs: tier = 6
        elif rule == 'mp' and all(r in selected_rows for r in k[2]): tier = 0
        elif rule == 'instantiate' and universal in selected_outputs: tier = 1
        elif rule == 'eq_subst' and equality in selected_outputs and antecedent in selected_outputs: tier = 2
        elif rule == 'axiom': tier = 3
        elif rule == 'eq_subst' and equality in selected_outputs: tier = 4
        else: tier = 5
        score = (tier,) + ((features[k[0]]['bucket'],) if features else ()) + (ast_size(witness['formula']), canonical(witness), k[0], k[2])
        scores.append((score, k))
    scores.sort(key=lambda item: item[0])
    ordered = [k for score, k in scores]
    if len(ordered) != len(keys) or set(ordered) != set(keys):
        raise ValueError('full unchanged fallback permutation')
    trace = None
    if features:
        h = hashlib.sha256()
        for score, k in scores:
            h.update((canonical(dict(key=[k[0], k[1], list(k[2])], score=score)) + '\n').encode())
        compact = []
        for i in sorted(features):
            feature = features[i]
            compact.append(dict(recipe=i, **{field: feature[field] for field in ('status', 'bucket', 'pattern_status', 'pattern_reason', 'matches', 'scope')},
                comparison_count=len(feature['comparisons']),
                comparison_label_counts={label: sum(v['status'] == label for v in feature['comparisons']) for label in BUCKET},
                complete_comparisons_sha256=hashlib.sha256(canonical(feature['comparisons']).encode()).hexdigest()))
        trace = dict(schema='literal-receptor-order-trace-v1',
            selected_output_constraints=[dict(key=v['key'], formula_code=v['formula_code']) for v in selected],
            recipe_features=compact, complete_score_stream_sha256=h.hexdigest(), complete_keys=len(keys),
            score_contract='(unchanged readiness tier, match bucket, original size/witness/recipe/refs)',
            match_bucket_order=BUCKET,
            interpretation='selected structural constraints may have pending ordered sources; no proof claim')
    return keys, ordered, trace, list(features.values())
