"""Numeric clause ordering for the lifted proof-search experiment.

The search owns applicability and fairness. A selector returns only an index
of an offered clause. The learner receives one checked, cost-sensitive return
per episode, following the earlier demand-policy experiment's linear softmax
policy gradient.
"""

from math import exp, isfinite, log1p, sqrt
from random import Random


FEATURES = (
    "unit",
    "negative unit",
    "clause width",
    "symbol count",
    "term depth",
    "variable count",
    "input clause",
    "goal ancestry",
    "goal predicate overlap",
    "active opposite head present",
    "active opposite-head count",
    "unit with active opposite head",
    "derivation depth",
    "waiting age",
    "window position",
)


def clause_features(option, position, length):
    """Use bounded structural features and no theorem or symbol names."""
    unit = option["literals"] == 1
    active = option["active_matches"]
    return (
        float(unit),
        float(unit and not option["clause"][0][0]),
        min(option["literals"], 8) / 8,
        min(option["symbols"], 48) / 48,
        min(option["depth"], 12) / 12,
        min(option["variables"], 8) / 8,
        float(option["input"]),
        float(option["origin_goal"]),
        min(option["goal_overlap"], 4) / 4,
        float(active > 0),
        min(log1p(active) / 5, 1.0),
        float(unit and active > 0),
        min(option["derivation_depth"], 16) / 16,
        min(option["age"], 24) / 24,
        position / max(1, length - 1),
    )


def _goal_priority(option):
    return (
        (2.0 if option["literals"] == 1 else 0.0)
        + (1.5 if option["origin_goal"] else 0.0)
        + min(option["goal_overlap"], 3)
        + 0.75 * min(log1p(option["active_matches"]), 4.0)
        - 0.12 * option["symbols"]
    )


def fixed_selector(name, seed=0):
    """Construct a fixed-order control using the same eligible shortlist."""
    if name == "fifo":
        return lambda options, step: 0
    if name == "random":
        rng = Random(seed)
        return lambda options, step: rng.randrange(len(options))
    if name == "size":
        return lambda options, step: min(
            range(len(options)), key=lambda i: (
                options[i]["symbols"], options[i]["literals"], i,
            ),
        )
    if name == "goal":
        return lambda options, step: max(
            range(len(options)), key=lambda i: _goal_priority(options[i]),
        )
    raise ValueError(f"unknown fixed policy: {name}")


def checked_reward(checked, work, *, reference=1000.0):
    """Reward a replayed proof and charge a bounded logarithmic work cost."""
    if work < 0 or reference <= 0:
        raise ValueError("reward requires nonnegative work and positive reference")
    cost = min(log1p(work) / log1p(reference), 1.0)
    return (1.0 if checked else -0.5) - 0.5 * cost


class SelectionEpisode:
    def __init__(self, weights, rng=None):
        self.weights = weights
        self.rng = rng
        self.trace = [0.0] * len(weights) if rng is not None else None
        self.decisions = 0
        self.ranked = 0
        self.non_fifo = 0

    def __call__(self, options, step):
        if len(options) == 1:
            return 0
        rows = [clause_features(option, i, len(options)) for i, option in enumerate(options)]
        scores = [sum(w * x for w, x in zip(self.weights, row)) for row in rows]
        if self.rng is None:
            selected = max(range(len(scores)), key=scores.__getitem__)
        else:
            peak = max(scores)
            mass = [exp(score - peak) for score in scores]
            total = sum(mass)
            selected = self.rng.choices(range(len(mass)), weights=mass, k=1)[0]
            for i, values in enumerate(zip(*rows)):
                mean = sum(value * weight for value, weight in zip(values, mass)) / total
                # Keep a discounted eligibility trace without retaining clauses.
                self.trace[i] = 0.99 * self.trace[i] + rows[selected][i] - mean
        self.decisions += 1
        self.ranked += len(options)
        self.non_fifo += int(selected != 0)
        return selected


class NumericPolicy:
    def __init__(self, seed=0, learning_rate=0.15):
        if not isfinite(learning_rate) or learning_rate <= 0:
            raise ValueError("learning rate must be positive and finite")
        self.seed = seed
        self.learning_rate = learning_rate
        self.weights = (0.0,) * len(FEATURES)
        self.updates = 0
        self._baseline = 0.0
        self._rng = Random(seed)
        self._frozen = False

    def selector(self, *, train=False, seed=None):
        """Sample only during training. Frozen evaluation uses deterministic argmax."""
        if train and self._frozen:
            raise ValueError("a frozen policy cannot start a training episode")
        rng = None
        if train:
            rng = Random(self._rng.getrandbits(64) if seed is None else seed)
        return SelectionEpisode(self.weights, rng)

    def update(self, episode, reward):
        if self._frozen or episode.trace is None or episode.weights is not self.weights:
            raise ValueError("expected a current training episode")
        if not isfinite(reward):
            raise ValueError("reward must be finite")
        advantage = reward - self._baseline
        self._baseline += 0.1 * advantage
        scale = self.learning_rate * advantage / sqrt(max(1, episode.decisions))
        self.weights = tuple(
            max(-8.0, min(8.0, weight + scale * gradient))
            for weight, gradient in zip(self.weights, episode.trace)
        )
        episode.trace = None
        self.updates += 1

    def snapshot(self):
        return {
            "features": list(FEATURES),
            "weights": list(self.weights),
            "seed": self.seed,
            "updates": self.updates,
        }

    @classmethod
    def from_snapshot(cls, snapshot):
        if tuple(snapshot["features"]) != FEATURES:
            raise ValueError("snapshot feature layout does not match")
        weights = tuple(float(w) for w in snapshot["weights"])
        if len(weights) != len(FEATURES) or any(not isfinite(w) for w in weights):
            raise ValueError("snapshot weights must match the feature layout")
        policy = cls(seed=snapshot["seed"])
        policy.weights = weights
        policy.updates = int(snapshot["updates"])
        policy._frozen = True
        return policy
