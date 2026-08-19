#!/usr/bin/env python3
"""Build the preregistered IQC confirmation candidate receipt, seed only."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import zlib
from dataclasses import asdict
from pathlib import Path

from materials_gcts_iqc_complete_frontier_confirmation_execution import (
    freeze_confirmation_candidates)
from materials_gcts_iqc_complete_frontier_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, ORACLE_LIFT_BOUND,
    SEED_RADIUS, SOURCE_COMMIT, SOURCE_SHA256, audit)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_complete_frontier_confirmation_candidates_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "7727841852ca4688f6ed99557c0e5bb452e4f25117747cd99d3f01520423a5a1"
EXPECTED_RECEIPT_DIGEST = \
    "b4e7d872d36519cd9415265c8fba65be4de82a166eb852fc086d33ac4ad4f1ae"


def _verify_source_hashes():
    for relative, expected in SOURCE_SHA256:
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f"confirmation source drift: {relative}")


def _seed(bound):
    physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                         + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(bound, physical)
    return _crop(oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-complete-frontier-confirmation-seed")


def _crop_code(row):
    return tuple((tuple(map(float, point)), str(color))
                 for point, color in zip(row.positions, row.species))


def _digest(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_candidate_receipt():
    protocol = audit()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("confirmation protocol digest drift")
    _verify_source_hashes()
    seed = _seed(ORACLE_LIFT_BOUND)
    seed_check = _seed(ORACLE_LIFT_BOUND + 1)
    stable = _crop_code(seed) == _crop_code(seed_check)
    if not stable:
        raise AssertionError("confirmation seed changes at lift bound + 1")
    execution = freeze_confirmation_candidates(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species)
    terminal_bytes = json.dumps(
        execution.terminal_actions, separators=(",", ":")).encode()
    compressed_terminals = base64.b64encode(
        zlib.compress(terminal_bytes, level=9)).decode()
    payload = {
        "schema_version": 1,
        "source_commit": SOURCE_COMMIT,
        "protocol_digest": protocol.manifest_digest,
        "center": CONFIRMATION_CENTER,
        "seed_radius": SEED_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "seed_atoms": len(seed.positions),
        "seed_bound_plus_one_stable": stable,
        "action_reach_schedule": execution.action_reach_schedule,
        "unpruned_from_depth": execution.unpruned_from_depth,
        "candidate_counts_by_depth": execution.candidate_counts_by_depth,
        "terminal_count": execution.terminal_count,
        "terminal_actions_zlib_base64": compressed_terminals,
        "terminal_actions_sha256": hashlib.sha256(terminal_bytes).hexdigest(),
        "scalar_order": execution.scalar_order,
        "fusion_order": execution.fusion_order,
        "per_channel_portfolio_budget":
            execution.per_channel_portfolio_budget,
        "portfolio_indices": execution.portfolio_indices,
        "candidate_digest": execution.candidate_digest,
        "portfolio_digest": execution.portfolio_digest,
        "execution_digest": execution.execution_digest,
        "target_open_count": 0,
        "target_used": execution.target_used,
    }
    return {**payload, "receipt_digest": _digest(payload)}


def validate_candidate_receipt(payload):
    body = dict(payload)
    digest = body.pop("receipt_digest")
    try:
        terminal_bytes = zlib.decompress(base64.b64decode(
            body["terminal_actions_zlib_base64"], validate=True))
        terminal_actions = json.loads(terminal_bytes)
    except Exception as error:
        raise AssertionError("invalid compressed confirmation terminals") from error
    if (_digest(body) != digest or body["schema_version"] != 1
            or body["protocol_digest"] != EXPECTED_MANIFEST_DIGEST
            or tuple(body["center"]) != CONFIRMATION_CENTER
            or tuple(body["action_reach_schedule"]) != (8, 8, 8)
            or body["unpruned_from_depth"] != 0
            or body["per_channel_portfolio_budget"] != 9
            or body["terminal_count"] != len(terminal_actions)
            or hashlib.sha256(terminal_bytes).hexdigest() !=
               body["terminal_actions_sha256"]
            or len(body["scalar_order"]) != body["terminal_count"]
            or len(body["fusion_order"]) != body["terminal_count"]
            or len(body["portfolio_indices"]) > 18
            or body["target_open_count"] != 0 or body["target_used"]
            or not body["seed_bound_plus_one_stable"]):
        raise AssertionError("confirmation candidate receipt drift")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    receipt = build_candidate_receipt()
    print(json.dumps(receipt, indent=2, sort_keys=True)
          if args.json else receipt)


if __name__ == "__main__":
    main()
