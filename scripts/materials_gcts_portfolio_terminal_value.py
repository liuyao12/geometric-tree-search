#!/usr/bin/env python3
"""Group-heldout terminal value for a fixed-width GCTS marking portfolio."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_recurrent_branch_value import (
    FrozenRecurrentBranchValue, RecurrentBranchExample, _fit,
    recurrent_branch_value_digest, score_recurrent_branch)


@dataclass(frozen=True)
class PortfolioTerminalExample:
    group: Hashable
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    successful: bool


@dataclass(frozen=True)
class PortfolioTerminalCandidate:
    example: PortfolioTerminalExample
    tie_key: Hashable


@dataclass(frozen=True)
class TerminalRepresentation:
    name: str
    feature_indices: tuple[int, ...]


@dataclass(frozen=True)
class TerminalCapacityAudit:
    representation: str
    neighbors: int
    supplied_groups: int
    selected_exact_groups: int
    first_exact_rank_sum: int


@dataclass(frozen=True)
class FrozenPortfolioTerminalValue:
    representation: TerminalRepresentation
    value: FrozenRecurrentBranchValue
    target_used: bool = False


@dataclass(frozen=True)
class PortfolioTerminalValueAudit:
    groups: int
    examples: int
    positive_examples: int
    capacities: tuple[TerminalCapacityAudit, ...]
    selected_representation: str
    selected_neighbors: int
    selected_exact_groups: int
    supplied_groups: int
    model_digest: str
    target_used: bool


@dataclass(frozen=True)
class PortfolioTerminalSelection:
    top_indices: tuple[int, ...]
    stable_index: int
    certified_exact: bool | None
    mixed_top_tie: bool | None


def portfolio_terminal_value_digest(model: FrozenPortfolioTerminalValue) -> str:
    return hashlib.sha256(repr((
        model.representation,
        recurrent_branch_value_digest(model.value))).encode()).hexdigest()


def _project(row: PortfolioTerminalExample,
             representation: TerminalRepresentation) -> RecurrentBranchExample:
    return RecurrentBranchExample(
        row.group, tuple(row.features[index]
                         for index in representation.feature_indices),
        row.action_colors, row.successful)


def fit_grouped_portfolio_terminal_value(
        examples: Sequence[PortfolioTerminalExample], *,
        feature_names: Sequence[str], color_keys: Sequence[str],
        representations: Sequence[TerminalRepresentation],
        candidate_neighbors=(1, 3, 5, 9, 15, 25), beta_prior=.5,
        ) -> tuple[FrozenPortfolioTerminalValue, PortfolioTerminalValueAudit]:
    rows = tuple(examples)
    names = tuple(feature_names)
    colors = tuple(color_keys)
    variants = tuple(representations)
    neighbors = tuple(sorted(set(map(int, candidate_neighbors))))
    if (not rows or not names or not colors or not variants or not neighbors or
            neighbors[0] < 1 or beta_prior <= 0 or
            len({row.group for row in rows}) < 3 or
            len({variant.name for variant in variants}) != len(variants)):
        raise ValueError("invalid portfolio terminal corpus")
    for variant in variants:
        if (not variant.name or not variant.feature_indices or
                len(set(variant.feature_indices)) !=
                len(variant.feature_indices) or
                min(variant.feature_indices) < 0 or
                max(variant.feature_indices) >= len(names)):
            raise ValueError("invalid terminal representation")
    if any(len(row.features) != len(names) or not row.action_colors or
           any(color not in colors for color in row.action_colors)
           for row in rows):
        raise ValueError("terminal example schema mismatch")
    groups = tuple(sorted({row.group for row in rows}, key=repr))
    capacities = []
    for variant in variants:
        projected = tuple(_project(row, variant) for row in rows)
        variant_names = tuple(names[index] for index in variant.feature_indices)
        for count in neighbors:
            supplied = selected = rank_sum = 0
            for group in groups:
                training = tuple(row for row in projected if row.group != group)
                held = tuple(row for row in projected if row.group == group)
                model = _fit(training, variant_names, colors, count, beta_prior)
                scores = tuple(score_recurrent_branch(
                    model, row.features, row.action_colors) for row in held)
                if not any(row.successful for row in held):
                    continue
                supplied += 1
                best_exact = max(score for score, row in zip(scores, held)
                                 if row.successful)
                rank_sum += 1 + sum(score > best_exact + 1e-15
                                    for score in scores)
                top = max(scores)
                tie = tuple(row for score, row in zip(scores, held)
                            if abs(score - top) <= 1e-15)
                selected += int(all(row.successful for row in tie))
            capacities.append(TerminalCapacityAudit(
                variant.name, count, supplied, selected, rank_sum))
    representation_order = {row.name: index
                            for index, row in enumerate(variants)}
    chosen = min(capacities, key=lambda row: (
        -row.selected_exact_groups, row.first_exact_rank_sum,
        representation_order[row.representation], row.neighbors))
    representation = next(row for row in variants
                          if row.name == chosen.representation)
    projected = tuple(_project(row, representation) for row in rows)
    model = FrozenPortfolioTerminalValue(representation, _fit(
        projected, tuple(names[index]
                         for index in representation.feature_indices),
        colors, chosen.neighbors, beta_prior))
    audit = PortfolioTerminalValueAudit(
        groups=len(groups), examples=len(rows),
        positive_examples=sum(row.successful for row in rows),
        capacities=tuple(capacities),
        selected_representation=representation.name,
        selected_neighbors=chosen.neighbors,
        selected_exact_groups=chosen.selected_exact_groups,
        supplied_groups=chosen.supplied_groups,
        model_digest=portfolio_terminal_value_digest(model),
        target_used=False)
    return model, audit


def score_portfolio_terminal(
        model: FrozenPortfolioTerminalValue,
        features: Sequence[float], action_colors: Sequence[str]) -> float:
    projected = tuple(features[index]
                      for index in model.representation.feature_indices)
    return score_recurrent_branch(model.value, projected, action_colors)


def select_portfolio_terminal(
        model: FrozenPortfolioTerminalValue,
        candidates: Sequence[PortfolioTerminalCandidate],
        ) -> PortfolioTerminalSelection:
    rows = tuple(candidates)
    if (not rows or len({row.tie_key for row in rows}) != len(rows)):
        raise ValueError("invalid portfolio terminal set")
    scores = tuple(score_portfolio_terminal(
        model, row.example.features, row.example.action_colors) for row in rows)
    top = max(scores)
    indices = tuple(index for index, score in enumerate(scores)
                    if abs(score - top) <= 1e-15)
    # The executor supplies a target-free exact-geometry key for deterministic
    # replay; labels never participate in tie resolution.
    stable = min(indices, key=lambda index: repr(rows[index].tie_key))
    labels = {rows[index].example.successful for index in indices}
    return PortfolioTerminalSelection(
        top_indices=indices, stable_index=stable,
        certified_exact=(next(iter(labels)) if len(labels) == 1 else False),
        mixed_top_tie=len(labels) > 1)
