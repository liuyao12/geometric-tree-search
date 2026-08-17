#!/usr/bin/env python3
"""Exact, target-free decomposition of a partial macro completion.

Whole promoted-macro actions are sometimes too coarse: a frozen RHS can
contain several independently attached missing regions.  This module cuts the
missing RHS only at absent *train-witnessed* port relations.  It never asks
which predicted sites occur in an evaluation target.  Components without an
admitted connection to an already observed child are retained explicitly as
residual subclusters, so decomposition cannot manufacture coverage.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    is_proper_rotation, matvec)

SiteKey = tuple[str, int, int, int]


@dataclass(frozen=True)
class EmissionComponent:
    component_id: str
    child_nodes: tuple[int, ...]
    child_types: tuple[int, ...]
    sites: tuple[tuple[Hashable, tuple[float, float, float]], ...]
    internal_ports: tuple[tuple[int, int, tuple], ...]
    attachment_ports: tuple[tuple[int, int, tuple], ...]
    attached_to_observed_rhs: bool
    exact_proper_se3_candidate: bool


@dataclass(frozen=True)
class PartialMacroDecomposition:
    macro_id: int
    emission_components: tuple[EmissionComponent, ...]
    residual_subclusters: tuple[EmissionComponent, ...]
    missing_child_nodes: tuple[int, ...]
    source_site_count: int
    represented_site_count: int
    duplicate_overlap_sites: int
    complete_cover: bool
    colored_union_digest: str
    target_used: bool


@dataclass(frozen=True)
class AtomicFrontierComponent:
    component_id: str
    child_node: int
    child_type: int
    prototype_site_indices: tuple[int, ...]
    sites: tuple[tuple[Hashable, tuple[float, float, float]], ...]
    directly_port_attached: bool
    exact_proper_se3_candidate: bool


@dataclass(frozen=True)
class AtomicFrontierDecomposition:
    macro_id: int
    emission_components: tuple[AtomicFrontierComponent, ...]
    residual_subclusters: tuple[AtomicFrontierComponent, ...]
    observed_overlap_sites: tuple[tuple[Hashable, tuple[float, float, float]], ...]
    source_site_count: int
    complete_cover: bool
    exact_colored_union: bool
    target_used: bool


def _site_key(site, tolerance: float) -> SiteKey:
    species, point = site
    return ((species if isinstance(species, str) else repr(species)),
            *(round(float(value) / tolerance) for value in point))


def _admitted_semantics(program) -> frozenset[tuple]:
    atlas = getattr(program, "atlas", None)
    values = {(item.parent_type, item.child_type, item.symmetry_orbit_key)
              for item in getattr(atlas, "ports", ())}
    values.update((item.parent_type, item.child_type,
                   item.symmetry_orbit_key)
                  for item in getattr(program, "boundary_ports", ()))
    # Some compact training fixtures retain only relation classes.  They are
    # still train-witnessed, unlike a naked edge copied from an RHS.
    values.update((parent_type, child_type, key)
                  for _parent, _child, parent_type, child_type, key in
                  getattr(atlas, "relation_classes", ()))
    return frozenset(values)


def _component_digest(macro_id, nodes, node_types, ports, local_sites):
    # local_sites are frozen macro-frame sites, hence unchanged by the proper
    # SE(3) pose used to instantiate a completion.
    payload = (macro_id, tuple(sorted((node, node_types[node])
                                     for node in nodes)),
               tuple(sorted(ports)), tuple(sorted(local_sites)))
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def _connected_components(nodes, adjacency):
    remaining = set(nodes)
    result = []
    while remaining:
        root = min(remaining)
        pending = [root]
        component = set()
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            pending.extend(sorted(adjacency[node] - component, reverse=True))
        remaining.difference_update(component)
        result.append(tuple(sorted(component)))
    return tuple(result)


def _gabriel_adjacency(sites, tolerance):
    """Parameter-free proper-SE(3)-invariant proximity graph."""
    points = tuple(site[1] for site in sites)
    adjacency = {index: set() for index in range(len(points))}
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            squared = sum((points[left][axis] - points[right][axis]) ** 2
                          for axis in range(3))
            if squared <= tolerance * tolerance:
                continue
            midpoint = tuple((points[left][axis] + points[right][axis]) / 2
                             for axis in range(3))
            radius_squared = squared / 4
            blocked = any(
                index not in (left, right) and
                sum((point[axis] - midpoint[axis]) ** 2 for axis in range(3))
                < radius_squared - tolerance * tolerance
                for index, point in enumerate(points))
            if not blocked:
                adjacency[left].add(right)
                adjacency[right].add(left)
    return adjacency


def _render_prototype(prototype, rotation, translation):
    return tuple((species, tuple(matvec(rotation, point)[axis] +
                                   translation[axis] for axis in range(3)))
                 for species, point in prototype.sites)


def decompose_partial_macro_completion(
        lower_program, macro, completion, *, pose_tolerance: float = .03,
) -> PartialMacroDecomposition:
    """Partition a frozen completion into attached and residual components.

    An internal missing--missing edge is usable only when its exact semantic
    port was admitted by the training program.  Exact shared colored sites
    also join children: overlapping atoms cannot be committed independently.
    A component is an emission action only when an admitted RHS edge attaches
    it to a matched child.  Every other component is an explicit residual.
    """
    if pose_tolerance <= 0 or not math.isfinite(pose_tolerance):
        raise ValueError("pose tolerance must be finite and positive")
    if getattr(lower_program, "target_used", False) or completion.target_used:
        raise ValueError("decomposition requires train-frozen, target-free data")
    if completion.macro_id != macro.macro_id:
        raise ValueError("completion and frozen macro IDs differ")
    if (not completion.exact_frozen_rhs_geometry or
            not is_proper_rotation(completion.macro_rotation)):
        raise ValueError("completion must have exact proper-SE(3) RHS geometry")

    placements = {item.node: item for item in macro.child_placements}
    missing = {item.node: item for item in completion.missing_children}
    matched = set(completion.matched_nodes)
    if set(missing) & matched or set(missing) | matched != set(placements):
        raise ValueError("matched and missing nodes must partition frozen RHS")
    if any(item.type_id != placements[node].cluster_type or
           not is_proper_rotation(item.rotation)
           for node, item in missing.items()):
        raise ValueError("predicted child type/pose differs from frozen RHS")

    admitted = _admitted_semantics(lower_program)
    port_adjacency = {node: set() for node in missing}
    overlap_adjacency = {node: set() for node in missing}
    internal = []
    attachments = []
    for edge in getattr(macro, "edges", ()):
        if edge.port not in admitted:
            continue
        if edge.source in missing and edge.target in missing:
            port_adjacency[edge.source].add(edge.target)
            port_adjacency[edge.target].add(edge.source)
            internal.append((edge.source, edge.target, edge.port))
        elif ((edge.source in missing and edge.target in matched) or
              (edge.target in missing and edge.source in matched)):
            attachments.append((edge.source, edge.target, edge.port))

    site_maps = {}
    coordinate_species = {}
    for node, child in missing.items():
        values = {}
        for site in child.sites:
            key = _site_key(site, pose_tolerance)
            coordinate = key[1:]
            previous = coordinate_species.setdefault(coordinate, key[0])
            if previous != key[0]:
                raise ValueError("predicted RHS has a colored-site conflict")
            values.setdefault(key, (site[0], tuple(float(v) for v in site[1])))
        site_maps[node] = values
    nodes = sorted(missing)
    for left_index, left in enumerate(nodes):
        for right in nodes[left_index + 1:]:
            if set(site_maps[left]).intersection(site_maps[right]):
                overlap_adjacency[left].add(right)
                overlap_adjacency[right].add(left)

    # Causal frontier rule: an admitted port to an already observed child is
    # enough to expose a child now.  A missing--missing port is a dependency
    # for a later wave, not a reason to commit both children atomically.
    # Exact shared atoms are different: their owners must remain one action.
    direct = {node for edge in attachments for node in edge[:2]
              if node in missing}
    frontier = set()
    pending = list(direct)
    while pending:
        node = pending.pop()
        if node in frontier:
            continue
        frontier.add(node)
        pending.extend(overlap_adjacency[node] - frontier)
    residual_nodes = set(nodes) - frontier
    residual_adjacency = {
        node: (port_adjacency[node] | overlap_adjacency[node]) & residual_nodes
        for node in residual_nodes}
    groups = [(group, True) for group in
              _connected_components(frontier, overlap_adjacency)]
    groups.extend((group, False) for group in
                  _connected_components(residual_nodes, residual_adjacency))

    node_types = {node: placements[node].cluster_type for node in missing}
    source_keys = set().union(*(set(values) for values in site_maps.values())) \
        if site_maps else set()
    raw_count = sum(len(values) for values in site_maps.values())
    emitted = []
    residual = []
    represented = set()
    for nodes_in_component, is_frontier in groups:
        node_set = set(nodes_in_component)
        component_internal = tuple(sorted(
            edge for edge in internal
            if edge[0] in node_set and edge[1] in node_set))
        component_attachments = tuple(sorted(
            edge for edge in attachments
            if edge[0] in node_set or edge[1] in node_set))
        keys = set().union(*(set(site_maps[node])
                           for node in nodes_in_component))
        represented.update(keys)
        sites = tuple(site_maps[node][key]
                      for key in sorted(keys)
                      for node in nodes_in_component if key in site_maps[node])
        # The generator above may encounter the same key in multiple children;
        # retain its canonical first owner only.
        sites = tuple(dict.fromkeys(sites))
        local_sites = tuple(
            (placements[node].cluster_type,
             tuple(round(value / pose_tolerance)
                   for value in placements[node].translation))
            for node in nodes_in_component)
        component = EmissionComponent(
            _component_digest(macro.macro_id, nodes_in_component, node_types,
                              component_internal + component_attachments,
                              local_sites),
            nodes_in_component,
            tuple(node_types[node] for node in nodes_in_component), sites,
            component_internal, component_attachments,
            bool(component_attachments) and is_frontier, True)
        (emitted if is_frontier else residual).append(component)

    digest = hashlib.sha256(repr(tuple(sorted(source_keys))).encode()).hexdigest()
    return PartialMacroDecomposition(
        macro.macro_id, tuple(emitted), tuple(residual), tuple(nodes),
        len(source_keys), len(represented), raw_count - len(source_keys),
        represented == source_keys, digest, False)


def decompose_atomic_frontier(
        lower_program, macro, completion, *, pose_tolerance: float = .03,
) -> AtomicFrontierDecomposition:
    """Peel a finite atom frontier inside each port-attached missing child.

    The child support itself can be the over-large action.  Its exact Gabriel
    graph supplies a radius-free local adjacency.  Novel sites adjacent to an
    already observed overlap site form the current emission layer; deeper
    sites remain explicit residual subclusters.  A witnessed non-overlapping
    boundary port exposes the whole child because it has no atom anchor.
    """
    # Reuse all macro/pose/target invariants and the complete child cover audit.
    coarse = decompose_partial_macro_completion(
        lower_program, macro, completion, pose_tolerance=pose_tolerance)
    prototypes = {item.type_id: item for item in lower_program.prototypes}
    occupied = {}
    for occurrence in lower_program.occurrences:
        prototype = prototypes[occurrence.type_id]
        for site in _render_prototype(prototype, occurrence.rotation,
                                      occurrence.translation):
            occupied.setdefault(_site_key(site, pose_tolerance), site)
    admitted = _admitted_semantics(lower_program)
    missing = {item.node: item for item in completion.missing_children}
    matched = set(completion.matched_nodes)
    directly_attached = set()
    for edge in getattr(macro, "edges", ()):
        if edge.port not in admitted:
            continue
        if edge.source in missing and edge.target in matched:
            directly_attached.add(edge.source)
        if edge.target in missing and edge.source in matched:
            directly_attached.add(edge.target)
    # A frozen outgoing boundary role can anchor one uniquely typed missing
    # child.  If several children fit the role, decomposition fails closed by
    # leaving them residual rather than choosing by node order.
    for slot in getattr(macro, "boundary_slots", ()):
        if (slot.node not in matched or slot.direction != "outgoing" or
                slot.port not in admitted or slot.occurrence_support <= 0):
            continue
        choices = tuple(node for node, child in missing.items()
                        if child.type_id == slot.outside_type)
        if len(choices) == 1:
            directly_attached.add(choices[0])

    emissions = []
    residuals = []
    observed_sites = {}
    source = {}
    represented = set()
    for child in completion.missing_children:
        prototype = prototypes[child.type_id]
        if len(prototype.sites) != len(child.sites):
            raise ValueError("predicted child lost frozen prototype site order")
        sites = tuple((site[0], tuple(float(v) for v in site[1]))
                      for site in child.sites)
        keys = tuple(_site_key(site, pose_tolerance) for site in sites)
        for key, site in zip(keys, sites):
            source.setdefault(key, site)
        observed = {index for index, key in enumerate(keys) if key in occupied}
        for index in observed:
            observed_sites.setdefault(keys[index], sites[index])
        novel = set(range(len(sites))) - observed
        adjacency = _gabriel_adjacency(sites, pose_tolerance)
        if child.node in directly_attached:
            frontier = ({index for index in novel
                         if adjacency[index].intersection(observed)}
                        if observed else set(novel))
        else:
            frontier = set()
        remainder = novel - frontier
        frontier_adjacency = {index: adjacency[index] & frontier
                              for index in frontier}
        groups = [(group, True) for group in
                  _connected_components(frontier, frontier_adjacency)]
        residual_adjacency = {index: adjacency[index] & remainder
                              for index in remainder}
        groups.extend((group, False) for group in
                      _connected_components(remainder, residual_adjacency))
        for indices, emitted_now in groups:
            component_sites = tuple(sites[index] for index in indices)
            represented.update(keys[index] for index in indices)
            payload = (macro.macro_id, child.node, child.type_id, indices)
            component = AtomicFrontierComponent(
                hashlib.sha256(repr(payload).encode()).hexdigest(),
                child.node, child.type_id, indices, component_sites,
                child.node in directly_attached, True)
            (emissions if emitted_now else residuals).append(component)
        represented.update(keys[index] for index in observed)
    source_keys = set(source)
    return AtomicFrontierDecomposition(
        macro.macro_id, tuple(emissions), tuple(residuals),
        tuple(observed_sites[key] for key in sorted(observed_sites)),
        len(source_keys), represented == source_keys,
        {_site_key(site, pose_tolerance)
         for component in emissions + residuals for site in component.sites} |
        set(observed_sites) == source_keys,
        coarse.target_used)
