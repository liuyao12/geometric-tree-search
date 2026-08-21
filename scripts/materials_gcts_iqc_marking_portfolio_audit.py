#!/usr/bin/env python3
"""Audit a two-mark IQC tree portfolio without selecting a winner.

Development labels and the already-consumed confirmation labels are joined
only after the generic portfolio has frozen its retained action IDs.  This is
a candidate-supply/rollback result: it proves that an unconfirmed rollout mark
can no longer erase the stable connection head.  It does not validate a final
value, autonomous continuation, stationarity, or exponential growth.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from materials_gcts_iqc_obligation_expanded_metric_audit import (
    MODEL_SPECS, _candidate_id, _representation_key, _score_receipt,
    freeze_geometry_receipts)
from materials_gcts_iqc_stage_local_augmented_rollout_dataset import (
    load_default_dataset)
from materials_gcts_iqc_stage_local_augmented_rollout_value_audit import (
    evaluate as rollout_audit)
from materials_gcts_iqc_stage_local_rollout_confirmation import load_receipt
from materials_gcts_marking_portfolio_tree import (
    FrozenPortfolioAction, search_marking_portfolio)


@dataclass(frozen=True)
class IQCMarkingPortfolioAudit:
    development_groups: int
    development_execution_candidates: int
    development_retained_states: int
    development_exact_supply_groups: int
    connection_exact_groups: int
    rollout_exact_groups: int
    portfolio_exact_groups: int
    portfolio_loses_an_exact_head: bool
    confirmation_candidate_count: int
    confirmation_connection_index: int
    confirmation_rollout_index: int
    confirmation_heads_differ: bool
    confirmation_retained_indices: tuple[int, ...]
    confirmation_exact_retained: int
    confirmation_inexact_retained: int
    confirmation_exact_connection_head_preserved: bool
    confirmation_target_reopened: bool
    identical_candidate_tree_for_both_markings: bool
    winner_selected: bool
    autonomous_growth_claimed: bool
    stationary_or_exponential_claimed: bool
    portfolio_supply_gate_passed: bool
    honest_status: str


def _freeze(value):
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze(item))
                            for key, item in value.items()))
    return value


def _one_level(action_ids, connection_scores, rollout_scores):
    actions = tuple(FrozenPortfolioAction(
        index, _freeze(action_id),
        (("connection", float(connection_scores[index])),
         ("rollout", float(rollout_scores[index]))))
                    for index, action_id in enumerate(action_ids))
    return search_marking_portfolio(
        "seed", expand=lambda _state: actions,
        state_key=lambda state: state,
        marking_names=("connection", "rollout"), depth=1, beam_width=2)


def evaluate() -> IQCMarkingPortfolioAudit:
    dataset = load_default_dataset()
    audit = rollout_audit()
    selected_id = audit["selected_model"]["model_id"]
    family, spec = next((family, spec)
                        for model_id, family, spec in MODEL_SPECS
                        if model_id == selected_id)
    geometry = tuple({
        "group": int(group["group"]),
        "candidate_index": int(row["candidate_index"]),
        "action_key": row["action_key"], "transitions": row["transitions"],
        "trace": row["trace"],
    } for group in dataset["groups"] for row in group["rows"])
    evaluation = tuple(row for row in geometry
                       if int(row["candidate_index"]) < 8)
    labels = {_candidate_id({
        "group": int(group["group"]),
        "candidate_index": int(row["candidate_index"])}):
        bool(row["exact"])
              for group in dataset["groups"] for row in group["rows"]}
    receipts, _digest = freeze_geometry_receipts(geometry)
    table = receipts[_representation_key(family, spec)]["receipts"]
    rollout_scores = {_candidate_id(row): _score_receipt(
        table[_candidate_id(row)],
        {key: (value, 3 if value else 0) for key, value in labels.items()},
        spec) for row in evaluation}
    supplied = connection_exact = rollout_exact = portfolio_exact = 0
    retained_total = 0
    lost = False
    for group in range(dataset["development_groups"]):
        rows = tuple(row for row in evaluation if row["group"] == group)
        actions = tuple(row["action_key"] for row in rows)
        scores = tuple(rollout_scores[_candidate_id(row)] for row in rows)
        frozen = _one_level(actions, tuple(-index for index in range(len(rows))),
                            scores)
        retained = tuple(int(node.action_path[0])
                         for node in frozen.retained)
        truths = tuple(labels[_candidate_id(row)] for row in rows)
        supplied += int(any(truths))
        connection_exact += int(truths[0])
        rollout_index = min(range(len(rows)), key=lambda index: (
            -scores[index], _candidate_id(rows[index])))
        rollout_exact += int(truths[rollout_index])
        portfolio_exact += int(any(truths[index] for index in retained))
        lost = lost or any(truths[index] for index in (0, rollout_index)) and \
            not any(truths[index] for index in retained)
        retained_total += len(retained)

    # The receipt is already consumed.  Freeze the two-mark candidate supply
    # from its pre-target trace first; join only its published block-one labels.
    receipt = load_receipt()
    trace = receipt["marked_trace"]["blocks"][0]
    action_ids = tuple(trace["candidate_action_keys"])
    scores = tuple(map(float, trace["candidate_scores"]))
    confirmation = _one_level(
        action_ids, tuple(-index for index in range(len(action_ids))), scores)
    retained = tuple(int(node.action_path[0])
                     for node in confirmation.retained)
    connection_index = int(receipt["baseline_trace"]["blocks"][0]
                           ["selected_index"])
    rollout_index = int(receipt["marked_trace"]["blocks"][0]
                        ["selected_index"])
    known = {
        connection_index: bool(receipt["baseline_score"]["blocks"][0]
                               ["exact_action"]),
        rollout_index: bool(receipt["marked_score"]["blocks"][0]
                            ["exact_action"]),
    }
    exact_retained = sum(known.get(index, False) for index in retained)
    inexact_retained = sum(index in known and not known[index]
                           for index in retained)
    passed = bool(
        portfolio_exact == supplied and not lost and
        connection_index != rollout_index and
        connection_index in retained and rollout_index in retained and
        known[connection_index] and not known[rollout_index] and
        exact_retained == 1)
    return IQCMarkingPortfolioAudit(
        dataset["development_groups"], len(evaluation), retained_total,
        supplied, connection_exact, rollout_exact, portfolio_exact, lost,
        len(action_ids), connection_index, rollout_index,
        connection_index != rollout_index, retained, exact_retained,
        inexact_retained, connection_index in retained and
        known[connection_index], False, True, False, False, False, passed,
        ("two-mark tree preserves the exact connection head for rollback"
         if passed else "two-mark portfolio supply gate remains red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
