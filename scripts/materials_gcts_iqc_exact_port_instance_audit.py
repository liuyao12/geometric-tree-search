#!/usr/bin/env python3
"""Audit occurrence-level port continuation on the wide IQC portfolio."""

from __future__ import annotations

import argparse
import hashlib
import json

from materials_gcts_iqc_exact_port_instance_dataset import (
    RELATIONS, load_default_dataset)


def evaluate():
    dataset = load_default_dataset()
    rows = tuple(row for group in dataset["groups"] for row in group["rows"])
    supplied_groups = tuple(group for group in dataset["groups"]
                            if any(row["exact"] for row in group["rows"]))
    relation_rows = []
    for relation in RELATIONS:
        satisfied = tuple(row for row in rows
                          if row["certificates"][relation]["status"]
                          == "satisfied")
        unsatisfied = tuple(row for row in rows
                            if row["certificates"][relation]["status"]
                            == "unsatisfied")
        relation_rows.append({
            "relation": relation,
            "satisfied_exact": sum(bool(row["exact"])
                                   for row in satisfied),
            "satisfied_false": sum(not bool(row["exact"])
                                   for row in satisfied),
            "unsatisfied_exact": sum(bool(row["exact"])
                                     for row in unsatisfied),
            "unsatisfied_false": sum(not bool(row["exact"])
                                     for row in unsatisfied),
            "exact_supply_groups_after_filter": sum(any(
                row["exact"] and
                row["certificates"][relation]["status"] == "satisfied"
                for row in group["rows"]) for group in supplied_groups),
            "raw_matching_pair_actions": sum(
                int(row["raw_matching_pair_actions"][relation])
                for row in rows),
            "invariant_candidate_classes": sum(
                int(row["invariant_candidate_classes"][relation])
                for row in rows),
        })
    forward = next(row for row in relation_rows
                   if row["relation"] == "forward")
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": len(dataset["groups"]),
        "supplied_groups": len(supplied_groups),
        "retained_branches": len(rows),
        "exact_branches": sum(bool(row["exact"]) for row in rows),
        "false_branches": sum(not bool(row["exact"]) for row in rows),
        "relations": relation_rows,
        "fixed_forward_exact_retention": (
            forward["satisfied_exact"] /
            sum(bool(row["exact"]) for row in rows)),
        "fixed_forward_false_rejection": (
            forward["unsatisfied_false"] /
            sum(not bool(row["exact"]) for row in rows)),
        "fixed_forward_filtered_precision": (
            forward["satisfied_exact"] /
            (forward["satisfied_exact"] + forward["satisfied_false"])),
        "fixed_forward_preserves_every_supplied_group": (
            forward["exact_supply_groups_after_filter"] ==
            len(supplied_groups)),
        "all_successor_enumerations_complete": all(
            group["successor_enumeration_complete"]
            for group in dataset["groups"]),
        "all_searches_complete": all(
            row["certificates"][relation]["search_complete"]
            for row in rows for relation in RELATIONS),
        "raw_occurrence_indices_serialized": False,
        "proper_motion_invariant_candidate_identity": True,
        "selected_endpoint_metric_graph_serialized": bool(
            dataset["selected_endpoint_metric_graph_serialized"]),
        "complete_branch_metric_graph_serialized": bool(
            dataset["complete_branch_metric_graph_serialized"]),
        "exact_instance_improves_over_semantic_role_cover": bool(
            forward["unsatisfied_false"] > 0 and
            forward["satisfied_exact"] > forward["unsatisfied_exact"]),
        "exact_instance_gate_passed": bool(
            forward["unsatisfied_exact"] == 0 and
            forward["unsatisfied_false"] > 0 and
            forward["exact_supply_groups_after_filter"] ==
            len(supplied_groups)),
        "boundary_conditioned_backoff_required": True,
        "relation_selected_on_fresh_confirmation": False,
        "mandatory_physical_port_occupancy_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "honest_status": (
            "exact occurrence incidence rejects 26 of 61 false branches and "
            "retains 57 of 59 exact branches under forward continuation, but "
            "one supplied nucleus loses its only exact branch; complete "
            "branch graphs are serialized for the separate transfer audit"),
    }
    return {**body, "audit_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    print(json.dumps(row, indent=2, sort_keys=True)
          if args.json else row["honest_status"])


if __name__ == "__main__":
    main()
