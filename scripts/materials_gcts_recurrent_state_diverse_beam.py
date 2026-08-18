#!/usr/bin/env python3
"""Bounded beam allocation across recurrent partial-branch state cells."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_recurrent_branch_value import (
    FrozenRecurrentBranchValue, branch_value_features,
    score_recurrent_branch)


@dataclass(frozen=True)
class RecurrentStateBeamSpec:
    state_bin_width: float
    quota_per_state: int
    beam_width: int


@dataclass(frozen=True)
class RecurrentStateBeamCandidate:
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    tie_key: Hashable
    payload: object = None


def recurrent_branch_state_code(
        head: FrozenRecurrentBranchValue,
        features: Sequence[float], action_colors: Sequence[str], *,
        state_bin_width: float) -> tuple[int, ...]:
    if state_bin_width <= 0:
        raise ValueError("state bin width must be positive")
    values = branch_value_features(features, action_colors, head.color_keys)
    if len(values) != len(head.means):
        raise ValueError("recurrent branch state schema mismatch")
    return tuple(round(((value - mean) / scale) / state_bin_width)
                 for value, mean, scale in
                 zip(values, head.means, head.scales))


def select_recurrent_state_diverse_beam(
        head: FrozenRecurrentBranchValue,
        candidates: Sequence[RecurrentStateBeamCandidate],
        spec: RecurrentStateBeamSpec,
        ) -> tuple[RecurrentStateBeamCandidate, ...]:
    """Rank exact candidates, then allocate a finite quota per state cell."""
    rows = tuple(candidates)
    if (not rows or spec.state_bin_width <= 0 or
            spec.quota_per_state < 1 or spec.beam_width < 1 or
            len({row.tie_key for row in rows}) != len(rows)):
        raise ValueError("invalid recurrent state beam candidates")
    cells = defaultdict(list)
    for row in rows:
        code = recurrent_branch_state_code(
            head, row.features, row.action_colors,
            state_bin_width=spec.state_bin_width)
        score = score_recurrent_branch(
            head, row.features, row.action_colors)
        cells[code].append((score, row))
    for cell in cells.values():
        cell.sort(key=lambda item: (-item[0], repr(item[1].tie_key)))
    ordered = tuple(sorted(cells.values(), key=lambda cell: (
        -cell[0][0], repr(cell[0][1].tie_key))))
    selected = []
    for rank in range(spec.quota_per_state):
        selected.extend(cell[rank] for cell in ordered if rank < len(cell))
    return tuple(row for _score, row in selected[:spec.beam_width])
