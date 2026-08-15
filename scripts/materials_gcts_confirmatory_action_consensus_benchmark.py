#!/usr/bin/env python3
"""One-shot confirmation of whole-action consensus plus train frequency.

The scoring rule and top-action budget were frozen after an earlier exploratory
patch: normalized minimum emitted-site consensus + normalized log1p training
production observations, with overlap then stable candidate id as ties. This
module applies that rule once to a different spatially disjoint IQC patch.
Confirmation labels are constructed only after the complete candidate batch,
features, rule, and 31 degree-preserving incidence controls are frozen.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_frozen_frontier_replay import (
    RadialBoundary, enumerate_frontier, fit_frozen_frontier_program)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


@dataclass(frozen=True)
class TopActionScore:
    arm: str
    budget: int
    exact_actions: int
    inexact_actions: int
    correct_emitted_site_counts: int
    wrong_emitted_site_counts: int


@dataclass(frozen=True)
class MatchedActionWork:
    arm: str
    matched_unique_correct_sites: int
    proposal_checks: int
    geometric_backtracks: int


@dataclass(frozen=True)
class ConfirmatoryActionConsensusBenchmark:
    oracle_atoms: int
    training_atoms: int
    seed_atoms: int
    target_atoms: int
    training_center: tuple[float, float, float]
    confirmatory_center: tuple[float, float, float]
    training_center_norm_squared: float
    confirmatory_center_norm_squared: float
    train_target_raw_id_intersection: int
    centers_separation: float
    sum_train_target_radii: float
    spatial_domains_disjoint: bool
    recognized_seed_occurrences: int
    explicit_seed_gap_atoms: int
    frozen_candidates: int
    attempted_poses: int
    rejected_outside_public_boundary: int
    public_radial_boundary_used_before_labels: bool
    frozen_budget: int
    frozen_consensus_weight: float
    frozen_log_frequency_weight: float
    exploratory_rule_center: tuple[float, float, float]
    rule_source: str
    confirmatory_labels_used_for_rule_or_budget: bool
    frequency_only: TopActionScore
    consensus_only: TopActionScore
    combined: TopActionScore
    combined_matched_work: MatchedActionWork
    frequency_matched_work: MatchedActionWork
    consensus_matched_work: MatchedActionWork
    shuffled_runs: int
    shuffled_exact_actions: tuple[int, ...]
    shuffled_wrong_emitted_sites: tuple[int, ...]
    shuffled_matched_work: tuple[MatchedActionWork, ...]
    maximum_shuffled_exact_actions: int
    minimum_shuffled_wrong_emitted_sites: int
    empirical_exact_action_p_value: float
    empirical_wrong_site_p_value: float
    minimum_shuffled_matched_total_work: int
    empirical_matched_work_p_value: float
    candidate_ids_and_actions_identical_across_arms: bool
    every_shuffle_preserves_candidate_degree: bool
    every_shuffle_preserves_site_degree: bool
    grammar_and_frequency_fit_on_training_only: bool
    rule_and_budget_frozen_before_confirmation: bool
    target_constructed_after_candidates_and_controls: bool
    target_used_for_candidate_generation_features_or_ranking: bool
    confirmatory_gate_passed: bool


def _incidence(candidates, tolerance):
    """Cluster emitted colored positions by actual metric, not hash bins."""
    representatives = []
    incidence = []
    for candidate in candidates:
        keys = set()
        for species, point in sorted(candidate.novel_sites, key=repr):
            matches = [index for index, (known_species, known_point) in
                       enumerate(representatives)
                       if known_species == species and
                       math.dist(point, known_point) <= tolerance]
            if matches:
                key = min(matches, key=lambda index:
                          math.dist(point, representatives[index][1]))
            else:
                key = len(representatives)
                representatives.append((species, point))
            keys.add(key)
        incidence.append(frozenset(keys))
    return tuple(incidence), tuple(representatives)


def _consensus(incidence):
    degrees = Counter(site for sites in incidence for site in sites)
    raw = tuple(min((degrees[site] for site in sites), default=0)
                for sites in incidence)
    maximum = max(raw, default=1)
    return tuple(value / maximum for value in raw), degrees


def _degree_preserving_shuffle(incidence, seed):
    rng = random.Random(seed)
    shuffled = [set(values) for values in incidence]
    edge_count = sum(map(len, shuffled))
    nonempty = [index for index, values in enumerate(shuffled) if values]
    for _ in range(max(1, edge_count * 12)):
        if len(nonempty) < 2:
            break
        left, right = rng.sample(nonempty, 2)
        left_only = tuple(shuffled[left] - shuffled[right])
        right_only = tuple(shuffled[right] - shuffled[left])
        if not left_only or not right_only:
            continue
        first = rng.choice(left_only)
        second = rng.choice(right_only)
        shuffled[left].remove(first)
        shuffled[left].add(second)
        shuffled[right].remove(second)
        shuffled[right].add(first)
    return tuple(frozenset(values) for values in shuffled)


def _order(consensus, log_frequency, candidates, mode):
    if mode == "combined":
        score = tuple(consensus[index] + log_frequency[index]
                      for index in range(len(candidates)))
    elif mode == "frequency":
        score = log_frequency
    elif mode == "consensus":
        score = consensus
    else:
        raise ValueError("unknown scoring mode")
    return tuple(sorted(range(len(candidates)), key=lambda index: (
        -score[index], -candidates[index].overlap_atoms, index)))


def _top_score(name, order, incidence, target_keys, budget):
    exact = correct = wrong = 0
    for index in order[:budget]:
        good = incidence[index].intersection(target_keys)
        bad = incidence[index].difference(target_keys)
        exact += bool(incidence[index]) and not bad
        correct += len(good)
        wrong += len(bad)
    return TopActionScore(
        name, budget, exact, budget - exact, correct, wrong)


def _matched_work(name, order, incidence, target_keys, matched_sites):
    recovered = set()
    backtracks = 0
    for checks, index in enumerate(order, 1):
        bad = incidence[index].difference(target_keys)
        if bad:
            backtracks += 1
        else:
            recovered.update(incidence[index].intersection(target_keys))
        if matched_sites.issubset(recovered):
            return MatchedActionWork(
                name, len(matched_sites), checks, backtracks)
    raise RuntimeError("candidate order cannot recover matched sites")


def evaluate(*, shuffled_runs: int = 31) -> ConfirmatoryActionConsensusBenchmark:
    if shuffled_runs != 31:
        raise ValueError("confirmation requires the frozen 31 controls")
    training_center = (-16.0, 0.0, 0.0)
    confirmation_center = (5.0, -17.0, 4.0)
    train_radius = target_radius = 11.0
    seed_radius = 7.0
    frozen_budget = 100
    oracle, _ = oracle_patch_fast(9, 34.0)
    training, training_ids = _crop(
        oracle, training_center, train_radius, "IQC-consensus-train")
    seed_cloud, _ = _crop(
        oracle, confirmation_center, seed_radius, "IQC-confirm-seed")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    enumeration = enumerate_frozen_port_occurrences(
        learned, seed_cloud.species, seed_cloud.positions,
        select_greedy_cover=True)
    covered = {index for _, support in enumeration.occurrence_supports
               for index in support}
    gaps = tuple((seed_cloud.species[index], seed_cloud.positions[index])
                 for index in range(len(seed_cloud.positions))
                 if index not in covered)
    frontier = enumerate_frontier(
        frozen, enumeration.occurrences, explicit_gap_sites=gaps,
        boundary=RadialBoundary(confirmation_center, target_radius))
    candidates = frontier.candidates
    incidence, emitted_representatives = _incidence(
        candidates, frozen.overlap_tolerance)
    consensus, site_degrees = _consensus(incidence)
    raw_frequency = tuple(math.log1p(
        frozen.productions[candidate.production_id].training_observations)
                          for candidate in candidates)
    maximum_frequency = max(raw_frequency, default=1.0)
    log_frequency = tuple(value / maximum_frequency
                          for value in raw_frequency)
    combined_order = _order(
        consensus, log_frequency, candidates, "combined")
    frequency_order = _order(
        consensus, log_frequency, candidates, "frequency")
    consensus_order = _order(
        consensus, log_frequency, candidates, "consensus")

    shuffled_incidence = tuple(_degree_preserving_shuffle(
        incidence, 32452843 + 49999 * run) for run in range(shuffled_runs))
    shuffled_consensus = tuple(_consensus(values)[0]
                               for values in shuffled_incidence)
    shuffled_orders = tuple(_order(
        values, log_frequency, candidates, "combined")
                            for values in shuffled_consensus)

    # Sealed oracle boundary: target crop and raw ids are first constructed
    # after candidates, real features, controls, and every order are frozen.
    target, target_ids = _crop(
        oracle, confirmation_center, target_radius, "IQC-confirm-target")
    target_sites = tuple(zip(target.species, target.positions))
    target_keys = {index for index, (species, point) in
                   enumerate(emitted_representatives)
                   if any(species == target_species and
                          math.dist(point, target_point) <=
                          frozen.overlap_tolerance
                          for target_species, target_point in target_sites)}
    combined = _top_score(
        "combined", combined_order, incidence, target_keys, frozen_budget)
    frequency = _top_score(
        "frequency-only", frequency_order, incidence, target_keys,
        frozen_budget)
    consensus_only = _top_score(
        "consensus-only", consensus_order, incidence, target_keys,
        frozen_budget)
    shuffled_scores = tuple(_top_score(
        f"shuffle-{run}", order, incidence, target_keys, frozen_budget)
                            for run, order in enumerate(shuffled_orders))
    matched_sites = frozenset(site for index in
        combined_order[:frozen_budget]
        if not incidence[index].difference(target_keys)
        for site in incidence[index])
    combined_work = _matched_work(
        "combined", combined_order, incidence, target_keys, matched_sites)
    frequency_work = _matched_work(
        "frequency-only", frequency_order, incidence, target_keys,
        matched_sites)
    consensus_work = _matched_work(
        "consensus-only", consensus_order, incidence, target_keys,
        matched_sites)
    shuffled_work = tuple(_matched_work(
        f"shuffle-{run}", order, incidence, target_keys, matched_sites)
                          for run, order in enumerate(shuffled_orders))
    shuffled_exact = tuple(item.exact_actions for item in shuffled_scores)
    shuffled_wrong = tuple(item.wrong_emitted_site_counts
                           for item in shuffled_scores)
    exact_p = ((1 + sum(value >= combined.exact_actions
                        for value in shuffled_exact)) /
               (shuffled_runs + 1))
    wrong_p = ((1 + sum(value <= combined.wrong_emitted_site_counts
                        for value in shuffled_wrong)) /
               (shuffled_runs + 1))
    combined_total_work = (combined_work.proposal_checks +
                           combined_work.geometric_backtracks)
    shuffled_total_work = tuple(item.proposal_checks +
                                item.geometric_backtracks
                                for item in shuffled_work)
    matched_p = ((1 + sum(value <= combined_total_work
                          for value in shuffled_total_work)) /
                 (shuffled_runs + 1))
    candidate_degrees = tuple(map(len, incidence))
    site_degree_code = tuple(sorted(site_degrees.items(), key=repr))
    row_preserved = all(tuple(map(len, values)) == candidate_degrees
                        for values in shuffled_incidence)
    column_preserved = all(tuple(sorted(
        _consensus(values)[1].items(), key=repr)) == site_degree_code
                           for values in shuffled_incidence)
    separation = math.dist(training_center, confirmation_center)
    raw_intersection = len(set(training_ids).intersection(target_ids))
    passed = (combined.exact_actions > frequency.exact_actions and
              combined.exact_actions > consensus_only.exact_actions and
              combined.wrong_emitted_site_counts <
              frequency.wrong_emitted_site_counts and
              combined.wrong_emitted_site_counts <
              consensus_only.wrong_emitted_site_counts and
              exact_p <= .05 and wrong_p <= .05 and matched_p <= .05 and
              combined_total_work < min(shuffled_total_work) and row_preserved and
              column_preserved and raw_intersection == 0)
    return ConfirmatoryActionConsensusBenchmark(
        len(oracle.positions), len(training.positions),
        len(seed_cloud.positions), len(target.positions), training_center,
        confirmation_center,
        sum(value * value for value in training_center),
        sum(value * value for value in confirmation_center),
        raw_intersection, separation,
        train_radius + target_radius, separation >
        train_radius + target_radius and raw_intersection == 0,
        len(enumeration.occurrences), len(gaps), len(candidates),
        frontier.attempted_poses, frontier.outside_boundary, True,
        frozen_budget, 1.0, 1.0,
        (8.0, 14.0, 7.0),
        "frozen after the separate exploratory patch; not retuned here",
        False,
        frequency, consensus_only, combined, combined_work, frequency_work,
        consensus_work, shuffled_runs, shuffled_exact, shuffled_wrong,
        shuffled_work, max(shuffled_exact), min(shuffled_wrong), exact_p,
        wrong_p, min(shuffled_total_work), matched_p,
        True, row_preserved, column_preserved, True, True, True,
        False, passed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
