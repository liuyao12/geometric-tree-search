#!/usr/bin/env python3
"""Promote exact port-graph macros into the next generic GCTS level.

No prescribed scale or family knowledge enters promotion.  Each ``MacroType``
atom union becomes a centered colored point-set prototype.  Its retained
training embeddings are independently re-rendered from child cluster poses and
registered by a proper rigid motion.  Shared training atom indices define the
next overlap atlas.  Witnessed cross-boundary child-port relations additionally
define finite boundary ports, including non-overlapping macro pairs.

``PromotedMacroProgram`` deliberately exposes the prototype/occurrence/support/
atlas/minimum-overlap contract consumed by ``reduce_occurrence_graph`` and
``mine_port_graph_macros``; it can therefore be promoted again without a
material-specific adapter.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_port_atlas import IrregularPortProgram
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, ClusterPrototype, Matrix, PortAtlas, Vector,
    canonical_relative_pose, fit_occurrence_pose, is_proper_rotation,
    learn_overlap_ports, make_prototype, matmul, matvec, transpose)
from materials_gcts_port_graph_macros import MacroType

Site = tuple[Hashable, Vector]


@dataclass(frozen=True)
class MacroBoundaryPort:
    parent_type: int
    child_type: int
    relative_rotation: Matrix
    relative_translation: Vector
    symmetry_orbit_key: tuple[int, ...]
    occurrence_observations: int
    child_port_witnesses: int


@dataclass(frozen=True)
class MacroBoundaryRelation:
    parent_occurrence: int
    child_occurrence: int
    parent_type: int
    child_type: int
    symmetry_orbit_key: tuple[int, ...]
    child_port_witnesses: int


@dataclass(frozen=True)
class PromotedMacroProgram:
    level: int
    source_macro_types: int
    prototypes: tuple[ClusterPrototype, ...]
    prototype_macro_types: tuple[tuple[int, int], ...]
    occurrences: tuple[ClusterOccurrence, ...]
    occurrence_supports: tuple[tuple[int, tuple[int, ...]], ...]
    atlas: PortAtlas
    boundary_ports: tuple[MacroBoundaryPort, ...]
    boundary_relation_classes: tuple[MacroBoundaryRelation, ...]
    minimum_shared_atoms: int
    minimum_distance: float
    prototype_failures: int
    pose_fit_failures: int
    conflicting_atom_unions: int
    family_label_used: bool
    lattice_used: bool
    physical_potential_used: bool
    target_used: bool


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(left[axis] + right[axis] for axis in range(3))  # type: ignore[return-value]


def _subtract(left: Vector, right: Vector) -> Vector:
    return tuple(left[axis] - right[axis] for axis in range(3))  # type: ignore[return-value]


def _render_occurrence(
    occurrence: ClusterOccurrence, prototype: ClusterPrototype,
) -> tuple[Site, ...]:
    return tuple((species, _add(
        matvec(occurrence.rotation, point), occurrence.translation))
        for species, point in prototype.sites)


def _render_macro_embedding(
    node_occurrences: Sequence[int], atomic_occurrences,
    atomic_prototypes, tolerance: float,
) -> tuple[Site, ...] | None:
    sites = {}
    positions = {}
    for occurrence_id in node_occurrences:
        occurrence = atomic_occurrences[occurrence_id]
        for species, point in _render_occurrence(
                occurrence, atomic_prototypes[occurrence.type_id]):
            coordinate = tuple(round(value / tolerance) for value in point)
            if coordinate in sites and sites[coordinate] != species:
                return None
            sites[coordinate] = species
            positions.setdefault(coordinate, point)
    return tuple((sites[key], positions[key]) for key in sorted(sites))


def _relative(parent: ClusterOccurrence,
              child: ClusterOccurrence) -> tuple[Matrix, Vector]:
    inverse = transpose(parent.rotation)
    return (matmul(inverse, child.rotation),
            matvec(inverse, _subtract(
                child.translation, parent.translation)))


def _fit_boundary_ports(
    atomic_program: IrregularPortProgram,
    prototypes: Sequence[ClusterPrototype],
    occurrences: Sequence[ClusterOccurrence],
    macro_nodes: dict[int, frozenset[int]],
    *, tolerance: float, minimum_observations: int,
) -> tuple[tuple[MacroBoundaryPort, ...],
           tuple[MacroBoundaryRelation, ...]]:
    admitted_atomic = {
        (port.parent_type, port.child_type, port.symmetry_orbit_key)
        for port in atomic_program.atlas.ports}
    membership: dict[int, list[int]] = {}
    for macro_occurrence, nodes in macro_nodes.items():
        for node in nodes:
            membership.setdefault(node, []).append(macro_occurrence)
    witness_counts = Counter()
    for parent, child, parent_type, child_type, pose_key in (
            atomic_program.atlas.relation_classes):
        if (parent_type, child_type, pose_key) not in admitted_atomic:
            continue
        for parent_macro in membership.get(parent, ()):
            for child_macro in membership.get(child, ()):
                if parent_macro != child_macro:
                    witness_counts[(parent_macro, child_macro)] += 1
    occurrence_by_id = {item.occurrence_id: item for item in occurrences}
    prototype_by_id = {item.type_id: item for item in prototypes}
    grouped = {}
    raw_relations = []
    for (parent_id, child_id), witnesses in sorted(witness_counts.items()):
        parent = occurrence_by_id[parent_id]
        child = occurrence_by_id[child_id]
        rotation, translation = _relative(parent, child)
        canonical_rotation, canonical_translation, key = (
            canonical_relative_pose(
                prototype_by_id[parent.type_id],
                prototype_by_id[child.type_id], rotation, translation,
                tolerance))
        group_key = parent.type_id, child.type_id, key
        if group_key not in grouped:
            grouped[group_key] = [canonical_rotation,
                                  canonical_translation, 0, 0]
        grouped[group_key][2] += 1
        grouped[group_key][3] += witnesses
        raw_relations.append((parent_id, child_id, parent.type_id,
                              child.type_id, key, witnesses, group_key))
    ports = []
    admitted = set()
    for group_key in sorted(grouped, key=repr):
        rotation, translation, observations, witnesses = grouped[group_key]
        if observations < minimum_observations:
            continue
        parent_type, child_type, key = group_key
        ports.append(MacroBoundaryPort(
            parent_type, child_type, rotation, translation, key,
            observations, witnesses))
        admitted.add(group_key)
    relations = tuple(MacroBoundaryRelation(*relation[:6])
                      for relation in raw_relations
                      if relation[6] in admitted)
    return tuple(ports), relations


def promote_macro_types(
    atomic_program: IrregularPortProgram,
    macro_types: Sequence[MacroType], *, level: int = 1,
    pose_tolerance: float = .03, minimum_shared_atoms: int = 2,
    minimum_port_observations: int = 2,
) -> PromotedMacroProgram:
    """Compile exact retained macros into a generic next-level program."""
    if level < 1:
        raise ValueError("promoted hierarchy levels start at one")
    if pose_tolerance <= 0:
        raise ValueError("pose tolerance must be positive")
    if minimum_shared_atoms < 1 or minimum_port_observations < 1:
        raise ValueError("overlap and observation minima must be positive")
    atomic_occurrences = {item.occurrence_id: item
                          for item in atomic_program.occurrences}
    atomic_prototypes = {item.type_id: item
                         for item in atomic_program.prototypes}
    prototypes = []
    prototype_macro_types = []
    occurrences = []
    supports = []
    macro_nodes = {}
    prototype_failures = pose_failures = conflicts = 0
    next_occurrence = 0
    for macro in macro_types:
        try:
            prototype = make_prototype(
                len(prototypes), macro.atom_union,
                tolerance=pose_tolerance)
        except ValueError:
            prototype_failures += 1
            continue
        fitted_for_type = []
        for macro_occurrence in macro.occurrences:
            observed = _render_macro_embedding(
                macro_occurrence.node_occurrences, atomic_occurrences,
                atomic_prototypes, pose_tolerance)
            if observed is None:
                conflicts += 1
                continue
            try:
                fitted = fit_occurrence_pose(
                    next_occurrence, prototype, observed,
                    tolerance=pose_tolerance)
            except ValueError:
                pose_failures += 1
                continue
            fitted_for_type.append((fitted, macro_occurrence))
            next_occurrence += 1
        if len(fitted_for_type) < 2:
            pose_failures += len(fitted_for_type)
            next_occurrence -= len(fitted_for_type)
            continue
        prototypes.append(prototype)
        prototype_macro_types.append((prototype.type_id, macro.macro_id))
        for fitted, macro_occurrence in fitted_for_type:
            # If an earlier macro was discarded, occurrence ids are already
            # contiguous because its provisional ids were rolled back.
            fitted = ClusterOccurrence(
                len(occurrences), prototype.type_id,
                fitted.rotation, fitted.translation)
            occurrences.append(fitted)
            supports.append((fitted.occurrence_id,
                             macro_occurrence.atom_indices))
            macro_nodes[fitted.occurrence_id] = frozenset(
                macro_occurrence.node_occurrences)
    support_by_id = dict(supports)
    allowed = frozenset(
        (parent.occurrence_id, child.occurrence_id)
        for parent in occurrences for child in occurrences
        if parent.occurrence_id != child.occurrence_id and
        len(set(support_by_id[parent.occurrence_id]).intersection(
            support_by_id[child.occurrence_id])) >= minimum_shared_atoms)
    minimum_distance = getattr(
        atomic_program, "minimum_distance", getattr(
            getattr(atomic_program, "cover", None), "minimum_distance",
            pose_tolerance * 2))
    atlas = learn_overlap_ports(
        tuple(prototypes), tuple(occurrences),
        minimum_overlap=minimum_shared_atoms,
        minimum_observations=minimum_port_observations,
        overlap_tolerance=pose_tolerance,
        exclusion_distance=max(pose_tolerance, minimum_distance * .45),
        allowed_occurrence_pairs=allowed)
    boundary_ports, boundary_relations = _fit_boundary_ports(
        atomic_program, prototypes, occurrences, macro_nodes,
        tolerance=pose_tolerance,
        minimum_observations=minimum_port_observations)
    return PromotedMacroProgram(
        level, len(macro_types), tuple(prototypes),
        tuple(prototype_macro_types), tuple(occurrences), tuple(supports),
        atlas, boundary_ports, boundary_relations, minimum_shared_atoms,
        minimum_distance, prototype_failures, pose_failures, conflicts,
        False, False, False, False)
