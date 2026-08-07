#!/usr/bin/env python3
"""Exact transform-DAG representation for recursive material clusters.

Every parent is represented by complete child clusters, rigid transforms, and
uncovered residual atoms.  Children may be reused by many parents.  Expansion
is verified against the exact representative support, while search can inspect
the compact child graph before materializing atomic coordinates.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from statistics import median
from typing import Dict, Hashable, Optional, Sequence, Tuple

from materials_pointset_clusters import (
    ClusterLearningResult, ClusterType, learn_cluster_candidates,
    occurrence_type_labels)

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class ChildTransform:
    child_type: int
    translation: Vector
    rotation: Matrix
    orientation_sign: int


@dataclass(frozen=True)
class DagNode:
    level: int
    type_id: int
    support_atoms: int
    children: Tuple[ChildTransform, ...]
    residual_offsets: Tuple[Tuple[str, Vector], ...]


@dataclass(frozen=True)
class DagLevelResult:
    level: int
    radius: float
    cluster_types: int
    recurring_types: int
    largest_recurring_support: int
    largest_recurring_children: int
    largest_recurring_residuals: int
    dictionary_explicit_atoms: int
    dictionary_dag_entries: int
    improper_child_transforms: int


@dataclass(frozen=True)
class TransformDagResult:
    system: str
    atoms: int
    levels: Tuple[DagLevelResult, ...]
    root_level: int
    root_type: int
    represented_atoms: int
    root_dag_entries: int
    root_compression: float
    exact_expansion: bool
    support_amplification: Tuple[float, ...]


def _subtract(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def _add(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _scale(factor: float, vector: Sequence[float]) -> Vector:
    return tuple(factor * value for value in vector)  # type: ignore[return-value]


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _frame(first: Vector, second: Vector) -> Optional[Matrix]:
    length = _norm(first)
    if length < 1e-8:
        return None
    e1 = _scale(1.0 / length, first)
    remainder = _subtract(second, _scale(_dot(second, e1), e1))
    remainder_length = _norm(remainder)
    if remainder_length < 1e-8:
        return None
    e2 = _scale(1.0 / remainder_length, remainder)
    return e1, e2, _cross(e1, e2)


def _rank_one_frame(vector: Vector) -> Optional[Matrix]:
    length = _norm(vector)
    if length < 1e-8:
        return None
    e1 = _scale(1.0 / length, vector)
    reference = min(((1.0, 0.0, 0.0),
                     (0.0, 1.0, 0.0),
                     (0.0, 0.0, 1.0)),
                    key=lambda axis: abs(_dot(axis, e1)))
    remainder = _subtract(reference, _scale(_dot(reference, e1), e1))
    e2 = _scale(1.0 / _norm(remainder), remainder)
    return e1, e2, _cross(e1, e2)


def _rotation(source: Matrix, target: Matrix) -> Matrix:
    return tuple(tuple(sum(source[index][row] * target[index][column]
                           for index in range(3))
                       for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    return tuple(sum(vector[row] * matrix[row][column]
                     for row in range(3)) for column in range(3))  # type: ignore[return-value]


def _nearest_scale(points: Sequence[Vector]) -> float:
    return median(min(_norm(_subtract(point, other))
                      for other_index, other in enumerate(points)
                      if other_index != index)
                  for index, point in enumerate(points))


def _learn_levels(
    positions: Sequence[Vector], species: Sequence[Hashable],
    maximum_levels: int, radius_growth: float,
) -> Tuple[Tuple[float, ...], Tuple[ClusterLearningResult, ...],
           Tuple[Tuple[int, ...], ...]]:
    scale = _nearest_scale(positions)
    radii = tuple(scale * 1.08 * radius_growth ** level
                  for level in range(maximum_levels))
    results = []
    labels_by_level = []
    labels: Sequence[Hashable] = species
    for radius in radii:
        learned = learn_cluster_candidates(
            labels, positions, neighbor_count=None, radius=radius,
            descriptor_tolerance=1e-5, minimum_occurrences=1)
        learned = _split_by_exact_congruence(learned, labels, positions)
        labels = occurrence_type_labels(learned)
        results.append(learned)
        labels_by_level.append(tuple(labels))
    return radii, tuple(results), tuple(labels_by_level)


def _split_by_exact_congruence(
    learned: ClusterLearningResult,
    labels: Sequence[Hashable],
    positions: Sequence[Vector],
) -> ClusterLearningResult:
    refined = []
    for provisional in learned.cluster_types:
        if len(provisional.representative_members) > 80:
            refined.append(ClusterType(
                type_id=len(refined),
                center_species=provisional.center_species,
                signature=provisional.signature,
                representative_center=provisional.representative_center,
                representative_members=provisional.representative_members,
                representative_species=provisional.representative_species,
                representative_distances=provisional.representative_distances,
                occurrences=provisional.occurrences,
            ))
            continue
        groups = []
        for occurrence in provisional.occurrences:
            target_members = occurrence.member_indices
            target_center = occurrence.center_index
            target_offsets = tuple(
                _subtract(positions[index], positions[target_center])
                for index in target_members)
            target_labels = tuple(labels[index] for index in target_members)
            for representative, members in groups:
                center = representative.center_index
                source_offsets = tuple(
                    _subtract(positions[index], positions[center])
                    for index in representative.member_indices)
                source_labels = tuple(labels[index]
                                      for index in representative.member_indices)
                if _register_colored_supports(
                        source_offsets, source_labels,
                        target_offsets, target_labels,
                        allow_reflection=False) is not None:
                    members.append(occurrence)
                    break
            else:
                groups.append((occurrence, [occurrence]))
        for representative, occurrences in groups:
            members = representative.member_indices
            distances = tuple(tuple(_norm(_subtract(positions[left],
                                                     positions[right]))
                                    for right in members)
                              for left in members)
            refined.append(ClusterType(
                type_id=len(refined),
                center_species=labels[representative.center_index],
                signature=provisional.signature,
                representative_center=representative.center_index,
                representative_members=members,
                representative_species=tuple(labels[index]
                                             for index in members),
                representative_distances=distances,
                occurrences=tuple(occurrences),
            ))
    occurrences = tuple(occurrence for cluster_type in refined
                        for occurrence in cluster_type.occurrences)
    return ClusterLearningResult(
        learned.point_count, learned.minimum_distance,
        tuple(refined), occurrences)


def _occurrence_rotations(
    level: int,
    learned: ClusterLearningResult,
    input_labels: Sequence[Hashable],
    positions: Sequence[Vector],
) -> Dict[Tuple[int, int], Matrix]:
    rotations: Dict[Tuple[int, int], Matrix] = {}
    for cluster_type in learned.cluster_types:
        representative = cluster_type.representative_members
        center = representative[0]
        offsets = tuple(_subtract(positions[index], positions[center])
                        for index in representative)
        for occurrence in cluster_type.occurrences:
            target_center = occurrence.center_index
            target_offsets = tuple(
                _subtract(positions[index], positions[target_center])
                for index in occurrence.member_indices)
            rotation = _register_colored_supports(
                offsets,
                tuple(input_labels[index] for index in representative),
                target_offsets,
                tuple(input_labels[index]
                      for index in occurrence.member_indices),
                allow_reflection=False)
            if rotation is None:
                raise RuntimeError(
                    f"could not register level {level} type "
                    f"{cluster_type.type_id} at center {target_center}")
            rotations[(cluster_type.type_id, target_center)] = rotation
    return rotations


def _register_colored_supports(
    source_offsets: Sequence[Vector],
    source_labels: Sequence[Hashable],
    target_offsets: Sequence[Vector],
    target_labels: Sequence[Hashable],
    allow_reflection: bool = True,
) -> Optional[Matrix]:
    target_set = {(_site_key(offset), label)
                  for offset, label in zip(target_offsets, target_labels)}
    if len(source_offsets) == 1:
        return ((1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0))
    for first in range(1, len(source_offsets)):
        source_frame = _rank_one_frame(source_offsets[first])
        if source_frame is None:
            continue
        radius = _norm(source_offsets[first])
        for target_first in range(1, len(target_offsets)):
            if (target_labels[target_first] != source_labels[first] or
                    abs(_norm(target_offsets[target_first]) - radius) > 1e-5):
                continue
            target_frame = _rank_one_frame(target_offsets[target_first])
            if target_frame is None:
                continue
            rotation = _rotation(source_frame, target_frame)
            transformed = {
                (_site_key(_matvec(rotation, offset)), label)
                for offset, label in zip(source_offsets, source_labels)}
            if transformed == target_set:
                return rotation
    for first in range(1, len(source_offsets)):
        for second in range(1, len(source_offsets)):
            if first == second:
                continue
            source_frame = _frame(source_offsets[first], source_offsets[second])
            if source_frame is None:
                continue
            first_radius = _norm(source_offsets[first])
            second_radius = _norm(source_offsets[second])
            pair_distance = _norm(_subtract(source_offsets[first],
                                             source_offsets[second]))
            for target_first in range(1, len(target_offsets)):
                if (target_labels[target_first] != source_labels[first] or
                        abs(_norm(target_offsets[target_first]) -
                            first_radius) > 1e-5):
                    continue
                for target_second in range(1, len(target_offsets)):
                    if target_first == target_second:
                        continue
                    if (target_labels[target_second] != source_labels[second] or
                            abs(_norm(target_offsets[target_second]) -
                                second_radius) > 1e-5 or
                            abs(_norm(_subtract(target_offsets[target_first],
                                                target_offsets[target_second])) -
                                pair_distance) > 1e-5):
                        continue
                    target_frame = _frame(target_offsets[target_first],
                                          target_offsets[target_second])
                    if target_frame is None:
                        continue
                    candidate_frames = [target_frame]
                    if allow_reflection:
                        candidate_frames.append(
                            (target_frame[0], target_frame[1],
                             _scale(-1.0, target_frame[2])))
                    for candidate_frame in candidate_frames:
                        rotation = _rotation(source_frame, candidate_frame)
                        transformed = {
                            (_site_key(_matvec(rotation, offset)), label)
                            for offset, label in zip(source_offsets,
                                                     source_labels)}
                        if transformed == target_set:
                            return rotation
    return None


def build_transform_dag(
    system: str,
    positions: Sequence[Vector],
    species: Sequence[str],
    *,
    maximum_levels: int = 3,
    radius_growth: float = 2.2,
    prelearned: Optional[Tuple[
        Tuple[float, ...], Tuple[ClusterLearningResult, ...],
        Tuple[Tuple[int, ...], ...]]] = None,
) -> Tuple[TransformDagResult, Tuple[Tuple[DagNode, ...], ...]]:
    radii, learned_levels, labels_by_level = (
        prelearned if prelearned is not None else _learn_levels(
            positions, species, maximum_levels, radius_growth))
    nodes_by_level = []
    level_results = []
    largest_supports = []

    for level_index, learned in enumerate(learned_levels):
        nodes = []
        if level_index == 0:
            for cluster_type in learned.cluster_types:
                center = cluster_type.representative_center
                residuals = tuple(
                    (species[index], _subtract(positions[index], positions[center]))
                    for index in cluster_type.representative_members)
                nodes.append(DagNode(
                    1, cluster_type.type_id,
                    len(cluster_type.representative_members), (), residuals))
        else:
            child_learned = learned_levels[level_index - 1]
            child_labels = labels_by_level[level_index - 1]
            child_input_labels: Sequence[Hashable] = (
                species if level_index == 1
                else labels_by_level[level_index - 2])
            rotations = _occurrence_rotations(
                level_index, child_learned, child_input_labels, positions)
            occurrences_by_center = {}
            for child_type in child_learned.cluster_types:
                for occurrence in child_type.occurrences:
                    occurrences_by_center[occurrence.center_index] = (
                        child_type.type_id, occurrence)
            for cluster_type in learned.cluster_types:
                parent_center = cluster_type.representative_center
                parent_support = set(cluster_type.representative_members)
                candidates = []
                for child_center in parent_support:
                    child = occurrences_by_center.get(child_center)
                    if child is None:
                        continue
                    child_type, occurrence = child
                    child_support = set(occurrence.member_indices)
                    if not child_support.issubset(parent_support):
                        continue
                    candidates.append((child_type, child_center,
                                       frozenset(child_support)))
                uncovered = set(parent_support)
                selected = []
                while candidates:
                    best = max(candidates,
                               key=lambda item: len(item[2] & uncovered))
                    gain = len(best[2] & uncovered)
                    if gain <= 1:
                        break
                    selected.append(best)
                    uncovered.difference_update(best[2])
                    candidates.remove(best)
                children = tuple(ChildTransform(
                    child_type=child_type,
                    translation=_subtract(positions[child_center],
                                          positions[parent_center]),
                    rotation=rotations[(child_type, child_center)],
                    orientation_sign=(1 if _determinant(
                        rotations[(child_type, child_center)]) > 0 else -1),
                ) for child_type, child_center, _ in selected)
                residuals = tuple(
                    (species[index], _subtract(positions[index],
                                                positions[parent_center]))
                    for index in sorted(uncovered))
                nodes.append(DagNode(
                    level_index + 1, cluster_type.type_id,
                    len(parent_support), children, residuals))
        nodes_tuple = tuple(nodes)
        nodes_by_level.append(nodes_tuple)
        recurring = [cluster_type for cluster_type in learned.cluster_types
                     if len(cluster_type.occurrences) >= 2]
        largest = max(recurring,
                      key=lambda item: len(item.representative_members),
                      default=None)
        largest_node = (nodes_tuple[largest.type_id]
                        if largest is not None else None)
        largest_support = (len(largest.representative_members)
                           if largest is not None else 0)
        largest_supports.append(largest_support)
        level_results.append(DagLevelResult(
            level_index + 1,
            radii[level_index],
            len(learned.cluster_types),
            len(recurring),
            largest_support,
            len(largest_node.children) if largest_node else 0,
            len(largest_node.residual_offsets) if largest_node else 0,
            sum(len(item.representative_members)
                for item in learned.cluster_types),
            sum(len(node.children) + len(node.residual_offsets)
                for node in nodes_tuple),
            sum(child.orientation_sign < 0 for node in nodes_tuple
                for child in node.children),
        ))

    top_recurring = [item for item in learned_levels[-1].cluster_types
                     if len(item.occurrences) >= 2]
    root_type = max(top_recurring,
                    key=lambda item: len(item.representative_members))
    root = nodes_by_level[-1][root_type.type_id]
    expanded = expand_node(nodes_by_level, maximum_levels, root.type_id)
    center = positions[root_type.representative_center]
    expected = {(_site_key(_subtract(positions[index], center)), species[index])
                for index in root_type.representative_members}
    actual = {(_site_key(offset), chemical)
              for chemical, offset in expanded}
    support_amplification = tuple(
        largest_supports[index] / largest_supports[index - 1]
        if largest_supports[index - 1] else 0.0
        for index in range(1, len(largest_supports)))
    result = TransformDagResult(
        system, len(positions), tuple(level_results), maximum_levels,
        root.type_id, len(expected),
        len(root.children) + len(root.residual_offsets),
        len(expected) / max(1, len(root.children) + len(root.residual_offsets)),
        actual == expected, support_amplification)
    return result, tuple(nodes_by_level)


def _site_key(point: Sequence[float], tolerance: float = 1e-5) -> Tuple[int, int, int]:
    return tuple(round(value / tolerance) for value in point)  # type: ignore[return-value]


def _determinant(matrix: Matrix) -> float:
    return _dot(matrix[0], _cross(matrix[1], matrix[2]))


def expand_node(
    levels: Sequence[Sequence[DagNode]], level: int, type_id: int,
) -> Tuple[Tuple[str, Vector], ...]:
    node = levels[level - 1][type_id]
    atoms: Dict[Tuple[Tuple[int, int, int], str], Tuple[str, Vector]] = {}
    for chemical, offset in node.residual_offsets:
        atoms[(_site_key(offset), chemical)] = (chemical, offset)
    for child in node.children:
        for chemical, child_offset in expand_node(
                levels, level - 1, child.child_type):
            offset = _add(child.translation,
                          _matvec(child.rotation, child_offset))
            atoms[(_site_key(offset), chemical)] = (chemical, offset)
    return tuple(atoms.values())


def evaluate() -> Tuple[TransformDagResult, TransformDagResult]:
    from materials_gcts_icosahedral_modelset import oracle_patch
    from materials_pointset_benchmarks import crystalline_control
    crystal = crystalline_control(shell_radius=5)
    quasicrystal, _ = oracle_patch(3, 9.0)
    return (
        build_transform_dag(
            crystal.name, crystal.positions, crystal.species)[0],
        build_transform_dag(
            quasicrystal.name, quasicrystal.positions,
            quasicrystal.species)[0],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps([asdict(item) for item in result], indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
