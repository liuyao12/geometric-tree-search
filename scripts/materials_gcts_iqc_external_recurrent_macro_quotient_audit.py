#!/usr/bin/env python3
"""Transfer the frozen recurrent macro quotient to wide IQC fallbacks.

The ten wide nuclei and their complete three-action graphs are unchanged.
Development capacity and every shuffled control are fitted before wide labels
are joined.  The quotient may score/admit immutable branches only; it does not
change their exact proper-SE(3) geometry, ports, or certificates.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json

from materials_gcts_iqc_exact_port_instance_dataset import (
    load_default_dataset)
from materials_gcts_iqc_external_recurrent_branch_transfer_audit import (
    evaluate as evaluate_scalar_transfer)
from materials_gcts_iqc_recurrent_macro_geometry_dataset import load_fixture
from materials_gcts_iqc_recurrent_macro_quotient import (
    ADMISSION_POSTERIOR, SHUFFLES, _rows, _score, _shuffle,
    canonical_colored_triangle, fit_macro_quotient, select_spec)


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _wide_candidates(dataset):
    rows = []
    for group in dataset["groups"]:
        group_id = int(group["group"])
        for row in group["rows"]:
            if row["certificates"]["forward"]["status"] != "unsatisfied":
                continue
            graph = row["complete_branch_action_graph"]
            semantic_geometry = canonical_colored_triangle(
                tuple(graph["node_colors"]),
                tuple(map(float, graph["pair_distances_nn"])), 0.)
            rows.append({
                "group": group_id,
                "candidate_id": _digest({
                    "group": group_id,
                    "stable_index": int(row["stable_index"]),
                    "graph": graph,
                }),
                "stable_index": int(row["stable_index"]),
                "semantic_geometry": semantic_geometry,
            })
    return tuple(sorted(rows, key=lambda row: (
        row["group"], row["candidate_id"])))


def _wide_labels(dataset):
    labels = {}
    supplied = set()
    for group in dataset["groups"]:
        group_id = int(group["group"])
        for row in group["rows"]:
            if row["certificates"]["forward"]["status"] != "unsatisfied":
                continue
            candidate_id = _digest({
                "group": group_id,
                "stable_index": int(row["stable_index"]),
                "graph": row["complete_branch_action_graph"],
            })
            labels[candidate_id] = bool(row["exact"])
            if row["exact"]:
                supplied.add(group_id)
    return labels, tuple(sorted(supplied))


def _score_semantic(model, semantic_geometry):
    key = canonical_colored_triangle(
        semantic_geometry[0], semantic_geometry[1],
        model.spec.distance_width)
    match = next((row for row in model.types
                  if row.semantic_key == key), None)
    return match.posterior if match else model.global_positive_rate


def _freeze_orders(model, candidates):
    orders = []
    for group in sorted({row["group"] for row in candidates}):
        rows = tuple(row for row in candidates if row["group"] == group)
        scored = tuple((_score_semantic(
            model, row["semantic_geometry"]), row) for row in rows)
        order = tuple(row for _score_value, row in sorted(
            scored, key=lambda item: (-item[0], item[1]["candidate_id"])))
        scores = tuple(score for score, _row in sorted(
            scored, key=lambda item: (-item[0], item[1]["candidate_id"])))
        orders.append((group, order, scores))
    return tuple(orders)


def _score_orders(orders, labels):
    selected = []
    for group, order, scores in orders:
        if order and scores[0] >= ADMISSION_POSTERIOR:
            selected.append((group, order[0], scores[0]))
    exact = sum(labels[row["candidate_id"]]
                for _group, row, _score_value in selected)
    false = len(selected) - exact
    ranks = tuple((group, next((rank for rank, row in enumerate(order, 1)
                               if labels[row["candidate_id"]]), None))
                  for group, order, _scores in orders)
    return tuple(selected), exact, false, ranks


def evaluate():
    development = load_fixture()
    development_rows = _rows(development)
    selected_development, _audits = select_spec(development_rows)
    model = fit_macro_quotient(development_rows, selected_development.spec)

    wide = load_default_dataset()
    candidates = _wide_candidates(wide)
    candidate_digest = _digest(tuple((
        row["group"], row["candidate_id"], row["semantic_geometry"])
        for row in candidates))
    orders = _freeze_orders(model, candidates)
    null_orders = []
    null_specs = []
    for trial in range(SHUFFLES):
        shuffled = _rows(development, _shuffle(development_rows, trial))
        null_selected, _null_audits = select_spec(shuffled)
        null_model = fit_macro_quotient(shuffled, null_selected.spec)
        null_specs.append(null_selected.spec)
        null_orders.append(_freeze_orders(null_model, candidates))

    order_digest = _digest(tuple((
        group, tuple(row["candidate_id"] for row in order), scores)
        for group, order, scores in orders))

    # Exact labels first enter after the real and all 31 null orders freeze.
    labels, supplied_groups = _wide_labels(wide)
    selected, exact, false, ranks = _score_orders(orders, labels)
    null_results = tuple(_score_orders(order, labels)
                         for order in null_orders)
    null_exact = tuple(result[1] for result in null_results)
    null_false = tuple(result[2] for result in null_results)
    recoverable_groups = sum(rank is not None for _group, rank in ranks)
    p_exact = (1 + sum(value >= exact for value in null_exact)) / (
        SHUFFLES + 1)
    p_false = (1 + sum(value <= false for value in null_false)) / (
        SHUFFLES + 1)
    scalar = evaluate_scalar_transfer()
    body = {
        "development_dataset_digest": development["dataset_digest"],
        "wide_dataset_digest": wide["dataset_digest"],
        "development_selected_spec": asdict(selected_development.spec),
        "development_quotient_model_digest": model.model_digest,
        "wide_candidate_count": len(candidates),
        "wide_candidate_groups": len(orders),
        "wide_supplied_groups": supplied_groups,
        "wide_recoverable_exact_groups": recoverable_groups,
        "wide_selected_groups": len(selected),
        "wide_selected_exact_groups": exact,
        "wide_selected_false_groups": false,
        "wide_exact_ranks": ranks,
        "prior_scalar_selected_exact_groups":
            scalar["wide_selected_exact_groups"],
        "prior_scalar_selected_false_groups":
            scalar["wide_selected_false_groups"],
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
        "all_null_candidate_sets_identical": True,
        "candidate_geometry_changed": False,
        "wide_labels_joined_after_all_orders_freeze": True,
        "wide_atoms_or_labels_used_for_fit_or_capacity": False,
        "raw_coordinates_ids_or_group_used_as_semantic_feature": False,
        "integrated_as_default_macro_rule": False,
        "external_macro_quotient_gate_passed": bool(
            recoverable_groups > 0 and exact == recoverable_groups and
            false == 0 and exact > scalar["wide_selected_exact_groups"] and
            p_exact <= .05 and p_false <= .05),
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["honest_status"] = (
        "recurrent macro quotient passes external wide transfer"
        if body["external_macro_quotient_gate_passed"] else
        "recurrent macro quotient remains below external wide transfer")
    body["audit_digest"] = _digest(body)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True)
          if args.json else report["honest_status"])


if __name__ == "__main__":
    main()
