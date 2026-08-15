#!/usr/bin/env python3
"""Honest crystal/quasicrystal frontier-replay gate with a sealed scorer."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, enumerate_frontier,
    fit_frozen_frontier_program,
    replay_frontier, score_replay)
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program


def _symmetric_periodic_target(
    configuration: AtomicConfiguration,
) -> AtomicConfiguration:
    """Oracle-only 3x3x3 explicit crop surrounding the observed crystal.

    The learner receives a non-periodic copy below.  A symmetric scorer window
    avoids declaring an outward action wrong merely because the conventional
    positive-octant replication omitted that side of the frontier.
    """
    if configuration.cell is None:
        raise ValueError("symmetric periodic target needs an oracle cell")
    positions = []
    species = []
    for shift in itertools.product((-1, 0, 1), repeat=3):
        offset = tuple(sum(shift[row] * configuration.cell[row][axis]
                           for row in range(3)) for axis in range(3))
        for point, label in zip(configuration.positions, configuration.species):
            positions.append(tuple(point[axis] + offset[axis]
                                   for axis in range(3)))
            species.append(label)
    return AtomicConfiguration(
        configuration.name + "-symmetric-oracle", tuple(positions),
        tuple(species))


@dataclass(frozen=True)
class FrozenReplayCase:
    system: str
    training_atoms: int
    target_atoms: int
    frozen_productions: int
    oriented_seed_atoms: int
    explicit_unoriented_seed_atoms: int
    attempted_poses: int
    rejected_outside_boundary: int
    candidate_actions: int
    oracle_best_correct_atoms: int
    oracle_best_precision: float
    oracle_correct_action_exists: bool
    proposed_novel_atoms: int
    correct_novel_atoms: int
    precision: float
    heldout_recall: float
    target_used_for_proposals: bool
    one_step_gate_passed: bool


@dataclass(frozen=True)
class FrozenReplayBenchmark:
    cases: tuple[FrozenReplayCase, ...]
    crystal_gate_passed: bool
    ideal_quasicrystal_gate_passed: bool
    real_quasicrystal_gate_passed: bool
    all_targets_sealed_from_proposals: bool


def _case(training: AtomicConfiguration,
          target: AtomicConfiguration) -> FrozenReplayCase:
    learned = compile_irregular_port_program(
        training.species, training.positions)
    program = fit_frozen_frontier_program(learned)
    parent_types = {production.parent_type for production in
                    program.productions}
    eligible = tuple(occurrence for occurrence in learned.occurrences
                     if occurrence.type_id in parent_types)
    if not eligible:
        return FrozenReplayCase(
            training.name, len(training.positions), len(target.positions),
            len(program.productions), 0, len(training.positions), 0, 0,
            0, 0, 0.0, False, 0, 0, 0.0, 0.0, False, False)
    # Training-only frontier choice: the eligible occurrence whose centroid is
    # farthest from the training centroid. No held-out point participates.
    origin = tuple(sum(point[axis] for point in training.positions) /
                   len(training.positions) for axis in range(3))
    parent = max(eligible, key=lambda occurrence: (
        math.dist(occurrence.translation, origin),
        occurrence.occurrence_id))
    members = set(dict(learned.occurrence_supports)[parent.occurrence_id])
    gaps = tuple((training.species[index], training.positions[index])
                 for index in range(len(training.positions))
                 if index not in members)
    radius = max(math.dist(point, origin) for point in training.positions) * 2.0
    seed = FrontierSeed((parent,), gaps)
    boundary = RadialBoundary(origin, radius)
    # Enumerate first without a target.  The oracle ceiling below is computed
    # afterward and is diagnostic only: it tells us whether a marking could
    # select a correct action from this exact frozen candidate set.
    frontier = enumerate_frontier(
        program, seed.occurrences, explicit_gap_sites=seed.explicit_gap_sites,
        boundary=boundary)
    replay = replay_frontier(
        program, seed, maximum_steps=1, boundary=boundary)
    score = score_replay(replay, target.species, target.positions)
    target_sites = tuple(zip(target.species, target.positions))
    candidate_scores = []
    for candidate in frontier.candidates:
        correct = sum(any(
            species == target_species and math.dist(point, target_point) <= .03
            for target_species, target_point in target_sites)
                      for species, point in candidate.novel_sites)
        candidate_scores.append((
            correct, correct / max(1, len(candidate.novel_sites))))
    best_correct, best_precision = max(
        candidate_scores, default=(0, 0.0), key=lambda item: (item[0], item[1]))
    passed = (score.proposed_novel_atoms > 0 and score.precision >= .99 and
              not score.target_used_for_proposals)
    return FrozenReplayCase(
        training.name, len(training.positions), len(target.positions),
        len(program.productions), replay.initial_oriented_sites,
        replay.explicit_seed_gap_sites, replay.attempted_poses,
        replay.rejected_outside_boundary, len(frontier.candidates),
        best_correct, best_precision,
        any(correct > 0 and precision >= .99
            for correct, precision in candidate_scores),
        score.proposed_novel_atoms,
        score.correct_novel_atoms, score.precision, score.heldout_recall,
        score.target_used_for_proposals, passed)


def evaluate() -> FrozenReplayBenchmark:
    nacl_source = next(item for item in benchmark_systems()
                       if item.name == "NaCl-rocksalt")
    nacl_target = _symmetric_periodic_target(nacl_source)
    nacl = AtomicConfiguration(
        nacl_source.name, nacl_source.positions, nacl_source.species)
    iqc, _ = oracle_patch(3, 9.0)
    iqc_target, _ = oracle_patch(4, 15.0)
    cdyb = build_cdyb_split()
    cases = tuple(_case(training, target) for training, target in (
        (nacl, nacl_target), (iqc, iqc_target),
        (cdyb.training, cdyb.validation)))
    return FrozenReplayBenchmark(
        cases, cases[0].one_step_gate_passed,
        cases[1].one_step_gate_passed,
        cases[2].one_step_gate_passed,
        all(not case.target_used_for_proposals for case in cases))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
