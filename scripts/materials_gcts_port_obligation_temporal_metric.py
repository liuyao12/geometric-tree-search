#!/usr/bin/env python3
"""Temporal, identity-free metric over bounded port-obligation traces.

The earlier role metric pooled every transition into one histogram and thereby
forgot *when* a connection was discharged or contradicted.  This module keeps
the same finite colored parent→source role channels, but concatenates a global
summary with a fixed number of ordered time bins.  It remains a marking only:
exact action geometry, ports, collision checks, and replay certificates stay
outside the model and are never changed or authorized by it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math

from materials_gcts_port_obligation_role_metric import (
    PortObligationRoleMetricSpec, learn_separation_threshold,
    role_conditioned_features)


@dataclass(frozen=True)
class PortObligationTemporalMetricSpec:
    horizon: int
    time_bins: int
    separation_channels: bool
    neighbors: int
    weighted: bool


@dataclass(frozen=True)
class FrozenPortObligationTemporalMetric:
    spec: PortObligationTemporalMetricSpec
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


def temporal_role_features(transitions, spec, separation_threshold):
    if spec.horizon < 1 or spec.time_bins < 2:
        raise ValueError("temporal horizon must be positive and use >=2 bins")
    if spec.time_bins > spec.horizon:
        raise ValueError("time bins cannot exceed the temporal horizon")
    transitions = tuple(transitions[:spec.horizon])
    base_spec = PortObligationRoleMetricSpec(
        spec.horizon, spec.separation_channels, False, 1, False)
    features = list(role_conditioned_features(
        transitions, base_spec, separation_threshold))
    for bin_index in range(spec.time_bins):
        start = bin_index * spec.horizon // spec.time_bins
        stop = (bin_index + 1) * spec.horizon // spec.time_bins
        bin_spec = PortObligationRoleMetricSpec(
            max(1, stop - start), spec.separation_channels, False, 1, False)
        features.extend(role_conditioned_features(
            transitions[start:stop], bin_spec, separation_threshold))
    return tuple(features)


def _standardizer(rows, spec, threshold):
    vectors = tuple(temporal_role_features(
        row["transitions"], spec, threshold) for row in rows)
    means = tuple(sum(vector[index] for vector in vectors) / len(vectors)
                  for index in range(len(vectors[0])))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (vector[index] - means[index]) ** 2 for vector in vectors) /
        len(vectors))) for index in range(len(means)))
    return vectors, means, scales


def fit_port_obligation_temporal_metric(rows, spec):
    rows = tuple(rows)
    if not rows:
        raise ValueError("cannot fit an empty temporal obligation metric")
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
    return FrozenPortObligationTemporalMetric(
        spec, threshold, means, scales, detached, _digest(body))


def score_port_obligation_temporal_metric(model, transitions):
    vector = temporal_role_features(
        transitions, model.spec, model.separation_threshold)
    nearest_by_group = {}
    for row in model.training_rows:
        distance = sum(((left - right) / scale) ** 2
                       for left, right, scale in zip(
                           vector, row["features"], model.scales))
        record = distance, row["candidate_id"], float(row["fit_label"])
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
    "FrozenPortObligationTemporalMetric",
    "PortObligationTemporalMetricSpec",
    "fit_port_obligation_temporal_metric",
    "score_port_obligation_temporal_metric", "temporal_role_features",
]
