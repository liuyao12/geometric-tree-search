#!/usr/bin/env python3
"""Checks for the deterministic, geometry-blind cover curriculum."""

from __future__ import annotations

import unittest
from collections import Counter

from materials_cover_curriculum import FAMILIES, build_cover_curriculum


def _fingerprint(case):
    problem = case.problem
    return (
        case.metadata,
        tuple(sorted(map(repr, problem.universe))),
        tuple(
            (repr(item.id), tuple(sorted(map(repr, item.covers))), item.cost)
            for item in problem.occurrences
        ),
    )


class CoverCurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.curriculum = build_cover_curriculum(
            train_per_family=2, test_per_family=1)

    def test_splits_are_deterministic_and_seed_disjoint(self) -> None:
        repeat = build_cover_curriculum(train_per_family=2, test_per_family=1)
        self.assertEqual(
            tuple(map(_fingerprint, self.curriculum.all_cases)),
            tuple(map(_fingerprint, repeat.all_cases)),
        )
        train_seeds = {case.metadata.seed for case in self.curriculum.train}
        test_seeds = {case.metadata.seed for case in self.curriculum.test}
        self.assertTrue(train_seeds.isdisjoint(test_seeds))
        self.assertTrue(
            {case.metadata.case_id for case in self.curriculum.train}.isdisjoint(
                case.metadata.case_id for case in self.curriculum.test))

    def test_each_split_contains_every_family(self) -> None:
        expected = set(FAMILIES)
        self.assertEqual(
            {case.metadata.family for case in self.curriculum.train}, expected)
        self.assertEqual(
            {case.metadata.family for case in self.curriculum.test}, expected)
        counts = Counter(case.metadata.family for case in self.curriculum.train)
        self.assertEqual(set(counts.values()), {2})

    def test_public_cases_expose_no_geometric_or_lattice_features(self) -> None:
        forbidden = {
            "coordinate", "coordinates", "position", "positions", "rotation",
            "lattice", "unit_cell", "species", "source_sites",
        }
        for case in self.curriculum.all_cases:
            self.assertFalse(hasattr(case, "point_set"))
            self.assertFalse(hasattr(case.problem, "positions"))
            exposed_feature_names = {
                name.lower() for name in case.metadata.policy_features
            } | {name.lower() for name, _ in case.metadata.parameters}
            self.assertTrue(forbidden.isdisjoint(exposed_feature_names))
            self.assertEqual(
                set(case.metadata.policy_features),
                {"cover_supports", "occurrence_costs", "pair_constraints",
                 "marked_frontier_state"},
            )

    def test_all_cases_are_small_and_exactly_solvable(self) -> None:
        for case in self.curriculum.all_cases:
            with self.subTest(case=case.metadata.case_id):
                self.assertLessEqual(len(case.problem.universe), 40)
                self.assertLessEqual(len(case.problem.occurrences), 40)
                result = case.problem.solve(max_expanded_nodes=20_000)
                self.assertTrue(result.complete)
                self.assertTrue(result.optimal)
                self.assertLess(result.expanded_nodes, 20_000)

    def test_every_family_contains_overlapping_candidate_supports(self) -> None:
        for family in FAMILIES:
            case = next(item for item in self.curriculum.train
                        if item.metadata.family == family)
            supports = [item.covers for item in case.problem.occurrences]
            self.assertTrue(any(
                left & right
                for index, left in enumerate(supports)
                for right in supports[index + 1:]
            ), family)

    def test_non_lattice_optimum_really_uses_overlap(self) -> None:
        case = next(item for item in self.curriculum.train
                    if item.metadata.family == "non_lattice_motifs")
        result = case.problem.solve()
        by_id = {item.id: item for item in case.problem.occurrences}
        memberships = Counter(
            object_id
            for occurrence_id in result.selected
            for object_id in by_id[occurrence_id].covers
        )
        self.assertGreater(sum(count > 1 for count in memberships.values()), 0)

    def test_delayed_conflict_traps_greedy_but_not_gcts(self) -> None:
        case = next(item for item in self.curriculum.train
                    if item.metadata.family == "delayed_conflict")
        greedy = case.problem.greedy()
        exact = case.problem.solve()
        self.assertFalse(greedy.complete)
        self.assertEqual(greedy.selected[0], "tempting")
        self.assertGreater(len(greedy.selected), 1)
        self.assertTrue(exact.complete)
        self.assertTrue(exact.optimal)
        self.assertNotIn("tempting", exact.selected)

    def test_invalid_split_sizes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_cover_curriculum(train_per_family=0)
        with self.assertRaises(ValueError):
            build_cover_curriculum(test_per_family=0)


if __name__ == "__main__":
    unittest.main()
