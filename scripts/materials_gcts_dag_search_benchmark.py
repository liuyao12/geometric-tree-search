#!/usr/bin/env python3
"""Atomic versus transform-DAG parent-recognition benchmark.

Candidate macros are adversarial: every decoy properly rotates and translates
one child onto a known child of the same type.  Atomic search scores every leaf
of every candidate.  DAG-GCTS scores only level-(L-1) child-type markings,
selects a parent, and materializes its leaves once.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import time
from dataclasses import asdict, dataclass
from typing import Dict, Sequence, Tuple

from materials_gcts_transform_dag import (
    DagNode, Matrix, TransformDagResult, Vector, _add, _determinant,
    _matvec, _site_key, _subtract, build_transform_dag, expand_node)


@dataclass(frozen=True)
class DagSearchResult:
    system: str
    candidates: int
    represented_atoms: int
    marked_child_clusters: int
    atomic_candidate_decisions: int
    dag_candidate_decisions: int
    atomic_coordinate_evaluations: int
    dag_port_evaluations: int
    selected_expansion_atoms: int
    operation_reduction: float
    atomic_seconds: float
    dag_seconds: float
    wall_speedup: float
    atomic_selected_exact: bool
    dag_selected_exact: bool
    dag_best_score: int
    dag_correct_score: int


def _proper_axis_rotations() -> Tuple[Matrix, ...]:
    rotations = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            matrix: Matrix = tuple(tuple(
                signs[row] if permutation[row] == column else 0.0
                for column in range(3)) for row in range(3))  # type: ignore[assignment]
            if _determinant(matrix) > 0.5:
                rotations.append(matrix)
    return tuple(rotations)


def _transform_keyed(
    items: Sequence[Tuple[object, Vector]], matrix: Matrix, translation: Vector,
) -> set[Tuple[Tuple[int, int, int], object]]:
    return {(_site_key(_add(translation, _matvec(matrix, point))), label)
            for label, point in items}


def benchmark_dag_search(
    result: TransformDagResult,
    levels: Sequence[Sequence[DagNode]],
    *,
    candidate_count: int = 4096,
    seed: int = 71,
) -> DagSearchResult:
    root = levels[result.root_level - 1][result.root_type]
    leaves = tuple((chemical, point) for chemical, point in expand_node(
        levels, result.root_level, result.root_type))
    ports = tuple((child.child_type, child.translation)
                  for child in root.children)
    if not ports:
        raise ValueError("root has no child-cluster marking ports")
    atomic_target = _transform_keyed(
        leaves, ((1.0, 0.0, 0.0),
                 (0.0, 1.0, 0.0),
                 (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0))
    dag_target = _transform_keyed(
        ports, ((1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0))
    ports_by_type: Dict[int, list[Vector]] = {}
    for child_type, point in ports:
        ports_by_type.setdefault(child_type, []).append(point)
    identity: Matrix = ((1.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0),
                        (0.0, 0.0, 1.0))
    candidates = [(identity, (0.0, 0.0, 0.0))]
    rng = random.Random(seed)
    rotations = _proper_axis_rotations()
    for _ in range(candidate_count - 1):
        matrix = rng.choice(rotations)
        child_type, source = rng.choice(ports)
        target = rng.choice(ports_by_type[child_type])
        translation = _subtract(target, _matvec(matrix, source))
        candidates.append((matrix, translation))

    started = time.perf_counter()
    atomic_scores = [len(_transform_keyed(
        leaves, matrix, translation) & atomic_target)
        for matrix, translation in candidates]
    atomic_seconds = time.perf_counter() - started

    started = time.perf_counter()
    dag_scores = [len(_transform_keyed(
        ports, matrix, translation) & dag_target)
        for matrix, translation in candidates]
    dag_selected = max(range(len(candidates)), key=dag_scores.__getitem__)
    # Materialization is intentionally after selection.
    selected_leaves = _transform_keyed(
        leaves, *candidates[dag_selected])
    dag_seconds = time.perf_counter() - started
    atomic_selected = max(range(len(candidates)), key=atomic_scores.__getitem__)
    atomic_output = _transform_keyed(leaves, *candidates[atomic_selected])
    atomic_operations = len(candidates) * len(leaves)
    dag_operations = len(candidates) * len(ports) + len(leaves)
    return DagSearchResult(
        result.system,
        len(candidates),
        len(leaves),
        len(ports),
        len(leaves),
        1,
        atomic_operations,
        len(candidates) * len(ports),
        len(leaves),
        atomic_operations / dag_operations,
        atomic_seconds,
        dag_seconds,
        atomic_seconds / dag_seconds if dag_seconds else float("inf"),
        atomic_output == atomic_target,
        selected_leaves == atomic_target,
        max(dag_scores),
        dag_scores[0],
    )


def evaluate(candidate_count: int = 2048) -> Tuple[DagSearchResult, DagSearchResult]:
    from materials_gcts_icosahedral_modelset import oracle_patch
    from materials_pointset_benchmarks import crystalline_control
    crystal = crystalline_control(shell_radius=5)
    quasicrystal, _ = oracle_patch(3, 9.0)
    crystal_result, crystal_levels = build_transform_dag(
        crystal.name, crystal.positions, crystal.species)
    quasicrystal_result, quasicrystal_levels = build_transform_dag(
        quasicrystal.name, quasicrystal.positions, quasicrystal.species)
    return (
        benchmark_dag_search(
            crystal_result, crystal_levels,
            candidate_count=candidate_count, seed=71),
        benchmark_dag_search(
            quasicrystal_result, quasicrystal_levels,
            candidate_count=candidate_count, seed=73),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=int, default=2048)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.candidates)
    print(json.dumps([asdict(item) for item in result], indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
