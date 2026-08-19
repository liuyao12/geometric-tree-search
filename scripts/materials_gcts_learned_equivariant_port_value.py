#!/usr/bin/env python3
"""Train-learned invariant interactions on exact irregular-port incidence.

Candidate geometry is frozen elsewhere.  This module only ranks those exact
actions by learning sparse source-node × port × neighbor-node interactions.
Every message is formed in the canonical unlabeled incidence graph and pooled
afterwards, so atom/action order and global proper rigid motion never enter.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortNode)


FeatureKey = tuple[Hashable, ...]
Embedding = tuple[tuple[FeatureKey, float], ...]


@dataclass(frozen=True)
class LearnedEquivariantPortExample:
    group: Hashable
    graph: PartialIrregularPortGraph
    successful: bool


@dataclass(frozen=True)
class LearnedEquivariantPortSpec:
    interaction_order: int = 3
    support_type_weight: float = 0.
    ridge: float = 1.
    minimum_feature_groups: int = 2
    steps: int = 160
    learning_rate: float = .16
    objective: str = "classification"


@dataclass(frozen=True)
class FrozenLearnedEquivariantPortValue:
    spec: LearnedEquivariantPortSpec
    feature_keys: tuple[FeatureKey, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    training_groups: int
    training_examples: int
    positive_examples: int
    model_digest: str
    target_used: bool = False


def _add(target, key, value):
    if value:
        target[key] = target.get(key, 0.) + value


def _node_features(node: PartialPortNode, support_type_weight: float):
    result = {
        ("constant",): 1.,
        ("chemistry", node.action_species): 1.,
        ("coverage",): node.matched_atoms / node.prototype_atoms,
        ("coverage-square",):
            (node.matched_atoms / node.prototype_atoms) ** 2,
        ("support-size",): math.log1p(node.prototype_atoms) / 4.,
        ("group-evidence",): math.log1p(node.training_group_support) / 3.,
    }
    if support_type_weight:
        result[("support-type", node.support_type_id)] = support_type_weight
    return result


def _edge_features(edge: PartialIncidenceEdge):
    result = {
        ("constant",): 1.,
        ("connection-witnessed", edge.connection_witnessed): 1.,
    }
    actual_shared = sum(count for _species, count in edge.shared_species)
    shared_total = max(1, actual_shared)
    _add(result, ("shared-count",), math.log1p(actual_shared) / 3.)
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


def _pool(target, prefix, rows):
    if not rows:
        return
    keys = set().union(*(row.keys() for row in rows))
    inverse = 1 / len(rows)
    for key in keys:
        values = tuple(row.get(key, 0.) for row in rows)
        _add(target, prefix + ("mean",) + key, sum(values) * inverse)
        _add(target, prefix + ("max",) + key, max(values))


def equivariant_port_interaction_embedding(
        graph: PartialIrregularPortGraph,
        spec: LearnedEquivariantPortSpec = LearnedEquivariantPortSpec(),
        ) -> Embedding:
    if graph.target_used:
        raise ValueError("target-tainted graph cannot enter port interactions")
    if (spec.interaction_order not in (2, 3)
            or spec.support_type_weight < 0):
        raise ValueError("invalid equivariant port-interaction specification")
    if graph.edges and not graph.incidence_edges:
        raise ValueError("exact incidence is required for learned messages")
    node_features = tuple(_node_features(
        node, spec.support_type_weight) for node in graph.nodes)
    incidents = [[] for _node in graph.nodes]
    for edge in graph.incidence_edges:
        if (edge.left_index < 0 or edge.right_index >= len(graph.nodes)
                or edge.left_index >= edge.right_index):
            raise ValueError("invalid canonical incidence endpoint")
        incidents[edge.left_index].append((edge, edge.right_index))
        incidents[edge.right_index].append((edge, edge.left_index))
    updated = []
    for source_index, source in enumerate(node_features):
        row = {("self",) + key: value for key, value in source.items()}
        degree = max(1, len(incidents[source_index]))
        for edge, neighbor_index in incidents[source_index]:
            port = _edge_features(edge)
            neighbor = node_features[neighbor_index]
            for port_key, port_value in port.items():
                _add(row, ("port",) + port_key, port_value / degree)
                for neighbor_key, neighbor_value in neighbor.items():
                    _add(row, ("neighbor-port",) + neighbor_key + port_key,
                         neighbor_value * port_value / degree)
                    if spec.interaction_order == 3:
                        for source_key, source_value in source.items():
                            _add(row, ("source-port-neighbor",) +
                                 source_key + port_key + neighbor_key,
                                 source_value * port_value * neighbor_value /
                                 degree)
        updated.append(row)
    pooled = {}
    _pool(pooled, ("node",), node_features)
    _pool(pooled, ("message",), updated)
    edge_rows = tuple(_edge_features(edge) for edge in graph.incidence_edges)
    _pool(pooled, ("global-port",), edge_rows)
    _add(pooled, ("isolated-fraction",),
         graph.isolated_nodes / max(1, len(graph.nodes)))
    return tuple(sorted(pooled.items(), key=lambda row: repr(row[0])))


def _sigmoid(value):
    if value >= 0:
        inverse = math.exp(-min(value, 60.))
        return 1 / (1 + inverse)
    exponent = math.exp(max(value, -60.))
    return exponent / (1 + exponent)


def _aggregated_pairwise_gradient(weights, vectors, paired_groups):
    """Exact pairwise-logistic gradient without pairwise sparse differences.

    For every positive/negative pair, ``d = x_pos - x_neg`` and the gradient
    contribution is ``(sigmoid(w·d) - 1) d``. The scalar coefficient can be
    accumulated once on each endpoint, after which one sparse pass over the
    examples produces the same gradient. This changes only floating-point
    summation order; it retains every pair and does not sample or approximate.
    """
    scores = tuple(sum(weights[index] * value for index, value in vector)
                   for vector in vectors)
    coefficients = [0.] * len(vectors)
    group_scale = 1 / len(paired_groups)
    for positive_indices, negative_indices in paired_groups:
        pair_scale = group_scale / (
            len(positive_indices) * len(negative_indices))
        for positive_index in positive_indices:
            positive_score = scores[positive_index]
            for negative_index in negative_indices:
                error = pair_scale * (
                    _sigmoid(positive_score - scores[negative_index]) - 1.)
                coefficients[positive_index] += error
                coefficients[negative_index] -= error
    gradient = [0.] * len(weights)
    for coefficient, vector in zip(coefficients, vectors):
        if not coefficient:
            continue
        for index, value in vector:
            gradient[index] += coefficient * value
    return gradient


def fit_learned_equivariant_port_value(
        examples: Sequence[LearnedEquivariantPortExample],
        spec: LearnedEquivariantPortSpec = LearnedEquivariantPortSpec(),
        ) -> FrozenLearnedEquivariantPortValue:
    rows = tuple(sorted(examples, key=lambda row: (
        repr(row.group), row.graph.canonical_digest, row.successful)))
    groups = {row.group for row in rows}
    positive = sum(row.successful for row in rows)
    if (not rows or len(groups) < 2 or positive in (0, len(rows))
            or spec.ridge <= 0 or spec.minimum_feature_groups < 1
            or spec.steps < 1 or spec.learning_rate <= 0
            or spec.objective not in (
                "classification", "pairwise", "pairwise-aggregated")
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid learned equivariant-port corpus")
    embeddings = tuple(dict(equivariant_port_interaction_embedding(
        row.graph, spec)) for row in rows)
    feature_groups = defaultdict(set)
    for row, embedding in zip(rows, embeddings):
        for key, value in embedding.items():
            if value:
                feature_groups[key].add(row.group)
    keys = tuple(sorted((key for key, support in feature_groups.items()
                         if len(support) >= spec.minimum_feature_groups),
                        key=repr))
    if not keys:
        raise ValueError("no recurrent equivariant message features")
    scales = tuple(max(1e-6, math.sqrt(sum(
        embedding.get(key, 0.) ** 2 for embedding in embeddings) /
        len(rows))) for key in keys)
    key_index = {key: index for index, key in enumerate(keys)}
    vectors = tuple(tuple((key_index[key], value / scales[key_index[key]])
                          for key, value in embedding.items()
                          if key in key_index and value)
                    for embedding in embeddings)
    weights = [0.] * len(keys)
    intercept = 0. if spec.objective == "pairwise" else math.log(
        (positive + .5) / (len(rows) - positive + .5))
    positive_weight = len(rows) / (2 * positive)
    negative_weight = len(rows) / (2 * (len(rows) - positive))
    inverse = 1 / len(rows)
    vector_maps = tuple(dict(vector) for vector in vectors)
    by_group = defaultdict(lambda: ([], []))
    for index, row in enumerate(rows):
        by_group[row.group][0 if row.successful else 1].append(index)
    paired_groups = tuple((positive_indices, negative_indices)
                          for positive_indices, negative_indices in
                          by_group.values()
                          if positive_indices and negative_indices)
    if spec.objective.startswith("pairwise") and len(paired_groups) < 2:
        raise ValueError("pairwise objective needs two contrasted groups")
    for step in range(spec.steps):
        gradient = [0.] * len(keys)
        intercept_gradient = 0.
        if spec.objective == "classification":
            for row, vector in zip(rows, vectors):
                score = intercept + sum(weights[index] * value
                                        for index, value in vector)
                sample_weight = positive_weight if row.successful else \
                    negative_weight
                error = sample_weight * (_sigmoid(score) - row.successful)
                intercept_gradient += error
                for index, value in vector:
                    gradient[index] += error * value
            gradient_scale = inverse
            intercept_scale = inverse
        elif spec.objective == "pairwise":
            group_scale = 1 / len(paired_groups)
            for positive_indices, negative_indices in paired_groups:
                pair_scale = group_scale / (
                    len(positive_indices) * len(negative_indices))
                for positive_index in positive_indices:
                    for negative_index in negative_indices:
                        first = vector_maps[positive_index]
                        second = vector_maps[negative_index]
                        difference = {index: first.get(index, 0.) -
                                      second.get(index, 0.)
                                      for index in set(first) | set(second)}
                        margin = sum(weights[index] * value
                                     for index, value in difference.items())
                        error = pair_scale * (_sigmoid(margin) - 1.)
                        for index, value in difference.items():
                            gradient[index] += error * value
            gradient_scale = 1.
            intercept_scale = 0.
        else:
            gradient = _aggregated_pairwise_gradient(
                weights, vectors, paired_groups)
            gradient_scale = 1.
            intercept_scale = 0.
        rate = spec.learning_rate / math.sqrt(1 + step / 40)
        intercept -= rate * intercept_gradient * intercept_scale
        for index in range(len(weights)):
            weights[index] -= rate * (
                gradient[index] * gradient_scale + spec.ridge * weights[index] *
                inverse)
    payload = (spec, keys, scales, tuple(weights), intercept,
               len(groups), len(rows), positive)
    return FrozenLearnedEquivariantPortValue(
        spec, keys, scales, tuple(weights), intercept, len(groups), len(rows),
        positive, hashlib.sha256(repr(payload).encode()).hexdigest())


def score_learned_equivariant_port_value(
        model: FrozenLearnedEquivariantPortValue,
        graph: PartialIrregularPortGraph) -> float:
    embedding = dict(equivariant_port_interaction_embedding(
        graph, model.spec))
    score = model.intercept + sum(
        weight * embedding.get(key, 0.) / scale
        for key, scale, weight in zip(
            model.feature_keys, model.scales, model.weights)
        if key in embedding)
    return _sigmoid(score)


def shuffle_equivariant_port_labels_within_groups(
        examples: Sequence[LearnedEquivariantPortExample], *, seed: int,
        ) -> tuple[LearnedEquivariantPortExample, ...]:
    rows = tuple(examples)
    by_group = defaultdict(list)
    for index, row in enumerate(rows):
        by_group[row.group].append(index)
    labels = [row.successful for row in rows]
    rng = random.Random(seed)
    for indices in by_group.values():
        shuffled = [labels[index] for index in indices]
        rng.shuffle(shuffled)
        for index, label in zip(indices, shuffled):
            labels[index] = label
    return tuple(LearnedEquivariantPortExample(
        row.group, row.graph, labels[index])
        for index, row in enumerate(rows))
