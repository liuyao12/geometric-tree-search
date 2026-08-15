#!/usr/bin/env python3
"""Compile discovered irregular supports into finite oriented GCTS ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_supports import (
    FrozenSupportVocabulary, IrregularCover, enumerate_frozen_vocabulary,
    fit_frozen_vocabulary)
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, ClusterPrototype, PortAtlas, fit_occurrence_pose,
    learn_overlap_ports, make_prototype)


@dataclass(frozen=True)
class IrregularPortProgram:
    cover: IrregularCover
    vocabulary: FrozenSupportVocabulary
    prototypes: tuple[ClusterPrototype, ...]
    prototype_support_types: tuple[tuple[int, int], ...]
    occurrences: tuple[ClusterOccurrence, ...]
    occurrence_supports: tuple[tuple[int, tuple[int, ...]], ...]
    atlas: PortAtlas
    pose_fit_failures: int
    candidate_overlap_relations: int
    minimum_shared_atoms: int
    family_label_used: bool
    lattice_used: bool
    physical_potential_used: bool


@dataclass(frozen=True)
class FrozenPortEnumeration:
    occurrences: tuple[ClusterOccurrence, ...]
    occurrence_supports: tuple[tuple[int, tuple[int, ...]], ...]
    candidate_overlap_relations: int
    recognized_support_occurrences: int
    pose_fit_failures: int


def compile_irregular_port_program(
    species: Sequence[Hashable], positions: Sequence[Sequence[float]], *,
    support_tolerance: float = .02, pose_tolerance: float = .03,
    minimum_shared_atoms: int = 2,
) -> IrregularPortProgram:
    """Discover supports, fit proper poses, and quotient witnessed overlaps.

    Only repeated non-collinear support types enter the oriented atlas. Gap
    terminals remain in the exact cover but have no invented continuous frame.
    Candidate occurrence relations are restricted to pairs whose observed
    index supports actually share ``minimum_shared_atoms`` input sites.
    """
    if minimum_shared_atoms < 1:
        raise ValueError("minimum_shared_atoms must be positive")
    points = tuple(tuple(float(value) for value in point)
                   for point in positions)
    vocabulary, cover = fit_frozen_vocabulary(
        species, points, distance_tolerance=support_tolerance)
    prototypes = []
    prototype_support_types = []
    occurrences = []
    occurrence_supports = []
    failures = 0
    next_occurrence_id = 0
    next_prototype_id = 0
    for support_type in cover.support_types:
        if support_type.kind != "repeated" or support_type.support_size < 3:
            continue
        # A colored distance graph does not distinguish enantiomers. Split the
        # metric class into proper-congruence subclasses here so a reflection
        # is never silently encoded as a rotation or discarded from coverage.
        proper_subtypes: list[ClusterPrototype] = []
        for occurrence in support_type.occurrences:
            observed = tuple((species[index], points[index])
                             for index in occurrence.member_indices)
            fitted = None
            for prototype in proper_subtypes:
                try:
                    fitted = fit_occurrence_pose(
                        next_occurrence_id, prototype, observed,
                        tolerance=pose_tolerance)
                    break
                except ValueError:
                    continue
            if fitted is None:
                try:
                    prototype = make_prototype(
                        next_prototype_id, observed,
                        tolerance=pose_tolerance)
                    fitted = fit_occurrence_pose(
                        next_occurrence_id, prototype, observed,
                        tolerance=pose_tolerance)
                except ValueError:
                    failures += 1
                    continue
                proper_subtypes.append(prototype)
                prototypes.append(prototype)
                prototype_support_types.append(
                    (prototype.type_id, support_type.type_id))
                next_prototype_id += 1
            if fitted is None:
                failures += 1
                continue
            occurrences.append(fitted)
            occurrence_supports.append(
                (next_occurrence_id, occurrence.member_indices))
            next_occurrence_id += 1

    support_by_id = dict(occurrence_supports)
    allowed = frozenset(
        (parent.occurrence_id, child.occurrence_id)
        for parent in occurrences for child in occurrences
        if parent.occurrence_id != child.occurrence_id and
        len(set(support_by_id[parent.occurrence_id]).intersection(
            support_by_id[child.occurrence_id])) >= minimum_shared_atoms)
    atlas = learn_overlap_ports(
        tuple(prototypes), tuple(occurrences),
        minimum_overlap=minimum_shared_atoms,
        minimum_observations=2,
        overlap_tolerance=pose_tolerance,
        exclusion_distance=max(pose_tolerance, cover.minimum_distance * .45),
        allowed_occurrence_pairs=allowed)
    return IrregularPortProgram(
        cover, vocabulary, tuple(prototypes),
        tuple(prototype_support_types), tuple(occurrences),
        tuple(occurrence_supports), atlas, failures, len(allowed),
        minimum_shared_atoms, False, False, False)


def enumerate_frozen_port_occurrences(
    program: IrregularPortProgram,
    species: Sequence[Hashable], positions: Sequence[Sequence[float]], *,
    pose_tolerance: float = .03, maximum_per_support_type: int | None = None,
    select_greedy_cover: bool = False,
) -> FrozenPortEnumeration:
    """Fit only train-frozen proper prototypes to target support embeddings."""
    if maximum_per_support_type is not None and maximum_per_support_type < 1:
        raise ValueError("maximum_per_support_type must be positive")
    points = tuple(tuple(float(value) for value in point)
                   for point in positions)
    frozen = enumerate_frozen_vocabulary(
        program.vocabulary, species, points)
    selected_by_type = None
    if select_greedy_cover:
        remaining = set(frozen.covered_indices)
        candidates = [
            (type_index, occurrence)
            for type_index, group in enumerate(frozen.occurrences_by_type)
            for occurrence in group]
        selected_by_type = {index: [] for index in
                            range(len(frozen.occurrences_by_type))}
        while remaining:
            type_index, occurrence = max(
                candidates,
                key=lambda item: (
                    len(set(item[1].member_indices).intersection(remaining)),
                    len(item[1].member_indices), -item[0],
                    tuple(-index for index in item[1].member_indices)),
                default=(-1, None))
            if occurrence is None:
                break
            gain = set(occurrence.member_indices).intersection(remaining)
            if not gain:
                break
            selected_by_type[type_index].append(occurrence)
            remaining.difference_update(gain)
            candidates.remove((type_index, occurrence))
    prototypes = {prototype.type_id: prototype
                  for prototype in program.prototypes}
    by_support_type: dict[int, list[ClusterPrototype]] = {}
    for prototype_id, support_type in program.prototype_support_types:
        by_support_type.setdefault(support_type, []).append(
            prototypes[prototype_id])
    occurrences = []
    supports = []
    failures = 0
    next_id = 0
    for type_index, (frozen_prototype, group) in enumerate(zip(
            program.vocabulary.prototypes, frozen.occurrences_by_type)):
        source_group = (selected_by_type[type_index]
                        if selected_by_type is not None else group)
        candidates = tuple(source_group[:maximum_per_support_type]
                           if maximum_per_support_type is not None
                           else source_group)
        for occurrence in candidates:
            observed = tuple((species[index], points[index])
                             for index in occurrence.member_indices)
            fitted = None
            for prototype in by_support_type.get(
                    frozen_prototype.type_id, ()):
                try:
                    fitted = fit_occurrence_pose(
                        next_id, prototype, observed,
                        tolerance=pose_tolerance)
                    break
                except ValueError:
                    continue
            if fitted is None:
                failures += 1
                continue
            occurrences.append(fitted)
            supports.append((next_id, occurrence.member_indices))
            next_id += 1
    support_by_id = dict(supports)
    relations = sum(
        parent.occurrence_id != child.occurrence_id and
        len(set(support_by_id[parent.occurrence_id]).intersection(
            support_by_id[child.occurrence_id])) >= program.minimum_shared_atoms
        for parent in occurrences for child in occurrences)
    return FrozenPortEnumeration(
        tuple(occurrences), tuple(supports), relations,
        sum(len(group) for group in frozen.occurrences_by_type), failures)


def compile_frozen_target_atlas(
    program: IrregularPortProgram,
    enumeration: FrozenPortEnumeration, *, pose_tolerance: float = .03,
) -> PortAtlas:
    """Score target relations using the frozen prototypes and port schema."""
    support_by_id = dict(enumeration.occurrence_supports)
    allowed = frozenset(
        (parent.occurrence_id, child.occurrence_id)
        for parent in enumeration.occurrences
        for child in enumeration.occurrences
        if parent.occurrence_id != child.occurrence_id and
        len(set(support_by_id[parent.occurrence_id]).intersection(
            support_by_id[child.occurrence_id])) >= program.minimum_shared_atoms)
    return learn_overlap_ports(
        program.prototypes, enumeration.occurrences,
        minimum_overlap=program.minimum_shared_atoms,
        minimum_observations=1, overlap_tolerance=pose_tolerance,
        exclusion_distance=max(
            pose_tolerance, program.cover.minimum_distance * .45),
        allowed_occurrence_pairs=allowed)
