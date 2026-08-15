#!/usr/bin/env python3
"""Cluster-placement-level overlap-consensus audit on sealed IQC crops."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import json
import math
from statistics import median

from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_iqc_overlap_consensus_marking import (
    ActionBatchScore, boundary_censored_candidates,
    calibrate_action_threshold, candidate_incidence_scores,
    candidate_subfrontier, compatible_batch, crop, frozen_frontier,
    normalized_action_scores, score_action_batch,
    shuffled_candidate_incidence)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import _site_key


@dataclass(frozen=True)
class IQCActionConsensusAudit:
    train_crop_atoms: int
    train_seed_atoms: int
    eval_crop_atoms: int
    eval_seed_atoms: int
    train_candidates_before_censor: int
    train_candidates_after_censor: int
    eval_candidates_before_censor: int
    eval_candidates_after_censor: int
    calibrated_ratio_95: float
    calibration_gate_available: bool
    train_action_batch_95: ActionBatchScore
    calibrated_ratio_99: float
    train_action_batch_99: ActionBatchScore
    eval_consensus_95: ActionBatchScore
    eval_consensus_99: ActionBatchScore
    eval_overlap_only_matched: ActionBatchScore
    eval_frequency_matched: ActionBatchScore
    shuffled_median_action_precision: float
    shuffled_median_correct_atoms: float
    shuffled_best_correct_atoms: int
    shuffled_runs: int
    empirical_shuffle_p_value: float
    empirical_shuffle_precision_p_value: float
    threshold_transferred_at_95_precision: bool
    identical_candidate_actions_all_arms: bool
    eval_outer_atoms_used_during_fit_calibration_or_enumeration: bool
    causal_superiority_gate_passed: bool
    integrated_as_default_marking: bool


def _shell_keys(species, positions, center, inner, outer):
    return {_site_key((chemical, point), .03)
            for chemical, point in zip(species, positions)
            if inner + 1e-10 < math.dist(point, center) <= outer + 1e-10}


def _apply_ratio(candidates, support, ratio, correct, shell_atoms,
                 minimum_distance):
    scores = normalized_action_scores(candidates, support)
    batch, checked, backtracks = compatible_batch(
        candidates, scores, minimum_score=ratio,
        exclusion_distance=minimum_distance * .45)
    return score_action_batch(batch, checked, backtracks, correct, shell_atoms)


def _matched_baseline(candidates, raw_scores, placements, correct, shell_atoms,
                      minimum_distance):
    batch, checked, backtracks = compatible_batch(
        candidates, raw_scores, maximum_placements=placements,
        exclusion_distance=minimum_distance * .45)
    return score_action_batch(batch, checked, backtracks, correct, shell_atoms)


def evaluate(*, shuffled_runs=31):
    raw, _ = oracle_patch_fast(10, 32.)
    train_center, eval_center = (-16., 0., 0.), (8., 14., 7.)
    train_species, train_positions, _ = crop(
        raw.species, raw.positions, train_center, 11.)
    train_seed_species, train_seed_positions, _ = crop(
        raw.species, raw.positions, train_center, 7.)
    program = compile_irregular_port_program(train_species, train_positions)
    train_frontier = frozen_frontier(
        program, train_seed_species, train_seed_positions)
    train_candidates = boundary_censored_candidates(
        train_frontier, train_center, 11.)
    train_support, _, _ = candidate_incidence_scores(train_candidates)
    train_correct = _shell_keys(
        raw.species, raw.positions, train_center, 7., 11.)
    train_shell_atoms = len(train_species) - len(train_seed_species)
    minimum_distance = program.cover.minimum_distance
    ratio95, train95, available = calibrate_action_threshold(
        train_candidates, train_support, train_correct, train_shell_atoms,
        precision_gate=.95, exclusion_distance=minimum_distance * .45)
    ratio99, train99, _ = calibrate_action_threshold(
        train_candidates, train_support, train_correct, train_shell_atoms,
        precision_gate=.99, exclusion_distance=minimum_distance * .45)

    eval_seed_species, eval_seed_positions, _ = crop(
        raw.species, raw.positions, eval_center, 7.)
    eval_frontier = frozen_frontier(
        program, eval_seed_species, eval_seed_positions)
    eval_candidates = boundary_censored_candidates(
        eval_frontier, eval_center, 11.)
    consensus, _, _ = candidate_incidence_scores(eval_candidates)
    # Outer labels first enter below; candidates and frozen ratio are sealed.
    eval_species, eval_positions, _ = crop(
        raw.species, raw.positions, eval_center, 11.)
    eval_correct = _shell_keys(
        raw.species, raw.positions, eval_center, 7., 11.)
    shell_atoms = len(eval_species) - len(eval_seed_species)
    eval_consensus = _apply_ratio(
        eval_candidates, consensus, ratio95, eval_correct, shell_atoms,
        minimum_distance)
    eval_consensus99 = _apply_ratio(
        eval_candidates, consensus, ratio99, eval_correct, shell_atoms,
        minimum_distance)
    overlap_scores = {candidate.candidate_id: candidate.overlap_atoms
                      for candidate in eval_candidates}
    frequency_scores = {candidate.candidate_id:
                        candidate.production_frequency
                        for candidate in eval_candidates}
    overlap = _matched_baseline(
        eval_candidates, overlap_scores, eval_consensus.placements,
        eval_correct, shell_atoms, minimum_distance)
    frequency = _matched_baseline(
        eval_candidates, frequency_scores, eval_consensus.placements,
        eval_correct, shell_atoms, minimum_distance)
    shuffled = []
    eval_boundary_frontier = candidate_subfrontier(
        eval_frontier, eval_candidates)
    for run in range(shuffled_runs):
        incidence, support = shuffled_candidate_incidence(
            eval_boundary_frontier, seed=16180 + run)
        maximum = max(support.values(), default=1)
        scores = {candidate.candidate_id: min(
            (support[site] / maximum
             for site in incidence[candidate.candidate_id]), default=0.)
                  for candidate in eval_candidates}
        shuffled.append(_matched_baseline(
            eval_candidates, scores, eval_consensus.placements,
            eval_correct, shell_atoms, minimum_distance))
    p_value = ((1 + sum(item.unique_correct_atoms >=
                        eval_consensus.unique_correct_atoms
                        for item in shuffled)) / (shuffled_runs + 1))
    precision_p = ((1 + sum(item.emitted_site_precision >=
                            eval_consensus.emitted_site_precision
                            for item in shuffled)) / (shuffled_runs + 1))
    superiority = (
        eval_consensus.unique_correct_atoms > overlap.unique_correct_atoms and
        eval_consensus.unique_correct_atoms > frequency.unique_correct_atoms and
        p_value <= .05 and
        (eval_consensus.action_precision >= .95 or
         eval_consensus.emitted_site_precision >= .95))
    return IQCActionConsensusAudit(
        len(train_species), len(train_seed_species),
        len(eval_species), len(eval_seed_species),
        len(train_frontier.candidates), len(train_candidates),
        len(eval_frontier.candidates), len(eval_candidates), ratio95,
        available, train95, ratio99, train99, eval_consensus,
        eval_consensus99, overlap,
        frequency, median(item.action_precision for item in shuffled),
        median(item.unique_correct_atoms for item in shuffled),
        max(item.unique_correct_atoms for item in shuffled), shuffled_runs,
        p_value, precision_p,
        (eval_consensus.action_precision >= .95 or
         eval_consensus.emitted_site_precision >= .95), True, False,
        superiority, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shuffles", type=int, default=31)
    args = parser.parse_args()
    result = evaluate(shuffled_runs=args.shuffles)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
