#!/usr/bin/env python3
"""Audit the bounded local-section value on fixed IQC portfolio terminals."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures/iqc_local_section_terminal_value.json"


@dataclass(frozen=True)
class IQCLocalSectionTerminalAudit:
    groups: int
    features: int
    terminal_supply: int
    baseline_selected_exact: int
    selected_exact: int
    selected_correct: int
    gain_over_baseline: int
    joint_support_selected_exact: int
    closure_selected_folds: int
    irregular_support_types: int
    irregular_support_selected_folds: int
    irregular_selected_exact: int
    irregular_selected_correct: int
    irregular_incidence_selected_folds: int
    irregular_incidence_selected_exact: int
    irregular_incidence_selected_correct: int
    typed_port_graph_selected_folds: int
    typed_port_graph_best_inner_exact: int
    graph_kernel_selected_folds: int
    graph_kernel_best_inner_exact: int
    graph_kernel_selected_exact: int
    graph_kernel_selected_correct: int
    message_passing_selected_folds: int
    message_passing_best_inner_exact: int
    message_passing_selected_exact: int
    message_passing_selected_correct: int
    learned_message_selected_folds: int
    learned_message_best_inner_exact: int
    learned_message_standalone_exact: int
    learned_message_integrated_exact: int
    learned_message_integrated_correct: int
    learned_message_exact_shuffle_p: float
    chiral_features: int
    chirality_selected_folds: int
    chiral_selected_exact: int
    chiral_selected_correct: int
    proper_se3_invariant: bool
    lattice_coordinates_used: bool
    chirality_preserved: bool
    development_gate_passed: bool
    fresh_confirmation_authorized: bool
    target_used: bool


def evaluate(path: Path = FIXTURE) -> IQCLocalSectionTerminalAudit:
    data = json.loads(path.read_text())
    if data["format"] != "iqc-local-section-terminal-value-v1":
        raise AssertionError("unexpected local-section fixture")
    source = path.parent / data["source_fixture"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != \
            data["source_fixture_sha256"]:
        raise AssertionError("terminal-value source changed")
    schema = data["schema"]
    irregular = data["irregular_support_control"]
    incidence = irregular["pair_incidence_control"]
    typed_graph = irregular["typed_port_graph_control"]
    graph_kernel = irregular["continuous_graph_kernel_control"]
    message_passing = irregular["bounded_message_passing_control"]
    learned_message = irregular["learned_message_readout_control"]
    chiral = data["explicit_chirality_control"]
    if (data["groups"] != 20 or data["terminal_supply"] != 18
            or len(data["selected_representations"]) != 5
            or len(data["selected_neighbors"]) != 5
            or schema["features"] != 180
            or data["mixed_top_ties"] != 0):
        raise AssertionError("local-section protocol changed")
    if (graph_kernel["selected_folds"] != [1, 2]
            or len(graph_kernel["selected_capacities"]) != 5
            or len(graph_kernel["model_digests"]) != 5
            or graph_kernel["terminal_supply"] != data["terminal_supply"]
            or graph_kernel["development_gate_passed"]
            or graph_kernel["target_used_before_selection"]):
        raise AssertionError("continuous graph-kernel protocol changed")
    if (message_passing["selected_folds"]
            or message_passing["selected_depths"] != [1, 1, 1, 1, 1]
            or len(message_passing["model_digests"]) != 5
            or message_passing["terminal_supply"] != data["terminal_supply"]
            or message_passing["development_gate_passed"]
            or message_passing["target_used_before_selection"]):
        raise AssertionError("bounded message-passing protocol changed")
    if (learned_message["selected_folds"] != [1, 2]
            or learned_message["selected_depths"] != [1, 1, 1, 1, 1]
            or len(learned_message["model_digests"]) != 5
            or len(learned_message["fold_digests"]) != 5
            or learned_message["terminal_supply"] != data["terminal_supply"]
            or learned_message["development_gate_passed"]
            or learned_message["target_used_before_selection"]):
        raise AssertionError("learned message-readout protocol changed")
    target_used = bool(data["target_used_before_selection"])
    gate = data["selected_exact"] >= \
        data["development_gate"]["minimum_selected_exact"]
    return IQCLocalSectionTerminalAudit(
        data["groups"], schema["features"], data["terminal_supply"],
        data["baseline_selected_exact"], data["selected_exact"],
        data["selected_correct"],
        data["selected_exact"] - data["baseline_selected_exact"],
        data["joint_support_control"]["selected_exact"],
        data["prototype_closure_selected_folds"],
        irregular["recurrent_support_types"],
        sum("partial" in row
            for row in irregular["selected_representations"]),
        irregular["selected_exact"], irregular["selected_correct"],
        sum("incidence" in row
            for row in incidence["selected_representations"]),
        incidence["selected_exact"], incidence["selected_correct"],
        typed_graph["selected_folds"],
        max(typed_graph["inner_selected_exact"]),
        len(graph_kernel["selected_folds"]),
        max(graph_kernel["inner_selected_exact"]),
        graph_kernel["selected_exact"],
        graph_kernel["selected_correct"],
        len(message_passing["selected_folds"]),
        max(message_passing["inner_selected_exact"]),
        message_passing["selected_exact"],
        message_passing["selected_correct"],
        len(learned_message["selected_folds"]),
        max(learned_message["inner_selected_exact"]),
        learned_message["standalone_selected_exact"],
        learned_message["integrated_selected_exact"],
        learned_message["integrated_selected_correct"],
        learned_message["integrated_exact_plus_one_p"],
        chiral["features"], chiral["chirality_selected_folds"],
        chiral["selected_exact"], chiral["selected_correct"],
        schema["proper_se3_invariant"],
        schema["lattice_coordinates_used"], schema["chirality_preserved"],
        gate, gate and not target_used and
        not data["fresh_confirmation_opened"], target_used)


if __name__ == "__main__":
    print(evaluate())
