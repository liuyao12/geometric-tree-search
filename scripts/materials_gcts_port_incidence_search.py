#!/usr/bin/env python3
"""Bounded, target-free GCTS search over explicit port incidences.

The aggregate obligation descriptor records means and entropies.  This module
keeps the finite connection roles themselves.  Exact action identifiers remain
search identities only; the carried state is made exclusively from local
cluster colors, cumulative neighbor counts, and normalized separation bins.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Hashable, Iterable, Mapping, Sequence

from materials_gcts_recursive_connections import RecursiveConnectionState


@dataclass(frozen=True, order=True)
class PortRole:
    parent_color: str
    parent_neighbors: tuple[int, ...]
    source_color: str
    source_neighbors: tuple[int, ...]
    separation_bin: int


@dataclass(frozen=True)
class PortIncidenceState:
    roles: tuple[tuple[PortRole, int], ...]
    overflow_roles: int
    overflow_mass: int

    @property
    def mass(self) -> int:
        return sum(count for _role, count in self.roles)


@dataclass(frozen=True)
class PortIncidenceAction:
    action_id: Hashable
    required: PortIncidenceState
    produced: PortIncidenceState
    marking_score: float
    emitted_sites: int
    payload: object = None
    patterns: tuple[tuple[PortRole, ...], ...] = ()


@dataclass(frozen=True)
class PortRoleEvidence:
    positive: int
    total: int


@dataclass(frozen=True)
class FrozenPortIncidencePolicy:
    evidence: Mapping[PortRole, PortRoleEvidence]
    admitted_roles: frozenset[PortRole]
    pattern_evidence: Mapping[tuple[PortRole, ...], PortRoleEvidence]
    admitted_patterns: frozenset[tuple[PortRole, ...]]
    minimum_positive_support: int
    minimum_purity: float


@dataclass(frozen=True)
class PortIncidenceSearchTrace:
    selected_ids: tuple[Hashable, ...]
    explored_actions: int
    backtracks: int
    satisfied_obligation_mass: int
    carried_obligations: PortIncidenceState
    stranded_roles: tuple[PortRole, ...]
    target_used: bool


def semantic_port_role(state: RecursiveConnectionState) -> PortRole:
    """Remove occurrence/action identity while retaining connection geometry."""
    return PortRole(
        state.parent_type.color_key,
        tuple(state.parent_type.cumulative_neighbor_counts),
        state.source_type.color_key,
        tuple(state.source_type.cumulative_neighbor_counts),
        int(state.normalized_separation_bin),
    )


def port_incidence_state(
        proposals, points: Iterable | None = None, *, maximum_roles: int = 8,
        minimum_multiplicity: int = 1) -> PortIncidenceState:
    """Canonical bounded role multiset for a frozen proposal snapshot."""
    if maximum_roles < 1 or minimum_multiplicity < 1:
        raise ValueError("incidence bounds must be positive")
    selected = tuple(sorted(proposals.votes if points is None else points))
    counts: Counter[PortRole] = Counter()
    for point in selected:
        for state, count in proposals.state_votes.get(point, {}).items():
            counts[semantic_port_role(state)] += int(count)
    retained = tuple(sorted(
        ((role, count) for role, count in counts.items()
         if count >= minimum_multiplicity),
        key=lambda row: (-row[1], row[0])))
    explicit = retained[:maximum_roles]
    overflow = retained[maximum_roles:]
    return PortIncidenceState(
        tuple(sorted(explicit)), len(overflow),
        sum(count for _role, count in overflow))


def port_incidence_patterns(
        proposals, points: Iterable, *, maximum_order: int = 2,
        maximum_patterns: int = 32,
        roles_per_site: int = 4) -> tuple[tuple[PortRole, ...], ...]:
    """Canonical bounded role-incidence patterns on whole-action sites.

    Patterns contain no site coordinates: they record which semantic port
    roles jointly vote for one emitted site.  Order two is the current bounded
    GCTS interaction order; higher-order memorization is rejected.
    """
    if (maximum_order < 1 or maximum_order > 2 or maximum_patterns < 1 or
            roles_per_site < 1):
        raise ValueError("invalid incidence-pattern bounds")
    counts = Counter()
    for point in tuple(sorted(points)):
        roles = tuple(sorted(
            ((semantic_port_role(state), int(count))
             for state, count in proposals.state_votes.get(point, {}).items()),
            key=lambda row: (-row[1], row[0])))[:roles_per_site]
        for order in range(1, min(maximum_order, len(roles)) + 1):
            for rows in combinations(roles, order):
                pattern = tuple(sorted(role for role, _count in rows))
                counts[pattern] += min(count for _role, count in rows)
    return tuple(pattern for pattern, _count in sorted(
        counts.items(), key=lambda row: (-row[1], row[0]))[:maximum_patterns])


def fit_port_incidence_policy(
        examples: Sequence[tuple[PortIncidenceAction, bool]], *,
        minimum_positive_support: int = 2,
        minimum_purity: float = .8) -> FrozenPortIncidencePolicy:
    """Fit a finite role table from train-only whole-action outcomes."""
    if (not examples or minimum_positive_support < 1 or
            not 0. < minimum_purity <= 1.):
        raise ValueError("invalid incidence-policy fit")
    counts = defaultdict(lambda: [0, 0])
    pattern_counts = defaultdict(lambda: [0, 0])
    for action, successful in examples:
        # Produced roles are the obligations a branch asks the next frontier
        # to honor.  Multiplicity weights evidence but cannot create a role.
        for role, multiplicity in action.produced.roles:
            counts[role][1] += multiplicity
            counts[role][0] += multiplicity * int(successful)
        for pattern in set(action.patterns):
            pattern_counts[pattern][1] += 1
            pattern_counts[pattern][0] += int(successful)
    evidence = {role: PortRoleEvidence(positive, total)
                for role, (positive, total) in counts.items()}
    pattern_evidence = {
        pattern: PortRoleEvidence(positive, total)
        for pattern, (positive, total) in pattern_counts.items()}
    admitted = frozenset(
        role for role, item in evidence.items()
        if item.positive >= minimum_positive_support and
        item.positive / item.total >= minimum_purity)
    admitted_patterns = frozenset(
        pattern for pattern, item in pattern_evidence.items()
        if item.positive >= minimum_positive_support and
        item.positive / item.total >= minimum_purity)
    return FrozenPortIncidencePolicy(
        evidence, admitted, pattern_evidence, admitted_patterns,
        minimum_positive_support, minimum_purity)


def incidence_action_score(
        policy: FrozenPortIncidencePolicy,
        action: PortIncidenceAction) -> float:
    """Conservative evidence score; exact geometry is never authorized here."""
    pattern_rows = []
    for pattern in action.patterns:
        item = policy.pattern_evidence.get(pattern)
        if item:
            pattern_rows.append((item.positive + 1) / (item.total + 2))
    if pattern_rows:
        return max(pattern_rows) + sum(pattern_rows) / len(pattern_rows)
    rows = []
    for role, count in action.produced.roles:
        item = policy.evidence.get(role)
        rows.extend([((item.positive + 1) / (item.total + 2))
                     if item else 0.] * count)
    if not rows:
        return 0.
    return min(rows) + sum(rows) / len(rows)


def _counter(state: PortIncidenceState) -> Counter[PortRole]:
    return Counter(dict(state.roles))


def _bounded_state(counts: Counter[PortRole], maximum_roles: int) \
        -> PortIncidenceState:
    rows = tuple(sorted(((role, count) for role, count in counts.items()
                         if count > 0), key=lambda row: (-row[1], row[0])))
    explicit = rows[:maximum_roles]
    overflow = rows[maximum_roles:]
    return PortIncidenceState(tuple(sorted(explicit)), len(overflow),
                              sum(count for _role, count in overflow))


def _advance_obligations(
        carried: PortIncidenceState, action: PortIncidenceAction,
        maximum_roles: int) -> tuple[PortIncidenceState, int]:
    unresolved = _counter(carried)
    consumed = _counter(action.required)
    satisfied = 0
    for role in tuple(unresolved):
        amount = min(unresolved[role], consumed[role])
        unresolved[role] -= amount
        satisfied += amount
        if unresolved[role] <= 0:
            del unresolved[role]
    unresolved.update(_counter(action.produced))
    return _bounded_state(unresolved, maximum_roles), satisfied


def _stranded_roles(
        carried: PortIncidenceState,
        children: Sequence[PortIncidenceAction]) -> tuple[PortRole, ...]:
    available = {role for child in children for role, _count in
                 child.required.roles}
    return tuple(role for role, _count in carried.roles
                 if role not in available)


@dataclass(frozen=True)
class _Path:
    actions: tuple[PortIncidenceAction, ...]
    carried: PortIncidenceState
    satisfied: int
    policy_score: float
    stranded: tuple[PortRole, ...]


def search_port_incidence_paths(
        roots: Sequence[PortIncidenceAction],
        expand: Callable[[PortIncidenceAction], Sequence[PortIncidenceAction]],
        policy: FrozenPortIncidencePolicy, *, maximum_depth: int = 3,
        beam_width: int = 8, maximum_roles: int = 8,
        require_admitted_produced_roles: bool = True,
        require_admitted_action_pattern: bool = False) \
        -> PortIncidenceSearchTrace:
    """Search whole actions while carrying unresolved connection incidences.

    A non-root action must consume at least one carried role.  A branch is
    backtracked when a carried role has no frozen child action capable of
    consuming it.  The callback receives only the current exact action and is
    never given a target configuration.
    """
    if maximum_depth < 1 or beam_width < 1 or maximum_roles < 1:
        raise ValueError("search dimensions must be positive")
    roots = tuple(roots)
    if not roots:
        return PortIncidenceSearchTrace(
            (), 0, 0, 0, PortIncidenceState((), 0, 0), (), False)
    explored = len(roots)
    backtracks = 0
    beam = []
    for action in roots:
        if (require_admitted_action_pattern and not
                any(pattern in policy.admitted_patterns
                    for pattern in action.patterns)):
            backtracks += 1
            continue
        if require_admitted_produced_roles and any(
                role not in policy.admitted_roles
                for role, _count in action.produced.roles):
            backtracks += 1
            continue
        carried, satisfied = _advance_obligations(
            PortIncidenceState((), 0, 0), action, maximum_roles)
        children = tuple(expand(action))
        stranded = _stranded_roles(carried, children) if children else \
            tuple(role for role, _count in carried.roles)
        if stranded and maximum_depth > 1:
            backtracks += 1
            continue
        beam.append(_Path((action,), carried, satisfied,
                          incidence_action_score(policy, action), stranded))
    beam = sorted(beam, key=lambda path: (
        len(path.stranded), -path.satisfied, -path.policy_score,
        -path.actions[-1].marking_score,
        tuple(map(repr, (action.action_id for action in path.actions)))))[:beam_width]

    for _depth in range(1, maximum_depth):
        next_paths = []
        for path in beam:
            children = tuple(expand(path.actions[-1]))
            explored += len(children)
            for action in children:
                if (require_admitted_action_pattern and not
                        any(pattern in policy.admitted_patterns
                            for pattern in action.patterns)):
                    backtracks += 1
                    continue
                carried, satisfied = _advance_obligations(
                    path.carried, action, maximum_roles)
                if path.carried.mass and not satisfied:
                    backtracks += 1
                    continue
                if require_admitted_produced_roles and any(
                        role not in policy.admitted_roles
                        for role, _count in action.produced.roles):
                    backtracks += 1
                    continue
                grandchildren = tuple(expand(action))
                stranded = (_stranded_roles(carried, grandchildren)
                            if grandchildren else tuple(
                                role for role, _count in carried.roles))
                if stranded and _depth + 1 < maximum_depth:
                    backtracks += 1
                    continue
                next_paths.append(_Path(
                    path.actions + (action,), carried,
                    path.satisfied + satisfied,
                    path.policy_score + incidence_action_score(policy, action),
                    stranded))
        if not next_paths:
            break
        beam = sorted(next_paths, key=lambda path: (
            len(path.stranded), -path.satisfied, -path.policy_score,
            -sum(action.marking_score for action in path.actions),
            tuple(map(repr, (action.action_id for action in path.actions)))))[:beam_width]
    if not beam:
        return PortIncidenceSearchTrace(
            (), explored, backtracks, 0, PortIncidenceState((), 0, 0), (),
            False)
    best = beam[0]
    return PortIncidenceSearchTrace(
        tuple(action.action_id for action in best.actions), explored,
        backtracks, best.satisfied, best.carried, best.stranded, False)
