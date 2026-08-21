#!/usr/bin/env python3
"""Soft metric over identity-free, role-conditioned port obligations.

Unlike an aggregate backoff, this representation retains which colored
parent→source role owns each discharge, contradiction, and relational count.
Optional separation channels split roles at a median learned only from the
training rows.  Optional pair channels retain relations between simultaneous
selected roles.  A frozen k-nearest model takes at most one vote per training
nucleus and only ranks immutable exact executor actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import statistics

from materials_gcts_port_obligation_automaton import (
    CONTRADICTION_FLAGS, PAIR_RELATIONS, ROLE_RELATIONS)


COLORS = ("X", "Y", "Z")
ROLE_VALUE_COUNT = 4 + len(CONTRADICTION_FLAGS) + 3 * len(ROLE_RELATIONS)


@dataclass(frozen=True)
class PortObligationRoleMetricSpec:
    horizon: int
    separation_channels: bool
    pair_channels: bool
    neighbors: int
    weighted: bool


@dataclass(frozen=True)
class FrozenPortObligationRoleMetric:
    spec: PortObligationRoleMetricSpec
    separation_threshold: float
    means: tuple[float, ...]
    scales: tuple[float, ...]
    training_rows: tuple[dict, ...]
    model_digest: str
    target_used: bool = False
    candidate_geometry_changed: bool = False
    raw_role_ids_or_coordinates_serialized: bool = False


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _color(value):
    symbol = str(value).strip("'\"")
    if symbol not in COLORS:
        raise ValueError(f"unsupported role color {symbol}")
    return COLORS.index(symbol)


def learn_separation_threshold(rows):
    values = tuple(float(item["role"][4])
                   for row in rows for transition in row["transitions"]
                   for item in transition["selected_role_transitions"])
    if not values:
        return 0.
    return float(statistics.median(values))


def _channel(role, separation_channels, threshold):
    channel = _color(role[0]) * len(COLORS) + _color(role[2])
    if separation_channels:
        channel = channel * 2 + int(float(role[4]) > threshold)
    return channel


def role_conditioned_features(transitions, spec, separation_threshold):
    if spec.horizon < 1 or spec.neighbors < 1:
        raise ValueError("metric horizon and neighbor count must be positive")
    transitions = tuple(transitions[:spec.horizon])
    channels = len(COLORS) ** 2 * (2 if spec.separation_channels else 1)
    nodes = [[0.] * ROLE_VALUE_COUNT for _ in range(channels)]
    pairs = [[[0.] * len(PAIR_RELATIONS) for _ in range(channels)]
             for _ in range(channels)] if spec.pair_channels else None
    for transition in transitions:
        selected = tuple(transition["selected_role_transitions"])
        selected_channels = []
        for row in selected:
            channel = _channel(
                row["role"], spec.separation_channels,
                separation_threshold)
            selected_channels.append(channel)
            values = (
                tuple(float(row[name]) for name in (
                    "before", "after", "discharged", "produced")) +
                tuple(float(bool(row["contradiction_flags"][name]))
                      for name in CONTRADICTION_FLAGS) +
                tuple(float(row["relation_counts"][name][field])
                      for name in ROLE_RELATIONS
                      for field in ("lost", "gained", "after"))
            )
            for index, value in enumerate(values):
                nodes[channel][index] += value
        if pairs is not None:
            for row in transition["selected_pair_relations"]:
                left = selected_channels[int(row["left_rank"])]
                right = selected_channels[int(row["right_rank"])]
                for index, name in enumerate(PAIR_RELATIONS):
                    pairs[left][right][index] += float(bool(row[name]))
    divisor = max(1, len(transitions))
    result = [value / divisor for channel in nodes for value in channel]
    if pairs is not None:
        result.extend(value / divisor for left in pairs
                      for right in left for value in right)
    return tuple(result)


def _standardizer(rows, spec, threshold):
    vectors = tuple(role_conditioned_features(
        row["transitions"], spec, threshold) for row in rows)
    means = tuple(sum(vector[index] for vector in vectors) / len(vectors)
                  for index in range(len(vectors[0])))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (vector[index] - means[index]) ** 2 for vector in vectors) /
        len(vectors))) for index in range(len(means)))
    return vectors, means, scales


def fit_port_obligation_role_metric(rows, spec):
    rows = tuple(rows)
    if not rows:
        raise ValueError("cannot fit an empty role metric")
    threshold = learn_separation_threshold(rows) \
        if spec.separation_channels else 0.
    vectors, means, scales = _standardizer(rows, spec, threshold)
    detached = tuple({
        "group": int(row["group"]),
        "candidate_id": str(row["candidate_id"]),
        "fit_label": bool(row["fit_label"]),
        "features": vector,
    } for row, vector in zip(rows, vectors))
    body = {
        "spec": asdict(spec), "separation_threshold": threshold,
        "means": means, "scales": scales, "training": detached,
    }
    return FrozenPortObligationRoleMetric(
        spec, threshold, means, scales, detached, _digest(body))


def score_port_obligation_role_metric(model, transitions):
    vector = role_conditioned_features(
        transitions, model.spec, model.separation_threshold)
    nearest_by_group = {}
    for row in model.training_rows:
        distance = sum(((left - right) / scale) ** 2
                       for left, right, scale in zip(
                           vector, row["features"], model.scales))
        record = (distance, row["candidate_id"],
                  float(row["fit_label"]))
        prior = nearest_by_group.get(row["group"])
        if prior is None or record[:2] < prior[:2]:
            nearest_by_group[row["group"]] = record
    nearest = sorted(nearest_by_group.values())[:model.spec.neighbors]
    if not nearest:
        return 0.
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if model.spec.weighted else 1.
                    for distance, _candidate, _label in nearest)
    return sum(weight * row[2] for weight, row in zip(weights, nearest)) / \
        sum(weights)


__all__ = [
    "COLORS", "FrozenPortObligationRoleMetric",
    "PortObligationRoleMetricSpec", "fit_port_obligation_role_metric",
    "learn_separation_threshold", "role_conditioned_features",
    "score_port_obligation_role_metric",
]
