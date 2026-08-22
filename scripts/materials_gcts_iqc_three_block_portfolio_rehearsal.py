#!/usr/bin/env python3
"""Consumed-nucleus rehearsal of the target-free three-block portfolio.

This durable development audit reuses the already consumed rollback nucleus.
It exists to verify execution parity, runtime, and end-to-end candidate supply
before any new spatial confirmation is preregistered.  The target is opened
only after the target-free receipt is immutable.  Nothing here is fresh
confirmation evidence.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from materials_gcts_iqc_child_option_third_block_audit import (
    THIRD_BLOCK_RADIUS)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    OUTER_ORACLE_LIFT_BOUND)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_iqc_three_block_channel_execution import _point_key
from materials_gcts_iqc_three_block_portfolio_execution import (
    freeze_three_block_portfolio_execution)
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_three_block_portfolio_rehearsal_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "557a3be2daab28c069f8886d0c7339563e82b196548eabb7084a68f981e7e67b"
EXPECTED_RESULT_DIGEST = \
    "557be761cd7393bc33a9235d85deaed2e7adbff26968e688aaa4fd67f95354eb"


def _crop_at(radius, label):
    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + radius)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    return _crop(oracle, CONFIRMATION_CENTER, radius, label)


def evaluate(*, workers=4):
    seed = _crop_at(SEED_RADIUS, "IQC-three-block-rehearsal-seed")
    execution = freeze_three_block_portfolio_execution(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=TARGET_RADIUS,
        second_radius=SECOND_BLOCK_RADIUS, third_radius=THIRD_BLOCK_RADIUS,
        workers=workers)
    receipt = asdict(execution)
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()
    frozen = repr((receipt, receipt_digest))

    # The consumed target is materialized only after the receipt freezes.
    target = _crop_at(
        THIRD_BLOCK_RADIUS, "IQC-three-block-rehearsal-consumed-target")
    truth = {_point_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    exact = tuple(lineage for lineage in execution.lineages if all(
        truth.get(_point_key(point)) == color
        for point, color in lineage.all_actions))
    first_exact_parents = tuple(sorted({lineage.parent_id for lineage in exact}))
    second_exact_paths = tuple(sorted({
        (lineage.parent_id, lineage.child_stable_index)
        for lineage in exact}))
    if frozen != repr((receipt, receipt_digest)):
        raise AssertionError("three-block receipt mutated after target open")
    body = {
        "schema_version": 1,
        "center": CONFIRMATION_CENTER,
        "seed_radius": SEED_RADIUS,
        "first_radius": TARGET_RADIUS,
        "second_radius": SECOND_BLOCK_RADIUS,
        "third_radius": THIRD_BLOCK_RADIUS,
        "seed_atoms": len(seed.positions),
        "target_atoms": len(target.positions),
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "lineage_candidates": len(execution.lineages),
        "exact_lineages": len(exact),
        "exact_parent_ids": first_exact_parents,
        "exact_parent_child_ids": second_exact_paths,
        "end_to_end_candidate_supply": bool(exact),
        "target_open_count": 1,
        "target_used_for_candidate_or_ranking": False,
        "consumed_target_rehearsal_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_winner_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            body["receipt"]["target_used"] or
            body["target_open_count"] != 1 or
            body["target_used_for_candidate_or_ranking"] or
            not body["consumed_target_rehearsal_only"] or
            body["fresh_confirmation_claimed"] or
            body["autonomous_winner_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("three-block portfolio rehearsal drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("three-block rehearsal result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("three-block rehearsal fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    if args.json:
        print(text, end="")
    else:
        print(json.dumps({
            "lineage_candidates": row["lineage_candidates"],
            "exact_lineages": row["exact_lineages"],
            "exact_parent_child_ids": row["exact_parent_child_ids"],
            "end_to_end_candidate_supply":
                row["end_to_end_candidate_supply"],
            "receipt_digest": row["receipt_digest"],
            "result_digest": row["result_digest"],
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
