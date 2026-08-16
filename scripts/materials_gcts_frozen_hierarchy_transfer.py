#!/usr/bin/env python3
"""Strict deployment of a train-frozen recursive macro hierarchy.

This module never mines, quotients, or renumbers a target artifact.  Exact
train productions (and their exact derivation alternatives) are matched on a
target port graph, assigned to a frozen quotient type only when that assignment
is unique, and fitted to the already frozen next-level prototype.  Target
relations are retained only when their semantic class was admitted on train.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_dense_macro_matching import (
    _render_union, match_dense_macro_types)
from materials_gcts_macro_promotion import (
    MacroBoundaryRelation, PromotedMacroProgram)
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, PortAtlas, canonical_relative_pose,
    fit_occurrence_pose, learn_overlap_ports, matmul, matvec, transpose)


@dataclass(frozen=True)
class FrozenTransferLevel:
    level: int
    frozen_types: int
    transferred_types: int
    exact_representative_types: int
    safe_backoff_types: int
    occurrences: int
    occurrence_multiplicity_by_type: tuple[tuple[int, int], ...]
    minimum_independent_occurrences_per_frozen_type: int
    minimum_distinct_namespaces_per_frozen_type: int
    every_frozen_type_transferred: bool
    covered_atoms: int
    gap_atoms: int
    coverage: float
    ambiguous_supports: int
    cross_namespace_rejections: int
    pose_rejections: int
    exact_replay: bool
    explicit_residual_atoms: int
    raw_atom_digest: str
    exact_representation_digest: str
    complete_representation_certificate: bool
    frozen_type_ids_preserved: bool
    admitted_overlap_semantics_only: bool
    admitted_boundary_semantics_only: bool
    active_frozen_type_ids: tuple[int, ...] = ()
    inactive_frozen_type_ids: tuple[int, ...] = ()
    minimum_independent_occurrences_per_active_type: int = 0
    minimum_distinct_namespaces_per_active_type: int = 0
    partial_deployment_safe: bool = False


@dataclass(frozen=True)
class FrozenTransferStep:
    program: PromotedMacroProgram
    audit: FrozenTransferLevel


def _subtract(left, right):
    return tuple(left[i] - right[i] for i in range(3))


def _site_key(site, tolerance):
    return (repr(site[0]),) + tuple(round(value / tolerance)
                                    for value in site[1])


def _render_occurrence(occurrence, prototype):
    return tuple((species, tuple(
        matvec(occurrence.rotation, point)[axis] +
        occurrence.translation[axis] for axis in range(3)))
                 for species, point in prototype.sites)


def _alternative_type_map(quotient):
    """Map quotient-exported alternative IDs to their unique frozen class."""
    result = {}
    cursor = 0
    for geometry in quotient.derivation_classes:
        for _alternative in geometry.alternatives:
            if cursor >= len(quotient.alternative_macros):
                raise ValueError("incomplete frozen alternative vocabulary")
            result[quotient.alternative_macros[cursor].macro_id] = \
                geometry.geometry_class_id
            cursor += 1
    if cursor != len(quotient.alternative_macros):
        raise ValueError("unmapped frozen derivation alternative")
    return result


def _lower_relations(program):
    admitted_overlap = {(p.parent_type, p.child_type, p.symmetry_orbit_key)
                        for p in program.atlas.ports}
    relations = {(a, b) for a, b, pt, ct, key in
                 program.atlas.relation_classes
                 if (pt, ct, key) in admitted_overlap}
    admitted_boundary = {
        (p.parent_type, p.child_type, p.symmetry_orbit_key)
        for p in getattr(program, "boundary_ports", ())}
    relations.update((r.parent_occurrence, r.child_occurrence)
                     for r in getattr(program, "boundary_relation_classes", ())
                     if (r.parent_type, r.child_type, r.symmetry_orbit_key)
                     in admitted_boundary)
    return relations


def transfer_frozen_hierarchy_level(
        source_program, quotient, frozen_promoted: PromotedMacroProgram,
        atom_namespaces: Sequence[Hashable], *, pose_tolerance: float = .03,
        raw_atom_sites: Sequence[tuple[Hashable, Sequence[float]]] | None = None,
) -> FrozenTransferStep:
    """Deploy one frozen level, failing closed on class or namespace ambiguity.

    ``atom_namespaces`` names the primitive atom domains.  It is deployment
    metadata only: it prevents a macro from joining independent patches and is
    never used to select a production type.
    """
    support_count = len(atom_namespaces)
    if raw_atom_sites is not None and len(raw_atom_sites) != support_count:
        raise ValueError("raw atom sites and namespaces must align")
    frozen_by_macro = dict(frozen_promoted.prototype_macro_types)
    prototypes = {item.type_id: item for item in frozen_promoted.prototypes}
    if set(frozen_by_macro.values()) != {
            item.macro_id for item in quotient.quotient_macros}:
        raise ValueError("frozen promoted type map does not match quotient")

    proposed = []
    exact_dense = match_dense_macro_types(
        source_program, quotient.quotient_macros,
        pose_tolerance=pose_tolerance)
    for macro in exact_dense.dense_macro_types:
        for occurrence in macro.promotion_occurrences:
            proposed.append((tuple(occurrence.atom_indices), macro.macro_id,
                             occurrence, "exact"))

    alternative_map = _alternative_type_map(quotient)
    if quotient.alternative_macros:
        alternative_dense = match_dense_macro_types(
            source_program, quotient.alternative_macros,
            pose_tolerance=pose_tolerance)
        for macro in alternative_dense.dense_macro_types:
            frozen_type = alternative_map[macro.macro_id]
            for occurrence in macro.promotion_occurrences:
                proposed.append((tuple(occurrence.atom_indices), frozen_type,
                                 occurrence, "backoff"))

    # A support may have several exact derivations but may name only one
    # frozen quotient type.  Otherwise no target-side tie-break is permitted.
    by_support = {}
    for support, macro_id, occurrence, source in proposed:
        by_support.setdefault(support, []).append(
            (macro_id, occurrence, source))
    unambiguous = []
    ambiguous = 0
    for support in sorted(by_support):
        values = by_support[support]
        type_ids = {item[0] for item in values}
        if len(type_ids) != 1:
            ambiguous += 1
            continue
        # Exact representative wins only as a deterministic derivation choice;
        # all choices here have the same frozen quotient type and atom union.
        chosen = min(values, key=lambda item: (
            item[2] != "exact", item[1].node_occurrences))
        unambiguous.append((support, *chosen))

    source_occurrences = {item.occurrence_id: item
                          for item in source_program.occurrences}
    source_prototypes = {item.type_id: item
                         for item in source_program.prototypes}
    occurrences = []
    supports = []
    nodes = {}
    origins = []
    cross_namespace = pose_rejections = 0
    replay_exact = True
    for support, macro_id, macro_occurrence, origin in unambiguous:
        namespaces = {atom_namespaces[index] for index in support}
        if len(namespaces) != 1:
            cross_namespace += 1
            continue
        prototype_id = next((prototype_id for prototype_id, frozen_macro_id
                             in frozen_promoted.prototype_macro_types
                             if frozen_macro_id == macro_id), None)
        if prototype_id is None:
            pose_rejections += 1
            continue
        observed = _render_union(
            macro_occurrence.node_occurrences, source_occurrences,
            source_prototypes, pose_tolerance)
        if observed is None:
            pose_rejections += 1
            continue
        try:
            fitted = fit_occurrence_pose(
                len(occurrences), prototypes[prototype_id], observed,
                tolerance=pose_tolerance)
        except ValueError:
            pose_rejections += 1
            continue
        fitted = ClusterOccurrence(
            len(occurrences), prototype_id, fitted.rotation,
            fitted.translation)
        replay_exact &= ({_site_key(site, pose_tolerance)
                          for site in _render_occurrence(
                              fitted, prototypes[prototype_id])} ==
                         {_site_key(site, pose_tolerance)
                          for site in observed})
        occurrences.append(fitted)
        supports.append((fitted.occurrence_id, support))
        nodes[fitted.occurrence_id] = frozenset(
            macro_occurrence.node_occurrences)
        origins.append(origin)

    # Observe target poses, then intersect with the immutable train atlas.
    memberships = {}
    for occurrence_id, support in supports:
        for atom in support:
            memberships.setdefault(atom, []).append(occurrence_id)
    shared = Counter()
    for values in memberships.values():
        for left in set(values):
            for right in set(values):
                if left != right:
                    shared[left, right] += 1
    allowed = frozenset(pair for pair, count in shared.items()
                        if count >= frozen_promoted.minimum_shared_atoms)
    observed_atlas = learn_overlap_ports(
        frozen_promoted.prototypes, tuple(occurrences),
        minimum_overlap=frozen_promoted.minimum_shared_atoms,
        minimum_observations=1, overlap_tolerance=pose_tolerance,
        exclusion_distance=max(
            pose_tolerance, frozen_promoted.minimum_distance * .45),
        allowed_occurrence_pairs=allowed)
    admitted_overlap = {(p.parent_type, p.child_type, p.symmetry_orbit_key)
                        for p in frozen_promoted.atlas.ports}
    overlap_relations = tuple(
        item for item in observed_atlas.relation_classes
        if (item[2], item[3], item[4]) in admitted_overlap)
    atlas = PortAtlas(
        frozen_promoted.atlas.ports, len(overlap_relations), 0, 0, 0, 0,
        overlap_relations)

    # Transfer boundary relations only if (a) the child macros are connected
    # by an admitted lower-level relation and (b) their relative pose is a
    # train-admitted next-level boundary semantic.
    lower_relations = _lower_relations(source_program)
    admitted_boundary = {
        (p.parent_type, p.child_type, p.symmetry_orbit_key)
        for p in frozen_promoted.boundary_ports}
    boundary_relations = []
    for parent in occurrences:
        for child in occurrences:
            if parent.occurrence_id == child.occurrence_id:
                continue
            witnesses = sum((left, right) in lower_relations
                            for left in nodes[parent.occurrence_id]
                            for right in nodes[child.occurrence_id])
            if not witnesses:
                continue
            inverse = transpose(parent.rotation)
            rotation = matmul(inverse, child.rotation)
            translation = matvec(inverse, _subtract(
                child.translation, parent.translation))
            _, _, key = canonical_relative_pose(
                prototypes[parent.type_id], prototypes[child.type_id],
                rotation, translation, pose_tolerance)
            semantic = parent.type_id, child.type_id, key
            if semantic in admitted_boundary:
                boundary_relations.append(MacroBoundaryRelation(
                    parent.occurrence_id, child.occurrence_id,
                    parent.type_id, child.type_id, key, witnesses))

    program = PromotedMacroProgram(
        frozen_promoted.level, frozen_promoted.source_macro_types,
        frozen_promoted.prototypes, frozen_promoted.prototype_macro_types,
        tuple(occurrences), tuple(supports), atlas,
        frozen_promoted.boundary_ports, tuple(boundary_relations),
        frozen_promoted.minimum_shared_atoms,
        frozen_promoted.minimum_distance, 0, pose_rejections, 0,
        False, False, False, False)
    covered = {atom for _, support in supports for atom in support}
    transferred = {item.type_id for item in occurrences}
    supports_by_type = {prototype.type_id: []
                        for prototype in frozen_promoted.prototypes}
    occurrence_by_id = {item.occurrence_id: item for item in occurrences}
    for occurrence_id, support in supports:
        supports_by_type[occurrence_by_id[occurrence_id].type_id].append(
            frozenset(support))
    multiplicities = []
    independent_counts = []
    namespace_counts = []
    independent_by_type = {}
    namespaces_by_type = {}
    for type_id in sorted(supports_by_type):
        values = supports_by_type[type_id]
        multiplicities.append((type_id, len(values)))
        chosen = []
        for support in sorted(values, key=lambda item: (len(item), tuple(item))):
            if all(not support.intersection(prior) for prior in chosen):
                chosen.append(support)
        independent_counts.append(len(chosen))
        independent_by_type[type_id] = len(chosen)
        namespace_count = len({atom_namespaces[next(iter(support))]
                               for support in values if support})
        namespace_counts.append(namespace_count)
        namespaces_by_type[type_id] = namespace_count
    minimum_independent = min(independent_counts, default=0)
    minimum_namespaces = min(namespace_counts, default=0)
    active_ids = tuple(sorted(transferred))
    inactive_ids = tuple(sorted(set(supports_by_type).difference(transferred)))
    active_independent = tuple(independent_by_type[type_id]
                               for type_id in active_ids)
    active_namespaces = tuple(namespaces_by_type[type_id]
                              for type_id in active_ids)
    minimum_active_independent = min(active_independent, default=0)
    minimum_active_namespaces = min(active_namespaces, default=0)
    every_transferred = (len(transferred) == len(prototypes) and
                         minimum_independent >= 2 and
                         minimum_namespaces >= 2)
    exact_types = {item.type_id for item, origin in zip(occurrences, origins)
                   if origin == "exact"}
    backoff_types = transferred - exact_types
    overlap_ok = all((item[2], item[3], item[4]) in admitted_overlap
                     for item in atlas.relation_classes)
    boundary_ok = all((item.parent_type, item.child_type,
                       item.symmetry_orbit_key) in admitted_boundary
                      for item in boundary_relations)
    residual_indices = tuple(sorted(set(range(support_count)) - covered))
    if raw_atom_sites is None:
        raw_digest = representation_digest = ""
        representation_complete = False
    else:
        def atom_record(index):
            species, position = raw_atom_sites[index]
            return (index, repr(atom_namespaces[index]), repr(species),
                    tuple(round(float(value) / pose_tolerance)
                          for value in position))
        raw_records = tuple(atom_record(index)
                            for index in range(support_count))
        represented_records = tuple(atom_record(index) for index in
                                    sorted(covered)) + tuple(
                                        atom_record(index)
                                        for index in residual_indices)
        raw_digest = hashlib.sha256(repr(raw_records).encode()).hexdigest()
        representation_digest = hashlib.sha256(
            repr(tuple(sorted(represented_records))).encode()).hexdigest()
        representation_complete = (raw_digest == representation_digest and
                                   not covered.intersection(residual_indices))
    type_map_preserved = (
        program.prototype_macro_types == frozen_promoted.prototype_macro_types)
    partial_safe = (bool(occurrences) and replay_exact and
                    representation_complete and type_map_preserved and
                    overlap_ok and boundary_ok)
    audit = FrozenTransferLevel(
        frozen_promoted.level, len(frozen_promoted.prototypes),
        len(transferred), len(exact_types), len(backoff_types),
        len(occurrences), tuple(multiplicities), minimum_independent,
        minimum_namespaces, every_transferred, len(covered),
        len(residual_indices),
        len(covered) / max(1, support_count), ambiguous, cross_namespace,
        pose_rejections, replay_exact, len(residual_indices), raw_digest,
        representation_digest, representation_complete,
        type_map_preserved, overlap_ok, boundary_ok, active_ids, inactive_ids,
        minimum_active_independent, minimum_active_namespaces, partial_safe)
    return FrozenTransferStep(program, audit)
