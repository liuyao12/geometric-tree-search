#!/usr/bin/env python3
"""Posthoc, target-file-only diagnosis of the valid second fresh result."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

from materials_gcts_iqc_parent_balanced_confirmation_preregistration_v2 import \
    canonical_json
from materials_gcts_iqc_parent_balanced_confirmation_v2 import \
    load_default_result


def evaluate():
    row = load_default_result()
    parents = defaultdict(list)
    for candidate, labels, terminal in zip(
            row["receipt"]["candidates"], row["candidate_action_labels"],
            row["candidate_terminal_labels"]):
        parents[int(candidate["parent_lineage_index"])].append(
            (tuple(labels), tuple(terminal)))
    parent_best = {parent: max(sum(labels) for labels, _terminal in rows)
                   for parent, rows in parents.items()}
    exact_first_nine = {parent for parent, rows in parents.items()
                        if any(all(labels[:9]) for labels, _ in rows)}
    exact_terminal = {parent for parent, rows in parents.items()
                      if any(all(terminal) for _labels, terminal in rows)}
    body = {
        "schema_version": 1,
        "source_result_digest": row["result_digest"],
        "source_receipt_digest": row["receipt_digest"],
        "source_target_site_digest": row["target_site_digest"],
        "raw_complete_nine_action_lineages":
            row["complete_nine_action_lineages"],
        "retained_nine_action_parents": len(parents),
        "retained_fourth_candidates": row["fourth_candidates_retained"],
        "retained_parent_best_correct_action_histogram": tuple(sorted(
            Counter(parent_best.values()).items())),
        "retained_candidates_first_nine_correct_histogram": tuple(sorted(
            Counter(sum(labels[:9])
                    for labels in row["candidate_action_labels"]).items())),
        "retained_candidates_terminal_correct_histogram": tuple(sorted(
            Counter(sum(labels)
                    for labels in row["candidate_terminal_labels"]).items())),
        "exact_first_nine_parent_count": len(exact_first_nine),
        "exact_terminal_parent_count": len(exact_terminal),
        "exact_terminal_parent_indices": tuple(sorted(exact_terminal)),
        "best_complete_correct_actions": row["best_correct_actions"],
        "unretained_nine_action_geometry_serialized": False,
        "can_distinguish_raw_supply_failure_from_selector_loss": False,
        "failure_boundary":
            "at or before the nine-action parent-balanced selection",
        "fourth_block_exact_terminal_supply_present": bool(exact_terminal),
        "target_reopened_or_execution_repeated": False,
        "scientific_gate_passed": False,
        "next_required_instrumentation": (
            "serialize every raw nine-action lineage before target",
            "record per-stage execution timings",
            "cache shared fourth-frontier prefixes",
        ),
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["retained_nine_action_parents"] != 64 or
            body["exact_first_nine_parent_count"] != 0 or
            body["exact_terminal_parent_count"] != 8 or
            body["best_complete_correct_actions"] != 11 or
            body["unretained_nine_action_geometry_serialized"] or
            body["can_distinguish_raw_supply_failure_from_selector_loss"] or
            not body["fourth_block_exact_terminal_supply_present"] or
            body["target_reopened_or_execution_repeated"] or
            body["scientific_gate_passed"]):
        raise AssertionError("second fresh failure diagnosis drift")
    return row


if __name__ == "__main__":
    print(json.dumps(validate_result(evaluate()), indent=2, sort_keys=True))
