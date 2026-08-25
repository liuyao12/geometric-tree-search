#!/usr/bin/env python3
"""Finite multi-conformer molecular port grammar and target-blind growth.

The older molecular executor intentionally accepts one exact rigid molecular
prototype.  Real diffraction geometries can contain several recurring metric
conformers of the same molecular topology.  This module preserves those as a
finite typed vocabulary and learns directed proper-SE(3) ports between them.
It never broadens a tolerance merely to collapse distinct measured geometry.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from materials_gcts_molecular_gap_clusters import (
    MolecularGapCover,
    learn_molecular_gap_cover,
    unwrapped_cluster_sites,
)
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence,
    ClusterPrototype,
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


def _render(prototype: ClusterPrototype, rotation: Matrix,
            translation: Vector) -> tuple[Site, ...]:
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _sites_digest(sites: Sequence[Site], tolerance: float) -> str:
    payload = sorted((str(species), *(round(value / tolerance) for value in point))
                     for species, point in sites)
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class ConformerPort:
    port_id: int
    parent_type: int
    child_type: int
    relative_rotation: Matrix
    relative_translation: Vector
    symmetry_orbit_key: tuple[int, ...]
    observations: int


@dataclass(frozen=True)
class FrozenMolecularConformerGrammar:
    prototypes: tuple[ClusterPrototype, ...]
    signatures: tuple[tuple, ...]
    formula: tuple[tuple[str, int], ...]
    ports: tuple[ConformerPort, ...]
    training_molecules: int
    training_connections: int
    pose_tolerance: float
    exclusion_distance: float
    minimum_port_observations: int
    material_label_used: bool = False
    expected_formula_used: bool = False
    target_used: bool = False


@dataclass(frozen=True)
class ConformerCandidate:
    candidate_id: str
    child_type: int
    rotation: Matrix
    translation: Vector
    sites: tuple[Site, ...]
    parent_occurrences: tuple[int, ...]
    port_ids: tuple[int, ...]
    witness_count: int
    observation_support: int
    marking_score: float


@dataclass(frozen=True)
class ConformerGrowthWave:
    wave: int
    candidates: int
    ranked_candidates: int
    below_threshold: int
    accepted: int
    emitted_atoms: int
    candidate_digest: str
    accepted_ids: tuple[str, ...]
    eligible_candidates: tuple[ConformerCandidate, ...]


@dataclass(frozen=True)
class ConformerGrowthTrace:
    seed_atoms: int
    seed_molecules: int
    recognized_conformer_types: tuple[int, ...]
    waves: tuple[ConformerGrowthWave, ...]
    placed_molecules: int
    emitted_sites: tuple[Site, ...]
    accepted_candidates: tuple[ConformerCandidate, ...]
    collision_rejections: int
    redundant_rejections: int
    boundary_rejections: int
    target_used: bool
    exact_geometry_certificates: bool


@dataclass(frozen=True)
class ConformerAnchorCandidate:
    candidate_id: str
    anchor: Site
    parent_witnesses: int
    pose_hypotheses: int
    observation_support: int


@dataclass(frozen=True)
class ConformerAnchorWave:
    wave: int
    candidate_anchors: int
    accepted_anchors: int
    retained_pose_hypotheses: int
    candidate_digest: str
    eligible_candidates: tuple[ConformerAnchorCandidate, ...]
    accepted_ids: tuple[str, ...]


@dataclass(frozen=True)
class ConformerAnchorTrace:
    seed_anchors: int
    waves: tuple[ConformerAnchorWave, ...]
    emitted_anchors: tuple[Site, ...]
    anchor_hypothesis_counts: tuple[int, ...]
    resolved_new_molecules: int
    unresolved_new_molecules: int
    target_used: bool
    alternatives_are_mutually_exclusive: bool
    exact_port_geometry_certificates: bool


def _port_orbit(parent: ClusterPrototype, child: ClusterPrototype,
                port: ConformerPort) -> tuple[tuple[Matrix, Vector], ...]:
    poses = {}
    for parent_symmetry in parent.proper_symmetries:
        shifted = matvec(parent_symmetry, port.relative_translation)
        for child_symmetry in child.proper_symmetries:
            rotation = matmul(matmul(parent_symmetry, port.relative_rotation),
                              transpose(child_symmetry))
            key = tuple(round(value / 1e-7) for row in rotation for value in row) + tuple(
                round(value / 1e-7) for value in shifted)
            poses[key] = (rotation, shifted)
    return tuple(poses[key] for key in sorted(poses))


def _prototype_anchor(prototype: ClusterPrototype) -> int:
    populations = Counter(species for species, _ in prototype.sites)
    keys = []
    for index, (species, point) in enumerate(prototype.sites):
        fingerprint = tuple(sorted(round(math.dist(point, other) / 1e-7)
                                   for other_index, (_, other) in enumerate(prototype.sites)
                                   if other_index != index))
        keys.append(((populations[species], str(species), fingerprint), index))
    minimum = min(key for key, _ in keys)
    winners = [index for key, index in keys if key == minimum]
    if len(winners) != 1:
        raise ValueError("molecular conformer has no unique geometry-derived anchor")
    return winners[0]


def _anchor_site(prototype: ClusterPrototype, rotation: Matrix,
                 translation: Vector) -> Site:
    index = _prototype_anchor(prototype)
    species, point = prototype.sites[index]
    return species, _add(matvec(rotation, point), translation)


def fit_molecular_conformer_grammar(
    species: Sequence[str], positions: Sequence[Sequence[float]], *,
    cell: Optional[Sequence[Sequence[float]]] = None,
    pose_tolerance: float = .04,
    minimum_port_observations: int = 2,
    exclusion_distance: float = .55,
) -> FrozenMolecularConformerGrammar:
    if minimum_port_observations < 1:
        raise ValueError("minimum port observations must be positive")
    cover = learn_molecular_gap_cover(species, positions, cell=cell,
                                      descriptor_tolerance=pose_tolerance)
    if cover.extended_network_rejected or not cover.molecules:
        raise ValueError("training cloud must contain finite molecular components")
    formulas = {molecule.formula for molecule in cover.molecules}
    if len(formulas) != 1:
        raise ValueError("one conformer grammar cannot mix molecular formulas")
    type_count = cover.molecule_type_count
    prototypes = []
    signatures = []
    occurrences: list[ClusterOccurrence] = []
    occurrence_by_id: dict[int, ClusterOccurrence] = {}
    for type_id in range(type_count):
        members = [molecule for molecule in cover.molecules if molecule.type_id == type_id]
        if not members:
            raise ValueError("molecular conformer type IDs must be dense")
        representative_sites = unwrapped_cluster_sites(
            species, positions, members[0].members, cell=cell)
        prototype = make_prototype(type_id, representative_sites,
                                   tolerance=pose_tolerance)
        prototypes.append(prototype)
        signatures.append(members[0].signature)
        for molecule in members:
            sites = unwrapped_cluster_sites(species, positions, molecule.members,
                                            cell=cell)
            occurrence = fit_occurrence_pose(
                molecule.occurrence_id, prototype, sites,
                tolerance=pose_tolerance)
            occurrences.append(occurrence)
            occurrence_by_id[molecule.occurrence_id] = occurrence

    grouped: dict[tuple[int, int, tuple[int, ...]], list[tuple[Matrix, Vector]]] = {}
    for connection in cover.connections:
        for parent_index, child_index in (connection.components,
                                          tuple(reversed(connection.components))):
            parent = occurrence_by_id[parent_index]
            child = occurrence_by_id[child_index]
            parent_prototype = prototypes[parent.type_id]
            child_prototype = prototypes[child.type_id]
            inverse_parent = transpose(parent.rotation)
            relative_rotation = matmul(inverse_parent, child.rotation)
            relative_translation = matvec(
                inverse_parent, _sub(child.translation, parent.translation))
            rotation, translation, key = canonical_relative_pose(
                parent_prototype, child_prototype,
                relative_rotation, relative_translation,
                tolerance=pose_tolerance)
            grouped.setdefault((parent.type_id, child.type_id, key), []).append(
                (rotation, translation))
    retained = [(key, poses) for key, poses in grouped.items()
                if len(poses) >= minimum_port_observations]
    retained.sort(key=lambda item: item[0])
    ports = tuple(ConformerPort(
        port_id=index,
        parent_type=key[0], child_type=key[1],
        relative_rotation=poses[0][0], relative_translation=poses[0][1],
        symmetry_orbit_key=key[2], observations=len(poses),
    ) for index, (key, poses) in enumerate(retained))
    if not ports:
        raise ValueError("no recurrent typed molecular connection port was learned")
    return FrozenMolecularConformerGrammar(
        prototypes=tuple(prototypes), signatures=tuple(signatures),
        formula=next(iter(formulas)), ports=ports,
        training_molecules=len(occurrences),
        training_connections=len(cover.connections),
        pose_tolerance=pose_tolerance,
        exclusion_distance=exclusion_distance,
        minimum_port_observations=minimum_port_observations,
    )


def recognize_seed_conformers(
    grammar: FrozenMolecularConformerGrammar,
    species: Sequence[str], positions: Sequence[Sequence[float]],
) -> tuple[MolecularGapCover, tuple[ClusterOccurrence, ...], tuple[Site, ...]]:
    cover = learn_molecular_gap_cover(
        species, positions, descriptor_tolerance=grammar.pose_tolerance)
    signature_to_type = {signature: type_id
                         for type_id, signature in enumerate(grammar.signatures)}
    occurrences = []
    for molecule in cover.molecules:
        type_id = signature_to_type.get(molecule.signature)
        if type_id is None:
            continue
        sites = unwrapped_cluster_sites(species, positions, molecule.members)
        occurrences.append(fit_occurrence_pose(
            len(occurrences), grammar.prototypes[type_id], sites,
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


def _compatible(left: ConformerCandidate, right: ConformerCandidate,
                tolerance: float, exclusion: float) -> bool:
    return _classify_candidate(left.sites, right.sites,
                               tolerance, exclusion) == "novel"


def execute_molecular_conformer_growth(
    grammar: FrozenMolecularConformerGrammar,
    seed_occurrences: Sequence[ClusterOccurrence],
    seed_sites: Sequence[Site], *,
    boundary_center: Vector,
    boundary_radius: float,
    maximum_waves: int = 6,
    maximum_accepted_per_wave: int = 128,
    minimum_witnesses: int = 1,
    port_scores: Optional[Mapping[int, float]] = None,
    minimum_marking_score: float = -math.inf,
) -> ConformerGrowthTrace:
    if grammar.target_used:
        raise ValueError("target-tainted grammar cannot execute")
    placed = list(seed_occurrences)
    occupied = list(seed_sites)
    emitted: list[Site] = []
    accepted_all: list[ConformerCandidate] = []
    waves = []
    collision_rejections = redundant_rejections = boundary_rejections = 0
    known_pose_keys = {_sites_digest(
        _render(grammar.prototypes[item.type_id], item.rotation, item.translation),
        grammar.pose_tolerance) for item in placed}
    ports_by_parent: dict[int, list[ConformerPort]] = {}
    for port in grammar.ports:
        ports_by_parent.setdefault(port.parent_type, []).append(port)
    for wave_index in range(maximum_waves):
        proposals: dict[str, list[tuple[int, ConformerPort, Matrix, Vector,
                                             tuple[Site, ...]]]] = {}
        for parent_index, parent in enumerate(placed):
            parent_prototype = grammar.prototypes[parent.type_id]
            for port in ports_by_parent.get(parent.type_id, ()):
                child_prototype = grammar.prototypes[port.child_type]
                for relative_rotation, relative_translation in _port_orbit(
                        parent_prototype, child_prototype, port):
                    rotation = matmul(parent.rotation, relative_rotation)
                    translation = _add(parent.translation,
                                       matvec(parent.rotation, relative_translation))
                    sites = _render(child_prototype, rotation, translation)
                    key = _sites_digest(sites, grammar.pose_tolerance)
                    proposals.setdefault(key, []).append((
                        parent_index, port, rotation, translation, sites))
        candidates = []
        for key, witnesses in sorted(proposals.items()):
            if key in known_pose_keys:
                redundant_rejections += 1
                continue
            parent_index, port, rotation, translation, sites = witnesses[0]
            if math.dist(translation, boundary_center) > boundary_radius + grammar.pose_tolerance:
                boundary_rejections += 1
                continue
            classification = _classify_candidate(
                sites, occupied, grammar.pose_tolerance,
                grammar.exclusion_distance)
            if classification == "collision":
                collision_rejections += 1
                continue
            if classification == "redundant":
                redundant_rejections += 1
                continue
            parent_ids = tuple(sorted({placed[item[0]].occurrence_id
                                       for item in witnesses}))
            port_ids = tuple(sorted({item[1].port_id for item in witnesses}))
            child_types = {item[1].child_type for item in witnesses}
            if len(child_types) != 1:
                raise AssertionError("one exact candidate geometry has multiple child types")
            candidate = ConformerCandidate(
                candidate_id=key, child_type=port.child_type,
                rotation=rotation, translation=translation, sites=sites,
                parent_occurrences=parent_ids, port_ids=port_ids,
                witness_count=len(parent_ids),
                observation_support=sum(item[1].observations for item in witnesses),
                marking_score=max(((port_scores or {}).get(item, 0.0)
                                   for item in port_ids), default=0.0),
            )
            if candidate.witness_count >= minimum_witnesses:
                candidates.append(candidate)
        candidates.sort(key=lambda item: (-item.marking_score,
                                          -item.witness_count,
                                          -item.observation_support,
                                          item.candidate_id))
        geometry_candidates = tuple(candidates)
        ranked = [candidate for candidate in candidates
                  if candidate.marking_score >= minimum_marking_score]
        accepted = []
        for candidate in ranked:
            if len(accepted) >= maximum_accepted_per_wave:
                break
            if all(_compatible(candidate, other, grammar.pose_tolerance,
                               grammar.exclusion_distance)
                   for other in accepted):
                accepted.append(candidate)
        digest = hashlib.sha256(json.dumps(
            sorted(item.candidate_id for item in geometry_candidates),
            separators=(",", ":")).encode()).hexdigest()
        if not accepted:
            waves.append(ConformerGrowthWave(
                wave_index + 1, len(geometry_candidates), len(ranked),
                len(geometry_candidates) - len(ranked), 0, 0, digest, (),
                geometry_candidates))
            break
        for candidate in accepted:
            placed.append(ClusterOccurrence(
                len(placed), candidate.child_type,
                candidate.rotation, candidate.translation))
            known_pose_keys.add(candidate.candidate_id)
            occupied.extend(candidate.sites)
            emitted.extend(candidate.sites)
            accepted_all.append(candidate)
        waves.append(ConformerGrowthWave(
            wave_index + 1, len(geometry_candidates), len(ranked),
            len(geometry_candidates) - len(ranked), len(accepted),
            sum(len(candidate.sites) for candidate in accepted), digest,
            tuple(item.candidate_id for item in accepted), geometry_candidates))
    return ConformerGrowthTrace(
        seed_atoms=len(seed_sites), seed_molecules=len(seed_occurrences),
        recognized_conformer_types=tuple(sorted({item.type_id for item in seed_occurrences})),
        waves=tuple(waves), placed_molecules=len(placed),
        emitted_sites=tuple(emitted), accepted_candidates=tuple(accepted_all),
        collision_rejections=collision_rejections,
        redundant_rejections=redundant_rejections,
        boundary_rejections=boundary_rejections,
        target_used=False, exact_geometry_certificates=True,
    )


def execute_molecular_conformer_anchor_growth(
    grammar: FrozenMolecularConformerGrammar,
    seed_occurrences: Sequence[ClusterOccurrence], *,
    boundary_center: Vector,
    boundary_radius: float,
    maximum_waves: int = 6,
    maximum_anchors_per_wave: int = 128,
    maximum_hypotheses_per_anchor: int = 64,
    minimum_parent_witnesses: int = 1,
    anchor_tolerance: float = .06,
    anchor_exclusion_distance: float = 1.5,
) -> ConformerAnchorTrace:
    """Grow shared molecular anchors while retaining typed pose alternatives.

    A new oxygen anchor is physical and unique, while its mutually exclusive
    D2O conformer/orientation hypotheses remain symbolic.  Those hypotheses
    all self-feed the next frontier; no half-occupied or alternative D sites
    are rendered simultaneously.
    """
    if grammar.target_used:
        raise ValueError("target-tainted grammar cannot execute")
    if minimum_parent_witnesses < 1:
        raise ValueError("minimum parent witnesses must be positive")
    ports_by_parent: dict[int, list[ConformerPort]] = {}
    for port in grammar.ports:
        ports_by_parent.setdefault(port.parent_type, []).append(port)
    hypotheses: dict[str, dict[str, tuple[ClusterOccurrence, int]]] = {}
    anchor_sites: dict[str, Site] = {}
    for occurrence in seed_occurrences:
        prototype = grammar.prototypes[occurrence.type_id]
        anchor = _anchor_site(prototype, occurrence.rotation,
                              occurrence.translation)
        anchor_key = _sites_digest((anchor,), anchor_tolerance)
        pose_key = f"{occurrence.type_id}:" + _sites_digest(
            _render(prototype, occurrence.rotation, occurrence.translation),
            grammar.pose_tolerance)
        hypotheses.setdefault(anchor_key, {})[pose_key] = (occurrence, 0)
        anchor_sites[anchor_key] = anchor
    seed_keys = set(hypotheses)
    next_occurrence_id = len(seed_occurrences)
    emitted = []
    waves = []
    for wave_index in range(maximum_waves):
        proposals: dict[str, dict[str, tuple[ClusterOccurrence, int]]] = {}
        proposal_parents: dict[str, set[str]] = {}
        for parent_anchor_key, alternatives in hypotheses.items():
            for parent, _ in alternatives.values():
                parent_prototype = grammar.prototypes[parent.type_id]
                for port in ports_by_parent.get(parent.type_id, ()):
                    child_prototype = grammar.prototypes[port.child_type]
                    for relative_rotation, relative_translation in _port_orbit(
                            parent_prototype, child_prototype, port):
                        rotation = matmul(parent.rotation, relative_rotation)
                        translation = _add(parent.translation,
                                           matvec(parent.rotation, relative_translation))
                        anchor = _anchor_site(child_prototype, rotation, translation)
                        anchor_key = _sites_digest((anchor,), anchor_tolerance)
                        if anchor_key in hypotheses:
                            continue
                        if math.dist(anchor[1], boundary_center) > boundary_radius + anchor_tolerance:
                            continue
                        pose_key = f"{port.child_type}:" + _sites_digest(
                            _render(child_prototype, rotation, translation),
                            grammar.pose_tolerance)
                        occurrence = ClusterOccurrence(
                            next_occurrence_id, port.child_type,
                            rotation, translation)
                        previous = proposals.setdefault(anchor_key, {}).get(pose_key)
                        if previous is None or port.observations > previous[1]:
                            proposals[anchor_key][pose_key] = (occurrence, port.observations)
                        proposal_parents.setdefault(anchor_key, set()).add(parent_anchor_key)
                        anchor_sites[anchor_key] = anchor
        candidate_records = tuple(sorted((ConformerAnchorCandidate(
            candidate_id=key,
            anchor=anchor_sites[key],
            parent_witnesses=len(proposal_parents.get(key, ())),
            pose_hypotheses=len(proposals[key]),
            observation_support=sum(support for _, support in proposals[key].values()),
        ) for key in proposals), key=lambda item: (
            -item.parent_witnesses, -item.observation_support,
            item.pose_hypotheses, item.candidate_id)))
        ordered = [item.candidate_id for item in candidate_records
                   if item.parent_witnesses >= minimum_parent_witnesses]
        digest = hashlib.sha256(json.dumps(
            [item.candidate_id for item in candidate_records],
            separators=(",", ":")).encode()).hexdigest()
        accepted = []
        occupied_anchors = [site for key, site in anchor_sites.items()
                            if key in hypotheses]
        for anchor_key in ordered:
            if len(accepted) >= maximum_anchors_per_wave:
                break
            anchor = anchor_sites[anchor_key]
            if any(math.dist(anchor[1], existing[1]) < anchor_exclusion_distance
                   for existing in occupied_anchors):
                continue
            if any(math.dist(anchor[1], anchor_sites[other][1]) < anchor_exclusion_distance
                   for other in accepted):
                continue
            accepted.append(anchor_key)
        for anchor_key in accepted:
            ranked = sorted(proposals[anchor_key].items(),
                            key=lambda item: (-item[1][1], item[0]))
            hypotheses[anchor_key] = dict(ranked[:maximum_hypotheses_per_anchor])
            emitted.append(anchor_sites[anchor_key])
            next_occurrence_id += len(hypotheses[anchor_key])
        waves.append(ConformerAnchorWave(
            wave=wave_index + 1,
            candidate_anchors=len(proposals),
            accepted_anchors=len(accepted),
            retained_pose_hypotheses=sum(len(hypotheses[key]) for key in accepted),
            candidate_digest=digest,
            eligible_candidates=candidate_records,
            accepted_ids=tuple(accepted),
        ))
        if not accepted:
            break
    new_counts = [len(alternatives) for key, alternatives in hypotheses.items()
                  if key not in seed_keys]
    return ConformerAnchorTrace(
        seed_anchors=len(seed_keys), waves=tuple(waves),
        emitted_anchors=tuple(emitted),
        anchor_hypothesis_counts=tuple(sorted(new_counts)),
        resolved_new_molecules=sum(count == 1 for count in new_counts),
        unresolved_new_molecules=sum(count > 1 for count in new_counts),
        target_used=False, alternatives_are_mutually_exclusive=True,
        exact_port_geometry_certificates=True,
    )


def grammar_audit(grammar: FrozenMolecularConformerGrammar) -> dict:
    directed_type_pairs = Counter((port.parent_type, port.child_type)
                                  for port in grammar.ports)
    return {
        "conformer_types": len(grammar.prototypes),
        "ports": len(grammar.ports),
        "directed_type_pairs": len(directed_type_pairs),
        "training_molecules": grammar.training_molecules,
        "training_connections": grammar.training_connections,
        "material_label_used": grammar.material_label_used,
        "expected_formula_used": grammar.expected_formula_used,
        "target_used": grammar.target_used,
    }
