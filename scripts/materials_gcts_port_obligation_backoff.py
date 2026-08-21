#!/usr/bin/env python3
"""Finite identity-free backoff for sequential port-obligation markings.

Exact executor actions and proper-SE(3) geometry remain outside this model.
For each already-frozen transition the marking first looks for a supported
fine state, then (if configured) a role-shape state, and finally an aggregate
contradiction state.  The first supported state supplies one group-balanced
posterior.  No raw port/type IDs, coordinates, material labels, or target
atoms enter a state.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json

from materials_gcts_port_obligation_automaton import (
    CONTRADICTION_FLAGS, PAIR_RELATIONS, ROLE_RELATIONS)


LEVEL_KINDS = ("exact", "role_shape", "aggregate")


@dataclass(frozen=True)
class PortObligationBackoffLevel:
    kind: str
    count_cap: int
    minimum_groups: int = 1


@dataclass(frozen=True)
class PortObligationBackoffSpec:
    levels: tuple[PortObligationBackoffLevel, ...]
    weakest_states: int = 8


@dataclass(frozen=True)
class PortObligationBackoffState:
    level_index: int
    symbol: tuple
    training_groups: tuple[int, ...]
    group_positive_rates: tuple[float, ...]
    posterior: float


@dataclass(frozen=True)
class FrozenPortObligationBackoff:
    spec: PortObligationBackoffSpec
    states: tuple[PortObligationBackoffState, ...]
    model_digest: str
    target_used: bool = False
    candidate_geometry_changed: bool = False
    raw_role_ids_or_coordinates_serialized: bool = False


@dataclass(frozen=True)
class PortObligationBackoffScore:
    score: float
    recognized_fraction: float
    level_hits: tuple[int, ...]
    unrecognized_transitions: int


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _bounded(value, cap):
    value = int(value)
    if value < 0:
        raise ValueError("obligation counts must be nonnegative")
    return min(int(cap), value)


def _role_row(row, cap, *, relation_presence):
    basic = tuple(_bounded(row[name], cap) for name in (
        "before", "after", "discharged", "produced"))
    flags = tuple(int(bool(row["contradiction_flags"][name]))
                  for name in CONTRADICTION_FLAGS)
    relations = tuple(tuple(_bounded(
        row["relation_counts"][name][field], cap)
        for field in ("lost", "gained", "after"))
        for name in ROLE_RELATIONS)
    if relation_presence:
        relations = tuple(tuple(int(value > 0) for value in values)
                          for values in relations)
    return basic, flags, relations


def transition_backoff_symbol(transition, level):
    if level.kind not in LEVEL_KINDS:
        raise ValueError(f"unsupported obligation backoff level {level.kind}")
    if level.count_cap < 1 or level.minimum_groups < 1:
        raise ValueError("backoff bounds must be positive")
    cap = level.count_cap
    roles = tuple(transition["selected_role_transitions"])
    pairs = tuple(transition["selected_pair_relations"])
    pair_rows = tuple(sorted(tuple(int(bool(row[name]))
                                   for name in PAIR_RELATIONS)
                             for row in pairs))
    if level.kind == "exact":
        return ("exact", tuple(sorted(
            _role_row(row, cap, relation_presence=False)
            for row in roles)), pair_rows)
    if level.kind == "role_shape":
        return ("role_shape", tuple(sorted(
            _role_row(row, cap, relation_presence=True)
            for row in roles)), pair_rows)

    basic = tuple(_bounded(sum(int(row[name]) for row in roles), cap)
                  for name in ("before", "after", "discharged", "produced"))
    flags = tuple(_bounded(sum(int(bool(
        row["contradiction_flags"][name])) for row in roles), cap)
        for name in CONTRADICTION_FLAGS)
    relations = tuple(tuple(_bounded(sum(int(
        row["relation_counts"][name][field]) for row in roles), cap)
        for field in ("lost", "gained", "after"))
        for name in ROLE_RELATIONS)
    pair_counts = tuple(_bounded(sum(int(bool(row[name])) for row in pairs),
                                 cap) for name in PAIR_RELATIONS)
    return ("aggregate", _bounded(len(roles), cap), basic, flags,
            relations, pair_counts)


def trajectory_backoff_symbols(transitions, level):
    return tuple(transition_backoff_symbol(row, level)
                 for row in transitions)


def fit_port_obligation_backoff(rows, spec):
    rows = tuple(rows)
    if not rows or not spec.levels:
        raise ValueError("cannot fit an empty obligation backoff")
    if spec.weakest_states < 1:
        raise ValueError("weakest state count must be positive")
    if len({level.kind for level in spec.levels}) != len(spec.levels):
        raise ValueError("backoff levels must have distinct kinds")
    observations = tuple(defaultdict(lambda: defaultdict(list))
                         for _ in spec.levels)
    for row in rows:
        group = int(row["group"])
        label = float(bool(row["fit_label"]))
        for level_index, level in enumerate(spec.levels):
            symbols = set(trajectory_backoff_symbols(
                row["transitions"], level))
            for symbol in symbols:
                observations[level_index][symbol][group].append(label)
    states = []
    for level_index, (level, by_symbol) in enumerate(zip(
            spec.levels, observations)):
        for symbol, by_group in by_symbol.items():
            if len(by_group) < level.minimum_groups:
                continue
            groups = tuple(sorted(by_group))
            rates = tuple(sum(by_group[group]) / len(by_group[group])
                          for group in groups)
            states.append(PortObligationBackoffState(
                level_index, symbol, groups, rates,
                (1. + sum(rates)) / (2. + len(rates))))
    states = tuple(sorted(states, key=lambda row: (
        row.level_index, repr(row.symbol))))
    body = {
        "spec": asdict(spec),
        "states": tuple(asdict(row) for row in states),
    }
    return FrozenPortObligationBackoff(spec, states, _digest(body))


def score_port_obligation_backoff(model, transitions):
    transitions = tuple(transitions)
    state_maps = tuple({} for _ in model.spec.levels)
    for row in model.states:
        state_maps[row.level_index][row.symbol] = row.posterior
    values = []
    level_hits = [0 for _ in model.spec.levels]
    unrecognized = 0
    for transition in transitions:
        for level_index, level in enumerate(model.spec.levels):
            symbol = transition_backoff_symbol(transition, level)
            if symbol in state_maps[level_index]:
                values.append(state_maps[level_index][symbol])
                level_hits[level_index] += 1
                break
        else:
            unrecognized += 1
    if not values:
        return PortObligationBackoffScore(
            0., 0., tuple(level_hits), unrecognized)
    weakest = sorted(values)[:model.spec.weakest_states]
    return PortObligationBackoffScore(
        sum(weakest) / len(weakest),
        len(values) / len(transitions),
        tuple(level_hits), unrecognized)


__all__ = [
    "FrozenPortObligationBackoff", "LEVEL_KINDS",
    "PortObligationBackoffLevel", "PortObligationBackoffScore",
    "PortObligationBackoffSpec", "PortObligationBackoffState",
    "fit_port_obligation_backoff", "score_port_obligation_backoff",
    "trajectory_backoff_symbols", "transition_backoff_symbol",
]
