#!/usr/bin/env python3
"""Sealed train/eval audit of primitive IQC overlap-consensus marking."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from statistics import median

from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_iqc_overlap_consensus_marking import (
    RankedSiteScore, choose_consensus_threshold, crop, frozen_frontier,
    incidence_scores, score_selected, shuffled_incidence_consensus,
    threshold_selection, top_k_selection)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import _site_key


@dataclass(frozen=True)
class IQCOverlapConsensusAudit:
    train_crop_atoms: int
    train_seed_atoms: int
    train_shell_atoms: int
    eval_crop_atoms: int
    eval_seed_atoms: int
    eval_shell_atoms: int
    train_eval_crop_domain_ids_disjoint: bool
    frozen_prototypes: int
    frozen_ports: int
    train_seed_occurrences: int
    eval_seed_occurrences: int
    train_candidates: int
    eval_candidates: int
    train_candidate_digest: str
    eval_candidate_digest: str
    calibrated_threshold: int
    train_precision_gate_available: bool
    train_consensus: RankedSiteScore
    eval_consensus: RankedSiteScore
    eval_overlap_only: RankedSiteScore
    eval_production_frequency: RankedSiteScore
    shuffled_median_precision: float
    shuffled_median_correct: float
    shuffled_best_correct: int
    shuffled_runs: int
    empirical_shuffle_p_value: float
    identical_eval_candidates_all_arms: bool
    eval_target_used_during_fit_calibration_or_candidate_enumeration: bool
    oracle_family_phi_cell_used_by_learner: bool
    threshold_transferred_at_99_precision: bool
    causal_superiority_gate_passed: bool
    integrated_as_default_marking: bool


def _shell_keys(species, positions, center, inner, outer):
    return {_site_key((chemical, point), .03)
            for chemical, point in zip(species, positions)
            if inner + 1e-10 < math.dist(point, center) <= outer + 1e-10}


def evaluate(*, shuffled_runs: int = 31) -> IQCOverlapConsensusAudit:
    if shuffled_runs < 3:
        raise ValueError("at least three shuffles are required")
    raw, _oracle_metadata = oracle_patch_fast(10, 32.0)
    train_center = (-16., 0., 0.)
    eval_center = (8., 14., 7.)
    train_species, train_positions, train_ids = crop(
        raw.species, raw.positions, train_center, 11.)
    train_seed_species, train_seed_positions, _ = crop(
        raw.species, raw.positions, train_center, 7.)
    program = compile_irregular_port_program(train_species, train_positions)
    train_frontier = frozen_frontier(
        program, train_seed_species, train_seed_positions)
    train_correct = _shell_keys(
        raw.species, raw.positions, train_center, 7., 11.)
    threshold, available = choose_consensus_threshold(
        train_frontier, train_correct)
    train_consensus_scores, _, _ = incidence_scores(train_frontier)
    train_selected = threshold_selection(train_consensus_scores, threshold)
    train_score = score_selected(
        train_selected, train_correct,
        len(train_species) - len(train_seed_species))

    # Evaluation target coordinates are not touched until after the frozen
    # seed frontier and threshold have both been constructed.
    eval_seed_species, eval_seed_positions, _ = crop(
        raw.species, raw.positions, eval_center, 7.)
    eval_frontier = frozen_frontier(
        program, eval_seed_species, eval_seed_positions)
    consensus, overlap, frequency = incidence_scores(eval_frontier)
    eval_selected = threshold_selection(consensus, threshold)
    eval_species, eval_positions, eval_ids = crop(
        raw.species, raw.positions, eval_center, 11.)
    eval_correct = _shell_keys(
        raw.species, raw.positions, eval_center, 7., 11.)
    shell_atoms = len(eval_species) - len(eval_seed_species)
    consensus_score = score_selected(
        eval_selected, eval_correct, shell_atoms)
    matched = len(eval_selected)
    overlap_score = score_selected(
        top_k_selection(overlap, matched), eval_correct, shell_atoms)
    frequency_score = score_selected(
        top_k_selection(frequency, matched), eval_correct, shell_atoms)
    shuffled = tuple(score_selected(
        top_k_selection(shuffled_incidence_consensus(
            eval_frontier, seed=31415 + run), matched),
        eval_correct, shell_atoms) for run in range(shuffled_runs))
    p_value = ((1 + sum(item.correct >= consensus_score.correct
                        for item in shuffled)) / (shuffled_runs + 1))
    digest = lambda frontier: hashlib.sha256(
        repr(frontier.candidate_digest_payload).encode()).hexdigest()
    superiority = (
        consensus_score.correct > overlap_score.correct and
        consensus_score.correct > frequency_score.correct and
        p_value <= .05 and consensus_score.precision >= .99)
    return IQCOverlapConsensusAudit(
        len(train_species), len(train_seed_species),
        len(train_species) - len(train_seed_species),
        len(eval_species), len(eval_seed_species), shell_atoms,
        set(train_ids).isdisjoint(eval_ids),
        len(program.prototypes), len(program.atlas.ports),
        train_frontier.seed_occurrences, eval_frontier.seed_occurrences,
        len(train_frontier.candidates), len(eval_frontier.candidates),
        digest(train_frontier), digest(eval_frontier), threshold, available,
        train_score, consensus_score, overlap_score, frequency_score,
        median(item.precision for item in shuffled),
        median(item.correct for item in shuffled),
        max(item.correct for item in shuffled), shuffled_runs, p_value, True,
        False, False, consensus_score.precision >= .99,
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
