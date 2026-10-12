"""SOURCE ONLY independent epsilon-mixture, reward and update reconstruction.

No production math imports. The trajectory adapter must independently reconstruct
complete event tapes, graph facts, ownership, commit identities and source pins
before these arithmetic functions can qualify a donor. These are not a trainer,
proof checker, search driver or an executed numeric control.
"""
import math


def need(condition, label):
    if not condition:
        raise ValueError(label)


def number(value):
    need(type(value) in (int, float) and math.isfinite(value), 'finite literal numeric value')
    return float(value)


def vector(value):
    need(type(value) is dict and all(type(k) is str and k for k in value), 'literal sparse vector')
    return {k: number(value[k]) for k in sorted(value)}


def distribution(menu, weights, epsilon=0.1, temperature=1.0):
    ids = menu['action_ids']
    features = [vector(f) for f in menu['feature_vectors']]
    weights = vector(weights)
    need(ids and ids == sorted(set(ids)) and len(ids) == len(features), 'complete canonical action pool')
    epsilon, temperature = number(epsilon), number(temperature)
    need(0 <= epsilon <= 1 and temperature > 0, 'epsilon mixture and positive temperature')
    names = sorted(set(weights).union(*(set(f) for f in features)))
    logits = [math.fsum(weights.get(k, 0.0) * f.get(k, 0.0) for k in names) / temperature
              for f in features]
    need(all(math.isfinite(v) for v in logits), 'finite bounded policy logits')
    numerators = [math.exp(v - max(logits)) for v in logits]
    normalizer = math.fsum(numerators)
    q = [v / normalizer for v in numerators]
    p = [math.fsum(((1 - epsilon) * v, epsilon / len(ids))) for v in q]
    return dict(version='family-epsilon-mixture-policy-math-v2', action_ids=list(ids), features=features,
                weights=weights, epsilon=epsilon, temperature=temperature, feature_names=names,
                logits=logits, softmax=q, probabilities=p, normalizer=normalizer,
                probability_sum=math.fsum(p))


def choice_and_gradient(distribution_record, draw):
    draw = number(draw)
    need(0 <= draw < 1, 'one literal saved half-open draw')
    q, p = distribution_record['softmax'], distribution_record['probabilities']
    total = 0.0
    index = None
    for j, probability in enumerate(p):
        total += probability
        if draw < total:
            index = j
            break
    if index is None:
        index = max(j for j, mass in enumerate(p) if mass > 0)
    choice = dict(chosen_index=index, chosen_id=distribution_record['action_ids'][index], draw=draw,
                  chosen_probability=p[index], chosen_softmax_probability=q[index],
                  CDF_arithmetic='literal left-to-right +=; strict draw<cumulative; last-positive roundoff fallback')
    expectation = {k: math.fsum(q[j] * f.get(k, 0.0)
                              for j, f in enumerate(distribution_record['features']))
                   for k in distribution_record['feature_names']}
    factor = ((1 - distribution_record['epsilon']) * q[index] / p[index] /
              distribution_record['temperature'])
    score = {k: factor * (distribution_record['features'][index].get(k, 0.0) - expectation[k])
             for k in distribution_record['feature_names']}
    return choice, dict(gradient=score, expected_softmax_features=expectation,
                        mixture_gradient_factor=factor)


def audit_policy(record, menu, weights, draw, compare, epsilon=0.1, temperature=1.0):
    expected = distribution(menu, weights, epsilon, temperature)
    choice, gradient = choice_and_gradient(expected, draw)
    compare(record['menu'], menu, 'complete independently reconstructed feature menu')
    compare(record['distribution'], expected, 'mixture distribution including every action')
    compare(record['choice'], choice, 'saved chronological draw and literal CDF choice')
    compare(record['score_gradient'], gradient, 'mixture gradient, not softmax gradient')
    return choice, gradient


def reward(counters, certificate_accepted):
    need(type(certificate_accepted) is bool, 'independent complete primitive certificate flag')
    fields = ('maximum_distinct_dependency_complete_nonroot_facts', 'logical_rows',
              'primitive_attempts', 'attempt_limit', 'construction_validation_checks',
              'check_ceiling', 'retired_commits', 'commits')
    need(set(counters) == set(fields) and all(type(counters[k]) is int and counters[k] >= 0
                                            for k in fields), 'exact reconstructed counter schema')
    f, h, a, maximum, v, ceiling, retired, committed = [counters[k] for k in fields]
    need(h > 0 and maximum > 0 and ceiling > 0 and f <= h and retired <= committed,
         'per-state potential and unique committed retirements')
    terminal = float(certificate_accepted)
    shaping, attempts, validation = 0.05 * f / h, 0.10 * min(1.0, a / maximum), 0.05 * min(1.0, v / ceiling)
    retirement = 0.01 * retired / max(1, committed)
    return dict(return_value=math.fsum((terminal, shaping, -attempts, -validation, -retirement)),
                terminal=terminal, shaping=shaping, attempt_cost=attempts,
                construction_cost=validation, retirement_cost=retirement)


def update(weights, score_gradients, return_value, old_baseline, *, rate=0.05, alpha=0.2, ceiling=1.0):
    weights = vector(weights)
    gradients = [vector(g) for g in score_gradients]
    value, baseline, rate, alpha, ceiling = map(number, (return_value, old_baseline, rate, alpha, ceiling))
    need(rate >= 0 and 0 <= alpha <= 1 and ceiling > 0, 'fixed update hyperparameters')
    names = sorted(set(weights).union(*(set(g) for g in gradients)))
    mean = {k: math.fsum(g.get(k, 0.0) for g in gradients) / max(1, len(gradients)) for k in names}
    advantage = value - baseline
    direction = {k: advantage * mean[k] for k in names}
    norm = math.sqrt(math.fsum(v * v for v in direction.values()))
    scale = min(1.0, ceiling / norm) if norm else 1.0
    increment = {k: rate * scale * direction[k] for k in names}
    new_weights = {k: math.fsum((weights.get(k, 0.0), increment[k])) for k in names}
    return dict(version='family-epsilon-mixture-policy-math-v2', old_weights=weights, weights=new_weights,
                old_baseline=baseline, baseline=math.fsum(((1 - alpha) * baseline, alpha * value)),
                return_value=value, advantage=advantage, choice_count=len(gradients), mean_score_gradient=mean,
                score_gradient_L2=math.sqrt(math.fsum(v * v for v in mean.values())),
                advantage_direction_L2_before_clip=norm, clip_scale=scale,
                direction_L2_after_clip=norm * scale, increment=increment,
                learning_rate=rate, ema_alpha=alpha, direction_norm_ceiling=ceiling)


def qualifying_episode(episode, receipt, frozen_episode, exact_pin, audit_output):
    """Receipt fields cannot substitute for an exact independently rebuilt tape.

    audit_output must come from the future independently accepted full-tape
    adapter. There is deliberately no CLI/loader and no implicit authority from
    a producer PASS field. This stage cannot qualify raw trials by itself.
    """
    need(episode['split'] == 'donor' and episode['executed'] is True, 'no held-out or unexecuted update')
    need(episode['episode_id'] == frozen_episode['id'] and episode['seed'] == frozen_episode['seed'] and
         episode['donor'] == frozen_episode['donor'], 'fixed curriculum order/context/seed')
    need(episode['trajectory_pin'] == exact_pin and receipt['trajectory_pin'] == exact_pin,
         'exact actual trajectory bytes, not mutable episode data')
    need(receipt['complete_trace_accepted'] is True and receipt['owned_resource_accepted'] is True and
         receipt['feature_policy_replay_accepted'] is True, 'whole tape and complete lifecycle qualified')
    need(audit_output['complete_tape_accepted'] is True and
         audit_output['reward_counters'] == episode['reward_counters'] == receipt['reward_counters'],
         'true dependency-complete facts and independently reconstructed counters')
    need(audit_output['policy_choices'] == episode['policy_choices'],
         'every saved policy record/gradient agrees with exact reconstructed tape')
    need(receipt['old_weights'] == audit_output['old_weights'], 'weights frozen through all branches')
    need(receipt['status'] in ('unknown_search_budget', 'finite_exact_point_tiling',
                               'exhausted_finite_marked_subtree'), 'no resource-UNKNOWN or partial trace update')
    accepted = audit_output['primitive_certificate_accepted'] is True
    need(accepted == (receipt['status'] == 'finite_exact_point_tiling') ==
         (receipt['primitive_certificate_accepted'] is True), 'independent terminal bonus only')
    return audit_output
