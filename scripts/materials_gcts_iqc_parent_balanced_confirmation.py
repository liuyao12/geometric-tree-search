#!/usr/bin/env python3
"""One-shot fresh IQC confirmation of parent-balanced fourth-block supply.

Run ``--write`` exactly once.  The attempt marker is created before opening
the seed.  The complete target-blind execution receipt is serialized before
the fourth-radius target is constructed, then the frozen candidates are
scored without refit, reranking, retry, or further execution.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from materials_gcts_iqc_fresh_parent_balanced_execution import \
    freeze_fresh_parent_balanced_execution
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXECUTION_WORKERS, EXPECTED_MANIFEST_DIGEST,
    FIRST_RADIUS, FOURTH_RADIUS, MANIFEST,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard, PARENT_WIDTH,
    PRIOR_CENTERS, SECOND_RADIUS, SEED_RADIUS, THIRD_RADIUS, canonical_json,
    validate_preregistration)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_parent_balanced_confirmation_v1.json.gz"
ATTEMPT_MARKER = ROOT / \
    "fixtures/iqc_parent_balanced_confirmation_attempt_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "15493709b9aeacbb3aa658151026f6b8ff4cea6b3ef8412d737f49779675ff5c"
EXPECTED_RESULT_DIGEST = \
    "89f541a5229925b19e07b22d9c7d0b6a1b686427959f038632b07bcb0d95594c"


def _point_key(point):
    return tuple(round(float(value), 8) for value in point)


def _action_labels(actions, truth):
    return tuple(truth.get(_point_key(point)) == str(color)
                 for point, color in actions)


def _serialize_receipt(execution):
    receipt = asdict(execution)
    payload = canonical_json(receipt)
    return receipt, payload, hashlib.sha256(payload).hexdigest()


def _execute_and_score_once():
    guard = OneShotOrderGuard()
    guard.protocol_verified()
    guard.seed_opened()
    seed, seed_lifts = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    execution = freeze_fresh_parent_balanced_execution(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, third_radius=THIRD_RADIUS,
        fourth_radius=FOURTH_RADIUS, workers=EXECUTION_WORKERS)
    receipt, receipt_bytes, receipt_digest = _serialize_receipt(execution)
    if (execution.target_used or execution.parent_width != PARENT_WIDTH or
            execution.nine_action_parent_count != 8 or
            execution.nine_action_candidates_retained != 8 * PARENT_WIDTH or
            execution.fourth_parent_lineages_retained != 8 * PARENT_WIDTH or
            execution.fourth_candidates_retained !=
            8 * PARENT_WIDTH * PARENT_WIDTH or
            len(execution.candidates) !=
            execution.fourth_candidates_retained or any(
                len(candidate.all_actions) != 12 or
                len(candidate.actions) != 3
                for candidate in execution.candidates)):
        raise AssertionError("fresh parent-balanced receipt invariant drift")
    guard.receipt_frozen(receipt_digest)
    frozen_receipt = bytes(receipt_bytes)

    # The fresh target is first constructed here, after all 512 candidate
    # identities, scores, actions, and parent assignments are immutable.
    guard.target_opened()
    target, target_lifts = oracle_crop_fast(
        CONFIRMATION_CENTER, FOURTH_RADIUS)
    truth = {_point_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    labels = tuple(_action_labels(candidate.all_actions, truth)
                   for candidate in execution.candidates)
    terminal_labels = tuple(_action_labels(candidate.actions, truth)
                            for candidate in execution.candidates)
    correct_counts = tuple(sum(row) for row in labels)
    exact_indices = tuple(index for index, row in enumerate(labels)
                          if all(row))
    exact_terminal_indices = tuple(
        index for index, row in enumerate(terminal_labels) if all(row))
    exact_parents = tuple(sorted({
        execution.candidates[index].parent_lineage_index
        for index in exact_indices}))
    exact_terminal_parents = tuple(sorted({
        execution.candidates[index].parent_lineage_index
        for index in exact_terminal_indices}))
    post_receipt, post_bytes, post_digest = _serialize_receipt(execution)
    receipt_unchanged = (post_receipt == receipt and
                         post_bytes == frozen_receipt and
                         post_digest == receipt_digest)
    guard.scored(post_digest)
    nearest_prior = min(math.dist(CONFIRMATION_CENTER, prior)
                        for prior in PRIOR_CENTERS)
    seed_is_target_subset = set(seed_lifts).issubset(target_lifts)
    success = bool(
        exact_indices and receipt_unchanged and seed_is_target_subset and
        not execution.target_used and guard.target_open_count == 1 and
        nearest_prior > MINIMUM_REQUIRED_DOMAIN_SEPARATION)
    body = {
        "schema_version": 1,
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "center": CONFIRMATION_CENTER,
        "radii": (SEED_RADIUS, FIRST_RADIUS, SECOND_RADIUS, THIRD_RADIUS,
                  FOURTH_RADIUS),
        "workers": EXECUTION_WORKERS,
        "parent_width": PARENT_WIDTH,
        "seed_atoms": len(seed.positions),
        "target_atoms": len(target.positions),
        "novel_target_atoms": len(set(target_lifts) - set(seed_lifts)),
        "seed_is_target_subset": seed_is_target_subset,
        "nearest_prior_center_separation": nearest_prior,
        "required_domain_separation": MINIMUM_REQUIRED_DOMAIN_SEPARATION,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "receipt_serialized_before_target": True,
        "receipt_unchanged_after_target": receipt_unchanged,
        "candidate_digest_before_target": execution.candidate_digest,
        "complete_nine_action_lineages":
            execution.complete_nine_action_lineages,
        "nine_action_candidates_retained":
            execution.nine_action_candidates_retained,
        "nine_action_parent_count": execution.nine_action_parent_count,
        "fourth_candidates_before_balance":
            execution.fourth_candidates_before_balance,
        "fourth_candidates_retained":
            execution.fourth_candidates_retained,
        "fourth_parent_lineages_retained":
            execution.fourth_parent_lineages_retained,
        "exact_four_block_candidates": len(exact_indices),
        "exact_four_block_candidate_indices": exact_indices,
        "exact_four_block_parent_lineages": exact_parents,
        "exact_terminal_blocks": len(exact_terminal_indices),
        "exact_terminal_parent_lineages": exact_terminal_parents,
        "best_correct_actions": max(correct_counts, default=0),
        "exact_candidate_fraction": len(exact_indices) /
            max(1, len(execution.candidates)),
        "target_order_audit": guard.audit(),
        "target_used_for_candidate_or_ranking": False,
        "fresh_parent_balanced_fourth_block_supply_confirmed": success,
        "winner_selected_or_validated": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "rerun_or_fallback_allowed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    audit = body["target_order_audit"]
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            body["protocol_digest"] != EXPECTED_MANIFEST_DIGEST or
            body["receipt"]["target_used"] or
            body["parent_width"] != PARENT_WIDTH or
            body["nine_action_candidates_retained"] != 8 * PARENT_WIDTH or
            body["fourth_parent_lineages_retained"] != 8 * PARENT_WIDTH or
            body["fourth_candidates_retained"] !=
            8 * PARENT_WIDTH * PARENT_WIDTH or
            not body["receipt_serialized_before_target"] or
            not body["receipt_unchanged_after_target"] or
            body["target_used_for_candidate_or_ranking"] or
            audit["state"] != "scored" or
            audit["seed_open_count"] != 1 or
            audit["target_open_count"] != 1 or
            audit["score_count"] != 1 or
            audit["receipt_digest"] != body["receipt_digest"] or
            body["winner_selected_or_validated"] or
            body["autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"] or
            body["rerun_or_fallback_allowed"]):
        raise AssertionError("fresh parent-balanced confirmation drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("fresh parent-balanced result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("fresh parent-balanced fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def _attempt_marker_bytes():
    return canonical_json({
        "schema_version": 1,
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "one_shot_invocation": 1,
        "confirmation_center": CONFIRMATION_CENTER,
    }) + b"\n"


def _summary(row):
    return {key: row[key] for key in (
        "fresh_parent_balanced_fourth_block_supply_confirmed",
        "seed_atoms", "target_atoms", "complete_nine_action_lineages",
        "nine_action_candidates_retained", "fourth_candidates_retained",
        "exact_four_block_candidates", "exact_four_block_parent_lineages",
        "exact_terminal_blocks", "best_correct_actions", "receipt_digest",
        "result_digest")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.write:
        validate_preregistration()
        if DEFAULT_FIXTURE.exists() or ATTEMPT_MARKER.exists():
            raise RuntimeError("fresh parent-balanced one-shot already consumed")
        ATTEMPT_MARKER.parent.mkdir(parents=True, exist_ok=True)
        with ATTEMPT_MARKER.open("xb") as stream:
            stream.write(_attempt_marker_bytes())
        row = validate_result(_execute_and_score_once())
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps(row if args.json else _summary(row),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
