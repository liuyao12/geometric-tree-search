#!/usr/bin/env python3
"""Fit the local-section child marking on three consumed IQC nuclei.

Requires NumPy only when regenerating the frozen artifact.  All targets here
are already consumed development/confirmation data.  Grouped selection leaves
one entire nucleus out and scores incremental exact-child supply when the new
channel is unioned with the four legacy marking channels.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_local_section_child_marking import (
    DEFAULT_FIXTURE, FORMAT, FrozenLocalSectionChildMarking,
    FrozenLocalSectionSchema, compute_model_digest, feature_names,
    local_section_features, model_payload)


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
)
SCHEMA = FrozenLocalSectionSchema(
    ("X", "Y", "Z"), 8., .25, 8,
    ("base", "colored", "ports", "coupled"), 6)
POSITION_TOLERANCE = 1e-5
RIDGE_GRID = (.1, 1., 10., 100., 1000.)
TOP_K_GRID = (1, 2, 4, 8, 16)
AGGREGATION = "minimum"
EXPECTED_ARTIFACT_DIGEST = (
    "9f8f3a73155b79b36d7b299a1f0db11ad082f5460569805fc8f6385770f15146")


def _distance_squared(first, second):
    return sum((a - b) ** 2 for a, b in zip(first, second))


def _action_key(action):
    point, color = action
    return tuple(round(float(value), SCHEMA.site_key_decimals)
                 for value in point), str(color)


def _load_rows():
    root = Path(__file__).resolve().parent
    rows, groups = [], []
    case_records = []
    for group, (name, relative, center) in enumerate(CASES):
        raw = gzip.decompress((root / relative).read_bytes())
        receipt = json.loads(raw)["receipt"]
        seed, _ = oracle_crop_fast(center, 9.)
        target, _ = oracle_crop_fast(center, 32.56230589874905)
        by_species = {color: tuple(point for point, species in zip(
            target.positions, target.species) if species == color)
                      for color in set(target.species)}
        branches = []
        for branch in receipt["second_branches"]:
            features = local_section_features(
                seed_positions=seed.positions, seed_species=seed.species,
                branch=branch, schema=SCHEMA)
            labels = {}
            for key in features:
                point, color = key
                labels[key] = min(_distance_squared(
                    point, candidate) for candidate in by_species[color]) <= \
                    POSITION_TOLERANCE ** 2
                rows.append(features[key]); groups.append((group, labels[key]))
            first_exact = all(min(_distance_squared(
                tuple(map(float, point)), candidate)
                for candidate in by_species[str(color)]) <=
                POSITION_TOLERANCE ** 2
                for point, color in branch["first_actions"])
            exact_children = tuple(index for index, actions in enumerate(
                branch["second_actions"]) if first_exact and all(
                    labels[_action_key(action)] for action in actions))
            legacy = []
            for channel in range(len(SCHEMA.source_channel_names)):
                order = sorted(range(len(branch["second_actions"])),
                               key=lambda index: (
                                   -branch["second_channel_scores"][index][
                                       channel], index))
                for child in order[:8]:
                    if child not in legacy:
                        legacy.append(child)
            branches.append({
                "branch": branch, "features": features,
                "exact_children": exact_children,
                "legacy_children": tuple(legacy)})
        case_records.append({
            "name": name, "group": group, "seed": seed,
            "branches": branches})
    return rows, groups, case_records


def _fit_numpy(matrix, labels, ridge):
    import numpy as np
    matrix = np.asarray(matrix, dtype=float)
    labels = np.asarray(labels, dtype=float)
    means = matrix.mean(axis=0)
    scales = matrix.std(axis=0)
    scales[scales < 1e-9] = 1.
    normalized = (matrix - means) / scales
    design = np.column_stack((np.ones(len(normalized)), normalized))
    weights = np.zeros(design.shape[1])
    regularized = np.r_[0., np.ones(design.shape[1] - 1)]
    for _ in range(100):
        logits = np.clip(design @ weights, -30., 30.)
        probabilities = 1. / (1. + np.exp(-logits))
        gradient = design.T @ (probabilities - labels) + \
            ridge * regularized * weights
        variance = probabilities * (1. - probabilities)
        hessian = design.T @ (design * variance[:, None]) + \
            ridge * np.diag(regularized) + 1e-8 * np.eye(design.shape[1])
        step = np.linalg.solve(hessian, gradient)
        weights -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    return means, scales, weights[0], weights[1:]


def _probabilities(matrix, fitted):
    import numpy as np
    means, scales, intercept, weights = fitted
    matrix = np.asarray(matrix, dtype=float)
    logits = np.clip(intercept + ((matrix - means) / scales) @ weights,
                     -30., 30.)
    return 1. / (1. + np.exp(-logits))


def _logloss(labels, probabilities):
    return sum(-(label * math.log(max(probability, 1e-12)) +
                 (1 - label) * math.log(max(1 - probability, 1e-12)))
               for label, probability in zip(labels, probabilities)) / \
        len(labels)


def fit_artifact():
    rows, grouped_labels, cases = _load_rows()
    labels = [int(label) for _group, label in grouped_labels]
    selection_rows = []
    for ridge in RIDGE_GRID:
        fold_scores = {}
        fold_logloss = []
        for heldout in range(len(CASES)):
            train_indices = [index for index, (group, _label)
                             in enumerate(grouped_labels)
                             if group != heldout]
            test_indices = [index for index, (group, _label)
                            in enumerate(grouped_labels)
                            if group == heldout]
            fitted = _fit_numpy([rows[index] for index in train_indices],
                                [labels[index] for index in train_indices],
                                ridge)
            probabilities = _probabilities(
                [rows[index] for index in test_indices], fitted)
            fold_logloss.append(_logloss(
                [labels[index] for index in test_indices], probabilities))
            lookup = {}
            for index, probability in zip(test_indices, probabilities):
                group = grouped_labels[index][0]
                lookup.setdefault(group, []).append(float(probability))
            # Recompute a feature-key probability map in stable row order.
            cursor = 0
            for case in cases:
                if case["group"] != heldout:
                    continue
                values = lookup[heldout]
                for branch in case["branches"]:
                    count = len(branch["features"])
                    branch["_heldout_probabilities"] = dict(zip(
                        sorted(branch["features"]), values[cursor:
                            cursor + count]))
                    cursor += count
        for top_k in TOP_K_GRID:
            supplied = total = 0
            for case in cases:
                for branch in case["branches"]:
                    exact = set(branch["exact_children"])
                    if not exact:
                        continue
                    total += 1
                    scores = []
                    probability = branch["_heldout_probabilities"]
                    for child, actions in enumerate(
                            branch["branch"]["second_actions"]):
                        score = min(probability[_action_key(action)]
                                    for action in actions)
                        scores.append((score, child))
                    local = {child for _score, child in sorted(
                        scores, key=lambda row: (-row[0], row[1]))[:top_k]}
                    supplied += bool(exact & (
                        set(branch["legacy_children"]) | local))
            selection_rows.append({
                "ridge_lambda": ridge, "top_k": top_k,
                "supplied_exact_child_groups": supplied,
                "total_exact_child_groups": total,
                "mean_grouped_logloss": sum(fold_logloss) /
                    len(fold_logloss)})
    selected = min(selection_rows, key=lambda row: (
        -row["supplied_exact_child_groups"], row["top_k"],
        row["mean_grouped_logloss"], row["ridge_lambda"]))
    fitted = _fit_numpy(rows, labels, selected["ridge_lambda"])
    means, scales, intercept, weights = fitted
    provisional = FrozenLocalSectionChildMarking(
        SCHEMA, feature_names(SCHEMA), tuple(map(float, means)),
        tuple(map(float, scales)), tuple(map(float, weights)),
        float(intercept), selected["ridge_lambda"], selected["top_k"],
        AGGREGATION, "", True, False)
    digest = compute_model_digest(provisional)
    model = FrozenLocalSectionChildMarking(
        provisional.schema, provisional.feature_names, provisional.means,
        provisional.scales, provisional.weights, provisional.intercept,
        provisional.ridge_lambda, provisional.child_top_k,
        provisional.aggregation, digest, True, False)
    artifact = {
        "format": FORMAT,
        "training_cases": tuple({
            "name": name, "center": center,
            "source_fixture_sha256": hashlib.sha256((
                Path(__file__).resolve().parent / relative).read_bytes()
            ).hexdigest()} for name, relative, center in CASES),
        "training_rows": len(rows),
        "positive_rows": sum(labels),
        "position_tolerance": POSITION_TOLERANCE,
        "ridge_grid": RIDGE_GRID,
        "top_k_grid": TOP_K_GRID,
        "selection_rows": selection_rows,
        "selected": selected,
        "model": model_payload(model),
        "model_digest": model.model_digest,
        "target_used_for_training": True,
        "future_target_used_for_scoring": False,
        "family_or_global_origin_feature": False,
    }
    artifact["artifact_digest"] = hashlib.sha256(
        canonical_json({key: value for key, value in artifact.items()
                        if key != "artifact_digest"})).hexdigest()
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    artifact = fit_artifact()
    if (EXPECTED_ARTIFACT_DIGEST and
            artifact["artifact_digest"] != EXPECTED_ARTIFACT_DIGEST):
        raise AssertionError("local-section fitted artifact drift")
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
