#!/usr/bin/env python3
"""Species-aware finite-tolerance scorer for frozen Cartesian actions."""

from __future__ import annotations

import math


def colored_position_index(positions, species, *, tolerance=1e-5):
    if (not math.isfinite(tolerance) or tolerance <= 0 or
            len(positions) != len(species)):
        raise ValueError("invalid colored-position target")
    cells = {}
    for point, color in zip(positions, species):
        if len(point) != 3 or any(not math.isfinite(float(v)) for v in point):
            raise ValueError("invalid target point")
        key = tuple(math.floor(float(value) / tolerance) for value in point)
        cells.setdefault((str(color), key), []).append(tuple(map(float, point)))
    return cells


def colored_position_match(point, color, index, *, tolerance=1e-5):
    if len(point) != 3 or any(not math.isfinite(float(v)) for v in point):
        return False
    key = tuple(math.floor(float(value) / tolerance) for value in point)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for candidate in index.get((str(color), (
                        key[0] + dx, key[1] + dy, key[2] + dz)), ()):
                    if math.dist(point, candidate) <= tolerance:
                        return True
    return False


def colored_action_labels(actions, index, *, tolerance=1e-5):
    return tuple(colored_position_match(
        point, color, index, tolerance=tolerance)
        for point, color in actions)


__all__ = [
    "colored_action_labels", "colored_position_index",
    "colored_position_match"]
