#!/usr/bin/env python3
"""One-shot fresh IQC confirmation of target-blind three-block supply.

Run ``--write`` exactly once.  The CLI creates a durable attempt marker before
opening the seed, freezes and serializes the complete portfolio receipt, opens
the third-radius target once, and then performs pure scoring.  A marker or
result fixture makes every later ``--write`` invocation fail closed.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from materials_gcts_iqc_three_block_portfolio_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXECUTION_WORKERS, EXPECTED_ACTIONS_PER_BLOCK,
    EXPECTED_LINEAGE_ACTIONS, EXPECTED_MANIFEST_DIGEST, FIRST_BLOCK_RADIUS,
    MANIFEST, MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard,
    PRIOR_CENTERS, SECOND_BLOCK_RADIUS, SEED_RADIUS, THIRD_BLOCK_RADIUS,
    canonical_json, validate_preregistration)
from materials_gcts_iqc_three_block_portfolio_execution import (
    freeze_three_block_portfolio_execution)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_three_block_portfolio_confirmation_v1.json.gz"
ATTEMPT_MARKER = ROOT / \
    "fixtures/iqc_three_block_portfolio_confirmation_attempt_v1.json"
EXPECTED_FIXTURE_SHA256 = ""
EXPECTED_RESULT_DIGEST = ""


def _point_key(point):
    return tuple(round(float(value), 8) for value in point)


def _action_key(actions):
    return tuple((_point_key(point), str(color))
                 for point, color in actions)


def _unique_prefixes(lineages, fields):
    rows = {}
    for lineage in lineages:
        actions = tuple(action for field in fields
                        for action in getattr(lineage, field))
        rows.setdefault(_action_key(actions), actions)
    return tuple(rows[key] for key in sorted(rows))


def _score_actions(actions, truth):
    return sum(truth.get(_point_key(point)) == str(color)
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
    execution = freeze_three_block_portfolio_execution(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_BLOCK_RADIUS,
        second_radius=SECOND_BLOCK_RADIUS, third_radius=THIRD_BLOCK_RADIUS,
        workers=EXECUTION_WORKERS)
    receipt, receipt_bytes, receipt_digest = _serialize_receipt(execution)
    if (execution.target_used or any(
            len(lineage.first_actions) != EXPECTED_ACTIONS_PER_BLOCK or
            len(lineage.second_actions) != EXPECTED_ACTIONS_PER_BLOCK or
            len(lineage.third_actions) != EXPECTED_ACTIONS_PER_BLOCK or
            len(lineage.all_actions) != EXPECTED_LINEAGE_ACTIONS
            for lineage in execution.lineages)):
        raise AssertionError("target-free receipt/action arity drift")
    guard.receipt_frozen(receipt_digest)
    frozen_receipt = bytes(receipt_bytes)

    # This is the only fresh target construction in the one-shot harness.
    guard.target_opened()
    target, target_lifts = oracle_crop_fast(
        CONFIRMATION_CENTER, THIRD_BLOCK_RADIUS)
    truth = {_point_key(point): str(color) for point, color in zip(
        target.positions, target.species)}

    first_prefixes = _unique_prefixes(execution.lineages, ("first_actions",))
    second_prefixes = _unique_prefixes(
        execution.lineages, ("first_actions", "second_actions"))
    exact_first = tuple(actions for actions in first_prefixes
                        if _score_actions(actions, truth) == len(actions))
    exact_second = tuple(actions for actions in second_prefixes
                         if _score_actions(actions, truth) == len(actions))
    lineage_correct_counts = tuple(
        _score_actions(lineage.all_actions, truth)
        for lineage in execution.lineages)
    exact_indices = tuple(index for index, count in enumerate(
        lineage_correct_counts) if count == EXPECTED_LINEAGE_ACTIONS)
    exact_lineages = tuple(execution.lineages[index]
                           for index in exact_indices)
    exact_parent_ids = tuple(sorted({lineage.parent_id
                                     for lineage in exact_lineages}))
    exact_parent_child_ids = tuple(sorted({
        (lineage.parent_id, lineage.child_stable_index)
        for lineage in exact_lineages}))
    post_score_receipt, post_score_bytes, post_score_digest = \
        _serialize_receipt(execution)
    receipt_unchanged = (post_score_receipt == receipt and
                         post_score_bytes == frozen_receipt and
                         post_score_digest == receipt_digest)
    guard.scored(post_score_digest)
    nearest_prior = min(math.dist(CONFIRMATION_CENTER, prior)
                        for prior in PRIOR_CENTERS)
    seed_is_target_subset = set(seed_lifts).issubset(target_lifts)
    success = bool(
        exact_lineages and receipt_unchanged and seed_is_target_subset and
        not execution.target_used and guard.target_open_count == 1 and
        nearest_prior > MINIMUM_REQUIRED_DOMAIN_SEPARATION)
    body = {
        "schema_version": 1,
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "protocol_source_commit": MANIFEST["source_commit"],
        "center": CONFIRMATION_CENTER,
        "radii": (SEED_RADIUS, FIRST_BLOCK_RADIUS, SECOND_BLOCK_RADIUS,
                  THIRD_BLOCK_RADIUS),
        "workers": EXECUTION_WORKERS,
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
        "candidate_lineages": len(execution.lineages),
        "unique_first_prefixes": len(first_prefixes),
        "exact_first_prefixes": len(exact_first),
        "unique_second_prefixes": len(second_prefixes),
        "exact_second_prefixes": len(exact_second),
        "best_correct_actions": max(lineage_correct_counts, default=0),
        "exact_lineages": len(exact_lineages),
        "exact_lineage_indices": exact_indices,
        "exact_parent_ids": exact_parent_ids,
        "exact_parent_child_ids": exact_parent_child_ids,
        "exact_candidate_fraction": (len(exact_lineages) /
                                     max(1, len(execution.lineages))),
        "target_order_audit": guard.audit(),
        "target_used_for_candidate_or_ranking": False,
        "fresh_bounded_three_block_candidate_supply_confirmed": success,
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
        raise AssertionError("fresh three-block confirmation drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("fresh three-block result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("fresh three-block fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def _attempt_marker_bytes():
    return canonical_json({
        "schema_version": 1,
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "one_shot_invocation": 1,
        "confirmation_center": CONFIRMATION_CENTER,
    }) + b"\n"


def _summary(row):
    return {
        "fresh_bounded_three_block_candidate_supply_confirmed":
            row["fresh_bounded_three_block_candidate_supply_confirmed"],
        "seed_atoms": row["seed_atoms"],
        "target_atoms": row["target_atoms"],
        "candidate_lineages": row["candidate_lineages"],
        "exact_lineages": row["exact_lineages"],
        "exact_parent_child_ids": row["exact_parent_child_ids"],
        "best_correct_actions": row["best_correct_actions"],
        "receipt_digest": row["receipt_digest"],
        "result_digest": row["result_digest"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.write:
        if DEFAULT_FIXTURE.exists() or ATTEMPT_MARKER.exists():
            raise RuntimeError("fresh confirmation one-shot already consumed")
        ATTEMPT_MARKER.parent.mkdir(parents=True, exist_ok=True)
        with ATTEMPT_MARKER.open("xb") as stream:
            stream.write(_attempt_marker_bytes())
        row = validate_result(_execute_and_score_once())
        text = json.dumps(row, indent=2, sort_keys=True) + "\n"
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps(row if args.json else _summary(row),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
