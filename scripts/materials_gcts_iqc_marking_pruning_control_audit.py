#!/usr/bin/env python3
"""Audit rejected pruning changes around the fixed-width IQC portfolio."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures/iqc_marking_pruning_controls.json"


@dataclass(frozen=True)
class IQCMarkingPruningControlReport:
    groups: int
    beam: tuple[int, ...]
    baseline_selected_exact: int
    baseline_terminal_supply: int
    reach12_root_supply: int
    reach12_terminal_supply: int
    reach12_selected_exact: int
    stage_value_selected_exact: int
    stage_value_terminal_supply: int
    descendant_viability_selected_exact: int
    descendant_viability_terminal_supply: int
    lookahead_terminal_supply: int
    lookahead_selected_exact: int
    lookahead_proposal_checks: int
    pose_edge_selected_exact: int
    pose_edge_selected_correct: int
    pose_edge_representation_selected_folds: int
    action_consensus_selected_exact: int
    action_consensus_selected_correct: int
    multiplicity_selected_exact: int
    multiplicity_selected_correct: int
    multiplicity_score_selected_exact: int
    groups_where_exact_and_false_have_full_order_support: int
    controls_improve_baseline: bool
    development_gate_passed: bool
    fresh_confirmation_authorized: bool
    target_used: bool


def evaluate(path: Path = FIXTURE) -> IQCMarkingPruningControlReport:
    data = json.loads(path.read_text())
    if data["format"] != "iqc-marking-pruning-controls-v1":
        raise AssertionError("unexpected pruning-control fixture")
    source = path.parent / data["source_fixture"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != \
            data["source_fixture_sha256"]:
        raise AssertionError("portfolio terminal source changed")
    groups = int(data["groups"])
    baseline = data["portfolio_terminal_baseline"]
    reach = data["root_reach_control"]["results"]["12"]
    stage = data["independent_stage_value_control"]["summary"]
    viability = data["descendant_viability_control"]["summary"]
    lookahead = data["broad_terminal_lookahead_control"]
    pose_edge = data["pose_edge_lookahead_control"]
    consensus = data["action_consensus_lookahead_control"]
    multiplicity = data["commuting_order_multiplicity_control"]
    if (tuple(data["beam"]) != (4, 4, 8) or groups != 20 or
            any(len(row) != 3 for row in
                data["independent_stage_value_control"]["selected_heads"]) or
            any(len(row) != 3 for row in
                data["descendant_viability_control"]["selected_heads"])):
        raise AssertionError("pruning-control protocol changed")
    target_used = any((
        data["target_used"], data["root_reach_control"]["target_used"],
        data["independent_stage_value_control"]["target_used"],
        data["descendant_viability_control"]["target_used"],
        data["broad_terminal_lookahead_control"]
            ["target_used_before_selection"],
        data["pose_edge_lookahead_control"]
            ["target_used_before_selection"],
        data["action_consensus_lookahead_control"]
            ["target_used_before_selection"],
        data["commuting_order_multiplicity_control"]
            ["target_used_before_selection"]))
    controls_improve = max(
        reach["selected_exact"], stage["selected_exact"],
        viability["selected_exact"],
        lookahead["selected_exact"],
        pose_edge["selected_exact"],
        consensus["selected_exact"],
        multiplicity["rankings"]["multiplicity_then_score"]
            ["selected_exact"],
        multiplicity["rankings"]["score_plus_0.1_log_multiplicity"]
            ["selected_exact"]) > baseline["selected_exact"]
    gate = int(data["development_gate"]["minimum_selected_exact"])
    passed = max(baseline["selected_exact"], reach["selected_exact"],
                 stage["selected_exact"],
                 viability["selected_exact"],
                 lookahead["selected_exact"],
                 pose_edge["selected_exact"],
                 consensus["selected_exact"],
                 multiplicity["rankings"]["multiplicity_then_score"]
                     ["selected_exact"],
                 multiplicity["rankings"]
                     ["score_plus_0.1_log_multiplicity"]
                     ["selected_exact"]) >= gate
    return IQCMarkingPruningControlReport(
        groups, tuple(data["beam"]), baseline["selected_exact"],
        baseline["terminal_supply"], reach["stage_supply"][0],
        reach["terminal_supply"], reach["selected_exact"],
        stage["selected_exact"], stage["terminal_supply"],
        viability["selected_exact"], viability["terminal_supply"],
        lookahead["terminal_supply"], lookahead["selected_exact"],
        lookahead["proposal_checks"],
        pose_edge["selected_exact"], pose_edge["selected_correct"],
        pose_edge["edge_representation_selected_folds"],
        consensus["selected_exact"], consensus["selected_correct"],
        multiplicity["rankings"]["multiplicity_then_score"]
            ["selected_exact"],
        multiplicity["rankings"]["multiplicity_then_score"]
            ["selected_correct"],
        multiplicity["rankings"]["score_plus_0.1_log_multiplicity"]
            ["selected_exact"],
        multiplicity["groups_where_exact_and_false_both_have_six"],
        controls_improve, passed, passed and not target_used, target_used)


if __name__ == "__main__":
    print(evaluate())
