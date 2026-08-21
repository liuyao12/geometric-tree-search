#!/usr/bin/env python3
"""Tie-robust stage-local IQC marking selection on consumed development.

The earlier selection broke exact performance ties by declaration order and
therefore chose a saturated three-neighbour depth-one score.  This audit uses
the same frozen candidates, features, labels, budgets, and shuffled controls,
but breaks equal-yield models by leave-nucleus-out positive/negative margin,
mixed-cutoff ties, and score resolution.  No confirmation data is imported.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_preregistration import SHUFFLES
from materials_gcts_iqc_stage_local_prefix_dataset import load_default_dataset
from materials_gcts_iqc_stage_local_prefix_marking_audit import (
    BEAM_BUDGETS, SPECS, VARIANTS, _baseline, _eligible, _flatten,
    _freeze_receipts, _real_labels, _row_id, _score_tables, _select_rows,
    _shuffle_labels)


EXPECTED_AUDIT_DIGEST = \
    "9f711846c532b44903e3384d9cb6f71649eefbfb36a7dbd5f696a3183af47e8c"


def _robust_objective(candidates, selected, scores, labels):
    groups = tuple(sorted({row["group"] for row in candidates}))
    viable_groups = sum(any(labels[_row_id(row)][0]
                            for row in selected.get(group, ()))
                        for group in groups)
    viable_rows = sum(labels[_row_id(row)][0]
                      for rows in selected.values() for row in rows)
    correct_sites = sum(labels[_row_id(row)][1]
                        for rows in selected.values() for row in rows)
    safe, margins, resolutions = 0, [], []
    for group in groups:
        rows = tuple(row for row in candidates if row["group"] == group)
        positives = tuple(scores[_row_id(row)] for row in rows
                          if labels[_row_id(row)][0])
        negatives = tuple(scores[_row_id(row)] for row in rows
                          if not labels[_row_id(row)][0])
        margin = (max(positives) - max(negatives)
                  if positives and negatives else 0.)
        margins.append(margin)
        chosen = selected.get(group, ())
        cutoff = scores[_row_id(chosen[-1])] if chosen else float("inf")
        tied = tuple(row for row in rows
                     if abs(scores[_row_id(row)] - cutoff) <= 1e-12)
        mixed = (any(labels[_row_id(row)][0] for row in tied) and
                 any(not labels[_row_id(row)][0] for row in tied))
        safe += not mixed
        resolutions.append(len({scores[_row_id(row)] for row in rows}))
    retained = sum(map(len, selected.values()))
    # Once a model preserves at least one viable prefix per group, prefer a
    # genuinely separating score before rewarding duplicate viable rows.  The
    # earlier declaration-order tie break did the reverse and selected a
    # saturated score even though a positive-margin model already existed.
    return (
        viable_groups, safe, min(margins, default=0.), sum(margins),
        min(resolutions, default=0), sum(resolutions),
        viable_rows, correct_sites, -retained)


def _run_budget(rows, labels, score_tables, budget):
    selected_keys, stages, specs = {}, [], []
    for depth, stage_budget in enumerate(budget, start=1):
        depth_rows = tuple(row for row in rows if row["depth"] == depth)
        candidates = _eligible(depth_rows, selected_keys, depth)
        audits = []
        for spec_index, spec in enumerate(SPECS):
            table = score_tables[(depth, spec_index)]
            scores = {_row_id(row): table[_row_id(row)] for row in candidates}
            selected = _select_rows(candidates, scores, stage_budget) \
                if candidates else {}
            audits.append((
                _robust_objective(candidates, selected, scores, labels),
                -spec_index, spec, selected))
        objective, _stable, spec, selected = max(
            audits, key=lambda item: (item[0], item[1]))
        selected_keys = {group: {
            row["action_key_frozen"] for row in group_rows}
                         for group, group_rows in selected.items()}
        specs.append(spec)
        stages.append({
            "depth": depth, "budget": stage_budget,
            "spec": asdict(spec), "eligible": len(candidates),
            "selected": sum(map(len, selected.values())),
            "viable_groups": objective[0], "tie_safe_groups": objective[1],
            "minimum_class_margin": objective[2],
            "sum_class_margin": objective[3],
            "minimum_score_resolution": objective[4],
            "sum_score_resolution": objective[5],
            "viable_rows": objective[6], "correct_sites": objective[7],
            "selected_ids": tuple(sorted(
                _row_id(row) for group in selected.values() for row in group)),
        })
    final = stages[-1]
    return {
        "budget": tuple(budget), "stages": tuple(stages),
        "chosen_specs": tuple(asdict(spec) for spec in specs),
        "exact_selected_groups": final["viable_groups"],
        "exact_selected_rows": final["viable_rows"],
        "selected_correct_sites": final["correct_sites"],
        "total_selected_prefixes": sum(stage["selected"]
                                       for stage in stages),
        "minimum_margin_across_depths": min(
            stage["minimum_class_margin"] for stage in stages),
        "tie_safe_group_depths": sum(stage["tie_safe_groups"]
                                     for stage in stages),
    }


def _select(rows, labels, receipts):
    tables = _score_tables(rows, labels, receipts)
    audits = tuple(_run_budget(rows, labels, tables, budget)
                   for budget in BEAM_BUDGETS)
    index = max(range(len(audits)), key=lambda candidate: (
        audits[candidate]["exact_selected_groups"],
        audits[candidate]["exact_selected_rows"],
        audits[candidate]["selected_correct_sites"],
        audits[candidate]["stages"][1]["viable_groups"],
        audits[candidate]["stages"][0]["viable_groups"],
        audits[candidate]["tie_safe_group_depths"],
        audits[candidate]["minimum_margin_across_depths"],
        -audits[candidate]["total_selected_prefixes"], -candidate))
    return index, audits


def evaluate():
    dataset = load_default_dataset()
    rows = _flatten(dataset)
    receipts, receipt_records, receipt_digest = _freeze_receipts(rows)
    labels = _real_labels(rows)
    selected_index, audits = _select(rows, labels, receipts)
    selected = audits[selected_index]
    baseline = _baseline(rows, labels, selected["budget"])
    nulls, null_indices = [], []
    for trial in range(SHUFFLES):
        index, results = _select(
            rows, _shuffle_labels(rows, trial), receipts)
        null_indices.append(index)
        nulls.append(results[index])
    null_groups = tuple(row["exact_selected_groups"] for row in nulls)
    null_rows = tuple(row["exact_selected_rows"] for row in nulls)
    group_p = (1 + sum(value >= selected["exact_selected_groups"]
                       for value in null_groups)) / (SHUFFLES + 1)
    row_p = (1 + sum(value >= selected["exact_selected_rows"]
                     for value in null_rows)) / (SHUFFLES + 1)
    supply = sum(any(row["viable_prefix"] for row in rows
                     if row["group"] == group and row["depth"] == 3)
                 for group in range(dataset["consumed_development_groups"]))
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["consumed_development_groups"],
        "rows_by_depth": tuple(sum(row["depth"] == depth for row in rows)
                               for depth in (1, 2, 3)),
        "exact_terminal_supply_groups": supply,
        "feature_variants": VARIANTS,
        "candidate_specs": tuple(asdict(spec) for spec in SPECS),
        "beam_budgets": BEAM_BUDGETS,
        "geometry_receipt_records": receipt_records,
        "geometry_receipt_digest_before_labels": receipt_digest,
        "selection_adds_margin_tie_and_resolution_after_exact_yield": True,
        "selected_policy_index": selected_index,
        "selected_result": selected,
        "all_budget_results": audits,
        "matched_pose_port_baseline": baseline,
        "shuffle_trials": SHUFFLES,
        "fully_reselected_shuffle_policy_indices": tuple(null_indices),
        "shuffle_exact_group_counts": null_groups,
        "shuffle_exact_row_counts": null_rows,
        "shuffle_exact_group_maximum": max(null_groups),
        "shuffle_exact_row_maximum": max(null_rows),
        "shuffle_group_upper_tail_p": group_p,
        "shuffle_row_upper_tail_p": row_p,
        "old_confirmation_imported_or_used": False,
        "targets_used_for_features_or_receipts": False,
        "candidate_geometry_changed": False,
        "consumed_development_only": True,
        "fresh_confirmation_opened": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["tie_robust_stage_local_gate_passed"] = bool(
        supply == dataset["consumed_development_groups"] and
        selected["exact_selected_groups"] >
        baseline["exact_selected_groups"] and
        selected["exact_selected_groups"] > max(null_groups) and
        selected["exact_selected_rows"] > max(null_rows) and
        group_p <= .05 and row_p <= .05 and
        selected["stages"][0]["tie_safe_groups"] ==
        dataset["consumed_development_groups"] and
        selected["stages"][0]["minimum_class_margin"] > 0.)
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    if EXPECTED_AUDIT_DIGEST and row["audit_digest"] != \
            EXPECTED_AUDIT_DIGEST:
        raise AssertionError("tie-robust stage-local audit drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          ("tie-robust stage-local marking gate passes" if
           row["tie_robust_stage_local_gate_passed"] else
           "tie-robust stage-local marking gate remains red"))


if __name__ == "__main__":
    main()
