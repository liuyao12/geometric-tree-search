#!/usr/bin/env python3
"""First integrated experiment for hierarchical overlapping point-set covers.

This joins the deliberately separate layers:

1. learn rotation-invariant local cluster candidates from colored Cartesian
   points;
2. enumerate complete colored distance-graph embeddings of a learned type;
3. select a globally complete, potentially overlapping cover with GCTS;
4. replace selected occurrences by colored centers and run the learner again.

Generator metadata is used only to score the planted non-lattice benchmark.
No lattice, unit cell, or planted occurrence is passed to either learner or
cover solver.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Dict, Sequence, Tuple

from materials_overlap_cover import Occurrence, OverlapCoverProblem
from materials_pointset_benchmarks import (
    ColoredPointSet,
    amorphous_hard_core_point_set,
    crystalline_control,
    overlapping_motif_point_set,
    random_rotation,
)
from materials_pointset_clusters import (
    ClusterOccurrence,
    ClusterType,
    enumerate_type_occurrences,
    learn_cluster_candidates,
)


@dataclass(frozen=True)
class CrystalResult:
    atoms: int
    level1_types: int
    level1_recurring_types: int
    rotation_invariant: bool
    greedy_cover_occurrences: int
    coarse_objects: int
    level2_recurring_types: int
    level2_recurring_occurrences: int
    exact_control_atoms: int
    exact_control_greedy_occurrences: int
    exact_control_occurrences: int
    exact_control_expanded_nodes: int
    exact_control_backtracks: int


@dataclass(frozen=True)
class NonLatticeCoverResult:
    atoms: int
    planted_occurrences: int
    nearest_support_seed_occurrences: int
    enumerated_occurrences: int
    occurrence_precision: float
    occurrence_recall: float
    cover_complete: bool
    selected_occurrences: int
    overlap_excess_memberships: int
    multiply_covered_atoms: int
    overlap_required: bool
    expanded_nodes: int
    backtracks: int
    level2_objects: int
    level2_recurring_types: int


@dataclass(frozen=True)
class AmorphousResult:
    atoms: int
    singleton_types: int
    recurring_types: int
    recurring_occurrences: int


@dataclass(frozen=True)
class IntegratedResult:
    crystal: CrystalResult
    non_lattice_cover: NonLatticeCoverResult
    amorphous_null: AmorphousResult


def _matvec(matrix: Sequence[Sequence[float]], point: Sequence[float]) -> Tuple[float, float, float]:
    return tuple(sum(matrix[row][column] * point[column] for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _rigid_copy(point_set: ColoredPointSet) -> ColoredPointSet:
    rotation = random_rotation(random.Random(991))
    translation = (7.25, -3.5, 2.125)
    positions = tuple(tuple(value + translation[axis]
                            for axis, value in enumerate(_matvec(rotation, point)))
                      for point in point_set.positions)
    return ColoredPointSet(point_set.name + "-rigid-copy", positions,
                           point_set.species)


def _indexed_occurrences(cluster_types: Sequence[ClusterType]) -> Tuple[Tuple[Occurrence, ...], Dict[int, Tuple[ClusterType, ClusterOccurrence]]]:
    cover_occurrences = []
    lookup: Dict[int, Tuple[ClusterType, ClusterOccurrence]] = {}
    for cluster_type in cluster_types:
        for cluster_occurrence in cluster_type.occurrences:
            identifier = len(cover_occurrences)
            cover_occurrences.append(Occurrence(
                identifier, cluster_occurrence.member_indices))
            lookup[identifier] = (cluster_type, cluster_occurrence)
    return tuple(cover_occurrences), lookup


def evaluate_crystal() -> CrystalResult:
    sample = crystalline_control()
    learned = learn_cluster_candidates(
        sample.species, sample.positions, neighbor_count=6,
        descriptor_tolerance=1e-5)
    moved = _rigid_copy(sample)
    moved_learned = learn_cluster_candidates(
        moved.species, moved.positions, neighbor_count=6,
        descriptor_tolerance=1e-5)
    rotation_invariant = (
        tuple(item.signature for item in learned.cluster_types)
        == tuple(item.signature for item in moved_learned.cluster_types)
        and tuple(len(item.occurrences) for item in learned.cluster_types)
        == tuple(len(item.occurrences) for item in moved_learned.cluster_types)
    )

    occurrences, lookup = _indexed_occurrences(learned.cluster_types)
    greedy = OverlapCoverProblem(range(len(sample.positions)), occurrences).greedy()
    coarse_points = tuple(
        sample.positions[lookup[identifier][1].center_index]
        for identifier in greedy.selected)
    coarse_species = tuple(
        f"C{lookup[identifier][0].type_id}"
        for identifier in greedy.selected)
    coarse = learn_cluster_candidates(
        coarse_species, coarse_points, neighbor_count=2,
        minimum_occurrences=2, descriptor_tolerance=1e-5)

    # A 33-atom crop is small enough to certify the optimum exactly.  The
    # hundred-atom crop above is intentionally kept as a greedy/GCTS-policy
    # benchmark until stronger markings and learned ordering are connected.
    exact_sample = crystalline_control(shell_radius=2)
    exact_learned = learn_cluster_candidates(
        exact_sample.species, exact_sample.positions, neighbor_count=6,
        descriptor_tolerance=1e-5)
    exact_occurrences, _ = _indexed_occurrences(exact_learned.cluster_types)
    exact_problem = OverlapCoverProblem(
        range(len(exact_sample.positions)), exact_occurrences)
    exact_greedy = exact_problem.greedy()
    exact = exact_problem.solve()

    return CrystalResult(
        atoms=len(sample.positions),
        level1_types=len(learned.cluster_types),
        level1_recurring_types=sum(
            len(item.occurrences) > 1 for item in learned.cluster_types),
        rotation_invariant=rotation_invariant,
        greedy_cover_occurrences=len(greedy.selected),
        coarse_objects=len(coarse_points),
        level2_recurring_types=len(coarse.cluster_types),
        level2_recurring_occurrences=len(coarse.occurrences),
        exact_control_atoms=len(exact_sample.positions),
        exact_control_greedy_occurrences=len(exact_greedy.selected),
        exact_control_occurrences=len(exact.selected),
        exact_control_expanded_nodes=exact.expanded_nodes,
        exact_control_backtracks=exact.backtracks,
    )


def _silica_type(sample: ColoredPointSet) -> Tuple[ClusterType, int]:
    seeds = learn_cluster_candidates(
        sample.species, sample.positions, neighbor_count=4,
        minimum_occurrences=2, descriptor_tolerance=1e-5)
    candidates = [
        item for item in seeds.cluster_types
        if item.center_species == "Si" and len(item.representative_members) == 5
    ]
    if not candidates:
        raise RuntimeError("no recurring Si-centered five-atom seed was learned")
    result = max(candidates, key=lambda item: len(item.occurrences))
    return result, len(result.occurrences)


def evaluate_non_lattice_cover() -> NonLatticeCoverResult:
    sample = overlapping_motif_point_set()
    cluster_type, seed_occurrences = _silica_type(sample)
    embeddings = enumerate_type_occurrences(
        cluster_type, sample.species, sample.positions,
        distance_tolerance=1e-5)

    learned_supports = {frozenset(item.member_indices) for item in embeddings}
    planted_supports = {
        frozenset(item.atom_indices) for item in sample.motif_occurrences
    }
    true_positives = len(learned_supports & planted_supports)
    precision = true_positives / len(learned_supports) if learned_supports else 0.0
    recall = true_positives / len(planted_supports) if planted_supports else 0.0

    cover_occurrences = tuple(
        Occurrence(index, item.member_indices)
        for index, item in enumerate(embeddings))
    result = OverlapCoverProblem(
        range(len(sample.positions)), cover_occurrences).solve()
    selected = [embeddings[index] for index in result.selected]
    memberships = Counter(
        atom for occurrence in selected for atom in occurrence.member_indices)
    overlap_excess = sum(memberships.values()) - len(memberships)
    multiply_covered = sum(count > 1 for count in memberships.values())

    coarse_points = tuple(
        sample.positions[item.center_index] for item in selected)
    coarse_species = ("SiO4",) * len(coarse_points)
    coarse = learn_cluster_candidates(
        coarse_species, coarse_points, neighbor_count=3,
        minimum_occurrences=2, descriptor_tolerance=1e-5)

    # Every candidate contains exactly one distinct silicon center.  Covering
    # all silicon atoms therefore forces every occurrence; shared oxygens make
    # a partition impossible for this candidate dictionary.
    overlap_required = (
        result.complete
        and len(result.selected) == len(embeddings)
        and overlap_excess > 0
    )
    return NonLatticeCoverResult(
        atoms=len(sample.positions),
        planted_occurrences=len(planted_supports),
        nearest_support_seed_occurrences=seed_occurrences,
        enumerated_occurrences=len(embeddings),
        occurrence_precision=precision,
        occurrence_recall=recall,
        cover_complete=result.complete,
        selected_occurrences=len(result.selected),
        overlap_excess_memberships=overlap_excess,
        multiply_covered_atoms=multiply_covered,
        overlap_required=overlap_required,
        expanded_nodes=result.expanded_nodes,
        backtracks=result.backtracks,
        level2_objects=len(coarse_points),
        level2_recurring_types=len(coarse.cluster_types),
    )


def evaluate_amorphous_null() -> AmorphousResult:
    sample = amorphous_hard_core_point_set()
    all_types = learn_cluster_candidates(
        sample.species, sample.positions, neighbor_count=6,
        descriptor_tolerance=1e-5)
    recurring = learn_cluster_candidates(
        sample.species, sample.positions, neighbor_count=6,
        minimum_occurrences=2, descriptor_tolerance=1e-5)
    return AmorphousResult(
        atoms=len(sample.positions),
        singleton_types=len(all_types.cluster_types),
        recurring_types=len(recurring.cluster_types),
        recurring_occurrences=len(recurring.occurrences),
    )


def evaluate() -> IntegratedResult:
    return IntegratedResult(
        crystal=evaluate_crystal(),
        non_lattice_cover=evaluate_non_lattice_cover(),
        amorphous_null=evaluate_amorphous_null(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    if arguments.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(result)


if __name__ == "__main__":
    main()
