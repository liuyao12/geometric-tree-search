#!/usr/bin/env python3
"""Target-free fallback prefixes against shared-action failure modes."""

from __future__ import annotations

import hashlib
from collections import Counter


def _value(row, name):
    return row[name] if isinstance(row, dict) else getattr(row, name)


def _action_key(action):
    point, color = action
    return tuple(map(float, point)), str(color)


def _prefix_actions(branch, child):
    return tuple(_action_key(row) for row in
                 tuple(_value(branch, "first_actions")) +
                 tuple(tuple(_value(branch, "second_actions"))[child]))


def select_action_marginal_prefixes(*, scheduled, branches):
    """Keep every joint leader and add one structurally diverse fallback.

    The selector sees only already-frozen action geometry and schedule ranks.
    It never receives a target, correctness label, material family, lattice,
    or global direction.  Joint leaders remain untouched.  For each parent,
    the added fallback first avoids actions occurring in every joint prefix,
    then minimizes overlap with the complete joint action marginal.
    """
    branches = tuple(sorted(branches, key=lambda row: int(
        _value(row, "first_rank"))))
    by_parent = {int(_value(row, "first_rank")): row for row in branches}
    if tuple(by_parent) != tuple(range(1, len(branches) + 1)):
        raise ValueError("prefix parents must be contiguous and unique")
    selected_rows = tuple(scheduled["selected_rows"])
    joint = {}
    fallback = {}
    for row in selected_rows:
        parent, child, sources, joint_rank, joint_score, base_rank, \
            base_score = row
        parent, child = int(parent), int(child)
        if parent not in by_parent:
            raise ValueError("scheduled prefix references unknown parent")
        if "joint" in sources:
            prior = joint.get(parent)
            candidate = (int(joint_rank), child, row)
            if prior is None or candidate[:2] < prior[:2]:
                joint[parent] = candidate
        if "base-fallback" in sources:
            fallback.setdefault(parent, []).append(row)
    if set(joint) != set(by_parent):
        raise ValueError("every parent needs one joint prefix")

    joint_rows = tuple(joint[parent][2] for parent in sorted(joint))
    joint_actions = {
        parent: frozenset(_prefix_actions(
            by_parent[parent], int(joint[parent][2][1])))
        for parent in joint}
    marginal = Counter(action for rows in joint_actions.values()
                       for action in rows)
    universal = frozenset(action for action, count in marginal.items()
                          if count == len(joint))
    diverse_rows = []
    for parent in sorted(joint):
        leader_child = int(joint[parent][2][1])
        candidates = [row for row in fallback.get(parent, ())
                      if int(row[1]) != leader_child]
        if not candidates:
            continue

        def objective(row):
            actions = frozenset(_prefix_actions(
                by_parent[parent], int(row[1])))
            return (
                len(actions & universal),
                sum(marginal[action] for action in actions),
                max((marginal[action] for action in actions), default=0),
                -len(actions - set(marginal)),
                int(row[5]), int(row[3]), int(row[1]))

        diverse_rows.append(min(candidates, key=objective))
    rows = tuple(sorted(joint_rows + tuple(diverse_rows),
                        key=lambda row: (int(row[0]),
                                         0 if "joint" in row[2] else 1,
                                         int(row[1]))))
    if len({(int(row[0]), int(row[1])) for row in rows}) != len(rows):
        raise AssertionError("duplicate action-marginal prefix")
    selected_actions = tuple((int(row[0]), int(row[1]),
                              _prefix_actions(by_parent[int(row[0])],
                                              int(row[1])))
                             for row in rows)
    return {
        "selected_rows": rows,
        "joint_rows": joint_rows,
        "diverse_fallback_rows": tuple(diverse_rows),
        "joint_universal_actions": tuple(sorted(universal)),
        "selected_prefix_digest": hashlib.sha256(
            repr(selected_actions).encode()).hexdigest(),
        "target_used": False,
    }


__all__ = ["select_action_marginal_prefixes"]
