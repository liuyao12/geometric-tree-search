#!/usr/bin/env python3
"""Posthoc per-site labels for the frozen expanded IQC obligation corpus.

The source fixture already contains every candidate action and trajectory.
This companion never changes that geometry: it reconstructs only the consumed
development targets, verifies the preregistered lift bound at bound+1, and
records one Boolean label for each of the three immutable action sites.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from materials_gcts_iqc_obligation_expanded_dataset import (
    _digest, _site_key, load_default_dataset as load_source_dataset)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    ORACLE_LIFT_BOUND, TARGET_RADIUS)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_obligation_expanded_site_labels_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "6daebc19c530347c5704dadcdfa327b48248294744fdedd8b1e5eb97fbbed2e7"
EXPECTED_DATASET_DIGEST = \
    "dfa9ddfc2d770f09c292fc4652c73f5c11ad7f0e61c43b36f71eed7e246dfddf"


def build_dataset():
    source = load_source_dataset()
    centers = tuple(tuple(map(float, group["center"]))
                    for group in source["groups"])
    physical_radius = math.ceil(max(math.dist(
        (0., 0., 0.), center) for center in centers) + TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical_radius)
    check, _ = oracle_patch_fast(ORACLE_LIFT_BOUND + 1, physical_radius)
    groups = []
    for group, center in zip(source["groups"], centers):
        target = _crop(oracle, center, TARGET_RADIUS,
                       "expanded-obligation-site-label")
        target_check = _crop(check, center, TARGET_RADIUS,
                             "expanded-obligation-site-label-check")
        if (tuple(target.positions), tuple(target.species)) != (
                tuple(target_check.positions), tuple(target_check.species)):
            raise AssertionError("site-label crop changes at bound + 1")
        truth = {_site_key(point): str(color) for point, color in zip(
            target.positions, target.species)}
        rows = []
        for index, row in enumerate(group["rows"]):
            labels = tuple(truth.get(_site_key(point)) == str(color)
                           for point, color in row["action_key"])
            if sum(labels) != int(row["correct_sites"]) or \
                    all(labels) != bool(row["exact"]):
                raise AssertionError("site labels disagree with source row")
            rows.append({
                "candidate_index": index,
                "action_digest": _digest(row["action_key"]),
                "site_correct": labels,
            })
        groups.append({
            "group": int(group["group"]), "center": center,
            "target_atoms": len(target.positions), "rows": tuple(rows),
        })
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "groups": tuple(groups),
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "oracle_bound_plus_one_stable": True,
        "source_geometry_changed": False,
        "labels_joined_posthoc_after_source_geometry_freeze": True,
        "consumed_development_only": True,
        "fresh_confirmation_claimed": False,
    }
    return {**body, "dataset_digest": _digest(body)}


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    source = load_source_dataset()
    if (_digest(body) != digest or
            body["source_dataset_digest"] != source["dataset_digest"] or
            len(body["groups"]) != len(source["groups"]) or
            not body["oracle_bound_plus_one_stable"] or
            body["source_geometry_changed"] or
            not body["labels_joined_posthoc_after_source_geometry_freeze"] or
            body["fresh_confirmation_claimed"]):
        raise AssertionError("expanded site-label companion drift")
    for group, source_group in zip(body["groups"], source["groups"]):
        if len(group["rows"]) != len(source_group["rows"]):
            raise AssertionError("expanded site-label row count drift")
        for item, source_row in zip(group["rows"], source_group["rows"]):
            if (item["action_digest"] != _digest(source_row["action_key"]) or
                    sum(item["site_correct"]) !=
                    int(source_row["correct_sites"]) or
                    all(item["site_correct"]) != bool(source_row["exact"])):
                raise AssertionError("expanded per-site label mismatch")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("unexpected expanded site-label digest")
    return row


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("expanded site-label fixture byte drift")
    return validate_dataset(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("expanded site-label fixture already exists")
    row = build_dataset()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
