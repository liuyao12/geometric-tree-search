#!/usr/bin/env python3
"""Frozen proper-SE(3) molecular ports and target-blind frontier growth."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Sequence

from materials_gcts_molecular_gap_clusters import (
    MolecularGapCover,
    learn_molecular_gap_cover,
    unwrapped_cluster_sites,
)
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence,
    ClusterPrototype,
    IDENTITY,
    Matrix,
    Site,
    Vector,
    canonical_relative_pose,
    fit_occurrence_pose,
    make_prototype,
    matmul,
    matvec,
    transpose,
)


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def _sub(left: Vector, right: Vector) -> Vector:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


@dataclass(frozen=True)
class MolecularPort:
    port_id: int
    relative_rotation: Matrix
    relative_translation: Vector
    symmetry_orbit_key: tuple[int, ...]
    observations: int


@dataclass(frozen=True)
class FrozenMolecularPortGrammar:
    prototype: ClusterPrototype
    molecular_signature: tuple
    ports: tuple[MolecularPort, ...]
    training_molecules: int
    training_connections: int
    pose_tolerance: float
    exclusion_distance: float
    material_label_used: bool = False
    target_used: bool = False


@dataclass(frozen=True)
class MolecularCandidate:
    candidate_id: str
    rotation: Matrix
    translation: Vector
    sites: tuple[Site, ...]
    parent_occurrences: tuple[int, ...]
    port_ids: tuple[int, ...]
    witness_count: int
    observation_support: int
    marking_score: float


@dataclass(frozen=True)
class MolecularGrowthWave:
    wave: int
    candidates: int
    accepted: int
    emitted_atoms: int
    candidate_digest: str
    accepted_ids: tuple[str, ...]
    eligible_candidates: tuple[MolecularCandidate, ...]


@dataclass(frozen=True)
class MolecularGrowthTrace:
    seed_atoms: int
    seed_molecules: int
    waves: tuple[MolecularGrowthWave, ...]
    placed_molecules: int
    emitted_sites: tuple[Site, ...]
    accepted_candidates: tuple[MolecularCandidate, ...]
    collision_rejections: int
    redundant_rejections: int
    boundary_rejections: int
    minimum_witnesses: int
    target_used: bool
    exact_geometry_certificates: bool


@dataclass(frozen=True)
class MolecularAnchorWave:
    wave: int
    candidate_anchors: int
    accepted_anchors: int
    retained_orientation_hypotheses: int
    candidate_digest: str


@dataclass(frozen=True)
class MolecularAnchorGrowthTrace:
    seed_anchors: int
    waves: tuple[MolecularAnchorWave, ...]
    emitted_anchors: tuple[Site, ...]
    anchor_hypothesis_counts: tuple[int, ...]
    resolved_new_molecules: int
    unresolved_new_molecules: int
    target_used: bool
    alternatives_are_mutually_exclusive: bool
    exact_port_geometry_certificates: bool


def _sites_digest(sites: Sequence[Site], tolerance: float) -> str:
    payload = sorted((str(species), *(round(value / tolerance) for value in point))
                     for species, point in sites)
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def _render(prototype: ClusterPrototype, rotation: Matrix,
            translation: Vector) -> tuple[Site, ...]:
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _prototype_anchor(prototype: ClusterPrototype) -> int:
    populations = {species: sum(item_species == species for item_species, _ in prototype.sites)
                   for species, _ in prototype.sites}
    radial = []
    for index, (species, point) in enumerate(prototype.sites):
        fingerprint = tuple(sorted(round(math.dist(point, other) / 1e-7)
                                   for other_index, (_, other) in enumerate(prototype.sites)
                                   if other_index != index))
        radial.append(((populations[species], str(species), fingerprint), index))
    minimum = min(key for key, _ in radial)
    winners = [index for key, index in radial if key == minimum]
    if len(winners) != 1:
        raise ValueError("molecular prototype has no unique geometry-derived anchor site")
    return winners[0]


def _anchor_site(prototype: ClusterPrototype, rotation: Matrix,
                 translation: Vector) -> Site:
    index = _prototype_anchor(prototype)
    species, point = prototype.sites[index]
    return species, _add(matvec(rotation, point), translation)


def _port_orbit(prototype: ClusterPrototype, port: MolecularPort) -> tuple[tuple[Matrix, Vector], ...]:
    poses = {}
    for parent_symmetry in prototype.proper_symmetries:
        shifted = matvec(parent_symmetry, port.relative_translation)
        for child_symmetry in prototype.proper_symmetries:
            rotation = matmul(matmul(parent_symmetry, port.relative_rotation),
                              transpose(child_symmetry))
            key = tuple(round(value / 1e-7) for row in rotation for value in row) + tuple(
                round(value / 1e-7) for value in shifted)
            poses[key] = (rotation, shifted)
    return tuple(poses[key] for key in sorted(poses))


def fit_molecular_port_grammar(
    species: Sequence[str], positions: Sequence[Sequence[float]], *,
    cell: Optional[Sequence[Sequence[float]]] = None,
    pose_tolerance: float = .04,
    minimum_port_observations: int = 2,
    exclusion_distance: float = .55,
) -> FrozenMolecularPortGrammar:
    """Fit one recurring molecular prototype and its finite connection ports."""
    cover = learn_molecular_gap_cover(species, positions, cell=cell,
                                      descriptor_tolerance=pose_tolerance)
    if cover.extended_network_rejected or cover.molecule_type_count != 1:
        raise ValueError("training cloud must contain one finite recurring molecular type")
    representative = cover.molecules[0]
    observed = unwrapped_cluster_sites(species, positions, representative.members, cell=cell)
    prototype = make_prototype(0, observed, tolerance=pose_tolerance)
    occurrences = []
    for molecule in cover.molecules:
        sites = unwrapped_cluster_sites(species, positions, molecule.members, cell=cell)
        occurrences.append(fit_occurrence_pose(
            molecule.occurrence_id, prototype, sites, tolerance=pose_tolerance))

    grouped: dict[tuple[int, ...], list[tuple[Matrix, Vector]]] = {}
    for connection in cover.connections:
        for parent_index, child_index in (connection.components,
                                          tuple(reversed(connection.components))):
            parent, child = occurrences[parent_index], occurrences[child_index]
            inverse_parent = transpose(parent.rotation)
            relative_rotation = matmul(inverse_parent, child.rotation)
            relative_translation = matvec(
                inverse_parent, _sub(child.translation, parent.translation))
            rotation, translation, key = canonical_relative_pose(
                prototype, prototype, relative_rotation, relative_translation,
                tolerance=pose_tolerance)
            grouped.setdefault(key, []).append((rotation, translation))
    retained = [(key, poses) for key, poses in grouped.items()
                if len(poses) >= minimum_port_observations]
    retained.sort(key=lambda item: item[0])
    ports = tuple(MolecularPort(index, poses[0][0], poses[0][1], key, len(poses))
                  for index, (key, poses) in enumerate(retained))
    if not ports:
        raise ValueError("no recurrent molecular connection port was learned")
    return FrozenMolecularPortGrammar(
        prototype=prototype, molecular_signature=representative.signature,
        ports=ports, training_molecules=len(occurrences),
        training_connections=len(cover.connections), pose_tolerance=pose_tolerance,
        exclusion_distance=exclusion_distance)


def recognize_seed_molecules(
    grammar: FrozenMolecularPortGrammar,
    species: Sequence[str], positions: Sequence[Sequence[float]],
) -> tuple[MolecularGapCover, tuple[ClusterOccurrence, ...], tuple[Site, ...]]:
    cover = learn_molecular_gap_cover(
        species, positions, descriptor_tolerance=grammar.pose_tolerance)
    occurrences = []
    for molecule in cover.molecules:
        if molecule.signature != grammar.molecular_signature:
            continue
        sites = unwrapped_cluster_sites(species, positions, molecule.members)
        occurrences.append(fit_occurrence_pose(
            len(occurrences), grammar.prototype, sites,
            tolerance=grammar.pose_tolerance))
    seed_sites = tuple((species[index], tuple(float(value) for value in positions[index]))
                       for index in range(len(positions)))
    return cover, tuple(occurrences), seed_sites


def _classify_candidate(sites: Sequence[Site], occupied: Sequence[Site],
                        tolerance: float, exclusion: float) -> str:
    matched = 0
    for species, point in sites:
        exact = [(other_species, other_point) for other_species, other_point in occupied
                 if math.dist(point, other_point) <= tolerance]
        if exact:
            if any(other_species != species for other_species, _ in exact):
                return "collision"
            matched += 1
            continue
        if any(math.dist(point, other_point) < exclusion
               for _, other_point in occupied):
            return "collision"
    if matched == len(sites):
        return "redundant"
    if matched:
        return "collision"
    return "novel"


def _candidate_compatible(left: MolecularCandidate, right: MolecularCandidate,
                          tolerance: float, exclusion: float) -> bool:
    return _classify_candidate(left.sites, right.sites, tolerance, exclusion) == "novel"


def execute_molecular_port_growth(
    grammar: FrozenMolecularPortGrammar,
    seed_occurrences: Sequence[ClusterOccurrence],
    seed_sites: Sequence[Site],
    *,
    boundary_center: Vector,
    boundary_radius: float,
    maximum_waves: int = 6,
    maximum_accepted_per_wave: int = 128,
    minimum_witnesses: int = 1,
    port_scores: Optional[Mapping[int, float]] = None,
) -> MolecularGrowthTrace:
    """Execute target-blind antichains while preserving tree-action identity."""
    if grammar.target_used:
        raise ValueError("target-tainted grammar cannot execute")
    placed = list(seed_occurrences)
    occupied = list(seed_sites)
    emitted: list[Site] = []
    accepted_all: list[MolecularCandidate] = []
    waves = []
    collision_rejections = redundant_rejections = boundary_rejections = 0
    known_pose_keys = {_sites_digest(_render(grammar.prototype, item.rotation, item.translation),
                                     grammar.pose_tolerance) for item in placed}
    for wave_index in range(maximum_waves):
        proposals: dict[str, list[tuple[int, int, Matrix, Vector, tuple[Site, ...], int]]] = {}
        for parent_index, parent in enumerate(placed):
            for port in grammar.ports:
                for relative_rotation, relative_translation in _port_orbit(grammar.prototype, port):
                    rotation = matmul(parent.rotation, relative_rotation)
                    translation = _add(parent.translation,
                                       matvec(parent.rotation, relative_translation))
                    sites = _render(grammar.prototype, rotation, translation)
                    key = _sites_digest(sites, grammar.pose_tolerance)
                    proposals.setdefault(key, []).append((
                        parent_index, port.port_id, rotation, translation, sites,
                        port.observations))
        candidates = []
        for key, witnesses in sorted(proposals.items()):
            if key in known_pose_keys:
                redundant_rejections += 1
                continue
            parent, port, rotation, translation, sites, _ = witnesses[0]
            if math.dist(translation, boundary_center) > boundary_radius + grammar.pose_tolerance:
                boundary_rejections += 1
                continue
            classification = _classify_candidate(
                sites, occupied, grammar.pose_tolerance, grammar.exclusion_distance)
            if classification == "collision":
                collision_rejections += 1
                continue
            if classification == "redundant":
                redundant_rejections += 1
                continue
            parent_ids = tuple(sorted({placed[item[0]].occurrence_id for item in witnesses}))
            port_ids = tuple(sorted({item[1] for item in witnesses}))
            candidate = MolecularCandidate(
                candidate_id=key, rotation=rotation, translation=translation,
                sites=sites, parent_occurrences=parent_ids, port_ids=port_ids,
                witness_count=len(parent_ids),
                observation_support=sum(item[5] for item in witnesses),
                marking_score=(max((port_scores or {}).get(item, 0.0)
                                   for item in port_ids) if port_ids else 0.0),
            )
            if candidate.witness_count >= minimum_witnesses:
                candidates.append(candidate)
        candidates.sort(key=lambda item: (-item.marking_score,
                                          -item.witness_count,
                                          -item.observation_support,
                                          item.candidate_id))
        accepted = []
        for candidate in candidates:
            if len(accepted) >= maximum_accepted_per_wave:
                break
            if all(_candidate_compatible(candidate, other,
                                         grammar.pose_tolerance,
                                         grammar.exclusion_distance)
                   for other in accepted):
                accepted.append(candidate)
        candidate_digest = hashlib.sha256(json.dumps(
            sorted(candidate.candidate_id for candidate in candidates),
            separators=(",", ":")).encode()).hexdigest()
        if not accepted:
            waves.append(MolecularGrowthWave(
                wave_index + 1, len(candidates), 0, 0, candidate_digest, (),
                tuple(candidates)))
            break
        new_sites = []
        for candidate in accepted:
            occurrence = ClusterOccurrence(
                len(placed), grammar.prototype.type_id,
                candidate.rotation, candidate.translation)
            placed.append(occurrence)
            known_pose_keys.add(candidate.candidate_id)
            occupied.extend(candidate.sites)
            new_sites.extend(candidate.sites)
            emitted.extend(candidate.sites)
            accepted_all.append(candidate)
        waves.append(MolecularGrowthWave(
            wave_index + 1, len(candidates), len(accepted), len(new_sites),
            candidate_digest, tuple(item.candidate_id for item in accepted),
            tuple(candidates)))
    return MolecularGrowthTrace(
        seed_atoms=len(seed_sites), seed_molecules=len(seed_occurrences),
        waves=tuple(waves), placed_molecules=len(placed),
        emitted_sites=tuple(emitted), accepted_candidates=tuple(accepted_all),
        collision_rejections=collision_rejections,
        redundant_rejections=redundant_rejections,
        boundary_rejections=boundary_rejections,
        minimum_witnesses=minimum_witnesses, target_used=False,
        exact_geometry_certificates=True,
    )


def execute_molecular_anchor_growth(
    grammar: FrozenMolecularPortGrammar,
    seed_occurrences: Sequence[ClusterOccurrence],
    *,
    boundary_center: Vector,
    boundary_radius: float,
    maximum_waves: int = 6,
    maximum_hypotheses_per_anchor: int = 32,
    anchor_tolerance: float = .06,
    anchor_exclusion_distance: float = 1.5,
) -> MolecularAnchorGrowthTrace:
    """Grow shared molecular anchors while retaining decoration alternatives.

    A full molecular pose remains the tree-search state, but mutually
    exclusive poses with the same unique molecular anchor are not rendered as
    simultaneous atoms.  Their shared anchor is emitted once and every exact
    orientation stays available to generate the next frontier.
    """
    if grammar.target_used:
        raise ValueError("target-tainted grammar cannot execute")
    hypotheses: dict[str, dict[str, ClusterOccurrence]] = {}
    anchor_sites: dict[str, Site] = {}
    for occurrence in seed_occurrences:
        anchor = _anchor_site(grammar.prototype, occurrence.rotation,
                              occurrence.translation)
        anchor_key = _sites_digest((anchor,), anchor_tolerance)
        pose_key = _sites_digest(_render(grammar.prototype, occurrence.rotation,
                                         occurrence.translation), grammar.pose_tolerance)
        hypotheses.setdefault(anchor_key, {})[pose_key] = occurrence
        anchor_sites[anchor_key] = anchor
    seed_keys = set(hypotheses)
    waves = []
    next_occurrence_id = len(seed_occurrences)
    for wave_index in range(maximum_waves):
        proposals: dict[str, dict[str, tuple[ClusterOccurrence, int]]] = {}
        for alternatives in hypotheses.values():
            for parent in alternatives.values():
                for port in grammar.ports:
                    for relative_rotation, relative_translation in _port_orbit(grammar.prototype, port):
                        rotation = matmul(parent.rotation, relative_rotation)
                        translation = _add(parent.translation,
                                           matvec(parent.rotation, relative_translation))
                        anchor = _anchor_site(grammar.prototype, rotation, translation)
                        anchor_key = _sites_digest((anchor,), anchor_tolerance)
                        if anchor_key in hypotheses:
                            continue
                        if math.dist(anchor[1], boundary_center) > boundary_radius + anchor_tolerance:
                            continue
                        if any(math.dist(anchor[1], existing[1]) < anchor_exclusion_distance
                               for existing in anchor_sites.values()):
                            continue
                        sites = _render(grammar.prototype, rotation, translation)
                        pose_key = _sites_digest(sites, grammar.pose_tolerance)
                        occurrence = ClusterOccurrence(
                            next_occurrence_id, grammar.prototype.type_id,
                            rotation, translation)
                        prior = proposals.setdefault(anchor_key, {}).get(pose_key)
                        support = port.observations + (prior[1] if prior else 0)
                        proposals[anchor_key][pose_key] = (occurrence, support)
        ordered_anchors = sorted(proposals)
        candidate_digest = hashlib.sha256(json.dumps(
            [(key, sorted(proposals[key])) for key in ordered_anchors],
            separators=(",", ":")).encode()).hexdigest()
        accepted = []
        accepted_points: list[Vector] = []
        for anchor_key in ordered_anchors:
            sample_occurrence = next(iter(proposals[anchor_key].values()))[0]
            anchor = _anchor_site(grammar.prototype, sample_occurrence.rotation,
                                  sample_occurrence.translation)
            if any(math.dist(anchor[1], point) < anchor_exclusion_distance
                   for point in accepted_points):
                continue
            accepted.append(anchor_key)
            accepted_points.append(anchor[1])
        if not accepted:
            waves.append(MolecularAnchorWave(
                wave_index + 1, len(proposals), 0, 0, candidate_digest))
            break
        retained = 0
        for anchor_key in accepted:
            ranked = sorted(proposals[anchor_key].items(),
                            key=lambda item: (-item[1][1], item[0]))
            alternatives = {}
            for pose_key, (occurrence, _) in ranked[:maximum_hypotheses_per_anchor]:
                occurrence = ClusterOccurrence(
                    next_occurrence_id, occurrence.type_id,
                    occurrence.rotation, occurrence.translation)
                next_occurrence_id += 1
                alternatives[pose_key] = occurrence
            hypotheses[anchor_key] = alternatives
            retained += len(alternatives)
            exemplar = next(iter(alternatives.values()))
            anchor_sites[anchor_key] = _anchor_site(
                grammar.prototype, exemplar.rotation, exemplar.translation)
        waves.append(MolecularAnchorWave(
            wave_index + 1, len(proposals), len(accepted), retained,
            candidate_digest))
    new_keys = sorted(set(hypotheses) - seed_keys)
    counts = tuple(len(hypotheses[key]) for key in new_keys)
    return MolecularAnchorGrowthTrace(
        seed_anchors=len(seed_keys), waves=tuple(waves),
        emitted_anchors=tuple(anchor_sites[key] for key in new_keys),
        anchor_hypothesis_counts=counts,
        resolved_new_molecules=sum(count == 1 for count in counts),
        unresolved_new_molecules=sum(count > 1 for count in counts),
        target_used=False, alternatives_are_mutually_exclusive=True,
        exact_port_geometry_certificates=True,
    )


def score_sites(predicted: Sequence[Site], target: Sequence[Site],
                tolerance: float = .06) -> tuple[int, int, int]:
    unmatched = set(range(len(target)))
    correct = 0
    for species, point in predicted:
        matches = [index for index in unmatched if target[index][0] == species
                   and math.dist(point, target[index][1]) <= tolerance]
        if matches:
            chosen = min(matches, key=lambda index: math.dist(point, target[index][1]))
            unmatched.remove(chosen)
            correct += 1
    return correct, len(predicted) - correct, len(unmatched)
