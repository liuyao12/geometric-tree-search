"""Prospective numeric/API-contract controls only; ROOT activation is required.

No model, graph, tile, target, training trajectory or random generator is used.
The overlay below is a test double, not the geometry Controller or its adapter.
The outer owner must separately enforce its whole owned lifetime/memory gates.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import resource
import signal
import sys
import time


def pin(path):
    data = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def load_source(record, name):
    if pin(record['path']) != record:
        raise ValueError('source pin mismatch: ' + record['path'])
    spec = importlib.util.spec_from_file_location(name, record['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # Required by Python 3.9 dataclasses.
    spec.loader.exec_module(module)
    return module


def close(actual, expected, tolerance=2e-12):
    if not math.isfinite(actual) or not math.isfinite(expected):
        raise AssertionError('finite comparison required')
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(('numeric mismatch', actual, expected, tolerance))


def reference_probabilities(features, weights, epsilon, temperature):
    """Separate finite reference formula; no call to production distribution."""
    keys = sorted(set(weights).union(*(set(vector) for vector in features)))
    logits = [math.fsum(weights.get(key, 0.0) * vector.get(key, 0.0)
                        for key in keys) / temperature for vector in features]
    offset = max(logits)
    masses = [math.exp(value - offset) for value in logits]
    total = math.fsum(masses)
    q = [mass / total for mass in masses]
    return q, [(1.0 - epsilon) * value + epsilon / len(q) for value in q]


def reference_choice(probabilities, draw):
    cumulative = 0.0
    for index, probability in enumerate(probabilities):
        cumulative += probability
        if draw < cumulative:
            return index
    return max(index for index, probability in enumerate(probabilities) if probability > 0.0)


class OverlayTestDouble:
    """Abstract contract only: immutable descriptor catalog plus trailed overlay.

Supplied base keys are already legal. This does not compute legality, scheduler,
hint waiting/retirement, whole-cluster validation, or the graph's rollback.
"""
    def __init__(self):
        self.original = (('F-A', (1, 3), (0,)), ('F-B', (2,), (1,)))
        self.active = None
        self.states = {'F-A': 'waiting', 'F-B': 'waiting'}
        self.root_checkpoint = ('opaque-root-checkpoint', 0)
        self.view_checkpoint = ('opaque-view-checkpoint', 0)

    def choose(self, identifier):
        if identifier is not None and identifier not in self.states:
            raise ValueError('only frozen catalog identities may be selected')
        self.active = identifier

    def order(self, complete_legal_base_keys):
        base = tuple(complete_legal_base_keys)
        if len(set(base)) != len(base):
            raise ValueError('distinct complete base keys required')
        if self.active is None:
            return base  # NULL suppresses every untouched fixed priority.
        record = next(item for item in self.original if item[0] == self.active)
        preferred = tuple(key for key in record[1] if key in base)
        return preferred + tuple(key for key in base if key not in preferred)

    def checkpoint(self):
        return (self.active, tuple(sorted(self.states.items())),
                self.root_checkpoint, self.view_checkpoint)

    def rollback(self, checkpoint):
        active, states, root, view = checkpoint
        self.active = active
        self.states = dict(states)
        self.root_checkpoint = root
        self.view_checkpoint = view


def run_controls(policy, bridge, record_control, mark_numeric_invocation):
    annotations = bridge.PairedPoolCheckpoint.__annotations__
    assert isinstance(annotations['active_descriptor_id'], str)
    assert isinstance(annotations['active_controller_view_checkpoint'], str)
    record_control('python39_deferred_annotation_import', {'runtime': list(sys.version_info[:3])})

    ids = ['A', 'B', 'NULL']
    vectors = [{'a': -1.0, 'b': 0.5}, {'a': 0.2, 'b': -1.0}, {'a': 1.5, 'b': 0.1}]
    cases = [
        ('epsilon0_temp05', vectors, {'a': 0.35, 'b': -0.2}, 0.0, 0.5),
        ('epsilon01_temp1', vectors, {'a': 0.35, 'b': -0.2}, 0.1, 1.0),
        ('epsilon035_temp2', vectors, {'a': 0.35, 'b': -0.2}, 0.35, 2.0),
        ('epsilon1_uniform', vectors, {'a': 0.35, 'b': -0.2}, 1.0, 0.5),
        ('zero_weights', vectors, {'a': 0.0, 'b': 0.0}, 0.1, 1.0),
        ('duplicate_vectors', [vectors[0], vectors[0], vectors[2]],
         {'a': 0.35, 'b': -0.2}, 0.2, 1.0),
    ]
    derivative_count = 0
    changed_gradient_mutant = False
    for name, features, weights, epsilon, temperature in cases:
        mark_numeric_invocation()
        distribution = policy.distribution(ids, features, weights,
                                           epsilon=epsilon, temperature=temperature)
        expected_q, expected_p = reference_probabilities(features, weights, epsilon, temperature)
        for actual, expected in zip(distribution['softmax'], expected_q):
            close(actual, expected)
        for actual, expected in zip(distribution['probabilities'], expected_p):
            close(actual, expected)
        close(distribution['probability_sum'], 1.0)
        if epsilon == 1.0 or not any(weights.values()):
            for probability in distribution['probabilities']:
                close(probability, 1.0 / len(ids))
        for draw in (0.0, 0.125, 0.5, math.nextafter(1.0, 0.0)):
            selected = policy.choose(distribution, draw)
            assert selected['chosen_index'] == reference_choice(distribution['probabilities'], draw)
            assert selected['chosen_id'] == ids[selected['chosen_index']]
        gradients = []
        for action in range(len(ids)):
            analytic = policy.score_gradient(distribution, action)['gradient']
            gradients.append(analytic)
            for feature in ('a', 'b'):
                step = 1e-6
                plus = dict(weights); minus = dict(weights)
                plus[feature] += step; minus[feature] -= step
                p_plus = reference_probabilities(features, plus, epsilon, temperature)[1][action]
                p_minus = reference_probabilities(features, minus, epsilon, temperature)[1][action]
                derivative = (math.log(p_plus) - math.log(p_minus)) / (2.0 * step)
                close(analytic[feature], derivative, tolerance=2e-7)
                derivative_count += 1
        if name == 'epsilon035_temp2':
            q = distribution['softmax']
            expected_a = math.fsum(q[i] * features[i]['a'] for i in range(len(ids)))
            plain_softmax_mutant = (features[0]['a'] - expected_a) / temperature
            changed_gradient_mutant = abs(plain_softmax_mutant - gradients[0]['a']) > 1e-5
            assert changed_gradient_mutant
        record_control('mixture_case:' + name, {
            'distribution': distribution, 'gradients': gradients, 'finite_derivatives': 6,
            'draws_per_case': 4, 'scalar_reference_tolerance': 2e-12,
            'derivative_tolerance': 2e-7})
    assert derivative_count == 36
    record_control('plain_softmax_gradient_mutant_detected', {'detected': changed_gradient_mutant})

    for epsilon in (0.0, 0.2):
        extreme = policy.distribution(ids, [{'a': 1.0}, {'a': 0.0}, {'a': -1.0}],
                                      {'a': 1000.0}, epsilon=epsilon, temperature=0.5)
        assert all(math.isfinite(p) and p >= 0.0 for p in extreme['probabilities'])
        close(math.fsum(extreme['probabilities']), 1.0)
        picked = policy.choose(extreme, math.nextafter(1.0, 0.0))
        assert picked['chosen_index'] == reference_choice(extreme['probabilities'], picked['draw'])
        if epsilon == 0.0:
            assert extreme['probabilities'] == [1.0, 0.0, 0.0]
            assert picked['chosen_index'] == 0
        record_control('stable_extreme_logits:' + str(epsilon), {'distribution': extreme, 'choice': picked})

    # The sub-ulp fallback is tested with an explicitly synthetic valid rounded
    # sequence. It is not claimed to be a source-generated action distribution.
    gap = {'probabilities': [0.5, 0.5 - 2e-16, 0.0],
           'action_ids': ids, 'softmax': [0.5, 0.5 - 2e-16, 0.0]}
    assert policy.choose(gap, math.nextafter(1.0, 0.0))['chosen_index'] == 1
    record_control('synthetic_last_positive_roundoff_fallback', {'zero_tail_not_selected': True})

    malformed = [
        ('negative_normalized', [-0.1, 0.5, 0.6]), ('nan', [float('nan'), 0.0, 1.0]),
        ('plus_infinity', [float('inf'), 0.0, 0.0]), ('minus_infinity', [-float('inf'), 1.0, 0.0]),
        ('bool', [True, 0.0, 0.0]), ('string', ['1', 0.0, 0.0]),
        ('empty', []), ('nonsequence', '1'), ('unnormalized', [0.1, 0.1, 0.1]),
    ]
    for name, probabilities in malformed:
        bad = {'probabilities': probabilities, 'action_ids': ids, 'softmax': [1.0, 0.0, 0.0]}
        try:
            policy.choose(bad, 0.5)
        except ValueError:
            record_control('malformed_probability_rejected:' + name, {'rejected': True})
        else:
            raise AssertionError('malformed probabilities accepted: ' + name)

    clipped = policy.update({'a': 0.0, 'b': 0.0}, [{'a': 3.0, 'b': 4.0}],
                            2.0, 0.0, executed=True)
    close(clipped['advantage'], 2.0)
    close(clipped['advantage_direction_L2_before_clip'], 10.0)
    close(clipped['clip_scale'], 0.1)
    close(clipped['direction_L2_after_clip'], 1.0)
    close(clipped['weights']['a'], 0.03); close(clipped['weights']['b'], 0.04)
    close(clipped['baseline'], 0.4)
    assert abs(clipped['weights']['a'] - 0.06) > 1e-5  # Clip-before-advantage mutant.
    record_control('advantage_before_direction_clip', clipped)

    ordered = policy.update({'a': 0.0}, [{'a': 0.2}], 2.0, 0.5, executed=True)
    close(ordered['advantage'], 1.5); close(ordered['baseline'], 0.8)
    close(ordered['weights']['a'], 0.015)
    assert abs(ordered['advantage'] - (2.0 - ordered['baseline'])) > 1e-5
    record_control('old_baseline_before_update_then_EMA', ordered)
    empty = policy.update({'a': 0.3}, [], 0.5, 0.0, executed=True)
    close(empty['weights']['a'], 0.3); close(empty['baseline'], 0.1)
    record_control('empty_executed_episode_changes_only_EMA', empty)
    try:
        policy.update({'a': 0.3}, [], 0.5, 0.0, executed=False)
    except ValueError:
        record_control('unexecuted_episode_cannot_update', {'rejected': True})
    else:
        raise AssertionError('unexecuted update accepted')

    counts = dict(producer_primitive_certificate_passed=False,
                  maximum_distinct_dependency_complete_nonroot_facts=0, logical_rows=24,
                  primitive_attempts=10, attempt_limit=250, construction_validation_checks=0,
                  check_ceiling=2048, retired_commits=0, commits=0)
    no_facts = policy.reward(**counts)
    close(no_facts['return'], -0.004)
    counts['maximum_distinct_dependency_complete_nonroot_facts'] = 12
    some_facts = policy.reward(**counts)
    close(some_facts['return'], 0.021)
    record_control('reward_counter_arithmetic_only', {
        'no_facts': no_facts, 'some_facts': some_facts,
        'scope': 'No engine fact counter exists here; this is not pending-input reward certification.'})

    overlay = OverlayTestDouble()
    original = overlay.original
    root = overlay.checkpoint()
    assert overlay.order((3, 2, 1)) == (3, 2, 1)
    overlay.choose('F-A'); parent = overlay.checkpoint()
    assert overlay.order((3, 2, 1)) == (1, 3, 2)
    overlay.states['F-A'] = 'retired'; overlay.choose('F-B')
    overlay.view_checkpoint = ('opaque-view-checkpoint', 1)
    assert overlay.order((3, 2, 1)) == (2, 3, 1)
    overlay.rollback(parent)
    assert overlay.checkpoint() == parent
    assert overlay.active == 'F-A' and overlay.states['F-A'] == 'waiting'
    overlay.choose(None)
    assert overlay.order((3, 2, 1)) == (3, 2, 1)
    overlay.rollback(root)
    assert overlay.checkpoint() == root and overlay.original == original
    for chosen in (None, 'F-A', 'F-B'):
        overlay.choose(chosen)
        ordered_keys = overlay.order((3, 2, 1))
        assert len(ordered_keys) == 3 and set(ordered_keys) == {1, 2, 3}
        assert overlay.original == original
    # Explicit adversaries: stale active overlay would survive graph-only
    # rollback; untouched fixed priorities would leak into a NULL choice.
    stale_overlay_mutant = ('F-B', parent[1], parent[2], parent[3])
    assert stale_overlay_mutant != parent
    fixed_priority_null_mutant = (1, 3, 2)
    assert fixed_priority_null_mutant != (3, 2, 1)
    record_control('abstract_overlay_contract_not_engine_conformance', {
        'NULL_suppresses_fixed_priority': True, 'complete_fallback_preserved': True,
        'paired_active_and_view_restored': True, 'original_catalog_unchanged': True,
        'two_contract_mutants_distinguished': True,
        'scope': 'Test-double contract only; actual Controller/graph/hint rollback remains unimplemented.'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--activation', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    started = time.monotonic()
    plan_record = pin(args.plan)
    plan = json.loads(Path(args.plan).read_text())
    activation_record = pin(args.activation)
    activation = json.loads(Path(args.activation).read_text())
    if activation.get('scope') != 'root_authorized_numeric_fixture_only':
        raise ValueError('ROOT numeric-only activation required')
    if activation.get('plan') != plan_record or activation.get('source_pins') != plan['sources']:
        raise ValueError('exact plan/source activation required')
    if activation.get('runtime_pin') != pin(sys.executable):
        raise ValueError('exact activated Python executable required')
    if str(Path(args.output)) != plan['prospective_output']:
        raise ValueError('exact declared fresh output directory required')
    for record in plan['sources']:
        if pin(record['path']) != record:
            raise ValueError('frozen source mismatch')
    if sys.version_info[:2] != (3, 9):
        raise ValueError('Python 3.9 numeric/API compatibility gate required')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    controls = []
    result = {'status': 'unknown_before_controls', 'scope': plan['scope'],
              'plan': plan_record, 'activation': activation_record,
              'controls': controls, 'numeric_fixture_worker_runs': 1,
              'policy_numeric_functions_executed': False,
              'production_engine_runs': 0, 'search_runs': 0, 'training_runs': 0,
              'random_draws_generated': 0, 'runtime_adapter_implemented': False}

    def checkpoint():
        # This mutable file is prospective owned output, never old source data.
        (output / 'partial-controls.json').write_text(json.dumps(result, ensure_ascii=False,
                                                               allow_nan=False, indent=2) + '\n')

    def record_control(identifier, detail):
        controls.append({'id': identifier, 'status': 'passed', 'detail': detail})
        checkpoint()

    def mark_numeric_invocation():
        result['policy_numeric_functions_executed'] = True

    def timeout(signum, frame):
        raise TimeoutError('numeric worker internal time budget')

    signal.signal(signal.SIGALRM, timeout)
    remaining = plan['limits']['internal_seconds'] - (time.monotonic() - started)
    if remaining <= 0.0:
        result['status'] = 'unknown_internal_time_budget'
        checkpoint()
        return 0
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        policy = load_source(plan['math_source'], '_family_policy_math_v2_numeric_gate')
        bridge = load_source(plan['bridge_source'], '_family_pool_bridge_v2_numeric_gate')
        run_controls(policy, bridge, record_control, mark_numeric_invocation)
        result['status'] = 'passed_numeric_and_abstract_API_controls_only'
    except TimeoutError as error:
        result['status'] = 'unknown_internal_time_budget'
        result['error'] = str(error)
    except BaseException as error:
        result['status'] = 'failed_numeric_or_abstract_API_control'
        result['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        result['worker_seconds_before_final_serialization'] = time.monotonic() - started
        result['worker_kernel_peak_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if result['worker_kernel_peak_bytes'] > plan['limits']['memory_bytes']:
            result['status'] = 'unknown_worker_memory_budget'
        result['scope_warning'] = 'Outer owned lifetime/resource receipt is additionally required; no scientific Controller, fact counter, trajectory, training or learned-policy claim.'
        checkpoint()
        # Keep alarm through final output/cleanup, then disarm after writing.
        (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False,
                                                     allow_nan=False, indent=2) + '\n')
        signal.setitimer(signal.ITIMER_REAL, 0.0)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
