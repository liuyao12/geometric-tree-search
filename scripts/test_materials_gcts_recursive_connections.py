#!/usr/bin/env python3

import math
import unittest

from materials_gcts_recursive_connection_benchmark import evaluate
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types,
    propose_with_recursive_marking)


class RecursiveConnectionMarkingTest(unittest.TestCase):
    def test_connection_marking_is_rigid_motion_invariant(self):
        points = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (1., 1., 0.))
        colors = ("A", "B", "B", "A")
        target = tuple((2 * x, 2 * y, z) for x, y, z in points)
        types = local_cluster_types(points, colors, (.75, 1.1, 1.5))
        marker = learn_recursive_connection_marking(
            points, types, target, 2., minimum_positive_support=1)
        angle = .71
        moved = tuple((math.cos(angle) * x - math.sin(angle) * y + 3.,
                       math.sin(angle) * x + math.cos(angle) * y - 2., z + 1.)
                      for x, y, z in points)
        moved_types = local_cluster_types(moved, colors, (.75, 1.1, 1.5))
        original = propose_with_recursive_marking(marker, points, types)
        transformed = propose_with_recursive_marking(marker, moved, moved_types)
        self.assertEqual(original.accepted_pair_actions,
                         transformed.accepted_pair_actions)
        self.assertEqual(sorted(original.votes.values()),
                         sorted(transformed.votes.values()))
        self.assertIsNotNone(original.pair_actions)
        self.assertIsNotNone(transformed.pair_actions)
        self.assertEqual(sum(map(len, original.pair_actions.values())),
                         original.accepted_pair_actions)
        self.assertEqual(
            sorted((action.parent_index, action.source_index, action.state)
                   for actions in original.pair_actions.values()
                   for action in actions),
            sorted((action.parent_index, action.source_index, action.state)
                   for actions in transformed.pair_actions.values()
                   for action in actions))

    def test_frozen_ideal_iqc_marking_recovers_most_next_level(self):
        result = evaluate()
        self.assertTrue(result.scale_inferred_from_seed_only)
        self.assertLess(result.scale_absolute_error, 2e-6)
        self.assertGreater(min(result.one_level_distance_closure,
                               result.two_level_distance_closure), .5)
        self.assertEqual(result.atom_counts, (507, 1969, 8603))
        self.assertFalse(result.trained_on_heldout_labels)
        self.assertFalse(result.lattice_coordinates_used)
        self.assertFalse(result.physical_potential_used)
        self.assertGreater(result.marked_coverage, .95)
        by_votes = {point.minimum_votes: point
                    for point in result.operating_points}
        self.assertEqual(result.known_sites_excluded, 1969)
        self.assertEqual(result.novel_target_sites, 6634)
        self.assertGreater(by_votes[8].precision, .50)
        self.assertGreater(by_votes[2].coverage, .85)
        self.assertLess(by_votes[16].false_sites, 200)


if __name__ == "__main__":
    unittest.main()
