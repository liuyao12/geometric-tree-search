#!/usr/bin/env python3
"""Rollout-value audit trained with target-free quantile failures.

All sixteen candidates per nucleus train each grouped model, while evaluation
remains restricted to the unchanged top-eight execution portfolio.  This tests
whether broadened failure roles make future connection markings causal rather
than merely reflecting an already high-purity shortlist.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
import random

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_metric_audit import (
    MODEL_SPECS, _auc, _candidate_id, _representation_key, _score_receipt,
    freeze_geometry_receipts)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    SHUFFLES, SHUFFLE_SEED)
from materials_gcts_iqc_stage_local_augmented_rollout_dataset import (
    load_default_dataset)


EXPECTED_AUDIT_DIGEST = \
    "f8c45d84339b3f10ee18a2d3cf71c4ca686c773318788c7a17afe8982087777f"


def _shuffle(labels, trial):
    rng = random.Random(f"{SHUFFLE_SEED}:augmented-rollout:{trial}")
    result = dict(labels)
    for group in sorted({int(key.split(":", 1)[0]) for key in labels}):
        keys = sorted(key for key in labels
                      if int(key.split(":", 1)[0]) == group)
        values = [labels[key] for key in keys]
        rng.shuffle(values)
        result.update(zip(keys, values))
    return result


def _heldout_augmented(evaluation, training_labels, model_id, family, spec,
                       receipt_record):
    """Fit scores from all frozen labels, but audit only executable rows."""
    evaluation_labels = {
        _candidate_id(row): training_labels[_candidate_id(row)]
        for row in evaluation}
    scores = {_candidate_id(row): _score_receipt(
        receipt_record["receipts"][_candidate_id(row)],
        training_labels, spec) for row in evaluation}
    groups = tuple(sorted({int(row["group"]) for row in evaluation}))
    selected = tuple(min(
        (row for row in evaluation if int(row["group"]) == group),
        key=lambda row: (-scores[_candidate_id(row)], _candidate_id(row)))
                     for group in groups)
    epsilon = 1e-9
    logloss = -sum(
        float(evaluation_labels[key][0]) * math.log(max(epsilon, value)) +
        (1. - float(evaluation_labels[key][0])) * math.log(max(
            epsilon, 1. - value)) for key, value in scores.items()) / len(scores)
    return {
        "model_id": model_id, "family": family,
        "selected": tuple(_candidate_id(row) for row in selected),
        "exact": sum(int(evaluation_labels[_candidate_id(row)][0])
                     for row in selected),
        "sites": sum(int(evaluation_labels[_candidate_id(row)][1])
                     for row in selected),
        "exact_bearing_groups": sum(any(
            evaluation_labels[_candidate_id(row)][0]
            for row in evaluation if int(row["group"]) == group)
                                    for group in groups),
        "auc": _auc(evaluation_labels, scores), "logloss": logloss,
    }


def _select(evaluation, labels, receipts):
    audits = tuple(_heldout_augmented(
        evaluation, labels, model_id, family, spec,
        receipts[_representation_key(family, spec)])
        for model_id, family, spec in MODEL_SPECS)
    index = max(range(len(audits)), key=lambda candidate: (
        audits[candidate]["exact"], audits[candidate]["sites"],
        -audits[candidate]["logloss"], audits[candidate]["auc"],
        -candidate))
    return index, audits


def evaluate():
    dataset = load_default_dataset()
    geometry = tuple({
        "group": int(group["group"]),
        "candidate_index": int(row["candidate_index"]),
        "action_key": row["action_key"],
        "transitions": row["transitions"], "trace": row["trace"],
        "trace_digest": row["trace_digest"],
        "execution_eligible": bool(row["execution_eligible"]),
    } for group in dataset["groups"] for row in group["rows"])
    evaluation = tuple(row for row in geometry if row["execution_eligible"])
    labels = {_candidate_id({
        "group": int(group["group"]),
        "candidate_index": int(row["candidate_index"])}):
        (bool(row["exact"]), int(row["correct_sites"]))
              for group in dataset["groups"] for row in group["rows"]}
    receipts, receipt_digest = freeze_geometry_receipts(geometry)
    index, audits = _select(evaluation, labels, receipts)
    selected = audits[index]
    nulls, null_models = [], []
    for trial in range(SHUFFLES):
        null_index, results = _select(
            evaluation, _shuffle(labels, trial), receipts)
        null_models.append(MODEL_SPECS[null_index][0])
        nulls.append(results[null_index])
    null_exact = tuple(row["exact"] for row in nulls)
    null_sites = tuple(row["sites"] for row in nulls)
    exact_p = (1 + sum(value >= selected["exact"]
                       for value in null_exact)) / (SHUFFLES + 1)
    sites_p = (1 + sum(value >= selected["sites"]
                       for value in null_sites)) / (SHUFFLES + 1)
    execution_groups = tuple(tuple(
        row for row in group["rows"] if row["execution_eligible"])
                             for group in dataset["groups"])
    supply = sum(any(row["exact"] for row in group)
                 for group in execution_groups)
    baseline_exact = sum(bool(group[0]["exact"])
                         for group in execution_groups)
    baseline_sites = sum(int(group[0]["correct_sites"])
                         for group in execution_groups)
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "training_candidates": len(geometry),
        "execution_candidates": len(evaluation),
        "exact_execution_supply_groups": supply,
        "quantile_training_candidates_used_at_execution": False,
        "candidate_model_count": len(MODEL_SPECS),
        "geometry_receipt_digest_before_labels": receipt_digest,
        "candidate_models": tuple({
            "model_id": model_id, "family": family, "spec": asdict(spec)}
            for model_id, family, spec in MODEL_SPECS),
        "selected_model_index": index,
        "selected_model": {
            "model_id": MODEL_SPECS[index][0],
            "family": MODEL_SPECS[index][1],
            "spec": asdict(MODEL_SPECS[index][2]),
        },
        "selected_result": selected,
        "all_model_results": audits,
        "connection_top_one_exact": baseline_exact,
        "connection_top_one_sites": baseline_sites,
        "shuffle_trials": SHUFFLES,
        "fully_reselected_shuffle_models": tuple(null_models),
        "shuffle_exact_counts": null_exact,
        "shuffle_site_counts": null_sites,
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_sites_maximum": max(null_sites),
        "shuffle_exact_upper_tail_p": exact_p,
        "shuffle_sites_upper_tail_p": sites_p,
        "candidate_label_vectors_shuffled_over_all_sixteen": True,
        "candidate_geometry_or_rollouts_changed": False,
        "confirmation_data_imported_or_used": False,
        "targets_used_for_receipts_or_ranking": False,
        "consumed_development_only": True,
        "fresh_confirmation_opened": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["augmented_rollout_gate_passed"] = bool(
        selected["exact"] == supply and selected["sites"] >= baseline_sites and
        selected["exact"] > max(null_exact) and
        selected["sites"] > max(null_sites) and
        exact_p <= .05 and sites_p <= .05)
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    if EXPECTED_AUDIT_DIGEST and row["audit_digest"] != \
            EXPECTED_AUDIT_DIGEST:
        raise AssertionError("augmented rollout value audit drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          ("augmented rollout value gate passes" if
           row["augmented_rollout_gate_passed"] else
           "augmented rollout value gate remains red"))


if __name__ == "__main__":
    main()
