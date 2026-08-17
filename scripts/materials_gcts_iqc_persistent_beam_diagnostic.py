#!/usr/bin/env python3
"""Diagnose a persistent multi-depth beam on the completed fourth IQC nucleus."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment import score_frontier_attachments
from materials_gcts_frontier_attachment_benchmark import score_regenerative_growth
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    CONFIRMATION_CENTER, _bounded_proposals, fit_multinucleus_marking)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_persistent_frontier_beam import (
    run_persistent_frontier_beam)


@dataclass(frozen=True)
class PersistentBeamDiagnostic:
    evaluation_center: tuple[float, float, float]
    robust_leave_one_nucleus_out_marking: bool
    lookahead_depth: int
    beam_width: int
    branching_width: int
    requested_waves: int
    executed_waves: int
    seed_atoms: int
    target_atoms: int
    first_candidate_true_sites: tuple[int, ...]
    first_candidate_false_sites: tuple[int, ...]
    first_candidate_value_scores: tuple[float, ...]
    selected_path_ranks: tuple[int, ...]
    wave_selected_paths: tuple[tuple[int, ...], ...]
    wave_candidate_true_sites: tuple[tuple[int, ...], ...]
    wave_candidate_false_sites: tuple[tuple[int, ...], ...]
    wave_true_sites: tuple[int, ...]
    wave_false_sites: tuple[int, ...]
    evaluated_branches: int
    terminal_frontier_candidates: int
    emitted_sites: int
    correct_sites: int
    false_sites: int
    target_materialized_after_execution: bool
    target_used_for_selection: bool
    exact_first_action_recovered: bool
    all_executed_actions_exact: bool
    confirmatory_status: str


def evaluate(*, lookahead_depth=3, beam_width=4, branching_width=4,
             robust_marking=False, evaluation_center=CONFIRMATION_CENTER,
             root_rank_values=None, waves=1, candidate_snapshot_width=None,
             root_rank_values_by_previous=None):
    center = tuple(float(value) for value in evaluation_center)
    (prototypes, connection, training_seeds, training_targets,
     _training_proposals, marker, refinement, robust_marker,
     robust_refinement) = fit_multinucleus_marking()
    if robust_marking:
        marker, refinement = robust_marker, robust_refinement
    seed = _seed_crop(center)
    proposals = _bounded_proposals(
        connection, prototypes, seed, center)
    scores = score_frontier_attachments(
        marker, proposals, seed.positions, seed.species)
    learned_factor = sum(len(target.positions) / len(train.positions)
                         for train, target in zip(
                             training_seeds, training_targets)) / len(
                                 training_seeds)
    predicted_novel = max(1, round(len(seed.positions) * learned_factor) -
                          len(seed.positions))
    pool = min(len(scores), 2 * predicted_novel)
    execution = run_persistent_frontier_beam(
        marker, refinement, connection, proposals,
        seed.positions, seed.species, CLUSTER_EDGES, pool,
        center, EVALUATION_TARGET_RADIUS, waves=waves,
        beam_width=beam_width, branching_width=branching_width,
        lookahead_depth=lookahead_depth, root_rank_values=root_rank_values,
        candidate_snapshot_width=candidate_snapshot_width,
        root_rank_values_by_previous=root_rank_values_by_previous)

    # This nucleus has already completed its confirmation role; truth is still
    # attached only after the new persistent-beam decision is immutable.
    target = _open_target(center)
    scored = score_regenerative_growth(
        execution.records, execution.traces, seed.positions,
        target.positions, target.species)
    colors = {tuple(round(value, 6) for value in point): species
              for point, species in zip(target.positions, target.species)}
    candidate_truth = tuple(tuple(sum(
        colors.get(tuple(round(value, 6) for value in point)) == species
        for point, species in zip(points, species_values))
        for points, species_values in zip(
            decision.first_candidate_positions,
            decision.first_candidate_species))
        for decision in execution.decisions)
    candidate_falsehood = tuple(tuple(total - true
        for total, true in zip(decision.first_candidate_sites, truths))
        for decision, truths in zip(execution.decisions, candidate_truth))
    first = execution.decisions[0]
    candidate_true = candidate_truth[0]
    candidate_false = candidate_falsehood[0]
    correct = sum(row.true_sites for row in scored)
    false = sum(row.false_sites for row in scored)
    emitted = correct + false
    recovered = bool(scored and scored[0].true_sites > 0 and
                     scored[0].false_sites == 0)
    all_exact = emitted > 0 and false == 0
    return PersistentBeamDiagnostic(
        center, robust_marking, lookahead_depth, beam_width, branching_width,
        waves, len(execution.records),
        len(seed.positions), len(target.positions), candidate_true,
        candidate_false, first.first_candidate_value_scores,
        first.selected_path_ranks,
        tuple(item.selected_path_ranks for item in execution.decisions),
        candidate_truth, candidate_falsehood,
        tuple(item.true_sites for item in scored),
        tuple(item.false_sites for item in scored),
        first.evaluated_branches, first.terminal_frontier_candidates,
        emitted, correct, false, True,
        execution.target_used_for_selection, recovered, all_exact,
        ("exploratory persistent beam recovers the exact first action"
         if recovered else "persistent beam remains red on the diagnostic"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--beam-width", type=int, default=4)
    parser.add_argument("--branching-width", type=int, default=4)
    parser.add_argument("--robust-marking", action="store_true")
    parser.add_argument("--center", type=float, nargs=3,
                        default=CONFIRMATION_CENTER)
    parser.add_argument("--waves", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate(lookahead_depth=args.depth,
                      beam_width=args.beam_width,
                      branching_width=args.branching_width,
                      robust_marking=args.robust_marking,
                      evaluation_center=args.center, waves=args.waves)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
