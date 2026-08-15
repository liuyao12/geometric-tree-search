#!/usr/bin/env python3
"""Promote exact action submacros into the generic occurrence/port contract.

Patch IDs are namespaces for supports and source action-node IDs.  Dense
occurrences are fitted from their witnessed child unions; neither a target
cloud nor material metadata enters promotion.  Primitive action edges and
incoming frozen-port witnesses are retained as promoted boundary evidence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from materials_gcts_action_submacro_mining import (
    ActionMacroCorpusEntry, ActionSubmacroType)
from materials_gcts_frozen_frontier_replay import _add
from materials_gcts_macro_promotion import (
    MacroBoundaryPort, MacroBoundaryRelation, PromotedMacroProgram)
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, canonical_relative_pose, fit_occurrence_pose,
    learn_overlap_ports, make_prototype, matmul, matvec, transpose)


@dataclass(frozen=True)
class ActionSubmacroPromotionAudit:
    source_types: int
    promoted_types: int
    dense_source_occurrences: int
    promoted_occurrences: int
    namespaced_support_atoms: int
    overlap_ports: int
    overlap_relations: int
    boundary_ports: int
    boundary_relations: int
    prototype_failures: int
    pose_fit_failures: int
    target_used: bool


def _subtract(left, right):
    return tuple(left[index] - right[index]
                 for index in range(3))


def _render_child(program, child):
    prototype = next(item for item in program.prototypes
                     if item.type_id == child.cluster_type)
    return tuple((species, _add(matvec(child.rotation, point),
                                child.translation))
                 for species, point in prototype.sites)


def _observed_union(program, macro, source_node_ids, tolerance):
    requested = set(source_node_ids)
    selected = tuple(child for child in macro.children
                     if child.node_id in requested)
    if len(selected) != len(requested):
        raise ValueError("dense submacro occurrence references an unknown node")
    sites = {}
    species_at = {}
    for child in selected:
        for species, local in _render_child(program, child):
            point = _add(matvec(macro.world_rotation, local),
                         macro.world_translation)
            key = tuple(round(value / tolerance) for value in point)
            if key in species_at and species_at[key] != species:
                raise ValueError("dense submacro union has a colored conflict")
            species_at[key] = species
            sites.setdefault(key, (species, point))
    return tuple(sites[key] for key in sorted(sites))


def _source_relations(entries):
    relations = set()
    for entry in entries:
        patch = entry.patch_id
        macro = entry.macro
        node_ids = tuple(child.node_id for child in macro.children)
        for edge in macro.edges:
            left, right = node_ids[edge.source], node_ids[edge.target]
            relations.add((patch, left, right))
            relations.add((patch, right, left))
        for slot in macro.boundary_slots:
            child = node_ids[slot.child]
            relations.add((patch, slot.outside_parent_occurrence, child))
            relations.add((patch, child, slot.outside_parent_occurrence))
    return relations


def _relative(parent, child):
    inverse = transpose(parent.rotation)
    return (matmul(inverse, child.rotation),
            matvec(inverse, _subtract(
                child.translation, parent.translation)))


def _boundary_atlas(prototypes, occurrences, occurrence_sources,
                    primitive_relations, tolerance, minimum_observations):
    prototype_by_id = {item.type_id: item for item in prototypes}
    grouped = {}
    raw = []
    for parent in occurrences:
        parent_source = occurrence_sources[parent.occurrence_id]
        parent_nodes = set(parent_source.source_node_ids)
        for child in occurrences:
            if parent.occurrence_id == child.occurrence_id:
                continue
            child_source = occurrence_sources[child.occurrence_id]
            if parent_source.patch_id != child_source.patch_id:
                continue
            child_nodes = set(child_source.source_node_ids)
            witnesses = sum(
                (parent_source.patch_id, left, right) in primitive_relations
                for left in parent_nodes for right in child_nodes)
            if not witnesses:
                continue
            rotation, translation = _relative(parent, child)
            canonical_rotation, canonical_translation, key = (
                canonical_relative_pose(
                    prototype_by_id[parent.type_id],
                    prototype_by_id[child.type_id], rotation, translation,
                    tolerance))
            group_key = parent.type_id, child.type_id, key
            grouped.setdefault(group_key, [canonical_rotation,
                                           canonical_translation, 0, 0])
            grouped[group_key][2] += 1
            grouped[group_key][3] += witnesses
            raw.append((parent.occurrence_id, child.occurrence_id,
                        parent.type_id, child.type_id, key, witnesses,
                        group_key))
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
    relations = tuple(MacroBoundaryRelation(*item[:6]) for item in raw
                      if item[6] in admitted)
    return tuple(ports), relations


def promote_action_submacros(
        program, submacros: Sequence[ActionSubmacroType],
        action_macros: Sequence[ActionMacroCorpusEntry], *, level: int = 2,
        pose_tolerance: float = .03, minimum_shared_atoms: int = 2,
        minimum_port_observations: int = 2,
) -> tuple[PromotedMacroProgram, ActionSubmacroPromotionAudit]:
    """Create the generic promoted-program duck type from train witnesses."""
    if level < 1 or pose_tolerance <= 0:
        raise ValueError("level and pose tolerance must be positive")
    if minimum_shared_atoms < 1 or minimum_port_observations < 1:
        raise ValueError("port minima must be positive")
    macro_lookup = {(item.patch_id, item.macro.macro_id): item.macro
                    for item in action_macros}
    prototypes = []
    prototype_sources = []
    occurrences = []
    occurrence_sources = {}
    raw_supports = []
    prototype_failures = pose_failures = 0
    for submacro in submacros:
        try:
            prototype = make_prototype(
                len(prototypes), submacro.atom_union,
                tolerance=pose_tolerance)
        except (AssertionError, ValueError):
            prototype_failures += 1
            continue
        fitted = []
        for source in submacro.dense_occurrences:
            macro = macro_lookup.get((source.patch_id,
                                      source.action_macro_id))
            if macro is None:
                pose_failures += 1
                continue
            try:
                observed = _observed_union(
                    program, macro, source.source_node_ids, pose_tolerance)
                pose = fit_occurrence_pose(
                    len(occurrences) + len(fitted), prototype, observed,
                    tolerance=pose_tolerance)
            except ValueError:
                pose_failures += 1
                continue
            fitted.append((pose, source))
        if len(fitted) < 2:
            pose_failures += len(fitted)
            continue
        prototype = type(prototype)(len(prototypes), prototype.sites,
                                    prototype.proper_symmetries)
        prototypes.append(prototype)
        prototype_sources.append((prototype.type_id, submacro.submacro_id))
        for pose, source in fitted:
            occurrence = ClusterOccurrence(
                len(occurrences), prototype.type_id,
                pose.rotation, pose.translation)
            occurrences.append(occurrence)
            occurrence_sources[occurrence.occurrence_id] = source
            raw_supports.append((occurrence.occurrence_id, source.patch_id,
                                 source.atom_site_keys))

    atom_ids = {}
    supports = []
    for occurrence_id, patch_id, site_keys in raw_supports:
        support = []
        for site_key in site_keys:
            namespaced = patch_id, site_key
            if namespaced not in atom_ids:
                atom_ids[namespaced] = len(atom_ids)
            support.append(atom_ids[namespaced])
        supports.append((occurrence_id, tuple(sorted(set(support)))))
    support_by_id = {key: set(value) for key, value in supports}
    allowed = frozenset(
        (left.occurrence_id, right.occurrence_id)
        for left in occurrences for right in occurrences
        if left.occurrence_id != right.occurrence_id and
        len(support_by_id[left.occurrence_id].intersection(
            support_by_id[right.occurrence_id])) >= minimum_shared_atoms)
    exclusion_distance = getattr(
        program, "exclusion_distance", pose_tolerance)
    minimum_distance = getattr(
        program, "minimum_distance",
        max(pose_tolerance * 2, exclusion_distance / .45))
    atlas = learn_overlap_ports(
        tuple(prototypes), tuple(occurrences),
        minimum_overlap=minimum_shared_atoms,
        minimum_observations=minimum_port_observations,
        overlap_tolerance=pose_tolerance,
        exclusion_distance=max(pose_tolerance, exclusion_distance),
        allowed_occurrence_pairs=allowed)
    boundary_ports, boundary_relations = _boundary_atlas(
        prototypes, occurrences, occurrence_sources,
        _source_relations(action_macros), pose_tolerance,
        minimum_port_observations)
    promoted = PromotedMacroProgram(
        level, len(submacros), tuple(prototypes), tuple(prototype_sources),
        tuple(occurrences), tuple(supports), atlas, boundary_ports,
        boundary_relations, minimum_shared_atoms, minimum_distance,
        prototype_failures, pose_failures, 0,
        False, False, False, False)
    audit = ActionSubmacroPromotionAudit(
        len(submacros), len(prototypes),
        sum(len(item.dense_occurrences) for item in submacros),
        len(occurrences), len(atom_ids), len(atlas.ports),
        len(atlas.relation_classes), len(boundary_ports),
        len(boundary_relations), prototype_failures, pose_failures, False)
    return promoted, audit
