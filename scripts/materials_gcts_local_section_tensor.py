#!/usr/bin/env python3
"""Bounded rigid-motion-invariant local sections for GCTS actions.

The tensor relates a finite colored action set to atoms that are already
occupied.  It is a marking representation only: it neither proposes sites nor
changes the exact cluster/port geometry admitted by the search.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Sequence


Point = tuple[float, float, float]


@dataclass(frozen=True)
class LocalSectionSchema:
    species: tuple[str, ...]
    distance_scale: float
    radial_bin_width: float = .5
    radial_bins: int = 8
    angular_cutoff: float = 3.
    angular_bins: int = 6
    include_chirality: bool = False
    target_used: bool = False


@dataclass(frozen=True)
class LocalSectionTensor:
    values: tuple[float, ...]
    schema_digest: str
    proper_se3_invariant: bool = True
    lattice_coordinates_used: bool = False
    target_used: bool = False
    chirality_preserved: bool = False


def local_section_schema_digest(schema: LocalSectionSchema) -> str:
    return hashlib.sha256(repr(schema).encode()).hexdigest()


def local_section_feature_names(schema: LocalSectionSchema) -> tuple[str, ...]:
    _validate_schema(schema)
    radial = tuple(
        f"radial:{action}:{neighbor}:{bucket}"
        for action in schema.species for neighbor in schema.species
        for bucket in range(schema.radial_bins))
    angular = tuple(
        f"angle:{action}:{left}{right}:{bucket}"
        for action in schema.species
        for index, left in enumerate(schema.species)
        for right in schema.species[index:]
        for bucket in range(schema.angular_bins))
    chiral = (() if not schema.include_chirality else tuple(
        f"chirality:{action}:{first}{second}{third}"
        for action in schema.species
        for first_index, first in enumerate(schema.species)
        for second_index, second in enumerate(
                schema.species[first_index:], first_index)
        for third in schema.species[second_index:]))
    return radial + angular + chiral


def _validate_schema(schema: LocalSectionSchema) -> None:
    if (not schema.species or len(set(schema.species)) != len(schema.species)
            or any(not item for item in schema.species)
            or schema.distance_scale <= 0 or schema.radial_bin_width <= 0
            or schema.radial_bins < 1 or schema.angular_cutoff <= 0
            or schema.angular_bins < 1 or schema.target_used):
        raise ValueError("invalid local-section schema")


def _points(rows: Sequence[Sequence[float]]) -> tuple[Point, ...]:
    points = tuple(tuple(map(float, row)) for row in rows)
    if any(len(point) != 3 or not all(map(math.isfinite, point))
           for point in points):
        raise ValueError("local-section points must be finite 3D vectors")
    return points  # type: ignore[return-value]


def _bin(value: float, width: float, count: int) -> int:
    return min(count - 1, max(0, int(value / width + 1e-10)))


def _determinant(left: Point, middle: Point, right: Point) -> float:
    return (left[0] * (middle[1] * right[2] - middle[2] * right[1])
            - left[1] * (middle[0] * right[2] - middle[2] * right[0])
            + left[2] * (middle[0] * right[1] - middle[1] * right[0]))


def local_section_tensor(
        action_positions: Sequence[Sequence[float]],
        action_species: Sequence[str],
        occupied_positions: Sequence[Sequence[float]],
        occupied_species: Sequence[str],
        schema: LocalSectionSchema,
        ) -> LocalSectionTensor:
    """Encode one action halo without a global frame, lattice, or target."""
    _validate_schema(schema)
    actions = _points(action_positions)
    occupied = _points(occupied_positions)
    action_species = tuple(map(str, action_species))
    occupied_species = tuple(map(str, occupied_species))
    allowed = set(schema.species)
    if (not actions or len(actions) != len(action_species)
            or len(occupied) != len(occupied_species)
            or any(item not in allowed for item in
                   action_species + occupied_species)
            or len(set(actions)) != len(actions)
            or set(actions) & set(occupied)):
        raise ValueError("invalid colored local-section inputs")

    radial = {(action, neighbor, bucket): 0.
              for action in schema.species for neighbor in schema.species
              for bucket in range(schema.radial_bins)}
    angular = {(action, left, right, bucket): 0.
               for action in schema.species
               for index, left in enumerate(schema.species)
               for right in schema.species[index:]
               for bucket in range(schema.angular_bins)}
    chiral = {(action, first, second, third): 0.
              for action in schema.species
              for first_index, first in enumerate(schema.species)
              for second_index, second in enumerate(
                      schema.species[first_index:], first_index)
              for third in schema.species[second_index:]}
    action_counts = {item: action_species.count(item)
                     for item in schema.species}
    radial_cutoff = schema.radial_bins * schema.radial_bin_width

    for center, action_color in zip(actions, action_species):
        neighbors = []
        for point, neighbor_color in zip(occupied, occupied_species):
            vector = tuple((point[axis] - center[axis]) /
                           schema.distance_scale for axis in range(3))
            radius = math.sqrt(sum(value * value for value in vector))
            if radius < radial_cutoff:
                radial[(action_color, neighbor_color, _bin(
                    radius, schema.radial_bin_width,
                    schema.radial_bins))] += 1.
            if 1e-10 < radius < schema.angular_cutoff:
                neighbors.append((neighbor_color, vector, radius))
        for index, (left_color, left, left_radius) in enumerate(neighbors):
            for right_color, right, right_radius in neighbors[index + 1:]:
                pair = tuple(sorted((left_color, right_color),
                                    key=schema.species.index))
                cosine = max(-1., min(1., sum(a * b for a, b in
                    zip(left, right)) / (left_radius * right_radius)))
                angular[(action_color, pair[0], pair[1], _bin(
                    cosine + 1., 2. / schema.angular_bins,
                    schema.angular_bins))] += 1.
        if schema.include_chirality:
            # By determinant multilinearity this equals the sum over every
            # ordered neighbor triple, but costs O(neighbors + channels)
            # rather than O(neighbors^3). Terms reusing one atom vanish
            # automatically because two columns are parallel.
            moments = {color: [[0., 0., 0.] for _power in range(3)]
                       for color in schema.species}
            for color, vector, radius in neighbors:
                unit = tuple(value / radius for value in vector)
                normalized_radius = radius / schema.angular_cutoff
                for power in range(3):
                    weight = normalized_radius ** power
                    for axis in range(3):
                        moments[color][power][axis] += unit[axis] * weight
            for first_index, first in enumerate(schema.species):
                for second_index, second in enumerate(
                        schema.species[first_index:], first_index):
                    for third in schema.species[second_index:]:
                        chiral[(action_color, first, second, third)] += \
                            _determinant(
                                tuple(moments[first][0]),
                                tuple(moments[second][1]),
                                tuple(moments[third][2]))

    values = tuple(radial[key] / max(1, action_counts[key[0]])
                   for key in radial)
    values += tuple(angular[key] / max(1, action_counts[key[0]])
                    for key in angular)
    if schema.include_chirality:
        values += tuple(chiral[key] / max(1, action_counts[key[0]])
                        for key in chiral)
    if len(values) != len(local_section_feature_names(schema)):
        raise AssertionError("local-section tensor schema mismatch")
    return LocalSectionTensor(
        values, local_section_schema_digest(schema),
        chirality_preserved=schema.include_chirality)
