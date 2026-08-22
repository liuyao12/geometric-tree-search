#!/usr/bin/env python3
"""Select a compute-bounded IQC prefix schedule by grouped validation."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json

from materials_gcts_iqc_joint_child_action_marking_fit import (
    CASES, _fit_numpy, _load_rows, _scores)
from materials_gcts_joint_child_action_marking import load_default_marking
from materials_gcts_joint_prefix_schedule import (
    BASE_CHANNEL_INDEX, DEFAULT_FIXTURE, FORMAT, canonical_json)


JOINT_WIDTH_GRID = (1, 2, 4, 8, 16, 32, 64)
BASE_WIDTH_GRID = (1, 2, 3, 4, 5, 6, 8, 10, 16)
PARENT_WIDTH = 8
EXPECTED_ARTIFACT_DIGEST = (
    "4e5c57d6a2ad15a374f9f973869f693e84a63c4e38cba829907054b74d895fe7")


def fit_artifact():
    rows, labels, groups, branches, case_audit = _load_rows()
    model, marking_artifact = load_default_marking()
    heldout_scores = [0.] * len(rows)
    for heldout in range(len(CASES)):
        train = [index for index, group in enumerate(groups)
                 if group != heldout]
        test = [index for index, group in enumerate(groups)
                if group == heldout]
        fitted = _fit_numpy(
            [rows[index] for index in train],
            [labels[index] for index in train], model.ridge_lambda,
            model.positive_weight)
        scores = _scores([rows[index] for index in test], fitted)
        for index, score in zip(test, scores):
            heldout_scores[index] = float(score)
    selection_rows = []
    for joint_width in JOINT_WIDTH_GRID:
        for base_width in BASE_WIDTH_GRID:
            supplied = total = selected_prefixes = 0
            per_case = [0] * len(CASES)
            per_case_total = [0] * len(CASES)
            for branch in branches:
                exact = {index for index, label
                         in enumerate(branch["labels"]) if label}
                count = len(branch["indices"])
                joint = sorted(range(count), key=lambda index: (
                    -heldout_scores[branch["indices"][index]], index))[
                        :joint_width]
                base = sorted(range(count), key=lambda index: (
                    -rows[branch["indices"][index]][-4 +
                        BASE_CHANNEL_INDEX], index))[:base_width]
                selected = set(joint) | set(base)
                selected_prefixes += len(selected)
                if exact:
                    total += 1
                    per_case_total[branch["group"]] += 1
                    hit = bool(exact & selected)
                    supplied += hit
                    per_case[branch["group"]] += hit
            selection_rows.append({
                "joint_top_k": joint_width,
                "base_top_k": base_width,
                "selected_prefixes_across_four_cases": selected_prefixes,
                "mean_selected_prefixes_per_execution":
                    selected_prefixes / len(CASES),
                "supplied_exact_child_groups": supplied,
                "total_exact_child_groups": total,
                "supplied_by_case": tuple(per_case),
                "total_by_case": tuple(per_case_total),
            })
    eligible = [row for row in selection_rows
                if row["supplied_exact_child_groups"] ==
                row["total_exact_child_groups"]]
    if not eligible:
        raise AssertionError("no grouped-valid prefix schedule")
    selected = min(eligible, key=lambda row: (
        row["selected_prefixes_across_four_cases"],
        row["joint_top_k"] + row["base_top_k"],
        row["joint_top_k"], row["base_top_k"]))
    schedule = {
        "parent_width": PARENT_WIDTH,
        "joint_top_k": selected["joint_top_k"],
        "base_top_k": selected["base_top_k"],
        "base_channel_index": BASE_CHANNEL_INDEX,
        "maximum_prefixes": PARENT_WIDTH * (
            selected["joint_top_k"] + selected["base_top_k"]),
        "target_used_for_selection": True,
        "target_used_for_execution": False,
    }
    artifact = {
        "format": FORMAT,
        "training_cases": case_audit,
        "joint_marking_model_digest": model.model_digest,
        "joint_marking_artifact_digest": marking_artifact[
            "artifact_digest"],
        "joint_width_grid": JOINT_WIDTH_GRID,
        "base_width_grid": BASE_WIDTH_GRID,
        "selection_rows": selection_rows,
        "selected": selected,
        "schedule": schedule,
        "grouped_leave_one_nucleus_out": True,
        "consumed_target_development_audit_only": True,
        "future_target_used_for_execution": False,
    }
    artifact["artifact_digest"] = hashlib.sha256(canonical_json({
        key: value for key, value in artifact.items()
        if key != "artifact_digest"})).hexdigest()
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    artifact = fit_artifact()
    if (EXPECTED_ARTIFACT_DIGEST and
            artifact["artifact_digest"] != EXPECTED_ARTIFACT_DIGEST):
        raise AssertionError("joint prefix schedule fitted artifact drift")
    text = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(json.dumps({
        "artifact_digest": artifact["artifact_digest"],
        "selected": artifact["selected"],
        "schedule": artifact["schedule"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
