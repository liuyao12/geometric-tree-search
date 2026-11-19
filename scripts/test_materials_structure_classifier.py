#!/usr/bin/env python3

import itertools
import math
import random
import unittest

from materials_pointset_benchmarks import (
    amorphous_hard_core_point_set,
    crystalline_control,
)
from materials_structure_classifier import evaluate_structure


def fibonacci_product(side=8):
    """Exact product of three finite Fibonacci substitution axes."""
    word = "A"
    while len(word) < side:
        word = "".join("AB" if symbol == "A" else "A" for symbol in word)
    word = word[:side]
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    coordinates = [0.0]
    for symbol in word[:side - 1]:
        coordinates.append(coordinates[-1] + (phi if symbol == "A" else 1.0))
    positions = []
    species = []
    for i, j, k in itertools.product(range(side), repeat=3):
        positions.append((coordinates[i], coordinates[j], coordinates[k]))
        parity = sum(word[index] == "B" for index in (i, j, k)) % 2
        species.append("A" if parity == 0 else "B")
    return tuple(positions), tuple(species)


def icosahedral_model_set(lift_bound=3, physical_radius=9.0):
    """Small exact 6-D cut-and-project control with three colors."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0

    def star_vectors(unit):
        return ((1.0, unit, 0.0), (-1.0, unit, 0.0),
                (0.0, 1.0, unit), (0.0, -1.0, unit),
                (unit, 0.0, 1.0), (unit, 0.0, -1.0))

    def project(lift, vectors):
        return tuple(sum(lift[index] * vectors[index][axis]
                         for index in range(6)) for axis in range(3))

    physical_vectors = star_vectors(phi)
    internal_vectors = star_vectors(-1.0 / phi)
    positions = []
    species = []
    for lift in itertools.product(range(-lift_bound, lift_bound + 1), repeat=6):
        physical = project(lift, physical_vectors)
        internal = project(lift, internal_vectors)
        physical_norm = math.sqrt(sum(value * value for value in physical))
        internal_norm = math.sqrt(sum(value * value for value in internal))
        if physical_norm <= physical_radius + 1e-10 and internal_norm <= 1.5 + 1e-10:
            positions.append(physical)
            species.append("X" if internal_norm < 0.75 else
                           ("Y" if internal_norm < 1.125 else "Z"))
    return tuple(positions), tuple(species)


def cubic_cell(repeats=4, spacing=2.0):
    positions = []
    species = []
    fractional = []
    for x in range(repeats):
        for y in range(repeats):
            for z in range(repeats):
                positions.append((spacing * x, spacing * y, spacing * z))
                species.append("Na" if (x + y + z) % 2 == 0 else "Cl")
                fractional.append((x / repeats, y / repeats, z / repeats))
    cell = ((spacing * repeats, 0.0, 0.0),
            (0.0, spacing * repeats, 0.0),
            (0.0, 0.0, spacing * repeats))
    return positions, species, fractional, cell


class StructureClassifierTests(unittest.TestCase):
    def test_rotated_spherical_binary_crystal_is_boundary_aware(self):
        sample = crystalline_control(shell_radius=4, seed=91)
        result = evaluate_structure(sample.positions, sample.species)
        self.assertEqual(result.category, "crystal")
        self.assertEqual(result.independent_translation_count, 3)
        self.assertGreater(result.translation_periodicity, 0.85)
        self.assertEqual(result.space_group.status, "cell-required")

    def test_small_position_noise_preserves_crystal_class(self):
        sample = crystalline_control(shell_radius=4, seed=92)
        rng = random.Random(12)
        noisy = [tuple(value + rng.gauss(0.0, 0.025) for value in point)
                 for point in sample.positions]
        result = evaluate_structure(noisy, sample.species)
        self.assertEqual(result.category, "crystal")
        self.assertGreaterEqual(result.independent_translation_count, 3)

    def test_hard_core_random_control_is_not_given_space_group(self):
        sample = amorphous_hard_core_point_set(atom_count=260, seed=419)
        result = evaluate_structure(sample.positions, sample.species)
        self.assertEqual(result.category, "amorphous")
        self.assertEqual(result.space_group.status, "not-applicable")
        self.assertLess(result.independent_translation_count, 3)

    def test_icosahedral_model_set_is_only_a_quasicrystal_candidate(self):
        positions, species = icosahedral_model_set()
        result = evaluate_structure(positions, species)
        self.assertEqual(result.category, "quasicrystal-candidate")
        self.assertEqual(result.independent_translation_count, 0)
        self.assertGreater(result.local_environment_recurrence, 0.8)
        self.assertEqual(result.space_group.status, "not-applicable")
        self.assertTrue(any("superspace" in caveat
                            for caveat in result.caveats))

    def test_fibonacci_product_short_translation_does_not_imply_lattice(self):
        # This finite product has three frequent axial displacements, each
        # matching about 82% of atoms.  They are not translations: composing
        # any one with itself drops the match sharply.
        positions, species = fibonacci_product(8)
        result = evaluate_structure(positions, species)
        self.assertEqual(len(positions), 512)
        self.assertEqual(result.category, "quasicrystal-candidate")
        self.assertGreater(result.translation_periodicity, 0.75)
        self.assertLess(result.translation_closure, 0.35)
        self.assertTrue(any("composition" in reason
                            for reason in result.reasons))

    def test_two_oriented_grains_are_polycrystal_like(self):
        left = crystalline_control(shell_radius=3, seed=1)
        right = crystalline_control(shell_radius=3, seed=2)
        positions = ([(point[0] - 10.0, point[1], point[2])
                      for point in left.positions] +
                     [(point[0] + 10.0, point[1], point[2])
                      for point in right.positions])
        species = left.species + right.species
        result = evaluate_structure(positions, species)
        self.assertEqual(result.category, "polycrystal-like")
        self.assertGreaterEqual(result.localized_translation_count, 2)
        self.assertEqual(result.space_group.status, "not-applicable")

    def test_species_are_part_of_translation_matching(self):
        sample = crystalline_control(shell_radius=4, seed=95)
        rng = random.Random(33)
        shuffled = list(sample.species)
        rng.shuffle(shuffled)
        ordered = evaluate_structure(sample.positions, sample.species)
        recolored = evaluate_structure(sample.positions, shuffled)
        self.assertGreater(ordered.translation_periodicity,
                           recolored.translation_periodicity + 0.25)

    def test_spglib_is_optional_and_tolerance_audited(self):
        positions, species, fractional, cell = cubic_cell()
        result = evaluate_structure(positions, species, cell=cell,
                                    fractional_positions=fractional)
        if result.space_group.status == "spglib-unavailable":
            self.assertIsNone(result.space_group.number)
        else:
            self.assertIn(result.space_group.status,
                          {"stable", "tolerance-sensitive"})
            self.assertIsNotNone(result.space_group.number)
            self.assertEqual(len(result.space_group.tolerance_labels), 5)

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_structure([(0.0, 0.0, 0.0)] * 15, ["X"] * 15)
        positions, species, _, _ = cubic_cell()
        with self.assertRaises(ValueError):
            evaluate_structure(positions, species[:-1])


if __name__ == "__main__":
    unittest.main()
