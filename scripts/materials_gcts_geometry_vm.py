#!/usr/bin/env python3
"""One geometry VM for recursive colored-point GCTS instructions.

Every instruction consumes a colored point cloud and emits new colored sites.
The VM knows no material or phase names. Compilers may choose a translation
cover, an anchored similarity section, or an overlap-port section from seed
evidence; execution and output semantics are shared.
"""

from __future__ import annotations

import itertools
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Tuple

from materials_gcts_generic import (
    AtomicConfiguration, fractional_to_cartesian, inverse3, matvec)
from materials_gcts_icosahedral_modelset import (
    infer_model, learned_species, lift_point, project, star_vectors,
    vector_norm)
from materials_gcts_metric_port_atlas import (
    MetricPortAtlas, PortPairSection, fit_metric_port_atlas,
    fit_port_pair_section, pair_section_frontier_width, pair_section_sites,
    propose_with_metric_ports)
from materials_gcts_recursive_connections import (
    LocalClusterType, local_cluster_types, map_to_prototypes, point_key)

ColoredSite = Tuple[Tuple[float, float, float], str]


@dataclass(frozen=True)
class TranslationPayload:
    basis: Tuple[Tuple[float, float, float], ...]
    motif: Tuple[Tuple[str, float, float, float], ...]


@dataclass(frozen=True)
class AnchorPayload:
    scale: float
    anchor: Tuple[float, float, float]
    radial_edges: Tuple[float, ...]
    prototypes: Tuple[LocalClusterType, ...]
    color_rules: Tuple[Tuple[LocalClusterType, str], ...]


@dataclass(frozen=True)
class InternalColorSection:
    unit: float
    internal_vectors: Tuple[Tuple[float, float, float], ...]
    ordered_species: Tuple[str, ...]
    thresholds: Tuple[float, ...]
    window_radius: float
    origin: Tuple[float, float, float]
    to_canonical: Tuple[Tuple[float, float, float], ...]


@dataclass(frozen=True)
class OverlapPayload:
    scale: float
    radial_edges: Tuple[float, ...]
    atlas: MetricPortAtlas
    section: PortPairSection
    seed_minimum_votes: int
    color_section: InternalColorSection


@dataclass(frozen=True)
class GeometryInstruction:
    opcode: str
    payload: Any
    learned_from_seed_only: bool = True
    family_label_used: bool = False
    physical_potential_used: bool = False


@dataclass(frozen=True)
class GeometryExecution:
    opcode: str
    input_atoms: int
    emitted_sites: frozenset[ColoredSite]


def _translation_sites(payload: TranslationPayload,
                       state: AtomicConfiguration) -> frozenset[ColoredSite]:
    inverse = inverse3(payload.basis)  # type: ignore[arg-type]
    coordinates = tuple(matvec(inverse, point) for point in state.positions)
    minimum = tuple(math.floor(min(point[axis] for point in coordinates) + 1e-5)
                    for axis in range(3))
    maximum = tuple(math.floor(max(point[axis] for point in coordinates) + 1e-5)
                    for axis in range(3))
    extents = tuple(maximum[axis] - minimum[axis] + 1 for axis in range(3))
    known = set(zip(map(point_key, state.positions), state.species))
    emitted = set()
    for image in itertools.product((0, 1), repeat=3):
        if image == (0, 0, 0):
            continue
        offset = tuple(image[axis] * extents[axis] for axis in range(3))
        for cell in itertools.product(*(range(minimum[axis], maximum[axis] + 1)
                                        for axis in range(3))):
            shifted = tuple(cell[axis] + offset[axis] for axis in range(3))
            for chemical, fx, fy, fz in payload.motif:
                fractional = tuple(shifted[axis] + (fx, fy, fz)[axis]
                                   for axis in range(3))
                point = point_key(fractional_to_cartesian(
                    payload.basis, fractional))  # type: ignore[arg-type]
                if (point, chemical) not in known:
                    emitted.add((point, chemical))
    return frozenset(emitted)


def _anchor_sites(payload: AnchorPayload,
                  state: AtomicConfiguration) -> frozenset[ColoredSite]:
    types = map_to_prototypes(local_cluster_types(
        state.positions, state.species, payload.radial_edges),
        payload.prototypes)
    rules = dict(payload.color_rules)
    known = {point_key(point) for point in state.positions}
    emitted = set()
    for point, cluster_type in zip(state.positions, types):
        if cluster_type not in rules:
            continue
        image = point_key(tuple(
            payload.anchor[axis] + payload.scale * (
                point[axis] - payload.anchor[axis]) for axis in range(3)))
        if image not in known:
            emitted.add((image, rules[cluster_type]))
    return frozenset(emitted)


def _section_color(section: InternalColorSection,
                   point: Tuple[float, float, float]) -> str:
    centered = tuple(point[axis] - section.origin[axis] for axis in range(3))
    canonical = matvec(section.to_canonical, centered)  # type: ignore[arg-type]
    coefficient_bound = max(16, math.ceil(max(map(abs, canonical))) + 8)
    lift, residual = lift_point(
        canonical, section.unit, coefficient_bound=coefficient_bound)
    if residual > 1e-5:
        raise ValueError("accepted port endpoint is outside the learned module")
    radius = vector_norm(project(lift, section.internal_vectors))
    return learned_species(radius, section.ordered_species, section.thresholds)


def _overlap_sites(payload: OverlapPayload, state: AtomicConfiguration,
                   level: int) -> frozenset[ColoredSite]:
    types = local_cluster_types(
        state.positions, state.species, payload.radial_edges)
    center = payload.color_section.origin
    maximum_radius = max(math.dist(point, center)
                         for point in state.positions)
    frontier_width = pair_section_frontier_width(
        payload.section, payload.atlas) * payload.scale ** max(0, level - 1)
    parents = tuple(index for index, point in enumerate(state.positions)
                    if math.dist(point, center) >=
                    maximum_radius - frontier_width)
    proposals = propose_with_metric_ports(
        payload.atlas, state.positions, types,
        level_scale=payload.scale ** level, parent_indices=parents)
    known = {point_key(point) for point in state.positions}
    pair_sites = pair_section_sites(
        payload.section, payload.atlas, state.positions, types,
        level_scale=payload.scale ** level, parent_indices=parents) - known
    threshold = math.ceil(payload.seed_minimum_votes /
                          payload.scale ** level)
    accepted = {point for point in pair_sites
                if proposals.votes[point] >= threshold}
    return frozenset((point, _section_color(payload.color_section, point))
                     for point in accepted)


def execute(instruction: GeometryInstruction, state: AtomicConfiguration,
            *, level: int = 1) -> GeometryExecution:
    """Execute one instruction through the shared colored-site contract."""
    if level < 1:
        raise ValueError("geometry VM levels start at one")
    if instruction.opcode == "translation_cover":
        sites = _translation_sites(instruction.payload, state)
    elif instruction.opcode == "anchor_similarity":
        sites = _anchor_sites(instruction.payload, state)
    elif instruction.opcode == "overlap_section":
        sites = _overlap_sites(instruction.payload, state, level)
    else:
        raise ValueError(f"unknown geometry opcode {instruction.opcode}")
    return GeometryExecution(instruction.opcode, len(state.positions), sites)


def compile_translation(rule) -> GeometryInstruction:
    return GeometryInstruction("translation_cover", TranslationPayload(
        rule.translation_basis, rule.translation_motif))


def compile_anchor(seed: AtomicConfiguration, scale: float,
                   radial_edges: Tuple[float, ...], anchor) -> GeometryInstruction:
    prototypes = local_cluster_types(seed.positions, seed.species, radial_edges)
    sites = {point_key(point): color for point, color in
             zip(seed.positions, seed.species)}
    evidence = {}
    for point, cluster_type in zip(seed.positions, prototypes):
        image = point_key(tuple(anchor[axis] + scale * (
            point[axis] - anchor[axis]) for axis in range(3)))
        if image in sites:
            evidence.setdefault(cluster_type, Counter())[sites[image]] += 1
    rules = tuple(sorted((cluster_type, min(colors, key=lambda color: (
        -colors[color], color))) for cluster_type, colors in evidence.items()))
    return GeometryInstruction("anchor_similarity", AnchorPayload(
        scale, anchor, radial_edges, tuple(sorted(set(prototypes))), rules))


def compile_overlap(seed: AtomicConfiguration, scale: float,
                    radial_edges: Tuple[float, ...], atlas: MetricPortAtlas,
                    pair_section: PortPairSection,
                    seed_minimum_votes: int, rule=None) -> GeometryInstruction:
    if rule is None:
        from materials_gcts_parametric_recursive import discover_rule
        rule = discover_rule(seed)
    if rule.origin is None or rule.to_canonical is None:
        raise ValueError("overlap color section needs a learned rigid frame")
    canonical = AtomicConfiguration(
        seed.name + "-canonical", tuple(matvec(rule.to_canonical, tuple(
            point[axis] - rule.origin[axis] for axis in range(3)))
            for point in seed.positions), seed.species, None, False,
        seed.provenance)
    unit, lifted, window, thresholds, residual = infer_model(canonical)
    if residual > 1e-5:
        raise ValueError("overlap color section needs an exact learned module")
    internal = star_vectors(-1.0 / unit)
    radii = {}
    for lift, chemical in lifted.items():
        radii.setdefault(chemical, []).append(vector_norm(project(lift, internal)))
    ordered = tuple(sorted(radii, key=lambda chemical:
                           sum(radii[chemical]) / len(radii[chemical])))
    color = InternalColorSection(
        unit, internal, ordered, thresholds, window, rule.origin,
        rule.to_canonical)
    return GeometryInstruction("overlap_section", OverlapPayload(
        scale, radial_edges, atlas, pair_section, seed_minimum_votes, color))


def compile_metric_overlap_from_seed(
        seed: AtomicConfiguration) -> GeometryInstruction:
    """Discover and compile an overlap program without a family label.

    Radial descriptors are expressed in units of the observed median nearest
    neighbor distance.  The dimensionless boundaries are generic shell bins,
    not material-specific distances.  The recursive scale and internal section
    are accepted only when ``discover_rule`` finds them from the same seed.
    """
    from materials_gcts_parametric_recursive import discover_rule

    rule = discover_rule(seed)
    if (rule.family != "internal_section_inflation" or rule.scale is None or
            rule.origin is None):
        raise ValueError("seed does not admit an internal-section overlap rule")
    nearest = tuple(min(math.dist(point, other)
                        for other_index, other in enumerate(seed.positions)
                        if other_index != index)
                    for index, point in enumerate(seed.positions))
    nearest_shells = Counter(round(distance, 5) for distance in nearest)
    minimum_shell_support = max(2, math.ceil(.05 * len(nearest)))
    recurrent_shells = tuple(distance for distance, support in
                             nearest_shells.items()
                             if support >= minimum_shell_support)
    if not recurrent_shells:
        raise ValueError("seed has no recurrent nearest-neighbor shell")
    unit_distance = min(recurrent_shells)
    radial_edges = tuple(unit_distance * ratio for ratio in
                         (1.31, 1.97, 2.62, 3.56))
    types = local_cluster_types(seed.positions, seed.species, radial_edges)
    atlas = fit_metric_port_atlas(
        seed.positions, types, seed.positions, rule.scale,
        target_colors=seed.species,
        observable_center=rule.origin,
        # The outermost observed site is inside, rather than exactly on, the
        # unknown sampling boundary. A small learned-shell padding prevents
        # treating valid boundary proposals as observed negatives.
        observable_radius=(max(math.dist(point, rule.origin)
                               for point in seed.positions) +
                           .1 * unit_distance))
    section = fit_port_pair_section(
        atlas, seed.positions, types, seed.positions)
    proposals = propose_with_metric_ports(
        atlas, seed.positions, types)
    known = {point_key(point) for point in seed.positions}
    pair_sites = pair_section_sites(
        section, atlas, seed.positions, types)
    votes = tuple(proposals.votes[point] for point in pair_sites
                  if point in known)
    if not votes:
        raise ValueError("learned overlap program has no seed-supported sites")
    return compile_overlap(
        seed, rule.scale, radial_edges, atlas, section, min(votes), rule)


def transform_instruction(
        instruction: GeometryInstruction,
        rotation: Tuple[Tuple[float, float, float], ...],
        translation: Tuple[float, float, float]) -> GeometryInstruction:
    """Move a learned instruction with its point cloud for invariance tests."""
    transpose = tuple(tuple(rotation[column][row] for column in range(3))
                      for row in range(3))
    move = lambda point: tuple(sum(rotation[row][column] * point[column]
                                   for column in range(3)) + translation[row]
                               for row in range(3))
    payload = instruction.payload
    if instruction.opcode == "translation_cover":
        payload = TranslationPayload(
            tuple(tuple(sum(rotation[row][column] * vector[column]
                            for column in range(3)) for row in range(3))
                  for vector in payload.basis), payload.motif)
    elif instruction.opcode == "anchor_similarity":
        payload = AnchorPayload(
            payload.scale, move(payload.anchor), payload.radial_edges,
            payload.prototypes, payload.color_rules)
    elif instruction.opcode == "overlap_section":
        section = payload.color_section
        # canonical = old_frame * R^T * (moved - moved_origin)
        moved_frame = tuple(tuple(sum(section.to_canonical[row][inner] *
                                      transpose[inner][column]
                                      for inner in range(3))
                                  for column in range(3)) for row in range(3))
        color = InternalColorSection(
            section.unit, section.internal_vectors, section.ordered_species,
            section.thresholds, section.window_radius, move(section.origin),
            moved_frame)
        payload = OverlapPayload(
            payload.scale, payload.radial_edges, payload.atlas,
            payload.section, payload.seed_minimum_votes, color)
    return GeometryInstruction(
        instruction.opcode, payload, instruction.learned_from_seed_only,
        instruction.family_label_used, instruction.physical_potential_used)
