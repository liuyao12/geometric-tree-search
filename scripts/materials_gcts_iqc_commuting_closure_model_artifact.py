#!/usr/bin/env python3
"""Inert scalar artifact for the grouped commuting-closure marking."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_commuting_closure_marking import (
    FrozenScalarCommutingClosureMarking,
    freeze_scalar_commuting_closure_marking,
    scalar_commuting_closure_marking_digest)
from materials_gcts_iqc_commuting_closure_marking_benchmark import \
    fit_default_model
from materials_gcts_iqc_frozen_fusion_artifact import (
    branch_value_from_payload, branch_value_payload, canonical_json,
    payload_digest)
from materials_gcts_portfolio_terminal_value import (
    FrozenPortfolioTerminalValue, TerminalRepresentation)


FORMAT = "materials-gcts-iqc-commuting-closure-scalar-v1"
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_closure_scalar_model_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "5230633077f8725df6614a08e7d50fae2e30199228c3a3f35031ca8bbb551b83"
EXPECTED_ARTIFACT_DIGEST = \
    "7854e6fa8b459d85680589f93f40f93f8f02fd79b9a24fde3fadd431c2e72141"


def marking_payload(model, *, source_hashes, examples, positive_examples,
                    development_gate_passed):
    payload = {
        "format": FORMAT,
        "model": {
            "scalar": {
                "representation": {
                    "name": model.scalar.representation.name,
                    "feature_indices": list(
                        model.scalar.representation.feature_indices),
                },
                "value": branch_value_payload(model.scalar.value),
            },
            "feature_names": list(model.feature_names),
            "color_keys": list(model.color_keys),
            "training_groups": model.training_groups,
            "model_digest": model.model_digest,
            "target_used": model.target_used,
        },
        "development_source_fixture_sha256": list(source_hashes),
        "development_examples": int(examples),
        "development_positive_examples": int(positive_examples),
        "development_gate_passed": bool(development_gate_passed),
        "target_used": False,
    }
    payload["artifact_digest"] = payload_digest(payload)
    return payload


def marking_from_payload(payload):
    if (payload.get("format") != FORMAT or
            payload.get("target_used") is not False or
            payload.get("artifact_digest") != payload_digest(payload) or
            not payload.get("development_gate_passed") or
            int(payload.get("development_examples", 0)) != 224 or
            int(payload.get("development_positive_examples", 0)) != 16):
        raise ValueError("invalid commuting-closure marking artifact")
    row = payload["model"]
    scalar = row["scalar"]
    representation = scalar["representation"]
    model = FrozenScalarCommutingClosureMarking(
        FrozenPortfolioTerminalValue(
            TerminalRepresentation(
                str(representation["name"]),
                tuple(map(int, representation["feature_indices"]))),
            branch_value_from_payload(scalar["value"])),
        tuple(map(str, row["feature_names"])),
        tuple(map(str, row["color_keys"])),
        int(row["training_groups"]), str(row["model_digest"]),
        bool(row.get("target_used", False)))
    if (model.target_used or model.scalar.target_used or
            scalar_commuting_closure_marking_digest(
                model.scalar, model.feature_names, model.color_keys,
                model.training_groups) != model.model_digest):
        raise ValueError("mutated commuting-closure scalar model")
    return model


def build_payload():
    fusion, audit, _frozen, examples, source_hashes = fit_default_model()
    model = freeze_scalar_commuting_closure_marking(fusion)
    return marking_payload(
        model, source_hashes=source_hashes, examples=len(examples),
        positive_examples=sum(row.successful for row in examples),
        development_gate_passed=(audit.selected_exact_groups == 4))


def load_default_marking(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 != "PENDING" and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("commuting-closure artifact byte drift")
    payload = json.loads(raw)
    if (EXPECTED_ARTIFACT_DIGEST != "PENDING" and
            payload.get("artifact_digest") != EXPECTED_ARTIFACT_DIGEST):
        raise AssertionError("commuting-closure artifact digest drift")
    return marking_from_payload(payload), payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        if DEFAULT_FIXTURE.exists():
            raise RuntimeError("commuting-closure model artifact already exists")
        payload = build_payload()
        DEFAULT_FIXTURE.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        payload = build_payload() if args.live else load_default_marking()[1]
    print(json.dumps(payload, indent=2, sort_keys=True))
