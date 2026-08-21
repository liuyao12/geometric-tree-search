#!/usr/bin/env python3
"""Audit exhaustive simultaneous semantic-port cover on the wide IQC set."""

from __future__ import annotations

import argparse
import hashlib
import json

from materials_gcts_iqc_simultaneous_port_cover_dataset import (
    EXPECTED_DATASET_DIGEST, load_default_dataset)


def evaluate():
    dataset = load_default_dataset()
    rows = tuple(row for group in dataset["groups"] for row in group["rows"])
    statuses = {name: tuple(
        row for row in rows if row["certificate"]["status"] == name)
        for name in ("satisfied", "unsatisfied", "unknown")}
    rejected = statuses["unsatisfied"]
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": len(dataset["groups"]),
        "retained_branches": len(rows),
        "exact_branches": sum(bool(row["exact"]) for row in rows),
        "false_branches": sum(not bool(row["exact"]) for row in rows),
        "satisfied_branches": len(statuses["satisfied"]),
        "unsatisfied_branches": len(rejected),
        "unknown_branches": len(statuses["unknown"]),
        "rejected_exact_branches": sum(bool(row["exact"])
                                       for row in rejected),
        "rejected_false_branches": sum(not bool(row["exact"])
                                       for row in rejected),
        "branches_with_no_persisting_role": sum(
            int(row["persisting_selected_role_identities"]) == 0
            for row in rows),
        "branches_with_persisting_role": sum(
            int(row["persisting_selected_role_identities"]) > 0
            for row in rows),
        "maximum_distinct_persisting_roles": max(
            int(row["persisting_selected_role_identities"])
            for row in rows),
        "role_relevant_successor_actions": sum(
            int(row["role_relevant_successor_actions"]) for row in rows),
        "maximum_role_relevant_actions_per_branch": max(
            int(row["role_relevant_successor_actions"]) for row in rows),
        "pair_conflicts": sum(int(row["pair_conflicts"]) for row in rows),
        "search_nodes": sum(int(row["certificate"]["explored_nodes"])
                            for row in rows),
        "all_successor_enumerations_complete": all(
            group["successor_enumeration_complete"]
            for group in dataset["groups"]),
        "all_searches_complete": all(
            row["certificate"]["search_complete"] for row in rows),
        "all_candidate_geometry_target_blind": all(
            not group["target_used_for_candidates_or_certificates"]
            for group in dataset["groups"]),
        "semantic_role_cover_rejects_any_false_branch": any(
            not bool(row["exact"]) for row in rejected),
        "simultaneous_semantic_role_gate_passed": bool(
            rejected and not any(bool(row["exact"]) for row in rejected)),
        "exact_port_instance_certificate_required": True,
        "physical_valence_or_mandatory_occupancy_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "honest_status": (
            "exhaustive simultaneous search is operational, but the semantic "
            "role quotient accepts every exact and false branch; retain exact "
            "finite port-instance incidence before the next search"),
    }
    return {**body, "audit_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    if args.json:
        print(json.dumps(row, indent=2, sort_keys=True))
    else:
        print(row["honest_status"])


if __name__ == "__main__":
    main()
