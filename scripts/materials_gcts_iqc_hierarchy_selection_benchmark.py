#!/usr/bin/env python3
"""Train-only beam hierarchy selection and frozen IQC transfer audit."""

from __future__ import annotations

from dataclasses import dataclass

from materials_gcts_hierarchy_selection_environment import (
    beam_select_hierarchy, greedy_select_hierarchy,
    score_frozen_hierarchy_on_heldout)
from materials_gcts_iqc_action_graph_corpus import _build_with_executions
from materials_gcts_iqc_reclustered_growth_corpus import _pack
from materials_gcts_irregular_port_atlas import compile_irregular_port_program


@dataclass(frozen=True)
class IQCHierarchySelectionBenchmark:
    greedy: object
    beam: object
    greedy_heldout: object
    beam_heldout: object
    heldout_fixture_available: bool
    beam_avoids_greedy_collapse: bool
    beam_improves_fixed_horizon_train_objective: bool
    beam_retains_more_exact_derivations: bool
    selection_target_blind: bool
    strict_stationarity_external_and_unchanged: bool


def evaluate():
    _, executions, _ = _build_with_executions()
    species, positions, _, _ = _pack(executions)
    train = compile_irregular_port_program(species, positions)
    greedy = greedy_select_hierarchy(train)
    beam = beam_select_hierarchy(train, beam_width=3)
    greedy_score = score_frozen_hierarchy_on_heldout(
        greedy, (), ())
    beam_score = score_frozen_hierarchy_on_heldout(
        beam, (), ())
    return IQCHierarchySelectionBenchmark(
        greedy, beam, greedy_score, beam_score,
        greedy_score.available and beam_score.available,
        beam.positive_levels > greedy.positive_levels,
        beam.fixed_horizon_score > greedy.fixed_horizon_score,
        any(beam_action.selected_types > greedy_action.selected_types
            for beam_action, greedy_action in zip(
                beam.actions, greedy.actions)),
        not greedy.target_used_for_selection and
        not beam.target_used_for_selection,
        greedy.strict_stationarity_gate_external and
        beam.strict_stationarity_gate_external)


if __name__ == "__main__":
    result = evaluate()
    print({
        "greedy_positive_levels": result.greedy.positive_levels,
        "beam_positive_levels": result.beam.positive_levels,
        "greedy_fixed_horizon_score": result.greedy.fixed_horizon_score,
        "beam_fixed_horizon_score": result.beam.fixed_horizon_score,
        "greedy_derivation_policies": tuple(
            action.derivation_policy for action in result.greedy.actions),
        "beam_derivation_policies": tuple(
            action.derivation_policy for action in result.beam.actions),
        "greedy_stationary": result.greedy.stationary,
        "beam_stationary": result.beam.stationary,
        "beam_avoids_greedy_collapse": result.beam_avoids_greedy_collapse,
        "beam_improves_fixed_horizon_train_objective":
            result.beam_improves_fixed_horizon_train_objective,
        "beam_retains_more_exact_derivations":
            result.beam_retains_more_exact_derivations,
        "heldout_fixture_available": result.heldout_fixture_available,
        "heldout_unavailable_reason": result.beam_heldout.unavailable_reason,
        "selection_target_blind": result.selection_target_blind,
    })
