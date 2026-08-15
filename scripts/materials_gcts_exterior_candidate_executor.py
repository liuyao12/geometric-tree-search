#!/usr/bin/env python3
"""Target-blind one-wave executor for frozen promoted-macro grammars."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Callable, Hashable, Sequence

from materials_gcts_macro_derivation import (
    FrozenMacroProduction, Site, _SpatialSiteIndex, _add, _classify,
    _compile_productions, _match, _pose_key, _production_ports, _render,
    _site_key, _unique_sites)
from materials_gcts_macro_promotion import PromotedMacroProgram
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, Matrix, Vector, expand_port_orbit, matmul, matvec)


@dataclass(frozen=True)
class ExteriorCandidateEvidence:
    parent_occurrence: int
    production_id: int
    production_kind: str
    required_shared_atoms: int
    observations: int
    child_port_witnesses: int


@dataclass(frozen=True)
class ExteriorCandidate:
    candidate_id: str
    child_type: int
    rotation: Matrix
    translation: Vector
    rendered: tuple[Site, ...]
    initial_overlap: tuple[tuple, ...]
    initial_emitted: tuple[Site, ...]
    evidence: tuple[ExteriorCandidateEvidence, ...]


@dataclass(frozen=True)
class FrozenExteriorCandidates:
    candidates: tuple[ExteriorCandidate, ...]
    seed_sites: tuple[Site, ...]
    boundary_origin: Vector
    boundary_radius: float
    pose_tolerance: float
    exclusion_distance: float
    frontier_occurrences: int
    attempted_proposals: int
    rejected_known_poses: int
    duplicate_proposals: int
    rejected_conflicts: int
    rejected_insufficient_overlap: int
    rejected_nonexterior: int
    target_used: bool


@dataclass(frozen=True)
class ExteriorWave:
    candidate_ids: tuple[str, ...]
    accepted_candidate_ids: tuple[str, ...]
    emitted_sites: tuple[Site, ...]
    rejected_batch_conflicts: int
    target_used: bool


@dataclass(frozen=True)
class ExteriorWaveScore:
    target_atoms: int
    proposed_atoms: int
    correct_atoms: int
    precision: float
    continuation_recall: float
    target_used_during_enumeration_or_execution: bool


def _candidate_id(child_type: int, rotation: Matrix, translation: Vector,
                  tolerance: float) -> str:
    payload = repr(_pose_key(
        child_type, rotation, translation, tolerance)).encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def enumerate_exterior_candidates(
    program: PromotedMacroProgram,
    seed_occurrences: Sequence[ClusterOccurrence], *,
    frontier_occurrences: Sequence[ClusterOccurrence] | None = None,
    explicit_seed_sites: Sequence[Site] = (),
    boundary_origin: Sequence[float], boundary_radius: float,
    pose_tolerance: float = .03,
) -> FrozenExteriorCandidates:
    """Enumerate immutable candidates without receiving evaluation atoms."""
    if not seed_occurrences:
        raise ValueError("at least one placed macro occurrence is required")
    origin = tuple(float(value) for value in boundary_origin)
    if (len(origin) != 3 or not all(math.isfinite(value) for value in origin)
            or boundary_radius <= 0 or not math.isfinite(boundary_radius)):
        raise ValueError("boundary needs a finite 3D origin and positive radius")
    prototypes = {item.type_id: item for item in program.prototypes}
    ports = _production_ports(program)
    productions = _compile_productions(program)
    by_parent = {}
    for production in productions:
        by_parent.setdefault(production.parent_type, []).append(production)
    seed_macro_sites = tuple(
        site for occurrence in seed_occurrences
        for site in _render(prototypes[occurrence.type_id],
                            occurrence.rotation, occurrence.translation))
    seed_sites = _unique_sites(
        seed_macro_sites + tuple(explicit_seed_sites), pose_tolerance)
    exclusion = max(pose_tolerance, program.minimum_distance * .45)
    occupied_index = _SpatialSiteIndex(seed_sites, exclusion)
    existing_poses = {_pose_key(
        occurrence.type_id, occurrence.rotation, occurrence.translation,
        pose_tolerance) for occurrence in seed_occurrences}
    frontier = (tuple(seed_occurrences) if frontier_occurrences is None
                else tuple(frontier_occurrences))
    if any(_pose_key(item.type_id, item.rotation, item.translation,
                     pose_tolerance) not in existing_poses
           for item in frontier):
        raise ValueError("frontier occurrence is not already placed")
    orbit_cache = {}
    pose_geometry = {}
    evidence_by_pose = {}
    attempted = known = duplicates = conflicts = insufficient = nonexterior = 0
    for parent in frontier:
        for production in by_parent.get(parent.type_id, ()):
            orbit = orbit_cache.get(production.production_id)
            if orbit is None:
                orbit = expand_port_orbit(
                    prototypes[production.parent_type],
                    prototypes[production.child_type],
                    ports[production.production_id], pose_tolerance)
                orbit_cache[production.production_id] = orbit
            for relative_rotation, relative_translation in orbit:
                attempted += 1
                rotation = matmul(parent.rotation, relative_rotation)
                translation = _add(parent.translation, matvec(
                    parent.rotation, relative_translation))
                pose = _pose_key(production.child_type, rotation,
                                 translation, pose_tolerance)
                if pose in existing_poses:
                    known += 1
                    continue
                geometry = pose_geometry.get(pose)
                if geometry is None:
                    rendered = _render(
                        prototypes[production.child_type], rotation,
                        translation)
                    overlap, emitted, invalid = occupied_index.classify(
                        rendered, pose_tolerance, exclusion)
                    exterior = any(math.dist(site[1], origin) >
                                   boundary_radius + pose_tolerance
                                   for site in emitted)
                    geometry = (production.child_type, rotation, translation,
                                rendered, overlap, emitted, invalid, exterior)
                    pose_geometry[pose] = geometry
                else:
                    duplicates += 1
                _, _, _, _, overlap, emitted, invalid, exterior = geometry
                if invalid:
                    conflicts += 1
                    continue
                if len(overlap) < production.required_shared_atoms:
                    insufficient += 1
                    continue
                if not emitted or not exterior:
                    nonexterior += 1
                    continue
                evidence_by_pose.setdefault(pose, []).append(
                    ExteriorCandidateEvidence(
                        parent.occurrence_id, production.production_id,
                        production.production_kind,
                        production.required_shared_atoms,
                        production.training_observations,
                        production.training_child_port_witnesses))
    candidates = []
    for pose in sorted(evidence_by_pose):
        (child_type, rotation, translation, rendered, overlap, emitted,
         _, _) = pose_geometry[pose]
        evidence = tuple(sorted(set(evidence_by_pose[pose]), key=lambda item: (
            item.production_id, item.parent_occurrence,
            item.production_kind)))
        candidates.append(ExteriorCandidate(
            _candidate_id(child_type, rotation, translation, pose_tolerance),
            child_type, rotation, translation, rendered, overlap, emitted,
            evidence))
    candidates.sort(key=lambda item: item.candidate_id)
    return FrozenExteriorCandidates(
        tuple(candidates), seed_sites, origin, boundary_radius,
        pose_tolerance, exclusion, len(frontier), attempted, known,
        duplicates, conflicts,
        insufficient, nonexterior, False)


def execute_exterior_wave(
    frozen: FrozenExteriorCandidates, *, maximum_candidates: int = 64,
    ranker: Callable[[ExteriorCandidate], object] | None = None,
) -> ExteriorWave:
    """Execute a permutation of one frozen candidate set conflict-free."""
    if maximum_candidates < 1:
        raise ValueError("maximum candidates must be positive")
    candidate_ids = tuple(item.candidate_id for item in frozen.candidates)
    ordered = sorted(
        frozen.candidates,
        key=(lambda item: (ranker(item), item.candidate_id)) if ranker else
        (lambda item: (-max(e.observations for e in item.evidence),
                       -len(item.initial_overlap), item.candidate_id)))
    index = _SpatialSiteIndex(frozen.seed_sites, frozen.exclusion_distance)
    accepted = []
    emitted_all = []
    rejected = 0
    for candidate in ordered:
        if len(accepted) >= maximum_candidates:
            break
        overlap, emitted, invalid = index.classify(
            candidate.rendered, frozen.pose_tolerance,
            frozen.exclusion_distance)
        if invalid or not emitted or not any(
                len(overlap) >= evidence.required_shared_atoms
                for evidence in candidate.evidence):
            rejected += 1
            continue
        index.extend(emitted)
        accepted.append(candidate.candidate_id)
        emitted_all.extend(emitted)
    return ExteriorWave(
        candidate_ids, tuple(accepted), tuple(emitted_all), rejected, False)


def score_exterior_wave(
    frozen: FrozenExteriorCandidates, wave: ExteriorWave,
    target_species: Sequence[Hashable],
    target_positions: Sequence[Sequence[float]], *, tolerance: float = .03,
) -> ExteriorWaveScore:
    """Post-hoc continuation scorer; evaluation atoms enter only here."""
    target = tuple((species, tuple(float(value) for value in point))
                   for species, point in zip(target_species, target_positions))
    seed_keys = {_site_key(site, tolerance) for site in frozen.seed_sites}
    heldout = tuple(site for site in target
                    if _site_key(site, tolerance) not in seed_keys)
    correct = _match(wave.emitted_sites, heldout, tolerance)
    return ExteriorWaveScore(
        len(target), len(wave.emitted_sites), correct,
        correct / max(1, len(wave.emitted_sites)),
        correct / max(1, len(heldout)),
        frozen.target_used or wave.target_used)
