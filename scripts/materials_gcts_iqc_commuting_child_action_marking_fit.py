#!/usr/bin/env python3
"""Fit a grouped child marking under the frozen commuting L1 policy."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_commuting_closure_model_artifact import \
    load_default_marking as load_upstream_marking
from materials_gcts_iqc_commuting_parent_execution import \
    freeze_commuting_second_frontier
from materials_gcts_iqc_joint_child_action_marking_fit import (
    CASES, POSITION_TOLERANCE, SCHEMA, _fit_numpy, _logloss, _scores)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_child_action_marking import (
    FORMAT, FrozenJointChildActionMarking, canonical_json,
    compute_model_digest, joint_child_action_features, joint_feature_names,
    model_from_artifact, model_payload)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_child_action_marking_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "20a805bf057252aa41898e4a9652d6e89ae4d3cde7bfad3f74dc3c82251caea8"
EXPECTED_ARTIFACT_DIGEST = \
    "2b838336088c46e527c5472879ec0f9075f121c9cf11ac3bdcd356ca578d6a2e"
EXPECTED_MODEL_DIGEST = \
    "fad91ee4b4ed4889cb57405fac1fa5c8f099bdaa718aaf7fc2aa071270b30604"
RIDGE_GRID = (.1, 1., 10., 100., 1000.)
POSITIVE_WEIGHT_GRID = (1., 3., 10., 30., 100., 300.)
TOP_K_GRID = (1, 2, 4, 8, 16, 32)


def _freeze_corpus(*, workers=4):
    upstream, upstream_artifact = load_upstream_marking()
    frozen = []
    # Phase one freezes every candidate set before any case target is opened.
    for group, (name, relative, center) in enumerate(CASES):
        source_raw = (ROOT / relative).read_bytes()
        import gzip
        receipt = json.loads(gzip.decompress(source_raw))["receipt"]
        seed, _ = oracle_crop_fast(center, 9.)
        execution = freeze_commuting_second_frontier(
            center=center, seed_positions=seed.positions,
            seed_species=seed.species, first_radius=receipt["radii"][0],
            second_radius=receipt["radii"][1], marking_model=upstream,
            workers=workers)
        frozen.append((
            group, name, relative, center, source_raw, receipt, seed,
            execution))

    rows, labels, groups, branch_records, case_audit = [], [], [], [], []
    # Phase two opens already-consumed labels only after all geometry is fixed.
    for (group, name, _relative, center, source_raw, receipt, seed,
         execution) in frozen:
        target, _ = oracle_crop_fast(center, receipt["radii"][1])
        truth = colored_position_index(
            target.positions, target.species, tolerance=POSITION_TOLERANCE)
        case_positive = 0
        exact_parents = 0
        for branch in execution.second_branches:
            features = joint_child_action_features(
                seed_positions=seed.positions, seed_species=seed.species,
                branch=branch, schema=SCHEMA)
            first_exact = all(colored_action_labels(
                branch.first_actions, truth, tolerance=POSITION_TOLERANCE))
            exact_parents += int(first_exact)
            branch_labels = tuple(int(first_exact and all(
                colored_action_labels(
                    actions, truth, tolerance=POSITION_TOLERANCE)))
                for actions in branch.second_actions)
            start = len(rows)
            rows.extend(features)
            labels.extend(branch_labels)
            groups.extend([group] * len(features))
            branch_records.append({
                "group": group,
                "parent": int(branch.first_rank),
                "indices": tuple(range(start, len(rows))),
                "labels": branch_labels,
            })
            case_positive += sum(branch_labels)
        case_audit.append({
            "name": name,
            "center": center,
            "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
            "candidate_digest": execution.selection_digest,
            "first_parents": len(execution.second_branches),
            "exact_first_parents": exact_parents,
            "second_candidates": sum(len(branch.second_actions)
                                     for branch in
                                     execution.second_branches),
            "positive_six_action_prefixes": case_positive,
        })
    return (tuple(rows), tuple(labels), tuple(groups),
            tuple(branch_records), tuple(case_audit), upstream,
            upstream_artifact)


def fit_artifact(*, workers=4):
    rows, labels, groups, branches, case_audit, upstream, upstream_artifact = \
        _freeze_corpus(workers=workers)
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
                supplied_branches = total_branches = 0
                supplied_groups = set()
                positive_groups = set()
                ranks = []
                for branch in branches:
                    exact = {index for index, label
                             in enumerate(branch["labels"]) if label}
                    if not exact:
                        continue
                    total_branches += 1
                    positive_groups.add(branch["group"])
                    order = tuple(sorted(
                        range(len(branch["indices"])), key=lambda index: (
                            -heldout_scores[branch["indices"][index]],
                            index)))
                    rank = min(order.index(index) + 1 for index in exact)
                    ranks.append((branch["group"], branch["parent"], rank))
                    if exact & set(order[:top_k]):
                        supplied_branches += 1
                        supplied_groups.add(branch["group"])
                selection_rows.append({
                    "ridge_lambda": ridge,
                    "positive_weight": positive_weight,
                    "top_k": top_k,
                    "heldout_groups_supplied": len(supplied_groups),
                    "heldout_groups_with_positive_supply":
                        len(positive_groups),
                    "heldout_exact_parent_branches_supplied":
                        supplied_branches,
                    "heldout_exact_parent_branches": total_branches,
                    "heldout_exact_ranks": tuple(ranks),
                    "heldout_first_exact_rank_sum":
                        sum(rank for _group, _parent, rank in ranks),
                    "mean_grouped_logloss": grouped_logloss,
                })
    selected = min(selection_rows, key=lambda row: (
        -row["heldout_groups_supplied"],
        -row["heldout_exact_parent_branches_supplied"],
        row["top_k"], row["heldout_first_exact_rank_sum"],
        row["mean_grouped_logloss"], row["ridge_lambda"],
        row["positive_weight"]))
    means, scales, intercept, weights = _fit_numpy(
        rows, labels, selected["ridge_lambda"],
        selected["positive_weight"])
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
        "variant": "commuting-closure-conditioned-v1",
        "upstream_model_digest": upstream.model_digest,
        "upstream_artifact_digest": upstream_artifact["artifact_digest"],
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
        "candidate_generation_target_used": False,
        "target_used_for_training": True,
        "future_target_used_for_scoring": False,
        "conditional_on_full_upstream_model": True,
        "fully_nested_upstream_selection": False,
        "candidate_id_or_global_frame_feature": False,
    }
    artifact["artifact_digest"] = hashlib.sha256(canonical_json({
        key: value for key, value in artifact.items()
        if key != "artifact_digest"})).hexdigest()
    return artifact


def summary(artifact):
    return {key: artifact[key] for key in (
        "artifact_digest", "model_digest", "upstream_model_digest",
        "training_rows", "positive_rows", "selected",
        "candidate_generation_target_used",
        "conditional_on_full_upstream_model",
        "fully_nested_upstream_selection")}


def load_default_marking(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 != "PENDING" and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("commuting child marking fixture drift")
    artifact = json.loads(gzip.decompress(raw))
    computed = hashlib.sha256(canonical_json({
        key: value for key, value in artifact.items()
        if key != "artifact_digest"})).hexdigest()
    if (computed != artifact.get("artifact_digest") or
            computed != EXPECTED_ARTIFACT_DIGEST or
            artifact.get("model_digest") != EXPECTED_MODEL_DIGEST or
            artifact.get("candidate_generation_target_used") or
            artifact.get("future_target_used_for_scoring") or
            artifact.get("fully_nested_upstream_selection") or
            not artifact.get("conditional_on_full_upstream_model")):
        raise AssertionError("commuting child marking artifact drift")
    return model_from_artifact(artifact), artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        if DEFAULT_FIXTURE.exists():
            raise RuntimeError("commuting child artifact already exists")
        artifact = fit_artifact()
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(artifact, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        artifact = load_default_marking()[1] if DEFAULT_FIXTURE.exists() \
            else fit_artifact()
    print(json.dumps(summary(artifact), indent=2, sort_keys=True))
