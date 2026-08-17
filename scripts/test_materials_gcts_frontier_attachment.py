#!/usr/bin/env python3

import math
import unittest
from collections import Counter

from materials_gcts_frontier_attachment import (
    FrontierAttachmentExample, describe_frontier_attachments,
    fit_frontier_attachment_marker_examples, score_frontier_attachments)
from materials_gcts_frontier_attachment_benchmark import evaluate
from materials_gcts_recursive_connections import MarkedProposalResult


class FrontierAttachmentTest(unittest.TestCase):
    def test_multiple_configurations_share_one_invariant_marker(self):
        def fixture(offset):
            candidates = ((offset + 1., 0., 0.), (offset + 2., 0., 0.))
            votes = Counter({point: 2 for point in candidates})
            colors = {point: Counter({"'A'": 2}) for point in candidates}
            proposals = MarkedProposalResult(
                votes, 4, None, colors, colors,
                {point: Counter() for point in candidates},
                {point: Counter() for point in candidates})
            known = ((offset, 0., 0.), (offset, 1., 0.))
            return proposals, known, ("A", "A"), (candidates[0],)

        fixtures = (fixture(0.), fixture(10.))
        marker = fit_frontier_attachment_marker_examples(tuple(
            FrontierAttachmentExample(
                proposal, known, colors, targets)
            for proposal, known, colors, targets in fixtures))
        self.assertEqual(marker.training_examples, 4)
        self.assertEqual(marker.training_positives, 2)
        scores = [score_frontier_attachments(
            marker, proposal, known, colors)
                  for proposal, known, colors, _targets in fixtures]
        self.assertAlmostEqual(tuple(scores[0].values())[0],
                               tuple(scores[1].values())[0])
        self.assertAlmostEqual(tuple(scores[0].values())[1],
                               tuple(scores[1].values())[1])

    def test_descriptor_is_rigid_motion_invariant(self):
        votes = Counter({(1., 1., 0.): 3, (2., 0., 0.): 2})
        colors = {point: Counter({"'A'": count})
                  for point, count in votes.items()}
        proposals = MarkedProposalResult(
            votes, sum(votes.values()), None, colors, colors,
            {point: Counter() for point in votes},
            {point: Counter() for point in votes})
        known = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
        known_colors = ("A", "B", "A")
        angle = .63

        def transform(point):
            x, y, z = point
            return (round(math.cos(angle) * x - math.sin(angle) * y + 3., 6),
                    round(math.sin(angle) * x + math.cos(angle) * y - 2., 6),
                    round(z + 1., 6))

        moved_votes = Counter({transform(point): count
                               for point, count in votes.items()})
        moved_colors = {transform(point): value
                        for point, value in colors.items()}
        moved = MarkedProposalResult(
            moved_votes, sum(moved_votes.values()), None,
            moved_colors, moved_colors,
            {point: Counter() for point in moved_votes},
            {point: Counter() for point in moved_votes})
        original = describe_frontier_attachments(
            proposals, known, known_colors, (1.4, 2.1, 3.0))
        transformed = describe_frontier_attachments(
            moved, tuple(map(transform, known)), known_colors, (1.4, 2.1, 3.0))
        for left, right in zip(sorted(original.values()),
                               sorted(transformed.values())):
            self.assertEqual(len(left), len(right))
            for first, second in zip(left, right):
                self.assertAlmostEqual(first, second, places=5)

    def test_iterated_maximum_plateaus_are_exact_macro_moves(self):
        result = evaluate()
        self.assertEqual(result.atom_counts, (507, 1969, 8603))
        self.assertFalse(result.trained_on_heldout_labels)
        self.assertTrue(result.rigid_motion_invariant_descriptor)
        waves = result.iterative_growth_waves
        self.assertEqual(len(waves), 8)
        self.assertTrue(all(wave.false_sites == 0 for wave in waves))
        self.assertEqual(waves[-1].cumulative_sites, 208)
        self.assertEqual(waves[-1].cumulative_precision, 1.0)
        self.assertGreaterEqual(max(wave.plateau_sites for wave in waves), 100)
        regenerative = result.regenerative_growth_waves
        self.assertEqual(len(regenerative), 8)
        self.assertTrue(all(wave.false_sites == 0 for wave in regenerative))
        self.assertEqual(regenerative[-1].cumulative_sites, 228)
        self.assertGreater(regenerative[-1].frontier_candidates,
                           regenerative[0].frontier_candidates)
        self.assertGreaterEqual(max(wave.plateau_sites
                                    for wave in regenerative), 100)
        diagnostics = {point.site_budget: point
                       for point in result.diagnostic_operating_points}
        self.assertGreater(diagnostics[500].precision, .95)


if __name__ == "__main__":
    unittest.main()
