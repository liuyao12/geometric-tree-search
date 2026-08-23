#!/usr/bin/env python3
"""Post-hoc supply confirmation for the sealed marked IQC fourth block."""

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
from materials_gcts_iqc_fourth_block_marked_extension import \
    load_group as load_extension
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_marked_confirmation_group2_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "c4848739a71d9f2dfc3962d383e8f613a0a59006640c41e0e92f4b471be547f6"
EXPECTED_RESULT_DIGEST = \
    "758a501623b218586d86ecf99fc5f9ba17d7dfd46b3441a2c6912bbc89dbe463"
GROUP = 2


def evaluate():
    beams = load_beams()
    beam = beams["beams"][GROUP]
    extension = load_extension(GROUP)
    if (beam["heldout_target_opened"] or beam["target_used_for_ranking"]
            or extension["confirmation_target_opened"]
            or extension["target_used_for_extension"]
            or extension["winner_selected"]):
        raise AssertionError("marked confirmation source was not sealed")
    target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
    truth = _truth_index(target.positions, target.species)

    def correct_count(actions):
        return sum(_correct(tuple(point), str(color), truth)
                   for point, color in actions)

    exact_parent_ids = tuple(row["stable_index"]
                             for row in beam["candidates"]
                             if correct_count(row["actions"]) == 9)
    continued = {tuple(row["lineage_id"])[1]
                 for row in extension["results"]
                 if row["status"] == "continued"}
    counts = []
    exact_parents = set()
    for parent in extension["results"]:
        if parent["status"] != "continued":
            continue
        parent_id = tuple(parent["lineage_id"])[1]
        for child in parent["successors"]:
            correct = correct_count(child["all_actions"])
            counts.append(correct)
            if correct == 12:
                exact_parents.add(parent_id)
    body = {
        "schema_version": 1,
        "group": GROUP,
        "source_beam_result_digest": beams["result_digest"],
        "source_extension_result_digest": extension["result_digest"],
        "source_action_budget": extension["action_budget"],
        "marking_model_digest": extension["marking_model_digest"],
        "beam_exact_parents": len(exact_parent_ids),
        "exact_parents_continued": sum(
            parent in continued for parent in exact_parent_ids),
        "successors": len(counts),
        "correct_action_histogram": tuple(sorted(Counter(counts).items())),
        "best_correct_actions": max(counts, default=0),
        "exact_twelve_action_successors": sum(
            count == 12 for count in counts),
        "exact_successor_parent_count": len(exact_parents),
        "exact_successor_fraction": sum(
            count == 12 for count in counts) / len(counts),
        "all_exact_parents_survived_replay": all(
            parent in continued for parent in exact_parent_ids),
        "marked_reach8_supplies_exact_fourth_block": any(
            count == 12 for count in counts),
        "target_opened_after_candidate_fixture": True,
        "target_used_for_extension": False,
        "target_used_for_ranking": False,
        "same_nucleus_unmarked_ablation_frozen_before_target": False,
        "causal_marking_superiority_claimed": False,
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
            or body["same_nucleus_unmarked_ablation_frozen_before_target"]
            or body["causal_marking_superiority_claimed"]
            or body["autonomous_winner_selected"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("marked fourth-block confirmation drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("marked confirmation result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("marked confirmation fixture byte drift")
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
        "group", "source_action_budget", "beam_exact_parents",
        "exact_parents_continued", "successors",
        "exact_twelve_action_successors", "exact_successor_parent_count",
        "exact_successor_fraction",
        "marked_reach8_supplies_exact_fourth_block",
        "same_nucleus_unmarked_ablation_frozen_before_target",
        "causal_marking_superiority_claimed", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
