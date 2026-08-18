#!/usr/bin/env python3
"""Bounded message-passing value on certified irregular-support port graphs.

The encoder never authorizes geometry.  It transports finite, proper-SE(3)
invariant node and port evidence already certified by
``partial_irregular_port_graph`` and ranks an unchanged exact candidate set.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence, Union

from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortEdge,
    PartialPortNode)


FeatureKey = tuple[Hashable, ...]
Embedding = tuple[tuple[FeatureKey, float], ...]


@dataclass(frozen=True)
class PartialMessagePassingSpec:
    neighbors: int = 5
    depth: int = 1
    support_type_weight: float = .25
    message_weight: float = 1.
    beta_prior: float = .5


@dataclass(frozen=True)
class PartialMessagePassingExample:
    group: Hashable
    graph: PartialIrregularPortGraph
    successful: bool


@dataclass(frozen=True)
class FrozenPartialMessagePassingValue:
    spec: PartialMessagePassingSpec
    examples: tuple[PartialMessagePassingExample, ...]
    embeddings: tuple[Embedding, ...]
    model_digest: str
    target_used: bool = False


def _add(target: dict[FeatureKey, float], key: FeatureKey,
         value: float) -> None:
    if value:
        target[key] = target.get(key, 0.) + value


def _node_features(node: PartialPortNode,
                   spec: PartialMessagePassingSpec) -> dict[FeatureKey, float]:
    result: dict[FeatureKey, float] = {}
    _add(result, ("chemistry", node.action_species), 1.)
    _add(result, ("support-type", node.support_type_id),
         spec.support_type_weight)
    _add(result, ("coverage",), node.matched_atoms / node.prototype_atoms)
    _add(result, ("support-size",), math.log1p(node.prototype_atoms) / 4.)
    _add(result, ("group-evidence",),
         math.log1p(node.training_group_support) / 3.)
    return result


def _edge_features(edge: Union[PartialPortEdge, PartialIncidenceEdge]
                   ) -> dict[FeatureKey, float]:
    result: dict[FeatureKey, float] = {}
    _add(result, ("connection-witnessed",
                  bool(getattr(edge, "connection_witnessed", True))), 1.)
    shared_total = max(1, sum(count for _species, count in
                              edge.shared_species))
    for species, count in edge.shared_species:
        _add(result, ("shared-chemistry", species), count / shared_total)
    for anchor in (0, 4, 8, 12, 16, 24):
        _add(result, ("separation-rbf", anchor),
             math.exp(-((edge.separation_bin - anchor) / 4.) ** 2))
    profile = tuple(value for _species, pair in
                    edge.shared_distance_profiles for value in pair)
    if profile:
        mean = sum(profile) / len(profile)
        variance = sum((value - mean) ** 2 for value in profile) / len(profile)
        _add(result, ("profile-mean",), mean / 16.)
        _add(result, ("profile-spread",), math.sqrt(variance) / 8.)
    _add(result, ("chirality", edge.chirality), 1.)
    return result


def _incident(edges: Sequence[PartialPortEdge], node: PartialPortNode):
    for edge in edges:
        left, right = edge.endpoint_types
        if node == left:
            yield edge, right
        if node == right:
            yield edge, left


def _indexed_incident(graph: PartialIrregularPortGraph, node_index: int):
    for edge in graph.incidence_edges:
        if edge.left_index == node_index:
            yield edge, edge.right_index
        elif edge.right_index == node_index:
            yield edge, edge.left_index


def partial_message_passing_embedding(
        graph: PartialIrregularPortGraph,
        spec: PartialMessagePassingSpec = PartialMessagePassingSpec(),
        ) -> Embedding:
    if graph.target_used:
        raise ValueError("target-tainted graph cannot enter message passing")
    if (spec.depth < 0 or spec.depth > 3 or spec.neighbors < 1
            or spec.support_type_weight < 0 or spec.message_weight < 0
            or spec.beta_prior <= 0):
        raise ValueError("invalid partial message-passing specification")
    nodes = tuple(sorted(graph.nodes))
    edges = tuple(sorted(graph.edges))
    current = [_node_features(node, spec) for node in nodes]
    pooled: dict[FeatureKey, float] = {}

    def pool(round_index: int, rows: Sequence[Mapping[FeatureKey, float]]):
        scale = 1 / max(1, len(rows))
        keys = set().union(*(row.keys() for row in rows)) if rows else set()
        for key in keys:
            values = [row.get(key, 0.) for row in rows]
            _add(pooled, ("round", round_index, "mean") + key,
                 sum(values) * scale)
            _add(pooled, ("round", round_index, "max") + key,
                 max(values, default=0.))

    pool(0, current)
    for round_index in range(1, spec.depth + 1):
        updated = []
        for node_index, node in enumerate(nodes):
            row = {("self",) + key: .5 * value
                   for key, value in current[node_index].items()}
            has_indexed_incidence = bool(graph.incidence_edges)
            indexed = tuple(_indexed_incident(graph, node_index))
            incidents = indexed if has_indexed_incidence else tuple(
                _incident(edges, node))
            normalization = spec.message_weight / max(1, len(incidents))
            for edge, neighbor in incidents:
                if has_indexed_incidence:
                    neighbor_index = neighbor
                else:
                    try:
                        neighbor_index = nodes.index(neighbor)
                    except ValueError as error:
                        raise ValueError(
                            "port endpoint is absent from graph") from error
                for key, value in current[neighbor_index].items():
                    _add(row, ("neighbor",) + key,
                         normalization * value)
                for key, value in _edge_features(edge).items():
                    _add(row, ("port",) + key,
                         normalization * value)
            updated.append(row)
        current = updated
        pool(round_index, current)

    # Global port chemistry is retained without endpoint IDs.  Incidence is
    # supplied only by the bounded propagation above.
    pooled_edges = graph.incidence_edges or edges
    if pooled_edges:
        scale = 1 / len(pooled_edges)
        for edge in pooled_edges:
            for key, value in _edge_features(edge).items():
                _add(pooled, ("global-port",) + key, scale * value)
    _add(pooled, ("isolated-fraction",),
         graph.isolated_nodes / max(1, len(graph.nodes)))
    return tuple(sorted(pooled.items(), key=lambda row: repr(row[0])))


def message_embedding_distance(left: Embedding, right: Embedding) -> float:
    first, second = dict(left), dict(right)
    keys = set(first) | set(second)
    if not keys:
        return 0.
    return math.sqrt(sum((first.get(key, 0.) - second.get(key, 0.)) ** 2
                         for key in keys) / len(keys))


def fit_partial_message_passing_value(
        examples: Sequence[PartialMessagePassingExample],
        spec: PartialMessagePassingSpec = PartialMessagePassingSpec(),
        ) -> FrozenPartialMessagePassingValue:
    rows = tuple(examples)
    if (not rows or len({row.group for row in rows}) < 2
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid partial message-passing corpus")
    embeddings = tuple(partial_message_passing_embedding(row.graph, spec)
                       for row in rows)
    payload = (spec, tuple((row.group, row.graph.canonical_digest,
                            row.successful, embedding)
                           for row, embedding in zip(rows, embeddings)))
    return FrozenPartialMessagePassingValue(
        spec, rows, embeddings,
        hashlib.sha256(repr(payload).encode()).hexdigest())


def score_partial_message_passing_value(
        model: FrozenPartialMessagePassingValue,
        graph: PartialIrregularPortGraph,
        ) -> float:
    embedding = partial_message_passing_embedding(graph, model.spec)
    ranked = sorted((message_embedding_distance(embedding, trained),
                     row.graph.canonical_digest, row.successful)
                    for row, trained in zip(model.examples,
                                            model.embeddings))
    selected = ranked[:min(model.spec.neighbors, len(ranked))]
    positive = sum(row[2] for row in selected)
    return (positive + model.spec.beta_prior) / \
        (len(selected) + 2 * model.spec.beta_prior)
