#!/usr/bin/env python3
"""Permutation- and proper-SE(3)-invariant GCTS branch connection features.

Raw pose counts are not branch-value channels.  Each accepted action instead
carries the bounded response of the already-frozen pose/port marking.  The
branch representation couples those responses to colored relative geometry,
while exact coordinates remain outside the value model and search certificate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class PosePortBranchAction:
    color: str
    position: tuple[float, float, float]
    channel_response: tuple[int, ...]


def pose_port_branch_feature_names(
        base_names: Sequence[str], color_keys: Sequence[str], *,
        maximum_actions: int, channel_count: int) -> tuple[str, ...]:
    colors = tuple(sorted(set(map(str, color_keys))))
    if (not base_names or maximum_actions < 1 or channel_count < 1 or
            not colors):
        raise ValueError("invalid pose-port branch feature schema")
    pairs = tuple((left, right) for index, left in enumerate(colors)
                  for right in colors[index:])
    return (tuple(base_names) + tuple(
        f"colored_separation:{left}{right}" for left, right in pairs) +
        tuple(f"pose_port_channel:{slot}:{channel}"
              for slot in range(maximum_actions)
              for channel in range(channel_count)))


def coupled_pose_port_branch_features(
        base_features: Sequence[float], actions: Sequence[PosePortBranchAction],
        *, color_keys: Sequence[str], maximum_actions: int,
        channel_count: int) -> tuple[float, ...]:
    """Couple a finite pose/port response multiset to colored distances."""
    base = tuple(map(float, base_features))
    rows = tuple(actions)
    colors = tuple(sorted(set(map(str, color_keys))))
    if (not base or not rows or len(rows) > maximum_actions or
            maximum_actions < 1 or channel_count < 1 or not colors or
            any(not math.isfinite(value) for value in base)):
        raise ValueError("invalid pose-port branch payload")
    for row in rows:
        if (row.color not in colors or len(row.position) != 3 or
                len(row.channel_response) != channel_count or
                any(not math.isfinite(float(value)) for value in row.position)):
            raise ValueError("invalid pose-port branch action")
    pairs = tuple((left, right) for index, left in enumerate(colors)
                  for right in colors[index:])
    distances = {pair: [] for pair in pairs}
    for index, row in enumerate(rows):
        for other in rows[index + 1:]:
            pair = tuple(sorted((row.color, other.color)))
            distances[pair].append(math.dist(row.position, other.position))
    colored = tuple(sum(distances[pair]) / len(distances[pair])
                    if distances[pair] else 0. for pair in pairs)
    # Sorting removes arbitrary order among commuting placements.  The
    # response itself is learned from proper-SE(3)-quotiented port evidence.
    marks = tuple(sorted((row.color, tuple(row.channel_response))
                         for row in rows))
    channels = tuple(float(value) for slot in range(maximum_actions)
                     for value in (marks[slot][1] if slot < len(marks)
                                   else (0,) * channel_count))
    return base + colored + channels
