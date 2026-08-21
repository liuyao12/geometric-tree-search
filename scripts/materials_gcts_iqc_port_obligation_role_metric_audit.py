#!/usr/bin/env python3
"""Grouped audit of a role-conditioned IQC obligation metric.

All geometry-only nearest-neighbor receipts are frozen before labels are used.
The feature/spec choice is nested by nucleus and every within-nucleus shuffle
repeats that choice.  A final train-only model ranks the consumed confirmation
trajectories before the published partial label order is loaded.  The target
is never reconstructed or reopened.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import itertools
import json
import math
import random

from materials_gcts_iqc_port_obligation_automaton_audit import _rows
from materials_gcts_iqc_port_obligation_confirmation import (
    load_default_result as load_confirmation_result)
from materials_gcts_iqc_port_obligation_confirmation_trajectories import (
    load_default_dataset as load_confirmation_trajectories)
from materials_gcts_iqc_relational_port_rule import SHUFFLES, SHUFFLE_SEED
from materials_gcts_port_obligation_role_metric import (
    PortObligationRoleMetricSpec, fit_port_obligation_role_metric,
    learn_separation_threshold, role_conditioned_features,
    score_port_obligation_role_metric)


HORIZONS = (4, 8, 16)
SEPARATION_CHANNELS = (False, True)
PAIR_CHANNELS = (False, True)
NEIGHBORS = (3, 5, 7, 9)
WEIGHTED = (False, True)
SPECS = tuple(PortObligationRoleMetricSpec(*values)
              for values in itertools.product(
                  HORIZONS, SEPARATION_CHANNELS, PAIR_CHANNELS,
                  NEIGHBORS, WEIGHTED))


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _candidate_id(row):
    return f"{int(row['group'])}:{int(row['stable_index'])}"


def _action_tuple(action):
    return tuple((tuple(float(value) for value in point), str(color))
                 for point, color in action)


def _feature_key(spec):
    return spec.horizon, spec.separation_channels, spec.pair_channels


def _feature_spec(key):
    return PortObligationRoleMetricSpec(*key, 1, False)


def _scales(vectors, training_indices):
    dimensions = len(vectors[0])
    means = tuple(sum(vectors[index][dimension]
                      for index in training_indices) / len(training_indices)
                  for dimension in range(dimensions))
    return tuple(max(1e-9, math.sqrt(sum(
        (vectors[index][dimension] - means[dimension]) ** 2
        for index in training_indices) / len(training_indices)))
        for dimension in range(dimensions))


def _freeze_neighbor_receipts(geometry):
    groups = tuple(sorted({int(row["group"]) for row in geometry}))
    receipts = {}
    thresholds = {}
    for heldout in groups:
        training_indices = tuple(index for index, row in enumerate(geometry)
                                 if int(row["group"]) != heldout)
        testing_indices = tuple(index for index, row in enumerate(geometry)
                                if int(row["group"]) == heldout)
        training = tuple(geometry[index] for index in training_indices)
        for key in sorted({_feature_key(spec) for spec in SPECS}):
            spec = _feature_spec(key)
            threshold = learn_separation_threshold(training) \
                if spec.separation_channels else 0.
            thresholds[heldout, key] = threshold
            vectors = tuple(role_conditioned_features(
                row["transitions"], spec, threshold) for row in geometry)
            scales = _scales(vectors, training_indices)
            for test_index in testing_indices:
                nearest_by_group = {}
                for train_index in training_indices:
                    distance = sum(((left - right) / scale) ** 2
                                   for left, right, scale in zip(
                                       vectors[test_index],
                                       vectors[train_index], scales))
                    row = geometry[train_index]
                    record = (distance, _candidate_id(row))
                    group = int(row["group"])
                    prior = nearest_by_group.get(group)
                    if prior is None or record < prior:
                        nearest_by_group[group] = record
                receipts[key, _candidate_id(geometry[test_index])] = \
                    tuple(sorted(nearest_by_group.values()))
    digest = _digest((tuple(sorted((repr(key), value)
                                   for key, value in receipts.items())),
                      tuple(sorted((repr(key), value)
                                   for key, value in thresholds.items()))))
    return receipts, thresholds, digest


def _score_receipt(receipt, labels, spec):
    nearest = receipt[:spec.neighbors]
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if spec.weighted else 1.
                    for distance, _candidate in nearest)
    return sum(weight * float(labels[candidate])
               for weight, (_distance, candidate) in zip(weights, nearest)) / \
        sum(weights)


def _auc(labels, scores):
    positive = tuple(key for key, value in labels.items() if value)
    negative = tuple(key for key, value in labels.items() if not value)
    if not positive or not negative:
        return .5
    wins = sum((scores[left] > scores[right]) +
               .5 * (scores[left] == scores[right])
               for left in positive for right in negative)
    return wins / (len(positive) * len(negative))


def _heldout(geometry, labels, sites, spec, receipts):
    key = _feature_key(spec)
    scores = {_candidate_id(row): _score_receipt(
        receipts[key, _candidate_id(row)], labels, spec)
        for row in geometry}
    selected = []
    for group in sorted({int(row["group"]) for row in geometry}):
        rows = tuple(row for row in geometry if int(row["group"]) == group)
        selected.append(min(rows, key=lambda row: (
            -scores[_candidate_id(row)], int(row["stable_index"]))))
    epsilon = 1e-9
    logloss = -sum(float(labels[key]) * math.log(max(epsilon, value)) +
                   (1. - float(labels[key])) * math.log(max(
                       epsilon, 1. - value))
                   for key, value in scores.items()) / len(scores)
    return {
        "selected": tuple((int(row["group"]), int(row["stable_index"]))
                          for row in selected),
        "exact": sum(bool(labels[_candidate_id(row)]) for row in selected),
        "sites": sum(int(sites[_candidate_id(row)]) for row in selected),
        "logloss": logloss,
        "auc": _auc(labels, scores),
    }


def _objective(result, index):
    spec = SPECS[index]
    return (result["exact"], result["sites"], -result["logloss"],
            result["auc"], -spec.horizon,
            not spec.pair_channels, not spec.separation_channels,
            -spec.neighbors, spec.weighted, -index)


def _select(geometry, labels, sites, receipts):
    audits = tuple(_heldout(
        geometry, labels, sites, spec, receipts) for spec in SPECS)
    index = max(range(len(audits)), key=lambda candidate:
                _objective(audits[candidate], candidate))
    return index, audits


def _shuffle(labels, trial):
    rng = random.Random(f"{SHUFFLE_SEED}:obligation-role-metric:{trial}")
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
    development, geometry, raw_labels, geometry_digest = _rows()
    labels = {_candidate_id(row): bool(raw_labels[
        int(row["group"]), int(row["stable_index"])][0])
        for row in geometry}
    sites = {_candidate_id(row): int(raw_labels[
        int(row["group"]), int(row["stable_index"])][1])
        for row in geometry}
    receipts, thresholds, receipt_digest = _freeze_neighbor_receipts(geometry)
    selected_index, audits = _select(
        geometry, labels, sites, receipts)
    selected_spec = SPECS[selected_index]
    selected = audits[selected_index]
    null_exact = []
    null_auc = []
    null_logloss = []
    null_specs = []
    for trial in range(SHUFFLES):
        shuffled = _shuffle(labels, trial)
        null_index, null_audits = _select(
            geometry, shuffled, sites, receipts)
        null_exact.append(null_audits[null_index]["exact"])
        null_auc.append(null_audits[null_index]["auc"])
        null_logloss.append(null_audits[null_index]["logloss"])
        null_specs.append(null_index)
    p_value = (1 + sum(value >= selected["exact"]
                       for value in null_exact)) / (SHUFFLES + 1)

    training_rows = tuple({
        **row, "candidate_id": _candidate_id(row),
        "fit_label": labels[_candidate_id(row)],
    } for row in geometry)
    model = fit_port_obligation_role_metric(
        training_rows, selected_spec)
    external = load_confirmation_trajectories()
    scored = tuple((row, score_port_obligation_role_metric(
        model, row["transitions"])) for row in external["geometry_rows"])
    ranked = tuple(sorted(scored, key=lambda item: (
        -item[1], repr(item[0]["action_key"]))))
    frozen_order = tuple(_action_tuple(row["action_key"])
                         for row, _score in ranked)
    frozen_scores = tuple(value for _row, value in ranked)
    external_order_digest = _digest((frozen_order, frozen_scores))

    confirmation = load_confirmation_result()
    old_order = tuple(_action_tuple(action)
                      for action in confirmation["ranked_action_keys"])
    first_exact = int(confirmation["first_exact_rank"])
    known_false = set(old_order[:first_exact - 1])
    known_exact = old_order[first_exact - 1]
    new_index = {action: index + 1 for index, action in enumerate(frozen_order)}
    known_exact_rank = new_index[known_exact]
    false_ranks = tuple(sorted(new_index[action] for action in known_false))
    body = {
        "schema_version": 1,
        "development_dataset_digest": development["dataset_digest"],
        "development_geometry_digest": geometry_digest,
        "neighbor_receipt_digest_before_labels": receipt_digest,
        "candidate_spec_count": len(SPECS),
        "selected_spec_index": selected_index,
        "selected_spec": asdict(selected_spec),
        "selected_development_result": selected,
        "model_digest": model.model_digest,
        "model_separation_threshold": model.separation_threshold,
        "model_feature_count": len(model.means),
        "shuffle_trials": SHUFFLES,
        "fully_nested_shuffle_selected_specs": tuple(null_specs),
        "fully_nested_shuffle_exact_counts": tuple(null_exact),
        "shuffle_exact_median": sorted(null_exact)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_upper_tail_p": p_value,
        "shuffle_auc_median": sorted(null_auc)[SHUFFLES // 2],
        "shuffle_auc_maximum": max(null_auc),
        "shuffle_auc_upper_tail_p": (1 + sum(
            value >= selected["auc"] for value in null_auc)) /
            (SHUFFLES + 1),
        "shuffle_logloss_median": sorted(null_logloss)[SHUFFLES // 2],
        "shuffle_logloss_minimum": min(null_logloss),
        "shuffle_logloss_lower_tail_p": (1 + sum(
            value <= selected["logloss"] for value in null_logloss)) /
            (SHUFFLES + 1),
        "external_target_free_dataset_digest": external["dataset_digest"],
        "external_candidate_count": len(ranked),
        "external_ranked_action_keys": frozen_order,
        "external_ranked_scores": frozen_scores,
        "external_order_digest_before_consumed_label_join":
            external_order_digest,
        "known_exact_old_rank": first_exact,
        "known_exact_role_metric_rank": known_exact_rank,
        "known_false_role_metric_ranks": false_ranks,
        "known_exact_outranks_all_four_published_false_actions":
            known_exact_rank < min(false_ranks),
        "second_exact_action_label_remains_unopened_and_unknown": True,
        "confirmation_target_reconstructed_or_reopened": False,
        "external_labels_used_for_fit_spec_or_rank": False,
        "candidate_geometry_changed": False,
        "integrated_as_default_marking": False,
        "new_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["role_metric_diagnostic_passed"] = bool(
        selected["exact"] >= 8 and selected["sites"] >= 27 and
        p_value <= .05 and
        body["known_exact_outranks_all_four_published_false_actions"])
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("role-conditioned obligation metric diagnostic passes" if
           report["role_metric_diagnostic_passed"] else
           "role-conditioned obligation metric remains exploratory"))


if __name__ == "__main__":
    main()
