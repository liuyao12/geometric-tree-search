#!/usr/bin/env python3
"""One-shot fresh confirmation for the five-channel IQC marking library."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from materials_gcts_iqc_marking_library_confirmation_preregistration import (
    COMPLETE_PARENT_WIDTH, CONFIRMATION_CENTER, EXECUTION_WORKERS,
    EXPECTED_ACTIONS_PER_BLOCK, EXPECTED_LINEAGE_ACTIONS,
    EXPECTED_MANIFEST_DIGEST, FIRST_BLOCK_RADIUS,
    LOCAL_SECTION_ARTIFACT_DIGEST, LOCAL_SECTION_FIXTURE_SHA256,
    LOCAL_SECTION_MODEL_DIGEST, MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    OneShotOrderGuard, POSITION_TOLERANCE, PRIOR_CENTERS,
    SECOND_BLOCK_RADIUS, SEED_RADIUS, SOURCE_COMMIT, THIRD_BLOCK_RADIUS,
    canonical_json)
from materials_gcts_iqc_three_block_marking_library_execution import (
    freeze_three_block_marking_library_execution)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_marking_library_confirmation_v1.json.gz"
ATTEMPT_MARKER = ROOT / \
    "fixtures/iqc_marking_library_confirmation_attempt_v1.json"
EXPECTED_FIXTURE_SHA256 = (
    "b061c69a32b4f9016389d5f428b88c7c58bf3d1dd0cd1a9a8ac12910aaf32656")
EXPECTED_RESULT_DIGEST = (
    "7120c4b369f52d4ba3cdc741a37729495ac8333bf1055af3a73d4e036519eb3d")


def _action_key(action):
    point, color = action
    return tuple(map(float, point)), str(color)


def _distance_squared(first, second):
    return sum((a - b) ** 2 for a, b in zip(first, second))


def _unique_prefixes(lineages, fields):
    rows = {}
    for lineage in lineages:
        actions = tuple(action for field in fields
                        for action in getattr(lineage, field))
        rows.setdefault(tuple(_action_key(action) for action in actions),
                        actions)
    return tuple(rows[key] for key in sorted(rows))


def _serialize_receipt(execution):
    receipt = asdict(execution)
    payload = canonical_json(receipt)
    return receipt, payload, hashlib.sha256(payload).hexdigest()


def _execute_and_score_once():
    guard = OneShotOrderGuard()
    guard.protocol_verified()
    guard.seed_opened()
    seed, seed_ids = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    execution = freeze_three_block_marking_library_execution(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_BLOCK_RADIUS,
        second_radius=SECOND_BLOCK_RADIUS, third_radius=THIRD_BLOCK_RADIUS,
        workers=EXECUTION_WORKERS)
    receipt, receipt_bytes, receipt_digest = _serialize_receipt(execution)
    if (execution.target_used or
            set(execution.selected_parent_ids) !=
            set(range(1, COMPLETE_PARENT_WIDTH + 1)) or
            execution.local_section_fixture_sha256 !=
            LOCAL_SECTION_FIXTURE_SHA256 or
            execution.local_section_model_digest !=
            LOCAL_SECTION_MODEL_DIGEST or
            execution.local_section_artifact_digest !=
            LOCAL_SECTION_ARTIFACT_DIGEST or
            any(len(lineage.first_actions) != EXPECTED_ACTIONS_PER_BLOCK or
                len(lineage.second_actions) != EXPECTED_ACTIONS_PER_BLOCK or
                len(lineage.third_actions) != EXPECTED_ACTIONS_PER_BLOCK or
                len(lineage.all_actions) != EXPECTED_LINEAGE_ACTIONS
                for lineage in execution.lineages)):
        raise AssertionError("marking-library receipt invariant drift")
    guard.receipt_frozen(receipt_digest)
    frozen_receipt = bytes(receipt_bytes)

    guard.target_opened()
    target, target_ids = oracle_crop_fast(
        CONFIRMATION_CENTER, THIRD_BLOCK_RADIUS)
    by_species = {color: tuple(point for point, species in zip(
        target.positions, target.species) if species == color)
                  for color in set(target.species)}
    unique_actions = {_action_key(action) for lineage in execution.lineages
                      for action in lineage.all_actions}
    nearest = {action: math.sqrt(min(_distance_squared(
        action[0], candidate) for candidate in by_species[action[1]]))
        for action in unique_actions}

    def score(actions):
        return sum(nearest[_action_key(action)] <= POSITION_TOLERANCE
                   for action in actions)

    first_prefixes = _unique_prefixes(execution.lineages, ("first_actions",))
    second_prefixes = _unique_prefixes(
        execution.lineages, ("first_actions", "second_actions"))
    exact_first = tuple(actions for actions in first_prefixes
                        if score(actions) == len(actions))
    exact_second = tuple(actions for actions in second_prefixes
                         if score(actions) == len(actions))
    lineage_scores = tuple(score(lineage.all_actions)
                           for lineage in execution.lineages)
    exact_indices = tuple(index for index, value in enumerate(lineage_scores)
                          if value == EXPECTED_LINEAGE_ACTIONS)
    exact_lineages = tuple(execution.lineages[index]
                           for index in exact_indices)
    legacy = dict(execution.legacy_child_ids_by_parent)
    local = dict(execution.local_child_ids_by_parent)
    exact_parent_children = tuple(sorted({
        (lineage.parent_id, lineage.child_stable_index)
        for lineage in exact_lineages}))
    exact_local_only = tuple(pair for pair in exact_parent_children
                             if pair[1] in local[pair[0]] and
                             pair[1] not in legacy[pair[0]])
    post_receipt, post_bytes, post_digest = _serialize_receipt(execution)
    receipt_unchanged = (post_receipt == receipt and
                         post_bytes == frozen_receipt and
                         post_digest == receipt_digest)
    guard.scored(post_digest)
    nearest_prior = min(math.dist(CONFIRMATION_CENTER, prior)
                        for prior in PRIOR_CENTERS)
    seed_subset = set(seed_ids).issubset(target_ids)
    success = bool(
        exact_lineages and receipt_unchanged and seed_subset and
        not execution.target_used and guard.target_open_count == 1 and
        nearest_prior > MINIMUM_REQUIRED_DOMAIN_SEPARATION and
        set(execution.selected_parent_ids) ==
        set(range(1, COMPLETE_PARENT_WIDTH + 1)))
    body = {
        "schema_version": 1,
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "protocol_source_commit": SOURCE_COMMIT,
        "center": CONFIRMATION_CENTER,
        "radii": (SEED_RADIUS, FIRST_BLOCK_RADIUS, SECOND_BLOCK_RADIUS,
                  THIRD_BLOCK_RADIUS),
        "position_tolerance": POSITION_TOLERANCE,
        "workers": EXECUTION_WORKERS,
        "seed_atoms": len(seed.positions),
        "target_atoms": len(target.positions),
        "novel_target_atoms": len(set(target_ids) - set(seed_ids)),
        "seed_is_target_subset": seed_subset,
        "nearest_prior_center_separation": nearest_prior,
        "required_domain_separation": MINIMUM_REQUIRED_DOMAIN_SEPARATION,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "receipt_serialized_before_target": True,
        "receipt_unchanged_after_target": receipt_unchanged,
        "candidate_lineages": len(execution.lineages),
        "unique_candidate_actions": len(unique_actions),
        "unique_first_prefixes": len(first_prefixes),
        "exact_first_prefixes": len(exact_first),
        "unique_second_prefixes": len(second_prefixes),
        "exact_second_prefixes": len(exact_second),
        "best_correct_actions": max(lineage_scores, default=0),
        "exact_lineages": len(exact_lineages),
        "exact_lineage_indices": exact_indices,
        "exact_parent_ids": tuple(sorted({lineage.parent_id
                                          for lineage in exact_lineages})),
        "exact_parent_child_ids": exact_parent_children,
        "exact_parent_child_ids_supplied_only_by_local_section":
            exact_local_only,
        "exact_candidate_fraction": len(exact_lineages) /
            max(1, len(execution.lineages)),
        "maximum_exact_lineage_position_residual": max((
            nearest[_action_key(action)] for lineage in exact_lineages
            for action in lineage.all_actions), default=None),
        "target_order_audit": guard.audit(),
        "target_used_for_candidate_or_ranking": False,
        "fresh_marking_library_three_block_supply_confirmed": success,
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
    receipt = body["receipt"]
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            body["protocol_digest"] != EXPECTED_MANIFEST_DIGEST or
            receipt["target_used"] or
            len(receipt["selected_parent_ids"]) != 8 or
            receipt["local_section_model_digest"] !=
            LOCAL_SECTION_MODEL_DIGEST or
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
        raise AssertionError("marking-library fresh result drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("marking-library result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("marking-library fixture byte drift")
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
        "fresh_marking_library_three_block_supply_confirmed", "seed_atoms",
        "target_atoms", "candidate_lineages", "exact_first_prefixes",
        "exact_second_prefixes", "best_correct_actions", "exact_lineages",
        "exact_parent_child_ids",
        "exact_parent_child_ids_supplied_only_by_local_section",
        "receipt_digest", "result_digest")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.write:
        if DEFAULT_FIXTURE.exists() or ATTEMPT_MARKER.exists():
            raise RuntimeError("marking-library one-shot already consumed")
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
