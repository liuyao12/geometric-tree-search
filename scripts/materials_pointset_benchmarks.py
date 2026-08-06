#!/usr/bin/env python3
"""Deterministic colored 3-D point sets for hierarchical-cover benchmarks.

The public representation is deliberately only species plus Cartesian
coordinates.  Generator metadata is ground truth for evaluation, not an input
contract for a learner.  In particular, consumers do not need lattice indices
or privileged orientations.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Sequence, Tuple

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class MotifOccurrence:
    """A planted occurrence, including enough information for exact scoring."""

    motif_type: str
    atom_indices: Tuple[int, ...]
    rotation: Matrix
    translation: Vector
    parent_occurrence: Optional[int] = None
    shared_atom: Optional[int] = None


@dataclass(frozen=True)
class ColoredPointSet:
    name: str
    positions: Tuple[Vector, ...]
    species: Tuple[str, ...]
    motif_templates: Mapping[str, Tuple[Tuple[str, Vector], ...]] = field(
        default_factory=dict)
    motif_occurrences: Tuple[MotifOccurrence, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.positions) != len(self.species):
            raise ValueError("positions and species must have equal length")
        if not self.positions:
            raise ValueError("a point set must be nonempty")

    def plain_input(self) -> Dict[str, object]:
        """Return the intentionally unprivileged input seen by learners."""
        return {"positions": self.positions, "species": self.species}


@dataclass(frozen=True)
class RadialSplit:
    center: Vector
    core_radius: float
    core_indices: Tuple[int, ...]
    annulus_indices: Tuple[int, ...]


def _add(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(float(a + b) for a, b in zip(left, right))  # type: ignore[return-value]


def _sub(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(float(a - b) for a, b in zip(left, right))  # type: ignore[return-value]


def _scale(value: float, vector: Sequence[float]) -> Vector:
    return tuple(float(value * coordinate) for coordinate in vector)  # type: ignore[return-value]


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _matvec(matrix: Matrix, vector: Sequence[float]) -> Vector:
    return tuple(sum(row[column] * vector[column] for column in range(3))
                 for row in matrix)  # type: ignore[return-value]


def random_rotation(rng: random.Random) -> Matrix:
    """Uniform SO(3) rotation from a deterministic random source."""
    u1, u2, u3 = rng.random(), rng.random(), rng.random()
    qx = math.sqrt(1.0 - u1) * math.sin(2.0 * math.pi * u2)
    qy = math.sqrt(1.0 - u1) * math.cos(2.0 * math.pi * u2)
    qz = math.sqrt(u1) * math.sin(2.0 * math.pi * u3)
    qw = math.sqrt(u1) * math.cos(2.0 * math.pi * u3)
    return (
        (1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw),
         2 * (qx * qz + qy * qw)),
        (2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz),
         2 * (qy * qz - qx * qw)),
        (2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw),
         1 - 2 * (qx * qx + qy * qy)),
    )


def minimum_pair_distance(point_set: ColoredPointSet) -> float:
    best = math.inf
    for index, left in enumerate(point_set.positions):
        for right in point_set.positions[index + 1:]:
            best = min(best, _norm(_sub(left, right)))
    return best


def radial_core_annulus_split(
    point_set: ColoredPointSet,
    core_fraction: float = 0.7,
    center: Optional[Vector] = None,
) -> RadialSplit:
    """Hide an outer radial annulus, retaining whole equal-radius shells.

    ``core_fraction`` selects the closest available shell boundary rather than
    splitting symmetry-equivalent atoms at the same radius.
    """
    if not 0.0 < core_fraction < 1.0:
        raise ValueError("core_fraction must be strictly between zero and one")
    if center is None:
        count = len(point_set.positions)
        center = tuple(sum(point[axis] for point in point_set.positions) / count
                       for axis in range(3))  # type: ignore[assignment]
    distances = tuple(_norm(_sub(point, center)) for point in point_set.positions)
    shells = sorted(set(round(value, 12) for value in distances))
    target = max(1, min(len(distances) - 1,
                        round(core_fraction * len(distances))))
    candidates = []
    for shell in shells[:-1]:
        inside = sum(value <= shell + 1e-11 for value in distances)
        if inside < len(distances):
            candidates.append((abs(inside - target), shell))
    if not candidates:
        raise ValueError("point set has no nontrivial radial split")
    radius = min(candidates)[1]
    core = tuple(index for index, value in enumerate(distances)
                 if value <= radius + 1e-11)
    annulus = tuple(index for index, value in enumerate(distances)
                    if value > radius + 1e-11)
    return RadialSplit(center, radius, core, annulus)


def crystalline_control(
    shell_radius: int = 4,
    spacing: float = 2.35,
    seed: int = 11,
) -> ColoredPointSet:
    """A randomly oriented and translated binary simple-cubic control."""
    if shell_radius < 2 or spacing <= 0:
        raise ValueError("shell_radius >= 2 and spacing > 0 are required")
    rng = random.Random(seed)
    rotation = random_rotation(rng)
    translation = tuple(rng.uniform(-3.0, 3.0) for _ in range(3))
    positions = []
    species = []
    source_sites = []
    for x in range(-shell_radius, shell_radius + 1):
        for y in range(-shell_radius, shell_radius + 1):
            for z in range(-shell_radius, shell_radius + 1):
                if x * x + y * y + z * z > shell_radius * shell_radius:
                    continue
                source = (x, y, z)
                cartesian = _scale(spacing, source)
                positions.append(_add(_matvec(rotation, cartesian), translation))
                species.append("Na" if (x + y + z) % 2 == 0 else "Cl")
                source_sites.append(source)
    return ColoredPointSet(
        "rotated-binary-crystal", tuple(positions), tuple(species),
        metadata={
            "family": "crystalline_control",
            "rotation": rotation,
            "translation": translation,
            "spacing": spacing,
            "source_sites": tuple(source_sites),
            "generator_lattice_used_only_for_scoring": True,
        })


def _tetrahedral_template(bond_length: float) -> Tuple[Tuple[str, Vector], ...]:
    factor = bond_length / math.sqrt(3.0)
    return (
        ("Si", (0.0, 0.0, 0.0)),
        ("O", _scale(factor, (1.0, 1.0, 1.0))),
        ("O", _scale(factor, (1.0, -1.0, -1.0))),
        ("O", _scale(factor, (-1.0, 1.0, -1.0))),
        ("O", _scale(factor, (-1.0, -1.0, 1.0))),
    )


def overlapping_motif_point_set(
    occurrence_count: int = 64,
    bond_length: float = 1.62,
    min_distance: float = 0.72,
    seed: int = 23,
) -> ColoredPointSet:
    """A non-lattice network of randomly oriented, corner-sharing SiO4 motifs.

    Every occurrence after the first shares one oxygen with an earlier motif.
    Independent SO(3) orientations make the resulting cover non-periodic and
    not tied to any lattice.  Collision rejection enforces a global hard core.
    """
    if occurrence_count < 2 or bond_length <= min_distance or min_distance <= 0:
        raise ValueError("invalid motif-network dimensions")
    rng = random.Random(seed)
    template = _tetrahedral_template(bond_length)
    positions: list[Vector] = []
    species: list[str] = []
    occurrences: list[MotifOccurrence] = []
    # (global oxygen atom, occurrence that introduced it)
    frontier: list[Tuple[int, int]] = []

    for occurrence_index in range(occurrence_count):
        accepted = False
        for _ in range(4000):
            rotation = random_rotation(rng)
            shared_atom = None
            parent = None
            shared_local = None
            if occurrence_index == 0:
                translation = (0.0, 0.0, 0.0)
            else:
                shared_atom, parent = frontier[rng.randrange(len(frontier))]
                shared_local = rng.randrange(1, len(template))
                translation = _sub(
                    positions[shared_atom],
                    _matvec(rotation, template[shared_local][1]))
            candidate_positions = [
                _add(_matvec(rotation, local), translation)
                for _, local in template
            ]
            valid = True
            for local_index, candidate in enumerate(candidate_positions):
                if local_index == shared_local:
                    continue
                if any(_norm(_sub(candidate, existing)) < min_distance - 1e-10
                       for existing in positions):
                    valid = False
                    break
                if any(_norm(_sub(candidate, other)) < min_distance - 1e-10
                       for other_index, other in enumerate(candidate_positions)
                       if other_index != local_index):
                    valid = False
                    break
            if not valid:
                continue

            atom_indices = []
            for local_index, ((chemical, _), point) in enumerate(
                    zip(template, candidate_positions)):
                if local_index == shared_local:
                    assert shared_atom is not None
                    atom_indices.append(shared_atom)
                else:
                    atom_indices.append(len(positions))
                    positions.append(point)
                    species.append(chemical)
            occurrences.append(MotifOccurrence(
                "SiO4", tuple(atom_indices), rotation, translation, parent,
                shared_atom))
            # Each newly introduced oxygen can seed a later corner-sharing motif.
            for local_index in range(1, len(template)):
                if local_index != shared_local:
                    frontier.append((atom_indices[local_index], occurrence_index))
            if shared_atom is not None:
                # Prefer a branching tree over repeatedly using one corner.
                try:
                    frontier.remove((shared_atom, parent))  # type: ignore[arg-type]
                except ValueError:
                    pass
            accepted = True
            break
        if not accepted:
            raise RuntimeError(
                f"could place only {occurrence_index} of {occurrence_count} motifs")

    return ColoredPointSet(
        "aperiodic-overlapping-SiO4-cover", tuple(positions), tuple(species),
        motif_templates={"SiO4": template},
        motif_occurrences=tuple(occurrences),
        metadata={
            "family": "non_lattice_overlapping_cover",
            "minimum_distance": min_distance,
            "construction": "randomly oriented corner-sharing motif tree",
            "lattice": None,
        })


def amorphous_hard_core_point_set(
    atom_count: int = 300,
    radius: float = 5.5,
    min_distance: float = 0.72,
    seed: int = 37,
) -> ColoredPointSet:
    """Uniform rejection-sampled hard-core points with independent colors."""
    if atom_count < 2 or radius <= 0 or min_distance <= 0:
        raise ValueError("invalid amorphous point-set dimensions")
    rng = random.Random(seed)
    positions: list[Vector] = []
    attempts = 0
    maximum_attempts = atom_count * 20000
    while len(positions) < atom_count and attempts < maximum_attempts:
        attempts += 1
        candidate = tuple(rng.uniform(-radius, radius) for _ in range(3))
        if _norm(candidate) > radius:
            continue
        if all(_norm(_sub(candidate, point)) >= min_distance
               for point in positions):
            positions.append(candidate)  # type: ignore[arg-type]
    if len(positions) != atom_count:
        raise RuntimeError(f"placed only {len(positions)} of {atom_count} atoms")
    palette = ("Cu", "Zr", "Al")
    weights = (0.50, 0.40, 0.10)
    species = tuple(rng.choices(palette, weights=weights, k=atom_count))
    return ColoredPointSet(
        "amorphous-hard-core-null", tuple(positions), species,
        metadata={
            "family": "amorphous_null",
            "minimum_distance": min_distance,
            "sampling_radius": radius,
            "accepted_after_attempts": attempts,
            "planted_motifs": False,
            "lattice": None,
        })


def benchmark_suite() -> Tuple[ColoredPointSet, ...]:
    return (crystalline_control(), overlapping_motif_point_set(),
            amorphous_hard_core_point_set())


if __name__ == "__main__":
    for sample in benchmark_suite():
        split = radial_core_annulus_split(sample)
        print(f"{sample.name}: atoms={len(sample.positions)}, "
              f"species={len(set(sample.species))}, "
              f"min_distance={minimum_pair_distance(sample):.6f}, "
              f"core={len(split.core_indices)}, "
              f"annulus={len(split.annulus_indices)}, "
              f"motifs={len(sample.motif_occurrences)}")
