#!/usr/bin/env python3
"""Reproduce the group-heldout IQC on-policy branch aggregation audit.

The expensive geometric rollouts are frozen as target-free branch examples
and closed-loop traces.  This audit refits every fold from the invariant rows,
checks their hashes, and separates path supply from value-model selection.
It is development cross-validation, not a fresh autonomous confirmation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_on_policy_branch_aggregation import (
    branch_examples_digest, fit_group_sealed_on_policy_values)
from materials_gcts_recurrent_branch_value_heads import DepthBranchExample


FIXTURE = Path(__file__).parent / "fixtures/iqc_on_policy_branch_aggregation.json"


@dataclass(frozen=True)
class IQCOnPolicyAggregationReport:
    groups: int
    folds: int
    on_policy_examples: int
    positive_on_policy_examples: int
    conflicting_descriptor_groups: int
    initial_terminal_supply: int
    initial_selected_exact: int
    initial_selected_correct_sites: int
    aggregated_terminal_supply: int
    aggregated_selected_exact: int
    aggregated_selected_correct_sites: int
    aggregated_stage_supply: tuple[int, ...]
    exact_path_supply_failures: int
    supplied_but_misranked: int
    terminal_supply_fraction: float
    selected_exact_fraction: float
    improvement_over_initial: int
    terminal_supply_gate_passed: bool
    selected_exact_gate_passed: bool
    improvement_gate_passed: bool
    development_gate_passed: bool
    fresh_confirmation_authorized: bool
    on_policy_corpus_digest: str
    closed_loop_candidate_digest: str
    target_used: bool


def _rows(raw) -> tuple[DepthBranchExample, ...]:
    return tuple(DepthBranchExample(
        row["group"], int(row["depth"]), tuple(row["features"]),
        tuple(row["action_colors"]), bool(row["successful"])) for row in raw)


def evaluate(path: Path = FIXTURE) -> IQCOnPolicyAggregationReport:
    data = json.loads(path.read_text())
    if data["format"] != "iqc-on-policy-branch-aggregation-v1":
        raise AssertionError("unexpected on-policy fixture format")
    base = path.parent / data["base_fixture"]
    if hashlib.sha256(base.read_bytes()).hexdigest() != \
            data["base_fixture_sha256"]:
        raise AssertionError("broad branch fixture changed")
    base_data = json.loads(base.read_text())
    broad = _rows(base_data["examples"])
    digest_parts = []
    on_policy_count = positive_count = conflict_count = 0
    for fold in data["folds"]:
        rows = _rows(fold["on_policy_examples"])
        digest = branch_examples_digest(rows)
        if digest != fold["on_policy_example_digest"]:
            raise AssertionError("on-policy branch rows changed")
        digest_parts.append(digest)
        _model, audit = fit_group_sealed_on_policy_values(
            broad, rows, heldout_groups=tuple(fold["heldout_groups"]),
            feature_names=data["feature_names"],
            color_keys=data["color_keys"],
            neighbors_by_depth=tuple(map(tuple, data["neighbors_by_depth"])),
            beta_prior=float(data["beta_prior"]))
        if (audit.training_example_digest !=
                fold["expected_training_example_digest"] or
                audit.model_digest != fold["expected_model_digest"] or
                audit.merged_examples != fold["expected_merged_examples"] or
                audit.conflicting_descriptor_groups !=
                fold["expected_conflicting_descriptor_groups"] or
                audit.heldout_seen_during_fit or audit.target_used):
            raise AssertionError("group-sealed fold does not reproduce")
        on_policy_count += len(rows)
        positive_count += sum(row.successful for row in rows)
        conflict_count += audit.conflicting_descriptor_groups
    corpus_digest = hashlib.sha256(
        repr(tuple(digest_parts)).encode()).hexdigest()
    if corpus_digest != data["on_policy_corpus_digest"]:
        raise AssertionError("combined on-policy corpus changed")

    closed = data["closed_loop"]
    initial = closed["initial"]
    aggregated = closed["aggregated"]
    groups = int(aggregated["groups"])
    if groups != initial["groups"] or groups != sum(
            len(fold["heldout_groups"]) for fold in data["folds"]):
        raise AssertionError("closed-loop group accounting changed")
    terminal_supply = int(aggregated["terminal_supply"])
    selected = int(aggregated["selected_exact"])
    supply_fraction = terminal_supply / groups
    selected_fraction = selected / groups
    gate = data["scientific_gate"]
    supply_gate = supply_fraction >= gate["minimum_terminal_supply_fraction"]
    selected_gate = selected_fraction >= gate["minimum_selected_exact_fraction"]
    improvement = selected - int(initial["selected_exact"])
    improvement_gate = (not gate["require_improvement_over_initial"] or
                        improvement > 0)
    development_gate = supply_gate and selected_gate and improvement_gate
    return IQCOnPolicyAggregationReport(
        groups=groups,
        folds=len(data["folds"]),
        on_policy_examples=on_policy_count,
        positive_on_policy_examples=positive_count,
        conflicting_descriptor_groups=conflict_count,
        initial_terminal_supply=int(initial["terminal_supply"]),
        initial_selected_exact=int(initial["selected_exact"]),
        initial_selected_correct_sites=int(initial["selected_correct_sites"]),
        aggregated_terminal_supply=terminal_supply,
        aggregated_selected_exact=selected,
        aggregated_selected_correct_sites=int(
            aggregated["selected_correct_sites"]),
        aggregated_stage_supply=tuple(aggregated["stage_supply"]),
        exact_path_supply_failures=groups - terminal_supply,
        supplied_but_misranked=terminal_supply - selected,
        terminal_supply_fraction=supply_fraction,
        selected_exact_fraction=selected_fraction,
        improvement_over_initial=improvement,
        terminal_supply_gate_passed=supply_gate,
        selected_exact_gate_passed=selected_gate,
        improvement_gate_passed=improvement_gate,
        development_gate_passed=development_gate,
        # A new one-shot target is opened only after the full development gate.
        fresh_confirmation_authorized=development_gate,
        on_policy_corpus_digest=corpus_digest,
        closed_loop_candidate_digest=closed["candidate_digest"],
        target_used=False)


if __name__ == "__main__":
    print(evaluate())
