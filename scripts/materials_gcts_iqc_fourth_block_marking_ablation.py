#!/usr/bin/env python3
"""Same-nucleus pre-target ablation of the fourth-block GCTS marking."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _correct, _truth_index, canonical_json)
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_iqc_fourth_block_extension import \
    load_group as load_unmarked
from materials_gcts_iqc_fourth_block_marked_extension import \
    load_group as load_marked
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_marking_ablation_group3_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "e51bfde4d4a2055b0a666d568e48be61a33554394943da96ad9f2eecb7735403"
EXPECTED_RESULT_DIGEST = \
    "392e37a78fde8a87e6f1e3d44cf1e9197004593be12eee7c7d9a85fd97d67811"
GROUP = 3
MAXIMUM_MARKED_WORK_RATIO = 1.05


def _score_arm(row, truth):
    def correct_count(actions):
        return sum(_correct(tuple(point), str(color), truth)
                   for point, color in actions)

    counts = []
    exact_parents = set()
    for parent in row["results"]:
        if parent["status"] != "continued":
            continue
        parent_id = tuple(parent["lineage_id"])[1]
        for child in parent["successors"]:
            correct = correct_count(child["all_actions"])
            counts.append(correct)
            if correct == 12:
                exact_parents.add(parent_id)
    return {
        "successors": len(counts),
        "correct_action_histogram": tuple(sorted(Counter(counts).items())),
        "best_correct_actions": max(counts, default=0),
        "exact_twelve_action_successors": sum(
            count == 12 for count in counts),
        "exact_successor_parent_count": len(exact_parents),
        "unique_geometry_expansions": row["unique_geometry_expansions"],
        "naive_geometry_expansions": row["naive_geometry_expansions"],
        "saved_geometry_expansions": row["saved_geometry_expansions"],
    }


def evaluate():
    beams = load_beams()
    beam = beams["beams"][GROUP]
    unmarked = load_unmarked(GROUP)
    marked = load_marked(GROUP)
    if (beam["heldout_target_opened"] or beam["target_used_for_ranking"]
            or unmarked["heldout_target_opened"]
            or unmarked["target_used_for_extension"]
            or marked["confirmation_target_opened"]
            or marked["target_used_for_extension"]
            or unmarked["lineages_extended"] != 64
            or marked["lineages_extended"] != 64
            or marked["action_budget"] != 8):
        raise AssertionError("fourth-block ablation inputs were not sealed")
    target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
    truth = _truth_index(target.positions, target.species)
    exact_parents = sum(all(
        _correct(point, color, truth) for point, color in row["actions"])
        for row in beam["candidates"])
    unmarked_score = _score_arm(unmarked, truth)
    marked_score = _score_arm(marked, truth)
    work_ratio = (marked_score["unique_geometry_expansions"] /
                  unmarked_score["unique_geometry_expansions"])
    supply_gain = (marked_score["exact_twelve_action_successors"] /
                   max(1, unmarked_score["exact_twelve_action_successors"]))
    gate = (
        marked_score["exact_twelve_action_successors"] >
        unmarked_score["exact_twelve_action_successors"]
        and marked_score["exact_successor_parent_count"] >=
        unmarked_score["exact_successor_parent_count"]
        and work_ratio <= MAXIMUM_MARKED_WORK_RATIO)
    body = {
        "schema_version": 1,
        "group": GROUP,
        "source_beam_result_digest": beams["result_digest"],
        "unmarked_result_digest": unmarked["result_digest"],
        "marked_result_digest": marked["result_digest"],
        "marking_model_digest": marked["marking_model_digest"],
        "action_budget_each_arm": 8,
        "retained_parents_each_arm": 64,
        "beam_exact_parents": exact_parents,
        "unmarked": unmarked_score,
        "marked": marked_score,
        "marked_unique_work_ratio": work_ratio,
        "marked_exact_supply_gain": supply_gain,
        "maximum_marked_work_ratio_gate": MAXIMUM_MARKED_WORK_RATIO,
        "marked_exact_supply_improved":
            marked_score["exact_twelve_action_successors"] >
            unmarked_score["exact_twelve_action_successors"],
        "marked_parent_coverage_preserved":
            marked_score["exact_successor_parent_count"] >=
            unmarked_score["exact_successor_parent_count"],
        "marked_work_within_gate":
            work_ratio <= MAXIMUM_MARKED_WORK_RATIO,
        "causal_marked_supply_gate_passed": gate,
        "both_candidate_receipts_frozen_before_target": True,
        "target_opened_once_after_both_receipts": True,
        "target_used_for_either_extension": False,
        "candidate_geometry_generator_identical": True,
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
            or body["action_budget_each_arm"] != 8
            or body["retained_parents_each_arm"] != 64
            or not math.isclose(body["maximum_marked_work_ratio_gate"],
                                MAXIMUM_MARKED_WORK_RATIO)
            or not body["both_candidate_receipts_frozen_before_target"]
            or not body["target_opened_once_after_both_receipts"]
            or body["target_used_for_either_extension"]
            or not body["candidate_geometry_generator_identical"]
            or body["autonomous_winner_selected"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("fourth-block marking ablation drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("fourth-block ablation result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("fourth-block ablation fixture byte drift")
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
    print(json.dumps({
        "group": row["group"],
        "beam_exact_parents": row["beam_exact_parents"],
        "unmarked_exact_successors":
            row["unmarked"]["exact_twelve_action_successors"],
        "marked_exact_successors":
            row["marked"]["exact_twelve_action_successors"],
        "unmarked_exact_parent_count":
            row["unmarked"]["exact_successor_parent_count"],
        "marked_exact_parent_count":
            row["marked"]["exact_successor_parent_count"],
        "marked_exact_supply_gain": row["marked_exact_supply_gain"],
        "marked_unique_work_ratio": row["marked_unique_work_ratio"],
        "causal_marked_supply_gate_passed":
            row["causal_marked_supply_gate_passed"],
        "autonomous_winner_selected": row["autonomous_winner_selected"],
        "result_digest": row["result_digest"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
