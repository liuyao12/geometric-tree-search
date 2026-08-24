#!/usr/bin/env python3
"""Grouped local marking for certified commuting IQC frontier batches."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from materials_gcts_equivariant_port_fusion_value import (
    fit_grouped_equivariant_port_fusion, select_equivariant_port_fusion)
from materials_gcts_iqc_frozen_fusion_runtime import action_key
from materials_gcts_portfolio_terminal_value import (
    FrozenPortfolioTerminalValue, TerminalRepresentation,
    portfolio_terminal_value_digest, score_portfolio_terminal)


@dataclass(frozen=True)
class FrozenCommutingClosureSelection:
    candidate_indices: tuple[int, ...]
    ranked_candidate_indices: tuple[int, ...]
    selected_indices: tuple[int, ...]
    candidate_digest: str
    model_digest: str
    candidate_geometry_unchanged: bool = True
    target_used: bool = False


@dataclass(frozen=True)
class FrozenScalarCommutingClosureMarking:
    scalar: FrozenPortfolioTerminalValue
    feature_names: tuple[str, ...]
    color_keys: tuple[str, ...]
    training_groups: int
    model_digest: str
    target_used: bool = False


def closure_representations(feature_names):
    names = tuple(map(str, feature_names))
    if len(names) < 32 or not all(name in names for name in (
            "depth", "partial-min-fraction", "partial-connected-action-pairs")):
        raise ValueError("unexpected commuting-closure feature schema")
    incidence = tuple(index for index, name in enumerate(names)
                      if name.startswith("partial-"))
    action = tuple(range(31))
    compact = tuple(sorted(set(action + incidence)))
    return (
        TerminalRepresentation("incidence", incidence),
        TerminalRepresentation("action-local", action),
        TerminalRepresentation("action-plus-incidence", compact),
        TerminalRepresentation("full", tuple(range(len(names)))),
    )


def fit_commuting_closure_marking(examples, *, feature_names, color_keys):
    return fit_grouped_equivariant_port_fusion(
        tuple(examples), feature_names=tuple(feature_names),
        color_keys=tuple(color_keys),
        representations=closure_representations(feature_names),
        graph_model_cache={})


def freeze_scalar_commuting_closure_marking(model):
    """Discard the graph head only when grouped selection assigned weight 0."""
    if model.target_used or abs(model.graph_rank_weight) > 1e-15:
        raise ValueError("fusion model is not exactly scalar-selected")
    digest = scalar_commuting_closure_marking_digest(
        model.scalar, model.feature_names, model.color_keys,
        model.training_groups)
    return FrozenScalarCommutingClosureMarking(
        model.scalar, tuple(model.feature_names), tuple(model.color_keys),
        int(model.training_groups), digest)


def scalar_commuting_closure_marking_digest(
        scalar, feature_names, color_keys, training_groups):
    return hashlib.sha256(repr((
        portfolio_terminal_value_digest(scalar), tuple(feature_names),
        tuple(color_keys), int(training_groups), 0.)).encode()).hexdigest()


def select_commuting_closure_marking(model, frontier, *, width=8):
    """Rank only certified closure states without altering their geometry."""
    if (not isinstance(width, int) or width < 1 or model.target_used or
            frontier.target_used or frontier.closure.target_used or
            len(frontier.states) != len(frontier.candidates)):
        raise ValueError("invalid frozen commuting-closure selection")
    closure_keys = {action_key(state.actions)
                    for state in frontier.closure.states}
    indices = tuple(index for index, state in enumerate(frontier.states)
                    if action_key(state.actions) in closure_keys)
    if not indices or len(indices) != len(closure_keys):
        raise ValueError("closure states are not an exact frontier subset")
    rows = tuple(frontier.candidates[index] for index in indices)
    if isinstance(model, FrozenScalarCommutingClosureMarking):
        scores = tuple(score_portfolio_terminal(
            model.scalar, row.scalar_features, row.action_colors)
            for row in rows)
    else:
        scores = select_equivariant_port_fusion(
            model, rows).fused_scores
    local_order = tuple(sorted(range(len(rows)), key=lambda offset: (
        -scores[offset], repr(rows[offset].tie_key))))
    order = tuple(indices[offset] for offset in local_order)
    selected = order[:min(width, len(order))]
    digest = hashlib.sha256(repr(tuple(
        action_key(frontier.states[index].actions)
        for index in indices)).encode()).hexdigest()
    return FrozenCommutingClosureSelection(
        indices, order, selected, digest, model.model_digest)


__all__ = [
    "FrozenCommutingClosureSelection",
    "FrozenScalarCommutingClosureMarking", "closure_representations",
    "fit_commuting_closure_marking",
    "freeze_scalar_commuting_closure_marking",
    "scalar_commuting_closure_marking_digest",
    "select_commuting_closure_marking"]
