#!/usr/bin/env python3
"""Fixed-width beam allocation across a frozen GCTS marking library."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_recurrent_branch_value import FrozenRecurrentBranchValue
from materials_gcts_recurrent_state_diverse_beam import (
    RecurrentStateBeamCandidate, RecurrentStateBeamSpec,
    select_recurrent_state_diverse_beam)


@dataclass(frozen=True)
class FrozenBranchMarking:
    name: str
    feature_indices: tuple[int, ...]
    value: FrozenRecurrentBranchValue


@dataclass(frozen=True)
class MarkingPortfolioCandidate:
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    tie_key: Hashable
    payload: object = None


def select_marking_portfolio_beam(
        markings: Sequence[FrozenBranchMarking],
        candidates: Sequence[MarkingPortfolioCandidate],
        spec: RecurrentStateBeamSpec,
        ) -> tuple[MarkingPortfolioCandidate, ...]:
    """Round-robin frozen marking beams under one common total budget."""
    library = tuple(markings)
    rows = tuple(candidates)
    if (not library or not rows or len({marking.name for marking in library}) !=
            len(library) or len({row.tie_key for row in rows}) != len(rows)):
        raise ValueError("invalid recurrent marking portfolio")
    width = len(rows[0].features)
    for marking in library:
        if (not marking.name or not marking.feature_indices or
                len(set(marking.feature_indices)) !=
                len(marking.feature_indices) or
                min(marking.feature_indices) < 0 or
                max(marking.feature_indices) >= width):
            raise ValueError("invalid marking feature projection")
    if any(len(row.features) != width for row in rows):
        raise ValueError("portfolio candidate schema mismatch")
    ranked = []
    for marking in library:
        projected = tuple(RecurrentStateBeamCandidate(
            tuple(row.features[index] for index in marking.feature_indices),
            row.action_colors, row.tie_key, row) for row in rows)
        ranked.append(select_recurrent_state_diverse_beam(
            marking.value, projected, spec))
    selected = []
    seen = set()
    rank = 0
    while len(selected) < spec.beam_width:
        changed = False
        for marking_rows in ranked:
            if rank < len(marking_rows):
                row = marking_rows[rank].payload
                if row.tie_key not in seen:
                    selected.append(row)
                    seen.add(row.tie_key)
                    changed = True
                    if len(selected) >= spec.beam_width:
                        break
        if not changed and all(rank >= len(marking_rows) - 1
                               for marking_rows in ranked):
            break
        rank += 1
    return tuple(selected)
