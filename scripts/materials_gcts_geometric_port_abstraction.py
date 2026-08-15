#!/usr/bin/env python3
"""Train-selected bounded geometry abstraction for causal frozen ports."""

from __future__ import annotations

import itertools
import math
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_causal_frontier_marking_ablation import (
    CausalGrowthTrace, FrozenFrontierAction, _fit, _rank)
from materials_gcts_oriented_overlap_ports import matvec, transpose

_PROTOTYPE_CACHE = {}
_PORT_CACHE = {}
_ANGLE_CACHE = {}


@dataclass(frozen=True)
class GeometryAbstractionSpec:
    normalized_distance_bin_width: float
    rotation_angle_bin_width: float
    include_axis_translation_invariant: bool
    include_incoming_outgoing_angle: bool
    minimum_state_support: int


@dataclass(frozen=True)
class GeometrySelectionAudit:
    spec: GeometryAbstractionSpec
    training_traces: int
    guarded_validation_traces: int
    guarded_domains_disjoint: bool
    validation_top_one_accuracy: float
    validation_exact_context_coverage: float
    validation_backoff_context_coverage: float
    model_states: int
    mdl_bits: float
    specifications_compared: int
    selected_on_training_only: bool


def nearest_neighbor_scale(positions: Sequence[Sequence[float]]) -> float:
    value = min(math.dist(left, right)
                for index, left in enumerate(positions)
                for right in positions[index + 1:])
    if not math.isfinite(value) or value <= 0:
        raise ValueError("training nearest-neighbor scale is invalid")
    return value


def _histogram(values) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(repr(value) for value in values).items()))


def _prototype_token(frozen, type_id: int):
    cache_key = id(frozen), type_id
    if cache_key in _PROTOTYPE_CACHE:
        return _PROTOTYPE_CACHE[cache_key]
    prototype = next(item for item in frozen.prototypes
                     if item.type_id == type_id)
    value = (len(prototype.sites),
             _histogram(tuple(species for species, _ in prototype.sites)))
    _PROTOTYPE_CACHE[cache_key] = value
    return value


def _norm(vector) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _unit(vector):
    length = _norm(vector)
    return None if length <= 1e-12 else tuple(value / length
                                              for value in vector)


def _rotation_angle(rotation) -> float:
    cosine = max(-1.0, min(1.0, (
        rotation[0][0] + rotation[1][1] + rotation[2][2] - 1.0) / 2.0))
    return math.acos(cosine)


def _axis_translation_invariant(rotation, translation) -> int:
    angle = _rotation_angle(rotation)
    direction = _unit(translation)
    sine = math.sin(angle)
    if direction is None or angle <= 1e-7:
        return -1
    if abs(sine) > 1e-7:
        axis = _unit((rotation[2][1] - rotation[1][2],
                      rotation[0][2] - rotation[2][0],
                      rotation[1][0] - rotation[0][1]))
    else:
        # At a half turn the antisymmetric part vanishes. R + I is 2 aa^T;
        # its longest row recovers the unoriented rotation axis robustly.
        rows = tuple(tuple(rotation[row][column] +
                           (1.0 if row == column else 0.0)
                           for column in range(3)) for row in range(3))
        axis = _unit(max(rows, key=_norm))
    if axis is None:
        return -1
    # Absolute alignment is invariant to the unavoidable axis-sign gauge.
    alignment = abs(sum(left * right for left, right in zip(axis, direction)))
    return min(3, int(alignment / .25))


def port_geometry_token(frozen, production_id: int,
                        spec: GeometryAbstractionSpec, train_nn_scale: float):
    cache_key = id(frozen), production_id, spec, train_nn_scale
    if cache_key in _PORT_CACHE:
        return _PORT_CACHE[cache_key]
    production = frozen.productions[production_id]
    port = production.port
    distance = _norm(port.relative_translation) / train_nn_scale
    token = (
        _prototype_token(frozen, port.parent_type),
        _prototype_token(frozen, port.child_type),
        min(len(port.overlap), 15), _histogram(port.overlap_species),
        min(31, int(distance / spec.normalized_distance_bin_width)),
        min(31, int(_rotation_angle(port.relative_rotation) /
                    spec.rotation_angle_bin_width)))
    if spec.include_axis_translation_invariant:
        token += (_axis_translation_invariant(
            port.relative_rotation, port.relative_translation),)
    _PORT_CACHE[cache_key] = token
    return token


def _incoming_outgoing_angle(frozen, incoming_id: int,
                             outgoing_id: int, width: float) -> int:
    cache_key = id(frozen), incoming_id, outgoing_id, width
    if cache_key in _ANGLE_CACHE:
        return _ANGLE_CACHE[cache_key]
    incoming = frozen.productions[incoming_id].port
    outgoing = frozen.productions[outgoing_id].port
    inverse = transpose(incoming.relative_rotation)
    inward = _unit(tuple(-value for value in matvec(
        inverse, incoming.relative_translation)))
    outward = _unit(outgoing.relative_translation)
    if inward is None or outward is None:
        return -1
    cosine = max(-1.0, min(1.0, sum(
        left * right for left, right in zip(inward, outward))))
    value = min(31, int(math.acos(cosine) / width))
    _ANGLE_CACHE[cache_key] = value
    return value


def abstract_trace(trace: CausalGrowthTrace, frozen,
                   spec: GeometryAbstractionSpec, train_nn_scale: float):
    incoming = tuple(sorted(port_geometry_token(
        frozen, port, spec, train_nn_scale)
                            for port in trace.incoming_ports))
    action = port_geometry_token(
        frozen, trace.chosen_outgoing_port, spec, train_nn_scale)
    if spec.include_incoming_outgoing_angle:
        action += (tuple(sorted(_incoming_outgoing_angle(
            frozen, port, trace.chosen_outgoing_port,
            spec.rotation_angle_bin_width)
                               for port in trace.incoming_ports)),)
    return CausalGrowthTrace(
        trace.parent_occurrence,
        _prototype_token(frozen, trace.parent_type), incoming, action,
        trace.occurrence_domain, trace.causal, trace.within_training_domain)


def abstract_action(action: FrozenFrontierAction, frozen,
                    raw_incoming: Sequence[int], spec: GeometryAbstractionSpec,
                    train_nn_scale: float) -> FrozenFrontierAction:
    incoming = tuple(sorted(port_geometry_token(
        frozen, port, spec, train_nn_scale) for port in raw_incoming))
    outgoing = port_geometry_token(
        frozen, int(action.production_id), spec, train_nn_scale)
    if spec.include_incoming_outgoing_angle:
        outgoing += (tuple(sorted(_incoming_outgoing_angle(
            frozen, port, int(action.production_id),
            spec.rotation_angle_bin_width) for port in raw_incoming)),)
    return FrozenFrontierAction(
        action.candidate_id, action.parent_occurrence,
        _prototype_token(frozen, int(action.parent_type)), incoming, outgoing,
        action.novel_site_keys, action.baseline_order)


def _guarded_split(traces: Sequence[CausalGrowthTrace]):
    desired = min(31, max(1, len(traces) // 16))
    stride = max(1, len(traces) // desired)
    validation = tuple(traces[index] for index in
                       range(stride // 2, len(traces), stride))[:desired]
    forbidden = {node for trace in validation
                 for node in trace.occurrence_domain}
    training = tuple(trace for trace in traces
                     if forbidden.isdisjoint(trace.occurrence_domain))
    train_nodes = {node for trace in training
                   for node in trace.occurrence_domain}
    if not training or not validation or train_nodes.intersection(forbidden):
        raise ValueError("guarded geometric marking split failed")
    return training, validation


def select_geometry_abstraction(
    raw_traces: Sequence[CausalGrowthTrace], frozen,
    train_nn_scale: float,
) -> GeometrySelectionAudit:
    """Choose bin widths/features/support by guarded train-only MDL."""
    raw_training, raw_validation = _guarded_split(raw_traces)
    specs = tuple(GeometryAbstractionSpec(*values) for values in
        itertools.product((.125, .25, .5),
                          (math.pi / 18, math.pi / 12, math.pi / 6),
                          (False, True), (False, True), (2, 4, 8, 16)))
    # Guarded validation ranks only train-observed alternatives for that raw
    # parent type. Enumerating every atlas port (including never-chosen orbit
    # variants) both changes the empirical decision problem and is needlessly
    # quadratic in a large frozen atlas.
    production_by_parent = {}
    for trace in raw_traces:
        production_by_parent.setdefault(trace.parent_type, set()).add(
            trace.chosen_outgoing_port)
    production_by_parent = {key: tuple(sorted(values))
                            for key, values in production_by_parent.items()}
    evaluated = []
    for spec in specs:
        training = tuple(abstract_trace(
            trace, frozen, spec, train_nn_scale) for trace in raw_training)
        validation = tuple(abstract_trace(
            trace, frozen, spec, train_nn_scale) for trace in raw_validation)
        model = _fit(training, spec.minimum_state_support)
        correct = exact_seen = backoff_seen = 0
        data_bits = 0.0
        for raw, abstract in zip(raw_validation, validation):
            candidates = []
            for production_id in production_by_parent.get(raw.parent_type, ()):
                raw_action = FrozenFrontierAction(
                    production_id, raw.parent_occurrence, raw.parent_type,
                    raw.incoming_ports, production_id, (), (production_id,))
                candidates.append(abstract_action(
                    raw_action, frozen, raw.incoming_ports, spec,
                    train_nn_scale))
            unique = {candidate.production_id: candidate
                      for candidate in candidates}
            order = sorted(unique.values(), key=lambda item: _rank(model, item))
            true = abstract.chosen_outgoing_port
            rank = next((index for index, item in enumerate(order, 1)
                         if item.production_id == true), len(order) + 1)
            correct += rank == 1
            data_bits += math.log2(max(1, rank))
            current_exact = ((abstract.parent_type,
                              abstract.incoming_ports) in model.exact)
            exact_seen += current_exact
            backoff_seen += (not current_exact and any(
                (abstract.parent_type, token) in model.order_one
                for token in abstract.incoming_ports))
        states = len(model.exact) + len(model.order_one)
        parameter_bits = 8.0 + 2.0 * states + math.log2(len(training) + 1)
        mdl = data_bits + parameter_bits
        evaluated.append((mdl, -correct, states, spec, exact_seen,
                          backoff_seen))
    mdl, negative_correct, states, spec, exact_seen, backoff_seen = min(
        evaluated, key=lambda item: (
            item[1], item[0], item[2], repr(item[3])))
    return GeometrySelectionAudit(
        spec, len(raw_training), len(raw_validation), True,
        -negative_correct / len(raw_validation),
        exact_seen / len(raw_validation),
        backoff_seen / len(raw_validation), states, mdl, len(specs), True)
