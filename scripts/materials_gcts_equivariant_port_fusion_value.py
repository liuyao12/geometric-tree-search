#!/usr/bin/env python3
"""Group-sealed fusion of a scalar local section and an equivariant port graph.

The two values are converted to percentile ranks *within the same immutable
candidate set*.  The graph can therefore refine an established scalar value,
but it cannot create a candidate, alter its exact geometry, or import an
absolute score calibration from another nucleus.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_learned_equivariant_port_value import (
    FrozenLearnedEquivariantPortValue, LearnedEquivariantPortExample,
    LearnedEquivariantPortSpec, fit_learned_equivariant_port_value,
    score_learned_equivariant_port_value)
from materials_gcts_partial_irregular_port_graph import PartialIrregularPortGraph
from materials_gcts_portfolio_terminal_value import (
    FrozenPortfolioTerminalValue, PortfolioTerminalExample,
    TerminalRepresentation, portfolio_terminal_value_digest,
    score_portfolio_terminal)
from materials_gcts_recurrent_branch_value import _fit


@dataclass(frozen=True)
class EquivariantPortFusionExample:
    group: Hashable
    scalar_features: tuple[float, ...]
    action_colors: tuple[str, ...]
    graph: PartialIrregularPortGraph
    successful: bool


@dataclass(frozen=True)
class EquivariantPortFusionCandidate:
    scalar_features: tuple[float, ...]
    action_colors: tuple[str, ...]
    graph: PartialIrregularPortGraph
    tie_key: Hashable


@dataclass(frozen=True)
class EquivariantPortFusionSpec:
    graph: LearnedEquivariantPortSpec = LearnedEquivariantPortSpec(
        interaction_order=3, support_type_weight=.25, ridge=10.,
        minimum_feature_groups=2, steps=100, learning_rate=.16,
        objective="pairwise")
    neighbors: tuple[int, ...] = (1, 3, 5, 9, 15, 25)
    graph_rank_weights: tuple[float, ...] = (0., .125, .25, .5, 1., 2.)
    beta_prior: float = .5


@dataclass(frozen=True)
class EquivariantPortFusionCapacity:
    representation: str
    neighbors: int
    graph_rank_weight: float
    supplied_groups: int
    selected_exact_groups: int
    first_exact_rank_sum: int


@dataclass(frozen=True)
class FrozenEquivariantPortFusionValue:
    scalar: FrozenPortfolioTerminalValue
    graph: FrozenLearnedEquivariantPortValue
    graph_rank_weight: float
    feature_names: tuple[str, ...]
    color_keys: tuple[str, ...]
    training_groups: int
    model_digest: str
    target_used: bool = False


@dataclass(frozen=True)
class EquivariantPortFusionAudit:
    groups: int
    examples: int
    positive_examples: int
    capacities: tuple[EquivariantPortFusionCapacity, ...]
    selected_representation: str
    selected_neighbors: int
    selected_graph_rank_weight: float
    selected_exact_groups: int
    supplied_groups: int
    first_exact_rank_sum: int
    model_digest: str
    candidate_geometry_unchanged: bool
    target_used: bool


@dataclass(frozen=True)
class EquivariantPortFusionSelection:
    top_indices: tuple[int, ...]
    stable_index: int
    scalar_percentile_ranks: tuple[float, ...]
    graph_percentile_ranks: tuple[float, ...]
    fused_scores: tuple[float, ...]


def percentile_ranks(values: Sequence[float]) -> tuple[float, ...]:
    """Return deterministic weak percentile ranks in [0,1]."""
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("cannot rank an empty candidate set")
    if len(rows) == 1:
        return (0.,)
    denominator = len(rows) - 1
    return tuple(sum(other < value - 1e-15 for other in rows) / denominator
                 for value in rows)


def _fit_scalar(examples, representation, neighbors, feature_names,
                color_keys, beta_prior):
    projected = tuple(PortfolioTerminalExample(
        row.group,
        tuple(row.scalar_features[index]
              for index in representation.feature_indices),
        row.action_colors, row.successful) for row in examples)
    names = tuple(feature_names[index]
                  for index in representation.feature_indices)
    return FrozenPortfolioTerminalValue(
        representation,
        _fit(projected, names, color_keys, neighbors, beta_prior))


def _scores(scalar_model, graph_model, graph_rank_weight, rows):
    scalar = percentile_ranks(tuple(score_portfolio_terminal(
        scalar_model, row.scalar_features, row.action_colors) for row in rows))
    graph = percentile_ranks(tuple(score_learned_equivariant_port_value(
        graph_model, row.graph) for row in rows))
    fused = tuple(first + graph_rank_weight * second
                  for first, second in zip(scalar, graph))
    return scalar, graph, fused


def _graph_cache_key(rows, graph_spec):
    corpus = tuple(sorted((
        repr(row.group), row.graph.canonical_digest, bool(row.successful))
        for row in rows))
    return graph_spec, corpus


def _fit_graph(rows, graph_spec, cache):
    key = _graph_cache_key(rows, graph_spec)
    if cache is not None and key in cache:
        return cache[key]
    model = fit_learned_equivariant_port_value(tuple(
        LearnedEquivariantPortExample(
            row.group, row.graph, row.successful) for row in rows), graph_spec)
    if cache is not None:
        cache[key] = model
    return model


def _capacity_result(rows, scores):
    successful_scores = tuple(score for score, row in zip(scores, rows)
                              if row.successful)
    if not successful_scores:
        return 0, 0, 0
    best = max(successful_scores)
    rank = 1 + sum(score > best + 1e-15 for score in scores)
    top = max(scores)
    selected = tuple(row for score, row in zip(scores, rows)
                     if abs(score - top) <= 1e-15)
    return 1, int(all(row.successful for row in selected)), rank


def fit_grouped_equivariant_port_fusion(
        examples: Sequence[EquivariantPortFusionExample], *,
        feature_names: Sequence[str], color_keys: Sequence[str],
        representations: Sequence[TerminalRepresentation],
        spec: EquivariantPortFusionSpec = EquivariantPortFusionSpec(),
        graph_model_cache: dict | None = None,
        ) -> tuple[FrozenEquivariantPortFusionValue,
                   EquivariantPortFusionAudit]:
    rows = tuple(sorted(examples, key=lambda row: (
        repr(row.group), row.graph.canonical_digest, row.scalar_features,
        row.action_colors, row.successful)))
    names = tuple(feature_names)
    colors = tuple(color_keys)
    variants = tuple(representations)
    groups = tuple(sorted({row.group for row in rows}, key=repr))
    neighbors = tuple(sorted(set(map(int, spec.neighbors))))
    alphas = tuple(sorted(set(map(float, spec.graph_rank_weights))))
    if (not rows or len(groups) < 3 or not names or not colors or not variants
            or not neighbors or neighbors[0] < 1 or not alphas
            or alphas[0] < 0 or spec.beta_prior <= 0
            or any(row.graph.target_used for row in rows)
            or any(len(row.scalar_features) != len(names)
                   or not row.action_colors for row in rows)):
        raise ValueError("invalid equivariant-port fusion corpus")
    capacities = {(variant.name, count, alpha): [0, 0, 0]
                  for variant in variants for count in neighbors
                  for alpha in alphas}
    for heldout in groups:
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        if not any(row.successful for row in held):
            continue
        graph_model = _fit_graph(training, spec.graph, graph_model_cache)
        graph_scores = percentile_ranks(tuple(
            score_learned_equivariant_port_value(graph_model, row.graph)
            for row in held))
        for variant in variants:
            for count in neighbors:
                scalar_model = _fit_scalar(
                    training, variant, count, names, colors, spec.beta_prior)
                scalar_scores = percentile_ranks(tuple(
                    score_portfolio_terminal(
                        scalar_model, row.scalar_features, row.action_colors)
                    for row in held))
                for alpha in alphas:
                    fused = tuple(first + alpha * second
                                  for first, second in zip(
                                      scalar_scores, graph_scores))
                    supplied, selected, rank = _capacity_result(held, fused)
                    totals = capacities[(variant.name, count, alpha)]
                    totals[0] += supplied
                    totals[1] += selected
                    totals[2] += rank
    audits = tuple(EquivariantPortFusionCapacity(
        name, count, alpha, values[0], values[1], values[2])
        for (name, count, alpha), values in capacities.items())
    order = {row.name: index for index, row in enumerate(variants)}
    chosen = min(audits, key=lambda row: (
        -row.selected_exact_groups, row.first_exact_rank_sum,
        order[row.representation], row.neighbors, row.graph_rank_weight))
    representation = next(row for row in variants
                          if row.name == chosen.representation)
    scalar_model = _fit_scalar(
        rows, representation, chosen.neighbors, names, colors,
        spec.beta_prior)
    graph_model = _fit_graph(rows, spec.graph, graph_model_cache)
    digest = hashlib.sha256(repr((
        portfolio_terminal_value_digest(scalar_model), graph_model.model_digest,
        chosen.graph_rank_weight, names, colors, len(groups))).encode()).hexdigest()
    model = FrozenEquivariantPortFusionValue(
        scalar_model, graph_model, chosen.graph_rank_weight, names, colors,
        len(groups), digest)
    return model, EquivariantPortFusionAudit(
        len(groups), len(rows), sum(row.successful for row in rows), audits,
        chosen.representation, chosen.neighbors, chosen.graph_rank_weight,
        chosen.selected_exact_groups, chosen.supplied_groups,
        chosen.first_exact_rank_sum, digest, True, False)


def select_equivariant_port_fusion(
        model: FrozenEquivariantPortFusionValue,
        candidates: Sequence[EquivariantPortFusionCandidate],
        ) -> EquivariantPortFusionSelection:
    rows = tuple(candidates)
    if (not rows or len({repr(row.tie_key) for row in rows}) != len(rows)
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid equivariant-port fusion candidates")
    scalar, graph, fused = _scores(
        model.scalar, model.graph, model.graph_rank_weight, rows)
    top = max(fused)
    selected = tuple(index for index, score in enumerate(fused)
                     if abs(score - top) <= 1e-15)
    stable = min(selected, key=lambda index: repr(rows[index].tie_key))
    return EquivariantPortFusionSelection(
        selected, stable, scalar, graph, fused)
