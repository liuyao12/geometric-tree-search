#!/usr/bin/env python3
"""Exactness regression for the bounded-neighborhood spatial hash."""

import math
import random

from materials_gcts_recursive_connections import (
    LocalClusterType, local_cluster_types)


def _brute(positions, colors, edges):
    keys = tuple(sorted({repr(color) for color in colors}))
    encoded = tuple(repr(color) for color in colors)
    result = []
    for center_index, center in enumerate(positions):
        counts = []
        for color in keys:
            separations = [
                math.dist(center, point)
                for index, point in enumerate(positions)
                if index != center_index and encoded[index] == color]
            counts.extend(sum(distance <= edge for distance in separations)
                          for edge in edges)
        result.append(LocalClusterType(encoded[center_index], tuple(counts)))
    return tuple(result)


def test_spatial_hash_matches_all_pairs_descriptor() -> None:
    randomizer = random.Random(20260813)
    positions = tuple(tuple(randomizer.uniform(-8, 8) for _ in range(3))
                      for _ in range(250))
    colors = tuple(randomizer.choice(("Na", "Cl", "Si"))
                   for _ in positions)
    edges = (.8, 1.7, 3.2)
    assert local_cluster_types(positions, colors, edges) == _brute(
        positions, colors, edges)


if __name__ == "__main__":
    test_spatial_hash_matches_all_pairs_descriptor()
    print("spatial local-cluster typing: exactness passed")
