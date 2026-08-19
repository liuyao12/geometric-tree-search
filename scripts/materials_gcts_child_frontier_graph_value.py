#!/usr/bin/env python3
"""Pairwise group-balanced value on canonical child-frontier graphs."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_child_frontier_graph import (
    ChildFrontierGraph, child_frontier_graph_embedding)
from materials_gcts_learned_equivariant_port_value import (
    _aggregated_pairwise_gradient)


@dataclass(frozen=True)
class ChildFrontierGraphExample:
    group: Hashable
    graph: ChildFrontierGraph
    successful: bool


@dataclass(frozen=True)
class ChildFrontierGraphUtilityExample:
    group: Hashable
    graph: ChildFrontierGraph
    utility_level: int


@dataclass(frozen=True)
class ChildFrontierGraphValueSpec:
    interaction_order: int = 2
    minimum_feature_groups: int = 2
    ridge: float = 10.
    steps: int = 100
    learning_rate: float = .16


@dataclass(frozen=True)
class FrozenChildFrontierGraphValue:
    spec: ChildFrontierGraphValueSpec
    feature_keys: tuple[Hashable, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: int
    training_examples: int
    positive_examples: int
    model_digest: str
    target_used: bool = False


@dataclass(frozen=True)
class FrozenChildFrontierGraphUtilityValue:
    spec: ChildFrontierGraphValueSpec
    feature_keys: tuple[Hashable, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: int
    training_examples: int
    maximum_utility: int
    mean_utility: float
    model_digest: str
    target_used: bool = False


def _sigmoid(value):
    if value >= 0:
        inverse = math.exp(-min(value, 60.))
        return 1 / (1 + inverse)
    exponent = math.exp(max(value, -60.))
    return exponent / (1 + exponent)


def fit_child_frontier_graph_value(
        examples: Sequence[ChildFrontierGraphExample],
        spec: ChildFrontierGraphValueSpec = ChildFrontierGraphValueSpec(),
        ) -> FrozenChildFrontierGraphValue:
    rows = tuple(sorted(examples, key=lambda row: (
        repr(row.group), row.graph.canonical_digest, row.successful)))
    groups = tuple(sorted({row.group for row in rows}, key=repr))
    positive = sum(row.successful for row in rows)
    if (not rows or len(groups) < 2 or positive in (0, len(rows))
            or spec.interaction_order not in (1, 2)
            or spec.minimum_feature_groups < 1 or spec.ridge <= 0
            or spec.steps < 1 or spec.learning_rate <= 0
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid child-frontier graph corpus")
    embeddings = tuple(dict(child_frontier_graph_embedding(
        row.graph, interaction_order=spec.interaction_order)) for row in rows)
    support = defaultdict(set)
    for row, embedding in zip(rows, embeddings):
        for key, value in embedding.items():
            if value:
                support[key].add(row.group)
    keys = tuple(sorted((key for key, seen in support.items()
                         if len(seen) >= spec.minimum_feature_groups),
                        key=repr))
    if not keys:
        raise ValueError("no recurrent child-frontier graph features")
    scales = tuple(max(1e-6, math.sqrt(sum(
        embedding.get(key, 0.) ** 2 for embedding in embeddings) / len(rows)))
        for key in keys)
    indices = {key: index for index, key in enumerate(keys)}
    vectors = tuple(tuple((indices[key], value / scales[indices[key]])
                          for key, value in embedding.items()
                          if key in indices and value)
                    for embedding in embeddings)
    by_group = defaultdict(lambda: ([], []))
    for index, row in enumerate(rows):
        by_group[row.group][0 if row.successful else 1].append(index)
    paired = tuple((positive_indices, negative_indices)
                   for positive_indices, negative_indices in by_group.values()
                   if positive_indices and negative_indices)
    if len(paired) < 2:
        raise ValueError("graph value needs two contrasted groups")
    weights = [0.] * len(keys)
    inverse = 1 / len(rows)
    for step in range(spec.steps):
        gradient = _aggregated_pairwise_gradient(weights, vectors, paired)
        rate = spec.learning_rate / math.sqrt(1 + step / 40)
        for index in range(len(weights)):
            weights[index] -= rate * (
                gradient[index] + spec.ridge * weights[index] * inverse)
    payload = (spec, keys, scales, tuple(weights), len(groups), len(rows),
               positive)
    return FrozenChildFrontierGraphValue(
        spec, keys, scales, tuple(weights), len(groups), len(rows), positive,
        hashlib.sha256(repr(payload).encode()).hexdigest())


def score_child_frontier_graph_value(
        model: FrozenChildFrontierGraphValue,
        graph: ChildFrontierGraph) -> float:
    if graph.target_used:
        raise ValueError("target-tainted child-frontier graph is forbidden")
    embedding = dict(child_frontier_graph_embedding(
        graph, interaction_order=model.spec.interaction_order))
    score = sum(weight * embedding.get(key, 0.) / scale
                for key, scale, weight in
                zip(model.feature_keys, model.scales, model.weights))
    return _sigmoid(score)


def _utility_pairwise_gradient(weights, vectors, grouped_rows):
    """Group-balanced ordinal gradient over every distinct utility pair."""
    scores = tuple(sum(weights[index] * value for index, value in vector)
                   for vector in vectors)
    coefficients = [0.] * len(vectors)
    group_scale = 1 / len(grouped_rows)
    for rows in grouped_rows:
        pairs = tuple((high_index, low_index, high_utility - low_utility)
                      for high_index, high_utility in rows
                      for low_index, low_utility in rows
                      if high_utility > low_utility)
        total_weight = sum(weight for _high, _low, weight in pairs)
        if not pairs or total_weight <= 0:
            continue
        for high_index, low_index, difference in pairs:
            error = group_scale * difference / total_weight * (
                _sigmoid(scores[high_index] - scores[low_index]) - 1.)
            coefficients[high_index] += error
            coefficients[low_index] -= error
    gradient = [0.] * len(weights)
    for coefficient, vector in zip(coefficients, vectors):
        for index, value in vector:
            gradient[index] += coefficient * value
    return gradient


def fit_child_frontier_graph_utility_value(
        examples: Sequence[ChildFrontierGraphUtilityExample],
        spec: ChildFrontierGraphValueSpec = ChildFrontierGraphValueSpec(),
        ) -> FrozenChildFrontierGraphUtilityValue:
    rows = tuple(sorted(examples, key=lambda row: (
        repr(row.group), row.graph.canonical_digest, row.utility_level)))
    groups = tuple(sorted({row.group for row in rows}, key=repr))
    if (not rows or len(groups) < 2
            or any(not isinstance(row.utility_level, int)
                   or row.utility_level < 0 or row.graph.target_used
                   for row in rows)
            or len({row.utility_level for row in rows}) < 2
            or spec.interaction_order not in (1, 2)
            or spec.minimum_feature_groups < 1 or spec.ridge <= 0
            or spec.steps < 1 or spec.learning_rate <= 0):
        raise ValueError("invalid child-frontier graph utility corpus")
    embeddings = tuple(dict(child_frontier_graph_embedding(
        row.graph, interaction_order=spec.interaction_order)) for row in rows)
    support = defaultdict(set)
    for row, embedding in zip(rows, embeddings):
        for key, value in embedding.items():
            if value:
                support[key].add(row.group)
    keys = tuple(sorted((key for key, seen in support.items()
                         if len(seen) >= spec.minimum_feature_groups),
                        key=repr))
    if not keys:
        raise ValueError("no recurrent child-frontier utility features")
    scales = tuple(max(1e-6, math.sqrt(sum(
        embedding.get(key, 0.) ** 2 for embedding in embeddings) / len(rows)))
        for key in keys)
    indices = {key: index for index, key in enumerate(keys)}
    vectors = tuple(tuple((indices[key], value / scales[indices[key]])
                          for key, value in embedding.items()
                          if key in indices and value)
                    for embedding in embeddings)
    grouped = tuple(group for group in (
        tuple((index, row.utility_level)
              for index, row in enumerate(rows) if row.group == key)
        for key in groups) if len({utility for _index, utility in group}) > 1)
    if len(grouped) < 2:
        raise ValueError("utility value needs two contrasted groups")
    weights = [0.] * len(keys)
    inverse = 1 / len(rows)
    for step in range(spec.steps):
        gradient = _utility_pairwise_gradient(weights, vectors, grouped)
        rate = spec.learning_rate / math.sqrt(1 + step / 40)
        for index in range(len(weights)):
            weights[index] -= rate * (
                gradient[index] + spec.ridge * weights[index] * inverse)
    maximum = max(row.utility_level for row in rows)
    mean = sum(row.utility_level for row in rows) / len(rows)
    payload = (spec, keys, scales, tuple(weights), len(groups), len(rows),
               maximum, mean)
    return FrozenChildFrontierGraphUtilityValue(
        spec, keys, scales, tuple(weights), len(groups), len(rows), maximum,
        mean, hashlib.sha256(repr(payload).encode()).hexdigest())


def score_child_frontier_graph_utility_value(
        model: FrozenChildFrontierGraphUtilityValue,
        graph: ChildFrontierGraph) -> float:
    if graph.target_used:
        raise ValueError("target-tainted child-frontier graph is forbidden")
    embedding = dict(child_frontier_graph_embedding(
        graph, interaction_order=model.spec.interaction_order))
    return sum(weight * embedding.get(key, 0.) / scale
               for key, scale, weight in
               zip(model.feature_keys, model.scales, model.weights))


__all__ = [
    "ChildFrontierGraphExample", "ChildFrontierGraphUtilityExample",
    "ChildFrontierGraphValueSpec",
    "FrozenChildFrontierGraphValue", "fit_child_frontier_graph_value",
    "FrozenChildFrontierGraphUtilityValue",
    "fit_child_frontier_graph_utility_value",
    "score_child_frontier_graph_utility_value",
    "score_child_frontier_graph_value"]
