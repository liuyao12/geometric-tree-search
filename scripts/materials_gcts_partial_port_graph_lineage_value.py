#!/usr/bin/env python3
"""Group-balanced value on a bounded sequence of irregular port graphs.

The geometry generator remains authoritative.  This module sees only the
canonical proper-SE(3)-invariant graph attached to each already-frozen stage
and learns a sparse value over node/port/message colors.  Stage order is
retained, while atom/action IDs and global coordinates never enter.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_learned_equivariant_port_value import (
    LearnedEquivariantPortSpec, _aggregated_pairwise_gradient,
    equivariant_port_interaction_embedding)
from materials_gcts_partial_irregular_port_graph import \
    PartialIrregularPortGraph


FeatureKey = tuple[Hashable, ...]
Embedding = tuple[tuple[FeatureKey, float], ...]


@dataclass(frozen=True)
class PartialPortGraphLineageExample:
    group: Hashable
    parent_group: Hashable
    graphs: tuple[PartialIrregularPortGraph, ...]
    successful: bool


@dataclass(frozen=True)
class PartialPortGraphLineageSpec:
    interaction_order: int = 3
    support_type_weight: float = .25
    ridge: float = 10.
    minimum_feature_groups: int = 2
    steps: int = 120
    learning_rate: float = .16
    parent_conditional: bool = False
    include_transitions: bool = True


@dataclass(frozen=True)
class FrozenPartialPortGraphLineageValue:
    spec: PartialPortGraphLineageSpec
    feature_keys: tuple[FeatureKey, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: int
    training_examples: int
    positive_examples: int
    model_digest: str
    target_used: bool = False


def _stage_code(graph: PartialIrregularPortGraph):
    """Finite ID-free-enough transition color; no digest or occurrence ID."""
    node_histogram = tuple(sorted(Counter(
        (node.support_type_id, node.action_species, node.matched_atoms,
         node.prototype_atoms, node.training_group_support)
        for node in graph.nodes).items(), key=repr))
    port_histogram = tuple(sorted(Counter(
        (edge.shared_species, edge.separation_bin,
         edge.shared_distance_profiles, edge.chirality,
         edge.connection_witnessed)
        for edge in graph.incidence_edges).items(), key=repr))
    return node_histogram, port_histogram, graph.isolated_nodes


def partial_port_graph_lineage_embedding(
        graphs: Sequence[PartialIrregularPortGraph],
        spec: PartialPortGraphLineageSpec = PartialPortGraphLineageSpec(),
        ) -> Embedding:
    rows = tuple(graphs)
    if (not rows or len(rows) > 8 or spec.interaction_order not in (2, 3)
            or spec.support_type_weight < 0
            or any(graph.target_used for graph in rows)):
        raise ValueError("invalid partial port-graph lineage")
    base_spec = LearnedEquivariantPortSpec(
        interaction_order=spec.interaction_order,
        support_type_weight=spec.support_type_weight)
    features = Counter()
    stage_codes = []
    for stage, graph in enumerate(rows):
        for key, value in equivariant_port_interaction_embedding(
                graph, base_spec):
            features[("stage", stage) + key] += value
        stage_codes.append(_stage_code(graph))
    if spec.include_transitions:
        for stage, (left, right) in enumerate(zip(
                stage_codes, stage_codes[1:])):
            # The exact finite transition is useful when recurrent across
            # nuclei.  Coarser marginal colors let unseen combinations back
            # off without erasing support/port semantics.
            features[("transition", stage, left, right)] += 1.
            features[("transition-node", stage, left[0], right[0])] += 1.
            features[("transition-port", stage, left[1], right[1])] += 1.
            features[("transition-isolation", stage, left[2], right[2])] += 1.
    return tuple(sorted(((key, float(value))
                         for key, value in features.items() if value),
                        key=lambda row: repr(row[0])))


def _cached_embedding(graphs, spec, cache):
    key = spec, tuple(graph.canonical_digest for graph in graphs)
    if cache is not None and key in cache:
        return cache[key]
    value = partial_port_graph_lineage_embedding(graphs, spec)
    if cache is not None:
        cache[key] = value
    return value


def fit_partial_port_graph_lineage_value(
        examples: Sequence[PartialPortGraphLineageExample],
        spec: PartialPortGraphLineageSpec = PartialPortGraphLineageSpec(),
        *, embedding_cache: dict | None = None,
        ) -> FrozenPartialPortGraphLineageValue:
    rows = tuple(sorted(examples, key=lambda row: (
        repr(row.group), repr(row.parent_group),
        tuple(graph.canonical_digest for graph in row.graphs),
        row.successful)))
    groups = tuple(sorted({row.group for row in rows}, key=repr))
    positive = sum(row.successful for row in rows)
    if (not rows or len(groups) < 2 or positive in (0, len(rows))
            or spec.minimum_feature_groups < 1 or spec.ridge <= 0
            or spec.steps < 1 or spec.learning_rate <= 0
            or any(graph.target_used for row in rows for graph in row.graphs)):
        raise ValueError("invalid partial port-graph lineage corpus")
    embeddings = tuple(dict(_cached_embedding(
        row.graphs, spec, embedding_cache)) for row in rows)
    support = defaultdict(set)
    for row, embedding in zip(rows, embeddings):
        for key, value in embedding.items():
            if value:
                support[key].add(row.group)
    keys = tuple(sorted((key for key, seen in support.items()
                         if len(seen) >= spec.minimum_feature_groups),
                        key=repr))
    if not keys:
        raise ValueError("no recurrent lineage graph features")
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
    paired = tuple((positive_rows, negative_rows)
                   for positive_rows, negative_rows in strata.values()
                   if positive_rows and negative_rows)
    if len(paired) < 2:
        raise ValueError("lineage graph value needs two contrasted strata")
    weights = [0.] * len(keys)
    inverse = 1 / len(rows)
    try:
        import numpy as np
    except ImportError:  # The generic contract remains stdlib-executable.
        np = None
    if np is not None:
        matrix = np.zeros((len(rows), len(keys)), dtype=float)
        for row_index, vector in enumerate(vectors):
            for feature_index, value in vector:
                matrix[row_index, feature_index] = value
        weights_array = np.zeros(len(keys), dtype=float)
        for step in range(spec.steps):
            scores = matrix @ weights_array
            coefficients = np.zeros(len(rows), dtype=float)
            group_scale = 1 / len(paired)
            for positive_rows, negative_rows in paired:
                positive_index = np.asarray(positive_rows, dtype=int)
                negative_index = np.asarray(negative_rows, dtype=int)
                margins = (scores[positive_index, None] -
                           scores[None, negative_index])
                errors = 1 / (1 + np.exp(-np.clip(
                    margins, -60., 60.))) - 1.
                pair_scale = group_scale / errors.size
                coefficients[positive_index] += errors.sum(axis=1) * pair_scale
                coefficients[negative_index] -= errors.sum(axis=0) * pair_scale
            gradient = matrix.T @ coefficients
            rate = spec.learning_rate / math.sqrt(1 + step / 40)
            weights_array -= rate * (
                gradient + spec.ridge * weights_array * inverse)
        weights = list(map(float, weights_array))
    else:
        for step in range(spec.steps):
            gradient = _aggregated_pairwise_gradient(weights, vectors, paired)
            rate = spec.learning_rate / math.sqrt(1 + step / 40)
            for index in range(len(weights)):
                weights[index] -= rate * (
                    gradient[index] + spec.ridge * weights[index] * inverse)
    payload = (spec, keys, scales, tuple(weights), len(groups), len(rows),
               positive)
    return FrozenPartialPortGraphLineageValue(
        spec, keys, scales, tuple(weights), len(groups), len(rows), positive,
        hashlib.sha256(repr(payload).encode()).hexdigest())


def score_partial_port_graph_lineage_value(
        model: FrozenPartialPortGraphLineageValue,
        graphs: Sequence[PartialIrregularPortGraph], *,
        embedding_cache: dict | None = None) -> float:
    embedding = dict(_cached_embedding(tuple(graphs), model.spec,
                                       embedding_cache))
    return sum(weight * embedding.get(key, 0.) / scale
               for key, scale, weight in zip(
                   model.feature_keys, model.scales, model.weights))


__all__ = [
    "FrozenPartialPortGraphLineageValue", "PartialPortGraphLineageExample",
    "PartialPortGraphLineageSpec", "fit_partial_port_graph_lineage_value",
    "partial_port_graph_lineage_embedding",
    "score_partial_port_graph_lineage_value"]
