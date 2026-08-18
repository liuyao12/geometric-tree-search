#!/usr/bin/env python3
"""Continuous finite graph kernel for partial irregular-support markings."""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_partial_irregular_port_graph import (
    PartialIrregularPortGraph, PartialPortEdge, PartialPortNode)


@dataclass(frozen=True)
class PartialGraphKernelSpec:
    neighbors: int = 5
    support_type_weight: float = .25
    node_weight: float = 1.
    edge_weight: float = 1.
    beta_prior: float = .5


@dataclass(frozen=True)
class PartialGraphKernelExample:
    group: Hashable
    graph: PartialIrregularPortGraph
    successful: bool


@dataclass(frozen=True)
class FrozenPartialGraphKernel:
    spec: PartialGraphKernelSpec
    examples: tuple[PartialGraphKernelExample, ...]
    model_digest: str
    target_used: bool = False


def _node_distance(left: PartialPortNode, right: PartialPortNode,
                   spec: PartialGraphKernelSpec) -> float:
    chemistry = 0. if left.action_species == right.action_species else 2.
    support_type = spec.support_type_weight * \
        (left.support_type_id != right.support_type_id)
    coverage = abs(left.matched_atoms / left.prototype_atoms -
                   right.matched_atoms / right.prototype_atoms)
    size = abs(math.log(left.prototype_atoms / right.prototype_atoms))
    evidence = abs(math.log((left.training_group_support + 1) /
                            (right.training_group_support + 1)))
    return chemistry + support_type + coverage + .4 * size + .15 * evidence


def _histogram_distance(left, right) -> float:
    first, second = dict(left), dict(right)
    keys = set(first) | set(second)
    total = max(1, sum(first.values()), sum(second.values()))
    return sum(abs(first.get(key, 0) - second.get(key, 0))
               for key in keys) / total


def _profile_values(edge: PartialPortEdge) -> tuple[int, ...]:
    return tuple(sorted(value for _species, pair in
                        edge.shared_distance_profiles for value in pair))


def _wasserstein(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    if not left and not right:
        return 0.
    length = max(len(left), len(right))
    first = left + (left[-1] if left else 0,) * (length - len(left))
    second = right + (right[-1] if right else 0,) * (length - len(right))
    return sum(abs(a - b) for a, b in zip(first, second)) / (4 * length)


def _edge_distance(left: PartialPortEdge, right: PartialPortEdge,
                   spec: PartialGraphKernelSpec) -> float:
    endpoint = min(
        _node_distance(left.endpoint_types[0], right.endpoint_types[0], spec) +
        _node_distance(left.endpoint_types[1], right.endpoint_types[1], spec),
        _node_distance(left.endpoint_types[0], right.endpoint_types[1], spec) +
        _node_distance(left.endpoint_types[1], right.endpoint_types[0], spec))
    shared = _histogram_distance(left.shared_species, right.shared_species)
    separation = min(2., abs(left.separation_bin - right.separation_bin) / 4)
    profile = _wasserstein(_profile_values(left), _profile_values(right))
    chirality = (0. if left.chirality == right.chirality else
                 .25 if 0 in (left.chirality, right.chirality) else 1.)
    return .35 * endpoint + shared + separation + profile + chirality


def _assignment_distance(left, right, distance, unmatched=2.) -> float:
    if not left and not right:
        return 0.
    if len(left) > len(right):
        left, right = right, left
    best = math.inf
    for chosen in itertools.permutations(range(len(right)), len(left)):
        value = sum(distance(item, right[index])
                    for item, index in zip(left, chosen))
        value += unmatched * (len(right) - len(left))
        best = min(best, value)
    return best / max(len(left), len(right), 1)


def partial_graph_distance(
        left: PartialIrregularPortGraph,
        right: PartialIrregularPortGraph,
        spec: PartialGraphKernelSpec = PartialGraphKernelSpec(),
        ) -> float:
    if left.target_used or right.target_used:
        raise ValueError("target-tainted graph cannot enter the kernel")
    node = _assignment_distance(
        left.nodes, right.nodes, lambda a, b: _node_distance(a, b, spec))
    edge = _assignment_distance(
        left.edges, right.edges, lambda a, b: _edge_distance(a, b, spec))
    return spec.node_weight * node + spec.edge_weight * edge


def fit_partial_graph_kernel(
        examples: Sequence[PartialGraphKernelExample],
        spec: PartialGraphKernelSpec = PartialGraphKernelSpec(),
        ) -> FrozenPartialGraphKernel:
    rows = tuple(examples)
    if (not rows or len({row.group for row in rows}) < 2
            or spec.neighbors < 1 or spec.beta_prior <= 0
            or spec.node_weight < 0 or spec.edge_weight < 0
            or spec.node_weight + spec.edge_weight <= 0
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid partial graph-kernel corpus")
    payload = (spec, tuple((row.group, row.graph.canonical_digest,
                            row.successful) for row in rows))
    return FrozenPartialGraphKernel(
        spec, rows, hashlib.sha256(repr(payload).encode()).hexdigest())


def score_partial_graph_kernel(
        model: FrozenPartialGraphKernel,
        graph: PartialIrregularPortGraph,
        ) -> float:
    ranked = sorted(((partial_graph_distance(graph, row.graph, model.spec),
                      row.graph.canonical_digest, row.successful)
                     for row in model.examples), key=lambda row: row[:2])
    selected = ranked[:min(model.spec.neighbors, len(ranked))]
    positive = sum(row[2] for row in selected)
    return (positive + model.spec.beta_prior) / \
        (len(selected) + 2 * model.spec.beta_prior)

