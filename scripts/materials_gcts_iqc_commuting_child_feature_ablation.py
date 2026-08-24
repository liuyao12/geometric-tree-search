#!/usr/bin/env python3
"""Consumed diagnostic for child-section feature fragmentation."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_commuting_child_action_marking_fit import (
    POSITION_TOLERANCE, _freeze_corpus, load_default_marking)
from materials_gcts_iqc_commuting_closure_model_artifact import \
    load_default_marking as load_parent_marking
from materials_gcts_iqc_commuting_parent_execution import \
    freeze_commuting_second_frontier
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, FIRST_RADIUS, SECOND_RADIUS, SEED_RADIUS,
    canonical_json)
from materials_gcts_iqc_hybrid_confirmation_v4 import \
    load_default_result as load_v4_result
from materials_gcts_iqc_joint_child_action_marking_fit import (
    _fit_numpy, _logloss, _scores)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_child_action_marking import \
    joint_child_action_features


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_child_feature_ablation_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "a365e591beab4553fbda68fba256ae2fc7d438582a973014df47052a41dbb5ce"
EXPECTED_RESULT_DIGEST = \
    "a28b7e776ec1dbcc04a6cadd14b4a4c737a618e71701f39f6981389c5b890d01"
RIDGE = .1
POSITIVE_WEIGHT = 10.
TOP_K = 16


def _feature_groups(names):
    names = tuple(names)
    all_indices = tuple(range(len(names)))
    non_site = tuple(index for index, name in enumerate(names)
                     if not name.startswith("child-site-"))
    legacy = tuple(index for index, name in enumerate(names)
                   if name.startswith("legacy-score:"))
    aggregate_site = tuple(index for index, name in enumerate(names)
                           if name.startswith("child-site-") and
                           (":proposed-species:" in name or
                            ":frozen-child-state-" in name or
                            ":source-" in name))
    nearest_site = tuple(index for index, name in enumerate(names)
                         if name.startswith("child-site-") and
                         (":proposed-species:" in name or
                          ":nearest-" in name or
                          ":frozen-child-state-" in name or
                          ":source-" in name))
    radial_site = tuple(index for index, name in enumerate(names)
                        if name.startswith("child-site-") and
                        (":proposed-species:" in name or
                         ":radial-bin-" in name or
                         ":frozen-child-state-" in name or
                         ":source-" in name))
    return {
        "full": all_indices,
        "no-site": non_site,
        "aggregate-site": tuple(sorted(set(non_site + aggregate_site))),
        "nearest-site": tuple(sorted(set(non_site + nearest_site))),
        "radial-site": tuple(sorted(set(non_site + radial_site))),
        "legacy-only": legacy,
    }


def _project(rows, indices):
    return tuple(tuple(row[index] for index in indices) for row in rows)


def _branch_ranks(scores, branches):
    ranks = []
    supplied = total = 0
    for branch in branches:
        exact = {index for index, label in enumerate(branch["labels"])
                 if label}
        if not exact:
            continue
        total += 1
        order = tuple(sorted(range(len(branch["indices"])), key=lambda index: (
            -scores[branch["indices"][index]], index)))
        rank = min(order.index(index) + 1 for index in exact)
        ranks.append((branch["group"], branch["parent"], rank))
        supplied += rank <= TOP_K
    return supplied, total, tuple(ranks)


def evaluate(*, workers=4):
    (rows, labels, groups, branches, _cases, parent_model,
     parent_artifact) = _freeze_corpus(workers=workers)
    frozen_child, child_artifact = load_default_marking()
    if frozen_child.model_digest != child_artifact["model_digest"]:
        raise AssertionError("child artifact drift")
    feature_groups = _feature_groups(frozen_child.feature_names)
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    execution = freeze_commuting_second_frontier(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, marking_model=parent_model,
        workers=workers)
    consumed_rows = []
    consumed_branches = []
    for branch in execution.second_branches:
        values = joint_child_action_features(
            seed_positions=seed.positions, seed_species=seed.species,
            branch=branch, schema=frozen_child.site_schema)
        start = len(consumed_rows)
        consumed_rows.extend(values)
        consumed_branches.append({
            "parent": int(branch.first_rank),
            "indices": tuple(range(start, len(consumed_rows))),
        })
    receipt = {
        "execution": asdict(execution),
        "child_artifact_digest": child_artifact["artifact_digest"],
        "representations": {name: indices
                            for name, indices in feature_groups.items()},
        "ridge": RIDGE,
        "positive_weight": POSITIVE_WEIGHT,
        "top_k": TOP_K,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    # Every consumed score is frozen before the already-consumed target opens.
    representations = {}
    frozen_consumed_scores = {}
    for name, indices in feature_groups.items():
        projected = _project(rows, indices)
        heldout_scores = [0.] * len(projected)
        for heldout in range(4):
            train = [index for index, group in enumerate(groups)
                     if group != heldout]
            test = [index for index, group in enumerate(groups)
                    if group == heldout]
            fitted = _fit_numpy(
                [projected[index] for index in train],
                [labels[index] for index in train], RIDGE, POSITIVE_WEIGHT)
            scores = _scores([projected[index] for index in test], fitted)
            for index, score in zip(test, scores):
                heldout_scores[index] = float(score)
        supplied, total, ranks = _branch_ranks(heldout_scores, branches)
        fitted = _fit_numpy(projected, labels, RIDGE, POSITIVE_WEIGHT)
        consumed_scores = tuple(map(float, _scores(
            _project(consumed_rows, indices), fitted)))
        frozen_consumed_scores[name] = consumed_scores
        representations[name] = {
            "features": len(indices),
            "development_exact_branches_supplied": supplied,
            "development_exact_branches": total,
            "development_exact_rank_sum": sum(row[2] for row in ranks),
            "development_mean_logloss": _logloss(labels, heldout_scores),
        }

    target = load_v4_result()
    sites = tuple((tuple(point), str(species))
                  for point, species in target["target_sites"])
    truth = colored_position_index(
        tuple(point for point, _species in sites),
        tuple(species for _point, species in sites),
        tolerance=POSITION_TOLERANCE)
    branch_by_parent = {int(row.first_rank): row
                        for row in execution.second_branches}
    for name, scores in frozen_consumed_scores.items():
        exact_ranks = []
        for branch in consumed_branches:
            parent = branch["parent"]
            source = branch_by_parent[parent]
            first_exact = all(colored_action_labels(
                source.first_actions, truth, tolerance=POSITION_TOLERANCE))
            exact = {index for index, actions in enumerate(
                source.second_actions) if first_exact and
                all(colored_action_labels(
                    actions, truth, tolerance=POSITION_TOLERANCE))}
            if not exact:
                continue
            order = tuple(sorted(range(len(branch["indices"])), key=lambda i: (
                -scores[branch["indices"][i]], i)))
            for child in sorted(exact):
                exact_ranks.append((parent, child,
                                    order.index(child) + 1))
        representations[name]["consumed_exact_ranks"] = exact_ranks
        representations[name]["consumed_exact_supplied"] = sum(
            rank <= TOP_K for _parent, _child, rank in exact_ranks)

    body = {
        "schema_version": 1,
        "training_rows": len(rows),
        "positive_rows": sum(labels),
        "consumed_candidates": len(consumed_rows),
        "receipt_digest": receipt_digest,
        "representations": representations,
        "candidate_generation_target_used": False,
        "consumed_target_opened_after_all_scores": True,
        "diagnostic_designed_after_consumed_failure": True,
        "fresh_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row, *, pin=True):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            row["training_rows"] != 3994 or row["positive_rows"] != 95 or
            row["candidate_generation_target_used"] or
            not row["consumed_target_opened_after_all_scores"] or
            not row["diagnostic_designed_after_consumed_failure"] or
            row["fresh_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"]):
        raise AssertionError("commuting child feature ablation drift")
    if pin and EXPECTED_RESULT_DIGEST != "PENDING" and \
            digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("commuting child feature result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 != "PENDING" and \
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("commuting child feature fixture drift")
    return validate_result(json.loads(raw))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.live or args.write:
        row = validate_result(evaluate(workers=args.workers), pin=False)
        if args.write:
            if DEFAULT_FIXTURE.exists():
                raise RuntimeError("commuting child feature fixture exists")
            DEFAULT_FIXTURE.write_text(
                json.dumps(row, indent=2, sort_keys=True) + "\n")
    else:
        row = load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))
