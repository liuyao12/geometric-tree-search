#!/usr/bin/env python3
"""Temporal typed incidence graph for a target-blind cluster lineage.

Each stage's partial-support matcher already certifies which occupied sites a
new action reuses.  This module transports those certificates into one finite
graph across stages.  Raw atom indices are used only to form incidence and are
then discarded; the public graph contains chemistry, support colors, proper
distance/chirality invariants, and directed earlier-to-later dependencies.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_supports import SpeciesKey, _species_key
from materials_gcts_partial_irregular_section import PartialIrregularSection


Point = tuple[float, float, float]
FeatureKey = tuple[Hashable, ...]
Embedding = tuple[tuple[FeatureKey, float], ...]


@dataclass(frozen=True, order=True)
class TemporalPortNode:
    stage_index: int
    support_type_id: int
    action_species: SpeciesKey
    matched_atoms: int
    prototype_atoms: int
    training_group_support: int


@dataclass(frozen=True, order=True)
class TemporalPortEdge:
    left_index: int
    right_index: int
    stage_pair: tuple[int, int]
    endpoint_types: tuple[TemporalPortNode, TemporalPortNode]
    shared_species: tuple[tuple[SpeciesKey, int], ...]
    separation_bin: int
    shared_distance_profiles: tuple[
        tuple[SpeciesKey, tuple[int, int]], ...]
    chirality: int
    earlier_site_used_by_later: bool
    connection_witnessed: bool


@dataclass(frozen=True)
class TemporalPartialPortGraph:
    nodes: tuple[TemporalPortNode, ...]
    edges: tuple[TemporalPortEdge, ...]
    stages: int
    dependency_edges: int
    connected_edges: int
    canonical_digest: str
    proper_se3_invariant: bool = True
    lattice_coordinates_used: bool = False
    raw_atom_ids_retained: bool = False
    target_used: bool = False


@dataclass(frozen=True)
class TemporalPortGraphExample:
    group: Hashable
    parent_group: Hashable
    graph: TemporalPartialPortGraph
    successful: bool


@dataclass(frozen=True)
class TemporalPortGraphValueSpec:
    ridge: float = 10.
    minimum_feature_groups: int = 2
    steps: int = 120
    learning_rate: float = .16
    parent_conditional: bool = True
    feature_domain: str = "full"


@dataclass(frozen=True)
class FrozenTemporalPortGraphValue:
    spec: TemporalPortGraphValueSpec
    feature_keys: tuple[FeatureKey, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: int
    training_examples: int
    positive_examples: int
    model_digest: str
    target_used: bool = False


def _point(value) -> Point:
    row = tuple(map(float, value))
    if len(row) != 3 or not all(map(math.isfinite, row)):
        raise ValueError("temporal port positions must be finite 3D points")
    return row  # type: ignore[return-value]


def _sub(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def _det(first, second, third):
    return (first[0] * (second[1] * third[2] - second[2] * third[1])
            - first[1] * (second[0] * third[2] - second[2] * third[0])
            + first[2] * (second[0] * third[1] - second[1] * third[0]))


def _node_color(node):
    return (node.stage_index, node.support_type_id, node.action_species,
            node.matched_atoms, node.prototype_atoms,
            node.training_group_support)


def _node_coarse(node):
    return (node.stage_index, node.action_species,
            node.matched_atoms, node.prototype_atoms)


def _edge_color(edge, nodes):
    left, right = nodes[edge.left_index], nodes[edge.right_index]
    endpoints = tuple(sorted((_node_color(left), _node_color(right))))
    return (edge.stage_pair, endpoints, edge.shared_species,
            edge.separation_bin, edge.shared_distance_profiles,
            edge.chirality, edge.earlier_site_used_by_later,
            edge.connection_witnessed)


def _edge_coarse(edge):
    return (edge.stage_pair, edge.shared_species, edge.separation_bin,
            edge.shared_distance_profiles, edge.chirality,
            edge.earlier_site_used_by_later, edge.connection_witnessed)


def temporal_partial_port_graph_embedding(
        graph: TemporalPartialPortGraph) -> Embedding:
    if graph.target_used:
        raise ValueError("target-tainted temporal graph cannot be ranked")
    features = Counter()
    incident = [[] for _node in graph.nodes]
    for node in graph.nodes:
        exact = _node_color(node)
        coarse = _node_coarse(node)
        features[("node", exact)] += 1
        features[("node-coarse", coarse)] += 1
    for edge in graph.edges:
        color = _edge_color(edge, graph.nodes)
        coarse = _edge_coarse(edge)
        features[("edge", color)] += 1
        features[("edge-coarse", coarse)] += 1
        incident[edge.left_index].append((edge, edge.right_index))
        incident[edge.right_index].append((edge, edge.left_index))
    for node, incident_rows in zip(graph.nodes, incident):
        messages = tuple((
            _edge_color(edge, graph.nodes),
            _node_color(graph.nodes[neighbor_index]))
            for edge, neighbor_index in incident_rows)
        features[("message", _node_color(node),
                  tuple(sorted(messages, key=repr)))] += 1
        coarse_messages = []
        for edge, neighbor_index in incident_rows:
            color = _edge_color(edge, graph.nodes)
            neighbor = _node_color(graph.nodes[neighbor_index])
            features[("message-one", _node_color(node), color,
                      neighbor)] += 1
            neighbor_node = graph.nodes[neighbor_index]
            coarse = (_edge_coarse(edge), _node_coarse(neighbor_node))
            coarse_messages.append(coarse)
            features[("message-one-coarse", _node_coarse(node),
                      *coarse)] += 1
        features[("message-coarse", _node_coarse(node),
                  tuple(sorted(coarse_messages, key=repr)))] += 1
    features[("global", graph.stages, len(graph.nodes), len(graph.edges),
              graph.dependency_edges, graph.connected_edges)] += 1
    return tuple(sorted(((key, float(value))
                         for key, value in features.items() if value),
                        key=lambda row: repr(row[0])))


def temporal_partial_port_graph(
        sections: Sequence[PartialIrregularSection],
        action_blocks: Sequence[Sequence[tuple[Sequence[float], Hashable]]],
        seed_positions: Sequence[Sequence[float]],
        seed_species: Sequence[Hashable], *, distance_scale: float,
        distance_bin_width: float = .25) -> TemporalPartialPortGraph:
    sections = tuple(sections)
    blocks = tuple(tuple(block) for block in action_blocks)
    seed_points = tuple(_point(point) for point in seed_positions)
    seed_colors = tuple(_species_key(value) for value in seed_species)
    actions = tuple((stage, _point(point), _species_key(species))
                    for stage, block in enumerate(blocks)
                    for point, species in block)
    if (not sections or len(sections) != len(blocks)
            or len(seed_points) != len(seed_colors)
            or any(len(section.action_matches) != len(block)
                   for section, block in zip(sections, blocks))
            or distance_scale <= 0 or distance_bin_width <= 0
            or not math.isfinite(distance_scale * distance_bin_width)
            or any(section.target_used for section in sections)):
        raise ValueError("invalid temporal partial port-graph inputs")
    quantum = distance_scale * distance_bin_width
    nodes = []
    supports = []
    cursor = 0
    prefix_limit = len(seed_points)
    for stage, (section, block) in enumerate(zip(sections, blocks)):
        local_limit = prefix_limit + len(block)
        for match, (_point_value, species) in zip(
                section.action_matches, block):
            if any(index < 0 or index >= local_limit
                   for index in match.matched_target_indices):
                raise ValueError("partial support escaped its temporal prefix")
            nodes.append(TemporalPortNode(
                stage, match.prototype_type_id, _species_key(species),
                match.matched_atoms, match.prototype_atoms,
                match.training_group_support))
            supports.append(frozenset(match.matched_target_indices))
        cursor += len(block)
        prefix_limit += len(block)
    if cursor != len(actions):
        raise AssertionError("temporal action accounting drift")
    positions = seed_points + tuple(point for _stage, point, _color in actions)
    colors = seed_colors + tuple(color for _stage, _point, color in actions)
    edges = []
    for left in range(len(actions)):
        for right in range(left + 1, len(actions)):
            left_stage, left_point, _ = actions[left]
            right_stage, right_point, _ = actions[right]
            shared = tuple(sorted(supports[left] & supports[right]))
            left_site = len(seed_points) + left
            right_site = len(seed_points) + right
            dependency = bool(left_stage < right_stage and
                              left_site in supports[right])
            shared_species = tuple(sorted(Counter(
                colors[index] for index in shared).items()))
            keyed_rows = []
            for index in shared:
                pair = tuple(sorted((
                    int(round(math.dist(
                        left_point, positions[index]) / quantum)),
                    int(round(math.dist(
                        right_point, positions[index]) / quantum)))))
                keyed_rows.append((colors[index], pair, index))
            keyed = tuple(sorted(keyed_rows, key=repr))
            profiles = tuple((species, pair)
                             for species, pair, _index in keyed)
            chirality = 0
            if len(keyed) >= 2 and keyed[0][:2] != keyed[1][:2]:
                first, second = keyed[0][2], keyed[1][2]
                volume = _det(_sub(right_point, left_point),
                              _sub(positions[first], left_point),
                              _sub(positions[second], left_point))
                epsilon = 1e-10 * distance_scale ** 3
                chirality = int(volume > epsilon) - int(volume < -epsilon)
            edges.append(TemporalPortEdge(
                left, right, (left_stage, right_stage),
                (nodes[left], nodes[right]), shared_species,
                int(round(math.dist(left_point, right_point) / quantum)),
                profiles, chirality, dependency, bool(shared or dependency)))
    provisional = TemporalPartialPortGraph(
        tuple(nodes), tuple(edges), len(blocks),
        sum(edge.earlier_site_used_by_later for edge in edges),
        sum(edge.connection_witnessed for edge in edges), "")
    embedding = temporal_partial_port_graph_embedding(provisional)
    return TemporalPartialPortGraph(
        provisional.nodes, provisional.edges, provisional.stages,
        provisional.dependency_edges, provisional.connected_edges,
        hashlib.sha256(repr(embedding).encode()).hexdigest())


def temporal_graph_feature_support(
        graphs: Sequence[tuple[Hashable, TemporalPartialPortGraph]],
        minimum_groups: int = 2):
    support = defaultdict(set)
    for group, graph in graphs:
        for key, value in temporal_partial_port_graph_embedding(graph):
            if value:
                support[key].add(group)
    return tuple(sorted((key for key, groups in support.items()
                         if len(groups) >= minimum_groups), key=repr))


def temporal_partial_port_prefix(
        graph: TemporalPartialPortGraph, stages: int) -> TemporalPartialPortGraph:
    """Return the exact induced prefix without consulting candidate targets."""
    if stages < 1 or stages > graph.stages or graph.target_used:
        raise ValueError("invalid temporal graph prefix")
    retained = tuple(index for index, node in enumerate(graph.nodes)
                     if node.stage_index < stages)
    inverse = {old: new for new, old in enumerate(retained)}
    nodes = tuple(graph.nodes[index] for index in retained)
    edges = tuple(TemporalPortEdge(
        inverse[edge.left_index], inverse[edge.right_index], edge.stage_pair,
        edge.endpoint_types, edge.shared_species, edge.separation_bin,
        edge.shared_distance_profiles, edge.chirality,
        edge.earlier_site_used_by_later, edge.connection_witnessed)
        for edge in graph.edges
        if edge.left_index in inverse and edge.right_index in inverse)
    provisional = TemporalPartialPortGraph(
        nodes, edges, stages,
        sum(edge.earlier_site_used_by_later for edge in edges),
        sum(edge.connection_witnessed for edge in edges), "")
    embedding = temporal_partial_port_graph_embedding(provisional)
    return TemporalPartialPortGraph(
        nodes, edges, stages, provisional.dependency_edges,
        provisional.connected_edges,
        hashlib.sha256(repr(embedding).encode()).hexdigest())


def _sigmoid(value):
    if value >= 0:
        inverse = math.exp(-min(value, 60.))
        return 1 / (1 + inverse)
    exponent = math.exp(max(value, -60.))
    return exponent / (1 + exponent)


def _pairwise_gradient(weights, vectors, paired):
    scores = tuple(sum(weights[index] * value for index, value in vector)
                   for vector in vectors)
    coefficients = [0.] * len(vectors)
    group_scale = 1 / len(paired)
    for positive, negative in paired:
        pair_scale = group_scale / (len(positive) * len(negative))
        for high in positive:
            for low in negative:
                error = pair_scale * (_sigmoid(scores[high] - scores[low]) - 1.)
                coefficients[high] += error
                coefficients[low] -= error
    gradient = [0.] * len(weights)
    for coefficient, vector in zip(coefficients, vectors):
        for index, value in vector:
            gradient[index] += coefficient * value
    return gradient


def fit_temporal_port_graph_value(
        examples: Sequence[TemporalPortGraphExample],
        spec: TemporalPortGraphValueSpec = TemporalPortGraphValueSpec(),
        *, embedding_cache: dict | None = None) -> FrozenTemporalPortGraphValue:
    rows = tuple(sorted(examples, key=lambda row: (
        repr(row.group), repr(row.parent_group), row.graph.canonical_digest,
        row.successful)))
    groups = tuple(sorted({row.group for row in rows}, key=repr))
    positive = sum(row.successful for row in rows)
    if (not rows or len(groups) < 2 or positive in (0, len(rows))
            or spec.ridge <= 0 or spec.minimum_feature_groups < 1
            or spec.steps < 1 or spec.learning_rate <= 0
            or spec.feature_domain not in ("full", "coarse")
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid temporal port-graph value corpus")
    cache = {} if embedding_cache is None else embedding_cache
    embeddings = []
    for row in rows:
        if row.graph.canonical_digest not in cache:
            cache[row.graph.canonical_digest] = \
                temporal_partial_port_graph_embedding(row.graph)
        embedding = dict(cache[row.graph.canonical_digest])
        if spec.feature_domain == "coarse":
            embedding = {key: value for key, value in embedding.items()
                         if key[0] in ("node-coarse", "edge-coarse",
                                      "message-one-coarse",
                                      "message-coarse", "global")}
        embeddings.append(embedding)
    support = defaultdict(set)
    for row, embedding in zip(rows, embeddings):
        for key, value in embedding.items():
            if value:
                support[key].add(row.group)
    keys = tuple(sorted((key for key, seen in support.items()
                         if len(seen) >= spec.minimum_feature_groups),
                        key=repr))
    if not keys:
        raise ValueError("no recurrent temporal port-graph features")
    scales = tuple(max(1e-6, math.sqrt(sum(
        embedding.get(key, 0.) ** 2 for embedding in embeddings) / len(rows)))
        for key in keys)
    indices = {key: index for index, key in enumerate(keys)}
    vectors = tuple(tuple((indices[key], value / scales[indices[key]])
                          for key, value in embedding.items()
                          if key in indices and value)
                    for embedding in embeddings)
    strata = defaultdict(lambda: ([], []))
    for index, row in enumerate(rows):
        stratum = (row.group, row.parent_group) if spec.parent_conditional \
            else row.group
        strata[stratum][0 if row.successful else 1].append(index)
    paired = tuple((high, low) for high, low in strata.values()
                   if high and low)
    if len(paired) < 2:
        raise ValueError("temporal graph value needs two contrasted strata")
    weights = [0.] * len(keys)
    inverse = 1 / len(rows)
    try:
        import numpy as np
    except ImportError:
        np = None
    if np is None:
        for step in range(spec.steps):
            gradient = _pairwise_gradient(weights, vectors, paired)
            rate = spec.learning_rate / math.sqrt(1 + step / 40)
            for index in range(len(weights)):
                weights[index] -= rate * (
                    gradient[index] + spec.ridge * weights[index] * inverse)
    else:
        matrix = np.zeros((len(rows), len(keys)), dtype=float)
        for row_index, vector in enumerate(vectors):
            for feature_index, value in vector:
                matrix[row_index, feature_index] = value
        values = np.zeros(len(keys), dtype=float)
        for step in range(spec.steps):
            scores = matrix @ values
            coefficients = np.zeros(len(rows), dtype=float)
            group_scale = 1 / len(paired)
            for high, low in paired:
                high_index = np.asarray(high, dtype=int)
                low_index = np.asarray(low, dtype=int)
                margins = scores[high_index, None] - scores[None, low_index]
                errors = 1 / (1 + np.exp(-np.clip(
                    margins, -60., 60.))) - 1.
                pair_scale = group_scale / errors.size
                coefficients[high_index] += errors.sum(axis=1) * pair_scale
                coefficients[low_index] -= errors.sum(axis=0) * pair_scale
            gradient = matrix.T @ coefficients
            rate = spec.learning_rate / math.sqrt(1 + step / 40)
            values -= rate * (gradient + spec.ridge * values * inverse)
        weights = list(map(float, values))
    payload = (spec, keys, scales, tuple(weights), len(groups), len(rows),
               positive)
    return FrozenTemporalPortGraphValue(
        spec, keys, scales, tuple(weights), len(groups), len(rows), positive,
        hashlib.sha256(repr(payload).encode()).hexdigest())


def score_temporal_port_graph_value(
        model: FrozenTemporalPortGraphValue, graph: TemporalPartialPortGraph,
        *, embedding_cache: dict | None = None) -> float:
    if graph.target_used:
        raise ValueError("target-tainted temporal graph cannot be scored")
    cache = {} if embedding_cache is None else embedding_cache
    if graph.canonical_digest not in cache:
        cache[graph.canonical_digest] = \
            temporal_partial_port_graph_embedding(graph)
    embedding = dict(cache[graph.canonical_digest])
    if model.spec.feature_domain == "coarse":
        embedding = {key: value for key, value in embedding.items()
                     if key[0] in ("node-coarse", "edge-coarse",
                                  "message-one-coarse", "message-coarse",
                                  "global")}
    return sum(weight * embedding.get(key, 0.) / scale
               for key, scale, weight in zip(
                   model.feature_keys, model.scales, model.weights))


__all__ = [
    "FrozenTemporalPortGraphValue", "TemporalPartialPortGraph",
    "TemporalPortEdge", "TemporalPortGraphExample",
    "TemporalPortGraphValueSpec", "TemporalPortNode",
    "fit_temporal_port_graph_value", "score_temporal_port_graph_value",
    "temporal_graph_feature_support", "temporal_partial_port_graph",
    "temporal_partial_port_graph_embedding", "temporal_partial_port_prefix"]
