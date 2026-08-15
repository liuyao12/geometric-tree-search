#!/usr/bin/env python3
"""Promote committed batch waves into exact target-free action macros."""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass

from materials_gcts_batch_frontier_search import BatchFrontierResult
from materials_gcts_frozen_frontier_replay import (
    FrozenFrontierProgram, Site, _add, _pose_key, _render, _site_key)
from materials_gcts_oriented_overlap_ports import (
    Matrix, Vector, expand_port_orbit, is_proper_rotation, matmul, matvec,
    transpose)
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionBoundary, ProductionChild, ProductionPort,
    canonicalize_production)


@dataclass(frozen=True)
class ActionMacroChild:
    node_id: int
    cluster_type: int
    rotation: Matrix
    translation: Vector


@dataclass(frozen=True)
class ActionMacroEdge:
    source: int
    target: int
    connection_kind: str
    port_key: tuple[str, ...]
    exact_overlap_site_keys: tuple[tuple[str, int, int, int], ...]


@dataclass(frozen=True)
class ActionMacroBoundary:
    child: int
    outside_parent_occurrence: int
    production_id: int
    port_key: tuple[str, ...]


@dataclass(frozen=True)
class ActionMacroCertificate:
    nodes_are_exactly_accepted_wave_component: bool
    every_child_pose_proper_se3: bool
    colored_union_is_exact: bool
    edge_overlaps_are_exact_intersections: bool
    incoming_boundaries_are_train_frozen_ports: bool
    pairwise_compatible_antichain: bool
    atom_union_site_keys: tuple[tuple[str, int, int, int], ...]
    certificate_digest: str


@dataclass(frozen=True)
class ActionMacroType:
    macro_id: int
    wave: int
    component: int
    children: tuple[ActionMacroChild, ...]
    edges: tuple[ActionMacroEdge, ...]
    atom_union: tuple[Site, ...]
    boundary_slots: tuple[ActionMacroBoundary, ...]
    certificate: ActionMacroCertificate
    production: PortGraphProduction | None
    normalized_production_key: str | None
    canonicalization_failure: str | None


@dataclass(frozen=True)
class ActionMacroRecurrence:
    normalized_production_key: str
    waves: tuple[int, ...]
    macro_ids: tuple[int, ...]
    recurs_across_three_consecutive_waves: bool
    hierarchy_stationarity_claimed: bool


@dataclass(frozen=True)
class ActionMacroPromotionResult:
    macros: tuple[ActionMacroType, ...]
    recurrences: tuple[ActionMacroRecurrence, ...]
    accepted_nodes: int
    covered_accepted_nodes: int
    exact_cover_of_accepted_nodes: bool
    target_used: bool


def _subtract(left: Vector, right: Vector) -> Vector:
    return tuple(left[index] - right[index]
                 for index in range(3))  # type: ignore[return-value]


def _species_key(species) -> str:
    return (f"{type(species).__module__}.{type(species).__qualname__}:"
            f"{species!r}")


def _chemistry(prototype) -> tuple[str, ...]:
    return tuple(sorted(_species_key(species)
                        for species, _ in prototype.sites))


def _population(prototype) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(_species_key(species)
                                for species, _ in prototype.sites).items()))


def _component_graph(nodes, rendered_keys):
    adjacency = {node.node_id: set() for node in nodes}
    pair_overlap = {}
    for left_index, left in enumerate(nodes):
        for right in nodes[left_index + 1:]:
            overlap = tuple(sorted(
                rendered_keys[left.node_id].intersection(
                    rendered_keys[right.node_id])))
            same_parent = (left.parent_occurrence is not None and
                           left.parent_occurrence == right.parent_occurrence)
            if overlap or same_parent:
                adjacency[left.node_id].add(right.node_id)
                adjacency[right.node_id].add(left.node_id)
                pair_overlap[(left.node_id, right.node_id)] = overlap
    components = []
    unseen = set(adjacency)
    while unseen:
        root = min(unseen)
        reached = {root}
        pending = [root]
        while pending:
            current = pending.pop()
            for neighbor in adjacency[current] - reached:
                reached.add(neighbor)
                pending.append(neighbor)
        unseen.difference_update(reached)
        components.append(tuple(sorted(reached)))
    return tuple(components), pair_overlap


def promote_batch_action_macros(
    program: FrozenFrontierProgram, result: BatchFrontierResult, *,
    canonical_tolerance: float = 1e-6,
) -> ActionMacroPromotionResult:
    """Promote exact committed action components; never inspect a target."""
    if result.target_used:
        raise ValueError("cannot promote a target-conditioned batch result")
    prototypes = {item.type_id: item for item in program.prototypes}
    productions = {item.production_id: item for item in program.productions}
    placed_by_id = {item.occurrence_id: item
                    for item in result.placed_occurrences}
    result_site_keys = {_site_key(site, program.overlap_tolerance)
                        for site in result.sites}
    orbit_cache = {}
    nodes_by_wave = defaultdict(list)
    for node in result.symbolic_nodes:
        if node.wave > 0:
            nodes_by_wave[node.wave].append(node)
    accepted_by_wave = {
        wave.wave: {item.candidate_id for item in wave.candidates
                    if item.accepted}
        for wave in result.waves}
    macros = []
    covered_nodes = set()
    for wave in sorted(nodes_by_wave):
        nodes = tuple(sorted(nodes_by_wave[wave], key=lambda item: item.node_id))
        rendered = {node.node_id: _render(
            prototypes[node.cluster_type], node.rotation, node.translation)
            for node in nodes}
        rendered_keys = {node_id: {
            _site_key(site, program.overlap_tolerance) for site in sites}
            for node_id, sites in rendered.items()}
        components, pair_overlap = _component_graph(nodes, rendered_keys)
        node_by_id = {node.node_id: node for node in nodes}
        for component_index, component_ids in enumerate(components):
            component_nodes = tuple(node_by_id[node_id]
                                    for node_id in component_ids)
            covered_nodes.update(component_ids)
            root = component_nodes[0]
            inverse_root = transpose(root.rotation)
            children = tuple(ActionMacroChild(
                node.node_id, node.cluster_type,
                matmul(inverse_root, node.rotation),
                matvec(inverse_root, _subtract(
                    node.translation, root.translation)))
                for node in component_nodes)
            local_union = {}
            species_at_coordinate = {}
            world_union_keys = set()
            for node in component_nodes:
                for species, point in rendered[node.node_id]:
                    world_union_keys.add(_site_key(
                        (species, point), program.overlap_tolerance))
                    local = matvec(inverse_root, _subtract(
                        point, root.translation))
                    coordinate = tuple(round(value /
                                             program.overlap_tolerance)
                                       for value in local)
                    if (coordinate in species_at_coordinate and
                            species_at_coordinate[coordinate] != species):
                        raise ValueError(
                            "accepted component has unlike-colored collision")
                    species_at_coordinate[coordinate] = species
                    local_union.setdefault(coordinate, (species, local))
            atom_union = tuple(local_union[key] for key in sorted(local_union))
            edges = []
            for left_index, left_id in enumerate(component_ids):
                for right_id in component_ids[left_index + 1:]:
                    pair = (left_id, right_id)
                    overlap = pair_overlap.get(pair)
                    left = node_by_id[left_id]
                    right = node_by_id[right_id]
                    same_parent = (left.parent_occurrence is not None and
                                   left.parent_occurrence ==
                                   right.parent_occurrence)
                    if overlap is None and not same_parent:
                        continue
                    overlap = overlap or ()
                    overlap_species = tuple(sorted(key[0] for key in overlap))
                    kind = "colored-overlap" if overlap else "shared-parent"
                    port_key = ((kind,) + overlap_species if overlap else
                                (kind, str(left.production_id),
                                 str(right.production_id)))
                    edges.append(ActionMacroEdge(
                        component_ids.index(left_id),
                        component_ids.index(right_id), kind, port_key,
                        tuple(overlap)))
            boundaries = []
            stationary_boundaries = []
            exact_boundary_witnesses = []
            for child_index, node in enumerate(component_nodes):
                production = productions.get(node.production_id)
                if production is None or node.parent_occurrence is None:
                    exact_boundary_witnesses.append(False)
                    continue
                parent_occurrence = placed_by_id.get(node.parent_occurrence)
                child_occurrence = placed_by_id.get(node.node_id)
                orbit = orbit_cache.get(production.production_id)
                if orbit is None:
                    orbit = expand_port_orbit(
                        prototypes[production.parent_type],
                        prototypes[production.child_type], production.port,
                        program.overlap_tolerance)
                    orbit_cache[production.production_id] = orbit
                witnessed = bool(
                    parent_occurrence is not None and
                    child_occurrence is not None and
                    parent_occurrence.type_id == production.parent_type and
                    child_occurrence.type_id == production.child_type and
                    any(_pose_key(child_occurrence,
                                  program.overlap_tolerance) == _pose_key(
                        type(child_occurrence)(
                            -1, production.child_type,
                            matmul(parent_occurrence.rotation,
                                   relative_rotation),
                            _add(parent_occurrence.translation, matvec(
                                parent_occurrence.rotation,
                                relative_translation))),
                        program.overlap_tolerance)
                        for relative_rotation, relative_translation in orbit))
                exact_boundary_witnesses.append(witnessed)
                parent_chemistry = _chemistry(
                    prototypes[production.parent_type])
                child_chemistry = _chemistry(
                    prototypes[production.child_type])
                semantic_key = ("train-frozen-incoming",) + tuple(sorted(
                    set(parent_chemistry + child_chemistry)))
                boundaries.append(ActionMacroBoundary(
                    child_index, node.parent_occurrence,
                    production.production_id, semantic_key))
                stationary_boundaries.append(ProductionBoundary(
                    child_index, "incoming", parent_chemistry, semantic_key,
                    tuple(sorted(_species_key(species)
                                 for species in production.port.overlap_species))))
            stationary_children = tuple(ProductionChild(
                _chemistry(prototypes[node.cluster_type]),
                f"proper-SE3:type-{node.cluster_type}",
                child.rotation, child.translation,
                prototypes[node.cluster_type].proper_symmetries,
                _population(prototypes[node.cluster_type]))
                for node, child in zip(component_nodes, children))
            stationary_ports = tuple(ProductionPort(
                edge.source, edge.target, edge.port_key,
                tuple(key[0] for key in edge.exact_overlap_site_keys))
                for edge in edges)
            production = PortGraphProduction(
                stationary_children, stationary_ports,
                tuple(stationary_boundaries))
            normalized_key = failure = None
            try:
                normalized_key = canonicalize_production(
                    production, tolerance=canonical_tolerance).normalized_key
            except ValueError as error:
                failure = str(error)
                production = None
            accepted_ids = accepted_by_wave.get(wave, set())
            exact_nodes = all(node.candidate_id in accepted_ids
                              for node in component_nodes)
            proper = all(is_proper_rotation(node.rotation)
                         for node in component_nodes)
            exact_overlap = all(
                edge.exact_overlap_site_keys == tuple(sorted(
                    rendered_keys[component_ids[edge.source]].intersection(
                        rendered_keys[component_ids[edge.target]])))
                for edge in edges if edge.connection_kind == "colored-overlap")
            frozen_boundaries = (
                len(boundaries) == len(component_nodes) and
                all(exact_boundary_witnesses))
            union_keys = tuple(sorted(world_union_keys))
            payload = repr((wave, component_ids, union_keys, edges,
                            boundaries)).encode()
            certificate = ActionMacroCertificate(
                exact_nodes, proper,
                len(atom_union) == len(world_union_keys) and
                world_union_keys.issubset(result_site_keys), exact_overlap,
                frozen_boundaries,
                next(item for item in result.waves if item.wave == wave).
                pairwise_compatible_antichain,
                union_keys, hashlib.sha256(payload).hexdigest())
            macros.append(ActionMacroType(
                len(macros), wave, component_index, children, tuple(edges),
                atom_union, tuple(boundaries), certificate, production,
                normalized_key, failure))
    grouped = defaultdict(list)
    for macro in macros:
        if macro.normalized_production_key is not None:
            grouped[macro.normalized_production_key].append(macro)
    recurrences = []
    for key in sorted(grouped):
        group = sorted(grouped[key], key=lambda item: (item.wave, item.macro_id))
        waves = tuple(sorted({item.wave for item in group}))
        consecutive = any((start + 1 in waves and start + 2 in waves)
                          for start in waves)
        recurrences.append(ActionMacroRecurrence(
            key, waves, tuple(item.macro_id for item in group), consecutive,
            False))
    accepted_nodes = sum(node.wave > 0 for node in result.symbolic_nodes)
    return ActionMacroPromotionResult(
        tuple(macros), tuple(recurrences), accepted_nodes,
        len(covered_nodes), len(covered_nodes) == accepted_nodes, False)
