#!/usr/bin/env python3
"""Depth-conditioned recurrent values for partial GCTS branches.

Every head sees the same invariant feature schema and order-independent action
color population.  Capacity is selected independently per depth while leaving
out every example from the held-out spatial group.  Exact candidate geometry
and the tree scheduler remain outside this ranking model.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_recurrent_branch_value import (
    FrozenRecurrentBranchValue, RecurrentBranchExample, _fit,
    score_recurrent_branch)


@dataclass(frozen=True)
class DepthBranchExample:
    group: Hashable
    depth: int
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    successful: bool


@dataclass(frozen=True)
class DepthBranchCapacityAudit:
    depth: int
    neighbors: int
    supplied_groups: int
    selected_exact_groups: int
    first_exact_rank_sum: int
    first_exact_ranks: tuple[int | None, ...]


@dataclass(frozen=True)
class FrozenDepthBranchValues:
    feature_names: tuple[str, ...]
    color_keys: tuple[str, ...]
    heads: tuple[tuple[int, FrozenRecurrentBranchValue], ...]
    target_used: bool = False


@dataclass(frozen=True)
class DepthBranchValuesAudit:
    groups: int
    depths: tuple[int, ...]
    examples: int
    positive_examples: int
    capacities: tuple[DepthBranchCapacityAudit, ...]
    selected_neighbors_by_depth: tuple[tuple[int, int], ...]
    supplied_stages: int
    selected_exact_stages: int
    selected_precision: float
    model_digest: str
    target_used_for_fit_or_capacity_selection: bool


def depth_branch_values_digest(model: FrozenDepthBranchValues) -> str:
    return hashlib.sha256(repr(model).encode()).hexdigest()


def score_depth_branch(model: FrozenDepthBranchValues, depth: int,
                       features: Sequence[float],
                       action_colors: Sequence[str]) -> float:
    heads = dict(model.heads)
    if int(depth) not in heads:
        raise ValueError("untrained recurrent branch depth")
    return score_recurrent_branch(
        heads[int(depth)], features, action_colors)


def fit_grouped_depth_branch_values(
        examples: Sequence[DepthBranchExample], *,
        feature_names: Sequence[str], color_keys: Sequence[str],
        candidate_neighbors=(1, 3, 5, 9, 15, 25), beta_prior=.5,
        ) -> tuple[FrozenDepthBranchValues, DepthBranchValuesAudit]:
    rows = tuple(examples)
    names = tuple(feature_names)
    colors = tuple(color_keys)
    neighbors = tuple(sorted(set(map(int, candidate_neighbors))))
    if (not rows or not names or not colors or not neighbors or
            neighbors[0] < 1 or beta_prior <= 0):
        raise ValueError("invalid depth-conditioned branch corpus")
    groups = tuple(sorted({row.group for row in rows}, key=repr))
    depths = tuple(sorted({int(row.depth) for row in rows}))
    if len(groups) < 3 or depths[0] < 1:
        raise ValueError("insufficient grouped depth evidence")
    for row in rows:
        if (row.depth not in depths or len(row.features) != len(names) or
                len(row.action_colors) != row.depth or
                any(color not in colors for color in row.action_colors)):
            raise ValueError("invalid partial branch example")
    capacities = []
    selected_rows = []
    heads = []
    supplied_total = selected_total = 0
    for depth in depths:
        depth_rows = tuple(row for row in rows if row.depth == depth)
        audits = []
        for neighbor_count in neighbors:
            supplied = selected = rank_sum = 0
            ranks = []
            for heldout in groups:
                training = tuple(RecurrentBranchExample(
                    row.group, row.features, row.action_colors, row.successful)
                    for row in depth_rows if row.group != heldout)
                held = tuple(row for row in depth_rows if row.group == heldout)
                if not training or not held:
                    ranks.append(None)
                    continue
                head = _fit(training, names, colors,
                            neighbor_count, beta_prior)
                scores = tuple(score_recurrent_branch(
                    head, row.features, row.action_colors) for row in held)
                if not any(row.successful for row in held):
                    ranks.append(None)
                    continue
                supplied += 1
                best_exact_score = max(
                    score for score, row in zip(scores, held)
                    if row.successful)
                rank = 1 + sum(
                    score > best_exact_score + 1e-15 for score in scores)
                ranks.append(rank)
                rank_sum += rank
                top_score = max(scores)
                top_tie = tuple(row for score, row in zip(scores, held)
                                if abs(score - top_score) <= 1e-15)
                # A descriptor-only model cannot choose within an exact score
                # tie.  Count top-one success only when the complete tie is
                # exact; fixture or candidate insertion order is irrelevant.
                selected += int(all(row.successful for row in top_tie))
            audits.append(DepthBranchCapacityAudit(
                depth, neighbor_count, supplied, selected, rank_sum,
                tuple(ranks)))
        chosen = min(audits, key=lambda row: (
            -row.selected_exact_groups, row.first_exact_rank_sum,
            row.neighbors))
        training = tuple(RecurrentBranchExample(
            row.group, row.features, row.action_colors, row.successful)
            for row in depth_rows)
        heads.append((depth, _fit(
            training, names, colors, chosen.neighbors, beta_prior)))
        capacities.extend(audits)
        selected_rows.append((depth, chosen.neighbors))
        supplied_total += chosen.supplied_groups
        selected_total += chosen.selected_exact_groups
    model = FrozenDepthBranchValues(names, colors, tuple(heads))
    audit = DepthBranchValuesAudit(
        len(groups), depths, len(rows), sum(row.successful for row in rows),
        tuple(capacities), tuple(selected_rows), supplied_total, selected_total,
        selected_total / max(1, supplied_total),
        depth_branch_values_digest(model), False)
    return model, audit
