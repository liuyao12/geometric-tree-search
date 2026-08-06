#!/usr/bin/env python3

import math
import unittest

from materials_pointset_benchmarks import (
    amorphous_hard_core_point_set,
    crystalline_control,
    minimum_pair_distance,
    overlapping_motif_point_set,
    radial_core_annulus_split,
)


def matvec(matrix, vector):
    return tuple(sum(row[column] * vector[column] for column in range(3))
                 for row in matrix)


def add(left, right):
    return tuple(a + b for a, b in zip(left, right))


class PointSetBenchmarkTests(unittest.TestCase):
    def test_crystal_transform_and_coloring(self):
        sample = crystalline_control(shell_radius=4, seed=101)
        self.assertGreaterEqual(len(sample.positions), 200)
        self.assertEqual(set(sample.species), {"Na", "Cl"})
        rotation = sample.metadata["rotation"]
        translation = sample.metadata["translation"]
        spacing = sample.metadata["spacing"]
        source_sites = sample.metadata["source_sites"]
        for row_index, row in enumerate(rotation):
            for other_index, other in enumerate(rotation):
                dot = sum(a * b for a, b in zip(row, other))
                self.assertAlmostEqual(dot, float(row_index == other_index), places=12)
        for site, actual in zip(source_sites, sample.positions):
            expected = add(matvec(rotation,
                                  tuple(spacing * value for value in site)),
                           translation)
            self.assertLess(math.dist(expected, actual), 1e-11)
        self.assertAlmostEqual(minimum_pair_distance(sample), spacing, places=10)

    def test_overlapping_non_lattice_cover_ground_truth(self):
        sample = overlapping_motif_point_set(occurrence_count=64, seed=202)
        self.assertEqual(len(sample.motif_occurrences), 64)
        self.assertEqual(len(sample.positions), 1 + 4 * 64)
        self.assertIsNone(sample.metadata["lattice"])
        template = sample.motif_templates["SiO4"]
        shared = 0
        rounded_rotations = set()
        for index, occurrence in enumerate(sample.motif_occurrences):
            self.assertEqual(len(set(occurrence.atom_indices)), len(template))
            rounded_rotations.add(tuple(round(value, 5)
                                        for row in occurrence.rotation for value in row))
            for atom_index, (chemical, local) in zip(occurrence.atom_indices,
                                                     template):
                expected = add(matvec(occurrence.rotation, local),
                               occurrence.translation)
                self.assertEqual(sample.species[atom_index], chemical)
                self.assertLess(math.dist(expected, sample.positions[atom_index]),
                                1e-10)
            if index:
                shared += 1
                self.assertIsNotNone(occurrence.shared_atom)
                parent_atoms = sample.motif_occurrences[
                    occurrence.parent_occurrence].atom_indices
                self.assertIn(occurrence.shared_atom, occurrence.atom_indices)
                self.assertIn(occurrence.shared_atom, parent_atoms)
        self.assertEqual(shared, 63)
        self.assertGreater(len(rounded_rotations), 60)
        self.assertGreaterEqual(minimum_pair_distance(sample), 0.72 - 1e-10)

    def test_amorphous_is_deterministic_and_hard_core(self):
        first = amorphous_hard_core_point_set(atom_count=300, seed=303)
        second = amorphous_hard_core_point_set(atom_count=300, seed=303)
        self.assertEqual(first.positions, second.positions)
        self.assertEqual(first.species, second.species)
        self.assertEqual(len(first.positions), 300)
        self.assertGreaterEqual(minimum_pair_distance(first), 0.72 - 1e-10)
        self.assertFalse(first.metadata["planted_motifs"])
        self.assertFalse(first.motif_occurrences)

    def test_radial_splits_are_complete_disjoint_and_geometric(self):
        for sample in (crystalline_control(), overlapping_motif_point_set(),
                       amorphous_hard_core_point_set()):
            split = radial_core_annulus_split(sample, core_fraction=0.68)
            core = set(split.core_indices)
            annulus = set(split.annulus_indices)
            self.assertTrue(core)
            self.assertTrue(annulus)
            self.assertFalse(core & annulus)
            self.assertEqual(core | annulus, set(range(len(sample.positions))))
            core_radii = [math.dist(sample.positions[index], split.center)
                          for index in core]
            annulus_radii = [math.dist(sample.positions[index], split.center)
                             for index in annulus]
            self.assertLess(max(core_radii), min(annulus_radii) + 1e-10)


if __name__ == "__main__":
    unittest.main()
