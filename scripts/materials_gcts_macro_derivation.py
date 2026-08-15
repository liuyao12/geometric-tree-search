#!/usr/bin/env python3
"""Self-fed symbolic execution of train-learned promoted macro ports.

The executor accepts only a ``PromotedMacroProgram`` and placed macro seeds.
At level l+1 it composes frozen overlap productions only with nodes emitted at
level l.  Every accepted child carries an overlap-inclusion certificate: its
colored intersection is already contained in the accumulated support, there
is no unlike-color collision, and its emitted set is the exact set difference.

No target cloud, cell, family, action radius, or prescribed similarity scale
appears in compilation or execution.  A separate scorer may inspect a finished
derivation.  The optional stationary-contract adapter converts 3--7 explicit
nodes to the existing strict production representation; inability to obtain a
non-collinear stationary frame is reported as absence, not relaxed semantics.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Hashable, Sequence

from materials_gcts_macro_promotion import PromotedMacroProgram
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, ClusterPrototype, Matrix, Vector, expand_port_orbit,
    is_proper_rotation, matmul, matvec)
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionChild, ProductionPort,
    canonicalize_production)

Site = tuple[Hashable, Vector]
SiteKey = tuple[str, int, int, int]


@dataclass(frozen=True)
class FrozenMacroProduction:
    production_id: int
    parent_type: int
    child_type: int
    symmetry_orbit_key: tuple[int, ...]
    production_kind: str
    required_shared_atoms: int
    training_observations: int
    training_child_port_witnesses: int


@dataclass(frozen=True)
class SymbolicMacroNode:
    node_id: int
    macro_type: int
    rotation: Matrix
    translation: Vector
    depth: int
    parent_node: int | None
    production_id: int | None


@dataclass(frozen=True)
class OverlapInclusionCertificate:
    parent_node: int
    child_node: int
    production_id: int
    production_kind: str
    required_shared_atoms: int
    included_overlap_sites: tuple[SiteKey, ...]
    emitted_sites: tuple[SiteKey, ...]
    conflicting_sites: int
    overlap_is_subset: bool
    emitted_is_exact_difference: bool
    adjacency_witnessed_in_training: bool
    training_child_port_witnesses: int
    certificate_digest: str


@dataclass(frozen=True)
class SymbolicDerivationStep:
    level: int
    node: SymbolicMacroNode
    certificate: OverlapInclusionCertificate


@dataclass(frozen=True)
class ExplicitDerivationLevel:
    level: int
    parent_nodes: int
    emitted_nodes: int
    atoms_before: int
    emitted_atoms: int
    atoms_after: int
    sites: tuple[Site, ...]


@dataclass(frozen=True)
class MacroDerivation:
    productions: tuple[FrozenMacroProduction, ...]
    nodes: tuple[SymbolicMacroNode, ...]
    steps: tuple[SymbolicDerivationStep, ...]
    explicit_levels: tuple[ExplicitDerivationLevel, ...]
    seed_sites: tuple[Site, ...]
    sites: tuple[Site, ...]
    attempted_candidates: int
    rejected_duplicate_poses: int
    rejected_conflicts: int
    rejected_insufficient_overlap: int
    rejected_batch_conflicts: int
    symbolic_atom_count: int
    explicit_atom_count: int
    independent_count_verified: bool
    self_fed: bool
    target_used: bool
    stationary_contract: PortGraphProduction | None
    stationary_normalized_key: str | None


@dataclass(frozen=True)
class DerivationScore:
    target_atoms: int
    seed_atoms: int
    proposed_novel_atoms: int
    correct_novel_atoms: int
    precision: float
    heldout_recall: float
    target_used_during_derivation: bool


@dataclass(frozen=True)
class _Candidate:
    parent_node: int
    production_id: int
    child_type: int
    rotation: Matrix
    translation: Vector
    rendered: tuple[Site, ...]
    overlap: tuple[SiteKey, ...]
    emitted: tuple[Site, ...]


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(left[axis] + right[axis] for axis in range(3))  # type: ignore[return-value]


def _site_key(site: Site, tolerance: float) -> SiteKey:
    species, point = site
    label = (f"{type(species).__module__}."
             f"{type(species).__qualname__}:{species!r}")
    return (label,) + tuple(round(value / tolerance)
                            for value in point)  # type: ignore[return-value]


def _pose_key(type_id: int, rotation: Matrix, translation: Vector,
              tolerance: float) -> tuple[int, ...]:
    return ((type_id,) + tuple(round(value / tolerance)
                               for row in rotation for value in row) +
            tuple(round(value / tolerance) for value in translation))


def _render(prototype: ClusterPrototype, rotation: Matrix,
            translation: Vector) -> tuple[Site, ...]:
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _unique_sites(sites: Sequence[Site], tolerance: float) -> tuple[Site, ...]:
    unique = {}
    species_at = {}
    for site in sites:
        species, point = site
        coordinate = tuple(round(value / tolerance) for value in point)
        if coordinate in species_at and species_at[coordinate] != species:
            raise ValueError("unlike-colored sites coincide in the derivation")
        species_at[coordinate] = species
        unique.setdefault(coordinate, site)
    return tuple(unique[key] for key in sorted(unique))


def _classify(
    rendered: Sequence[Site], occupied: Sequence[Site], tolerance: float,
    exclusion_distance: float,
) -> tuple[tuple[SiteKey, ...], tuple[Site, ...], bool]:
    overlap = []
    emitted = []
    for site in rendered:
        species, point = site
        coincident = tuple(known for known in occupied
                           if math.dist(point, known[1]) <= tolerance)
        if coincident:
            if any(known_species != species for known_species, _ in coincident):
                return (), (), True
            overlap.append(_site_key(site, tolerance))
        elif any(math.dist(point, known_point) < exclusion_distance
                 for _, known_point in occupied):
            return (), (), True
        else:
            emitted.append(site)
    return tuple(sorted(set(overlap))), tuple(emitted), False


class _SpatialSiteIndex:
    """Incremental exact-radius lookup over the occupied colored point set."""

    def __init__(self, sites: Sequence[Site], cell_size: float):
        if cell_size <= 0 or not math.isfinite(cell_size):
            raise ValueError("spatial-index cell size must be finite and positive")
        self.cell_size = cell_size
        self.cells = defaultdict(list)
        self.extend(sites)

    def _cell(self, point: Vector) -> tuple[int, int, int]:
        return tuple(math.floor(value / self.cell_size)
                     for value in point)  # type: ignore[return-value]

    def _neighbors(self, point: Vector):
        center = self._cell(point)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    yield from self.cells.get(
                        (center[0] + dx, center[1] + dy,
                         center[2] + dz), ())

    def extend(self, sites: Sequence[Site]) -> None:
        for site in sites:
            self.cells[self._cell(site[1])].append(site)

    def classify(
        self, rendered: Sequence[Site], tolerance: float,
        exclusion_distance: float,
    ) -> tuple[tuple[SiteKey, ...], tuple[Site, ...], bool]:
        if exclusion_distance > self.cell_size:
            raise ValueError("query radius exceeds spatial-index cell size")
        overlap = []
        emitted = []
        for site in rendered:
            species, point = site
            nearby = tuple(self._neighbors(point))
            coincident = tuple(
                known for known in nearby
                if math.dist(point, known[1]) <= tolerance)
            if coincident:
                if any(known_species != species
                       for known_species, _ in coincident):
                    return (), (), True
                overlap.append(_site_key(site, tolerance))
            elif any(math.dist(point, known_point) < exclusion_distance
                     for _, known_point in nearby):
                return (), (), True
            else:
                emitted.append(site)
        return tuple(sorted(set(overlap))), tuple(emitted), False


def _certificate(
    candidate: _Candidate, child_node: int,
    production: FrozenMacroProduction, occupied_before: Sequence[Site],
    tolerance: float, *, occupied_keys_before: set[SiteKey] | None = None,
) -> OverlapInclusionCertificate:
    occupied_keys = (occupied_keys_before if occupied_keys_before is not None
                     else {_site_key(site, tolerance)
                           for site in occupied_before})
    rendered_keys = {_site_key(site, tolerance) for site in candidate.rendered}
    overlap = tuple(sorted(rendered_keys.intersection(occupied_keys)))
    emitted = tuple(sorted(rendered_keys.difference(occupied_keys)))
    exact = (overlap == candidate.overlap and
             emitted == tuple(sorted(_site_key(site, tolerance)
                                     for site in candidate.emitted)))
    payload = repr((candidate.parent_node, child_node,
                    candidate.production_id, production.production_kind,
                    production.required_shared_atoms,
                    overlap, emitted)).encode()
    return OverlapInclusionCertificate(
        candidate.parent_node, child_node, candidate.production_id,
        production.production_kind, production.required_shared_atoms,
        overlap, emitted, 0,
        len(overlap) >= production.required_shared_atoms and
        set(overlap).issubset(occupied_keys), exact,
        (production.production_kind == "overlap" or
         production.training_child_port_witnesses > 0),
        production.training_child_port_witnesses,
        hashlib.sha256(payload).hexdigest())


def _stationary_adapter(
    program: PromotedMacroProgram, nodes: Sequence[SymbolicMacroNode],
    steps: Sequence[SymbolicDerivationStep],
) -> tuple[PortGraphProduction | None, str | None]:
    selected = tuple(nodes[:7])
    if len(selected) < 3:
        return None, None
    selected_ids = {node.node_id for node in selected}
    prototype_by_id = {item.type_id: item for item in program.prototypes}
    children = []
    for node in selected:
        prototype = prototype_by_id[node.macro_type]
        chemistry = tuple(sorted(repr(species)
                                 for species, _ in prototype.sites))
        chirality_payload = repr(tuple(
            (repr(species), tuple(round(value / 1e-6) for value in point))
            for species, point in prototype.sites)).encode()
        children.append(ProductionChild(
            chemistry, hashlib.sha256(chirality_payload).hexdigest(),
            node.rotation, node.translation, prototype.proper_symmetries))
    index = {node.node_id: offset for offset, node in enumerate(selected)}
    productions = {item.production_id: item for item in
                   _compile_productions(program)}
    ports = []
    for step in steps:
        if (step.node.node_id not in selected_ids or
                step.node.parent_node not in selected_ids):
            continue
        production = productions[step.certificate.production_id]
        ports.append(ProductionPort(
            index[step.node.parent_node], index[step.node.node_id],
            tuple(map(str, production.symmetry_orbit_key)),
            tuple(key[0] for key in step.certificate.included_overlap_sites)))
    production = PortGraphProduction(tuple(children), tuple(ports), ())
    try:
        canonical = canonicalize_production(production)
    except ValueError:
        return production, None
    return production, canonical.normalized_key


def _compile_productions(
    program: PromotedMacroProgram,
) -> tuple[FrozenMacroProduction, ...]:
    result = [FrozenMacroProduction(
        index, port.parent_type, port.child_type,
        port.symmetry_orbit_key, "overlap",
        max(program.minimum_shared_atoms, len(port.overlap)),
        port.observations, 0)
        for index, port in enumerate(program.atlas.ports)]
    offset = len(result)
    result.extend(FrozenMacroProduction(
        offset + index, port.parent_type, port.child_type,
        port.symmetry_orbit_key, "boundary", 0,
        port.occurrence_observations, port.child_port_witnesses)
        for index, port in enumerate(program.boundary_ports))
    return tuple(result)


def _production_ports(program: PromotedMacroProgram):
    """Geometry payloads aligned exactly with ``_compile_productions``."""
    return tuple(program.atlas.ports) + tuple(program.boundary_ports)


def execute_macro_derivation(
    program: PromotedMacroProgram,
    seed_occurrences: Sequence[ClusterOccurrence], *,
    explicit_seed_sites: Sequence[Site] = (),
    maximum_levels: int = 2, maximum_new_nodes_per_level: int = 64,
    pose_tolerance: float = .03,
    ranker: Callable[[int, int, int, tuple[int, ...], int, int], object] | None = None,
) -> MacroDerivation:
    """Breadth-first replay; each level is fed only by the preceding level."""
    if maximum_levels < 0 or maximum_new_nodes_per_level < 1:
        raise ValueError("invalid derivation safety limits")
    if not seed_occurrences:
        raise ValueError("at least one macro seed is required")
    if pose_tolerance <= 0:
        raise ValueError("pose tolerance must be positive")
    prototypes = {item.type_id: item for item in program.prototypes}
    ports = _production_ports(program)
    productions = _compile_productions(program)
    expanded_ports = {}
    by_parent = {}
    for production in productions:
        by_parent.setdefault(production.parent_type, []).append(production)
    nodes = []
    for occurrence in seed_occurrences:
        if occurrence.type_id not in prototypes or not is_proper_rotation(
                occurrence.rotation):
            raise ValueError("seed must use a known type and proper pose")
        nodes.append(SymbolicMacroNode(
            len(nodes), occurrence.type_id, occurrence.rotation,
            occurrence.translation, 0, None, None))
    oriented_sites = _unique_sites(tuple(
        site for node in nodes for site in _render(
            prototypes[node.macro_type], node.rotation, node.translation)),
        pose_tolerance)
    exclusion = max(pose_tolerance, program.minimum_distance * .45)
    occupied_list = list(oriented_sites)
    for raw_species, raw_point in explicit_seed_sites:
        point = tuple(float(value) for value in raw_point)
        if len(point) != 3 or not all(math.isfinite(value) for value in point):
            raise ValueError("explicit seed sites need finite 3D coordinates")
        site: Site = (raw_species, point)  # type: ignore[assignment]
        _, emitted, invalid = _classify(
            (site,), occupied_list, pose_tolerance, exclusion)
        if invalid:
            raise ValueError("explicit seed site conflicts with known support")
        if emitted:
            occupied_list.append(site)
    occupied = _unique_sites(occupied_list, pose_tolerance)
    occupied_index = _SpatialSiteIndex(occupied, exclusion)
    occupied_by_coordinate = {
        tuple(round(value / pose_tolerance) for value in site[1]): site
        for site in occupied}
    occupied_species = {
        coordinate: site[0]
        for coordinate, site in occupied_by_coordinate.items()}
    occupied_site_keys = {_site_key(site, pose_tolerance)
                          for site in occupied}
    seed_sites = occupied
    seed_atom_count = len(occupied)
    existing_poses = {_pose_key(node.macro_type, node.rotation,
                                node.translation, pose_tolerance)
                      for node in nodes}
    frontier = tuple(nodes)
    steps = []
    explicit = []
    attempted = duplicate = conflict = insufficient = batch_conflict = 0
    for level in range(1, maximum_levels + 1):
        candidates = {}
        for parent in frontier:
            for production in by_parent.get(parent.macro_type, ()):
                child_prototype = prototypes[production.child_type]
                orbit = expanded_ports.get(production.production_id)
                if orbit is None:
                    orbit = expand_port_orbit(
                        prototypes[production.parent_type], child_prototype,
                        ports[production.production_id], pose_tolerance)
                    expanded_ports[production.production_id] = orbit
                for relative_rotation, relative_translation in orbit:
                    attempted += 1
                    rotation = matmul(parent.rotation, relative_rotation)
                    translation = _add(
                        parent.translation,
                        matvec(parent.rotation, relative_translation))
                    pose_key = _pose_key(
                        production.child_type, rotation, translation,
                        pose_tolerance)
                    if pose_key in existing_poses:
                        duplicate += 1
                        continue
                    rendered = _render(child_prototype, rotation, translation)
                    overlap, emitted, invalid = occupied_index.classify(
                        rendered, pose_tolerance, exclusion)
                    if invalid:
                        conflict += 1
                        continue
                    if len(overlap) < production.required_shared_atoms:
                        insufficient += 1
                        continue
                    if not emitted:
                        duplicate += 1
                        continue
                    rendered_key = tuple(sorted(_site_key(
                        site, pose_tolerance) for site in rendered))
                    candidate = _Candidate(
                        parent.node_id, production.production_id,
                        production.child_type, rotation, translation,
                        rendered, overlap, emitted)
                    candidates.setdefault(rendered_key, candidate)
        ordered = list(candidates.values())
        default_key = lambda item: (
            -len(item.overlap), -len(item.emitted), item.production_id,
            item.parent_node, _pose_key(item.child_type, item.rotation,
                                       item.translation, pose_tolerance))
        if ranker is None:
            ordered.sort(key=default_key)
        else:
            ordered.sort(key=lambda item: ranker(
                item.parent_node, item.production_id, item.child_type,
                productions[item.production_id].symmetry_orbit_key,
                len(item.overlap), len(item.emitted)))
        before = len(occupied_by_coordinate)
        accepted_nodes = []
        emitted_atoms = 0
        for candidate in ordered:
            if len(accepted_nodes) >= maximum_new_nodes_per_level:
                break
            overlap, emitted, invalid = occupied_index.classify(
                candidate.rendered, pose_tolerance, exclusion)
            production = productions[candidate.production_id]
            required = production.required_shared_atoms
            if invalid or len(overlap) < required or not emitted:
                batch_conflict += 1
                continue
            node = SymbolicMacroNode(
                len(nodes), candidate.child_type, candidate.rotation,
                candidate.translation, level, candidate.parent_node,
                candidate.production_id)
            candidate = _Candidate(
                candidate.parent_node, candidate.production_id,
                candidate.child_type, candidate.rotation,
                candidate.translation, candidate.rendered, overlap, emitted)
            certificate = _certificate(
                candidate, node.node_id, production, occupied, pose_tolerance,
                occupied_keys_before=occupied_site_keys)
            if not (certificate.overlap_is_subset and
                    certificate.emitted_is_exact_difference and
                    certificate.adjacency_witnessed_in_training):
                raise AssertionError("invalid overlap-inclusion certificate")
            newly_occupied = []
            for site in emitted:
                coordinate = tuple(round(value / pose_tolerance)
                                   for value in site[1])
                if (coordinate in occupied_species and
                        occupied_species[coordinate] != site[0]):
                    raise ValueError(
                        "unlike-colored sites coincide in the derivation")
                if coordinate not in occupied_by_coordinate:
                    occupied_species[coordinate] = site[0]
                    occupied_by_coordinate[coordinate] = site
                    occupied_site_keys.add(_site_key(site, pose_tolerance))
                    newly_occupied.append(site)
            occupied_index.extend(newly_occupied)
            existing_poses.add(_pose_key(
                node.macro_type, node.rotation, node.translation,
                pose_tolerance))
            nodes.append(node)
            accepted_nodes.append(node)
            emitted_atoms += len(emitted)
            steps.append(SymbolicDerivationStep(level, node, certificate))
        occupied = tuple(occupied_by_coordinate[key]
                         for key in sorted(occupied_by_coordinate))
        explicit.append(ExplicitDerivationLevel(
            level, len(frontier), len(accepted_nodes), before,
            emitted_atoms, len(occupied), occupied))
        frontier = tuple(accepted_nodes)
        if not frontier:
            break
    symbolic_count = seed_atom_count + sum(
        len(step.certificate.emitted_sites) for step in steps)
    stationary, stationary_key = _stationary_adapter(program, nodes, steps)
    return MacroDerivation(
        productions, tuple(nodes), tuple(steps), tuple(explicit),
        seed_sites, occupied,
        attempted, duplicate, conflict, insufficient, batch_conflict,
        symbolic_count, len(occupied), symbolic_count == len(occupied),
        True, False, stationary, stationary_key)


def _match(source: Sequence[Site], target: Sequence[Site],
           tolerance: float) -> int:
    unmatched = set(range(len(target)))
    count = 0
    for species, point in source:
        candidates = [index for index in unmatched
                      if target[index][0] == species and
                      math.dist(point, target[index][1]) <= tolerance]
        if candidates:
            chosen = min(candidates, key=lambda index:
                         math.dist(point, target[index][1]))
            unmatched.remove(chosen)
            count += 1
    return count


def score_macro_derivation(
    derivation: MacroDerivation, target_species: Sequence[Hashable],
    target_positions: Sequence[Sequence[float]], *, tolerance: float = .03,
) -> DerivationScore:
    """Post-hoc scorer; targets cannot affect a completed derivation."""
    if len(target_species) != len(target_positions) or tolerance <= 0:
        raise ValueError("invalid scoring target or tolerance")
    target = tuple((species, tuple(float(value) for value in point))
                   for species, point in zip(target_species, target_positions))
    seed_sites = len(derivation.seed_sites)
    emitted_count = sum(level.emitted_atoms
                        for level in derivation.explicit_levels)
    seed_keys = {_site_key(site, tolerance) for site in derivation.seed_sites}
    proposed = tuple(site for site in derivation.sites
                     if _site_key(site, tolerance) not in seed_keys)
    correct = _match(proposed, target, tolerance)
    heldout = max(0, len(target) - seed_sites)
    return DerivationScore(
        len(target), seed_sites, emitted_count, correct,
        correct / max(1, emitted_count), correct / max(1, heldout),
        derivation.target_used)
