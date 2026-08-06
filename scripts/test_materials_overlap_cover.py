#!/usr/bin/env python3
"""Deterministic checks for the generic overlapping-cover GCTS kernel."""

import math
import random
import unittest
from dataclasses import FrozenInstanceError
from itertools import combinations

from materials_overlap_cover import (
    BranchCandidateOutcome,
    BranchStarted,
    Occurrence,
    OverlapCoverProblem,
    solve_overlap_cover,
)


class OverlapCoverTest(unittest.TestCase):
    @staticmethod
    def _brute_force(
        universe, occurrences, conflicts
    ):
        """Return the exact objective by enumerating every occurrence subset."""

        conflict_sets = {frozenset(pair) for pair in conflicts}
        best = None
        for size in range(len(occurrences) + 1):
            for chosen in combinations(range(len(occurrences)), size):
                if any(
                    frozenset((occurrences[left].id, occurrences[right].id))
                    in conflict_sets
                    for left, right in combinations(chosen, 2)
                ):
                    continue
                covered = frozenset().union(
                    *(occurrences[index].covers for index in chosen)
                ) if chosen else frozenset()
                if not frozenset(universe) <= covered:
                    continue
                objective = (
                    sum(occurrences[index].cost for index in chosen),
                    len(chosen),
                )
                if best is None or objective < best:
                    best = objective
        return best

    def test_conflict_traps_greedy_but_search_succeeds(self) -> None:
        problem = OverlapCoverProblem(
            {"a", "b", "c", "d"},
            (
                Occurrence("tempting", {"a", "b", "c"}),
                Occurrence("left", {"a", "b"}),
                Occurrence("right", {"c", "d"}),
            ),
            conflict_pairs=(("tempting", "right"),),
        )

        greedy = problem.greedy()
        exact = problem.solve()

        self.assertFalse(greedy.complete)
        self.assertFalse(greedy.optimal)
        self.assertEqual(greedy.selected, ("tempting",))
        self.assertTrue(exact.complete)
        self.assertEqual(exact.selected, ("left", "right"))
        self.assertEqual(exact.total_cost, 2.0)
        self.assertGreaterEqual(exact.expanded_nodes, 1)

    def test_branch_and_bound_improves_a_greedy_cover(self) -> None:
        problem = OverlapCoverProblem(
            range(1, 7),
            (
                Occurrence("big", {1, 2, 3, 4}),
                Occurrence("cross-a", {1, 2, 5}),
                Occurrence("cross-b", {3, 4, 6}),
                Occurrence("five", {5}),
                Occurrence("six", {6}),
            ),
        )

        greedy = problem.greedy()
        exact = problem.solve()

        self.assertTrue(greedy.complete)
        self.assertEqual(len(greedy.selected), 3)
        self.assertTrue(exact.complete)
        self.assertEqual(exact.selected, ("cross-a", "cross-b"))
        self.assertEqual(exact.total_cost, 2.0)
        self.assertGreater(exact.pruned_nodes, 0)

    def test_overlap_can_be_required(self) -> None:
        result = solve_overlap_cover(
            ("atom-0", "atom-1", "atom-2"),
            (
                Occurrence(("motif", "left", 0.0), {"atom-0", "atom-1"}),
                Occurrence(("motif", "right", 1.7), {"atom-1", "atom-2"}),
            ),
        )

        self.assertTrue(result.complete)
        self.assertEqual(len(result.selected), 2)
        # atom-1 belongs to both selected occurrences: this is a cover, not a
        # partition or exact-cover formulation.
        self.assertEqual(result.covered, frozenset(("atom-0", "atom-1", "atom-2")))

    def test_explicit_allow_list_and_predicates_compose(self) -> None:
        occurrences = (
            Occurrence("red", {0}),
            Occurrence("blue", {1}),
            Occurrence("green", {1}),
        )
        problem = OverlapCoverProblem(
            {0, 1},
            occurrences,
            compatible_pairs=(("red", "blue"), ("red", "green")),
            conflict_predicate=lambda left, right: {
                left.id, right.id
            } == {"red", "blue"},
        )
        result = problem.solve()
        self.assertTrue(result.complete)
        self.assertEqual(result.selected, ("red", "green"))

    def test_reports_unsatisfiable_problem(self) -> None:
        result = solve_overlap_cover(
            {0, 1},
            (Occurrence("only-zero", {0}),),
        )
        self.assertFalse(result.complete)
        self.assertEqual(result.selected, ())
        self.assertTrue(math.isinf(result.total_cost))
        self.assertGreater(result.backtracks, 0)

    def test_memo_merges_distinct_histories_with_identical_future(self) -> None:
        # Greedy selects T and is trapped by forced E.  Exact search first
        # propagates E, after which selecting either A or B leaves precisely
        # the same uncovered object and viable {C, D} placements.  The memo
        # may therefore soundly merge those distinct selected histories.
        occurrences = (
            Occurrence("T", {0, 1, 2}),
            Occurrence("A", {0, 1}),
            Occurrence("B", {0, 1}),
            Occurrence("C", {2}),
            Occurrence("D", {2}),
            Occurrence("E", {3}),
        )
        problem = OverlapCoverProblem(
            range(4), occurrences, conflict_pairs=(("T", "E"),)
        )

        without_memo = problem.solve(frontier_memo=False)
        with_memo = problem.solve(frontier_memo=True)

        self.assertTrue(with_memo.complete)
        self.assertEqual(with_memo.total_cost, without_memo.total_cost)
        self.assertEqual(len(with_memo.selected), len(without_memo.selected))
        self.assertGreaterEqual(with_memo.memo_hits, 1)
        self.assertLess(with_memo.expanded_nodes, without_memo.expanded_nodes)

    def test_frontier_key_does_not_merge_different_compatibility_marks(self) -> None:
        # A and B cover the same object, but only A permits cheap C.  Equal
        # uncovered sets alone are insufficient; viable occurrences must be
        # part of the canonical marked-frontier key.
        problem = OverlapCoverProblem(
            {0, 1},
            (
                Occurrence("A", {0}, 1.0),
                Occurrence("B", {0}, 1.0),
                Occurrence("C", {1}, 1.0),
                Occurrence("D", {1}, 4.0),
            ),
            conflict_pairs=(("B", "C"), ("A", "D")),
        )
        result = problem.solve(frontier_memo=True)
        self.assertTrue(result.complete)
        self.assertEqual(result.selected, ("A", "C"))
        self.assertEqual(result.total_cost, 2.0)

    def test_search_budget_returns_incumbent_without_claiming_optimality(self) -> None:
        problem = OverlapCoverProblem(
            range(1, 7),
            (
                Occurrence("big", {1, 2, 3, 4}),
                Occurrence("cross-a", {1, 2, 5}),
                Occurrence("cross-b", {3, 4, 6}),
                Occurrence("five", {5}),
                Occurrence("six", {6}),
            ),
        )
        interrupted = problem.solve(max_expanded_nodes=0)
        exact = problem.solve()

        self.assertTrue(interrupted.complete)
        self.assertFalse(interrupted.optimal)
        self.assertEqual(interrupted.expanded_nodes, 0)
        self.assertGreater(interrupted.total_cost, exact.total_cost)
        self.assertTrue(exact.optimal)
        with self.assertRaises(ValueError):
            problem.solve(max_expanded_nodes=1.5)

    def test_dynamic_packing_bound_proves_distinct_future_placements(self) -> None:
        # The three private objects have pairwise-disjoint candidate domains.
        # Although every large occurrence also covers shared object d (making
        # the maximum-gain cardinality bound only two), at least three future
        # occurrences are necessary.
        problem = OverlapCoverProblem(
            {"a", "b", "c", "d"},
            (
                Occurrence("ad", {"a", "d"}),
                Occurrence("a", {"a"}),
                Occurrence("bd", {"b", "d"}),
                Occurrence("b", {"b"}),
                Occurrence("cd", {"c", "d"}),
                Occurrence("c", {"c"}),
            ),
        )
        gain_only = problem.solve(packing_bound=False)
        packed = problem.solve(packing_bound=True)

        self.assertEqual(packed.total_cost, 3.0)
        self.assertEqual(len(packed.selected), 3)
        self.assertEqual(
            (packed.total_cost, len(packed.selected)),
            (gain_only.total_cost, len(gain_only.selected)),
        )
        self.assertLess(packed.expanded_nodes, gain_only.expanded_nodes)

    def test_branch_orderer_observes_but_cannot_change_legality(self) -> None:
        problem = OverlapCoverProblem(
            range(1, 7),
            (
                Occurrence("big", {1, 2, 3, 4}),
                Occurrence("cross-a", {1, 2, 5}),
                Occurrence("cross-b", {3, 4, 6}),
                Occurrence("five", {5}),
                Occurrence("six", {6}),
            ),
        )
        observations = []

        def reverse_order(instance, context, options):
            self.assertIs(instance, problem)
            self.assertIn(context.pivot, context.uncovered)
            self.assertEqual(set(context.domains[context.pivot]), set(options))
            observations.append(context)
            return tuple(reversed(options))

        ranked = problem.solve(branch_orderer=reverse_order)
        default = problem.solve()
        self.assertTrue(observations)
        self.assertEqual(ranked.total_cost, default.total_cost)
        self.assertEqual(len(ranked.selected), len(default.selected))

        with self.assertRaisesRegex(ValueError, "permutation"):
            problem.solve(branch_orderer=lambda _problem, _context, options: options[:-1])

    def test_branch_observer_reports_exact_candidate_outcomes(self) -> None:
        problem = OverlapCoverProblem(
            range(1, 7),
            (
                Occurrence("big", {1, 2, 3, 4}),
                Occurrence("cross-a", {1, 2, 5}),
                Occurrence("cross-b", {3, 4, 6}),
                Occurrence("five", {5}),
                Occurrence("six", {6}),
            ),
        )
        events = []
        observed = problem.solve(
            frontier_memo=False,
            branch_observer=lambda instance, event: (
                self.assertIs(instance, problem), events.append(event)
            )[-1],
        )
        baseline = problem.solve(frontier_memo=False)

        # Observation is behaviorally inert, including every existing counter.
        self.assertEqual(observed, baseline)
        self.assertEqual(len(events), 3)
        started = events[0]
        self.assertIsInstance(started, BranchStarted)
        self.assertEqual(started.branch_id, 0)
        self.assertEqual(started.ordered_indices, (0, 1))
        self.assertEqual(started.context.pivot, 1)
        self.assertEqual(started.context.domains[1], (0, 1))

        first, second = events[1:]
        self.assertIsInstance(first, BranchCandidateOutcome)
        self.assertEqual(first.candidate_index, 0)
        self.assertEqual(first.candidate_position, 0)
        self.assertEqual(first.descendant_expanded_nodes, 1)
        self.assertFalse(first.feasible)
        self.assertFalse(first.interrupted)
        self.assertFalse(first.improved_incumbent)
        self.assertIsNone(first.best_objective)
        self.assertEqual(first.incumbent_before, (3.0, 3))
        self.assertEqual(first.incumbent_after, (3.0, 3))

        self.assertEqual(second.candidate_index, 1)
        self.assertEqual(second.candidate_position, 1)
        self.assertEqual(second.descendant_expanded_nodes, 1)
        self.assertTrue(second.feasible)
        self.assertFalse(second.interrupted)
        self.assertTrue(second.improved_incumbent)
        self.assertEqual(second.best_objective, (2.0, 2))
        self.assertEqual(second.incumbent_after, (2.0, 2))

        # Frozen events and a read-only domain map prevent accidental mutation
        # from leaking back into search or later training records.
        with self.assertRaises(FrozenInstanceError):
            started.branch_id = 9
        with self.assertRaises(TypeError):
            started.context.domains[1] = ()

    def test_branch_observer_marks_budget_interruption_as_unknown(self) -> None:
        problem = OverlapCoverProblem(
            range(1, 7),
            (
                Occurrence("big", {1, 2, 3, 4}),
                Occurrence("cross-a", {1, 2, 5}),
                Occurrence("cross-b", {3, 4, 6}),
                Occurrence("five", {5}),
                Occurrence("six", {6}),
            ),
        )
        events = []
        result = problem.solve(
            max_expanded_nodes=1,
            branch_observer=lambda _problem, event: events.append(event),
        )
        outcomes = [
            event for event in events
            if isinstance(event, BranchCandidateOutcome)
        ]

        self.assertFalse(result.optimal)
        self.assertEqual(len(outcomes), 1)
        self.assertIsNone(outcomes[0].feasible)
        self.assertTrue(outcomes[0].interrupted)
        self.assertEqual(outcomes[0].descendant_expanded_nodes, 0)
        self.assertIsNone(outcomes[0].best_objective)

    def test_randomized_modes_match_exhaustive_optimum(self) -> None:
        # Exercise memoization and sound branch partitioning independently.
        # Fixed seeds make failures reproducible while still spanning covers,
        # unsatisfiable instances, overlaps, zero costs, and conflicts.
        for seed in range(120):
            rng = random.Random(seed)
            universe = frozenset(range(rng.randint(1, 5)))
            occurrences = tuple(
                Occurrence(
                    index,
                    {
                        item
                        for item in universe
                        if rng.random() < 0.45
                    } or {rng.choice(tuple(universe))},
                    rng.choice((0.0, 0.5, 1.0, 2.0)),
                )
                for index in range(rng.randint(1, 8))
            )
            conflicts = tuple(
                (left.id, right.id)
                for left, right in combinations(occurrences, 2)
                if rng.random() < 0.16
            )
            expected = self._brute_force(universe, occurrences, conflicts)
            problem = OverlapCoverProblem(
                universe, occurrences, conflict_pairs=conflicts
            )

            for frontier_memo in (False, True):
                for partition_branches in (False, True):
                    for packing_bound in (False, True):
                        with self.subTest(
                            seed=seed,
                            frontier_memo=frontier_memo,
                            partition_branches=partition_branches,
                            packing_bound=packing_bound,
                        ):
                            result = problem.solve(
                                frontier_memo=frontier_memo,
                                partition_branches=partition_branches,
                                packing_bound=packing_bound,
                                # Exercise the tracing path throughout the
                                # exhaustive exactness cross-check.
                                branch_observer=lambda _problem, _event: None,
                            )
                            self.assertTrue(result.optimal)
                            self.assertEqual(
                                result.complete, expected is not None
                            )
                            if expected is None:
                                self.assertTrue(math.isinf(result.total_cost))
                            else:
                                self.assertEqual(
                                    (result.total_cost, len(result.selected)),
                                    expected,
                                )


if __name__ == "__main__":
    unittest.main()
