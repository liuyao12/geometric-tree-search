#!/usr/bin/env python3
"""Serialize five held-target-sealed parent-balanced fourth-block beams."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import canonical_json
from materials_gcts_iqc_fourth_block_beam import freeze_fourth_block_beam
from materials_gcts_iqc_three_block_portfolio_execution import _prepare_pool


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_fourth_block_beams_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "4a84e9c6e6912428bdfc128537d6cb5c853e020e80ddbbb99c75bf26aae8a69d")
EXPECTED_RESULT_DIGEST = (
    "31501dd57252a547bbfa1976c407702079ff934b06de4538a5aa7bd3afb92cf5")


def _worker(group):
    return freeze_fourth_block_beam(group)


def evaluate(workers=4):
    if workers < 1:
        raise ValueError("workers must be positive")
    groups = tuple(range(5))
    if workers == 1:
        rows = tuple(map(_worker, groups))
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            rows = tuple(pool.map(_worker, groups))
    rows = tuple(sorted(rows, key=lambda row: row.heldout_group))
    if (tuple(row.heldout_group for row in rows) != groups
            or any(row.heldout_target_opened or row.target_used_for_ranking
                   for row in rows)
            or any(row.parents != 8 or row.parent_width != 8
                   or row.retained_candidates != 64 for row in rows)):
        raise AssertionError("fourth-block beam sealing drift")
    body = {
        "schema_version": 1,
        "beams": tuple(asdict(row) for row in rows),
        "groups": len(rows),
        "complete_candidates": sum(row.complete_candidates for row in rows),
        "retained_candidates": sum(row.retained_candidates for row in rows),
        "parents_per_group": 8,
        "retained_per_parent": 8,
        "heldout_targets_opened": False,
        "target_used_for_ranking": False,
        "extension_executed": False,
        "correctness_labels_present": False,
        "candidate_geometry_changed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1 or body["groups"] != 5
            or body["retained_candidates"] != 320
            or body["heldout_targets_opened"]
            or body["target_used_for_ranking"]
            or body["extension_executed"]
            or body["correctness_labels_present"]
            or body["candidate_geometry_changed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("fourth-block beam fixture drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("fourth-block beam result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("fourth-block beam fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate(args.workers))
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({key: row[key] for key in (
        "groups", "complete_candidates", "retained_candidates",
        "parents_per_group", "retained_per_parent",
        "heldout_targets_opened", "target_used_for_ranking",
        "result_digest")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
