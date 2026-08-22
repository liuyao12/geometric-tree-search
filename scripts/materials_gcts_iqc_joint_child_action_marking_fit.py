#!/usr/bin/env python3
"""Fit the joint child-action marking on four consumed IQC nuclei."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_child_action_marking import (
    DEFAULT_FIXTURE, FORMAT, FrozenJointChildActionMarking,
    canonical_json, compute_model_digest, joint_child_action_features,
    joint_feature_names, model_payload)
from materials_gcts_local_section_child_marking import (
    FrozenLocalSectionSchema)


CASES = (
    ("consumed-development",
     "fixtures/iqc_three_block_portfolio_rehearsal_v1.json.gz",
     (-70., 10., 70.)),
    ("fresh-four-parent-red",
     "fixtures/iqc_three_block_portfolio_confirmation_v1.json.gz",
     (-220., 80., 140.)),
    ("fresh-complete-parent-red",
     "fixtures/iqc_complete_parent_confirmation_v1.json.gz",
     (20., 220., -160.)),
    ("fresh-five-channel-red",
     "fixtures/iqc_marking_library_confirmation_v1.json.gz",
     (160., 20., 220.)),
)
SCHEMA = FrozenLocalSectionSchema(
    ("X", "Y", "Z"), 8., .25, 8,
    ("base", "colored", "ports", "coupled"), 6)
POSITION_TOLERANCE = 1e-5
RIDGE_GRID = (.1, 1., 10., 100., 1000.)
POSITIVE_WEIGHT_GRID = (1., 3., 10., 30., 100.)
TOP_K_GRID = (1, 2, 4, 8, 16)
EXPECTED_ARTIFACT_DIGEST = (
    "98b32b6944ddb0516d5e6e22aed72019b6b2cb7f2f5d8de70d83de1e9c08f2c2")


def _distance_squared(first, second):
    return sum((a - b) ** 2 for a, b in zip(first, second))


def _load_rows():
    root = Path(__file__).resolve().parent
    rows, labels, groups, branch_records = [], [], [], []
    case_audit = []
    for group, (name, relative, center) in enumerate(CASES):
        source_raw = (root / relative).read_bytes()
        receipt = json.loads(gzip.decompress(source_raw))["receipt"]
        seed, _ = oracle_crop_fast(center, 9.)
        target, _ = oracle_crop_fast(center, receipt["radii"][2])
        by_species = {color: tuple(point for point, species in zip(
            target.positions, target.species) if species == color)
                      for color in set(target.species)}
        case_positive = 0
        for branch in receipt["second_branches"]:
            features = joint_child_action_features(
                seed_positions=seed.positions, seed_species=seed.species,
                branch=branch, schema=SCHEMA)
            first_exact = all(min(_distance_squared(
                point, candidate) for candidate in by_species[color]) <=
                POSITION_TOLERANCE ** 2
                for point, color in branch["first_actions"])
            branch_labels = tuple(int(first_exact and all(
                min(_distance_squared(point, candidate)
                    for candidate in by_species[color]) <=
                POSITION_TOLERANCE ** 2
                for point, color in actions))
                for actions in branch["second_actions"])
            start = len(rows)
            rows.extend(features)
            labels.extend(branch_labels)
            groups.extend([group] * len(features))
            legacy = set()
            for channel in range(len(SCHEMA.source_channel_names)):
                order = sorted(range(len(features)), key=lambda index: (
                    -branch["second_channel_scores"][index][channel], index))
                legacy.update(order[:8])
            branch_records.append({
                "group": group,
                "indices": tuple(range(start, len(rows))),
                "labels": branch_labels,
                "legacy": tuple(sorted(legacy)),
            })
            case_positive += sum(branch_labels)
        case_audit.append({
            "name": name,
            "center": center,
            "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
            "positive_actions": case_positive,
        })
    return rows, labels, groups, branch_records, case_audit


def _fit_numpy(matrix, labels, ridge, positive_weight):
    import numpy as np
    matrix = np.asarray(matrix, dtype=float)
    labels = np.asarray(labels, dtype=float)
    means = matrix.mean(axis=0)
    scales = matrix.std(axis=0)
    scales[scales < 1e-9] = 1.
    design = np.column_stack((
        np.ones(len(matrix)), (matrix - means) / scales))
    sample_weights = np.where(labels > 0, positive_weight, 1.)
    regularizer = np.r_[0., np.full(matrix.shape[1], ridge)]
    system = design.T @ (design * sample_weights[:, None]) + \
        np.diag(regularizer) + 1e-8 * np.eye(design.shape[1])
    target = design.T @ (labels * sample_weights)
    coefficients = np.linalg.solve(system, target)
    return means, scales, coefficients[0], coefficients[1:]


def _scores(matrix, fitted):
    import numpy as np
    matrix = np.asarray(matrix, dtype=float)
    means, scales, intercept, weights = fitted
    return intercept + ((matrix - means) / scales) @ weights


def _logloss(labels, scores):
    total = 0.
    for label, score in zip(labels, scores):
        score = max(-30., min(30., float(score)))
        probability = 1. / (1. + math.exp(-score))
        total -= label * math.log(max(probability, 1e-12)) + \
            (1 - label) * math.log(max(1 - probability, 1e-12))
    return total / len(labels)


def fit_artifact():
    rows, labels, groups, branches, case_audit = _load_rows()
    selection_rows = []
    for positive_weight in POSITIVE_WEIGHT_GRID:
        for ridge in RIDGE_GRID:
            heldout_scores = [0.] * len(rows)
            for heldout in range(len(CASES)):
                train = [index for index, group in enumerate(groups)
                         if group != heldout]
                test = [index for index, group in enumerate(groups)
                        if group == heldout]
                fitted = _fit_numpy(
                    [rows[index] for index in train],
                    [labels[index] for index in train], ridge,
                    positive_weight)
                scores = _scores([rows[index] for index in test], fitted)
                for index, score in zip(test, scores):
                    heldout_scores[index] = float(score)
            grouped_logloss = _logloss(labels, heldout_scores)
            for top_k in TOP_K_GRID:
                supplied = total = incremental = 0
                exact_ranks = []
                for branch in branches:
                    exact = {index for index, label
                             in enumerate(branch["labels"]) if label}
                    if not exact:
                        continue
                    total += 1
                    order = sorted(range(len(branch["indices"])),
                                   key=lambda index: (
                                       -heldout_scores[
                                           branch["indices"][index]], index))
                    exact_ranks.append(min(order.index(index) + 1
                                           for index in exact))
                    selected = set(order[:top_k])
                    legacy = set(branch["legacy"])
                    supplied += bool(exact & (legacy | selected))
                    incremental += bool(exact & selected and
                                        not exact & legacy)
                selection_rows.append({
                    "ridge_lambda": ridge,
                    "positive_weight": positive_weight,
                    "top_k": top_k,
                    "supplied_exact_child_groups": supplied,
                    "total_exact_child_groups": total,
                    "incremental_action_marking_groups": incremental,
                    "grouped_exact_ranks": exact_ranks,
                    "mean_grouped_logloss": grouped_logloss,
                })
    selected = min(selection_rows, key=lambda row: (
        -row["supplied_exact_child_groups"], row["top_k"],
        row["mean_grouped_logloss"], row["ridge_lambda"],
        row["positive_weight"]))
    fitted = _fit_numpy(rows, labels, selected["ridge_lambda"],
                        selected["positive_weight"])
    means, scales, intercept, weights = fitted
    provisional = FrozenJointChildActionMarking(
        SCHEMA, joint_feature_names(SCHEMA), tuple(map(float, means)),
        tuple(map(float, scales)), tuple(map(float, weights)),
        float(intercept), selected["ridge_lambda"],
        selected["positive_weight"], selected["top_k"], "", True, False)
    digest = compute_model_digest(provisional)
    model = FrozenJointChildActionMarking(
        provisional.site_schema, provisional.feature_names,
        provisional.means, provisional.scales, provisional.weights,
        provisional.intercept, provisional.ridge_lambda,
        provisional.positive_weight, provisional.child_top_k,
        digest, True, False)
    artifact = {
        "format": FORMAT,
        "training_cases": case_audit,
        "training_rows": len(rows),
        "positive_rows": sum(labels),
        "position_tolerance": POSITION_TOLERANCE,
        "ridge_grid": RIDGE_GRID,
        "positive_weight_grid": POSITIVE_WEIGHT_GRID,
        "top_k_grid": TOP_K_GRID,
        "selection_rows": selection_rows,
        "selected": selected,
        "model": model_payload(model),
        "model_digest": model.model_digest,
        "target_used_for_training": True,
        "future_target_used_for_scoring": False,
        "candidate_id_or_global_frame_feature": False,
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
        raise AssertionError("joint child-action fitted artifact drift")
    text = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(json.dumps({
        "artifact_digest": artifact["artifact_digest"],
        "model_digest": artifact["model_digest"],
        "training_rows": artifact["training_rows"],
        "positive_rows": artifact["positive_rows"],
        "selected": artifact["selected"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
