#!/usr/bin/env python3
"""Progressive semantic-field audit for promoted macro stationarity."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Sequence

from materials_gcts_macro_stationary_adapter import (
    adapt_macro_type, prototype_semantics)
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionBoundary, ProductionChild,
    audit_chemical_population_substitution, canonicalize_production)


@dataclass(frozen=True)
class FieldIntersection:
    field: str
    keys_by_level: tuple[int, ...]
    adjacent_intersections: tuple[int, ...]
    consecutive_three_level_intersections: tuple[int, ...]


@dataclass(frozen=True)
class StationaryFieldAblation:
    levels: tuple[int, ...]
    records_by_level: tuple[int, ...]
    fields: tuple[FieldIntersection, ...]
    first_failing_field: str | None
    pose_adaptation_rejections: int
    population_adjacent_compatible_pairs: int
    population_three_level_equal_substitution_triples: int
    population_substitution_matrices: tuple[tuple[tuple[int, ...], ...], ...]
    reusable_pre_pose_three_level_keys: int
    topology_three_level_maximum_minimum_occurrences: int
    topology_three_level_meets_sixteen_deployments_each_level: bool
    strict_stationarity_claimed: bool
    target_family_phi_cell_used: bool


def _species(value):
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _species_role(semantic):
    return tuple(species for species, _ in semantic.chemical_population)


def _species_from_reduced(values):
    return tuple(value.rsplit("*", 1)[0] for value in values)


def _matrix_key(matrix, tolerance):
    return tuple(round(value / tolerance) for row in matrix for value in row)


def _vector_key(vector, scale, tolerance):
    return tuple(round(value / scale / tolerance) for value in vector)


def _port_lookup(artifact):
    return {
        (item.parent_type, item.child_type, item.symmetry_orbit_key): item
        for item in tuple(artifact.atlas.ports) +
        tuple(getattr(artifact, "boundary_ports", ())) }


def _canonical_prefixes(artifact, macro, semantics, tolerance):
    placements = tuple(sorted(macro.child_placements, key=lambda item: item.node))
    count = len(placements)
    raw_to_position = {item.node: index for index, item in enumerate(placements)}
    lookup = _port_lookup(artifact)
    alternatives = []
    distances = tuple(math.dist(left.translation, right.translation)
                      for index, left in enumerate(placements)
                      for right in placements[index + 1:])
    scale = min(value for value in distances if value > tolerance)
    for order in itertools.permutations(range(count)):
        remap = {old: new for new, old in enumerate(order)}
        topology_edges = tuple(sorted((
            remap[raw_to_position[edge.source]],
            remap[raw_to_position[edge.target]]) for edge in macro.edges))
        topology_boundary = tuple(sorted((
            remap[raw_to_position[slot.node]], slot.direction)
            for slot in macro.boundary_slots))
        topology = count, topology_edges, topology_boundary
        reduced_colors = tuple((
            semantics[placements[index].cluster_type].chemistry_key,
            semantics[placements[index].cluster_type].chirality_key)
                       for index in order)
        species_colors = tuple((
            _species_role(semantics[placements[index].cluster_type]),
            semantics[placements[index].cluster_type].chirality_key)
                       for index in order)
        port_edges = []
        for edge in macro.edges:
            port = lookup.get(tuple(edge.port))
            if port is None:
                raise ValueError("macro edge lacks a train-admitted semantic port")
            port_edges.append((
                remap[raw_to_position[edge.source]],
                remap[raw_to_position[edge.target]],
                tuple(sorted(_species(value)
                             for value in getattr(
                                 port, "overlap_species", ())))))
        port_boundary = []
        for slot in macro.boundary_slots:
            port = lookup.get(tuple(slot.port))
            if port is None:
                raise ValueError("macro boundary lacks a train-admitted port")
            outside = semantics[slot.outside_type]
            port_boundary.append((
                remap[raw_to_position[slot.node]], slot.direction,
                _species_role(outside), outside.chirality_key,
                tuple(sorted(_species(value)
                             for value in getattr(
                                 port, "overlap_species", ())))))
        ports = (tuple(sorted(port_edges, key=repr)),
                 tuple(sorted(port_boundary, key=repr)))
        pose_alternatives = []
        anchor = placements[order[0]]
        anchor_semantic = semantics[anchor.cluster_type]
        from materials_gcts_oriented_overlap_ports import (
            matmul, matvec, transpose)
        for anchor_gauge in anchor_semantic.proper_symmetries:
            inverse = transpose(matmul(anchor.rotation, anchor_gauge))
            child_pose = []
            for index in order:
                child = placements[index]
                rotations = tuple(_matrix_key(matmul(
                    inverse, matmul(child.rotation, symmetry)), tolerance)
                                  for symmetry in semantics[
                                      child.cluster_type].proper_symmetries)
                translation = matvec(inverse, tuple(
                    child.translation[axis] - anchor.translation[axis]
                    for axis in range(3)))
                child_pose.append((min(rotations),
                                   _vector_key(translation, scale, tolerance)))
            pose_alternatives.append(tuple(child_pose))
        species = (topology, species_colors)
        reduced = (topology, reduced_colors)
        species_ports = (topology, species_colors, ports)
        species_pose = (species_ports, min(pose_alternatives, key=repr))
        alternatives.append((topology, species, reduced, species_ports,
                             species_pose))
    return tuple(min(values, key=repr) for values in zip(*alternatives))


def _intersections(values_by_level, field):
    sets = tuple(set(values) for values in values_by_level)
    adjacent = tuple(len(left & right) for left, right in zip(sets, sets[1:]))
    triples = tuple(len(sets[index] & sets[index + 1] & sets[index + 2])
                    for index in range(max(0, len(sets) - 2)))
    return FieldIntersection(field, tuple(map(len, sets)), adjacent, triples)


def audit_stationary_fields(levels: Sequence[Any], *, tolerance=1e-6):
    ordered = tuple(sorted(levels, key=lambda item: item.hierarchy_level))
    topology = []
    species_chemistry = []
    topology_occurrences = []
    chemistry = []
    ports = []
    poses = []
    productions = []
    rejected = 0
    for level in ordered:
        semantics = {item.type_id: prototype_semantics(
            item, tolerance=tolerance) for item in level.artifact.prototypes}
        level_topology = []
        level_species_chemistry = []
        level_topology_occurrences = {}
        level_chemistry = []
        level_ports = []
        level_poses = []
        level_productions = {}
        cache = semantics.copy()
        for macro in level.submacros:
            try:
                top, species_chem, chem, port, species_pose = (
                    _canonical_prefixes(
                        level.artifact, macro, semantics, tolerance))
            except ValueError:
                rejected += 1
                continue
            level_topology.append(top)
            level_species_chemistry.append(species_chem)
            level_topology_occurrences.setdefault(top, 0)
            level_topology_occurrences[top] += len(macro.occurrences)
            level_chemistry.append(chem)
            level_ports.append(port)
            level_poses.append(species_pose)
            try:
                adapted = adapt_macro_type(
                    level.artifact, macro, tolerance=tolerance,
                    prototype_semantics_cache=cache)
            except ValueError:
                rejected += 1
                continue
            species_children = tuple(ProductionChild(
                tuple(species for species, _ in child.chemical_population),
                child.chirality_key, child.rotation, child.translation,
                child.proper_symmetries, child.chemical_population)
                                     for child in adapted.production.children)
            species_boundaries = tuple(ProductionBoundary(
                slot.child, slot.direction,
                _species_from_reduced(slot.outside_chemistry_key),
                slot.port_key, slot.overlap_chemistry)
                                       for slot in
                                       adapted.production.boundary_slots)
            species_production = PortGraphProduction(
                species_children, adapted.production.internal_ports,
                species_boundaries)
            try:
                key = canonicalize_production(
                    species_production, tolerance=tolerance).normalized_key
            except ValueError:
                # Binary oriented productions are represented in
                # ``species_pose`` above but remain ineligible for the strict
                # non-collinear canonical production contract.
                continue
            level_productions.setdefault(key, []).append(species_production)
        topology.append(tuple(level_topology))
        species_chemistry.append(tuple(level_species_chemistry))
        topology_occurrences.append(level_topology_occurrences)
        chemistry.append(tuple(level_chemistry))
        ports.append(tuple(level_ports))
        poses.append(tuple(level_poses))
        productions.append(level_productions)
    fields = (
        _intersections(topology, "topology+child-arity"),
        _intersections(species_chemistry, "species-set+chirality"),
        _intersections(chemistry, "reduced-chemistry+chirality-baseline"),
        _intersections(ports, "species-set+directed-port-semantics"),
        _intersections(poses, "species-set+normalized-proper-SE3-pose"))
    first_failure = next((item.field for item in fields
                          if not any(item.consecutive_three_level_intersections)),
                         None)
    population_pairs = population_triples = 0
    matrices = set()
    for index in range(len(productions) - 1):
        for key in set(productions[index]) & set(productions[index + 1]):
            for left in productions[index][key]:
                for right in productions[index + 1][key]:
                    population_pairs += audit_chemical_population_substitution(
                        left, right).consistent
    for index in range(len(productions) - 2):
        common = (set(productions[index]) & set(productions[index + 1]) &
                  set(productions[index + 2]))
        for key in common:
            for left, middle, right in itertools.product(
                    productions[index][key], productions[index + 1][key],
                    productions[index + 2][key]):
                first = audit_chemical_population_substitution(left, middle)
                second = audit_chemical_population_substitution(middle, right)
                compatible = (first.consistent and second.consistent and
                              first.substitution_matrix ==
                              second.substitution_matrix)
                population_triples += compatible
                if compatible:
                    matrices.add(first.substitution_matrix)
    pre_pose = sum(fields[3].consecutive_three_level_intersections)
    maximum_minimum = 0
    for index in range(max(0, len(topology_occurrences) - 2)):
        common = (set(topology_occurrences[index]) &
                  set(topology_occurrences[index + 1]) &
                  set(topology_occurrences[index + 2]))
        for key in common:
            maximum_minimum = max(maximum_minimum, min(
                topology_occurrences[index][key],
                topology_occurrences[index + 1][key],
                topology_occurrences[index + 2][key]))
    return StationaryFieldAblation(
        tuple(item.hierarchy_level for item in ordered),
        tuple(len(item.submacros) for item in ordered), fields,
        first_failure, rejected, population_pairs, population_triples,
        tuple(sorted(matrices)), pre_pose, maximum_minimum,
        maximum_minimum >= 16, False, False)
