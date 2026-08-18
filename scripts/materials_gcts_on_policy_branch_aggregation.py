#!/usr/bin/env python3
"""One-round, group-sealed aggregation of on-policy GCTS branch values.

The broad branch corpus describes many geometrically possible partial paths.
This module adds states actually visited by the frozen search policy, while
keeping every held-out spatial group out of both corpora.  Conflicting labels
for the same invariant descriptor are deliberately retained: collapsing them
would turn genuine representation aliasing into an optimistic deterministic
label.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_recurrent_branch_value import RecurrentBranchExample, _fit
from materials_gcts_recurrent_branch_value_heads import (
    DepthBranchExample, FrozenDepthBranchValues, depth_branch_values_digest)


@dataclass(frozen=True)
class OnPolicyAggregationAudit:
    training_groups: int
    heldout_groups: tuple[Hashable, ...]
    broad_examples: int
    on_policy_examples: int
    merged_examples: int
    positive_on_policy_examples: int
    conflicting_descriptor_groups: int
    selected_neighbors_by_depth: tuple[tuple[int, int], ...]
    training_example_digest: str
    model_digest: str
    heldout_seen_during_fit: bool
    target_used: bool


def _row_key(row: DepthBranchExample, *, include_outcome: bool) -> tuple:
    key = (row.group, int(row.depth), tuple(row.features),
           tuple(row.action_colors))
    return key + ((bool(row.successful),) if include_outcome else ())


def branch_examples_digest(rows: Sequence[DepthBranchExample]) -> str:
    payload = tuple(sorted(
        (_row_key(row, include_outcome=True) for row in rows), key=repr))
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def fit_group_sealed_on_policy_values(
        broad_examples: Sequence[DepthBranchExample],
        on_policy_examples: Sequence[DepthBranchExample], *,
        heldout_groups: Sequence[Hashable], feature_names: Sequence[str],
        color_keys: Sequence[str],
        neighbors_by_depth: Sequence[tuple[int, int]], beta_prior: float = .5,
        ) -> tuple[FrozenDepthBranchValues, OnPolicyAggregationAudit]:
    """Fit one frozen aggregation round without held-out group exposure.

    Exact duplicate rows are removed, but rows differing only in outcome are
    both retained.  The latter is the observable evidence that the chosen
    invariant representation aliases distinct geometric futures.
    """
    broad = tuple(broad_examples)
    on_policy = tuple(on_policy_examples)
    heldout = tuple(heldout_groups)
    heldout_set = set(heldout)
    names = tuple(feature_names)
    colors = tuple(color_keys)
    neighbor_map = dict((int(depth), int(count))
                        for depth, count in neighbors_by_depth)
    if (not broad or not on_policy or not heldout or not names or not colors or
            not neighbor_map or min(neighbor_map.values()) < 1 or
            beta_prior <= 0):
        raise ValueError("invalid on-policy aggregation corpus")
    all_rows = broad + on_policy
    depths = tuple(sorted({int(row.depth) for row in all_rows}))
    if set(depths) != set(neighbor_map):
        raise ValueError("one frozen capacity is required for every depth")
    for row in all_rows:
        if (len(row.features) != len(names) or row.depth < 1 or
                len(row.action_colors) != row.depth or
                any(color not in colors for color in row.action_colors)):
            raise ValueError("invalid on-policy branch example")

    training_broad = tuple(row for row in broad
                           if row.group not in heldout_set)
    training_on_policy = tuple(row for row in on_policy
                               if row.group not in heldout_set)
    if not training_broad or not training_on_policy:
        raise ValueError("held-out split leaves no training evidence")
    training_groups = {row.group for row in training_broad + training_on_policy}
    if len(training_groups) < 3:
        raise ValueError("insufficient independent training groups")

    # Outcome is part of the deduplication key by design.
    unique = {_row_key(row, include_outcome=True): row
              for row in training_broad + training_on_policy}
    merged = tuple(sorted(unique.values(), key=lambda row: repr(
        _row_key(row, include_outcome=True))))
    outcomes: dict[tuple, set[bool]] = {}
    for row in merged:
        outcomes.setdefault(_row_key(row, include_outcome=False), set()).add(
            bool(row.successful))
    conflicts = sum(len(labels) > 1 for labels in outcomes.values())

    heads = []
    for depth in depths:
        rows = tuple(RecurrentBranchExample(
            row.group, tuple(row.features), tuple(row.action_colors),
            bool(row.successful)) for row in merged if row.depth == depth)
        if not rows:
            raise ValueError("empty recurrent branch depth")
        heads.append((depth, _fit(
            rows, names, colors, neighbor_map[depth], beta_prior)))
    model = FrozenDepthBranchValues(names, colors, tuple(heads))
    audit = OnPolicyAggregationAudit(
        training_groups=len(training_groups),
        heldout_groups=heldout,
        broad_examples=len(training_broad),
        on_policy_examples=len(training_on_policy),
        merged_examples=len(merged),
        positive_on_policy_examples=sum(
            row.successful for row in training_on_policy),
        conflicting_descriptor_groups=conflicts,
        selected_neighbors_by_depth=tuple(sorted(neighbor_map.items())),
        training_example_digest=branch_examples_digest(merged),
        model_digest=depth_branch_values_digest(model),
        heldout_seen_during_fit=any(
            row.group in heldout_set for row in merged),
        target_used=False)
    return model, audit
