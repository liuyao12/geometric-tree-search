#!/usr/bin/env python3
"""Invariant checks for the recorded Hat online-memo demonstration."""

from __future__ import annotations

import argparse
import unittest

from hat_online_memo_demo import run_demo


class HatOnlineMemoDemoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = run_demo(
            argparse.Namespace(
                target_tiles=16,
                frontier_limit=10,
                candidate_limit=14,
                max_lattice_reach=4,
                channels=3,
                policy="random",
                seed=23,
                wall_time_ms=30000,
                output="unused.json",
            )
        )

    def test_starts_with_a_literal_empty_marking(self) -> None:
        first = self.payload["trace"][0]
        self.assertEqual(first["type"], "start")
        self.assertEqual(first["support"], [])
        self.assertEqual(first["marking"]["site_fore"], [])

    def test_demo_exercises_learning_and_reuse(self) -> None:
        summary = self.payload["summary"]
        self.assertEqual(summary["stopped_reason"], "target_tiles")
        self.assertGreater(summary["learned_failures"], 0)
        self.assertGreater(summary["memo_hits"], 0)
        self.assertLess(summary["physical_support_sites"], 12)

    def test_every_committed_update_replays_the_prefix(self) -> None:
        committed = [event for event in self.payload["trace"] if event["type"] == "memoized"]
        self.assertTrue(committed)
        for event in committed:
            diagnostics = event["learning"]["diagnostics"]
            self.assertTrue(diagnostics["assignment_satisfied"])
            self.assertTrue(diagnostics["accepted_replay"])
            self.assertEqual(diagnostics["memoized_failures"], event["learned_failures"])

    def test_final_marking_rejects_every_memoized_failure(self) -> None:
        validation = self.payload["summary"]["final_validation"]
        self.assertTrue(self.payload["summary"]["valid"])
        self.assertTrue(validation["accepted_replay"])
        self.assertEqual(validation["missed_failures"], [])
        self.assertEqual(validation["memoized_failures"], self.payload["summary"]["learned_failures"])


if __name__ == "__main__":
    unittest.main()
