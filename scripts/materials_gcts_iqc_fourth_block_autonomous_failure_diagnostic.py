#!/usr/bin/env python3
"""Post-hoc diagnosis of the consumed group-4 autonomous shortlist failure."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _correct, _truth_index, canonical_json)
from materials_gcts_iqc_fourth_block_autonomous_confirmation import \
    load_default_result as load_confirmation
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_iqc_fourth_block_terminal_features import \
    load_default_result as load_features
from materials_gcts_iqc_fourth_block_winner_preflight import \
    load_default_result as load_winner
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_autonomous_failure_group4_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "4c9740223b8017b554f68132f15511d3a548193f38583b92870fcf500a698ca9"
EXPECTED_RESULT_DIGEST = \
    "36f6fe288024c748851ad414bf4a4bc988a29da83f0c6a94e6ded45d6b4d4b73"
GROUP = 4
PARENT_BALANCED_WIDTH = 2


def evaluate():
    import numpy as np
    confirmation = load_confirmation()
    features = load_features()
    winner = load_winner()
    if (confirmation["autonomous_exact_fourth_block_continuation"]
            or confirmation["causal_autonomous_winner_gate_passed"]):
        raise AssertionError("failure diagnostic requires a consumed red gate")
    group = next(row for row in features["group_rows"]
                 if row["group"] == GROUP)
    beam = load_beams()["beams"][GROUP]
    target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
    truth = _truth_index(target.positions, target.species)
    means = np.asarray(winner["model"]["means"], dtype=float)
    scales = np.asarray(winner["model"]["scales"], dtype=float)
    weights = np.asarray(winner["model"]["weights"], dtype=float)
    rows = []
    for parent in group["parents"]:
        for candidate in parent["rows"]:
            actions = tuple((tuple(map(float, point)), str(color))
                            for point, color in candidate["actions"])
            score = float(((np.asarray(candidate["features"]) - means) /
                           scales) @ weights)
            correct = sum(_correct(point, color, truth)
                          for point, color in actions)
            rows.append({
                "parent_index": int(parent["parent_index"]),
                "stable_index": int(candidate["stable_index"]),
                "score": score, "correct_actions": correct,
                "exact": correct == 12,
            })
    order = tuple(sorted(range(len(rows)), key=lambda index: (
        -rows[index]["score"], rows[index]["parent_index"],
        rows[index]["stable_index"])))
    exact_ranks = tuple(rank for rank, index in enumerate(order, 1)
                        if rows[index]["exact"])
    exact_parents = tuple(sorted({row["parent_index"] for row in rows
                                  if row["exact"]}))
    parent_audit = []
    balanced = []
    for parent in sorted({row["parent_index"] for row in rows}):
        indices = tuple(index for index, row in enumerate(rows)
                        if row["parent_index"] == parent)
        indices = tuple(sorted(indices, key=lambda index: (
            -rows[index]["score"], rows[index]["stable_index"])))
        balanced.extend(indices[:PARENT_BALANCED_WIDTH])
        exact = tuple(rank for rank, index in enumerate(indices, 1)
                      if rows[index]["exact"])
        if exact:
            parent_audit.append({
                "parent_index": parent, "candidates": len(indices),
                "exact_candidates": len(exact),
                "first_exact_within_parent_rank": exact[0],
                "top_one_exact": rows[indices[0]]["exact"],
            })
    histogram = tuple(sorted(Counter(
        row["correct_actions"] for row in rows).items()))
    body = {
        "schema_version": 1,
        "group": GROUP,
        "source_confirmation_result_digest": confirmation["result_digest"],
        "source_feature_result_digest": features["result_digest"],
        "source_winner_model_digest": winner["model_digest"],
        "full_candidates": len(rows),
        "correct_action_histogram": histogram,
        "exact_candidates": len(exact_ranks),
        "exact_parent_count": len(exact_parents),
        "exact_parent_indices": exact_parents,
        "first_exact_global_rank": exact_ranks[0] if exact_ranks else None,
        "exact_ranks_first_twenty": exact_ranks[:20],
        "failed_global_shortlist_size": confirmation["candidates"],
        "failed_global_shortlist_exact": confirmation["exact_candidates"],
        "exact_parent_audit": tuple(parent_audit),
        "parent_balanced_width": PARENT_BALANCED_WIDTH,
        "parent_balanced_candidates": len(balanced),
        "parent_balanced_exact_candidates": sum(
            rows[index]["exact"] for index in balanced),
        "parent_balanced_exact_parent_count": len({
            rows[index]["parent_index"] for index in balanced
            if rows[index]["exact"]}),
        "failure_kind": "global pruning destroyed parent diversity",
        "target_consumed_only_for_posthoc_diagnosis": True,
        "confirmation_retried": False,
        "fresh_parent_balanced_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1 or body["group"] != GROUP
            or not body["target_consumed_only_for_posthoc_diagnosis"]
            or body["confirmation_retried"]
            or body["fresh_parent_balanced_confirmation_claimed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("autonomous failure diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("autonomous failure result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("autonomous failure fixture byte drift")
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
        "group", "full_candidates", "exact_candidates",
        "exact_parent_count", "first_exact_global_rank",
        "failed_global_shortlist_exact", "parent_balanced_width",
        "parent_balanced_candidates", "parent_balanced_exact_candidates",
        "parent_balanced_exact_parent_count", "failure_kind",
        "fresh_parent_balanced_confirmation_claimed", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
