#!/usr/bin/env python3
"""Finite group-balanced automaton over target-free port obligations.

The input trajectory is produced by an exact frozen executor.  This module
forgets concrete port identities and keeps only a bounded, permutation-
invariant symbol for each transition: selected-role discharge/production,
relation gain/loss/retention, contradiction flags, and simultaneous selected-
pair incidence.  Training groups contribute one mean label per state so a
large orbit cannot manufacture evidence.

The automaton is a marking only.  It scores an already existing exact branch;
it cannot create geometry, change a candidate, inspect a target, or certify a
stationary production.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json


ROLE_RELATIONS = (
    "backward", "forward", "reverse", "same_parent", "same_source",
    "touch_parent", "touch_source",
)
CONTRADICTION_FLAGS = (
    "forward_depleted", "no_forward_after", "no_reverse_after",
    "no_touch_source_after", "source_touch_depleted",
)
PAIR_RELATIONS = (
    "backward", "forward", "reverse", "same_parent", "same_source",
    "touch_parent", "touch_source",
)


@dataclass(frozen=True)
class PortObligationAutomatonSpec:
    count_cap: int = 4
    minimum_groups: int = 1
    weakest_states: int = 4


@dataclass(frozen=True)
class PortObligationState:
    symbol: tuple
    training_groups: tuple[int, ...]
    group_positive_rates: tuple[float, ...]
    posterior: float


@dataclass(frozen=True)
class FrozenPortObligationAutomaton:
    spec: PortObligationAutomatonSpec
    states: tuple[PortObligationState, ...]
    model_digest: str
    target_used: bool = False
    candidate_geometry_changed: bool = False


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _bounded(value, cap):
    value = int(value)
    if value < 0:
        raise ValueError("obligation counts must be nonnegative")
    return min(cap, value)


def transition_symbol(transition, spec):
    """Canonicalize one executor transition without concrete role identity."""
    if spec.count_cap < 1:
        raise ValueError("count cap must be positive")
    cap = spec.count_cap
    roles = []
    for row in transition["selected_role_transitions"]:
        relation_counts = row["relation_counts"]
        flags = row["contradiction_flags"]
        roles.append((
            _bounded(row["before"], cap),
            _bounded(row["after"], cap),
            _bounded(row["discharged"], cap),
            _bounded(row["produced"], cap),
            tuple(int(bool(flags[name])) for name in CONTRADICTION_FLAGS),
            tuple((
                _bounded(relation_counts[name]["lost"], cap),
                _bounded(relation_counts[name]["gained"], cap),
                _bounded(relation_counts[name]["after"], cap),
            ) for name in ROLE_RELATIONS),
        ))
    pairs = tuple(sorted(tuple(int(bool(row[name]))
                               for name in PAIR_RELATIONS)
                         for row in transition["selected_pair_relations"]))
    return tuple(sorted(roles)), pairs


def trajectory_symbols(transitions, spec):
    return tuple(transition_symbol(row, spec) for row in transitions)


def fit_port_obligation_automaton(rows, spec=PortObligationAutomatonSpec()):
    rows = tuple(rows)
    if not rows:
        raise ValueError("cannot fit an empty obligation corpus")
    if spec.minimum_groups < 1 or spec.weakest_states < 1:
        raise ValueError("automaton bounds must be positive")
    observations = defaultdict(lambda: defaultdict(list))
    for row in rows:
        group = int(row["group"])
        label = float(bool(row["fit_label"]))
        symbols = set(trajectory_symbols(row["transitions"], spec))
        for symbol in symbols:
            observations[symbol][group].append(label)
    states = []
    for symbol, by_group in observations.items():
        if len(by_group) < spec.minimum_groups:
            continue
        groups = tuple(sorted(by_group))
        rates = tuple(sum(by_group[group]) / len(by_group[group])
                      for group in groups)
        posterior = (1. + sum(rates)) / (2. + len(rates))
        states.append(PortObligationState(
            symbol, groups, rates, posterior))
    states = tuple(sorted(states, key=lambda row: repr(row.symbol)))
    body = {
        "spec": asdict(spec),
        "states": tuple(asdict(row) for row in states),
    }
    return FrozenPortObligationAutomaton(spec, states, _digest(body))


def score_port_obligation_trajectory(model, transitions):
    transitions = tuple(transitions)
    state_map = {row.symbol: row.posterior for row in model.states}
    values = [state_map[symbol] for symbol in trajectory_symbols(
        transitions, model.spec) if symbol in state_map]
    if not values:
        return 0., 0.
    weakest = sorted(values)[:model.spec.weakest_states]
    return sum(weakest) / len(weakest), len(values) / len(transitions)


__all__ = [
    "FrozenPortObligationAutomaton", "PortObligationAutomatonSpec",
    "PortObligationState", "fit_port_obligation_automaton",
    "score_port_obligation_trajectory", "trajectory_symbols",
    "transition_symbol",
]
