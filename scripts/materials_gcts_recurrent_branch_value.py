#!/usr/bin/env python3
"""Bounded nearest-recurrent value for complete GCTS search branches.

The value model sees only a frozen vector of local, proper-SE(3)-invariant
branch measurements and an order-independent histogram of the action colors.
It never receives coordinates, candidate/type identifiers, a material label,
or target sites.  Model capacity is selected by leaving out whole spatial
training groups.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass(frozen=True)
class RecurrentBranchExample:
    group: Hashable
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    successful: bool


@dataclass(frozen=True)
class FrozenRecurrentBranchValue:
    feature_names: tuple[str, ...]
    color_keys: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    normalized_examples: tuple[tuple[tuple[float, ...], bool], ...]
    neighbors: int
    beta_prior: float
    target_used: bool = False


@dataclass(frozen=True)
class RecurrentBranchCapacityAudit:
    neighbors: int
    supplied_groups: int
    selected_exact_groups: int
    first_exact_rank_sum: int
    first_exact_ranks: tuple[int | None, ...]


@dataclass(frozen=True)
class RecurrentBranchValueAudit:
    groups: int
    examples: int
    positive_examples: int
    feature_names: tuple[str, ...]
    color_keys: tuple[str, ...]
    capacities: tuple[RecurrentBranchCapacityAudit, ...]
    selected_neighbors: int
    supplied_groups: int
    selected_exact_groups: int
    selected_precision: float
    model_digest: str
    target_used_for_fit_or_capacity_selection: bool


def _validate(examples, feature_names, color_keys, candidate_neighbors,
              beta_prior):
    examples = tuple(sorted(examples, key=lambda row: (
        repr(row.group), tuple(row.features), tuple(row.action_colors),
        bool(row.successful))))
    names = tuple(feature_names)
    colors = tuple(color_keys)
    candidates = tuple(sorted(set(map(int, candidate_neighbors))))
    if (not examples or not names or len(set(names)) != len(names) or
            not colors or tuple(sorted(set(colors))) != colors or
            not candidates or candidates[0] < 1 or beta_prior <= 0 or
            len({row.group for row in examples}) < 3 or
            not any(row.successful for row in examples) or
            all(row.successful for row in examples)):
        raise ValueError("invalid recurrent branch training corpus")
    for row in examples:
        if (len(row.features) != len(names) or not row.action_colors or
                any(color not in colors for color in row.action_colors) or
                any(not math.isfinite(value) for value in row.features)):
            raise ValueError("invalid recurrent branch example")
    return examples, names, colors, candidates


def branch_value_features(features: Sequence[float],
                          action_colors: Sequence[str],
                          color_keys: Sequence[str]) -> tuple[float, ...]:
    """Append the order-independent action-color population."""
    features = tuple(map(float, features))
    actions = tuple(map(str, action_colors))
    colors = tuple(map(str, color_keys))
    if (not features or not actions or not colors or
            any(color not in colors for color in actions) or
            any(not math.isfinite(value) for value in features)):
        raise ValueError("invalid recurrent branch feature payload")
    return features + tuple(float(actions.count(color)) for color in colors)


def _fit(examples, feature_names, color_keys, neighbors, beta_prior):
    rows = tuple((branch_value_features(
        row.features, row.action_colors, color_keys), bool(row.successful))
                 for row in examples)
    width = len(rows[0][0])
    names = tuple(feature_names) + tuple(
        f"action_population:{color}" for color in color_keys)
    means = tuple(sum(row[0][index] for row in rows) / len(rows)
                  for index in range(width))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (row[0][index] - means[index]) ** 2 for row in rows) / len(rows)))
        for index in range(width))
    normalized = tuple(sorted((tuple(
        (value - mean) / scale for value, mean, scale in
        zip(features, means, scales)), label) for features, label in rows))
    return FrozenRecurrentBranchValue(
        names, tuple(color_keys), means, scales, normalized,
        int(neighbors), float(beta_prior))


def score_recurrent_branch(model: FrozenRecurrentBranchValue,
                           features: Sequence[float],
                           action_colors: Sequence[str]) -> float:
    values = branch_value_features(features, action_colors, model.color_keys)
    if len(values) != len(model.means):
        raise ValueError("recurrent branch feature schema mismatch")
    normalized = tuple((value - mean) / scale for value, mean, scale in
                       zip(values, model.means, model.scales))
    nearest = tuple(sorted((sum((left - right) ** 2 for left, right in
        zip(normalized, row)), label) for row, label in
        model.normalized_examples)[:min(
            model.neighbors, len(model.normalized_examples))])
    weighted_positive = sum(float(label) / (1. + distance)
                            for distance, label in nearest)
    total_weight = sum(1. / (1. + distance) for distance, _label in nearest)
    return (weighted_positive + model.beta_prior) / (
        total_weight + 2. * model.beta_prior)


def recurrent_branch_value_digest(model: FrozenRecurrentBranchValue) -> str:
    return hashlib.sha256(repr(model).encode()).hexdigest()


def fit_grouped_recurrent_branch_value(
        examples: Sequence[RecurrentBranchExample], *,
        feature_names: Sequence[str], color_keys: Sequence[str],
        candidate_neighbors=(1, 3, 5, 9, 15, 25), beta_prior=.5,
        ) -> tuple[FrozenRecurrentBranchValue, RecurrentBranchValueAudit]:
    examples, feature_names, color_keys, candidates = _validate(
        examples, feature_names, color_keys, candidate_neighbors, beta_prior)
    groups = tuple(sorted({row.group for row in examples}, key=repr))
    capacities = []
    for neighbors in candidates:
        ranks = []
        supplied = selected = rank_sum = 0
        for group in groups:
            training = tuple(row for row in examples if row.group != group)
            heldout = tuple(row for row in examples if row.group == group)
            model = _fit(training, feature_names, color_keys,
                         neighbors, beta_prior)
            scores = tuple(score_recurrent_branch(
                model, row.features, row.action_colors) for row in heldout)
            order = tuple(sorted(range(len(heldout)), key=lambda index: (
                -scores[index], branch_value_features(
                    heldout[index].features,
                    heldout[index].action_colors, color_keys))))
            if not any(row.successful for row in heldout):
                ranks.append(None)
                continue
            supplied += 1
            rank = next(rank for rank, index in enumerate(order, 1)
                        if heldout[index].successful)
            ranks.append(rank)
            rank_sum += rank
            selected += int(heldout[order[0]].successful)
        capacities.append(RecurrentBranchCapacityAudit(
            neighbors, supplied, selected, rank_sum, tuple(ranks)))
    selected = min(capacities, key=lambda row: (
        -row.selected_exact_groups, row.first_exact_rank_sum,
        row.neighbors))
    model = _fit(examples, feature_names, color_keys,
                 selected.neighbors, beta_prior)
    precision = selected.selected_exact_groups / max(1, selected.supplied_groups)
    audit = RecurrentBranchValueAudit(
        len(groups), len(examples), sum(row.successful for row in examples),
        tuple(feature_names), tuple(color_keys), tuple(capacities),
        selected.neighbors, selected.supplied_groups,
        selected.selected_exact_groups, precision,
        recurrent_branch_value_digest(model), False)
    return model, audit
