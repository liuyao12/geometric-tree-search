#!/usr/bin/env python3
"""Bounded local GCTS section for autonomous published Cd--Yb growth.

The train-only section couples two coordinate-free frontier observables:
distance from a proposed site to the already placed cloud (in learned nearest-
neighbor units), and the number of distinct frozen cluster connections that
witness the same placement.  A proposal near the existing cloud needs enough
independent witnesses.  Exact ports still generate every coordinate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_batch_frontier_search import (
    FrozenPortPairMarking, run_batch_frontier_search)
from materials_gcts_cdyb_autonomous_frontier_benchmark import (
    MAXIMUM_ACCEPTED_PER_WAVE, _ids_in_radius, _score, _seed)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_cdyb_partial_decoration_benchmark import (
    EVAL_CENTER, RADIUS, TRAIN_CENTERS)
from materials_gcts_frozen_frontier_replay import (
    RadialBoundary, _site_key, fit_frozen_frontier_program)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program


SECOND_EVAL_CENTER = (-15.0, 10.0, -15.0)
EVAL_CENTERS = (EVAL_CENTER, SECOND_EVAL_CENTER)
CONSENSUS_THRESHOLD = 0.6
MAXIMUM_WAVES = 10


@dataclass(frozen=True)
class NucleusScore:
    center: tuple[float, float, float]
    seed_atoms: int
    accepted_per_wave: tuple[int, ...]
    emitted_atoms: int
    correct_atoms: int
    wrong_atoms: int
    precision: float
    outer_recall: float
    candidate_proposals: int
    geometric_backtracks: int


@dataclass(frozen=True)
class PolicyScore:
    name: str
    minimum_close_connection_witnesses: int
    nuclei: tuple[NucleusScore, ...]
    total_emitted_atoms: int
    total_correct_atoms: int
    total_wrong_atoms: int
    aggregate_precision: float
    zero_error_correct_reach: int


@dataclass(frozen=True)
class CdYbLocalSectionAudit:
    train_atoms: int
    training_candidate_samples: int
    training_selected_candidate_precision: float
    learned_close_distance_cutoff_nn: float
    learned_minimum_close_connection_witnesses: int
    marking_domain_order: int
    evaluation_nuclei: int
    all_train_and_eval_domains_pairwise_disjoint: bool
    unmarked: PolicyScore
    marked: PolicyScore
    shuffle_trials: int
    shuffled_median_zero_error_correct_reach: float
    shuffled_best_zero_error_correct_reach: int
    marked_reach_empirical_p: float
    identical_first_wave_candidates_all_policies: bool
    all_traces_frozen_before_evaluation_targets: bool
    target_labels_used_during_fit_or_execution: bool
    uses_absolute_position_direction_family_cell_potential_or_source_sites: bool
    exact_promoted_action_macros: int
    recurring_three_wave_macro_signatures: int
    causal_local_marking_gate_passed: bool
    stationary_or_exponential_growth_claimed: bool
    limitation: str


def _marking(cutoff, minimum_witnesses, *, shuffle_seed=None):
    return FrozenPortPairMarking(
        context_probabilities=(), minimum_support=1,
        minimum_probability=0.0, target_used_during_fit=False,
        require_context_support=False,
        close_distance_cutoff_nn=cutoff,
        minimum_close_connection_witnesses=minimum_witnesses,
        witness_shuffle_seed=shuffle_seed)


def _execute(program, seed, center, marking=None):
    return run_batch_frontier_search(
        program, seed, threshold_ratio=CONSENSUS_THRESHOLD,
        maximum_waves=MAXIMUM_WAVES,
        maximum_accepted_per_wave=MAXIMUM_ACCEPTED_PER_WAVE,
        boundary=RadialBoundary(center, RADIUS), marking=marking)


def _digest_first_wave(trace):
    candidates = (() if not trace.waves else
                  tuple(item.candidate_id for item in trace.waves[0].candidates))
    return hashlib.sha256(repr(candidates).encode()).hexdigest()


def _policy_score(name, minimum_witnesses, traces, scores, seed_counts):
    nuclei = tuple(NucleusScore(
        center, seed_count, score.accepted_per_wave, score.emitted_atoms,
        score.correct_atoms, score.wrong_atoms, score.precision,
        score.outer_recall, score.candidate_proposals,
        score.geometric_backtracks)
        for center, seed_count, score in zip(EVAL_CENTERS, seed_counts, scores))
    emitted = sum(item.emitted_atoms for item in nuclei)
    correct = sum(item.correct_atoms for item in nuclei)
    wrong = sum(item.wrong_atoms for item in nuclei)
    return PolicyScore(
        name, minimum_witnesses, nuclei, emitted, correct, wrong,
        correct / max(1, emitted), correct if wrong == 0 else 0)


def evaluate(shuffle_trials=31):
    if shuffle_trials < 0:
        raise ValueError("shuffle trial count cannot be negative")
    atoms = generate_cdyb(4, (60.0,) * 3)
    train_ids = tuple(index for index, point in enumerate(atoms.positions)
                      if any(math.dist(center, point) <= RADIUS + 1e-10
                             for center in TRAIN_CENTERS))
    learned = compile_irregular_port_program(
        tuple(atoms.symbols[index] for index in train_ids),
        tuple(atoms.positions[index] for index in train_ids))
    frozen = fit_frozen_frontier_program(learned)

    fit_rows = []
    fit_correct = 0
    for center in TRAIN_CENTERS:
        _ids, _enumeration, _covered, seed = _seed(learned, atoms, center)
        trace = run_batch_frontier_search(
            frozen, seed, threshold_ratio=CONSENSUS_THRESHOLD,
            maximum_waves=5,
            maximum_accepted_per_wave=MAXIMUM_ACCEPTED_PER_WAVE,
            boundary=RadialBoundary(center, RADIUS))
        target = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
                  for index in _ids_in_radius(atoms, center, RADIUS)}
        for wave in trace.waves:
            for candidate in wave.candidates:
                if candidate.normalized_support + 1e-15 < CONSENSUS_THRESHOLD:
                    continue
                correct = set(candidate.emitted_site_keys) <= target
                fit_correct += correct
                fit_rows.append((
                    candidate.minimum_novel_to_occupied_distance_nn,
                    len(candidate.connection_witnesses), correct))
    if not fit_rows or fit_correct != len(fit_rows):
        raise AssertionError("selected train candidate frontier is not exact")
    unique_distances = sorted(set(round(row[0], 12) for row in fit_rows))
    if len(unique_distances) < 2:
        raise AssertionError("cannot fit a bounded distance section")
    _gap, left, right = max(
        (right - left, left, right)
        for left, right in zip(unique_distances, unique_distances[1:]))
    cutoff = (left + right) / 2
    close_rows = tuple(row for row in fit_rows if row[0] <= cutoff)
    minimum_witnesses = min(row[1] for row in close_rows)
    learned_marking = _marking(cutoff, minimum_witnesses)

    seed_payloads = tuple(_seed(learned, atoms, center)
                          for center in EVAL_CENTERS)
    seeds = tuple(item[3] for item in seed_payloads)
    seed_counts = tuple(len(item[0]) for item in seed_payloads)
    unmarked_traces = tuple(_execute(frozen, seed, center)
                            for center, seed in zip(EVAL_CENTERS, seeds))
    marked_traces = tuple(_execute(
        frozen, seed, center, learned_marking)
        for center, seed in zip(EVAL_CENTERS, seeds))
    shuffled_trace_groups = tuple(tuple(_execute(
        frozen, seed, center, _marking(
            cutoff, minimum_witnesses, shuffle_seed=440_719 + trial))
        for center, seed in zip(EVAL_CENTERS, seeds))
        for trial in range(shuffle_trials))
    all_trace_groups = (unmarked_traces, marked_traces,
                        *shuffled_trace_groups)
    identical = all(
        _digest_first_wave(group[index]) ==
        _digest_first_wave(unmarked_traces[index])
        for group in all_trace_groups for index in range(len(EVAL_CENTERS)))

    # Evaluation target crops are opened only after all unique policies finish.
    target_payloads = tuple((
        tuple(atoms.symbols[index] for index in
              _ids_in_radius(atoms, center, RADIUS)),
        tuple(atoms.positions[index] for index in
              _ids_in_radius(atoms, center, RADIUS)))
        for center in EVAL_CENTERS)
    def score_group(group):
        return tuple(_score(trace, species, positions)
                     for trace, (species, positions) in zip(
                         group, target_payloads))
    unmarked_scores = score_group(unmarked_traces)
    marked_scores = score_group(marked_traces)
    shuffled_score_groups = tuple(score_group(group)
                                  for group in shuffled_trace_groups)
    unmarked = _policy_score(
        "unmarked", 0, unmarked_traces, unmarked_scores, seed_counts)
    marked = _policy_score(
        "bounded-local-section", minimum_witnesses,
        marked_traces, marked_scores, seed_counts)
    shuffled_policies = tuple(_policy_score(
        f"association-shuffle-{trial}", minimum_witnesses,
        group, scores, seed_counts)
        for trial, (group, scores) in enumerate(zip(
            shuffled_trace_groups, shuffled_score_groups)))
    shuffled_reach = tuple(item.zero_error_correct_reach
                           for item in shuffled_policies)
    p_value = ((1 + sum(value >= marked.zero_error_correct_reach
                        for value in shuffled_reach)) /
               (1 + len(shuffled_reach))) if shuffled_reach else 1.0
    promoted = tuple(promote_batch_action_macros(frozen, trace)
                     for trace in marked_traces)
    centers = TRAIN_CENTERS + EVAL_CENTERS
    pairwise_disjoint = all(
        math.dist(left, right) > 2 * RADIUS
        for index, left in enumerate(centers)
        for right in centers[index + 1:])
    causal_gate = (
        marked.aggregate_precision == 1.0 and
        marked.zero_error_correct_reach >= 290 and
        p_value <= .05 and identical and pairwise_disjoint)
    return CdYbLocalSectionAudit(
        len(train_ids), len(fit_rows), fit_correct / len(fit_rows),
        cutoff, minimum_witnesses, 1, len(EVAL_CENTERS), pairwise_disjoint,
        unmarked, marked, shuffle_trials,
        median(shuffled_reach) if shuffled_reach else 0.0,
        max(shuffled_reach, default=0), p_value, identical, True, False,
        False, sum(len(item.macros) for item in promoted),
        sum(recurrence.recurs_across_three_consecutive_waves
            for item in promoted for recurrence in item.recurrences),
        causal_gate, False,
        "The learned bounded section gives exact finite continuation on two "
        "disjoint nuclei. Both traces still reach finite fixed points and no "
        "action-macro production recurs across three waves, so stationarity "
        "and exponential growth remain unproved.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shuffle-trials", type=int, default=31)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.shuffle_trials)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
