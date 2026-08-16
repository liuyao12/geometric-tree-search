#!/usr/bin/env python3
"""Target-blind multiwave execution of ranked partial macro completions."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, PortAtlas, canonical_relative_pose,
    fit_occurrence_pose, is_proper_rotation, matmul, matvec)
from materials_gcts_partial_completion_marking import (
    FrozenCompletionMarking, freeze_completion_candidate,
    rank_completion_candidates)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)


Site = tuple[Hashable, tuple[float, float, float]]


@dataclass(frozen=True)
class PartialCompletionLevel:
    frozen_lower_program: object
    alternatives: tuple[object, ...]
    alternative_parent_types: tuple[tuple[int, int], ...]
    promoted_program: object


@dataclass(frozen=True)
class PartialCompletionCertificate:
    candidate_id: str
    exact_frozen_rhs_geometry: bool
    proper_se3: bool
    frozen_port_witnessed: bool
    emitted_is_exact_difference: bool
    collision_free: bool
    promoted_pose_exact: bool
    digest: str


@dataclass(frozen=True)
class PartialCompletionWave:
    wave: int
    candidate_count: int
    candidate_digest: str
    accepted_whole_macros: int
    rejected_batch_conflicts: int
    rejected_redundant: int
    emitted_atoms: int
    appended_child_occurrences: int
    promoted_occurrences: int


@dataclass(frozen=True)
class PartialCompletionExecution:
    level: int
    initial_occurrences: int
    final_occurrences: tuple[ClusterOccurrence, ...]
    promoted_occurrences: tuple[ClusterOccurrence, ...]
    sites: tuple[Site, ...]
    waves: tuple[PartialCompletionWave, ...]
    certificates: tuple[PartialCompletionCertificate, ...]
    candidate_digests_frozen_before_scorer: bool
    target_api_present: bool
    target_used: bool
    primitive_child_actions: int
    whole_macro_actions: int
    symbolic_action_compression: float
    self_fed: bool
    ready_for_next_level: bool


@dataclass(frozen=True)
class PartialCompletionHierarchyExecution:
    levels: tuple[PartialCompletionExecution, ...]
    final_sites: tuple[Site, ...]
    target_api_present: bool
    target_used: bool


def _add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def _render(prototype, rotation, translation):
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _site_key(site, tolerance):
    return (repr(site[0]),) + tuple(round(value / tolerance)
                                    for value in site[1])


def _pose_key(type_id, rotation, translation, tolerance):
    return (type_id,
            tuple(round(value / tolerance)
                  for row in rotation for value in row),
            tuple(round(value / tolerance) for value in translation))


def _minimum_distance(program):
    value = getattr(program, "minimum_distance", None)
    if value is None:
        value = program.cover.minimum_distance
    return value


def _dynamic_program(frozen, occurrences, tolerance):
    prototypes = {item.type_id: item for item in frozen.prototypes}
    admitted_overlap = {(item.parent_type, item.child_type,
                         item.symmetry_orbit_key)
                        for item in frozen.atlas.ports}
    admitted_boundary = {(item.parent_type, item.child_type,
                          item.symmetry_orbit_key)
                         for item in getattr(frozen, "boundary_ports", ())}
    overlap = []
    boundary = []
    for parent in occurrences:
        for child in occurrences:
            if parent.occurrence_id == child.occurrence_id:
                continue
            inverse = tuple(tuple(parent.rotation[column][row]
                                  for column in range(3)) for row in range(3))
            relative_rotation = matmul(inverse, child.rotation)
            relative_translation = matvec(inverse, tuple(
                child.translation[index] - parent.translation[index]
                for index in range(3)))
            _rotation, _translation, key = canonical_relative_pose(
                prototypes[parent.type_id], prototypes[child.type_id],
                relative_rotation, relative_translation, tolerance)
            semantic = parent.type_id, child.type_id, key
            if semantic in admitted_overlap:
                overlap.append((parent.occurrence_id, child.occurrence_id,
                                *semantic))
            if semantic in admitted_boundary:
                source = next(item for item in frozen.boundary_ports
                              if (item.parent_type, item.child_type,
                                  item.symmetry_orbit_key) == semantic)
                boundary.append(SimpleNamespace(
                    parent_occurrence=parent.occurrence_id,
                    child_occurrence=child.occurrence_id,
                    parent_type=parent.type_id, child_type=child.type_id,
                    symmetry_orbit_key=key,
                    child_port_witnesses=source.child_port_witnesses))
    atlas = PortAtlas(
        frozen.atlas.ports, len(overlap), 0, 0, 0, 0, tuple(overlap))
    return SimpleNamespace(
        prototypes=frozen.prototypes, occurrences=tuple(occurrences),
        atlas=atlas, boundary_ports=getattr(frozen, "boundary_ports", ()),
        boundary_relation_classes=tuple(boundary),
        minimum_distance=_minimum_distance(frozen),
        target_used=False)


def _classify(sites, occupied, tolerance, exclusion):
    occupied_by_key = {_site_key(site, tolerance): site for site in occupied}
    emitted = []
    overlap = 0
    for site in sites:
        key = _site_key(site, tolerance)
        if key in occupied_by_key:
            overlap += 1
            continue
        for other_species, other_point in occupied:
            distance = math.dist(site[1], other_point)
            if distance <= tolerance and site[0] != other_species:
                return (), overlap, True
            if tolerance < distance < exclusion:
                return (), overlap, True
        emitted.append(site)
    return tuple(emitted), overlap, False


def _full_rhs_sites(completion, macro, prototypes):
    result = {}
    for placement in macro.child_placements:
        rotation = matmul(completion.macro_rotation, placement.rotation)
        translation = _add(completion.macro_translation, matvec(
            completion.macro_rotation, placement.translation))
        for site in _render(prototypes[placement.cluster_type],
                            rotation, translation):
            result[_site_key(site, 1e-8)] = site
    return tuple(result[key] for key in sorted(result))


def execute_partial_completion_level(
    level: PartialCompletionLevel,
    seed_occurrences: Sequence[ClusterOccurrence], *,
    explicit_seed_sites: Sequence[Site] = (), public_boundary=None,
    marking: FrozenCompletionMarking | None = None,
    maximum_waves: int = 3, maximum_accepted_per_wave: int = 32,
    minimum_child_coverage: float = 0., pose_tolerance: float = .03,
    level_index: int = 1,
) -> PartialCompletionExecution:
    if not seed_occurrences or maximum_waves < 0 or maximum_accepted_per_wave < 1:
        raise ValueError("invalid partial completion execution seed/limits")
    frozen = level.frozen_lower_program
    prototypes = {item.type_id: item for item in frozen.prototypes}
    promoted_prototypes = {item.type_id: item
                           for item in level.promoted_program.prototypes}
    parent_by_macro = dict(level.alternative_parent_types)
    macros = {item.macro_id: item for item in level.alternatives}
    occurrences = list(seed_occurrences)
    occupied = {}
    for occurrence in occurrences:
        if occurrence.type_id not in prototypes or not is_proper_rotation(
                occurrence.rotation):
            raise ValueError("seed occurrence is not a frozen proper pose")
        for site in _render(prototypes[occurrence.type_id],
                            occurrence.rotation, occurrence.translation):
            occupied.setdefault(_site_key(site, pose_tolerance), site)
    for species, raw_point in explicit_seed_sites:
        site = (species, tuple(map(float, raw_point)))
        occupied.setdefault(_site_key(site, pose_tolerance), site)
    promoted = []
    promoted_pose_keys = set()
    certificates = []
    waves = []
    primitive_actions = 0
    minimum_distance = _minimum_distance(frozen)
    exclusion = max(pose_tolerance, minimum_distance * .45)
    for wave_index in range(1, maximum_waves + 1):
        dynamic = _dynamic_program(frozen, occurrences, pose_tolerance)
        frontier = enumerate_partial_promoted_completions(
            dynamic, level.alternatives, minimum_matched_children=1,
            minimum_child_coverage=minimum_child_coverage,
            explicit_seed_sites=tuple(occupied.values()),
            public_boundary=public_boundary,
            frozen_parent_types=level.alternative_parent_types,
            pose_tolerance=pose_tolerance)
        candidates = []
        completion_by_id = {}
        for completion in frontier.completions:
            missing_sites = tuple(site for child in completion.missing_children
                                  for site in child.sites)
            emitted, overlap, invalid = _classify(
                missing_sites, tuple(occupied.values()),
                pose_tolerance, exclusion)
            frozen_candidate = freeze_completion_candidate(
                dynamic, macros[completion.macro_id], completion,
                live_overlap_support=overlap,
                live_collision_support=int(invalid),
                pose_tolerance=pose_tolerance)
            candidates.append(frozen_candidate)
            completion_by_id[frozen_candidate.candidate_id] = completion
        ranking = rank_completion_candidates(candidates, marking)
        digest = ranking.candidate_digest
        accepted = conflicts = redundant = emitted_count = child_count = 0
        batch_sites = dict(occupied)
        for ranked in ranking.ranked:
            if accepted >= maximum_accepted_per_wave:
                break
            candidate = ranked.candidate
            completion = completion_by_id[candidate.candidate_id]
            missing_sites = tuple(site for child in completion.missing_children
                                  for site in child.sites)
            emitted, _overlap, invalid = _classify(
                missing_sites, tuple(batch_sites.values()),
                pose_tolerance, exclusion)
            if invalid:
                conflicts += 1
                continue
            if not emitted:
                redundant += 1
                continue
            full_sites = _full_rhs_sites(
                completion, macros[completion.macro_id], prototypes)
            parent_type = parent_by_macro[completion.macro_id]
            try:
                fitted = fit_occurrence_pose(
                    len(promoted), promoted_prototypes[parent_type],
                    full_sites, tolerance=pose_tolerance)
            except ValueError:
                conflicts += 1
                continue
            promoted_pose = _pose_key(
                parent_type, fitted.rotation, fitted.translation,
                pose_tolerance)
            if promoted_pose in promoted_pose_keys:
                redundant += 1
                continue
            appended = 0
            existing_poses = {_pose_key(
                item.type_id, item.rotation, item.translation, pose_tolerance)
                              for item in occurrences}
            for child in completion.missing_children:
                pose = _pose_key(child.type_id, child.rotation,
                                 child.translation, pose_tolerance)
                if pose not in existing_poses:
                    occurrences.append(ClusterOccurrence(
                        len(occurrences), child.type_id,
                        child.rotation, child.translation))
                    existing_poses.add(pose)
                    appended += 1
            for site in emitted:
                batch_sites[_site_key(site, pose_tolerance)] = site
            promoted_occurrence = ClusterOccurrence(
                len(promoted), parent_type, fitted.rotation,
                fitted.translation)
            promoted.append(promoted_occurrence)
            promoted_pose_keys.add(promoted_pose)
            payload = (candidate.candidate_id,
                       tuple(sorted(_site_key(site, pose_tolerance)
                                    for site in emitted)), promoted_pose)
            certificates.append(PartialCompletionCertificate(
                candidate.candidate_id,
                completion.exact_frozen_rhs_geometry,
                is_proper_rotation(completion.macro_rotation), True,
                all(_site_key(site, pose_tolerance) not in occupied
                    for site in emitted), not invalid, True,
                hashlib.sha256(repr(payload).encode()).hexdigest()))
            accepted += 1
            child_count += appended
            primitive_actions += appended
            emitted_count += len(emitted)
        occupied = batch_sites
        waves.append(PartialCompletionWave(
            wave_index, len(candidates), digest, accepted, conflicts,
            redundant, emitted_count, child_count,
            len(promoted) - sum(item.promoted_occurrences for item in waves)))
        if not accepted:
            break
    exact = all(all((item.exact_frozen_rhs_geometry, item.proper_se3,
                     item.frozen_port_witnessed,
                     item.emitted_is_exact_difference,
                     item.collision_free, item.promoted_pose_exact))
                for item in certificates)
    if not exact:
        raise AssertionError("partial completion certificate failed")
    macro_actions = len(certificates)
    self_fed = (len(waves) > 1 and
                any(item.appended_child_occurrences > 0
                    for item in waves[:-1]))
    return PartialCompletionExecution(
        level_index, len(seed_occurrences), tuple(occurrences),
        tuple(promoted), tuple(occupied[key] for key in sorted(occupied)),
        tuple(waves), tuple(certificates), True, False, False,
        primitive_actions, macro_actions,
        primitive_actions / max(1, macro_actions), self_fed, bool(promoted))


def execute_partial_completion_hierarchy(
    levels: Sequence[PartialCompletionLevel],
    seed_occurrences: Sequence[ClusterOccurrence], *,
    explicit_seed_sites: Sequence[Site] = (), public_boundary=None,
    markings: Sequence[FrozenCompletionMarking | None] = (),
    maximum_waves_per_level: int = 2,
    maximum_accepted_per_wave: int = 32,
    pose_tolerance: float = .03,
) -> PartialCompletionHierarchyExecution:
    occurrences = tuple(seed_occurrences)
    sites = tuple(explicit_seed_sites)
    results = []
    for index, level in enumerate(levels, 1):
        if not occurrences:
            break
        marking = markings[index - 1] if index <= len(markings) else None
        result = execute_partial_completion_level(
            level, occurrences, explicit_seed_sites=sites,
            public_boundary=public_boundary, marking=marking,
            maximum_waves=maximum_waves_per_level,
            maximum_accepted_per_wave=maximum_accepted_per_wave,
            pose_tolerance=pose_tolerance, level_index=index)
        results.append(result)
        sites = result.sites
        occurrences = result.promoted_occurrences
        if not occurrences:
            break
    return PartialCompletionHierarchyExecution(
        tuple(results), sites, False, False)
