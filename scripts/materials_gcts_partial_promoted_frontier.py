#!/usr/bin/env python3
"""Target-free partial recognition of train-frozen promoted macro RHSs."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, is_proper_rotation, matmul, matvec, transpose)


@dataclass(frozen=True)
class PredictedMacroChild:
    node: int
    type_id: int
    rotation: tuple
    translation: tuple[float, float, float]
    sites: tuple


@dataclass(frozen=True)
class PartialPromotedCompletion:
    macro_id: int
    matched_nodes: tuple[int, ...]
    matched_occurrence_ids: tuple[int, ...]
    missing_children: tuple[PredictedMacroChild, ...]
    macro_rotation: tuple
    macro_translation: tuple[float, float, float]
    exact_frozen_rhs_geometry: bool
    target_used: bool
    frozen_parent_type: int | None = None


@dataclass(frozen=True)
class PartialPromotedFrontierAudit:
    admitted_macro_types: int
    observed_seed_occurrences: int
    minimum_matched_children: int
    frame_hypotheses: int
    insufficient_hypotheses: int
    collision_rejections: int
    redundant_completion_rejections: int
    internal_port_rejections: int
    child_coverage_rejections: int
    one_child_missing_port_rejections: int
    public_boundary_rejections: int
    ambiguous_completion_signatures: int
    completions: tuple[PartialPromotedCompletion, ...]
    frozen_ids_preserved: bool
    proper_se3_only: bool
    target_used: bool


def _add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def _subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def _render(prototype, rotation, translation):
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _site_key(site, tolerance):
    return (repr(site[0]),) + tuple(round(value / tolerance)
                                    for value in site[1])


def _render_key(prototype, rotation, translation, tolerance):
    return tuple(sorted(_site_key(site, tolerance)
                        for site in _render(prototype, rotation, translation)))


def _collision_free(sites, occupied, tolerance, exclusion):
    for species, point in sites:
        for other_species, other in occupied:
            distance = math.dist(point, other)
            if distance <= tolerance:
                if species != other_species:
                    return False
            elif distance < exclusion:
                return False
    return True


def _has_finite_proper_frame(prototype, tolerance):
    """A one-child anchor must not have a continuous rotational gauge."""
    points = tuple(point for _species, point in prototype.sites)
    noncollinear = False
    for root in points:
        for left in points:
            for right in points:
                first = _subtract(left, root)
                second = _subtract(right, root)
                cross = (first[1] * second[2] - first[2] * second[1],
                         first[2] * second[0] - first[0] * second[2],
                         first[0] * second[1] - first[1] * second[0])
                noncollinear |= math.sqrt(sum(value * value
                                               for value in cross)) > tolerance
    symmetries = tuple(prototype.proper_symmetries)
    keys = {tuple(round(value / tolerance)
                  for row in symmetry for value in row)
            for symmetry in symmetries}
    return (noncollinear and bool(symmetries) and
            len(keys) == len(symmetries) and
            all(is_proper_rotation(symmetry) for symmetry in symmetries))


def _admitted_relations(program):
    atlas = getattr(program, "atlas", None)
    relations = {(parent, child, (parent_type, child_type, key))
                 for parent, child, parent_type, child_type, key in
                 getattr(atlas, "relation_classes", ())}
    relations.update((item.parent_occurrence, item.child_occurrence,
                      (item.parent_type, item.child_type,
                       item.symmetry_orbit_key))
                     for item in getattr(program,
                                         "boundary_relation_classes", ()))
    return frozenset(relations)


def _admitted_port_semantics(program):
    atlas = getattr(program, "atlas", None)
    values = {(item.parent_type, item.child_type, item.symmetry_orbit_key)
              for item in getattr(atlas, "ports", ())}
    values.update((item.parent_type, item.child_type,
                   item.symmetry_orbit_key)
                  for item in getattr(program, "boundary_ports", ()))
    return frozenset(values)


def _has_frozen_port_to_missing(macro, witnessed, missing,
                                admitted_semantics):
    witnessed = set(witnessed)
    missing = set(missing)
    placements = {item.node: item.cluster_type
                  for item in macro.child_placements}
    internal = any(edge.source in witnessed and edge.target in missing and
                   edge.port in admitted_semantics
                   for edge in getattr(macro, "edges", ()))
    boundary = any(
        slot.node in witnessed and slot.direction == "outgoing" and
        slot.outside_type in {placements[node] for node in missing} and
        slot.port in admitted_semantics and slot.occurrence_support > 0
        for slot in getattr(macro, "boundary_slots", ()))
    return internal or boundary


def _largest_connected_witnesses(macro, slot_occurrences, relations):
    remaining = set(slot_occurrences)
    edges = tuple(getattr(macro, "edges", ()))
    # Lightweight callers may provide only frozen child placements.  In that
    # legacy contract geometry supplies the independent witness check; full
    # MacroType inputs additionally require their immutable port incidence.
    if not edges:
        return tuple(sorted(remaining))
    adjacency = {slot: set() for slot in remaining}
    for edge in edges:
        if edge.source not in remaining or edge.target not in remaining:
            continue
        if (slot_occurrences[edge.source], slot_occurrences[edge.target],
                edge.port) not in relations:
            continue
        adjacency[edge.source].add(edge.target)
        adjacency[edge.target].add(edge.source)
    components = []
    while remaining:
        root = min(remaining)
        pending = [root]
        component = set()
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            pending.extend(adjacency[node] - component)
        remaining.difference_update(component)
        components.append(tuple(sorted(component)))
    return max(components, key=lambda value: (len(value), value), default=())


def enumerate_partial_promoted_completions(
        lower_program, admitted_macros: Sequence[object], *,
        minimum_matched_children: int = 2,
        minimum_child_coverage: float = 0.,
        explicit_seed_sites: Sequence[tuple[Hashable, Sequence[float]]] = (),
        public_boundary: object | None = None,
        frozen_parent_types: Sequence[tuple[int, int]] = (),
        pose_tolerance: float = .03,
) -> PartialPromotedFrontierAudit:
    """Infer missing children from a uniquely identified frozen RHS pose.

    Only already observed lower-level occurrences and immutable child
    placements are consulted. A completion shared by different frozen macro
    IDs is rejected rather than target-side tie-broken.
    """
    if minimum_matched_children < 1:
        raise ValueError("partial recognition requires at least one child")
    if not 0 <= minimum_child_coverage <= 1:
        raise ValueError("child coverage must be in [0,1]")
    if pose_tolerance <= 0 or not math.isfinite(pose_tolerance):
        raise ValueError("pose tolerance must be finite and positive")
    if getattr(lower_program, "target_used", False):
        raise ValueError("partial frontier recognition requires a sealed seed")
    parent_type_by_macro = dict(frozen_parent_types)
    if len(parent_type_by_macro) != len(frozen_parent_types):
        raise ValueError("frozen alternative-to-parent map must be unique")
    prototypes = {item.type_id: item for item in lower_program.prototypes}
    occurrences = tuple(lower_program.occurrences)
    if any(item.type_id not in prototypes or
           not is_proper_rotation(item.rotation) for item in occurrences):
        raise ValueError("seed occurrence has unknown type or improper pose")
    occupied = tuple(
        site for occurrence in occurrences
        for site in _render(prototypes[occurrence.type_id],
                            occurrence.rotation, occurrence.translation)
    ) + tuple((species, tuple(float(value) for value in point))
              for species, point in explicit_seed_sites)
    occupied_keys = {_site_key(site, pose_tolerance) for site in occupied}
    observed_by_key = {}
    for occurrence in occurrences:
        key = (occurrence.type_id, _render_key(
            prototypes[occurrence.type_id], occurrence.rotation,
            occurrence.translation, pose_tolerance))
        observed_by_key.setdefault(key, []).append(occurrence.occurrence_id)
    relations = _admitted_relations(lower_program)
    admitted_port_semantics = _admitted_port_semantics(lower_program)

    hypotheses = insufficient = collisions = redundant = port_rejections = outside = 0
    coverage_rejections = 0
    one_child_port_rejections = 0
    proposals = {}
    for macro in admitted_macros:
        placements = tuple(macro.child_placements)
        if len(placements) < minimum_matched_children:
            continue
        seen_macro_poses = set()
        for anchor in placements:
            for occurrence in occurrences:
                if occurrence.type_id != anchor.cluster_type:
                    continue
                anchor_prototype = prototypes[anchor.cluster_type]
                if (minimum_matched_children == 1 and
                        not _has_finite_proper_frame(
                            anchor_prototype, pose_tolerance)):
                    one_child_port_rejections += 1
                    continue
                for symmetry in anchor_prototype.proper_symmetries:
                    hypotheses += 1
                    macro_rotation = matmul(matmul(
                        occurrence.rotation, symmetry),
                        transpose(anchor.rotation))
                    if not is_proper_rotation(macro_rotation):
                        continue
                    macro_translation = _subtract(
                        occurrence.translation,
                        matvec(macro_rotation, anchor.translation))
                    pose_key = (tuple(round(value / pose_tolerance)
                                      for row in macro_rotation for value in row),
                                tuple(round(value / pose_tolerance)
                                      for value in macro_translation))
                    if pose_key in seen_macro_poses:
                        continue
                    seen_macro_poses.add(pose_key)
                    predicted = []
                    slot_occurrences = {}
                    for placement in placements:
                        rotation = matmul(macro_rotation, placement.rotation)
                        translation = _add(
                            macro_translation,
                            matvec(macro_rotation, placement.translation))
                        prototype = prototypes[placement.cluster_type]
                        sites = _render(prototype, rotation, translation)
                        key = (placement.cluster_type, tuple(sorted(
                            _site_key(site, pose_tolerance) for site in sites)))
                        values = observed_by_key.get(key, ())
                        if values:
                            slot_occurrences[placement.node] = min(values)
                        predicted.append((placement, rotation, translation,
                                          sites, bool(values)))
                    connected = _largest_connected_witnesses(
                        macro, slot_occurrences, relations)
                    if (len({slot_occurrences[node] for node in connected}) <
                            minimum_matched_children):
                        if len(slot_occurrences) >= minimum_matched_children:
                            port_rejections += 1
                        else:
                            insufficient += 1
                        continue
                    if (len(connected) / len(placements) + 1e-12 <
                            minimum_child_coverage):
                        coverage_rejections += 1
                        continue
                    connected_set = set(connected)
                    missing_nodes = {item.node for item, _rotation,
                                     _translation, _sites, _found in predicted
                                     if item.node not in connected_set}
                    if (len(connected) == 1 and
                            not _has_frozen_port_to_missing(
                                macro, connected_set, missing_nodes,
                                admitted_port_semantics)):
                        one_child_port_rejections += 1
                        continue
                    missing = tuple(PredictedMacroChild(
                        item.node, item.cluster_type, rotation, translation, sites)
                        for item, rotation, translation, sites, found in predicted
                        if item.node not in connected_set)
                    if not missing:
                        continue
                    if not any(_site_key(site, pose_tolerance)
                               not in occupied_keys
                               for child in missing for site in child.sites):
                        redundant += 1
                        continue
                    if public_boundary is not None and any(
                            math.dist(point, public_boundary.origin) >
                            public_boundary.outer_radius + pose_tolerance
                            for child in missing for _, point in child.sites):
                        outside += 1
                        continue
                    exclusion = max(pose_tolerance,
                                    lower_program.minimum_distance * .45)
                    if any(not _collision_free(child.sites, occupied,
                                               pose_tolerance, exclusion)
                           for child in missing):
                        collisions += 1
                        continue
                    signature = tuple(sorted(
                        (item.cluster_type,
                         _render_key(prototypes[item.cluster_type], rotation,
                                     translation, pose_tolerance))
                        for item, rotation, translation, _sites, _found in
                        predicted))
                    candidate = PartialPromotedCompletion(
                        macro.macro_id, connected,
                        tuple(sorted({slot_occurrences[node]
                                      for node in connected})), missing,
                        macro_rotation, macro_translation, True, False,
                        parent_type_by_macro.get(macro.macro_id))
                    parent_type = parent_type_by_macro.get(
                        macro.macro_id, macro.macro_id)
                    proposals.setdefault(signature, {}).setdefault(
                        parent_type, {})[macro.macro_id] = candidate
    ambiguous = sum(len(parent_types) > 1
                    for parent_types in proposals.values())
    completions = tuple(
        candidate
        for signature, parent_types in sorted(
            proposals.items(), key=lambda item: repr(item[0]))
        if len(parent_types) == 1
        for candidate in next(iter(parent_types.values())).values())
    macro_ids = tuple(item.macro_id for item in admitted_macros)
    return PartialPromotedFrontierAudit(
        len(admitted_macros), len(occurrences), minimum_matched_children,
        hypotheses, insufficient, collisions, redundant, port_rejections,
        coverage_rejections, one_child_port_rejections, outside,
        ambiguous, completions,
        len(set(macro_ids)) == len(macro_ids),
        all(is_proper_rotation(item.macro_rotation) for item in completions),
        False)
