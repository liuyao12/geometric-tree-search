#!/usr/bin/env python3
"""Consumed-target diagnosis of the fresh IQC parent-beam failure.

The original one-shot receipt remains immutable and red.  This diagnostic
replays the already-frozen child portfolio under a complete eight-parent
antichain, then expands only the posthoc-identified omitted exact prefix.  It
is development evidence for the successor executor, never fresh confirmation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from materials_gcts_clusters2_future_option import (
    ChildOption, ParentOption, select_future_options)
from materials_gcts_iqc_three_block_complete_parent_execution import (
    COMPLETE_OPTION_SPEC)
from materials_gcts_iqc_three_block_portfolio_confirmation import (
    DEFAULT_FIXTURE as ONE_SHOT_FIXTURE,
    load_default_result as load_one_shot_result)
from materials_gcts_iqc_three_block_portfolio_confirmation_preregistration import (
    CONFIRMATION_CENTER, FIRST_BLOCK_RADIUS, SECOND_BLOCK_RADIUS, SEED_RADIUS,
    THIRD_BLOCK_RADIUS)
from materials_gcts_iqc_three_block_portfolio_execution import (
    _third_parent_worker)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_complete_parent_consumed_diagnostic_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "38343bb94b15e0f2f21527c3dda3fabbb1fb89c6961222a3357f4f202b016e70"
EXPECTED_RESULT_DIGEST = \
    "f6117d72502c6db123eca9ccdaa4d88047de09fda26d6e38ec03f58b1bca4923"
POSITION_TOLERANCE = 1e-5
DIAGNOSTIC_PARENT_ID = 2
DIAGNOSTIC_CHILD_ID = 120


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _action_key(action):
    point, color = action
    return tuple(map(float, point)), str(color)


def _distance_squared(first, second):
    return sum((a - b) ** 2 for a, b in zip(first, second))


def evaluate():
    one_shot = load_one_shot_result(ONE_SHOT_FIXTURE)
    receipt = one_shot["receipt"]
    parents = tuple(ParentOption(
        branch["first_rank"], tuple(ChildOption(
            (branch["first_rank"], stable_index), tuple(scores))
            for stable_index, scores in enumerate(
                branch["second_channel_scores"])))
        for branch in receipt["second_branches"])
    selection = select_future_options(parents, COMPLETE_OPTION_SPEC)
    branch = next(row for row in receipt["second_branches"]
                  if row["first_rank"] == DIAGNOSTIC_PARENT_ID)
    selected_children = dict(selection.selected_child_ids_by_parent)[
        DIAGNOSTIC_PARENT_ID]
    child_retained_target_free = (
        DIAGNOSTIC_PARENT_ID, DIAGNOSTIC_CHILD_ID) in selected_children

    # The target is already consumed by the immutable one-shot result.  It is
    # reopened here only for explicitly posthoc diagnostic labels.
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    target, _ = oracle_crop_fast(CONFIRMATION_CENTER, THIRD_BLOCK_RADIUS)
    by_species = {color: tuple(point for point, species in zip(
        target.positions, target.species) if species == color)
                  for color in set(target.species)}

    def correct(action):
        point, color = _action_key(action)
        return min(_distance_squared(point, candidate)
                   for candidate in by_species[color]) <= \
            POSITION_TOLERANCE ** 2

    exact_first_actions = sum(correct(action)
                              for action in branch["first_actions"])
    exact_second_children = tuple(index for index, actions in enumerate(
        branch["second_actions"])
        if exact_first_actions == 3 and
        sum(correct(action) for action in actions) == 3)
    payload = (
        CONFIRMATION_CENTER, seed.positions, seed.species,
        tuple(tuple((tuple(point), color) for point, color
                    in branch["first_actions"])),
        ((DIAGNOSTIC_CHILD_ID, tuple(tuple((tuple(point), color)
             for point, color in branch["second_actions"][
                 DIAGNOSTIC_CHILD_ID]))),),
        DIAGNOSTIC_PARENT_ID, FIRST_BLOCK_RADIUS, SECOND_BLOCK_RADIUS,
        THIRD_BLOCK_RADIUS)
    third_rows = _third_parent_worker(payload)
    third_counts, lineages = third_rows[0]
    unique_actions = {_action_key(action) for lineage in lineages
                      for action in lineage.all_actions}
    nearest = {action: math.sqrt(min(_distance_squared(
        action[0], candidate) for candidate in by_species[action[1]]))
        for action in unique_actions}
    lineage_scores = tuple(sum(nearest[_action_key(action)] <=
                               POSITION_TOLERANCE
                               for action in lineage.all_actions)
                           for lineage in lineages)
    exact_indices = tuple(index for index, score in enumerate(lineage_scores)
                          if score == 9)
    body = {
        "schema_version": 1,
        "one_shot_result_digest": one_shot["result_digest"],
        "one_shot_receipt_digest": one_shot["receipt_digest"],
        "one_shot_remains_red": not one_shot[
            "fresh_bounded_three_block_candidate_supply_confirmed"],
        "position_tolerance": POSITION_TOLERANCE,
        "complete_selected_parent_ids": selection.selected_parent_ids,
        "complete_parent_antichain": set(selection.selected_parent_ids) ==
            {branch["first_rank"] for branch in receipt["second_branches"]},
        "diagnostic_parent_id": DIAGNOSTIC_PARENT_ID,
        "diagnostic_parent_originally_selected": DIAGNOSTIC_PARENT_ID in
            receipt["selected_parent_ids"],
        "diagnostic_parent_exact_first_actions": exact_first_actions,
        "diagnostic_exact_second_children": exact_second_children,
        "diagnostic_child_id": DIAGNOSTIC_CHILD_ID,
        "diagnostic_child_retained_target_free":
            child_retained_target_free,
        "third_candidate_counts": third_counts,
        "third_lineages": len(lineages),
        "best_correct_actions": max(lineage_scores, default=0),
        "exact_nine_action_lineages": len(exact_indices),
        "exact_third_stable_indices": tuple(
            lineages[index].third_stable_index for index in exact_indices),
        "failure_localized_to_four_parent_truncation": bool(
            not one_shot["fresh_bounded_three_block_candidate_supply_confirmed"]
            and not DIAGNOSTIC_PARENT_ID in receipt["selected_parent_ids"]
            and exact_first_actions == 3
            and DIAGNOSTIC_CHILD_ID in exact_second_children
            and child_retained_target_free and exact_indices),
        "candidate_selection_target_used": False,
        "diagnostic_branch_chosen_posthoc": True,
        "consumed_target_diagnostic_only": True,
        "fresh_confirmation_claimed": False,
        "winner_or_autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            not body["one_shot_remains_red"] or
            body["candidate_selection_target_used"] or
            not body["diagnostic_branch_chosen_posthoc"] or
            not body["consumed_target_diagnostic_only"] or
            body["fresh_confirmation_claimed"] or
            body["winner_or_autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("complete-parent consumed diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("complete-parent diagnostic digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("complete-parent diagnostic fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
