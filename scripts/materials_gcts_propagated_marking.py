#!/usr/bin/env python3
"""Locally propagated GCTS section marks for recursive colored-point growth.

The global learned section is used once to initialize a bounded mark on every
seed site.  Thereafter a candidate receives its mark only from the marks on the
two clusters connected by a learned metric port.  Acceptance and chemical
color are functions of that propagated mark; inference never lifts a global
coordinate or queries the original point-set oracle.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Tuple

from materials_gcts_generic import AtomicConfiguration, matvec
from materials_gcts_geometry_vm import GeometryInstruction
from materials_gcts_icosahedral_modelset import (
    learned_species, lift_point, project, vector_norm)
from materials_gcts_port_cover_graph import (
    _bindings, _output, compile_gap_instruction)
from materials_gcts_recursive_connections import point_key

Point = Tuple[float, float, float]
Mark = Tuple[float, float, float]


@dataclass(frozen=True)
class PropagatedSectionMarking:
    seed_marks: tuple[tuple[Point, Mark], ...]
    transport_coefficients: tuple[float, float]
    window_radius: float
    ordered_species: tuple[str, ...]
    thresholds: tuple[float, ...]
    marking_dimension: int
    port_arity: int
    fitted_seed_atoms: int


@dataclass(frozen=True)
class MarkedConfiguration:
    configuration: AtomicConfiguration
    marks: tuple[tuple[Point, Mark], ...]


@dataclass(frozen=True)
class PropagatedWave:
    emitted_sites: frozenset[tuple[Point, str]]
    emitted_marks: tuple[tuple[Point, Mark], ...]
    candidate_groups: int
    outside_section_rejections: int
    inconsistent_mark_rejections: int


def _seed_mark(section, point: Point) -> Mark:
    centered = tuple(point[axis] - section.origin[axis] for axis in range(3))
    canonical = matvec(section.to_canonical, centered)
    bound = max(16, math.ceil(max(map(abs, canonical))) + 8)
    lifted, residual = lift_point(
        canonical, section.unit, coefficient_bound=bound)
    if residual > 1e-5:
        raise ValueError("seed site lies outside the learned module")
    return project(lifted, section.internal_vectors)


def fit_propagated_marking(
        instruction: GeometryInstruction,
        seed: AtomicConfiguration) -> PropagatedSectionMarking:
    """Fit seed marks and the conjugate affine port transport rule."""
    section = instruction.payload.color_section
    marks = tuple(sorted((point_key(point), _seed_mark(section, point))
                         for point in seed.positions))
    conjugate_scale = -1.0 / section.unit
    return PropagatedSectionMarking(
        marks, (1.0 - conjugate_scale, conjugate_scale),
        section.window_radius, section.ordered_species, section.thresholds,
        3, 2, len(seed.positions))


def initial_marked_configuration(
        seed: AtomicConfiguration,
        marking: PropagatedSectionMarking) -> MarkedConfiguration:
    if {point_key(point) for point in seed.positions} != {
            point for point, _ in marking.seed_marks}:
        raise ValueError("marking was not fitted to this seed configuration")
    return MarkedConfiguration(seed, marking.seed_marks)


def _transport(binding, known_marks, coefficients) -> Mark | None:
    inputs = tuple(known_marks.get(point_key(point))
                   for point in binding.points)
    if any(item is None for item in inputs):
        return None
    return tuple(sum(coefficient * mark[axis]
                     for coefficient, mark in zip(coefficients, inputs))
                 for axis in range(3))  # type: ignore[index]


def execute_propagated_wave(
        instruction: GeometryInstruction,
        marking: PropagatedSectionMarking,
        state: MarkedConfiguration,
        *, level: int,
        consensus_tolerance: float = 1e-5) -> PropagatedWave:
    """Apply one local frontier wave using only incoming carried marks."""
    node = compile_gap_instruction(instruction).nodes[0]
    known_marks = dict(state.marks)
    known_points = {point_key(point)
                    for point in state.configuration.positions}
    grouped = defaultdict(list)
    for binding in _bindings(node, state.configuration, level):
        point = _output(node.output, binding)
        if point not in known_points:
            grouped[point].append(binding)
    emitted = set()
    new_marks = {}
    outside = 0
    inconsistent = 0
    for point, bindings in grouped.items():
        predictions = tuple(mark for mark in (
            _transport(binding, known_marks,
                       marking.transport_coefficients)
            for binding in bindings) if mark is not None)
        if not predictions:
            inconsistent += 1
            continue
        mean = tuple(sum(mark[axis] for mark in predictions) /
                     len(predictions) for axis in range(3))
        if max(math.dist(mark, mean) for mark in predictions) > \
                consensus_tolerance:
            inconsistent += 1
            continue
        radius = vector_norm(mean)
        if radius > marking.window_radius + consensus_tolerance:
            outside += 1
            continue
        color = learned_species(
            radius, marking.ordered_species, marking.thresholds)
        emitted.add((point, color))
        new_marks[point] = mean
    return PropagatedWave(
        frozenset(emitted), tuple(sorted(new_marks.items())), len(grouped),
        outside, inconsistent)


def extend_marked_configuration(
        state: MarkedConfiguration,
        wave: PropagatedWave) -> MarkedConfiguration:
    sites = set(zip(map(point_key, state.configuration.positions),
                    state.configuration.species))
    sites.update(wave.emitted_sites)
    marks = dict(state.marks)
    marks.update(wave.emitted_marks)
    ordered = sorted(sites)
    configuration = AtomicConfiguration(
        state.configuration.name + "-propagated",
        tuple(point for point, _ in ordered),
        tuple(color for _, color in ordered), None, False,
        "Seed plus locally propagated GCTS section marks.")
    return MarkedConfiguration(configuration, tuple(sorted(marks.items())))
