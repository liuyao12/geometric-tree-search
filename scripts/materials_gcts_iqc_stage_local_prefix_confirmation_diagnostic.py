#!/usr/bin/env python3
"""Posthoc diagnosis of the consumed red stage-local IQC confirmation.

The complete repaired prefix tree and its feature rows freeze before the
already-consumed target is reconstructed.  The audit locates the first depth
where the frozen marking loses every viable prefix and measures feature-space
extrapolation.  It cannot authorize a retry or a new confirmation.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path

from materials_gcts_iqc_frozen_stage_local_prefix_marking import (
    load_default_model, score_depth_model)
from materials_gcts_iqc_obligation_expanded_dataset import _digest, _site_key
from materials_gcts_iqc_stage_local_prefix_confirmation_preregistration import (
    CONFIRMATION_CENTER, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_stage_local_prefix_dataset import _geometry_group
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
CONFIRMATION_RECEIPT = ROOT / \
    "fixtures/iqc_stage_local_prefix_confirmation_v1.json.gz"
EXPECTED_DIAGNOSTIC_DIGEST = \
    "3b93439f3e9e55ca9e0df6d0eaee99c369b4b70b77b8b39265084f6781187bc8"


def _standardized(model, features):
    return tuple((float(features[index]) - mean) / scale
                 for index, mean, scale in zip(
                     model.feature_indices, model.means, model.scales))


def _distance_diagnostic(model, features):
    vector = _standardized(model, features)
    nearest = {}
    for row in model.training_rows:
        distance = sum((left - right) ** 2 for left, right in zip(
            vector, row.features))
        record = (distance, row.row_id, bool(row.viable))
        if row.group not in nearest or record[:2] < nearest[row.group][:2]:
            nearest[row.group] = record
    rows = tuple(sorted(nearest.values()))
    minimums = tuple(min(item.features[index]
                         for item in model.training_rows)
                     for index in range(len(vector)))
    maximums = tuple(max(item.features[index]
                         for item in model.training_rows)
                     for index in range(len(vector)))
    outside = sum(value < lower or value > upper
                  for value, lower, upper in zip(vector, minimums, maximums))
    return {
        "nearest_group_distance": math.sqrt(rows[0][0]),
        "three_neighbor_distances": tuple(math.sqrt(row[0])
                                           for row in rows[:3]),
        "nearest_labels": tuple(row[2] for row in rows[:3]),
        "outside_training_range_features": outside,
        "feature_count": len(vector),
        "outside_training_range_fraction": outside / len(vector),
    }


def evaluate():
    receipt = json.loads(gzip.decompress(CONFIRMATION_RECEIPT.read_bytes()))
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    frozen = _geometry_group((
        0, CONFIRMATION_CENTER, seed.positions, seed.species))
    geometry_digest = frozen["geometry_digest_before_target"]

    target, _ = oracle_crop_fast(CONFIRMATION_CENTER, TARGET_RADIUS)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    model = load_default_model()
    selected_parent_keys, stages = {0: set()}, []
    for depth, (stage, depth_model, budget) in enumerate(zip(
            frozen["stages"], model.depth_models,
            model.retained_prefix_budget), start=1):
        rows = []
        for source in stage["rows"]:
            labels = tuple(truth.get(_site_key(point)) == str(color)
                           for point, color in source["action_key"])
            rows.append({
                **source, "site_correct": labels,
                "correct_sites": sum(labels), "viable": all(labels),
                "score": score_depth_model(depth_model, source["features"]),
                "distance": _distance_diagnostic(
                    depth_model, source["features"]),
            })
        eligible = tuple(rows if depth == 1 else (
            row for row in rows if any(tuple(parent) in selected_parent_keys[0]
                                       for parent in row["parent_keys"])))
        ranked = tuple(sorted(eligible, key=lambda row: (
            -row["score"], repr(row["action_key"]))))
        selected = ranked[:budget]
        selected_parent_keys = {0: {
            tuple(row["action_key"]) for row in selected}}
        viable_ranks = tuple(index + 1 for index, row in enumerate(ranked)
                             if row["viable"])
        stages.append({
            "depth": depth, "all_candidates": len(rows),
            "all_viable": sum(row["viable"] for row in rows),
            "eligible_candidates": len(eligible),
            "eligible_viable": len(viable_ranks),
            "first_viable_rank": min(viable_ranks, default=None),
            "retained_budget": budget,
            "selected": tuple({
                "action_key": row["action_key"], "score": row["score"],
                "site_correct": row["site_correct"],
                "correct_sites": row["correct_sites"],
                "distance": row["distance"],
            } for row in selected),
            "selected_viable": sum(row["viable"] for row in selected),
            "best_viable": ({
                "rank": viable_ranks[0],
                "score": next(row["score"] for row in ranked
                              if row["viable"]),
                "distance": next(row["distance"] for row in ranked
                                 if row["viable"]),
            } if viable_ranks else None),
        })
    selected_terminal = tuple(stages[-1]["selected"][0]["action_key"])
    receipt_terminal = tuple(tuple((tuple(point), str(color))
                                   for point, color in receipt[
                                       "marked_trace"]["waves"][0][
                                           "selected_actions"]))
    body = {
        "schema_version": 1,
        "consumed_confirmation_result_digest": receipt["result_digest"],
        "center": CONFIRMATION_CENTER,
        "seed_atoms": len(seed.positions), "target_atoms": len(target.positions),
        "candidate_counts_by_depth": frozen["candidate_counts_by_depth"],
        "complete_geometry_digest_before_target": geometry_digest,
        "stages": tuple(stages),
        "selected_terminal_reproduces_confirmation":
            selected_terminal == receipt_terminal,
        "complete_exact_terminal_count": stages[-1]["all_viable"],
        "first_depth_without_retained_viable_prefix": next((
            stage["depth"] for stage in stages
            if stage["eligible_viable"] and not stage["selected_viable"]),
            None),
        "target_opened_only_after_complete_geometry": True,
        "consumed_posthoc_diagnostic": True,
        "retry_authorized": False,
        "policy_integrated": False,
        "fresh_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "diagnostic_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    if EXPECTED_DIAGNOSTIC_DIGEST and row["diagnostic_digest"] != \
            EXPECTED_DIAGNOSTIC_DIGEST:
        raise AssertionError("stage-local confirmation diagnostic drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          "consumed stage-local IQC confirmation diagnosed")


if __name__ == "__main__":
    main()
