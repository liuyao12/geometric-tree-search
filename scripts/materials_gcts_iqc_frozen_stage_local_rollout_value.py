#!/usr/bin/env python3
"""Freeze the significant augmented stage-local rollout value model.

The development audit selects one representation/specification with grouped
whole-nucleus validation and 31 label-shuffle refits.  This module performs the
one allowed final fit on all twenty consumed development nuclei.  A future
candidate supplies only its already-frozen target-free rollout; scoring never
receives target atoms, absolute coordinates, material labels, or candidate
IDs.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_metric_audit import (
    MODEL_SPECS, _candidate_id, _vector)
from materials_gcts_iqc_stage_local_augmented_rollout_dataset import (
    load_default_dataset)
from materials_gcts_iqc_stage_local_augmented_rollout_value_audit import (
    EXPECTED_AUDIT_DIGEST, evaluate as development_audit)
from materials_gcts_port_obligation_temporal_metric import (
    PortObligationTemporalMetricSpec)
from materials_gcts_port_obligation_role_metric import (
    learn_separation_threshold)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_frozen_stage_local_rollout_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "1d8de219521e2a8568706a3c0467f96efef106a42553319466291fffde9644b6"
EXPECTED_MODEL_DIGEST = \
    "e0f67c875da55a430e9d4eab1a429939378bd325848fa108750e37b7895dee98"


@dataclass(frozen=True)
class FrozenRolloutTrainingRow:
    group: int
    features: tuple[float, ...]
    exact: bool
    stable_key: str


@dataclass(frozen=True)
class FrozenStageLocalRolloutValue:
    model_id: str
    family: str
    spec: PortObligationTemporalMetricSpec
    separation_threshold: float
    means: tuple[float, ...]
    scales: tuple[float, ...]
    training_rows: tuple[FrozenRolloutTrainingRow, ...]
    source_dataset_digest: str
    source_audit_digest: str
    model_digest: str
    target_used: bool = False


def _geometry(dataset):
    return tuple({
        "group": int(group["group"]),
        "candidate_index": int(row["candidate_index"]),
        "transitions": row["transitions"], "trace": row["trace"],
        "exact": bool(row["exact"]),
    } for group in dataset["groups"] for row in group["rows"])


def _standardize(vector, means, scales):
    return tuple((float(value) - mean) / scale
                 for value, mean, scale in zip(vector, means, scales))


def fit_default_model() -> FrozenStageLocalRolloutValue:
    dataset = load_default_dataset()
    audit = development_audit()
    if audit["audit_digest"] != EXPECTED_AUDIT_DIGEST or \
            not audit["augmented_rollout_gate_passed"]:
        raise AssertionError("augmented rollout gate is not frozen")
    model_id = str(audit["selected_model"]["model_id"])
    selected = next((family, spec) for candidate, family, spec in MODEL_SPECS
                    if candidate == model_id)
    family, spec = selected
    if family != "temporal":
        raise AssertionError("frozen rollout model must be temporal")
    rows = _geometry(dataset)
    threshold = learn_separation_threshold(rows) \
        if spec.separation_channels else 0.
    vectors = tuple(tuple(map(float, _vector(row, family, spec, threshold)))
                    for row in rows)
    width = len(vectors[0])
    means = tuple(sum(row[index] for row in vectors) / len(vectors)
                  for index in range(width))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (row[index] - means[index]) ** 2 for row in vectors) / len(vectors)))
                   for index in range(width))
    training = tuple(FrozenRolloutTrainingRow(
        int(row["group"]), _standardize(vector, means, scales),
        bool(row["exact"]), _candidate_id(row))
                     for row, vector in zip(rows, vectors))
    body = {
        "model_id": model_id, "family": family, "spec": asdict(spec),
        "separation_threshold": threshold, "means": means,
        "scales": scales,
        "training_rows": tuple(asdict(row) for row in training),
        "source_dataset_digest": dataset["dataset_digest"],
        "source_audit_digest": audit["audit_digest"],
        "development_labels_used_for_final_fit": True,
        "fresh_confirmation_target_used": False,
        "candidate_geometry_authorized": False,
    }
    return FrozenStageLocalRolloutValue(
        model_id, family, spec, threshold, means, scales, training,
        dataset["dataset_digest"], audit["audit_digest"], _digest(body))


def score_rollout(model: FrozenStageLocalRolloutValue, transitions, trace):
    if model.target_used:
        raise ValueError("target-tainted rollout model")
    row = {"transitions": transitions, "trace": trace}
    vector = _vector(row, model.family, model.spec,
                     model.separation_threshold)
    standardized = _standardize(vector, model.means, model.scales)
    nearest_by_group = {}
    for training in model.training_rows:
        distance = sum((left - right) ** 2 for left, right in zip(
            standardized, training.features))
        record = (distance, training.stable_key, training.exact)
        if training.group not in nearest_by_group or \
                record[:2] < nearest_by_group[training.group][:2]:
            nearest_by_group[training.group] = record
    nearest = sorted(nearest_by_group.values())[:model.spec.neighbors]
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if model.spec.weighted else 1. for distance, _key, _ in nearest)
    return sum(weight * float(row[2]) for weight, row in zip(weights, nearest)) / \
        sum(weights)


def _payload(model):
    return {
        "model_id": model.model_id, "family": model.family,
        "spec": asdict(model.spec),
        "separation_threshold": model.separation_threshold,
        "means": model.means, "scales": model.scales,
        "training_rows": tuple(asdict(row) for row in model.training_rows),
        "source_dataset_digest": model.source_dataset_digest,
        "source_audit_digest": model.source_audit_digest,
        "model_digest": model.model_digest, "target_used": model.target_used,
    }


def load_default_model(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("frozen rollout model byte drift")
    payload = json.loads(gzip.decompress(raw))
    spec = PortObligationTemporalMetricSpec(**payload["spec"])
    rows = tuple(FrozenRolloutTrainingRow(
        int(row["group"]), tuple(map(float, row["features"])),
        bool(row["exact"]), str(row["stable_key"]))
                 for row in payload["training_rows"])
    model = FrozenStageLocalRolloutValue(
        str(payload["model_id"]), str(payload["family"]), spec,
        float(payload["separation_threshold"]),
        tuple(map(float, payload["means"])),
        tuple(map(float, payload["scales"])), rows,
        str(payload["source_dataset_digest"]),
        str(payload["source_audit_digest"]), str(payload["model_digest"]),
        bool(payload["target_used"]))
    if EXPECTED_MODEL_DIGEST and model.model_digest != EXPECTED_MODEL_DIGEST:
        raise AssertionError("unexpected frozen rollout model")
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("frozen rollout fixture already exists")
    model = fit_default_model()
    text = json.dumps(_payload(model), indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
