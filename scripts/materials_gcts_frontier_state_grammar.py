#!/usr/bin/env python3
"""Promote recurring frontier waves into scale-normalized cluster states.

The compiler is deliberately material-blind.  It receives only a sequence of
colored point clouds emitted by a target-free growth trace.  Each wave gets an
adaptive nearest-neighbour graph; connected induced subgraphs are then
canonicalized modulo translation, positive uniform scale, and *proper* 3-D
rotation.  Repeated subgraphs become frontier-state types and a deterministic
non-overlapping cover retains explicit residual sites.

This is the missing bridge between finite local continuation and a claim of
recursive amplification.  A stationary witness is intentionally strict: the
same proper colored state must occur in three consecutive waves, its learned
scale ratio must repeat, and the number of uniquely covered atoms must grow by
the same factor greater than one.  Repeated fragments with constant support do
not pass merely because they recur.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_macro_stationary_adapter import _proper_geometry_code
from materials_gcts_oriented_overlap_ports import (
    IDENTITY, ClusterPrototype, Matrix, fit_occurrence_pose, make_prototype,
)

Point = tuple[float, float, float]
Site = tuple[Hashable, Point]


@dataclass(frozen=True)
class FrontierWaveSnapshot:
    wave: int
    positions: tuple[Point, ...]
    species: tuple[Hashable, ...]
    target_used: bool = False


@dataclass(frozen=True)
class FrontierStateOccurrence:
    wave: int
    member_indices: tuple[int, ...]
    scale: float
    translation: Point
    rotation: Matrix
    proper_pose_verified: bool


@dataclass(frozen=True)
class FrontierStateType:
    type_id: int
    support_size: int
    normalized_signature: tuple
    prototype_species: tuple[Hashable, ...]
    prototype_positions: tuple[Point, ...]
    occurrences: tuple[FrontierStateOccurrence, ...]
    independent_waves: int
    description_saving: int


@dataclass(frozen=True)
class FrontierStationaryWitness:
    type_id: int
    waves: tuple[int, int, int]
    learned_scale_ratio: float
    scale_ratios: tuple[float, float]
    covered_atoms: tuple[int, int, int]
    support_growth_ratios: tuple[float, float]


@dataclass(frozen=True)
class FrontierStateGrammar:
    wave_count: int
    atom_count: int
    maximum_nodes: int
    graph_shell_ratio: float
    candidate_subgraphs: int
    normalized_state_types: int
    recurring_state_types: tuple[FrontierStateType, ...]
    selected_occurrences: tuple[tuple[int, int, tuple[int, ...]], ...]
    repeated_covered_atoms: int
    residual_sites: tuple[tuple[int, int, Hashable, Point], ...]
    complete_cover: bool
    proper_pose_occurrences: int
    stationary_witnesses: tuple[FrontierStationaryWitness, ...]
    exponential_gate_passed: bool
    target_used: bool
    grammar_digest: str


def _species_key(value: Hashable) -> str:
    try:
        hash(value)
    except TypeError as error:
        raise ValueError("species labels must be hashable") from error
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _validate_wave(wave: FrontierWaveSnapshot) -> None:
    if wave.wave < 1:
        raise ValueError("wave numbers must be positive")
    if len(wave.positions) != len(wave.species):
        raise ValueError("positions and species must have equal length")
    if not wave.positions:
        raise ValueError("frontier waves must not be empty")
    if any(len(point) != 3 or not all(math.isfinite(value) for value in point)
           for point in wave.positions):
        raise ValueError("wave positions must be finite 3-D points")
    if len(set(wave.positions)) != len(wave.positions):
        raise ValueError("one frontier wave cannot contain duplicate points")
    for species in wave.species:
        _species_key(species)


def _centroid(points: Sequence[Point]) -> Point:
    return tuple(sum(point[axis] for point in points) / len(points)
                 for axis in range(3))  # type: ignore[return-value]


def _subtract(left: Point, right: Point) -> Point:
    return tuple(left[axis] - right[axis]
                 for axis in range(3))  # type: ignore[return-value]


def _scale(point: Point, factor: float) -> Point:
    return tuple(value * factor for value in point)  # type: ignore[return-value]


def _minimum_distance(points: Sequence[Point]) -> float:
    distances = tuple(
        math.dist(left, right)
        for index, left in enumerate(points)
        for right in points[index + 1:]
        if math.dist(left, right) > 1e-10)
    if not distances:
        raise ValueError("a multi-site wave needs separated points")
    return min(distances)


def _graph(points: Sequence[Point], shell_ratio: float):
    minimum = _minimum_distance(points)
    cutoff = minimum * shell_ratio
    adjacency = [set() for _ in points]
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            if math.dist(points[left], points[right]) <= cutoff + 1e-9:
                adjacency[left].add(right)
                adjacency[right].add(left)
    return tuple(frozenset(neighbors) for neighbors in adjacency)


def _connected_subgraphs(adjacency, maximum_nodes: int):
    current = {
        frozenset((left, right))
        for left, neighbors in enumerate(adjacency)
        for right in neighbors if left < right
    }
    for size in range(2, maximum_nodes + 1):
        if size > 2:
            current = {
                frozenset(set(members) | {neighbor})
                for members in current
                for member in members
                for neighbor in adjacency[member]
                if neighbor not in members
            }
        for members in sorted(current, key=lambda item: tuple(sorted(item))):
            yield tuple(sorted(members))


def _metric_code(sites: Sequence[Site], scale: float,
                 tolerance: float) -> tuple:
    profiles = []
    for index, (species, point) in enumerate(sites):
        incident = tuple(sorted(
            (_species_key(other_species),
             round(math.dist(point, other_point) / scale / tolerance))
            for other, (other_species, other_point) in enumerate(sites)
            if other != index))
        profiles.append((_species_key(species), incident))
    return tuple(sorted(profiles))


def _normalized_signature(sites: Sequence[Site], tolerance: float):
    scale = _minimum_distance(tuple(point for _species, point in sites))
    encoded = tuple((_species_key(species), point)
                    for species, point in sites)
    try:
        # This code retains handedness because it enumerates only right-handed
        # intrinsic frames.  Collinear and two-site states have no 3-D chirality
        # and correctly fall back to their complete colored metric graph.
        code = ("proper", _proper_geometry_code(encoded, scale, tolerance))
        proper = True
    except ValueError:
        code = ("metric", _metric_code(sites, scale, tolerance))
        proper = False
    return code, scale, proper


def _normalized_sites(sites: Sequence[Site], scale: float) -> tuple[Site, ...]:
    center = _centroid(tuple(point for _species, point in sites))
    return tuple((species, _scale(_subtract(point, center), 1.0 / scale))
                 for species, point in sites)


def _fit_occurrences(type_id: int, rows, waves, proper: bool,
                     tolerance: float):
    first_wave, first_members, first_scale = rows[0]
    first = waves[first_wave]
    first_sites = tuple((first.species[index], first.positions[index])
                        for index in first_members)
    normalized = _normalized_sites(first_sites, first_scale)
    prototype: ClusterPrototype | None = None
    if proper:
        prototype = make_prototype(type_id, normalized, tolerance)
    occurrences = []
    for wave_index, members, scale in rows:
        wave = waves[wave_index]
        sites = tuple((wave.species[index], wave.positions[index])
                      for index in members)
        center = _centroid(tuple(point for _species, point in sites))
        rotation = IDENTITY
        verified = False
        if prototype is not None:
            fitted = fit_occurrence_pose(
                len(occurrences), prototype, _normalized_sites(sites, scale),
                tolerance)
            rotation = fitted.rotation
            verified = True
        occurrences.append(FrontierStateOccurrence(
            wave.wave, members, scale, center, rotation, verified))
    return normalized, tuple(occurrences)


def _stationary_witnesses(types, tolerance):
    witnesses = []
    for state in types:
        if not state.occurrences or not all(
                occurrence.proper_pose_verified
                for occurrence in state.occurrences):
            # A point or collinear segment has a continuous stabilizer.  It is
            # useful cover evidence, but not a finite oriented GCTS state.
            continue
        by_wave = defaultdict(list)
        for occurrence in state.occurrences:
            by_wave[occurrence.wave].append(occurrence)
        waves = sorted(by_wave)
        for first in waves:
            if first + 1 not in waves or first + 2 not in waves:
                continue
            triple = (first, first + 1, first + 2)
            scales = []
            supports = []
            uniform = True
            for wave in triple:
                rows = by_wave[wave]
                occurrence_scales = tuple(row.scale for row in rows)
                if max(occurrence_scales) - min(occurrence_scales) > \
                        tolerance * max(occurrence_scales):
                    uniform = False
                    break
                scales.append(sum(occurrence_scales) / len(occurrence_scales))
                supports.append(len(set().union(*(
                    set(row.member_indices) for row in rows))))
            if not uniform:
                continue
            scale_ratios = (scales[1] / scales[0], scales[2] / scales[1])
            growth = (supports[1] / supports[0], supports[2] / supports[1])
            if (scale_ratios[0] > 1.0 + tolerance and
                    growth[0] > 1.0 + tolerance and
                    math.isclose(*scale_ratios, rel_tol=tolerance,
                                 abs_tol=tolerance) and
                    math.isclose(*growth, rel_tol=tolerance,
                                 abs_tol=tolerance)):
                witnesses.append(FrontierStationaryWitness(
                    state.type_id, triple, sum(scale_ratios) / 2,
                    scale_ratios, tuple(supports), growth))
    return tuple(witnesses)


def compile_frontier_state_grammar(
    snapshots: Sequence[FrontierWaveSnapshot], *,
    maximum_nodes: int = 5,
    graph_shell_ratio: float = 1.01,
    minimum_independent_waves: int = 2,
    tolerance: float = 1e-6,
) -> FrontierStateGrammar:
    """Compile a complete recurring-state cover from target-free wave traces."""
    if not 2 <= maximum_nodes <= 8:
        raise ValueError("maximum_nodes must be in [2, 8]")
    if graph_shell_ratio < 1.0 or not math.isfinite(graph_shell_ratio):
        raise ValueError("graph_shell_ratio must be finite and at least one")
    if minimum_independent_waves < 2:
        raise ValueError("recurrence needs at least two independent waves")
    if tolerance <= 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    waves = tuple(snapshots)
    if len(waves) < minimum_independent_waves:
        raise ValueError("too few waves for the recurrence requirement")
    for wave in waves:
        _validate_wave(wave)
    if len({wave.wave for wave in waves}) != len(waves):
        raise ValueError("wave numbers must be unique")
    waves = tuple(sorted(waves, key=lambda item: item.wave))
    by_number = {wave.wave: wave for wave in waves}

    groups = defaultdict(list)
    candidate_count = 0
    for wave in waves:
        if len(wave.positions) < 2:
            continue
        adjacency = _graph(wave.positions, graph_shell_ratio)
        for members in _connected_subgraphs(adjacency, maximum_nodes):
            candidate_count += 1
            sites = tuple((wave.species[index], wave.positions[index])
                          for index in members)
            signature, scale, proper = _normalized_signature(sites, tolerance)
            groups[(len(members), signature, proper)].append(
                (wave.wave, members, scale))

    admitted = []
    for key, rows in groups.items():
        support_size, signature, proper = key
        independent = len({wave for wave, _members, _scale in rows})
        saving = len(rows) * support_size - (support_size + len(rows))
        if independent >= minimum_independent_waves and saving > 0:
            admitted.append((key, tuple(sorted(rows)), independent, saving))
    admitted.sort(key=lambda item: (
        -item[0][0], -item[2], -len(item[1]), repr(item[0][1])))

    state_types = []
    for type_id, ((support_size, signature, proper), rows,
                  independent, saving) in enumerate(admitted):
        prototype_sites, occurrences = _fit_occurrences(
            type_id, rows, by_number, proper, tolerance)
        state_types.append(FrontierStateType(
            type_id, support_size, signature,
            tuple(species for species, _point in prototype_sites),
            tuple(point for _species, point in prototype_sites), occurrences,
            independent, saving))

    used = defaultdict(set)
    selected = []
    for state in state_types:
        for occurrence in state.occurrences:
            if used[occurrence.wave].intersection(occurrence.member_indices):
                continue
            used[occurrence.wave].update(occurrence.member_indices)
            selected.append((state.type_id, occurrence.wave,
                             occurrence.member_indices))
    residuals = tuple(
        (wave.wave, index, wave.species[index], wave.positions[index])
        for wave in waves for index in range(len(wave.positions))
        if index not in used[wave.wave])
    covered = sum(len(indices) for indices in used.values())
    atom_count = sum(len(wave.positions) for wave in waves)
    complete = covered + len(residuals) == atom_count
    witnesses = _stationary_witnesses(state_types, tolerance)
    payload = (
        maximum_nodes, graph_shell_ratio,
        tuple((state.support_size, state.normalized_signature,
               tuple((occurrence.wave, round(occurrence.scale / tolerance))
                     for occurrence in state.occurrences))
              for state in state_types),
        tuple(sorted((type_id, wave) for type_id, wave, _members in selected)),
        tuple(sorted((wave, _species_key(species))
                     for wave, _index, species, _point in residuals)),
    )
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=repr
    ).encode()).hexdigest()
    return FrontierStateGrammar(
        len(waves), atom_count, maximum_nodes, graph_shell_ratio,
        candidate_count, len(groups), tuple(state_types), tuple(selected),
        covered, residuals, complete,
        sum(occurrence.proper_pose_verified for state in state_types
            for occurrence in state.occurrences),
        witnesses, bool(witnesses) and not any(
            wave.target_used for wave in waves),
        any(wave.target_used for wave in waves),
        digest)
