#!/usr/bin/env python3
"""Durable executed five-wave confirmation of frozen IQC consensus.

The ratio 15/21 is imported as a fixed result of the disjoint train-only
action calibration.  This benchmark does not tune it.  It executes whole
cluster placements for five self-fed waves on a third spatially disjoint crop;
the target crop is constructed only after threshold 15/21 and the two
predeclared diagnostic thresholds (0 and .5) have finished.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math

from materials_gcts_batch_frontier_search import run_batch_frontier_search
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, _site_key, fit_frozen_frontier_program)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


@dataclass(frozen=True)
class ExecutedThresholdResult:
    threshold_ratio: float
    accepted_per_wave: tuple[int, ...]
    candidate_proposals: int
    geometric_backtracks: int
    placed_clusters: int
    proposed_unique_atoms: int
    correct_unique_atoms: int
    wrong_unique_atoms: int
    precision: float
    heldout_recall: float
    target_used_during_execution: bool


@dataclass(frozen=True)
class IQCMultiwaveConfirmatoryAudit:
    training_atoms: int
    confirmation_seed_atoms: int
    confirmation_target_atoms: int
    training_center: tuple[float, float, float]
    confirmation_center: tuple[float, float, float]
    train_target_raw_id_intersection: int
    spatial_domains_disjoint: bool
    frozen_calibration_ratio: float
    calibration_source: str
    maximum_waves: int
    maximum_accepted_per_wave: int
    public_boundary_radius: float
    consensus: ExecutedThresholdResult
    threshold_zero_diagnostic: ExecutedThresholdResult
    threshold_half_diagnostic: ExecutedThresholdResult
    target_constructed_after_all_executions: bool
    exact_self_fed_continuation: bool
    stationary_or_exponential_certificate: bool
    family_phi_cell_target_unused_by_executor: bool


def _score(result, target_species, target_positions):
    tolerance = .03
    initial = {_site_key(site, tolerance) for site in result.initial_sites}
    final = {_site_key(site, tolerance) for site in result.sites}
    target = {_site_key(site, tolerance)
              for site in zip(target_species, target_positions)}
    proposed = final - initial
    correct = proposed.intersection(target)
    heldout = target - initial
    return ExecutedThresholdResult(
        result.threshold_ratio,
        tuple(wave.accepted_candidates for wave in result.waves),
        sum(wave.candidate_count for wave in result.waves),
        sum(wave.rejected_pair_conflicts + wave.rejected_redundant
            for wave in result.waves),
        len(result.accepted_candidate_ids), len(proposed), len(correct),
        len(proposed - target), len(correct) / max(1, len(proposed)),
        len(correct) / max(1, len(heldout)), result.target_used)


def evaluate() -> IQCMultiwaveConfirmatoryAudit:
    training_center = (-16., 0., 0.)
    confirmation_center = (5., -17., 4.)
    train_radius = target_radius = 11.
    seed_radius = 7.
    oracle, _ = oracle_patch_fast(9, 34.)
    training, training_ids = _crop(
        oracle, training_center, train_radius, "IQC-wave-train")
    seed_cloud, _ = _crop(
        oracle, confirmation_center, seed_radius, "IQC-wave-seed")
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
    seed = FrontierSeed(enumeration.occurrences, gaps)
    boundary = RadialBoundary(confirmation_center, target_radius)
    ratios = (15 / 21, 0., .5)
    executions = tuple(run_batch_frontier_search(
        frozen, seed, threshold_ratio=ratio, maximum_waves=5,
        maximum_accepted_per_wave=40, boundary=boundary)
                       for ratio in ratios)
    # Scorer-only target construction occurs after every execution is frozen.
    target, target_ids = _crop(
        oracle, confirmation_center, target_radius, "IQC-wave-target")
    scored = tuple(_score(result, target.species, target.positions)
                   for result in executions)
    consensus = scored[0]
    exact_self_fed = (
        consensus.proposed_unique_atoms > 0 and
        consensus.proposed_unique_atoms == consensus.correct_unique_atoms and
        len([value for value in consensus.accepted_per_wave if value]) > 1 and
        not consensus.target_used_during_execution)
    return IQCMultiwaveConfirmatoryAudit(
        len(training.positions), len(seed_cloud.positions),
        len(target.positions), training_center, confirmation_center,
        len(set(training_ids).intersection(target_ids)),
        set(training_ids).isdisjoint(target_ids), 15 / 21,
        "strict train-only whole-action calibration; fixed before confirmation",
        5, 40, target_radius, consensus, scored[1], scored[2], True,
        exact_self_fed, False,
        not any(result.target_used_during_execution for result in scored))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
