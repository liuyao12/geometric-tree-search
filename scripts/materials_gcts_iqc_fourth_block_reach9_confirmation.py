#!/usr/bin/env python3
"""Post-hoc confirmation of sealed IQC fourth-block reach-nine supply.

The target-blind candidate fixture is loaded and hash-validated before this
module opens the held nucleus-1 target.  The resulting labels are diagnostic
only: exact parent/successor identities are never returned to an executor or
used to alter the frozen reach-nine policy.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _correct, _truth_index, canonical_json)
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_iqc_fourth_block_reach9_extension import \
    load_group as load_extension
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_reach9_confirmation_group1_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "46f1701463c60ee5a5c8fc9af36a8c404809f48c3f4eb32e2ea98196aa943dd8"
EXPECTED_RESULT_DIGEST = \
    "69ec8bca50ee846c5708bcb212bc68edf1b36e82d9fa5c0f2de2e54f086a0310"
GROUP = 1


def evaluate():
    beams = load_beams()
    beam = beams["beams"][GROUP]
    extension = load_extension(GROUP)
    if (beam["heldout_target_opened"] or beam["target_used_for_ranking"]
            or extension["confirmation_target_opened"]
            or extension["target_used_for_extension"]
            or extension["winner_selected"]):
        raise AssertionError("confirmation source was not target sealed")

    # This is the first point at which the held target is accepted.
    target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
    truth = _truth_index(target.positions, target.species)

    def correct_count(actions):
        return sum(_correct(tuple(point), str(color), truth)
                   for point, color in actions)

    exact_parent_ids = tuple(row["stable_index"]
                             for row in beam["candidates"]
                             if correct_count(row["actions"]) == 9)
    continued_ids = {tuple(row["lineage_id"])[1]
                     for row in extension["results"]
                     if row["status"] == "continued"}
    counts = []
    exact_by_parent = Counter()
    for parent in extension["results"]:
        if parent["status"] != "continued":
            continue
        parent_id = tuple(parent["lineage_id"])[1]
        for child in parent["successors"]:
            correct = correct_count(child["all_actions"])
            counts.append(correct)
            if correct == 12:
                exact_by_parent[parent_id] += 1
    histogram = tuple(sorted(Counter(counts).items()))
    body = {
        "schema_version": 1,
        "group": GROUP,
        "source_beam_result_digest": beams["result_digest"],
        "source_extension_result_digest": extension["result_digest"],
        "source_action_budget": extension["action_budget"],
        "beam_candidates": len(beam["candidates"]),
        "beam_exact_parents": len(exact_parent_ids),
        "exact_parents_continued": sum(
            parent in continued_ids for parent in exact_parent_ids),
        "successors": len(counts),
        "correct_action_histogram": histogram,
        "best_correct_actions": max(counts, default=0),
        "exact_twelve_action_successors": sum(
            count == 12 for count in counts),
        "exact_successor_parent_count": len(exact_by_parent),
        "all_exact_parents_survived_replay": all(
            parent in continued_ids for parent in exact_parent_ids),
        "frozen_geometry_reaches_exact_fourth_block": any(
            count == 12 for count in counts),
        "target_opened_after_candidate_fixture": True,
        "target_used_for_extension": False,
        "target_used_for_ranking": False,
        "exact_identities_returned_to_policy": False,
        "autonomous_winner_selected": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1 or body["group"] != GROUP
            or not body["target_opened_after_candidate_fixture"]
            or body["target_used_for_extension"]
            or body["target_used_for_ranking"]
            or body["exact_identities_returned_to_policy"]
            or body["autonomous_winner_selected"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("reach-nine confirmation drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("reach-nine confirmation result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("reach-nine confirmation fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate())
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({key: row[key] for key in (
        "group", "beam_exact_parents", "exact_parents_continued",
        "successors", "best_correct_actions",
        "exact_twelve_action_successors", "exact_successor_parent_count",
        "all_exact_parents_survived_replay",
        "frozen_geometry_reaches_exact_fourth_block",
        "target_used_for_extension", "target_used_for_ranking",
        "result_digest")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
