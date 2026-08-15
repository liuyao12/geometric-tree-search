#!/usr/bin/env python3
"""Sealed disjoint-patch IQC frontier-transfer benchmark.

The primitive irregular grammar is fitted on one crop.  Frozen prototypes are
recognized on a spatially disjoint seed crop, then replay runs without the
larger concentric scoring crop.  Target atoms are materialized only after all
requested replay traces have terminated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass

from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, fit_frozen_frontier_program, replay_frontier, score_replay)
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)


@dataclass(frozen=True)
class DisjointReplayWave:
    maximum_actions: int
    elapsed_seconds: float
    accepted_actions: int
    proposed_atoms: int
    correct_atoms: int
    precision: float
    heldout_recall: float
    target_used_for_proposals: bool


@dataclass(frozen=True)
class DisjointIQCFrontierBenchmark:
    oracle_atoms: int
    training_atoms: int
    seed_atoms: int
    target_atoms: int
    training_raw_id_digest: str
    seed_raw_id_digest: str
    target_raw_id_digest: str
    training_target_raw_id_intersection: int
    center_separation: float
    sum_training_target_radii: float
    spatial_domains_disjoint: bool
    training_center_squared_norm: float
    evaluation_center_squared_norm: float
    centers_related_by_origin_fixing_proper_rotation: bool
    frozen_productions: int
    recognized_seed_occurrences: int
    explicit_seed_gap_atoms: int
    fit_and_seed_recognition_seconds: float
    target_materialized_after_all_replays: bool
    target_used_before_scoring: bool
    waves: tuple[DisjointReplayWave, ...]


def _crop(configuration, center, radius, name):
    indices = tuple(index for index, point in enumerate(configuration.positions)
                    if math.dist(point, center) <= radius + 1e-10)
    return AtomicConfiguration(
        name, tuple(configuration.positions[index] for index in indices),
        tuple(configuration.species[index] for index in indices)), indices


def _digest(indices) -> str:
    return hashlib.sha256(repr(tuple(indices)).encode()).hexdigest()


def evaluate() -> DisjointIQCFrontierBenchmark:
    training_center = (-16.0, 0.0, 0.0)
    evaluation_center = (8.0, 14.0, 7.0)
    training_radius = target_radius = 11.0
    seed_radius = 7.0
    oracle, _ = oracle_patch_fast(8, 32.0)
    training, training_ids = _crop(
        oracle, training_center, training_radius, "IQC-disjoint-training")
    seed_cloud, seed_ids = _crop(
        oracle, evaluation_center, seed_radius, "IQC-disjoint-seed")
    started = time.perf_counter()
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
    preparation_seconds = time.perf_counter() - started
    raw_replays = []
    for maximum_actions in (1, 10, 100):
        started = time.perf_counter()
        replay = replay_frontier(
            frozen, seed, maximum_steps=maximum_actions)
        raw_replays.append((maximum_actions,
                            time.perf_counter() - started, replay))

    # Scoring geometry is first materialized after every replay is frozen.
    target, target_ids = _crop(
        oracle, evaluation_center, target_radius, "IQC-disjoint-target")
    waves = []
    for maximum_actions, elapsed, replay in raw_replays:
        score = score_replay(replay, target.species, target.positions)
        waves.append(DisjointReplayWave(
            maximum_actions, elapsed, len(replay.accepted_productions),
            score.proposed_novel_atoms, score.correct_novel_atoms,
            score.precision, score.heldout_recall,
            replay.target_used_for_proposals))
    train_norm = sum(value * value for value in training_center)
    evaluation_norm = sum(value * value for value in evaluation_center)
    separation = math.dist(training_center, evaluation_center)
    return DisjointIQCFrontierBenchmark(
        len(oracle.positions), len(training.positions),
        len(seed_cloud.positions), len(target.positions),
        _digest(training_ids), _digest(seed_ids), _digest(target_ids),
        len(set(training_ids).intersection(target_ids)), separation,
        training_radius + target_radius,
        separation > training_radius + target_radius,
        train_norm, evaluation_norm,
        math.isclose(train_norm, evaluation_norm, abs_tol=1e-12),
        len(frozen.productions), len(enumeration.occurrences), len(gaps),
        preparation_seconds, True,
        any(replay.target_used_for_proposals for _, _, replay in raw_replays),
        tuple(waves))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
