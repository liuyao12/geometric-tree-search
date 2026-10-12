"""Bounded synthetic AST controls only, never a point graph or proof search."""
import copy
import hashlib
import json
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path)
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('five-second pure AST gate')))
    signal.alarm(5)
    plan = json.loads((HERE / 'pure-ast-plan-v1.json').read_text())
    for entry in plan['sources'] + plan['inputs']:
        if pin(ROOT / entry['path']) != {k: entry[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('frozen pure-AST source/input changed')
    # This module imports only the stdlib and the pure ForwardOrder class; no
    # lifecycle/core/model/decoder/worker is imported or instantiated here.
    from receptor_literal_match_v1 import (pattern_from_guard, literal_guard_match,
                                           extract_pattern, evaluate_pattern)
    corpus = json.loads((ROOT / plan['inputs'][0]['path']).read_text())
    records = []

    def record(name, actual, expected, *, extraction=False):
        if extraction:
            if actual['status'] != expected:
                raise AssertionError((name, actual, expected))
        else:
            if actual['status'] != expected['status']:
                raise AssertionError((name, actual, expected))
            if actual['status'] == 'match' and actual['bindings'] != expected['bindings']:
                raise AssertionError((name, actual, expected))
        records.append({'id': name, 'actual': actual, 'expected': expected})

    for case in corpus['matcher_cases']:
        p = pattern_from_guard(case['pattern'], case['prefix_binders'])
        actual = literal_guard_match(p, case['available'])
        expected = copy.deepcopy(case['expected'])
        if expected['status'] == 'miss':
            expected['status'] = 'nonmatch'
        record('cross-domain/' + case['id'], actual, expected)

    for case in corpus['availability_cases']:
        if case['kind'] != 'availability':
            continue  # Seven arithmetic adapter role/dependency controls stay separate.
        selected = [{'key': [row['row'], row['row'], []], 'formula_code': row['row'],
                     'formula': row['formula']} for row in case['state']['selected_outputs']]
        if [row['key'][1] for row in selected] != case['expected_rows']:
            raise AssertionError('selected-only row projection')
        if [row['formula'] for row in selected] != case['expected_available_formulas']:
            raise AssertionError('selected-only formula projection')
        if 'pattern' in case:
            result = evaluate_pattern(pattern_from_guard(case['pattern'], case['prefix_binders']), selected)
            expected = case['expected_status'].replace('miss', 'nonmatch')
            if result['status'] != expected:
                raise AssertionError((case['id'], result, expected))
        else:
            result = {'selected_keys': [row['key'] for row in selected], 'selected_count': len(selected),
                      'unoccupied_marks_consulted': 0}
        records.append({'id': 'availability/' + case['id'], 'actual': result})

    a, b = ['fun', 'a', []], ['fun', 'b', []]
    x, y = ['var', 'x'], ['var', 'y']
    pred = lambda name, *args: ['pred', name, list(args)]
    guard, conclusion = pred('Rel', x, y), pred('Goal', a)
    u = ['all', 'z', pred('Unused', ['var', 'z'])]
    instance = ['all', 'x', ['all', 'y', ['imp', guard, conclusion]]]
    inst = lambda consequent: {'rule': 'instantiate', 'universal': u, 'formula': ['imp', u, consequent]}
    good = extract_pattern(inst(instance))
    record('extraction/instantiate-leading-distinct-prefix', good, 'supported', extraction=True)
    record('extraction/instantiate-match-slots', literal_guard_match(good, pred('Rel', a, b)),
           {'status': 'match', 'bindings': {'x': a, 'y': b}})
    record('extraction/MP-guard-not-equality-output',
           extract_pattern({'rule': 'mp', 'formula': ['eq', a, b]}, [pred('H', a), ['imp', pred('H', a), ['eq', a, b]]]),
           'supported', extraction=True)
    record('extraction/MP-ordered-interface-reversal',
           extract_pattern({'rule': 'mp', 'formula': conclusion}, [['imp', pred('H', a), conclusion], pred('H', a)]),
           'neutral', extraction=True)
    record('extraction/MP-quantified-antecedent-neutral',
           extract_pattern({'rule': 'mp', 'formula': conclusion}, [u, ['imp', u, conclusion]]),
           'neutral', extraction=True)
    record('extraction/repeated-leading-binder-neutral',
           extract_pattern(inst(['all', 'x', ['all', 'x', ['imp', pred('H', x), conclusion]]])),
           'neutral', extraction=True)
    record('extraction/free-variable-outside-prefix-neutral',
           extract_pattern(inst(['all', 'x', ['imp', pred('H', x, y), conclusion]])),
           'neutral', extraction=True)
    record('extraction/nested-quantified-guard-neutral',
           extract_pattern(inst(['all', 'x', ['imp', ['all', 'y', pred('H', y)], conclusion]])),
           'neutral', extraction=True)
    record('extraction/no-immediate-guard-neutral', extract_pattern(inst(pred('H', a))), 'neutral', extraction=True)
    malformed = inst(instance); malformed['universal'] = pred('Different', a)
    record('extraction/declared-universal-interface-disagrees', extract_pattern(malformed), 'neutral', extraction=True)
    record('extraction/unrelated-rule-neutral', extract_pattern({'rule': 'axiom', 'formula': ['imp', guard, conclusion]}),
           'neutral', extraction=True)
    record('syntax/empty-symbol-neutral', literal_guard_match(pattern_from_guard(pred('', x), ['x']), pred('', a)),
           {'status': 'neutral', 'bindings': {}})
    record('syntax/empty-binder-neutral', literal_guard_match(pattern_from_guard(pred('H', ['var', '']), ['']), pred('H', a)),
           {'status': 'neutral', 'bindings': {}})
    record('syntax/bool-term-neutral', literal_guard_match(pattern_from_guard(pred('H', x), ['x']), pred('H', False)),
           {'status': 'neutral', 'bindings': {}})
    compound = ['fun', 'f', [a]]
    mixed = pattern_from_guard(['and', pred('H', x), pred('Q', a)], ['x'])
    record('precedence/definite-miss-after-unsupported-image',
           literal_guard_match(mixed, ['and', pred('H', compound), pred('R', a)]),
           {'status': 'nonmatch', 'bindings': {}})
    mixed_reverse = pattern_from_guard(['and', pred('Q', a), pred('H', x)], ['x'])
    record('precedence/definite-miss-before-unsupported-image',
           literal_guard_match(mixed_reverse, ['and', pred('R', a), pred('H', compound)]),
           {'status': 'nonmatch', 'bindings': {}})
    record('precedence/unsupported-image-without-definite-miss',
           literal_guard_match(mixed, ['and', pred('H', compound), pred('Q', a)]),
           {'status': 'neutral', 'bindings': {}})
    receptor = pattern_from_guard(pred('H', x), ['x'])
    repeated = [{'key': [1, 0, []], 'formula_code': 4, 'formula': pred('H', a)},
                {'key': [1, 1, []], 'formula_code': 4, 'formula': pred('H', a)}]
    result = evaluate_pattern(receptor, repeated)
    if result['status'] != 'match' or [entry['key'] for entry in result['matches']] != [r['key'] for r in repeated]:
        raise AssertionError('identical formula constraints lost distinct selected identities')
    records.append({'id': 'availability/duplicate-selected-keys-retained', 'actual': result})
    empty = evaluate_pattern(receptor, [])
    if empty['status'] != 'neutral' or empty['comparisons']:
        raise AssertionError('no selected outputs must be neutral')
    records.append({'id': 'availability/no-selected-outputs-neutral', 'actual': empty})
    mixed_recipients = evaluate_pattern(receptor, [{'key': [2, 2, []], 'formula_code': 5, 'formula': u},
                        {'key': [3, 3, []], 'formula_code': 6, 'formula': pred('Different', a)}])
    if mixed_recipients['status'] != 'nonmatch':
        raise AssertionError('supported recipient subset nonmatch classification')
    records.append({'id': 'availability/neutral-recipient-and-supported-nonmatch', 'actual': mixed_recipients})
    forbidden = [name for name in sys.modules if name.startswith(('hilbert_primitive_', 'hilbert_cluster_', 'frozen_lifecycle_'))]
    if forbidden:
        raise AssertionError('actual engine imported by pure controls: ' + repr(forbidden))
    outcome = {'status': 'passed_bounded_pure_AST_matcher_controls', 'plan': pin(HERE / 'pure-ast-plan-v1.json'),
        'records': records, 'record_count': len(records), 'cross_domain_matcher_cases': len(corpus['matcher_cases']),
        'cross_domain_selected_availability_cases': 3, 'arithmetic_adapter_cases_not_executed': 7,
        'seconds_before_output_write': time.perf_counter() - started,
        'actual_model_loads': 0, 'engine_imports': 0, 'ordering_graph_calls': 0, 'searches': 0,
        'proofs': 0, 'native_queries': 0, 'new_training': 0,
        'scope': 'Pure syntax/selection projections only, no point-domain, scheduler, actual ranking permutation or logical certificate acceptance.'}
    with (HERE / 'pure-ast-outcome-v1.json').open('x') as stream:
        stream.write(json.dumps(outcome, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in outcome.items() if k != 'records'}))


if __name__ == '__main__':
    main()
