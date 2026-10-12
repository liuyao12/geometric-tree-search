"""Literal AST receptor advice; no logic oracle, engine, model or target lookup.

Only a pattern slot's image is restricted to a closed nullary function. Literal
compound constructors are compared recursively. Selected outputs are structural
constraints, possibly with pending dependencies, never asserted derived facts.
"""
import copy
import hashlib
import json
import time
from shared_symbolic_forward_order_v1 import ForwardOrder, canonical

BUCKET = {'match': 0, 'neutral': 1, 'nonmatch': 2}
SCHEMA = 'literal-receptor-pattern-v1'


def _term_reason(term, slots):
    if not isinstance(term, list) or not term:
        return 'unsupported-term-shape'
    if term[0] == 'var':
        if len(term) != 2 or not isinstance(term[1], str) or not term[1]:
            return 'unsupported-variable-shape'
        return None if term[1] in slots else 'free-or-out-of-scope-variable'
    if (term[0] != 'fun' or len(term) != 3 or not isinstance(term[1], str) or not term[1]
            or not isinstance(term[2], list)):
        return 'unsupported-term-constructor'
    for item in term[2]:
        reason = _term_reason(item, slots)
        if reason is not None:
            return reason
    return None


def _formula_reason(formula, slots):
    if not isinstance(formula, list) or not formula:
        return 'unsupported-formula-shape'
    tag = formula[0]
    if tag == 'all':
        return 'quantified-formula-outside-scope'
    if tag == 'bot':
        return None if len(formula) == 1 else 'unsupported-bottom-shape'
    if tag == 'pred':
        if (len(formula) != 3 or not isinstance(formula[1], str) or not formula[1]
                or not isinstance(formula[2], list)):
            return 'unsupported-predicate-shape'
        for item in formula[2]:
            reason = _term_reason(item, slots)
            if reason is not None:
                return reason
        return None
    if tag == 'eq':
        if len(formula) != 3:
            return 'unsupported-equality-shape'
        return _term_reason(formula[1], slots) or _term_reason(formula[2], slots)
    if tag == 'not':
        return (_formula_reason(formula[1], slots) if len(formula) == 2
                else 'unsupported-negation-shape')
    if tag in ('and', 'imp'):
        if len(formula) != 3:
            return 'unsupported-connective-shape'
        return _formula_reason(formula[1], slots) or _formula_reason(formula[2], slots)
    return 'unsupported-formula-constructor'


def pattern_from_guard(guard, binders=(), *, source='synthetic'):
    """A pure pattern constructor, also the public synthetic-corpus API."""
    names = list(binders)
    reason = None
    if any(not isinstance(name, str) or not name for name in names):
        reason = 'unsupported-prefix-binder-shape'
    elif len(names) != len(set(names)):
        reason = 'repeated-or-shadowed-prefix-binder'
    else:
        reason = _formula_reason(guard, set(names))
    return {'schema': SCHEMA, 'source': source,
            'status': 'supported' if reason is None else 'neutral',
            'reason': reason, 'prefix_binders': names, 'guard': copy.deepcopy(guard)}


def _neutral_pattern(source, reason):
    return {'schema': SCHEMA, 'source': source, 'status': 'neutral',
            'reason': reason, 'prefix_binders': [], 'guard': None}


def extract_pattern(witness, ordered_premise_formulas=()):
    """Read declared syntax without inferring or rewriting any command.

    Instantiate: consequent, distinct leading forall prefix, immediate guard.
    MP: first ordered premise is a rigid guard; second is its exact implication.
    An MP equality output therefore receives its actual antecedent receptor.
    """
    if not isinstance(witness, dict):
        return _neutral_pattern('unsupported', 'unsupported-witness-shape')
    rule = witness.get('rule')
    out = witness.get('formula')
    if rule == 'mp':
        if (not isinstance(ordered_premise_formulas, (list, tuple))
                or len(ordered_premise_formulas) != 2
                or ordered_premise_formulas[1] != ['imp', ordered_premise_formulas[0], out]):
            return _neutral_pattern('mp-ordered-antecedent', 'unsupported-ordered-MP-interface')
        return pattern_from_guard(ordered_premise_formulas[0], (), source='mp-ordered-antecedent')
    if rule != 'instantiate':
        return _neutral_pattern(str(rule), 'rule-outside-matching-scope')
    if (not isinstance(out, list) or len(out) != 3 or out[0] != 'imp'
            or out[1] != witness.get('universal')):
        return _neutral_pattern('instantiate-consequent', 'unsupported-instantiation-interface')
    formula, names = out[2], []
    while isinstance(formula, list) and formula and formula[0] == 'all':
        if len(formula) != 3 or not isinstance(formula[1], str) or not formula[1]:
            return _neutral_pattern('instantiate-consequent', 'unsupported-prefix-binder-shape')
        names.append(formula[1])
        formula = formula[2]
    if len(names) != len(set(names)):
        return _neutral_pattern('instantiate-consequent', 'repeated-or-shadowed-prefix-binder')
    if not isinstance(formula, list) or len(formula) != 3 or formula[0] != 'imp':
        return _neutral_pattern('instantiate-consequent', 'no-immediate-implication-guard')
    return pattern_from_guard(formula[1], names, source='instantiate-consequent')


def literal_guard_match(pattern_record, recipient_formula):
    """Literal ordered-tree matching, with explicitly bounded slot images.

    A definite literal mismatch wins over an unsupported image elsewhere in the
    same otherwise supported formula. Without a mismatch, any unsupported image
    is neutral. A quantified/free/unsupported recipient is entirely neutral.
    None of these outcomes is a logical rejection or pruning certificate.
    """
    if pattern_record.get('schema') != SCHEMA or pattern_record.get('status') != 'supported':
        return {'status': 'neutral', 'bucket': 1, 'bindings': {},
                'reason': pattern_record.get('reason') or 'unsupported-pattern'}
    checked = pattern_from_guard(pattern_record.get('guard'), pattern_record.get('prefix_binders', ()))
    if checked['status'] != 'supported':
        return {'status': 'neutral', 'bucket': 1, 'bindings': {}, 'reason': checked['reason']}
    reason = _formula_reason(recipient_formula, set())
    if reason is not None:
        return {'status': 'neutral', 'bucket': 1, 'bindings': {}, 'reason': reason}
    slots = set(checked['prefix_binders'])
    bindings = {}
    reasons = []

    def term(pattern, recipient):
        if pattern[0] == 'var':
            name = pattern[1]
            if name not in slots:
                return 'neutral'  # Already ruled out by pattern validation.
            if recipient[0] != 'fun' or recipient[2]:
                reasons.append('unsupported-compound-slot-image')
                return 'neutral'
            if name in bindings and bindings[name] != recipient:
                reasons.append('inconsistent-repeated-slot-image')
                return 'nonmatch'
            bindings[name] = copy.deepcopy(recipient)
            return 'match'
        if pattern[0] != recipient[0] or pattern[1] != recipient[1] or len(pattern[2]) != len(recipient[2]):
            reasons.append('literal-term-constructor-symbol-or-arity-mismatch')
            return 'nonmatch'
        return combine([term(p, r) for p, r in zip(pattern[2], recipient[2])])

    def combine(values):
        if 'nonmatch' in values:
            return 'nonmatch'
        return 'neutral' if 'neutral' in values else 'match'

    def formula(pattern, recipient):
        if pattern[0] != recipient[0]:
            reasons.append('literal-formula-constructor-or-polarity-mismatch')
            return 'nonmatch'
        tag = pattern[0]
        if tag == 'bot':
            return 'match'
        if tag == 'pred':
            if pattern[1] != recipient[1] or len(pattern[2]) != len(recipient[2]):
                reasons.append('literal-predicate-symbol-or-arity-mismatch')
                return 'nonmatch'
            return combine([term(p, r) for p, r in zip(pattern[2], recipient[2])])
        if tag == 'eq':
            return combine([term(pattern[1], recipient[1]), term(pattern[2], recipient[2])])
        return combine([formula(p, r) for p, r in zip(pattern[1:], recipient[1:])])

    status = formula(checked['guard'], recipient_formula)
    return {'status': status, 'bucket': BUCKET[status], 'bindings': bindings if status == 'match' else {},
            'reason': None if status == 'match' else sorted(set(reasons)),
            'interpretation': 'literal structural advice, not inference or candidate legality'}


def evaluate_pattern(record, selected_records):
    """Compare only supplied physically selected output constraints.

    Each selected record contains key, formula_code and formula. Matching does
    not inspect a marking registry, empty row, proof dependency or target.
    """
    comparisons = []
    if record['status'] == 'supported':
        for selected in selected_records:
            outcome = literal_guard_match(record, selected['formula'])
            comparisons.append({'key': copy.deepcopy(selected['key']),
                'formula_code': selected['formula_code'], **outcome})
    matches = [entry for entry in comparisons if entry['status'] == 'match']
    if matches:
        label = 'match'
    elif any(entry['status'] == 'nonmatch' for entry in comparisons):
        label = 'nonmatch'
    else:
        label = 'neutral'
    return {'status': label, 'bucket': BUCKET[label],
            'pattern_status': record['status'], 'pattern_reason': record['reason'],
            'comparisons': comparisons, 'matches': matches,
            'scope': 'supported selected output subset only; nonmatch does not mean impossible'}


class ReceptorOrder(ForwardOrder):
    """The original readiness tier, then match bucket, then original ties.

    Every key remains in a complete permutation. No model or target constants
    occur here. Per-recipe records are shared across all reference bindings;
    individual binding references still participate in the old readiness tier.
    """
    def __init__(self, graph):
        super().__init__(graph)
        started = time.perf_counter()
        self.pattern_records = [extract_pattern(recipe.witness, recipe.formulas)
                                for recipe in graph.recipes]
        self.metrics.update({'pattern_preparation_seconds': time.perf_counter() - started,
            'selected_constraint_collection_seconds': 0.0, 'literal_matching_seconds': 0.0,
            'feature_payload_hash_seconds': 0.0, 'recipe_features_evaluated': 0,
            'selected_constraint_comparisons': 0})
        self.last_trace = None

    def order(self, keys):
        started = time.perf_counter()
        g = self.graph
        selected = [{'key': key.data(), 'formula_code': g.recipes[key.recipe].output,
                     'formula': g.formulas[g.recipes[key.recipe].output]}
                    for key in g.selected]
        selected_outputs = {entry['formula_code'] for entry in selected}
        self.metrics['selected_constraint_collection_seconds'] += time.perf_counter() - started
        started = time.perf_counter()
        recipe_features = {index: evaluate_pattern(self.pattern_records[index], selected)
                           for index in sorted({key.recipe for key in keys})}
        self.metrics['literal_matching_seconds'] += time.perf_counter() - started
        self.metrics['recipe_features_evaluated'] += len(recipe_features)
        self.metrics['selected_constraint_comparisons'] += sum(len(f['comparisons']) for f in recipe_features.values())
        started = time.perf_counter()
        scored = []
        for key in keys:
            recipe = g.recipes[key.recipe]
            rule, universal, equality, antecedent, size, witness = self.features[key.recipe]
            # This is the exact old readiness logic. Historical 'proved' values
            # mean selected output constraints, not accepted proof derivations.
            if recipe.output in selected_outputs:
                tier = 6
            elif rule == 'mp' and all(any(k.row == ref for k in g.selected) for ref in key.refs):
                tier = 0
            elif rule == 'instantiate' and universal in selected_outputs:
                tier = 1
            elif rule == 'eq_subst' and equality in selected_outputs and antecedent in selected_outputs:
                tier = 2
            elif rule == 'axiom':
                tier = 3
            elif rule == 'eq_subst' and equality in selected_outputs:
                tier = 4
            else:
                tier = 5
            scored.append(((tier, recipe_features[key.recipe]['bucket'], size, witness, key.recipe, key.refs), key))
        self.metrics['feature_seconds'] += time.perf_counter() - started
        started = time.perf_counter()
        scored.sort(key=lambda value: value[0])
        ordered = [key for _, key in scored]
        self.metrics['sort_seconds'] += time.perf_counter() - started
        started = time.perf_counter()
        if len(ordered) != len(keys) or len(set(ordered)) != len(keys) or set(ordered) != set(keys):
            raise AssertionError('receptor order dropped or duplicated a legal base candidate')
        self.metrics['permutation_check_seconds'] += time.perf_counter() - started
        started = time.perf_counter()
        score_stream = hashlib.sha256()
        for score, key in scored:
            score_stream.update((canonical({'key': key.data(), 'score': score}) + '\n').encode())
        compact_features = []
        for index in sorted(recipe_features):
            feature = recipe_features[index]
            compact_features.append({'recipe': index,
                **{field: feature[field] for field in ('status', 'bucket', 'pattern_status', 'pattern_reason', 'matches', 'scope')},
                'comparison_count': len(feature['comparisons']),
                'comparison_label_counts': {label: sum(entry['status'] == label for entry in feature['comparisons'])
                                            for label in BUCKET},
                'complete_comparisons_sha256': hashlib.sha256(canonical(feature['comparisons']).encode()).hexdigest()})
        self.last_trace = {'schema': 'literal-receptor-order-trace-v1',
            'selected_output_constraints': [{'key': entry['key'], 'formula_code': entry['formula_code']} for entry in selected],
            'recipe_features': compact_features,
            'complete_score_stream_sha256': score_stream.hexdigest(), 'complete_keys': len(keys),
            'score_contract': '(unchanged readiness tier, match bucket, original size/witness/recipe/refs)',
            'match_bucket_order': BUCKET,
            'interpretation': 'selected structural constraints may have pending ordered sources; no proof claim'}
        self.metrics['feature_payload_hash_seconds'] += time.perf_counter() - started
        self.metrics['calls'] += 1
        self.metrics['complete_keys_ranked'] += len(keys)
        return ordered
