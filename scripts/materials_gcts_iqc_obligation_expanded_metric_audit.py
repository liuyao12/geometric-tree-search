#!/usr/bin/env python3
"""Grouped top-action audit on the preregistered disjoint IQC corpus.

The bounded role-pooled and temporal grids were defined by the earlier
consumed audits.  Geometry-only neighbor receipts are frozen first.  The real
labels and every one of 31 within-nucleus label shuffles then repeat the same
full model selection.  This is a development gate, not a confirmation.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import itertools
import json
import math
import random

import numpy as np

from materials_gcts_iqc_obligation_expanded_dataset import (
    load_default_dataset)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    SHUFFLES, SHUFFLE_SEED)
from materials_gcts_port_obligation_role_metric import (
    PortObligationRoleMetricSpec, learn_separation_threshold,
    role_conditioned_features)
from materials_gcts_port_obligation_temporal_metric import (
    PortObligationTemporalMetricSpec, temporal_role_features)


# This is exactly the finite grid used by the two published consumed audits;
# the expanded preregistration explicitly requires whole-nucleus spec refit.
ROLE_SPECS = tuple(PortObligationRoleMetricSpec(*values)
                   for values in itertools.product(
                       (4, 8, 16), (False, True), (False, True),
                       (3, 5, 7, 9), (False, True)))
TEMPORAL_SPECS = tuple(PortObligationTemporalMetricSpec(*values)
                       for values in itertools.product(
                           (8, 16), (2, 4), (False, True),
                           (3, 5, 7, 9), (False, True)))
MODEL_SPECS = tuple(
    (f"role-{index}", "role", spec)
    for index, spec in enumerate(ROLE_SPECS)) + tuple(
    (f"temporal-{index}", "temporal", spec)
    for index, spec in enumerate(TEMPORAL_SPECS)) + (
    ("role-trace", "role_trace",
     PortObligationRoleMetricSpec(4, False, False, 7, True)),
    ("temporal-trace", "temporal_trace",
     PortObligationTemporalMetricSpec(8, 2, True, 9, True)),
)
EXPECTED_AUDIT_DIGEST = \
    "8e6326a266a6cc37a871d9c2bf5e4fc12d7f545c8582e9b787ad86d4cb8bbfc0"


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _candidate_id(row):
    return f"{int(row['group'])}:{int(row['candidate_index'])}"


def _vector(row, name, spec, threshold):
    if name.startswith("role"):
        base = role_conditioned_features(
            row["transitions"], spec, threshold)
    elif name.startswith("temporal"):
        base = temporal_role_features(
            row["transitions"], spec, threshold)
    else:
        raise ValueError(f"unknown obligation model {name}")
    return base + (_trace_features(row["trace"])
                   if name.endswith("_trace") else ())


def _trace_features(trace):
    steps = tuple(trace["steps"])
    divisor = max(1, len(steps))
    mean = lambda field: sum(float(row[field]) for row in steps) / divisor
    return (
        math.log1p(float(trace["final_frontier_count"])),
        math.log1p(float(trace["final_frontier_vote_mass"])),
        math.log1p(float(trace["final_frontier_max_vote"])),
        math.log1p(float(trace["cumulative_selected_votes"])),
        float(trace["cumulative_log_probability"]) / divisor,
        mean("selected_probability"),
        mean("selected_votes"),
        mean("frontier_count_after") - mean("frontier_count_before"),
        mean("frontier_vote_mass_after") -
        mean("frontier_vote_mass_before"),
        mean("frontier_max_vote_after") -
        mean("frontier_max_vote_before"),
    )


def _representation_key(family, spec):
    if family.startswith("role"):
        return (family, spec.horizon, spec.separation_channels,
                spec.pair_channels)
    return (family, spec.horizon, spec.time_bins,
            spec.separation_channels)


def _freeze_model_receipts(geometry, family, spec):
    groups = tuple(sorted({int(row["group"]) for row in geometry}))
    receipts, thresholds = {}, {}
    cached_unseparated = None
    if not spec.separation_channels:
        cached_unseparated = np.asarray(tuple(
            _vector(row, family, spec, 0.) for row in geometry), dtype=float)
    for heldout in groups:
        train_indices = np.asarray(tuple(
            index for index, row in enumerate(geometry)
            if int(row["group"]) != heldout), dtype=int)
        test_indices = np.asarray(tuple(
            index for index, row in enumerate(geometry)
            if int(row["group"]) == heldout), dtype=int)
        training = tuple(geometry[index] for index in train_indices)
        threshold = learn_separation_threshold(training) \
            if spec.separation_channels else 0.
        thresholds[heldout] = threshold
        vectors = cached_unseparated
        if vectors is None:
            vectors = np.asarray(tuple(
                _vector(row, family, spec, threshold) for row in geometry),
                dtype=float)
        train = vectors[train_indices]
        means = train.mean(axis=0)
        scales = np.maximum(1e-9, train.std(axis=0))
        standardized_train = (train - means) / scales
        standardized_test = (vectors[test_indices] - means) / scales
        distances = np.maximum(0.,
            np.sum(standardized_test * standardized_test, axis=1)[:, None] +
            np.sum(standardized_train * standardized_train, axis=1)[None, :] -
            2. * standardized_test @ standardized_train.T)
        train_groups = tuple(int(geometry[index]["group"])
                             for index in train_indices)
        for local_test, test_index in enumerate(test_indices):
            nearest = {}
            for local_train, train_index in enumerate(train_indices):
                row = geometry[int(train_index)]
                record = (float(distances[local_test, local_train]),
                          _candidate_id(row))
                group = train_groups[local_train]
                if group not in nearest or record < nearest[group]:
                    nearest[group] = record
            receipts[_candidate_id(geometry[int(test_index)])] = tuple(
                sorted(nearest.values()))
    body = {
        "family": family, "representation": _representation_key(
            family, spec),
        "thresholds": tuple(sorted(thresholds.items())),
        "receipts": tuple(sorted(receipts.items())),
    }
    return receipts, thresholds, _digest(body)


def freeze_geometry_receipts(geometry):
    result = {}
    for _model_id, family, spec in MODEL_SPECS:
        key = _representation_key(family, spec)
        if key in result:
            continue
        receipts, thresholds, digest = _freeze_model_receipts(
            geometry, family, spec)
        result[key] = {
            "receipts": receipts, "thresholds": thresholds,
            "digest": digest,
        }
    return result, _digest(tuple(
        (repr(key), result[key]["digest"]) for key in sorted(result,
            key=repr)))


def _score_receipt(receipt, labels, spec):
    nearest = receipt[:spec.neighbors]
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if spec.weighted else 1.
                    for distance, _candidate in nearest)
    return sum(weight * float(labels[candidate][0])
               for weight, (_distance, candidate) in zip(weights, nearest)) / \
        sum(weights)


def _auc(labels, scores):
    positive = tuple(key for key, value in labels.items() if value[0])
    negative = tuple(key for key, value in labels.items() if not value[0])
    if not positive or not negative:
        return .5
    wins = sum((scores[left] > scores[right]) +
               .5 * (scores[left] == scores[right])
               for left in positive for right in negative)
    return wins / (len(positive) * len(negative))


def _heldout(geometry, labels, model_id, family, spec, receipt_record):
    scores = {_candidate_id(row): _score_receipt(
        receipt_record["receipts"][_candidate_id(row)], labels, spec)
        for row in geometry}
    selected = []
    groups = tuple(sorted({int(row["group"]) for row in geometry}))
    for group in groups:
        rows = tuple(row for row in geometry if int(row["group"]) == group)
        selected.append(min(rows, key=lambda row: (
            -scores[_candidate_id(row)], _candidate_id(row))))
    epsilon = 1e-9
    logloss = -sum(
        float(labels[key][0]) * math.log(max(epsilon, value)) +
        (1. - float(labels[key][0])) * math.log(max(
            epsilon, 1. - value)) for key, value in scores.items()) / \
        len(scores)
    return {
        "model_id": model_id,
        "family": family,
        "selected": tuple(_candidate_id(row) for row in selected),
        "exact": sum(int(labels[_candidate_id(row)][0])
                     for row in selected),
        "sites": sum(int(labels[_candidate_id(row)][1])
                     for row in selected),
        "exact_bearing_groups": sum(any(labels[_candidate_id(row)][0]
            for row in geometry if int(row["group"]) == group)
            for group in groups),
        "auc": _auc(labels, scores),
        "logloss": logloss,
    }


def _select(geometry, labels, receipts):
    audits = tuple(_heldout(
        geometry, labels, model_id, family, spec,
        receipts[_representation_key(family, spec)])
        for model_id, family, spec in MODEL_SPECS)
    index = max(range(len(audits)), key=lambda candidate: (
        audits[candidate]["exact"], audits[candidate]["sites"],
        -audits[candidate]["logloss"], audits[candidate]["auc"],
        -candidate))
    return index, audits


def _shuffle(labels, trial):
    rng = random.Random(
        f"{SHUFFLE_SEED}:expanded-obligation-metric:{trial}")
    result = dict(labels)
    groups = sorted({int(key.split(":", 1)[0]) for key in labels})
    for group in groups:
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
        "candidate_index": index,
        "action_key": row["action_key"],
        "transitions": row["transitions"],
        "trace": row["trace"],
        "trace_digest": row["trace_digest"],
    } for group in dataset["groups"]
      for index, row in enumerate(group["rows"]))
    receipts, receipt_digest = freeze_geometry_receipts(geometry)
    labels = {_candidate_id({"group": int(group["group"]),
                             "candidate_index": index}):
              (bool(row["exact"]), int(row["correct_sites"]))
              for group in dataset["groups"]
              for index, row in enumerate(group["rows"])}
    selected_index, audits = _select(geometry, labels, receipts)
    selected = audits[selected_index]
    null_results, null_models = [], []
    for trial in range(SHUFFLES):
        null_index, null_audits = _select(
            geometry, _shuffle(labels, trial), receipts)
        null_results.append(null_audits[null_index])
        null_models.append(MODEL_SPECS[null_index][0])
    null_exact = tuple(row["exact"] for row in null_results)
    null_sites = tuple(row["sites"] for row in null_results)
    exact_p = (1 + sum(value >= selected["exact"]
                       for value in null_exact)) / (SHUFFLES + 1)
    sites_p = (1 + sum(value >= selected["sites"]
                       for value in null_sites)) / (SHUFFLES + 1)
    body = {
        "schema_version": 1,
        "development_dataset_digest": dataset["dataset_digest"],
        "development_groups": len(dataset["groups"]),
        "candidate_count": len(geometry),
        "candidate_spec_count": len(MODEL_SPECS),
        "unique_geometry_representation_count": len(receipts),
        "geometry_receipt_digest_before_labels": receipt_digest,
        "candidate_models": tuple({
            "model_id": model_id, "family": family,
            "spec": asdict(spec)} for model_id, family, spec in MODEL_SPECS),
        "selected_model": {
            "model_id": MODEL_SPECS[selected_index][0],
            "family": MODEL_SPECS[selected_index][1],
            "spec": asdict(MODEL_SPECS[selected_index][2]),
        },
        "selected_result": selected,
        "all_model_results": audits,
        "shuffle_trials": SHUFFLES,
        "fully_reselected_shuffle_models": tuple(null_models),
        "shuffle_exact_counts": null_exact,
        "shuffle_site_counts": null_sites,
        "shuffle_exact_median": sorted(null_exact)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_exact_upper_tail_p": exact_p,
        "shuffle_sites_median": sorted(null_sites)[SHUFFLES // 2],
        "shuffle_sites_maximum": max(null_sites),
        "shuffle_sites_upper_tail_p": sites_p,
        "failed_or_label_trivial_nuclei_retained": True,
        "labels_and_correct_site_counts_shuffled_together": True,
        "numeric_acceleration_changed_no_candidates_or_semantics": True,
        "expanded_development_consumed": True,
        "candidate_geometry_changed": False,
        "targets_used_for_receipts_or_ranking": False,
        "consumed_confirmation_used_for_selection": False,
        "fresh_confirmation_opened": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["correct_site_yield_gate_passed"] = bool(
        sites_p <= .05 and selected["sites"] > max(null_sites))
    body["exact_action_gate_passed"] = bool(
        exact_p <= .05 and selected["exact"] > max(null_exact))
    body["top_action_superiority_gate_passed"] = bool(
        body["correct_site_yield_gate_passed"] and
        body["exact_action_gate_passed"])
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("expanded obligation top-action gate passes" if
           report["top_action_superiority_gate_passed"] else
           "expanded obligation top-action gate remains red"))


if __name__ == "__main__":
    main()
