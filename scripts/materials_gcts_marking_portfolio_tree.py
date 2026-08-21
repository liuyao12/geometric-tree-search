#!/usr/bin/env python3
"""Generic target-free tree search over a frozen marking library.

Candidate geometry is enumerated exactly once per retained physical state.
Every marking scores that same immutable action set; a round-robin union of
the per-marking orders preserves alternatives without pretending that the
markings agree.  This is deliberately a search/supply layer.  It does not use
target atoms, declare one marking correct, or turn finite depth into a
stationary/exponential claim.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Any, Callable, Hashable, Iterable, Sequence


@dataclass(frozen=True)
class FrozenPortfolioAction:
    action_id: Hashable
    next_state: Any
    marking_scores: tuple[tuple[str, float], ...]
    marking_channels: tuple[tuple[str, Hashable], ...] = ()


@dataclass(frozen=True)
class MarkingPortfolioNode:
    state: Any
    state_key: Hashable
    action_path: tuple[Hashable, ...]
    cumulative_scores: tuple[tuple[str, float], ...]
    marking_channels: tuple[tuple[str, Hashable], ...]


@dataclass(frozen=True)
class MarkingPortfolioLevel:
    depth: int
    candidate_count: int
    unique_state_count: int
    candidate_digest: str
    retained_state_keys: tuple[Hashable, ...]
    retained_action_paths: tuple[tuple[Hashable, ...], ...]
    marking_heads: tuple[tuple[str, Hashable], ...]


@dataclass(frozen=True)
class MarkingPortfolioResult:
    marking_names: tuple[str, ...]
    requested_depth: int
    beam_width: int
    beam_schedule: tuple[int, ...]
    allocation: str
    score_aggregation: str
    channel_diversity: bool
    levels: tuple[MarkingPortfolioLevel, ...]
    retained: tuple[MarkingPortfolioNode, ...]
    target_api_present: bool = False
    target_used: bool = False


def _score_map(values, names):
    scores = dict(values)
    if tuple(sorted(scores)) != tuple(sorted(names)) or \
            len(scores) != len(tuple(values)) or \
            any(not math.isfinite(float(value)) for value in scores.values()):
        raise ValueError("every frozen action must score every marking once")
    return {name: float(scores[name]) for name in names}


def _stable(value):
    return repr(value)


def _digest(rows):
    return hashlib.sha256(repr(tuple(rows)).encode()).hexdigest()


def search_marking_portfolio(
        seed_state: Any, *,
        expand: Callable[[Any], Iterable[FrozenPortfolioAction]],
        state_key: Callable[[Any], Hashable],
        marking_names: Sequence[str], depth: int, beam_width: int,
        beam_schedule: Sequence[int] | None = None,
        allocation: str = "global-marking-round-robin",
        score_aggregation: str = "additive",
        channel_diversity: bool = False,
        ) -> MarkingPortfolioResult:
    """Retain a finite union of rankings over one frozen candidate tree.

    Scores are additive along a path and larger is better.  At each depth the
    search takes rank one from every marking, then rank two, and so on until
    the common beam is full.  A physical state can be retained only once even
    when multiple markings or action orders reach it.
    """
    names = tuple(map(str, marking_names))
    widths = (tuple(map(int, beam_schedule)) if beam_schedule is not None
              else (int(beam_width),) * depth)
    if (not names or len(set(names)) != len(names) or depth < 1 or
            len(widths) != depth or any(width < len(names)
                                        for width in widths) or
            allocation not in ("global-marking-round-robin",
                               "parent-marking-round-robin") or
            score_aggregation not in ("additive", "replace")):
        raise ValueError("invalid marking portfolio search settings")
    seed_key = state_key(seed_state)
    nodes = (MarkingPortfolioNode(
        seed_state, seed_key, (), tuple((name, 0.) for name in names),
        tuple((name, "seed") for name in names)),)
    levels = []
    for level in range(1, depth + 1):
        expanded_pairs = []
        for parent_index, parent in enumerate(nodes):
            parent_scores = dict(parent.cumulative_scores)
            actions = tuple(expand(parent.state))
            if len({repr(action.action_id) for action in actions}) != \
                    len(actions):
                raise ValueError("action IDs must be unique per parent state")
            for action in actions:
                local = _score_map(action.marking_scores, names)
                channels = (dict(action.marking_channels)
                            if action.marking_channels else
                            {name: "all" for name in names})
                if tuple(sorted(channels)) != tuple(sorted(names)) or \
                        len(channels) != len(action.marking_channels or names):
                    raise ValueError(
                        "marking channels must align with marking scores")
                child_key = state_key(action.next_state)
                combined = {
                    name: (parent_scores[name] + local[name]
                           if score_aggregation == "additive"
                           else local[name])
                    for name in names}
                expanded_pairs.append((parent_index, MarkingPortfolioNode(
                    action.next_state, child_key,
                    parent.action_path + (action.action_id,),
                    tuple((name, combined[name]) for name in names),
                    tuple((name, channels[name]) for name in names))))
        if not expanded_pairs:
            break
        expanded = tuple(row for _parent, row in expanded_pairs)
        expanded = tuple(sorted(expanded, key=lambda row: (
            _stable(row.action_path), _stable(row.state_key))))
        geometry_rows = tuple(sorted((
            _stable(row.state_key), _stable(row.action_path))
            for row in expanded))
        def marking_order(rows, name):
            ordered = tuple(sorted(rows, key=lambda row: (
                -dict(row.cumulative_scores)[name],
                _stable(row.action_path), _stable(row.state_key))))
            if not channel_diversity:
                return ordered
            cells = {}
            for row in ordered:
                channel = dict(row.marking_channels)[name]
                cells.setdefault(_stable(channel), []).append(row)
            groups = tuple(sorted(cells.values(), key=lambda cell: (
                -dict(cell[0].cumulative_scores)[name],
                _stable(cell[0].action_path), _stable(cell[0].state_key))))
            result, cell_rank = [], 0
            while any(cell_rank < len(cell) for cell in groups):
                result.extend(cell[cell_rank] for cell in groups
                              if cell_rank < len(cell))
                cell_rank += 1
            return tuple(result)

        orders = {name: marking_order(expanded, name) for name in names}
        retained, retained_keys, rank = [], set(), 0
        heads = tuple((name, orders[name][0].state_key) for name in names)
        width = widths[level - 1]

        def admit(candidate):
            if candidate.state_key in retained_keys:
                return
            retained.append(candidate)
            retained_keys.add(candidate.state_key)

        if allocation == "parent-marking-round-robin":
            parent_orders = {}
            for parent_index in range(len(nodes)):
                children = tuple(row for owner, row in expanded_pairs
                                 if owner == parent_index)
                parent_orders[parent_index] = {
                    name: marking_order(children, name)
                    for name in names}
            local_rank = 0
            while len(retained) < width and any(
                    local_rank < len(parent_orders[parent][name])
                    for parent in parent_orders for name in names):
                for parent in range(len(nodes)):
                    for name in names:
                        rows = parent_orders[parent][name]
                        if local_rank < len(rows):
                            admit(rows[local_rank])
                        if len(retained) == width:
                            break
                    if len(retained) == width:
                        break
                local_rank += 1

        # Fill any unused capacity from the global marking orders. This also
        # implements the original allocation when lineage balancing is off.
        while len(retained) < width and any(
                rank < len(orders[name]) for name in names):
            for name in names:
                if rank >= len(orders[name]):
                    continue
                candidate = orders[name][rank]
                admit(candidate)
                if len(retained) == width:
                    break
            rank += 1
        nodes = tuple(retained)
        levels.append(MarkingPortfolioLevel(
            level, len(expanded), len({row.state_key for row in expanded}),
            _digest(geometry_rows), tuple(row.state_key for row in nodes),
            tuple(row.action_path for row in nodes), heads))
    return MarkingPortfolioResult(
        names, depth, max(widths), widths, allocation, score_aggregation,
        channel_diversity, tuple(levels), nodes)
