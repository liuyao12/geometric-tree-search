#!/usr/bin/env python3
"""Deterministic regressions for the learned-cover scaling benchmark."""

import unittest

from materials_cover_scaling_benchmark import (
    _instance,
    run_exact_bounded,
    run_greedy,
    train_radius_two_ranker,
)


class MaterialsCoverScalingBenchmarkTest(unittest.TestCase):
    def test_radius_two_instance_summary_is_lattice_free_and_stable(self) -> None:
        _, summary = _instance(2)

        self.assertEqual(summary.atoms, 33)
        self.assertEqual(summary.learned_types, 5)
        self.assertEqual(summary.occurrences, 33)
        self.assertEqual(summary.support_size_histogram, {7: 15, 10: 6, 12: 12})
        self.assertEqual(summary.sound_lower_bound, 3)
        self.assertEqual(summary.duplicate_supports, 0)
        self.assertEqual(summary.dominated_occurrences, 0)

    def test_radius_two_greedy_is_a_nonoptimal_six_cluster_cover(self) -> None:
        result = run_greedy(2)

        self.assertTrue(result.completed)
        self.assertFalse(result.optimal)
        self.assertEqual(result.selected_occurrences, 6)
        self.assertEqual(result.total_cost, 6.0)
        self.assertEqual(result.expanded_nodes, 6)

    def test_bounded_radius_two_gcts_still_certifies_optimum(self) -> None:
        result = run_exact_bounded(
            2,
            timeout_seconds=5.0,
            method="frontier_memo_gcts",
            solve_kwargs={
                "frontier_memo": True,
                "max_expanded_nodes": 500,
            },
        )

        self.assertTrue(result.completed)
        self.assertTrue(result.optimal)
        self.assertEqual(result.termination, "completed")
        self.assertEqual(result.selected_occurrences, 4)
        self.assertEqual(result.total_cost, 4.0)
        self.assertEqual(result.expanded_nodes, 44)
        self.assertEqual(result.memo_hits, 14)
        self.assertEqual(result.backtracks, 4)

    def test_radius_two_imitation_improves_radius_three_incumbent(self) -> None:
        ranker, training = train_radius_two_ranker(epochs=10)
        self.assertEqual(training.teacher_optimal_cost, 4.0)
        self.assertEqual(training.teacher_contexts, 10)
        self.assertEqual(training.teacher_examples, 37)
        self.assertEqual(training.informative_contexts, 6)

        ordinary = run_exact_bounded(
            3,
            timeout_seconds=5.0,
            method="unguided_gcts",
            solve_kwargs={
                "frontier_memo": False,
                "max_expanded_nodes": 100,
            },
        )
        ranked = run_exact_bounded(
            3,
            timeout_seconds=5.0,
            method="ranked_gcts",
            solve_kwargs={
                "frontier_memo": False,
                "max_expanded_nodes": 100,
            },
            ranker_weights=ranker.weights,
        )

        self.assertFalse(ordinary.optimal)
        self.assertFalse(ranked.optimal)
        self.assertEqual(ordinary.expanded_nodes, ranked.expanded_nodes)
        self.assertEqual(ordinary.total_cost, 14.0)
        self.assertEqual(ranked.total_cost, 13.0)


if __name__ == "__main__":
    unittest.main()
