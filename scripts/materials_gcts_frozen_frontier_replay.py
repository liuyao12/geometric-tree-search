#!/usr/bin/env python3
"""Target-blind frontier replay of train-frozen irregular port productions.

Fitting consumes an :class:`IrregularPortProgram` and detaches precisely the
proper cluster prototypes and the finite overlap-port alternatives admitted by
training.  Replay consumes that frozen artifact plus already placed cluster
occurrences.  It never enumerates supports, fits poses, or consults a target
point cloud.  A target is accepted only by :func:`score_replay`, after replay
has terminated, making leakage mechanically difficult rather than a flag in a
benchmark driver.

This is a production *replay* kernel, not yet a learned branch policy.  Its
deterministic policy repeatedly accepts the first maximum-overlap compatible
candidate.  Callers can instead use :func:`enumerate_frontier` as the action
generator of a tree search or GCTS marking policy.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Hashable, Mapping, Sequence

from materials_gcts_irregular_port_atlas import IrregularPortProgram
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, ClusterPrototype, Matrix, OrientedOverlapPort, Vector,
    expand_port_orbit, is_proper_rotation, matmul, matvec)

Site = tuple[Hashable, Vector]
PortKey = tuple[int, int, tuple[int, ...]]


@dataclass(frozen=True)
class RadialBoundary:
    origin: Vector
    outer_radius: float


@dataclass(frozen=True)
class FrontierSeed:
    occurrences: tuple[ClusterOccurrence, ...]
    explicit_gap_sites: tuple[Site, ...] = ()


@dataclass(frozen=True)
class FrozenProduction:
    production_id: int
    parent_type: int
    child_type: int
    port: OrientedOverlapPort
    training_observations: int


@dataclass(frozen=True)
class FrozenFrontierProgram:
    prototypes: tuple[ClusterPrototype, ...]
    productions: tuple[FrozenProduction, ...]
    overlap_tolerance: float
    exclusion_distance: float
    minimum_shared_atoms: int
    training_atoms: int
    family_label_used: bool
    lattice_used: bool
    physical_potential_used: bool
    target_artifacts_stored: bool


@dataclass(frozen=True)
class FrontierCandidate:
    parent_occurrence: int
    production_id: int
    child_type: int
    rotation: Matrix
    translation: Vector
    rendered_sites: tuple[Site, ...]
    overlap_atoms: int
    novel_sites: tuple[Site, ...]
    incoming_port: PortKey | None
    outgoing_port: PortKey


@dataclass(frozen=True)
class FrontierEnumeration:
    candidates: tuple[FrontierCandidate, ...]
    attempted_poses: int
    duplicate_placements: int
    conflicting_placements: int
    insufficient_overlap: int
    interior_placements: int
    outside_boundary: int


@dataclass(frozen=True)
class ReplayResult:
    initial_occurrences: int
    placed_occurrences: tuple[ClusterOccurrence, ...]
    initial_sites: tuple[Site, ...]
    initial_oriented_sites: int
    explicit_seed_gap_sites: int
    sites: tuple[Site, ...]
    accepted_productions: tuple[int, ...]
    frontier_rounds: int
    attempted_poses: int
    rejected_conflicts: int
    rejected_outside_boundary: int
    exhausted: bool
    target_used_for_proposals: bool

    @property
    def novel_atom_count(self) -> int:
        return len(self.sites) - len(self.initial_sites)


@dataclass(frozen=True)
class ReplayScore:
    target_atoms: int
    heldout_target_atoms: int
    proposed_novel_atoms: int
    correct_novel_atoms: int
    precision: float
    heldout_recall: float
    target_used_for_proposals: bool


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(left[axis] + right[axis] for axis in range(3))  # type: ignore[return-value]


def _subtract(left: Vector, right: Vector) -> Vector:
    return tuple(left[axis] - right[axis] for axis in range(3))  # type: ignore[return-value]


def _site_key(site: Site, tolerance: float) -> tuple[str, int, int, int]:
    species, point = site
    return ((f"{type(species).__module__}.{type(species).__qualname__}:"
             f"{species!r}"),) + tuple(round(value / tolerance)
                                      for value in point)  # type: ignore[return-value]


def _pose_key(occurrence: ClusterOccurrence,
              tolerance: float) -> tuple[int, ...]:
    return ((occurrence.type_id,) + tuple(
        round(value / tolerance)
        for row in occurrence.rotation for value in row) + tuple(
        round(value / tolerance) for value in occurrence.translation))


def _render(prototype: ClusterPrototype, rotation: Matrix,
            translation: Vector) -> tuple[Site, ...]:
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def fit_frozen_frontier_program(
    training: IrregularPortProgram, *, overlap_tolerance: float = .03,
    exclusion_distance: float | None = None,
) -> FrozenFrontierProgram:
    """Detach the finite production grammar; retain no training occurrences."""
    if overlap_tolerance <= 0:
        raise ValueError("overlap tolerance must be positive")
    exclusion = (max(overlap_tolerance, training.cover.minimum_distance * .45)
                 if exclusion_distance is None else exclusion_distance)
    if exclusion < overlap_tolerance:
        raise ValueError("exclusion distance cannot be below overlap tolerance")
    prototype_ids = {prototype.type_id for prototype in training.prototypes}
    productions = []
    for production_id, port in enumerate(training.atlas.ports):
        if port.parent_type not in prototype_ids or port.child_type not in prototype_ids:
            raise ValueError("training port references an absent prototype")
        productions.append(FrozenProduction(
            production_id, port.parent_type, port.child_type, port,
            port.observations))
    return FrozenFrontierProgram(
        training.prototypes, tuple(productions), overlap_tolerance, exclusion,
        training.minimum_shared_atoms, training.cover.point_count,
        training.family_label_used, training.lattice_used,
        training.physical_potential_used, False)


def _placed_sites(
    program: FrozenFrontierProgram,
    occurrences: Sequence[ClusterOccurrence],
    explicit_gap_sites: Sequence[Site] = (),
) -> tuple[Site, ...]:
    prototypes = {prototype.type_id: prototype
                  for prototype in program.prototypes}
    unique = {}
    for occurrence in occurrences:
        if occurrence.type_id not in prototypes:
            raise ValueError("seed occurrence has an unknown frozen type")
        if not is_proper_rotation(occurrence.rotation):
            raise ValueError("seed occurrence uses an improper pose")
        for site in _render(prototypes[occurrence.type_id],
                            occurrence.rotation, occurrence.translation):
            key = _site_key(site, program.overlap_tolerance)
            if key in unique and math.dist(unique[key][1], site[1]) > (
                    program.overlap_tolerance):
                raise ValueError("quantized seed-site collision")
            unique[key] = site
    for site in explicit_gap_sites:
        species, point = site
        normalized: Site = (species, tuple(float(value) for value in point))  # type: ignore[assignment]
        if not all(math.isfinite(value) for value in normalized[1]):
            raise ValueError("explicit gap coordinates must be finite")
        key = _site_key(normalized, program.overlap_tolerance)
        if key in unique and unique[key][0] != species:
            raise ValueError("explicit gap conflicts with an oriented seed site")
        unique[key] = normalized
    return tuple(unique[key] for key in sorted(unique))


def _classify_candidate(
    sites: Sequence[Site], occupied: Sequence[Site],
    overlap_tolerance: float, exclusion_distance: float,
) -> tuple[int, tuple[Site, ...], bool]:
    overlap = 0
    novel = []
    for species, point in sites:
        matches = [(known_species, known_point)
                   for known_species, known_point in occupied
                   if math.dist(point, known_point) <= overlap_tolerance]
        if matches:
            if any(known_species != species for known_species, _ in matches):
                return 0, (), True
            overlap += 1
            continue
        if any(math.dist(point, known_point) < exclusion_distance
               for _, known_point in occupied):
            return 0, (), True
        novel.append((species, point))
    return overlap, tuple(novel), False


class _SpatialSiteIndex:
    """Incremental exact-radius cell list for occupied replay sites."""

    def __init__(self, sites: Sequence[Site], cell_size: float):
        self.cell_size = cell_size
        self.cells = defaultdict(list)
        self.extend(sites)

    def _cell(self, point: Vector) -> tuple[int, int, int]:
        return tuple(math.floor(value / self.cell_size)
                     for value in point)  # type: ignore[return-value]

    def _nearby(self, point: Vector):
        center = self._cell(point)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    yield from self.cells.get((
                        center[0] + dx, center[1] + dy,
                        center[2] + dz), ())

    def extend(self, sites: Sequence[Site]) -> None:
        for site in sites:
            self.cells[self._cell(site[1])].append(site)

    def classify(
        self, sites: Sequence[Site], overlap_tolerance: float,
        exclusion_distance: float,
    ) -> tuple[int, tuple[Site, ...], bool]:
        overlap = 0
        novel = []
        for species, point in sites:
            nearby = tuple(self._nearby(point))
            matches = tuple(
                (known_species, known_point)
                for known_species, known_point in nearby
                if math.dist(point, known_point) <= overlap_tolerance)
            if matches:
                if any(known_species != species
                       for known_species, _ in matches):
                    return 0, (), True
                overlap += 1
                continue
            if any(math.dist(point, known_point) < exclusion_distance
                   for _, known_point in nearby):
                return 0, (), True
            novel.append((species, point))
        return overlap, tuple(novel), False


def enumerate_frontier(
    program: FrozenFrontierProgram,
    placed_occurrences: Sequence[ClusterOccurrence],
    *, explicit_gap_sites: Sequence[Site] = (),
    boundary: RadialBoundary | None = None,
    incoming_ports: Mapping[int, PortKey] | None = None,
    _occupied_index: _SpatialSiteIndex | None = None,
    _existing_poses: set[tuple[int, ...]] | None = None,
    _orbit_cache: dict[int, tuple[tuple[Matrix, Vector], ...]] | None = None,
) -> FrontierEnumeration:
    """Enumerate actions solely by composing frozen ports with placed poses."""
    prototypes = {prototype.type_id: prototype
                  for prototype in program.prototypes}
    productions_by_parent: dict[int, list[FrozenProduction]] = {}
    for production in program.productions:
        productions_by_parent.setdefault(
            production.parent_type, []).append(production)
    if boundary is not None and (
            boundary.outer_radius <= 0 or
            not all(math.isfinite(value) for value in boundary.origin) or
            not math.isfinite(boundary.outer_radius)):
        raise ValueError("radial boundary must be finite with positive radius")
    occupied_index = _occupied_index
    if occupied_index is None:
        occupied_index = _SpatialSiteIndex(_placed_sites(
            program, placed_occurrences, explicit_gap_sites),
            program.exclusion_distance)
    existing_poses = (_existing_poses if _existing_poses is not None else
                      {_pose_key(occurrence, program.overlap_tolerance)
                       for occurrence in placed_occurrences})
    orbit_cache = _orbit_cache if _orbit_cache is not None else {}
    candidates = {}
    attempted = duplicates = conflicts = insufficient = interior = outside = 0
    for parent in placed_occurrences:
        parent_prototype = prototypes[parent.type_id]
        for production in productions_by_parent.get(parent.type_id, ()):
            child_prototype = prototypes[production.child_type]
            orbit = orbit_cache.get(production.production_id)
            if orbit is None:
                orbit = expand_port_orbit(
                    parent_prototype, child_prototype, production.port,
                    program.overlap_tolerance)
                orbit_cache[production.production_id] = orbit
            for relative_rotation, relative_translation in orbit:
                attempted += 1
                rotation = matmul(parent.rotation, relative_rotation)
                translation = _add(
                    parent.translation,
                    matvec(parent.rotation, relative_translation))
                occurrence = ClusterOccurrence(
                    -1, production.child_type, rotation, translation)
                pose_key = _pose_key(occurrence, program.overlap_tolerance)
                if pose_key in existing_poses:
                    duplicates += 1
                    continue
                rendered = _render(child_prototype, rotation, translation)
                if boundary is not None and any(
                        math.dist(point, boundary.origin) >
                        boundary.outer_radius + program.overlap_tolerance
                        for _, point in rendered):
                    outside += 1
                    continue
                overlap, novel, conflict = occupied_index.classify(
                    rendered, program.overlap_tolerance,
                    program.exclusion_distance)
                if conflict:
                    conflicts += 1
                    continue
                if overlap < program.minimum_shared_atoms:
                    insufficient += 1
                    continue
                if not novel:
                    interior += 1
                    continue
                rendered_key = tuple(sorted(
                    _site_key(site, program.overlap_tolerance)
                    for site in rendered))
                candidate = FrontierCandidate(
                    parent.occurrence_id, production.production_id,
                    production.child_type, rotation, translation,
                    rendered, overlap, novel,
                    (incoming_ports or {}).get(parent.occurrence_id),
                    (production.port.parent_type,
                     production.port.child_type,
                     production.port.symmetry_orbit_key))
                prior = candidates.get(rendered_key)
                if prior is None or (
                        -candidate.overlap_atoms, candidate.production_id,
                        candidate.parent_occurrence) < (
                        -prior.overlap_atoms, prior.production_id,
                        prior.parent_occurrence):
                    candidates[rendered_key] = candidate
                else:
                    duplicates += 1
    ordered = tuple(sorted(candidates.values(), key=lambda candidate: (
        -candidate.overlap_atoms, -len(candidate.novel_sites),
        candidate.production_id, candidate.child_type,
        tuple(_site_key(site, program.overlap_tolerance)
              for site in candidate.rendered_sites))))
    return FrontierEnumeration(
        ordered, attempted, duplicates, conflicts, insufficient, interior,
        outside)


def seed_patch_from_training(
    training: IrregularPortProgram, species: Sequence[Hashable],
    positions: Sequence[Sequence[float]],
) -> FrontierSeed:
    """Make every non-oriented training atom an explicit inert seed gap."""
    if len(species) != training.cover.point_count or len(positions) != len(species):
        raise ValueError("seed cloud does not match the training point count")
    oriented = {index for _, support in training.occurrence_supports
                for index in support}
    gaps = tuple((species[index], tuple(float(value) for value in positions[index]))
                 for index in range(len(positions)) if index not in oriented)
    return FrontierSeed(training.occurrences, gaps)


def replay_frontier(
    program: FrozenFrontierProgram,
    seed_occurrences: Sequence[ClusterOccurrence] | FrontierSeed, *,
    maximum_steps: int = 100,
    boundary: RadialBoundary | None = None,
    ranker: Callable[[FrontierCandidate], object] | None = None,
) -> ReplayResult:
    """Greedily replay frozen productions without a target or oracle callback."""
    if maximum_steps < 0:
        raise ValueError("maximum steps cannot be negative")
    seed = (seed_occurrences if isinstance(seed_occurrences, FrontierSeed)
            else FrontierSeed(tuple(seed_occurrences)))
    if not seed.occurrences:
        raise ValueError("at least one placed seed occurrence is required")
    placed = [ClusterOccurrence(
        index, occurrence.type_id, occurrence.rotation, occurrence.translation)
        for index, occurrence in enumerate(seed.occurrences)]
    oriented_initial = _placed_sites(program, placed)
    initial_sites = _placed_sites(program, placed, seed.explicit_gap_sites)
    occupied_by_key = {
        _site_key(site, program.overlap_tolerance): site
        for site in initial_sites}
    occupied_index = _SpatialSiteIndex(
        initial_sites, program.exclusion_distance)
    existing_poses = {_pose_key(occurrence, program.overlap_tolerance)
                      for occurrence in placed}
    orbit_cache = {}
    accepted = []
    attempted = conflicts = outside = rounds = 0
    incoming_ports: dict[int, PortKey] = {}
    exhausted = False
    for _ in range(maximum_steps):
        frontier = enumerate_frontier(
            program, placed, explicit_gap_sites=seed.explicit_gap_sites,
            boundary=boundary, incoming_ports=incoming_ports,
            _occupied_index=occupied_index,
            _existing_poses=existing_poses, _orbit_cache=orbit_cache)
        rounds += 1
        attempted += frontier.attempted_poses
        conflicts += frontier.conflicting_placements
        outside += frontier.outside_boundary
        if not frontier.candidates:
            exhausted = True
            break
        candidate = (min(frontier.candidates, key=ranker)
                     if ranker is not None else frontier.candidates[0])
        occurrence = ClusterOccurrence(
            len(placed), candidate.child_type,
            candidate.rotation, candidate.translation)
        placed.append(occurrence)
        existing_poses.add(_pose_key(
            occurrence, program.overlap_tolerance))
        new_sites = []
        for site in candidate.novel_sites:
            key = _site_key(site, program.overlap_tolerance)
            if key not in occupied_by_key:
                occupied_by_key[key] = site
                new_sites.append(site)
        occupied_index.extend(new_sites)
        accepted.append(candidate.production_id)
        incoming_ports[len(placed) - 1] = candidate.outgoing_port
    sites = tuple(occupied_by_key[key] for key in sorted(occupied_by_key))
    return ReplayResult(
        len(seed.occurrences), tuple(placed), initial_sites,
        len(oriented_initial), len(seed.explicit_gap_sites), sites,
        tuple(accepted), rounds, attempted, conflicts, outside,
        exhausted, False)


def _matched_indices(source: Sequence[Site], target: Sequence[Site],
                     tolerance: float) -> set[int]:
    matched = set()
    for species, point in source:
        choices = [index for index, (target_species, target_point) in
                   enumerate(target) if index not in matched and
                   target_species == species and
                   math.dist(point, target_point) <= tolerance]
        if choices:
            matched.add(min(choices, key=lambda index:
                            math.dist(point, target[index][1])))
    return matched


def score_replay(
    result: ReplayResult, target_species: Sequence[Hashable],
    target_positions: Sequence[Sequence[float]], *, tolerance: float = .03,
) -> ReplayScore:
    """Compare a completed replay to held-out atoms; never generate actions."""
    if len(target_species) != len(target_positions):
        raise ValueError("target species and positions must have equal length")
    if tolerance <= 0:
        raise ValueError("score tolerance must be positive")
    target = tuple((species, tuple(float(value) for value in point))
                   for species, point in zip(target_species, target_positions))
    initial_target = _matched_indices(result.initial_sites, target, tolerance)
    heldout = set(range(len(target))).difference(initial_target)
    initial_keys = {_site_key(site, tolerance) for site in result.initial_sites}
    proposed = tuple(site for site in result.sites
                     if _site_key(site, tolerance) not in initial_keys)
    correct = _matched_indices(proposed, target, tolerance).intersection(heldout)
    return ReplayScore(
        len(target), len(heldout), len(proposed), len(correct),
        len(correct) / max(1, len(proposed)),
        len(correct) / max(1, len(heldout)),
        result.target_used_for_proposals)
