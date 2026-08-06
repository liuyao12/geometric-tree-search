#!/usr/bin/env python3
"""Regression tests for solver-independent cover branch ranking."""

from __future__ import annotations

import unittest

from materials_cover_ranking import (
    BranchExample,
    DescendantBranchOutcome,
    DescendantRewardConfig,
    FEATURE_NAMES,
    LinearBranchRanker,
    branch_features,
    make_solver_branch_orderer,
    train_from_descendant_outcomes,
    train_from_exact_teacher,
)
from materials_overlap_cover import Occurrence, OverlapCoverProblem


class CoverFeatureTests(unittest.TestCase):
    def test_features_use_only_cover_state_and_constraints(self) -> None:
        selected = [Occurrence("chosen", {0, 1}, 1.0)]
        candidate = Occurrence("wide", {1, 2, 3}, 1.5)
        rival = Occurrence("rival", {2, 4}, 1.0)
        domains = {2: (candidate, rival), 3: (candidate,), 4: (rival,)}

        features = branch_features(
            candidate=candidate,
            uncovered={2, 3, 4},
            covered={0, 1},
            selected=selected,
            domains=domains,
            legal_occurrences=(candidate, rival),
            pair_allowed=lambda left, right: {left.id, right.id} != {"wide", "rival"},
            universe_size=5,
            pivot_domain_size=2,
            selected_cost=1.0,
            incumbent_cost=4.0,
        )

        self.assertEqual(set(features), set(FEATURE_NAMES))
        self.assertAlmostEqual(features["gain_fraction"], 2.0 / 3.0)
        self.assertAlmostEqual(features["overlap_fraction"], 1.0 / 3.0)
        self.assertEqual(features["peer_conflict_fraction"], 1.0)
        self.assertGreater(features["covered_domain_inverse_mean"], 0.5)

    def test_feature_extraction_is_identifier_agnostic(self) -> None:
        def extract(offset: int) -> dict[str, float]:
            a = Occurrence(("a", offset), {offset, offset + 1}, 1.0)
            b = Occurrence(("b", offset), {offset + 1, offset + 2}, 2.0)
            return branch_features(
                candidate=a,
                uncovered={offset, offset + 1, offset + 2},
                covered=set(),
                selected=(),
                domains={offset: (a,), offset + 1: (a, b), offset + 2: (b,)},
                legal_occurrences=(a, b),
                pair_allowed=lambda _left, _right: True,
                universe_size=3,
                pivot_domain_size=2,
            )

        self.assertEqual(extract(0), extract(10_000))


class LinearRankerTests(unittest.TestCase):
    @staticmethod
    def features(gain: float, conflict: float, cost: float) -> dict[str, float]:
        values = {name: 0.0 for name in FEATURE_NAMES}
        values.update(
            bias=1.0,
            gain_fraction=gain,
            log_gain=gain,
            peer_conflict_fraction=conflict,
            cost_per_gain=cost,
        )
        return values

    def test_reward_training_improves_held_out_ranking(self) -> None:
        examples = []
        for context in range(8):
            candidates = (
                ("small-safe", self.features(0.25, 0.0, 0.5)),
                ("large-safe", self.features(0.75, 0.0, 0.5)),
                ("large-blocking", self.features(0.85, 1.0, 0.5)),
            )
            for candidate_id, features in candidates:
                reward = 3.0 * features["gain_fraction"] - 4.0 * features["peer_conflict_fraction"]
                examples.append(BranchExample(context, candidate_id, features, reward))

        held_out = [
            ("a-blocking", self.features(0.90, 1.0, 0.4)),
            ("z-useful", self.features(0.70, 0.0, 0.6)),
            ("m-small", self.features(0.20, 0.0, 0.3)),
        ]
        ranker = LinearBranchRanker()
        before = ranker.rank(held_out)
        ranker.fit(examples, epochs=25)
        after = ranker.rank(held_out)

        self.assertNotEqual(before[0], "z-useful")
        self.assertEqual(after[0], "z-useful")
        self.assertLess(
            ranker.score(held_out[0][1]), ranker.score(held_out[1][1])
        )

    def test_training_and_ties_are_deterministic(self) -> None:
        examples = [
            BranchExample("ctx", "b", self.features(0.8, 0.0, 0.5), 1.0),
            BranchExample("ctx", "a", self.features(0.2, 0.0, 0.5), 0.0),
        ]
        first = LinearBranchRanker().fit(examples)
        second = LinearBranchRanker().fit(reversed(examples))
        self.assertEqual(first.weights, second.weights)
        self.assertEqual(
            LinearBranchRanker().rank([("z", {}), ("a", {})]), ["a", "z"]
        )


class DescendantOutcomeTests(unittest.TestCase):
    @staticmethod
    def features(gain: float, conflict: float) -> dict[str, float]:
        values = {name: 0.0 for name in FEATURE_NAMES}
        values.update(
            bias=1.0,
            gain_fraction=gain,
            log_gain=gain,
            peer_conflict_fraction=conflict,
        )
        return values

    def test_descendant_value_corrects_contextual_membership_mislabel(self) -> None:
        """A global solution member can fail below a different partial state."""

        membership_examples = []
        outcomes = []
        for context in range(12):
            tempting = self.features(0.90, 1.0)
            safe = self.features(0.65, 0.0)

            # Simple final-cover membership calls the tempting occurrence
            # positive because it belongs to one global optimum.  In these
            # partial contexts, however, its contradiction is only discovered
            # after a large descendant search.
            membership_examples.extend(
                (
                    BranchExample(context, "global-member", tempting, 1.0),
                    BranchExample(context, "context-safe", safe, 0.0),
                )
            )
            outcomes.extend(
                (
                    DescendantBranchOutcome(
                        context, "global-member", tempting, False, 0.0, 80
                    ),
                    DescendantBranchOutcome(
                        context, "context-safe", safe, True, 0.4, 5
                    ),
                )
            )

        membership_ranker = LinearBranchRanker().fit(membership_examples)
        report = train_from_descendant_outcomes(outcomes)
        held_out = (
            ("delayed-failure", self.features(0.85, 1.0)),
            ("feasible-subtree", self.features(0.70, 0.0)),
        )

        self.assertEqual(membership_ranker.rank(held_out)[0], "delayed-failure")
        self.assertEqual(report.ranker.rank(held_out)[0], "feasible-subtree")
        self.assertEqual(report.context_count, 12)
        self.assertEqual(report.outcome_count, 24)
        self.assertEqual(report.feasible_outcome_count, 12)
        self.assertEqual(report.improving_outcome_count, 12)
        self.assertLess(report.min_reward, report.max_reward)

    def test_reward_favors_less_descendant_work_at_equal_quality(self) -> None:
        config = DescendantRewardConfig(node_weight=0.25)
        fast = DescendantBranchOutcome("ctx", "fast", {}, True, 0.5, 3)
        slow = DescendantBranchOutcome("ctx", "slow", {}, True, 0.5, 100)
        self.assertGreater(config.reward(fast), config.reward(slow))

    def test_custom_trace_adapter_and_explicit_examples(self) -> None:
        traces = [
            {
                "context": "ctx",
                "candidate": "a",
                "features": self.features(0.7, 0.0),
                "complete": True,
                "gain": 0.2,
                "nodes": 4,
            },
            BranchExample("ctx", "b", self.features(0.8, 1.0), -1.0),
        ]

        def adapter(record):
            if isinstance(record, BranchExample):
                return record
            return DescendantBranchOutcome(
                context_id=record["context"],
                candidate_id=record["candidate"],
                features=record["features"],
                feasible=record["complete"],
                incumbent_improvement=record["gain"],
                descendant_nodes=record["nodes"],
            )

        first = train_from_descendant_outcomes(traces, adapter=adapter)
        second = train_from_descendant_outcomes(reversed(traces), adapter=adapter)
        self.assertEqual(first.ranker.weights, second.ranker.weights)
        self.assertEqual(first.ranker.rank([
            ("a", self.features(0.7, 0.0)),
            ("b", self.features(0.8, 1.0)),
        ])[0], "a")


class TeacherImitationTests(unittest.TestCase):
    @staticmethod
    def problem() -> OverlapCoverProblem:
        return OverlapCoverProblem(
            range(1, 7),
            (
                Occurrence("big", {1, 2, 3, 4}),
                Occurrence("cross-a", {1, 2, 5}),
                Occurrence("cross-b", {3, 4, 6}),
                Occurrence("five", {5}),
                Occurrence("six", {6}),
            ),
        )

    def test_exact_search_produces_policy_examples_and_trains_ranker(self) -> None:
        problem = self.problem()
        report = train_from_exact_teacher(problem)

        self.assertTrue(report.teacher_result.complete)
        self.assertTrue(report.teacher_result.optimal)
        self.assertEqual(
            set(report.teacher_result.selected), {"cross-a", "cross-b"}
        )
        self.assertGreater(report.recorded_context_count, 0)
        self.assertGreater(report.labeled_context_count, 0)
        self.assertGreater(report.example_count, report.positive_example_count)
        self.assertEqual(report.example_count, len(report.examples))
        for context_id in {example.context_id for example in report.examples}:
            rewards = [
                example.reward
                for example in report.examples
                if example.context_id == context_id
            ]
            self.assertIn(1.0, rewards)

        # The learned policy remains only an ordering heuristic: a new exact
        # solve returns the same certified optimum.
        guided = problem.solve(
            branch_orderer=make_solver_branch_orderer(report.ranker)
        )
        self.assertTrue(guided.optimal)
        self.assertEqual(guided.total_cost, report.teacher_result.total_cost)
        self.assertEqual(len(guided.selected), len(report.teacher_result.selected))

    def test_refuses_an_interrupted_nonoptimal_teacher(self) -> None:
        with self.assertRaisesRegex(ValueError, "prove optimality"):
            train_from_exact_teacher(
                self.problem(), solve_kwargs={"max_expanded_nodes": 0}
            )

    def test_teacher_recorder_cannot_be_overridden(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not override"):
            train_from_exact_teacher(
                self.problem(), solve_kwargs={"branch_orderer": lambda *args: ()}
            )


if __name__ == "__main__":
    unittest.main()
