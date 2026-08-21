#!/usr/bin/env python3
"""Sealed wide transfer of the continuous shared port-incidence metric."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import random

from materials_gcts_iqc_external_port_incidence_quotient_audit import (
    _candidate_rows, _wide_labels)
from materials_gcts_iqc_port_incidence_metric import (
    graph_features, fit_metric, metric_rows, score, select_spec)
from materials_gcts_iqc_port_incidence_quotient import SHUFFLES, SHUFFLE_SEED


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _wide_metric_rows():
    rows = []
    for row in _candidate_rows():
        names, features, ranges = graph_features(row["graph"])
        rows.append({**row, "feature_names": names, "features": features,
                     "feature_ranges": ranges})
    return tuple(rows)


def _freeze_orders(model, candidates):
    result = []
    for group in sorted({row["group"] for row in candidates}):
        rows = tuple(row for row in candidates if row["group"] == group)
        scored = tuple((score(model, row), row) for row in rows)
        ordered = tuple(sorted(scored, key=lambda pair: (
            -pair[0], pair[1]["candidate_id"])))
        result.append((group, tuple(row for _value, row in ordered),
                       tuple(value for value, _row in ordered)))
    return tuple(result)


def _score_orders(orders, labels, threshold):
    selected = []
    for group, order, scores in orders:
        if order and scores[0] >= threshold:
            selected.append((group, order[0], scores[0]))
    exact = sum(labels[row["candidate_id"]]
                for _group, row, _value in selected)
    false = len(selected) - exact
    ranks = tuple((group, next((rank for rank, row in enumerate(order, 1)
                               if labels[row["candidate_id"]]), None))
                  for group, order, _scores in orders)
    return tuple(selected), exact, false, ranks


def _shuffle_labels(rows, trial):
    labels = [None] * len(rows)
    rng = random.Random(SHUFFLE_SEED + trial)
    for group in sorted({row["group"] for row in rows}):
        indices = [index for index, row in enumerate(rows)
                   if row["group"] == group]
        values = [rows[index]["fit_label"] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(labels)


def evaluate():
    development = metric_rows()
    selected_development, _audits = select_spec(development)
    model = fit_metric(development, selected_development.spec)
    candidates = _wide_metric_rows()
    candidate_digest = _digest(tuple((
        row["group"], row["candidate_id"],
        row["graph"]["canonical_digest"]) for row in candidates))
    orders = _freeze_orders(model, candidates)
    null_orders, null_specs, null_development = [], [], []
    for trial in range(SHUFFLES):
        labels = _shuffle_labels(development, trial)
        shuffled = tuple({**row, "fit_label": bool(label)}
                         for row, label in zip(development, labels))
        selected, _ = select_spec(shuffled)
        null_model = fit_metric(shuffled, selected.spec)
        null_development.append(selected)
        null_specs.append(selected.spec)
        null_orders.append(_freeze_orders(null_model, candidates))
    order_digest = _digest(tuple((
        group, tuple(row["candidate_id"] for row in order), scores)
        for group, order, scores in orders))

    # Labels first enter after real and all 31 null orders freeze.
    labels, supplied = _wide_labels()
    selected, exact, false, ranks = _score_orders(
        orders, labels, selected_development.spec.admission_threshold)
    null_results = tuple(_score_orders(
        order, labels, spec.admission_threshold)
        for order, spec in zip(null_orders, null_specs))
    null_exact = tuple(result[1] for result in null_results)
    null_false = tuple(result[2] for result in null_results)
    p_exact = (1 + sum(value >= exact for value in null_exact)) / (
        SHUFFLES + 1)
    p_false = (1 + sum(value <= false for value in null_false)) / (
        SHUFFLES + 1)
    development_null = tuple(row.selected_exact_groups
                             for row in null_development)
    development_p = (1 + sum(
        value >= selected_development.selected_exact_groups
        for value in development_null)) / (SHUFFLES + 1)
    body = {
        "development_selected": asdict(selected_development),
        "development_model_digest": model.model_digest,
        "development_shuffle_exact_median": sorted(
            development_null)[SHUFFLES // 2],
        "development_shuffle_exact_maximum": max(development_null),
        "development_exact_empirical_p": development_p,
        "wide_candidate_count": len(candidates),
        "wide_candidate_groups": len(orders),
        "wide_supplied_groups": supplied,
        "wide_selected_groups": len(selected),
        "wide_selected_exact_groups": exact,
        "wide_selected_false_groups": false,
        "wide_exact_ranks": ranks,
        "candidate_digest": candidate_digest,
        "order_digest": order_digest,
        "shuffle_trials": SHUFFLES,
        "shuffle_specs": tuple(asdict(spec) for spec in null_specs),
        "shuffle_exact_median": sorted(null_exact)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_false_median": sorted(null_false)[SHUFFLES // 2],
        "shuffle_false_minimum": min(null_false),
        "exact_empirical_p": p_exact,
        "false_empirical_p": p_false,
        "all_arms_use_identical_candidates": True,
        "wide_labels_joined_after_all_orders_freeze": True,
        "wide_atoms_or_labels_used_for_fit_or_capacity": False,
        "candidate_geometry_changed": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["external_port_metric_gate_passed"] = bool(
        exact == len(supplied) and false == 0 and p_exact <= .05
        and p_false <= .05)
    body["audit_digest"] = _digest(body)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("port-incidence metric passes external transfer" if
           report["external_port_metric_gate_passed"] else
           "port-incidence metric remains below external transfer"))


if __name__ == "__main__":
    main()
