#!/usr/bin/env python3
"""Candidate-preserving bounded portfolio of independent GCTS markings."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass(frozen=True)
class MarkingOrder:
    marking_id: str
    candidate_ids: tuple[Hashable, ...]
    target_used: bool = False


@dataclass(frozen=True)
class BoundedMarkingPortfolio:
    marking_ids: tuple[str, ...]
    retained_candidate_ids: tuple[Hashable, ...]
    retained_by_marking: tuple[tuple[str, tuple[Hashable, ...]], ...]
    candidates_per_marking: int
    candidate_universe_digest: str
    portfolio_digest: str
    target_used: bool = False


def bounded_marking_portfolio(
        orders: Sequence[MarkingOrder], *, candidates_per_marking: int = 1,
        ) -> BoundedMarkingPortfolio:
    rows = tuple(orders)
    if (not rows or candidates_per_marking < 1
            or len({row.marking_id for row in rows}) != len(rows)
            or any(not row.marking_id or not row.candidate_ids
                   or row.target_used
                   or len(set(map(repr, row.candidate_ids))) !=
                   len(row.candidate_ids) for row in rows)):
        raise ValueError("invalid marking portfolio")
    universe = tuple(sorted(map(repr, rows[0].candidate_ids)))
    if any(tuple(sorted(map(repr, row.candidate_ids))) != universe
           for row in rows[1:]):
        raise ValueError("markings must rank the identical candidate universe")
    retained = []
    retained_repr = set()
    by_marking = []
    for row in rows:
        selected = row.candidate_ids[:candidates_per_marking]
        by_marking.append((row.marking_id, selected))
        for candidate in selected:
            key = repr(candidate)
            if key not in retained_repr:
                retained.append(candidate)
                retained_repr.add(key)
    universe_digest = hashlib.sha256(repr(universe).encode()).hexdigest()
    payload = (tuple(row.marking_id for row in rows), tuple(map(repr, retained)),
               tuple((name, tuple(map(repr, selected)))
                     for name, selected in by_marking),
               candidates_per_marking, universe_digest)
    return BoundedMarkingPortfolio(
        tuple(row.marking_id for row in rows), tuple(retained),
        tuple(by_marking), candidates_per_marking, universe_digest,
        hashlib.sha256(repr(payload).encode()).hexdigest())


__all__ = ["BoundedMarkingPortfolio", "MarkingOrder",
           "bounded_marking_portfolio"]
