#!/usr/bin/env python3
"""Freeze the tie-robust stage-local IQC marking selected on development."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_frozen_stage_local_prefix_marking import (
    FrozenStageLocalPrefixMarking, PrefixMarkingSpec, _depth_model,
    _from_payload, _model_payload)
from materials_gcts_iqc_stage_local_margin_marking_audit import (
    EXPECTED_AUDIT_DIGEST, evaluate as development_audit)
from materials_gcts_iqc_stage_local_prefix_dataset import load_default_dataset
from materials_gcts_iqc_stage_local_prefix_marking_audit import _flatten


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_frozen_stage_local_margin_marking_v2.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "babf27b5a98776e440a0a497c9b21ccca69f385c974fc68b56fe7882eb7cb129"
EXPECTED_MODEL_DIGEST = \
    "eeef24a2721e6418d150f97c23401df5471129c63bff9f60053f9a05dcc59665"


def fit_default_model():
    dataset = load_default_dataset()
    audit = development_audit()
    if audit["audit_digest"] != EXPECTED_AUDIT_DIGEST or \
            not audit["tie_robust_stage_local_gate_passed"]:
        raise AssertionError("tie-robust stage-local gate is not frozen")
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


def load_default_model(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("tie-robust stage-local model byte drift")
    model = _from_payload(json.loads(gzip.decompress(raw)))
    if EXPECTED_MODEL_DIGEST and model.model_digest != EXPECTED_MODEL_DIGEST:
        raise AssertionError("unexpected tie-robust stage-local model")
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("tie-robust stage-local fixture already exists")
    model = fit_default_model()
    text = json.dumps(_model_payload(model), indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
