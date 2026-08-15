#!/usr/bin/env python3
"""Honest 9->15 IQC continuation gate for a frozen one-wave grammar."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_exterior_candidate_executor import (
    enumerate_exterior_candidates, execute_exterior_wave,
    score_exterior_wave)
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros


@dataclass(frozen=True)
class RankedWaveResult:
    policy: str
    candidate_id_digest: str
    accepted_candidates: int
    emitted_atoms: int
    correct_atoms: int
    precision: float
    continuation_recall: float


@dataclass(frozen=True)
class IQCExteriorWaveBenchmark:
    training_atoms: int
    heldout_target_atoms: int
    dense_macro_occurrences: int
    frontier_macro_occurrences: int
    fit_seconds: float
    enumerate_seconds: float
    frozen_candidates: int
    attempted_proposals: int
    rejected_known_poses: int
    duplicate_proposals: int
    rejected_conflicts: int
    rejected_insufficient_overlap: int
    rejected_nonexterior: int
    rankers_received_identical_candidate_ids: bool
    target_used_before_scoring: bool
    waves: tuple[RankedWaveResult, ...]


def _digest(candidate_ids) -> str:
    import hashlib
    return hashlib.sha256(repr(tuple(candidate_ids)).encode()).hexdigest()


def evaluate() -> IQCExteriorWaveBenchmark:
    training, _ = oracle_patch(3, 9.0)
    started = time.perf_counter()
    atomic = compile_irregular_port_program(
        training.species, training.positions)
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, mined.macro_types)
    promoted = promote_macro_types(atomic, dense.dense_macro_types)
    fit_seconds = time.perf_counter() - started
    started = time.perf_counter()
    atom_radii = tuple(sum(value * value for value in point) ** .5
                       for point in training.positions)
    frontier_atoms = {
        index for index, radius in enumerate(atom_radii)
        if radius >= max(atom_radii) - promoted.minimum_distance}
    supports = dict(promoted.occurrence_supports)
    frontier = tuple(
        occurrence for occurrence in promoted.occurrences
        if frontier_atoms.intersection(supports[occurrence.occurrence_id]))
    frozen = enumerate_exterior_candidates(
        promoted, promoted.occurrences,
        frontier_occurrences=frontier,
        explicit_seed_sites=tuple(zip(training.species, training.positions)),
        boundary_origin=(0.0, 0.0, 0.0), boundary_radius=9.0)
    enumerate_seconds = time.perf_counter() - started
    evidence_policy = lambda candidate: (
        -max(evidence.observations for evidence in candidate.evidence),
        -sum(evidence.child_port_witnesses
             for evidence in candidate.evidence),
        -len(candidate.initial_overlap))
    waves = (
        ("default", execute_exterior_wave(
            frozen, maximum_candidates=64)),
        ("evidence", execute_exterior_wave(
            frozen, maximum_candidates=64, ranker=evidence_policy)),
    )
    same_ids = len({wave.candidate_ids for _, wave in waves}) == 1
    # The larger oracle patch is deliberately constructed only after fitting,
    # enumeration, and execution have completed.
    target, _ = oracle_patch(4, 15.0)
    scored = []
    for policy, wave in waves:
        score = score_exterior_wave(
            frozen, wave, target.species, target.positions)
        scored.append(RankedWaveResult(
            policy, _digest(wave.candidate_ids),
            len(wave.accepted_candidate_ids), len(wave.emitted_sites),
            score.correct_atoms, score.precision,
            score.continuation_recall))
    return IQCExteriorWaveBenchmark(
        len(training.positions), len(target.positions),
        dense.total_dense_occurrences, len(frontier), fit_seconds,
        enumerate_seconds,
        len(frozen.candidates), frozen.attempted_proposals,
        frozen.rejected_known_poses, frozen.duplicate_proposals,
        frozen.rejected_conflicts, frozen.rejected_insufficient_overlap,
        frozen.rejected_nonexterior, same_ids,
        frozen.target_used or any(wave.target_used for _, wave in waves),
        tuple(scored))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
