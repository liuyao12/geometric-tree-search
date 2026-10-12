"""Prospective qualified episode update; pure functions, no dispatch/imports.

Uses the frozen policy math V2 object supplied by the caller. It is not a proof
checker or a trainer/owner implementation. ROOT must independently replay all
trajectory/feature/RNG/reward counters before passing a qualified receipt.
"""
from __future__ import annotations
import copy

VERSION = 'qualified-family-episode-mean-update-v1'


def initial_state(feature_names):
    return dict(version=VERSION, weights={name: 0.0 for name in sorted(feature_names)},
                baseline=0.0, qualified_episodes=0, audit_chain=[])


def qualified_update(math_module, training_state, episode, independent_receipt, *,
                     learning_rate=0.05, ema_alpha=0.2, direction_norm_ceiling=1.0):
    """No update from a failed/unexecuted/partial/resource-unknown trajectory.

    A completed budget-UNKNOWN search may teach cost/fact potential only when
    its complete returned trace and owned resource envelope independently pass.
    A positive terminal bonus requires independent primitive logical acceptance.
    Episode mean gradient and norm clipping are explicit heuristics, not an
    unbiased expected-return gradient claim. No held-out update is permitted.
    """
    if episode['split'] != 'donor' or episode['executed'] is not True:
        raise ValueError('only actually executed predeclared donor episodes train')
    if (independent_receipt['complete_trace_accepted'] is not True
            or independent_receipt['owned_resource_accepted'] is not True
            or independent_receipt['episode_id'] != episode['episode_id']
            or independent_receipt['trajectory_pin'] != episode['trajectory_pin']
            or independent_receipt['feature_policy_replay_accepted'] is not True):
        raise ValueError('exact qualified independent trace/features/RNG/resource receipt required')
    if independent_receipt['status'] not in ('unknown_search_budget', 'finite_exact_point_tiling',
                                             'exhausted_finite_marked_subtree'):
        raise ValueError('complete returned search status only')
    certificate = independent_receipt['primitive_certificate_accepted'] is True
    if certificate != (independent_receipt['status'] == 'finite_exact_point_tiling'):
        raise ValueError('positive update requires all-row independent primitive certificate')
    if independent_receipt['reward_counters'] != episode['reward_counters']:
        raise ValueError('all reward counters independently reconstructed')
    if independent_receipt['old_weights'] != training_state['weights']:
        raise ValueError('weights were frozen throughout this exact episode')
    gradients = [record['score_gradient']['gradient'] for record in episode['policy_choices']]
    reward = math_module.reward(producer_primitive_certificate_passed=certificate,
                               **episode['reward_counters'])
    update = math_module.update(training_state['weights'], gradients, reward['return'],
        training_state['baseline'], executed=True, learning_rate=learning_rate,
        ema_alpha=ema_alpha, direction_norm_ceiling=direction_norm_ceiling)
    result = copy.deepcopy(training_state)
    result['weights'], result['baseline'] = update['weights'], update['baseline']
    result['qualified_episodes'] += 1
    result['audit_chain'].append(copy.deepcopy(independent_receipt['receipt_pin']))
    return result, dict(episode_id=episode['episode_id'], trajectory_pin=episode['trajectory_pin'],
        audit_pin=independent_receipt['receipt_pin'], reward=reward, update=update,
        scope='Qualified donor update; never an evaluation update or held-out theorem discovery claim')
