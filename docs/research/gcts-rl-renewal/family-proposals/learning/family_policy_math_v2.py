"""Pure prospective policy math; no engine, RNG, model, file or checker imports.

Caller supplies the exact canonical action pool and independently reconstructible
bounded features. This module is source-only until ROOT separately activates
numeric controls and a scientific owner. It does not construct or validate tiles.
"""
import math

VERSION = 'family-epsilon-mixture-policy-math-v2'


def finite_number(value, label):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('finite literal number required: ' + label)
    return float(value)


def vector(value, label):
    if not isinstance(value, dict):
        raise ValueError('literal sparse vector required: ' + label)
    if any(not isinstance(key, str) or not key for key in value):
        raise ValueError('nonempty feature names required')
    return {key: finite_number(value[key], label + ':' + key) for key in sorted(value)}


def distribution(action_ids, feature_vectors, weights, *, epsilon=0.1, temperature=1.0):
    """One finite epsilon-mixture distribution in literal canonical action order.

Zero coefficients/features remain explicit in returned vectors. Action IDs are
only order/provenance identifiers; never features or learned coefficients.
"""
    if not isinstance(action_ids, (list, tuple)) or not action_ids:
        raise ValueError('nonempty canonical action pool, including NULL, required')
    if any(not isinstance(item, str) or not item for item in action_ids):
        raise ValueError('literal nonempty action identity required')
    if len(set(action_ids)) != len(action_ids) or list(action_ids) != sorted(action_ids):
        raise ValueError('distinct lexicographically sorted action identities required')
    if not isinstance(feature_vectors, (list, tuple)) or len(feature_vectors) != len(action_ids):
        raise ValueError('one full sparse vector per exact action required')
    epsilon = finite_number(epsilon, 'epsilon')
    temperature = finite_number(temperature, 'temperature')
    if not 0.0 <= epsilon <= 1.0 or temperature <= 0.0:
        raise ValueError('epsilon in unit interval and positive temperature required')
    w = vector(weights, 'weights')
    features = [vector(item, 'features') for item in feature_vectors]
    names = sorted(set(w).union(*(set(item) for item in features)))
    logits = [math.fsum(w.get(name, 0.0) * item.get(name, 0.0) for name in names) / temperature
              for item in features]
    if any(not math.isfinite(item) for item in logits):
        raise ValueError('finite policy logits required')
    highest = max(logits)
    exponentials = [math.exp(item - highest) for item in logits]
    normalizer = math.fsum(exponentials)
    q = [item / normalizer for item in exponentials]
    uniform = epsilon / len(q)
    p = [math.fsum(((1.0 - epsilon) * item, uniform)) for item in q]
    if any(not math.isfinite(item) or item < 0.0 for item in p):
        raise ValueError('invalid mixture distribution')
    return {'version': VERSION, 'action_ids': list(action_ids), 'features': features,
            'weights': w, 'epsilon': epsilon, 'temperature': temperature,
            'feature_names': names, 'logits': logits, 'softmax': q,
            'probabilities': p, 'normalizer': normalizer,
            'probability_sum': math.fsum(p)}


def choose(distribution_record, draw):
    """Consume the caller's ONE saved RNG draw; never create or reseed an RNG.

The record must be the unchanged output of distribution(), with its aligned
canonical action IDs, softmax values and full probability sequence. This entry
point separately rejects malformed/nonfinite/negative mixture probabilities;
other record fields retain that exact-generated-record precondition.
"""
    draw = finite_number(draw, 'draw')
    if not 0.0 <= draw < 1.0:
        raise ValueError('RNG draw in half-open unit interval required')
    probabilities = distribution_record['probabilities']
    if not isinstance(probabilities, (list, tuple)) or not probabilities:
        raise ValueError('nonempty literal recorded probability sequence required')
    p = [finite_number(item, 'recorded probability') for item in probabilities]
    if any(item < 0.0 for item in p):
        raise ValueError('nonnegative recorded probabilities required')
    if not math.isclose(math.fsum(p), 1.0, rel_tol=0.0, abs_tol=2e-12):
        raise ValueError('normalized exact recorded mixture required')
    cumulative = 0.0
    chosen = None
    for index, probability in enumerate(p):
        cumulative += probability  # Declared literal left-to-right CDF arithmetic.
        if draw < cumulative:
            chosen = index
            break
    if chosen is None:
        # Finite floating summation can leave a sub-ulp final gap. A zero-mass
        # tail may never be selected; choose the last positive mass only.
        chosen = max(index for index, probability in enumerate(p) if probability > 0.0)
    return {'chosen_index': chosen, 'chosen_id': distribution_record['action_ids'][chosen],
            'draw': draw, 'chosen_probability': p[chosen],
            'chosen_softmax_probability': distribution_record['softmax'][chosen],
            'CDF_arithmetic': 'literal left-to-right +=; strict draw<cumulative; last-positive roundoff fallback'}


def score_gradient(distribution_record, chosen_index):
    """Gradient of log MIXTURE probability, not plain-softmax gradient."""
    if type(chosen_index) is not int or not 0 <= chosen_index < len(distribution_record['features']):
        raise ValueError('literal chosen action index required')
    q = distribution_record['softmax']; p = distribution_record['probabilities']
    if p[chosen_index] <= 0.0:
        raise ValueError('zero probability choice has no log gradient')
    names = distribution_record['feature_names']
    features = distribution_record['features']
    expected = {name: math.fsum(q[index] * item.get(name, 0.0)
                              for index, item in enumerate(features)) for name in names}
    factor = ((1.0 - distribution_record['epsilon']) * q[chosen_index] /
              p[chosen_index] / distribution_record['temperature'])
    result = {name: factor * (features[chosen_index].get(name, 0.0) - expected[name]) for name in names}
    if any(not math.isfinite(value) for value in result.values()):
        raise ValueError('nonfinite score gradient')
    return {'gradient': result, 'expected_softmax_features': expected, 'mixture_gradient_factor': factor}


def reward(*, producer_primitive_certificate_passed, maximum_distinct_dependency_complete_nonroot_facts,
           logical_rows, primitive_attempts, attempt_limit, construction_validation_checks,
           check_ceiling, retired_commits, commits):
    """Pure counters only; caller/auditor must establish their source semantics.

Pending outputs, empty-row marks and exterior receptor aliases are NOT facts.
This function cannot prove that its caller counted them correctly. A producer
certificate bonus stays provisional until the entire independent audit passes.
"""
    if type(producer_primitive_certificate_passed) is not bool:
        raise ValueError('literal provisional certificate flag required')
    counts = (maximum_distinct_dependency_complete_nonroot_facts, logical_rows,
              primitive_attempts, attempt_limit, construction_validation_checks,
              check_ceiling, retired_commits, commits)
    if any(type(item) is not int or item < 0 for item in counts):
        raise ValueError('literal nonnegative integer reward counters required')
    if logical_rows < 1 or attempt_limit < 1 or check_ceiling < 1 or retired_commits > commits:
        raise ValueError('positive denominators and coherent commit counts required')
    if maximum_distinct_dependency_complete_nonroot_facts > logical_rows:
        raise ValueError('completion potential is per state, never accumulated rediscovery')
    shaping = 0.05 * maximum_distinct_dependency_complete_nonroot_facts / logical_rows
    attempt_cost = 0.10 * min(1.0, primitive_attempts / attempt_limit)
    construction_cost = 0.05 * min(1.0, construction_validation_checks / check_ceiling)
    retirement_cost = 0.01 * retired_commits / max(1, commits)
    terminal = float(producer_primitive_certificate_passed)
    value = math.fsum((terminal, shaping, -attempt_cost, -construction_cost, -retirement_cost))
    return {'return': value, 'terminal': terminal, 'shaping': shaping,
            'attempt_cost': attempt_cost, 'construction_cost': construction_cost,
            'retirement_cost': retirement_cost,
            'scope': 'Source-verified counters required; provisional certificate reward is not a solved-theorem count.'}


def update(weights, saved_score_gradients, episode_return, baseline, *, executed,
           learning_rate=0.05, ema_alpha=0.2, direction_norm_ceiling=1.0):
    """Episode mean-gradient heuristic; multiply advantage BEFORE clipping.

Caller logs every distribution/choice/gradient and freezes weights per episode.
Unexecuted episodes must not call this update. Empty executed episodes change
only the EMA, with zero gradient; that is not evidence that a policy learned.
"""
    if executed is not True:
        raise ValueError('no update for unexecuted or unqualified episode')
    w = vector(weights, 'weights')
    if not isinstance(saved_score_gradients, (list, tuple)):
        raise ValueError('complete saved score-gradient sequence required')
    gradients = [vector(item, 'gradient') for item in saved_score_gradients]
    return_value = finite_number(episode_return, 'episode return')
    old_baseline = finite_number(baseline, 'baseline')
    rate = finite_number(learning_rate, 'learning rate')
    alpha = finite_number(ema_alpha, 'EMA alpha')
    ceiling = finite_number(direction_norm_ceiling, 'direction norm ceiling')
    if rate < 0.0 or not 0.0 <= alpha <= 1.0 or ceiling <= 0.0:
        raise ValueError('nonnegative learning rate, unit EMA alpha and positive norm ceiling required')
    names = sorted(set(w).union(*(set(item) for item in gradients)))
    count = len(gradients)
    mean = {name: math.fsum(item.get(name, 0.0) for item in gradients) / max(1, count) for name in names}
    advantage = return_value - old_baseline
    direction = {name: advantage * mean[name] for name in names}
    score_norm = math.sqrt(math.fsum(value * value for value in mean.values()))
    preclip_norm = math.sqrt(math.fsum(value * value for value in direction.values()))
    scale = min(1.0, ceiling / preclip_norm) if preclip_norm else 1.0
    increment = {name: rate * scale * direction[name] for name in names}
    changed = {name: math.fsum((w.get(name, 0.0), increment[name])) for name in names}
    new_baseline = math.fsum(((1.0 - alpha) * old_baseline, alpha * return_value))
    if any(not math.isfinite(value) for value in (*changed.values(), new_baseline, preclip_norm)):
        raise ValueError('nonfinite learned update')
    return {'version': VERSION, 'old_weights': w, 'weights': changed, 'old_baseline': old_baseline,
            'baseline': new_baseline, 'return': return_value, 'advantage': advantage,
            'choice_count': count, 'mean_score_gradient': mean, 'score_gradient_L2': score_norm,
            'advantage_direction_L2_before_clip': preclip_norm, 'clip_scale': scale,
            'direction_L2_after_clip': preclip_norm * scale, 'increment': increment,
            'learning_rate': rate, 'ema_alpha': alpha, 'direction_norm_ceiling': ceiling,
            'scope': 'Episode-averaged/clipped heuristic, not an unbiased expected-return gradient claim.'}
