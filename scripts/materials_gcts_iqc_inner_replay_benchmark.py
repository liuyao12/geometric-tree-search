#!/usr/bin/env python3
"""Slow full multi-seed IQC reconstruction gate for indexed replay.

The evaluation geometry was seen while learning the productions.  This is a
target-blind reconstruction audit, not a held-out continuation claim.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import (
    execute_macro_derivation, score_macro_derivation)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros


@dataclass(frozen=True)
class IQCInnerReplayBenchmark:
    training_atoms: int
    dense_occurrences: int
    explicit_inner_atoms: int
    inner_macro_seeds: int
    actual_seed_atoms: int
    compile_match_promotion_seconds: float
    replay_seconds: float
    attempted_candidates: int
    accepted_nodes: int
    emitted_atoms: int
    correct_emitted_atoms: int
    precision: float
    training_reconstruction_recall: float
    evaluation_geometry_seen_during_learning: bool
    target_used_during_replay: bool


def evaluate() -> IQCInnerReplayBenchmark:
    configuration, _ = oracle_patch(3, 9.0)
    started = time.perf_counter()
    atomic = compile_irregular_port_program(
        configuration.species, configuration.positions)
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, mined.macro_types)
    promoted = promote_macro_types(atomic, dense.dense_macro_types)
    preparation_seconds = time.perf_counter() - started
    center = tuple(sum(point[axis] for point in configuration.positions) /
                   len(configuration.positions) for axis in range(3))
    atom_radii = tuple(math.dist(point, center)
                       for point in configuration.positions)
    atom_cutoff = sorted(atom_radii)[len(atom_radii) // 3]
    inner_atoms = tuple(index for index, radius in enumerate(atom_radii)
                        if radius <= atom_cutoff)
    macro_radii = tuple(math.dist(occurrence.translation, center)
                        for occurrence in promoted.occurrences)
    macro_cutoff = sorted(macro_radii)[len(macro_radii) // 10]
    seeds = tuple(occurrence for occurrence, radius in zip(
        promoted.occurrences, macro_radii) if radius <= macro_cutoff)
    explicit_sites = tuple(
        (configuration.species[index], configuration.positions[index])
        for index in inner_atoms)
    started = time.perf_counter()
    replay = execute_macro_derivation(
        promoted, seeds, explicit_seed_sites=explicit_sites,
        maximum_levels=1, maximum_new_nodes_per_level=64)
    replay_seconds = time.perf_counter() - started
    score = score_macro_derivation(
        replay, configuration.species, configuration.positions)
    return IQCInnerReplayBenchmark(
        len(configuration.positions), dense.total_dense_occurrences,
        len(inner_atoms), len(seeds), len(replay.seed_sites),
        preparation_seconds, replay_seconds, replay.attempted_candidates,
        len(replay.steps), score.proposed_novel_atoms,
        score.correct_novel_atoms, score.precision, score.heldout_recall,
        True, replay.target_used)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
