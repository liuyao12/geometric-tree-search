#!/usr/bin/env python3
"""Slow gate for dense IQC central-seed reconstruction replay.

The evaluation geometry was seen while learning the productions.  This checks
target-blind replay and reconstruction fidelity, not held-out continuation.
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
class IQCDenseReplayBenchmark:
    training_atoms: int
    atomic_occurrences: int
    admitted_macro_types: int
    sparse_admission_occurrences: int
    dense_promotion_occurrences: int
    overlap_ports: int
    boundary_ports: int
    compile_seconds: float
    mine_and_dense_match_seconds: float
    promotion_seconds: float
    replay_seconds: float
    seed_atoms: int
    attempted_candidates: int
    accepted_nodes: int
    emitted_atoms: int
    correct_emitted_atoms: int
    precision: float
    training_reconstruction_recall: float
    evaluation_geometry_seen_during_learning: bool
    target_used_during_replay: bool


def evaluate() -> IQCDenseReplayBenchmark:
    configuration, _ = oracle_patch(3, 9.0)
    started = time.perf_counter()
    atomic = compile_irregular_port_program(
        configuration.species, configuration.positions)
    compile_seconds = time.perf_counter() - started
    started = time.perf_counter()
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, mined.macro_types)
    match_seconds = time.perf_counter() - started
    started = time.perf_counter()
    promoted = promote_macro_types(atomic, dense.dense_macro_types)
    promotion_seconds = time.perf_counter() - started

    center = tuple(sum(point[axis] for point in configuration.positions) /
                   len(configuration.positions) for axis in range(3))
    seed = min(promoted.occurrences,
               key=lambda occurrence: (
                   math.dist(occurrence.translation, center),
                   occurrence.occurrence_id))
    started = time.perf_counter()
    replay = execute_macro_derivation(
        promoted, (seed,), maximum_levels=1,
        maximum_new_nodes_per_level=16)
    replay_seconds = time.perf_counter() - started
    # Scoring is post hoc, although this same geometry supplied the learner.
    score = score_macro_derivation(
        replay, configuration.species, configuration.positions)
    return IQCDenseReplayBenchmark(
        len(configuration.positions), len(atomic.occurrences),
        len(mined.macro_types), dense.total_sparse_admission_occurrences,
        dense.total_dense_occurrences, len(promoted.atlas.ports),
        len(promoted.boundary_ports), compile_seconds, match_seconds,
        promotion_seconds, replay_seconds, len(replay.seed_sites),
        replay.attempted_candidates, len(replay.steps),
        score.proposed_novel_atoms, score.correct_novel_atoms,
        score.precision, score.heldout_recall, True, replay.target_used)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
