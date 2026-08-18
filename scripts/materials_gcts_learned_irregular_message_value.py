#!/usr/bin/env python3
"""Group-sealed learned readout for irregular-port message embeddings."""

from __future__ import annotations

import hashlib
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_partial_irregular_message_passing import (
    Embedding, FeatureKey, PartialMessagePassingSpec,
    partial_message_passing_embedding)
from materials_gcts_partial_irregular_port_graph import \
    PartialIrregularPortGraph


@dataclass(frozen=True)
class LearnedIrregularMessageExample:
    group: Hashable
    graph: PartialIrregularPortGraph
    successful: bool


@dataclass(frozen=True)
class LearnedIrregularMessageSpec:
    depth: int = 1
    support_type_weight: float = .25
    ridge: float = 1.
    minimum_feature_groups: int = 2
    steps: int = 240
    learning_rate: float = .18


@dataclass(frozen=True)
class FrozenLearnedIrregularMessageValue:
    spec: LearnedIrregularMessageSpec
    feature_keys: tuple[FeatureKey, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    training_groups: int
    training_examples: int
    positive_examples: int
    model_digest: str
    target_used: bool = False


def _sigmoid(value: float) -> float:
    if value >= 0:
        inverse = math.exp(-min(value, 60.))
        return 1 / (1 + inverse)
    exponent = math.exp(max(value, -60.))
    return exponent / (1 + exponent)


def _embedding_spec(spec: LearnedIrregularMessageSpec):
    return PartialMessagePassingSpec(
        neighbors=1, depth=spec.depth,
        support_type_weight=spec.support_type_weight,
        message_weight=1., beta_prior=.5)


def _embedding_dict(graph, spec) -> dict[FeatureKey, float]:
    return dict(partial_message_passing_embedding(
        graph, _embedding_spec(spec)))


def fit_learned_irregular_message_value(
        examples: Sequence[LearnedIrregularMessageExample],
        spec: LearnedIrregularMessageSpec = LearnedIrregularMessageSpec(),
        ) -> FrozenLearnedIrregularMessageValue:
    rows = tuple(sorted(examples, key=lambda row: (
        repr(row.group), row.graph.canonical_digest, row.successful)))
    groups = {row.group for row in rows}
    positive = sum(row.successful for row in rows)
    if (not rows or len(groups) < 2 or positive in (0, len(rows))
            or spec.depth not in (1, 2) or spec.support_type_weight < 0
            or spec.ridge <= 0 or spec.minimum_feature_groups < 1
            or spec.steps < 1 or spec.learning_rate <= 0
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid learned irregular-message corpus")
    embeddings = tuple(_embedding_dict(row.graph, spec) for row in rows)
    feature_groups = defaultdict(set)
    for row, embedding in zip(rows, embeddings):
        for key, value in embedding.items():
            if value:
                feature_groups[key].add(row.group)
    keys = tuple(sorted((key for key, support in feature_groups.items()
                         if len(support) >= spec.minimum_feature_groups),
                        key=repr))
    if not keys:
        raise ValueError("no recurrent message features")
    # RMS scaling keeps absent features exactly zero.  This is both a natural
    # sparse graph-feature convention and avoids turning every missing typed
    # port into a dense negative entry merely by centering it.
    means = tuple(0. for _key in keys)
    scales = tuple(max(1e-6, math.sqrt(sum(
        embedding.get(key, 0.) ** 2 for embedding in embeddings) /
        len(rows))) for key in keys)
    key_index = {key: index for index, key in enumerate(keys)}
    vectors = tuple(tuple((key_index[key], value / scales[key_index[key]])
                          for key, value in embedding.items()
                          if key in key_index and value)
                    for embedding in embeddings)
    weights = [0.] * len(keys)
    intercept = math.log((positive + .5) / (len(rows) - positive + .5))
    positive_weight = len(rows) / (2 * positive)
    negative_weight = len(rows) / (2 * (len(rows) - positive))
    inverse = 1 / len(rows)
    for step in range(spec.steps):
        gradient = [0.] * len(keys)
        intercept_gradient = 0.
        for row, vector in zip(rows, vectors):
            score = intercept + sum(weights[index] * value
                                    for index, value in vector)
            sample_weight = positive_weight if row.successful else \
                negative_weight
            error = sample_weight * (_sigmoid(score) - row.successful)
            intercept_gradient += error
            for index, value in vector:
                gradient[index] += error * value
        rate = spec.learning_rate / math.sqrt(1 + step / 40)
        intercept -= rate * intercept_gradient * inverse
        for index in range(len(weights)):
            weights[index] -= rate * (
                gradient[index] * inverse + spec.ridge * weights[index] *
                inverse)
    payload = (spec, keys, means, scales, tuple(weights), intercept,
               len(groups), len(rows), positive)
    return FrozenLearnedIrregularMessageValue(
        spec, keys, means, scales, tuple(weights), intercept,
        len(groups), len(rows), positive,
        hashlib.sha256(repr(payload).encode()).hexdigest())


def score_learned_irregular_message_value(
        model: FrozenLearnedIrregularMessageValue,
        graph: PartialIrregularPortGraph,
        ) -> float:
    if graph.target_used:
        raise ValueError("target-tainted graph cannot be scored")
    embedding = _embedding_dict(graph, model.spec)
    score = model.intercept + sum(
        weight * embedding.get(key, 0.) / scale
        for key, scale, weight in zip(
            model.feature_keys, model.scales, model.weights)
        if key in embedding)
    return _sigmoid(score)


def shuffle_irregular_message_labels_within_groups(
        examples: Sequence[LearnedIrregularMessageExample], *, seed: int,
        ) -> tuple[LearnedIrregularMessageExample, ...]:
    rows = tuple(examples)
    by_group = defaultdict(list)
    for index, row in enumerate(rows):
        by_group[row.group].append(index)
    rng = random.Random(seed)
    labels = [row.successful for row in rows]
    for indices in by_group.values():
        shuffled = [labels[index] for index in indices]
        rng.shuffle(shuffled)
        for index, label in zip(indices, shuffled):
            labels[index] = label
    return tuple(LearnedIrregularMessageExample(
        row.group, row.graph, labels[index]) for index, row in
        enumerate(rows))
