#!/usr/bin/env python3
"""Grouped connection-rollout value audit for stage-local IQC terminals."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import random

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_metric_audit import (
    MODEL_SPECS, _candidate_id, _select, freeze_geometry_receipts)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    SHUFFLES, SHUFFLE_SEED)
from materials_gcts_iqc_stage_local_rollout_dataset import load_default_dataset


EXPECTED_AUDIT_DIGEST = ""


def _shuffle(labels, trial):
    rng = random.Random(f"{SHUFFLE_SEED}:stage-local-rollout:{trial}")
    result = dict(labels)
    for group in sorted({int(key.split(":", 1)[0]) for key in labels}):
        keys = sorted(key for key in labels
                      if int(key.split(":", 1)[0]) == group)
        values = [labels[key] for key in keys]
        rng.shuffle(values)
        result.update(zip(keys, values))
    return result


def evaluate():
    dataset = load_default_dataset()
    geometry = tuple({
        "group": int(group["group"]),
        "candidate_index": int(row["candidate_index"]),
        "action_key": row["action_key"],
        "transitions": row["transitions"], "trace": row["trace"],
        "trace_digest": row["trace_digest"],
    } for group in dataset["groups"] for row in group["rows"])
    labels = {_candidate_id({
        "group": int(group["group"]),
        "candidate_index": int(row["candidate_index"])}):
        (bool(row["exact"]), int(row["correct_sites"]))
              for group in dataset["groups"] for row in group["rows"]}
    receipts, receipt_digest = freeze_geometry_receipts(geometry)
    selected_index, audits = _select(geometry, labels, receipts)
    selected = audits[selected_index]
    nulls, null_models = [], []
    for trial in range(SHUFFLES):
        index, results = _select(
            geometry, _shuffle(labels, trial), receipts)
        null_models.append(MODEL_SPECS[index][0])
        nulls.append(results[index])
    null_exact = tuple(row["exact"] for row in nulls)
    null_sites = tuple(row["sites"] for row in nulls)
    exact_p = (1 + sum(value >= selected["exact"]
                       for value in null_exact)) / (SHUFFLES + 1)
    sites_p = (1 + sum(value >= selected["sites"]
                       for value in null_sites)) / (SHUFFLES + 1)
    supply = sum(any(row["exact"] for row in group["rows"])
                 for group in dataset["groups"])
    # The first candidate is the frozen connection score's top terminal.
    connection_exact = sum(bool(group["rows"][0]["exact"])
                           for group in dataset["groups"])
    connection_sites = sum(int(group["rows"][0]["correct_sites"])
                           for group in dataset["groups"])
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "candidate_count": len(geometry),
        "exact_supply_groups": supply,
        "candidate_model_count": len(MODEL_SPECS),
        "geometry_receipt_digest_before_labels": receipt_digest,
        "candidate_models": tuple({
            "model_id": model_id, "family": family, "spec": asdict(spec)}
            for model_id, family, spec in MODEL_SPECS),
        "selected_model_index": selected_index,
        "selected_model": {
            "model_id": MODEL_SPECS[selected_index][0],
            "family": MODEL_SPECS[selected_index][1],
            "spec": asdict(MODEL_SPECS[selected_index][2]),
        },
        "selected_result": selected,
        "all_model_results": audits,
        "connection_top_one_exact": connection_exact,
        "connection_top_one_sites": connection_sites,
        "shuffle_trials": SHUFFLES,
        "fully_reselected_shuffle_models": tuple(null_models),
        "shuffle_exact_counts": null_exact,
        "shuffle_site_counts": null_sites,
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_sites_maximum": max(null_sites),
        "shuffle_exact_upper_tail_p": exact_p,
        "shuffle_sites_upper_tail_p": sites_p,
        "candidate_label_vectors_shuffled_within_nucleus": True,
        "candidate_geometry_or_rollouts_changed": False,
        "confirmation_data_imported_or_used": False,
        "targets_used_for_receipts_or_ranking": False,
        "consumed_development_only": True,
        "fresh_confirmation_opened": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["rollout_value_gate_passed"] = bool(
        selected["exact"] == supply and selected["sites"] >= connection_sites and
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
        raise AssertionError("stage-local rollout value audit drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          ("stage-local rollout value gate passes" if
           row["rollout_value_gate_passed"] else
           "stage-local rollout value gate remains red"))


if __name__ == "__main__":
    main()
