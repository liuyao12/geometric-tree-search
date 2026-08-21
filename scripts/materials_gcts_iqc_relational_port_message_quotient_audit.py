#!/usr/bin/env python3
"""Grouped development and sealed-wide audit of a finite relational quotient.

Capacity is selected only by leave-one-development-nucleus-out replay.  Every
one of 31 within-nucleus label shuffles repeats the complete capacity selection
and fit.  The unchanged wide branch labels are joined only after the real and
all null candidate orders have frozen.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import itertools
import json
import random

from materials_gcts_iqc_external_port_incidence_quotient_audit import (
    _candidate_rows, _wide_labels)
from materials_gcts_iqc_port_incidence_metric import metric_rows
from materials_gcts_iqc_port_incidence_quotient import SHUFFLES, SHUFFLE_SEED
from materials_gcts_relational_port_message_quotient import (
    RelationalMessageSpec, fit_relational_port_quotient,
    relational_message_features, score_relational_port_quotient,
    species_palette)


FEATURE_DOMAINS = ("nodes", "edges", "all")
BIN_COUNTS = (3, 6)
MINIMUM_GROUPS = (2, 4)
TOP_TOKENS = (8, 32)
AGGREGATIONS = ("top", "logit")
ADMISSION_THRESHOLDS = (.55, .6, .65, .7, .75)
PRECISION_FLOOR = .95


@dataclass(frozen=True)
class RelationalMessageSelection:
    spec: RelationalMessageSpec
    supplied_groups: int
    selected_exact_groups: int
    selected_groups: int
    selected_precision: float
    supplied_recall: float
    correct_sites: int
    maximum_correct_sites: int


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _base_specs():
    return tuple(RelationalMessageSpec(domain, bins, minimum, 32,
                                       "top", .5)
                 for domain, bins, minimum in itertools.product(
                     FEATURE_DOMAINS, BIN_COUNTS, MINIMUM_GROUPS))


def _selection(rows, spec, ranked):
    selected = tuple(row for _group, value, row in ranked
                     if value >= spec.admission_threshold)
    groups = tuple(sorted({row["group"] for row in rows}))
    supplied = sum(any(row["exact"] for row in rows
                       if row["group"] == group) for group in groups)
    exact = sum(row["exact"] for row in selected)
    return RelationalMessageSelection(
        spec, supplied, exact, len(selected),
        exact / len(selected) if selected else 0.,
        exact / supplied if supplied else 0., 3 * exact, 3 * supplied)


def select_spec(rows):
    rows = tuple(rows)
    groups = tuple(sorted({row["group"] for row in rows}))
    palette = species_palette(row["graph"] for row in rows)
    audits = []
    for base in _base_specs():
        models = {}
        testing = {}
        for heldout in groups:
            training = tuple(row for row in rows
                             if row["group"] != heldout)
            testing[heldout] = tuple(row for row in rows
                                     if row["group"] == heldout)
            models[heldout] = fit_relational_port_quotient(
                training, base, palette=palette)
        for top_tokens, aggregation in itertools.product(
                TOP_TOKENS, AGGREGATIONS):
            scoring_spec = replace(base, top_tokens=top_tokens,
                                   aggregation=aggregation)
            ranked = []
            for heldout in groups:
                model = replace(models[heldout], spec=scoring_spec)
                order = tuple(sorted(((
                    score_relational_port_quotient(model, row["graph"]), row)
                    for row in testing[heldout]), key=lambda pair: (
                        -pair[0], pair[1]["candidate_id"])))
                ranked.append((heldout, order[0][0], order[0][1]))
            for threshold in ADMISSION_THRESHOLDS:
                spec = replace(scoring_spec,
                               admission_threshold=threshold)
                audits.append(_selection(rows, spec, ranked))
    audits = tuple(audits)
    precise = tuple(row for row in audits if row.selected_groups and
                    row.selected_precision >= PRECISION_FLOOR)
    pool = precise or audits
    domain_size = {"edges": 57, "nodes": 159, "all": 216}
    selected = max(pool, key=lambda row: (
        row.selected_exact_groups, row.correct_sites,
        row.selected_precision, -row.selected_groups,
        -domain_size[row.spec.feature_domain], -row.spec.bins,
        row.spec.minimum_groups, -row.spec.top_tokens,
        row.spec.aggregation == "top", row.spec.admission_threshold))
    return selected, audits


def _shuffle_rows(rows, trial):
    labels = [None] * len(rows)
    rng = random.Random(SHUFFLE_SEED + trial)
    for group in sorted({row["group"] for row in rows}):
        indices = [index for index, row in enumerate(rows)
                   if row["group"] == group]
        values = [rows[index]["fit_label"] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = bool(value)
    return tuple({**row, "fit_label": label}
                 for row, label in zip(rows, labels))


def _freeze_orders(model, candidates):
    result = []
    for group in sorted({row["group"] for row in candidates}):
        rows = tuple(row for row in candidates if row["group"] == group)
        ranked = tuple(sorted(((
            score_relational_port_quotient(model, row["graph"]), row)
            for row in rows), key=lambda pair: (
                -pair[0], pair[1]["candidate_id"])))
        result.append((group, tuple(row for _value, row in ranked),
                       tuple(value for value, _row in ranked)))
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


def evaluate():
    development = metric_rows()
    selected_development, audits = select_spec(development)
    palette = species_palette(row["graph"] for row in development)
    model = fit_relational_port_quotient(
        development, selected_development.spec, palette=palette)
    feature_names, _values, domains = relational_message_features(
        development[0]["graph"], palette)
    candidates = _candidate_rows()
    candidate_digest = _digest(tuple((
        row["group"], row["candidate_id"],
        row["graph"]["canonical_digest"]) for row in candidates))
    orders = _freeze_orders(model, candidates)

    null_selections, null_orders = [], []
    for trial in range(SHUFFLES):
        shuffled = _shuffle_rows(development, trial)
        selection, _null_audits = select_spec(shuffled)
        null_model = fit_relational_port_quotient(
            shuffled, selection.spec, palette=palette)
        null_selections.append(selection)
        null_orders.append(_freeze_orders(null_model, candidates))
    order_digest = _digest(tuple((
        group, tuple(row["candidate_id"] for row in order), scores)
        for group, order, scores in orders))

    # Wide labels first enter after every real/null capacity and order freezes.
    labels, supplied = _wide_labels()
    selected, exact, false, ranks = _score_orders(
        orders, labels, selected_development.spec.admission_threshold)
    null_results = tuple(_score_orders(
        order, labels, selection.spec.admission_threshold)
        for order, selection in zip(null_orders, null_selections))
    null_exact = tuple(result[1] for result in null_results)
    null_false = tuple(result[2] for result in null_results)
    development_null = tuple(row.selected_exact_groups
                             for row in null_selections)
    development_p = (1 + sum(
        value >= selected_development.selected_exact_groups
        for value in development_null)) / (SHUFFLES + 1)
    exact_p = (1 + sum(value >= exact for value in null_exact)) / (
        SHUFFLES + 1)
    false_p = (1 + sum(value <= false for value in null_false)) / (
        SHUFFLES + 1)
    body = {
        "development_rows": len(development),
        "development_groups": len({row["group"] for row in development}),
        "development_supplied_groups": selected_development.supplied_groups,
        "capacity_audits": len(audits),
        "selected_development": asdict(selected_development),
        "finite_state_count": len(model.states),
        "feature_count": len(feature_names),
        "node_feature_count": sum(domain == "nodes" for domain in domains),
        "edge_feature_count": sum(domain == "edges" for domain in domains),
        "model_digest": model.model_digest,
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
        "shuffle_exact_median": sorted(null_exact)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_false_median": sorted(null_false)[SHUFFLES // 2],
        "shuffle_false_minimum": min(null_false),
        "exact_empirical_p": exact_p,
        "false_empirical_p": false_p,
        "candidate_digest": candidate_digest,
        "order_digest": order_digest,
        "shuffle_trials": SHUFFLES,
        "all_arms_use_identical_candidates": True,
        "wide_labels_joined_after_all_orders_freeze": True,
        "wide_atoms_or_labels_used_for_fit_or_capacity": False,
        "group_balanced_state_evidence": True,
        "proper_se3_incidence_messages": True,
        "raw_ids_or_global_frame_in_state": False,
        "candidate_geometry_changed": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["finite_relational_message_gate_passed"] = bool(
        selected_development.selected_exact_groups >= 8 and
        development_p <= .05 and exact == len(supplied) and false == 0 and
        exact_p <= .05 and false_p <= .05)
    body["audit_digest"] = _digest(body)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("finite relational message quotient passes" if
           report["finite_relational_message_gate_passed"] else
           "finite relational message quotient remains below transfer gate"))


if __name__ == "__main__":
    main()
