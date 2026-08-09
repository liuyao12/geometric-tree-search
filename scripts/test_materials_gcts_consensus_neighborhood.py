#!/usr/bin/env python3

import math
import unittest
from collections import Counter

from materials_gcts_consensus_neighborhood import (
    describe_consensus_neighborhoods)
from materials_gcts_consensus_neighborhood_benchmark import evaluate


class ConsensusNeighborhoodTest(unittest.TestCase):
    def test_descriptor_is_rigid_motion_invariant(self):
        votes = Counter({
            (0., 0., 0.): 5,
            (1., 0., 0.): 3,
            (0., 1., 0.): 2,
            (0., 0., 1.): 1,
        })
        angle = .73
        transformed = Counter({
            (round(math.cos(angle) * x - math.sin(angle) * y + 4., 6),
             round(math.sin(angle) * x + math.cos(angle) * y - 3., 6),
             round(z + 2., 6)): count
            for (x, y, z), count in votes.items()})
        original_descriptors = describe_consensus_neighborhoods(
            votes, (.8, 1.4, 2.1))
        transformed_descriptors = describe_consensus_neighborhoods(
            transformed, (.8, 1.4, 2.1))
        self.assertEqual(sorted(original_descriptors.values()),
                         sorted(transformed_descriptors.values()))

    def test_second_order_marking_beats_vote_ranking_at_fixed_budgets(self):
        result = evaluate()
        self.assertEqual(result.atom_counts, (507, 1969, 8603))
        self.assertFalse(result.trained_on_heldout_labels)
        self.assertTrue(result.second_order_marking)
        self.assertTrue(result.rigid_motion_invariant_descriptor)
        self.assertEqual(result.predicted_next_atom_count, 5678)
        by_budget = {point.budget_multiplier: point
                     for point in result.budget_operating_points}
        strict = by_budget[.5]
        self.assertGreater(strict.second_order_precision,
                           strict.vote_only_precision)
        self.assertGreater(strict.second_order_coverage,
                           strict.vote_only_coverage)
        normal = by_budget[1.]
        self.assertGreater(normal.ensemble_precision,
                           normal.vote_only_precision)
        self.assertGreater(normal.ensemble_coverage,
                           normal.vote_only_coverage)
        exploratory = by_budget[2.]
        self.assertGreater(exploratory.binned_second_order_precision,
                           exploratory.vote_only_precision)
        self.assertGreater(exploratory.binned_second_order_coverage,
                           exploratory.vote_only_coverage)


if __name__ == "__main__":
    unittest.main()
