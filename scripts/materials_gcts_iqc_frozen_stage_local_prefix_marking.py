#!/usr/bin/env python3
"""Freeze the passing consumed-development stage-local IQC marking.

The artifact stores only selected target-free feature channels, standardized
training vectors, group IDs, and viability labels from the consumed corpus.
It contains no development positions, action coordinates, material targets,
or fresh-confirmation metadata.
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
from materials_gcts_iqc_stage_local_prefix_dataset import (
    load_default_dataset)
from materials_gcts_iqc_stage_local_prefix_marking_audit import (
    EXPECTED_AUDIT_DIGEST, PrefixMarkingSpec, _flatten, _row_id,
    _variant_indices, evaluate as development_audit)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_frozen_stage_local_prefix_marking_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "4b405f46f1bd89a8b422764f022266202af816b149a69be6a2b7fb5213a471c1"
EXPECTED_MODEL_DIGEST = \
    "28db73d00f9a38a134ef5b31322763fa7872376df2b23e44281d0a1207242a56"


@dataclass(frozen=True)
class FrozenPrefixTrainingRow:
    group: int
    row_id: str
    viable: bool
    features: tuple[float, ...]


@dataclass(frozen=True)
class FrozenPrefixDepthModel:
    depth: int
    spec: PrefixMarkingSpec
    feature_indices: tuple[int, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    training_rows: tuple[FrozenPrefixTrainingRow, ...]
    model_digest: str


@dataclass(frozen=True)
class FrozenStageLocalPrefixMarking:
    candidate_reach: tuple[int, ...]
    retained_prefix_budget: tuple[int, ...]
    depth_models: tuple[FrozenPrefixDepthModel, ...]
    source_dataset_digest: str
    source_audit_digest: str
    model_digest: str
    training_target_labels_used: bool = True
    fresh_confirmation_target_used: bool = False
    candidate_geometry_authorized: bool = False


def _mean_scale(vectors):
    width = len(vectors[0])
    means = tuple(sum(row[index] for row in vectors) / len(vectors)
                  for index in range(width))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (row[index] - means[index]) ** 2 for row in vectors) /
        len(vectors))) for index in range(width))
    return means, scales


def _depth_model(rows, depth, spec):
    source = tuple(row for row in rows if row["depth"] == depth)
    width = {len(row["features"]) for row in source}
    if len(width) != 1:
        raise AssertionError("stage-local training feature width drift")
    indices = _variant_indices(next(iter(width)), spec.variant)
    vectors = tuple(tuple(float(row["features"][index]) for index in indices)
                    for row in source)
    means, scales = _mean_scale(vectors)
    training = tuple(FrozenPrefixTrainingRow(
        int(row["group"]), _row_id(row), bool(row["viable_prefix"]),
        tuple((value - mean) / scale for value, mean, scale in zip(
            vector, means, scales))) for row, vector in zip(source, vectors))
    body = {
        "depth": depth, "spec": asdict(spec),
        "feature_indices": indices, "means": means, "scales": scales,
        "training_rows": tuple(asdict(row) for row in training),
    }
    return FrozenPrefixDepthModel(
        depth, spec, indices, means, scales, training, _digest(body))


def fit_default_model():
    dataset = load_default_dataset()
    audit = development_audit()
    if audit["audit_digest"] != EXPECTED_AUDIT_DIGEST or \
            not audit["stage_local_gate_passed"]:
        raise AssertionError("stage-local development gate is not frozen")
    selected = audit["selected_result"]
    specs = tuple(PrefixMarkingSpec(**row)
                  for row in selected["chosen_specs"])
    rows = _flatten(dataset)
    models = tuple(_depth_model(rows, depth, spec)
                   for depth, spec in enumerate(specs, start=1))
    body = {
        "candidate_reach": tuple(dataset["schedule"]),
        "retained_prefix_budget": tuple(selected["budget"]),
        "depth_models": tuple({
            **asdict(model), "spec": asdict(model.spec),
            "training_rows": tuple(asdict(row)
                                   for row in model.training_rows),
        } for model in models),
        "source_dataset_digest": dataset["dataset_digest"],
        "source_audit_digest": audit["audit_digest"],
        "training_target_labels_used": True,
        "fresh_confirmation_target_used": False,
        "candidate_geometry_authorized": False,
    }
    return FrozenStageLocalPrefixMarking(
        body["candidate_reach"], body["retained_prefix_budget"], models,
        body["source_dataset_digest"], body["source_audit_digest"],
        _digest(body))


def score_depth_model(model, full_features):
    vector = tuple(float(full_features[index])
                   for index in model.feature_indices)
    standardized = tuple((value - mean) / scale
                         for value, mean, scale in zip(
                             vector, model.means, model.scales))
    nearest = {}
    for row in model.training_rows:
        distance = sum((left - right) ** 2 for left, right in zip(
            standardized, row.features))
        record = (distance, row.row_id, float(row.viable))
        if row.group not in nearest or record[:2] < nearest[row.group][:2]:
            nearest[row.group] = record
    records = sorted(nearest.values())[:model.spec.neighbors]
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if model.spec.weighted else 1.
                    for distance, _row_id_value, _label in records)
    return sum(weight * record[2]
               for weight, record in zip(weights, records)) / sum(weights)


def _model_payload(model):
    return {
        "schema_version": 1,
        "candidate_reach": model.candidate_reach,
        "retained_prefix_budget": model.retained_prefix_budget,
        "depth_models": tuple({
            "depth": row.depth, "spec": asdict(row.spec),
            "feature_indices": row.feature_indices,
            "means": row.means, "scales": row.scales,
            "training_rows": tuple(asdict(item)
                                   for item in row.training_rows),
            "model_digest": row.model_digest,
        } for row in model.depth_models),
        "source_dataset_digest": model.source_dataset_digest,
        "source_audit_digest": model.source_audit_digest,
        "model_digest": model.model_digest,
        "training_target_labels_used": model.training_target_labels_used,
        "fresh_confirmation_target_used": model.fresh_confirmation_target_used,
        "candidate_geometry_authorized": model.candidate_geometry_authorized,
    }


def _from_payload(payload):
    models = tuple(FrozenPrefixDepthModel(
        int(row["depth"]), PrefixMarkingSpec(**row["spec"]),
        tuple(map(int, row["feature_indices"])),
        tuple(map(float, row["means"])), tuple(map(float, row["scales"])),
        tuple(FrozenPrefixTrainingRow(
            int(item["group"]), str(item["row_id"]), bool(item["viable"]),
            tuple(map(float, item["features"])))
              for item in row["training_rows"]), str(row["model_digest"]))
        for row in payload["depth_models"])
    model = FrozenStageLocalPrefixMarking(
        tuple(map(int, payload["candidate_reach"])),
        tuple(map(int, payload["retained_prefix_budget"])), models,
        str(payload["source_dataset_digest"]),
        str(payload["source_audit_digest"]), str(payload["model_digest"]),
        bool(payload["training_target_labels_used"]),
        bool(payload["fresh_confirmation_target_used"]),
        bool(payload["candidate_geometry_authorized"]))
    body = dict(payload)
    body.pop("schema_version", None)
    body.pop("model_digest")
    if _digest(body) != model.model_digest:
        raise AssertionError("frozen stage-local model digest drift")
    return model


def load_default_model(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("frozen stage-local model byte drift")
    model = _from_payload(json.loads(gzip.decompress(raw)))
    if EXPECTED_MODEL_DIGEST and model.model_digest != EXPECTED_MODEL_DIGEST:
        raise AssertionError("unexpected frozen stage-local model")
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("frozen stage-local fixture already exists")
    model = fit_default_model()
    payload = _model_payload(model)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
