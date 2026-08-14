#!/usr/bin/env python3
"""Recursively nestable relational port/cover graph for colored point sets.

All rules use the same five stages:
  binding domain -> affine output -> coincident grouping -> marking -> color.
Material-specific nouns do not occur in the graph or evaluator.  The current
compilers populate three finite domain/section variants from seed evidence.
"""

from __future__ import annotations

import itertools
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Tuple

from materials_gcts_generic import (
    AtomicConfiguration, fractional_to_cartesian, inverse3, matvec)
from materials_gcts_geometry_vm import (
    AnchorPayload, GeometryInstruction, InternalColorSection, OverlapPayload,
    TranslationPayload, _section_color)
from materials_gcts_metric_port_atlas import (
    pair_section_frontier_width)
from materials_gcts_recursive_connections import (
    local_cluster_types, map_to_prototypes, point_key)

Point = Tuple[float, float, float]
ColoredSite = Tuple[Point, str]


@dataclass(frozen=True)
class BindingDomain:
    arity: int
    relation: str
    parameters: Any


@dataclass(frozen=True)
class AffineOutput:
    coefficients: Tuple[float, ...]
    offset: Point


@dataclass(frozen=True)
class ConnectionSection:
    predicate: str
    parameters: Any
    minimum_consensus: str


@dataclass(frozen=True)
class ColorSection:
    predicate: str
    parameters: Any


@dataclass(frozen=True)
class CoverNode:
    node_id: str
    domain: BindingDomain
    output: AffineOutput
    connection: ConnectionSection
    color: ColorSection
    child_nodes: Tuple[str, ...]


@dataclass(frozen=True)
class PortCoverGraph:
    nodes: Tuple[CoverNode, ...]
    root_nodes: Tuple[str, ...]
    learned_from_seed_only: bool
    family_label_used: bool
    physical_potential_used: bool


@dataclass(frozen=True)
class Binding:
    points: Tuple[Point, ...]
    labels: Tuple[Any, ...]
    mark: Any
    literal_color: str | None = None


@dataclass(frozen=True)
class GraphExecution:
    visited_nodes: Tuple[str, ...]
    emitted_sites: frozenset[ColoredSite]
    novel_candidate_groups: int
    rejected_candidate_groups: int


def compile_instruction(instruction: GeometryInstruction) -> PortCoverGraph:
    """Normalize a selected VM instruction into the common graph schema."""
    payload = instruction.payload
    if isinstance(payload, TranslationPayload):
        node = CoverNode(
            "root", BindingDomain(1, "integer_cover", payload),
            AffineOutput((1.0,), (0.0, 0.0, 0.0)),
            ConnectionSection("always", None, "one"),
            ColorSection("binding_literal", None), ("root",))
    elif isinstance(payload, AnchorPayload):
        node = CoverNode(
            "root", BindingDomain(1, "typed_sites", payload),
            AffineOutput((payload.scale,), tuple(
                (1.0 - payload.scale) * value for value in payload.anchor)),
            ConnectionSection("admitted_type", dict(payload.color_rules),
                              "one"),
            ColorSection("type_table", dict(payload.color_rules)), ("root",))
    elif isinstance(payload, OverlapPayload):
        node = CoverNode(
            "root", BindingDomain(2, "metric_ports", payload),
            AffineOutput((1.0 - payload.scale, payload.scale),
                         (0.0, 0.0, 0.0)),
            ConnectionSection("port_pair_consensus", payload,
                              "ceil(seed_minimum / scale^level)"),
            ColorSection("bounded_section", payload.color_section), ("root",))
    else:
        raise ValueError("unsupported geometry instruction payload")
    return PortCoverGraph(
        (node,), ("root",), instruction.learned_from_seed_only,
        instruction.family_label_used, instruction.physical_potential_used)


def compile_gap_instruction(instruction: GeometryInstruction) -> PortCoverGraph:
    """Compile accepted single ports gated by the learned bounded section."""
    payload = instruction.payload
    if not isinstance(payload, OverlapPayload):
        raise ValueError("a gap node requires an overlap-port payload")
    node = CoverNode(
        "gap", BindingDomain(2, "metric_ports", payload),
        AffineOutput((1.0 - payload.scale, payload.scale),
                     (0.0, 0.0, 0.0)),
        ConnectionSection("bounded_section", payload.color_section, "one"),
        ColorSection("bounded_section", payload.color_section), ("gap",))
    return PortCoverGraph(
        (node,), ("gap",), instruction.learned_from_seed_only,
        instruction.family_label_used, instruction.physical_potential_used)


def _integer_bindings(payload: TranslationPayload,
                      state: AtomicConfiguration) -> Iterable[Binding]:
    inverse = inverse3(payload.basis)  # type: ignore[arg-type]
    coordinates = tuple(matvec(inverse, point) for point in state.positions)
    minimum = tuple(math.floor(min(point[axis] for point in coordinates) + 1e-5)
                    for axis in range(3))
    maximum = tuple(math.floor(max(point[axis] for point in coordinates) + 1e-5)
                    for axis in range(3))
    extents = tuple(maximum[axis] - minimum[axis] + 1 for axis in range(3))
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
                point = fractional_to_cartesian(
                    payload.basis, fractional)  # type: ignore[arg-type]
                yield Binding((point,), (chemical,), None, chemical)


def _typed_bindings(payload: AnchorPayload,
                    state: AtomicConfiguration) -> Iterable[Binding]:
    types = map_to_prototypes(local_cluster_types(
        state.positions, state.species, payload.radial_edges),
        payload.prototypes)
    for point, chemical, cluster_type in zip(
            state.positions, state.species, types):
        yield Binding((point,), (chemical,), cluster_type)


def _port_bindings(payload: OverlapPayload, state: AtomicConfiguration,
                   level: int) -> Iterable[Binding]:
    types = local_cluster_types(
        state.positions, state.species, payload.radial_edges)
    mapped = map_to_prototypes(types, payload.atlas.prototypes)
    center = payload.color_section.origin
    maximum_radius = max(math.dist(point, center) for point in state.positions)
    width = pair_section_frontier_width(
        payload.section, payload.atlas) * payload.scale ** max(0, level - 1)
    parents = (index for index, point in enumerate(state.positions)
               if math.dist(point, center) >= maximum_radius - width)
    maximum_distance = max((port[2] for port in payload.atlas.accepted_ports),
                           default=0.0) * payload.scale ** level + 1e-4
    cell_size = max(maximum_distance, 1e-9)
    grid = defaultdict(list)
    for index, point in enumerate(state.positions):
        grid[tuple(math.floor(value / cell_size) for value in point)].append(index)
    for parent in parents:
        point = state.positions[parent]
        cell = tuple(math.floor(value / cell_size) for value in point)
        for delta in itertools.product((-1, 0, 1), repeat=3):
            neighbor_cell = tuple(cell[axis] + delta[axis] for axis in range(3))
            for source in grid.get(neighbor_cell, ()):
                if source == parent:
                    continue
                source_point = state.positions[source]
                separation = math.dist(point, source_point)
                if separation > maximum_distance:
                    continue
                port = (mapped[parent], mapped[source], round(
                    separation / payload.scale ** level,
                    payload.atlas.distance_digits))
                if port in payload.atlas.accepted_ports:
                    yield Binding((point, source_point),
                                  (mapped[parent], mapped[source]), port)


def _bindings(node: CoverNode, state: AtomicConfiguration,
              level: int) -> Iterable[Binding]:
    if node.domain.relation == "integer_cover":
        return _integer_bindings(node.domain.parameters, state)
    if node.domain.relation == "typed_sites":
        return _typed_bindings(node.domain.parameters, state)
    if node.domain.relation == "metric_ports":
        return _port_bindings(node.domain.parameters, state, level)
    raise ValueError(f"unknown binding relation {node.domain.relation}")


def _output(output: AffineOutput, binding: Binding) -> Point:
    if len(output.coefficients) != len(binding.points):
        raise ValueError("affine output arity does not match binding")
    return point_key(tuple(output.offset[axis] + sum(
        coefficient * point[axis] for coefficient, point in
        zip(output.coefficients, binding.points)) for axis in range(3)))


def _inside_section(section: InternalColorSection, point: Point) -> bool:
    centered = tuple(point[axis] - section.origin[axis] for axis in range(3))
    canonical = matvec(section.to_canonical, centered)  # type: ignore[arg-type]
    from materials_gcts_icosahedral_modelset import (
        lift_point, project, vector_norm)
    coefficient_bound = max(16, math.ceil(max(map(abs, canonical))) + 8)
    lift, residual = lift_point(
        canonical, section.unit, coefficient_bound=coefficient_bound)
    return (residual <= 1e-5 and vector_norm(project(
        lift, section.internal_vectors)) <= section.window_radius + 1e-9)


def _accepted(node: CoverNode, point: Point,
              bindings: Tuple[Binding, ...], level: int) -> bool:
    if node.connection.predicate == "always":
        return True
    if node.connection.predicate == "admitted_type":
        return bindings[0].mark in node.connection.parameters
    if node.connection.predicate == "bounded_section":
        return _inside_section(node.connection.parameters, point)
    if node.connection.predicate == "port_pair_consensus":
        payload: OverlapPayload = node.connection.parameters
        ports = Counter(binding.mark for binding in bindings)
        unique = sorted(ports, key=repr)
        pair = lambda left, right: tuple(sorted((left, right), key=repr))
        supported = any(pair(left, right) in payload.section.accepted_pairs
                        for left, right in itertools.combinations_with_replacement(
                            unique, 2) if left != right or ports[left] >= 2)
        threshold = math.ceil(payload.seed_minimum_votes /
                              payload.scale ** level)
        return supported and len(bindings) >= threshold
    raise ValueError(f"unknown connection predicate {node.connection.predicate}")


def _color(node: CoverNode, point: Point,
           bindings: Tuple[Binding, ...]) -> str:
    if node.color.predicate == "binding_literal":
        colors = Counter(binding.literal_color for binding in bindings)
        return min(colors, key=lambda color: (-colors[color], color))
    if node.color.predicate == "type_table":
        colors = Counter(node.color.parameters[binding.mark]
                         for binding in bindings
                         if binding.mark in node.color.parameters)
        return min(colors, key=lambda color: (-colors[color], color))
    if node.color.predicate == "bounded_section":
        return _section_color(node.color.parameters, point)
    raise ValueError(f"unknown color predicate {node.color.predicate}")


def execute_graph(graph: PortCoverGraph, state: AtomicConfiguration,
                  *, level: int = 1) -> GraphExecution:
    """Execute every reachable node with one relational evaluation loop."""
    by_id = {node.node_id: node for node in graph.nodes}
    pending = list(graph.root_nodes)
    visited = []
    emitted = set()
    novel_candidates = 0
    known_points = {point_key(point) for point in state.positions}
    while pending:
        node_id = pending.pop(0)
        if node_id in visited:
            continue
        node = by_id[node_id]
        visited.append(node_id)
        grouped = defaultdict(list)
        for binding in _bindings(node, state, level):
            grouped[_output(node.output, binding)].append(binding)
        for point, candidates in grouped.items():
            frozen = tuple(candidates)
            if point not in known_points:
                novel_candidates += 1
                if _accepted(node, point, frozen, level):
                    emitted.add((point, _color(node, point, frozen)))
        pending.extend(child for child in node.child_nodes
                       if child not in visited)
    return GraphExecution(
        tuple(visited), frozenset(emitted), novel_candidates,
        novel_candidates - len(emitted))
