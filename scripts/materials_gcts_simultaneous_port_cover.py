#!/usr/bin/env python3
"""Exact bounded cover certificates for simultaneous semantic port duties.

This module deliberately separates three outcomes:

``satisfied``
    One explicitly compatible action set discharges every carried duty.
``unsatisfied``
    Exhaustive candidate enumeration and exhaustive search prove that no such
    set exists.
``unknown``
    The available candidates or the bounded search were truncated.  Absence
    of a witness is not converted into a branch rejection.

The duties are finite, symmetry-quotiented semantic port identities.  Exact
candidate geometry and collision checks remain upstream certificates; this
solver may select among those candidates but can never create geometry.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import math
from typing import Hashable, Iterable, Sequence


@dataclass(frozen=True)
class PortCoverAction:
    action_id: Hashable
    consumes: tuple[Hashable, ...]
    conflicts: frozenset[Hashable] = frozenset()
    marking_score: float = 0.
    payload: object = None


@dataclass(frozen=True)
class FrozenPortCoverProblem:
    obligations: tuple[Hashable, ...]
    actions: tuple[PortCoverAction, ...]
    enumeration_complete: bool
    target_used: bool = False


@dataclass(frozen=True)
class PortCoverCertificate:
    status: str
    selected_ids: tuple[Hashable, ...]
    covered_obligations: tuple[Hashable, ...]
    uncovered_obligations: tuple[Hashable, ...]
    explored_nodes: int
    candidate_digest: str
    certificate_digest: str
    enumeration_complete: bool
    search_complete: bool
    rejectable_as_inconsistent: bool
    target_used: bool = False


def _canonical_rows(values: Iterable[Hashable]) -> tuple[Hashable, ...]:
    return tuple(sorted(values, key=repr))


def _subtract(remaining: Counter, consumed: Counter) -> Counter:
    result = remaining.copy()
    for role, count in consumed.items():
        if role not in result:
            continue
        result[role] -= min(result[role], count)
        if result[role] <= 0:
            del result[role]
    return result


def _expanded(counter: Counter) -> tuple[Hashable, ...]:
    return _canonical_rows(
        role for role, count in counter.items() for _ in range(count))


def solve_simultaneous_port_cover(
        problem: FrozenPortCoverProblem, *, maximum_actions: int = 8,
        maximum_search_nodes: int = 100_000) -> PortCoverCertificate:
    """Find a minimum compatible cover, or return a fail-closed status.

    An action may discharge several duties at once.  Conflicts are interpreted
    symmetrically even when only one action declares the relation.  The search
    branches on the most constrained remaining duty and is exhaustive unless
    ``maximum_search_nodes`` is reached.
    """
    if (problem.target_used or maximum_actions < 0 or
            maximum_search_nodes < 1):
        raise ValueError("invalid or target-tainted port-cover problem")
    actions = tuple(sorted(problem.actions, key=lambda row: repr(row.action_id)))
    identifiers = tuple(action.action_id for action in actions)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("port-cover action IDs must be unique")
    known = set(identifiers)
    if any(not math.isfinite(action.marking_score) for action in actions):
        raise ValueError("port-cover scores must be finite")
    if any(set(action.conflicts) - known for action in actions):
        raise ValueError("port-cover conflict references an unknown action")

    obligation_counts = Counter(problem.obligations)
    consumed = {action.action_id: Counter(action.consumes)
                for action in actions}
    conflicts = {action.action_id: set(action.conflicts)
                 for action in actions}
    for action in actions:
        for other in action.conflicts:
            conflicts[other].add(action.action_id)
    candidates_by_role = defaultdict(tuple)
    for role in obligation_counts:
        candidates_by_role[role] = tuple(
            action for action in actions if consumed[action.action_id][role])

    candidate_code = tuple((action.action_id,
                            _canonical_rows(action.consumes),
                            _canonical_rows(conflicts[action.action_id]),
                            float(action.marking_score))
                           for action in actions)
    candidate_digest = hashlib.sha256(repr((
        _expanded(obligation_counts), candidate_code,
        bool(problem.enumeration_complete))).encode()).hexdigest()

    explored = 0
    search_complete = True
    best = None

    def visit(remaining: Counter, selected: tuple[PortCoverAction, ...]):
        nonlocal explored, search_complete, best
        if explored >= maximum_search_nodes:
            search_complete = False
            return
        explored += 1
        if not remaining:
            score = sum(action.marking_score for action in selected)
            key = (len(selected), -score,
                   tuple(repr(action.action_id) for action in selected))
            if best is None or key < best[0]:
                best = key, selected
            return
        if len(selected) >= maximum_actions:
            return
        if best is not None and len(selected) >= best[0][0]:
            return
        selected_ids = {action.action_id for action in selected}
        admissible = {}
        for role in remaining:
            rows = tuple(action for action in candidates_by_role[role]
                         if action.action_id not in selected_ids and
                         not any(action.action_id in conflicts[prior]
                                 for prior in selected_ids))
            admissible[role] = rows
        role = min(remaining, key=lambda item: (
            len(admissible[item]), repr(item)))
        for action in admissible[role]:
            visit(_subtract(remaining, consumed[action.action_id]),
                  selected + (action,))
            if not search_complete:
                return

    visit(obligation_counts, ())
    selected = () if best is None else best[1]
    selected_counts = Counter()
    for action in selected:
        selected_counts.update(consumed[action.action_id])
    uncovered = _subtract(obligation_counts, selected_counts)
    covered = obligation_counts.copy()
    for role in uncovered:
        covered[role] -= uncovered[role]
        if covered[role] <= 0:
            del covered[role]
    if best is not None:
        status = "satisfied"
    elif problem.enumeration_complete and search_complete:
        status = "unsatisfied"
    else:
        status = "unknown"
    selected_ids = tuple(action.action_id for action in selected)
    certificate_code = (
        status, _expanded(obligation_counts), selected_ids,
        tuple((action.action_id, _canonical_rows(action.consumes),
               _canonical_rows(conflicts[action.action_id]))
              for action in selected),
        bool(problem.enumeration_complete), bool(search_complete))
    certificate_digest = hashlib.sha256(
        repr(certificate_code).encode()).hexdigest()
    return PortCoverCertificate(
        status, selected_ids, _expanded(covered), _expanded(uncovered),
        explored, candidate_digest, certificate_digest,
        bool(problem.enumeration_complete), search_complete,
        status == "unsatisfied", False)


__all__ = [
    "FrozenPortCoverProblem", "PortCoverAction", "PortCoverCertificate",
    "solve_simultaneous_port_cover",
]
