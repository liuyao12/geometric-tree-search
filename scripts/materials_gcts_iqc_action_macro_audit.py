#!/usr/bin/env python3
"""Target-free IQC adapter for externally selected batch thresholds."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_batch_frontier_search import run_batch_frontier_search
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, fit_frozen_frontier_program)
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)


@dataclass(frozen=True)
class IQCActionMacroAudit:
    externally_supplied_threshold_ratio: float
    externally_supplied_wave_limit: int
    maximum_waves: int
    training_center: tuple[float, float, float]
    seed_center: tuple[float, float, float]
    public_boundary_radius: float | None
    training_atoms: int
    seed_atoms: int
    recognized_seed_occurrences: int
    wave_candidate_counts: tuple[int, ...]
    wave_maximum_minimum_support: tuple[int, ...]
    wave_accepted_counts: tuple[int, ...]
    emitted_atoms: int
    action_macros: int
    exact_certified_action_macros: int
    macro_child_counts: tuple[int, ...]
    macro_waves: tuple[int, ...]
    canonical_action_macros: int
    normalized_production_keys: tuple[str, ...]
    normalized_key_wave_support: tuple[tuple[str, tuple[int, ...]], ...]
    recurring_three_wave_signatures: int
    hierarchy_stationarity_claimed: bool
    executor_result_digest: str
    exact_cover_of_accepted_nodes: bool
    target_used: bool


def _crop(configuration, center, radius, name):
    indices = tuple(index for index, point in enumerate(configuration.positions)
                    if math.dist(point, center) <= radius + 1e-10)
    return AtomicConfiguration(
        name, tuple(configuration.positions[index] for index in indices),
        tuple(configuration.species[index] for index in indices))


def evaluate(*, threshold_ratio: float,
             maximum_accepted_per_wave: int,
             maximum_waves: int = 3,
             training_center: tuple[float, float, float] = (-16.0, 0.0, 0.0),
             seed_center: tuple[float, float, float] = (8.0, 14.0, 7.0),
             training_radius: float = 11.0,
             seed_radius: float = 7.0,
             public_boundary_radius: float | None = None,
             ) -> IQCActionMacroAudit:
    oracle, _ = oracle_patch_fast(8, 32.0)
    training = _crop(
        oracle, training_center, training_radius, "IQC-action-macro-train")
    seed_cloud = _crop(
        oracle, seed_center, seed_radius, "IQC-action-macro-seed")
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
    batch = run_batch_frontier_search(
        frozen, FrontierSeed(enumeration.occurrences, gaps),
        threshold_ratio=threshold_ratio, maximum_waves=maximum_waves,
        maximum_accepted_per_wave=maximum_accepted_per_wave,
        boundary=(None if public_boundary_radius is None else
                  RadialBoundary(seed_center, public_boundary_radius)))
    promoted = promote_batch_action_macros(frozen, batch)
    normalized_support = {}
    for macro in promoted.macros:
        if macro.normalized_production_key is not None:
            normalized_support.setdefault(
                macro.normalized_production_key, set()).add(macro.wave)
    digest = hashlib.sha256(repr((
        batch.threshold_ratio,
        tuple((wave.wave,
               tuple(item.candidate_id for item in wave.candidates),
               tuple(item.candidate_id for item in wave.candidates
                     if item.accepted)) for wave in batch.waves),
        tuple(_site for _site in batch.sites))).encode()).hexdigest()
    return IQCActionMacroAudit(
        threshold_ratio, maximum_accepted_per_wave, maximum_waves,
        training_center, seed_center, public_boundary_radius,
        len(training.positions), len(seed_cloud.positions),
        len(enumeration.occurrences),
        tuple(wave.candidate_count for wave in batch.waves),
        tuple(wave.maximum_minimum_site_support for wave in batch.waves),
        tuple(wave.accepted_candidates for wave in batch.waves),
        len(batch.sites) - len(batch.initial_sites), len(promoted.macros),
        sum(all((macro.certificate.
                     nodes_are_exactly_accepted_wave_component,
                 macro.certificate.every_child_pose_proper_se3,
                 macro.certificate.colored_union_is_exact,
                 macro.certificate.edge_overlaps_are_exact_intersections,
                 macro.certificate.
                     incoming_boundaries_are_train_frozen_ports,
                 macro.certificate.pairwise_compatible_antichain))
            for macro in promoted.macros),
        tuple(len(macro.children) for macro in promoted.macros),
        tuple(macro.wave for macro in promoted.macros),
        sum(macro.normalized_production_key is not None
            for macro in promoted.macros),
        tuple(sorted(macro.normalized_production_key
                     for macro in promoted.macros
                     if macro.normalized_production_key is not None)),
        tuple(sorted((key, tuple(sorted(waves)))
                     for key, waves in normalized_support.items())),
        sum(item.recurs_across_three_consecutive_waves
            for item in promoted.recurrences),
        any(item.hierarchy_stationarity_claimed
            for item in promoted.recurrences), digest,
        promoted.exact_cover_of_accepted_nodes,
        batch.target_used or promoted.target_used)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", required=True, type=float)
    parser.add_argument("--wave-limit", required=True, type=int)
    parser.add_argument("--waves", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(
        threshold_ratio=arguments.threshold,
        maximum_accepted_per_wave=arguments.wave_limit,
        maximum_waves=arguments.waves)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
