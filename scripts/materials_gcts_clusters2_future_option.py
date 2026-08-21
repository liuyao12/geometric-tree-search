#!/usr/bin/env python3
"""Target-free option values for a bounded cluster-of-clusters tree.

A parent placement is not ranked only by its present local score.  Instead,
each frozen marking channel scores the *same* finite set of child terminals.
The parent receives the mean of its best ``top_k`` child values in that
channel.  Selection is channel-diverse: one parent is first offered by every
channel, then the remaining beam slots are filled by the mean option value.

The module deliberately knows nothing about atoms, materials, targets, or
correct actions.  Exact geometry and collision checks remain responsibilities
of the caller; this layer only ranks an immutable tree.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass(frozen=True)
class ChildOption:
    child_id: Hashable
    channel_scores: tuple[float, ...]


@dataclass(frozen=True)
class ParentOption:
    parent_id: Hashable
    children: tuple[ChildOption, ...]


@dataclass(frozen=True)
class FrozenFutureOptionSpec:
    channel_names: tuple[str, ...]
    top_k: int = 8
    beam_width: int = 4


@dataclass(frozen=True)
class ScoredParentOption:
    parent_id: Hashable
    channel_values: tuple[float, ...]
    mean_value: float
    best_child_ids: tuple[Hashable, ...]
    child_count: int


@dataclass(frozen=True)
class FutureOptionSelection:
    scored: tuple[ScoredParentOption, ...]
    selected_parent_ids: tuple[Hashable, ...]
    selected_by_channels: tuple[tuple[str, Hashable], ...]
    selected_child_ids_by_parent: tuple[
        tuple[Hashable, tuple[Hashable, ...]], ...]
    candidate_digest: str
    target_used: bool = False


def _stable(value: Hashable) -> str:
    return repr(value)


def _validate(parents: Sequence[ParentOption],
              spec: FrozenFutureOptionSpec):
    parents = tuple(parents)
    channels = tuple(spec.channel_names)
    if (not parents or not channels or len(set(channels)) != len(channels)
            or spec.top_k < 1 or spec.beam_width < 1):
        raise ValueError("invalid clusters-squared future-option input")
    parent_ids = tuple(parent.parent_id for parent in parents)
    if len(set(parent_ids)) != len(parent_ids):
        raise ValueError("duplicate parent option id")
    width = len(channels)
    for parent in parents:
        if not parent.children:
            raise ValueError("a parent option has no frozen children")
        child_ids = tuple(child.child_id for child in parent.children)
        if len(set(child_ids)) != len(child_ids):
            raise ValueError("duplicate child option id")
        for child in parent.children:
            if (len(child.channel_scores) != width or any(
                    not math.isfinite(value)
                    for value in child.channel_scores)):
                raise ValueError("invalid child marking scores")
    return tuple(sorted(parents, key=lambda row: _stable(row.parent_id)))


def score_future_options(parents: Sequence[ParentOption],
                         spec: FrozenFutureOptionSpec
                         ) -> tuple[ScoredParentOption, ...]:
    """Score immutable child sets without authorizing any new geometry."""
    parents = _validate(parents, spec)
    scored = []
    for parent in parents:
        values = []
        best = []
        for channel in range(len(spec.channel_names)):
            ordered = tuple(sorted(parent.children, key=lambda child: (
                -child.channel_scores[channel], _stable(child.child_id))))
            retained = ordered[:min(spec.top_k, len(ordered))]
            values.append(sum(child.channel_scores[channel]
                              for child in retained) / len(retained))
            best.append(ordered[0].child_id)
        scored.append(ScoredParentOption(
            parent.parent_id, tuple(values), sum(values) / len(values),
            tuple(best), len(parent.children)))
    return tuple(scored)


def select_future_options(parents: Sequence[ParentOption],
                          spec: FrozenFutureOptionSpec
                          ) -> FutureOptionSelection:
    """Return a deterministic channel-diverse parent beam.

    Every channel sees exactly the same parent and child identifiers.  Channel
    proposals are traversed round-robin until each channel has contributed one
    previously unseen parent or is exhausted.  Remaining capacity is filled by
    the mean option value.  No callback can inspect a target during ranking.
    """
    scored = score_future_options(parents, spec)
    limit = min(spec.beam_width, len(scored))
    selected = []
    contributors = []
    for channel, name in enumerate(spec.channel_names):
        if len(selected) >= limit:
            break
        order = sorted(scored, key=lambda row: (
            -row.channel_values[channel], _stable(row.parent_id)))
        winner = next((row for row in order
                       if row.parent_id not in selected), None)
        if winner is not None:
            selected.append(winner.parent_id)
            contributors.append((name, winner.parent_id))
    if len(selected) < limit:
        for row in sorted(scored, key=lambda item: (
                -item.mean_value, _stable(item.parent_id))):
            if row.parent_id not in selected:
                selected.append(row.parent_id)
            if len(selected) == limit:
                break
    canonical = tuple((row.parent_id, tuple(
        (child.child_id, child.channel_scores)
        for child in sorted(row.children, key=lambda child:
                             _stable(child.child_id))))
        for row in _validate(parents, spec))
    digest = hashlib.sha256(repr(canonical).encode()).hexdigest()
    parent_lookup = {parent.parent_id: parent
                     for parent in _validate(parents, spec)}
    child_portfolios = []
    for parent_id in selected:
        parent = parent_lookup[parent_id]
        retained = []
        for channel in range(len(spec.channel_names)):
            order = sorted(parent.children, key=lambda child: (
                -child.channel_scores[channel], _stable(child.child_id)))
            for child in order[:min(spec.top_k, len(order))]:
                if child.child_id not in retained:
                    retained.append(child.child_id)
        child_portfolios.append((parent_id, tuple(retained)))
    return FutureOptionSelection(
        scored, tuple(selected), tuple(contributors),
        tuple(child_portfolios), digest, False)
