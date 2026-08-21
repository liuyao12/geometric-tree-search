#!/usr/bin/env python3
"""Transfer the shared-schema port-incidence quotient to unchanged wide IQC.

All real and shuffled development models freeze before wide exact labels are
read.  Candidate membership is the unchanged forward-UNSAT set from the exact
port-instance audit.  Unknown recurrent types fail closed; this audit never
changes an exact candidate pose, port, or certificate.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json

from materials_gcts_iqc_exact_port_instance_dataset import (
    load_default_dataset as load_exact_port_dataset)
from materials_gcts_iqc_external_recurrent_branch_transfer_audit import (
    evaluate as evaluate_scalar_transfer)
from materials_gcts_iqc_external_recurrent_macro_quotient_audit import (
    evaluate as evaluate_geometry_transfer)
from materials_gcts_iqc_port_incidence_quotient import (
    ADMISSION_POSTERIOR, SHUFFLES, development_rows,
    fit_port_incidence_quotient, score, select_spec, shuffled_labels)
from materials_gcts_iqc_wide_port_incidence_dataset import (
    load_default_dataset as load_wide_graph_dataset)


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _candidate_rows():
    graphs = load_wide_graph_dataset()
    exact_ports = load_exact_port_dataset()
    status = {(int(group["group"]), int(row["stable_index"])):
              row["certificates"]["forward"]["status"]
              for group in exact_ports["groups"] for row in group["rows"]}
    rows = []
    for group in graphs["groups"]:
        for row in group["rows"]:
            key = (int(group["group"]), int(row["stable_index"]))
            if status[key] != "unsatisfied":
                continue
            rows.append({
                "group": key[0], "stable_index": key[1],
                "candidate_id": str(row["candidate_id"]),
                "graph": row["port_incidence_graph"],
            })
    return tuple(sorted(rows, key=lambda row: (
        row["group"], row["candidate_id"])))


def _wide_labels():
    graphs = load_wide_graph_dataset()
    exact_ports = load_exact_port_dataset()
    forward = {(int(group["group"]), int(row["stable_index"])):
               row["certificates"]["forward"]["status"]
               for group in exact_ports["groups"] for row in group["rows"]}
    labels, supplied = {}, set()
    for group in graphs["groups"]:
        for row in group["rows"]:
            key = (int(group["group"]), int(row["stable_index"]))
            if forward[key] != "unsatisfied":
                continue
            labels[str(row["candidate_id"])] = bool(row["exact"])
            if row["exact"]:
                supplied.add(key[0])
    return labels, tuple(sorted(supplied))


def _freeze_orders(model, candidates):
    result = []
    for group in sorted({row["group"] for row in candidates}):
        rows = tuple(row for row in candidates if row["group"] == group)
        scored = tuple((score(model, row["graph"]), row) for row in rows)
        known = tuple(pair for pair in scored if pair[0] is not None)
        order = tuple(row for _value, row in sorted(
            known, key=lambda pair: (-pair[0], pair[1]["candidate_id"])))
        scores = tuple(value for value, _row in sorted(
            known, key=lambda pair: (-pair[0], pair[1]["candidate_id"])))
        result.append((group, order, scores, len(rows) - len(known)))
    return tuple(result)


def _score_orders(orders, labels):
    selected = []
    for group, order, scores, _unknown in orders:
        if order and scores[0] >= ADMISSION_POSTERIOR:
            selected.append((group, order[0], scores[0]))
    exact = sum(labels[row["candidate_id"]]
                for _group, row, _value in selected)
    false = len(selected) - exact
    ranks = tuple((group, next((rank for rank, row in enumerate(order, 1)
                               if labels[row["candidate_id"]]), None))
                  for group, order, _scores, _unknown in orders)
    return tuple(selected), exact, false, ranks


def evaluate():
    development = development_rows()
    selected_development, _audits = select_spec(development)
    model = fit_port_incidence_quotient(
        development, selected_development.spec)
    candidates = _candidate_rows()
    candidate_digest = _digest(tuple((
        row["group"], row["candidate_id"],
        row["graph"]["canonical_digest"]) for row in candidates))
    orders = _freeze_orders(model, candidates)
    null_orders, null_specs, null_development = [], [], []
    for trial in range(SHUFFLES):
        labels = shuffled_labels(development, trial)
        shuffled = tuple({**row, "fit_label": bool(label)}
                         for row, label in zip(development, labels))
        selected, _null_audits = select_spec(shuffled)
        null_model = fit_port_incidence_quotient(shuffled, selected.spec)
        null_specs.append(selected.spec)
        null_development.append(selected)
        null_orders.append(_freeze_orders(null_model, candidates))
    order_digest = _digest(tuple((
        group, tuple(row["candidate_id"] for row in order), scores, unknown)
        for group, order, scores, unknown in orders))

    # Wide labels first enter after the real and every null order are frozen.
    labels, supplied = _wide_labels()
    selected, exact, false, ranks = _score_orders(orders, labels)
    null_results = tuple(_score_orders(order, labels)
                         for order in null_orders)
    null_exact = tuple(result[1] for result in null_results)
    null_false = tuple(result[2] for result in null_results)
    recoverable = sum(rank is not None for _group, rank in ranks)
    p_exact = (1 + sum(value >= exact for value in null_exact)) / (
        SHUFFLES + 1)
    p_false = (1 + sum(value <= false for value in null_false)) / (
        SHUFFLES + 1)
    development_null_exact = tuple(
        row.selected_exact_groups for row in null_development)
    development_p = (1 + sum(
        value >= selected_development.selected_exact_groups
        for value in development_null_exact)) / (SHUFFLES + 1)
    scalar = evaluate_scalar_transfer()
    geometry = evaluate_geometry_transfer()
    body = {
        "development_selected": asdict(selected_development),
        "development_model_types": len(model.types),
        "development_model_digest": model.model_digest,
        "wide_candidate_count": len(candidates),
        "wide_candidate_groups": len(orders),
        "wide_supplied_groups": supplied,
        "wide_known_candidates": sum(len(order) for _group, order,
                                     _scores, _unknown in orders),
        "wide_unknown_candidates": sum(unknown for _group, _order,
                                       _scores, unknown in orders),
        "wide_recoverable_exact_groups": recoverable,
        "wide_selected_groups": len(selected),
        "wide_selected_exact_groups": exact,
        "wide_selected_false_groups": false,
        "wide_exact_ranks_among_known": ranks,
        "prior_scalar_selected_exact_groups":
            scalar["wide_selected_exact_groups"],
        "prior_scalar_selected_false_groups":
            scalar["wide_selected_false_groups"],
        "prior_geometry_selected_exact_groups":
            geometry["wide_selected_exact_groups"],
        "prior_geometry_selected_false_groups":
            geometry["wide_selected_false_groups"],
        "candidate_digest": candidate_digest,
        "order_digest": order_digest,
        "shuffle_trials": SHUFFLES,
        "shuffle_specs": tuple(asdict(spec) for spec in null_specs),
        "development_shuffle_exact_median": sorted(
            development_null_exact)[SHUFFLES // 2],
        "development_shuffle_exact_maximum": max(development_null_exact),
        "development_exact_empirical_p": development_p,
        "shuffle_exact_median": sorted(null_exact)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_false_median": sorted(null_false)[SHUFFLES // 2],
        "shuffle_false_minimum": min(null_false),
        "exact_empirical_p": p_exact,
        "false_empirical_p": p_false,
        "all_arms_use_identical_candidates": True,
        "wide_labels_joined_after_all_orders_freeze": True,
        "wide_atoms_or_labels_used_for_fit_or_capacity": False,
        "unknown_semantic_types_fail_closed": True,
        "candidate_geometry_changed": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["external_port_incidence_gate_passed"] = bool(
        recoverable > 0 and exact == recoverable and false == 0
        and exact > max(body["prior_scalar_selected_exact_groups"],
                        body["prior_geometry_selected_exact_groups"])
        and p_exact <= .05 and p_false <= .05)
    body["audit_digest"] = _digest(body)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("port-incidence quotient passes external transfer" if
           report["external_port_incidence_gate_passed"] else
           "port-incidence quotient remains below external transfer"))


if __name__ == "__main__":
    main()
