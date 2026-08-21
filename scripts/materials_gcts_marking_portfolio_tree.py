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


@dataclass(frozen=True)
class MarkingPortfolioNode:
    state: Any
    state_key: Hashable
    action_path: tuple[Hashable, ...]
    cumulative_scores: tuple[tuple[str, float], ...]


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
        ) -> MarkingPortfolioResult:
    """Retain a finite union of rankings over one frozen candidate tree.

    Scores are additive along a path and larger is better.  At each depth the
    search takes rank one from every marking, then rank two, and so on until
    the common beam is full.  A physical state can be retained only once even
    when multiple markings or action orders reach it.
    """
    names = tuple(map(str, marking_names))
    if (not names or len(set(names)) != len(names) or depth < 1 or
            beam_width < len(names)):
        raise ValueError("invalid marking portfolio search settings")
    seed_key = state_key(seed_state)
    nodes = (MarkingPortfolioNode(
        seed_state, seed_key, (), tuple((name, 0.) for name in names)),)
    levels = []
    for level in range(1, depth + 1):
        expanded = []
        for parent in nodes:
            parent_scores = dict(parent.cumulative_scores)
            actions = tuple(expand(parent.state))
            if len({repr(action.action_id) for action in actions}) != \
                    len(actions):
                raise ValueError("action IDs must be unique per parent state")
            for action in actions:
                local = _score_map(action.marking_scores, names)
                child_key = state_key(action.next_state)
                expanded.append(MarkingPortfolioNode(
                    action.next_state, child_key,
                    parent.action_path + (action.action_id,),
                    tuple((name, parent_scores[name] + local[name])
                          for name in names)))
        if not expanded:
            break
        expanded = tuple(sorted(expanded, key=lambda row: (
            _stable(row.action_path), _stable(row.state_key))))
        geometry_rows = tuple(sorted((
            _stable(row.state_key), _stable(row.action_path))
            for row in expanded))
        orders = {}
        for name in names:
            orders[name] = tuple(sorted(expanded, key=lambda row: (
                -dict(row.cumulative_scores)[name],
                _stable(row.action_path), _stable(row.state_key))))
        retained, retained_keys, rank = [], set(), 0
        heads = tuple((name, orders[name][0].state_key) for name in names)
        while len(retained) < beam_width and any(
                rank < len(orders[name]) for name in names):
            for name in names:
                if rank >= len(orders[name]):
                    continue
                candidate = orders[name][rank]
                key = candidate.state_key
                if key in retained_keys:
                    continue
                retained.append(candidate)
                retained_keys.add(key)
                if len(retained) == beam_width:
                    break
            rank += 1
        nodes = tuple(retained)
        levels.append(MarkingPortfolioLevel(
            level, len(expanded), len({row.state_key for row in expanded}),
            _digest(geometry_rows), tuple(row.state_key for row in nodes),
            tuple(row.action_path for row in nodes), heads))
    return MarkingPortfolioResult(
        names, depth, beam_width, tuple(levels), nodes)
