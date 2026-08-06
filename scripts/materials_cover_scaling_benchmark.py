#!/usr/bin/env python3
"""Scaling benchmark for lattice-free learned-cluster covering.

The benchmark deliberately builds every cover instance through the public
point-set learner.  Generator lattice coordinates are never passed to the
learner or the covering solver.  Exact runs execute in a child process so the
123-atom control can be bounded without changing solver semantics.

The output schema is intended to remain stable while GCTS gains frontier
memoization and learned branch ranking.  Optional solver keyword arguments are
enabled only when the installed solver advertises them.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import multiprocessing
import time
from collections import Counter
from dataclasses import asdict, dataclass
from queue import Empty
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

from materials_cover_ranking import (
    LinearBranchRanker,
    make_solver_branch_orderer,
    train_from_exact_teacher,
)
from materials_overlap_cover import Occurrence, OverlapCoverProblem
from materials_pointset_benchmarks import crystalline_control
from materials_pointset_clusters import learn_cluster_candidates


@dataclass(frozen=True)
class InstanceSummary:
    shell_radius: int
    atoms: int
    learned_types: int
    occurrences: int
    support_size_histogram: Mapping[int, int]
    maximum_support: int
    cardinality_lower_bound: int
    witness_lower_bound: int
    sound_lower_bound: int
    duplicate_supports: int
    dominated_occurrences: int
    incidence_signature_classes: int
    largest_incidence_signature_class: int


@dataclass(frozen=True)
class RunSummary:
    shell_radius: int
    method: str
    completed: bool
    optimal: Optional[bool]
    selected_occurrences: Optional[int]
    total_cost: Optional[float]
    expanded_nodes: Optional[int]
    memo_hits: Optional[int]
    backtracks: Optional[int]
    pruned_nodes: Optional[int]
    runtime_seconds: float
    termination: str
    max_expanded_nodes: Optional[int]


@dataclass(frozen=True)
class TrainingSummary:
    shell_radius: int
    teacher_optimal_cost: float
    teacher_contexts: int
    teacher_examples: int
    informative_contexts: int
    positive_examples: int
    epochs: int


def _instance(shell_radius: int) -> Tuple[OverlapCoverProblem, InstanceSummary]:
    sample = crystalline_control(shell_radius=shell_radius)
    learned = learn_cluster_candidates(
        sample.species,
        sample.positions,
        neighbor_count=6,
        descriptor_tolerance=1e-5,
    )
    occurrences = tuple(
        Occurrence(index, item.member_indices)
        for index, item in enumerate(learned.occurrences)
    )
    universe = tuple(range(len(sample.positions)))
    problem = OverlapCoverProblem(universe, occurrences)
    support_sizes = Counter(len(item.covers) for item in occurrences)
    maximum_support = max(support_sizes)

    # For unit-cost set cover, no occurrence can cover more than
    # ``maximum_support`` objects, hence this is a sound integer lower bound.
    cardinality_bound = math.ceil(len(universe) / maximum_support)
    witness = _disjoint_witness(universe, occurrences)

    support_counts = Counter(item.covers for item in occurrences)
    duplicates = sum(count - 1 for count in support_counts.values())
    dominated = sum(
        any(
            left != right
            and occurrence.cost >= candidate.cost
            and occurrence.covers < candidate.covers
            for right, candidate in enumerate(occurrences)
        )
        for left, occurrence in enumerate(occurrences)
    )
    object_degrees = {
        item: sum(item in occurrence.covers for occurrence in occurrences)
        for item in universe
    }
    # These cheap incidence signatures expose candidate symmetry buckets for
    # later canonicalization.  Equal signatures alone are not a proof of an
    # automorphism, so the benchmark reports but never prunes by them.
    incidence_signatures = Counter()
    for left, occurrence in enumerate(occurrences):
        intersections = Counter(
            len(occurrence.covers & candidate.covers)
            for right, candidate in enumerate(occurrences)
            if left != right
        )
        incidence_signatures[(
            len(occurrence.covers),
            tuple(sorted(object_degrees[item] for item in occurrence.covers)),
            tuple(sorted(intersections.items())),
        )] += 1
    summary = InstanceSummary(
        shell_radius=shell_radius,
        atoms=len(universe),
        learned_types=len(learned.cluster_types),
        occurrences=len(occurrences),
        support_size_histogram=dict(sorted(support_sizes.items())),
        maximum_support=maximum_support,
        cardinality_lower_bound=cardinality_bound,
        witness_lower_bound=len(witness),
        sound_lower_bound=max(cardinality_bound, len(witness)),
        duplicate_supports=duplicates,
        dominated_occurrences=dominated,
        incidence_signature_classes=len(incidence_signatures),
        largest_incidence_signature_class=max(incidence_signatures.values()),
    )
    return problem, summary


def build_instance(
    shell_radius: int,
) -> Tuple[OverlapCoverProblem, InstanceSummary]:
    """Public constructor shared by held-out policy benchmarks."""

    return _instance(shell_radius)


def _disjoint_witness(
    universe: Iterable[int], occurrences: Sequence[Occurrence]
) -> Tuple[int, ...]:
    """Return atoms of which each occurrence contains at most one.

    Every selected atom therefore requires a different cover occurrence.  The
    greedy witness is not necessarily maximum, but its size is always a sound
    lower bound and costs almost nothing to compute.
    """

    co_occurring = {item: set() for item in universe}
    for occurrence in occurrences:
        for item in occurrence.covers:
            co_occurring[item].update(occurrence.covers - {item})
    remaining = set(co_occurring)
    witness = []
    while remaining:
        item = min(
            remaining,
            key=lambda value: (len(co_occurring[value] & remaining), value),
        )
        witness.append(item)
        remaining.remove(item)
        remaining.difference_update(co_occurring[item])
    return tuple(witness)


def _result_summary(
    shell_radius: int,
    method: str,
    result: object,
    runtime: float,
    max_expanded_nodes: Optional[int] = None,
) -> RunSummary:
    complete = bool(getattr(result, "complete"))
    # The current unbudgeted solve() certifies optimality when it returns.
    # Enhanced solvers may expose an explicit optimal/terminated flag.
    optimal = getattr(result, "optimal", True if method != "greedy" else None)
    selected = tuple(getattr(result, "selected"))
    return RunSummary(
        shell_radius=shell_radius,
        method=method,
        completed=complete,
        optimal=optimal,
        selected_occurrences=len(selected),
        total_cost=float(getattr(result, "total_cost")),
        expanded_nodes=int(getattr(result, "expanded_nodes")),
        memo_hits=(
            int(getattr(result, "memo_hits"))
            if hasattr(result, "memo_hits")
            else None
        ),
        backtracks=int(getattr(result, "backtracks")),
        pruned_nodes=int(getattr(result, "pruned_nodes")),
        runtime_seconds=runtime,
        termination="completed",
        max_expanded_nodes=max_expanded_nodes,
    )


def run_greedy(shell_radius: int) -> RunSummary:
    problem, _ = _instance(shell_radius)
    started = time.perf_counter()
    result = problem.greedy()
    return _result_summary(
        shell_radius, "greedy", result, time.perf_counter() - started
    )


def train_radius_two_ranker(
    *, epochs: int = 10,
) -> Tuple[LinearBranchRanker, TrainingSummary]:
    """Imitate one certified radius-two cover using generic branch features."""

    problem, _ = _instance(2)
    report = train_from_exact_teacher(
        problem,
        solve_kwargs={
            "frontier_memo": True,
            "partition_branches": True,
        },
        fit_kwargs={"epochs": epochs},
    )
    return report.ranker, TrainingSummary(
        shell_radius=2,
        teacher_optimal_cost=report.teacher_result.total_cost,
        teacher_contexts=report.recorded_context_count,
        teacher_examples=report.example_count,
        informative_contexts=report.labeled_context_count,
        positive_examples=report.positive_example_count,
        epochs=epochs,
    )


def _supported_solve_kwargs(
    problem: OverlapCoverProblem, requested: Mapping[str, object]
) -> Dict[str, object]:
    parameters = inspect.signature(problem.solve).parameters
    return {key: value for key, value in requested.items() if key in parameters}


def _exact_worker(
    shell_radius: int,
    method: str,
    requested_kwargs: Mapping[str, object],
    ranker_weights: Optional[Mapping[str, float]],
    output: multiprocessing.Queue,
) -> None:
    try:
        problem, _ = _instance(shell_radius)
        kwargs = _supported_solve_kwargs(problem, requested_kwargs)
        if ranker_weights is not None:
            kwargs["branch_orderer"] = make_solver_branch_orderer(
                LinearBranchRanker(ranker_weights)
            )
        started = time.perf_counter()
        result = problem.solve(**kwargs)
        summary = asdict(_result_summary(
            shell_radius,
            method,
            result,
            time.perf_counter() - started,
            requested_kwargs.get("max_expanded_nodes"),
        ))
        if not summary["optimal"] and "max_expanded_nodes" in kwargs:
            summary["termination"] = "node_budget"
        output.put(
            ("ok", summary)
        )
    except BaseException as error:  # returned to the parent as benchmark data
        output.put(("error", f"{type(error).__name__}: {error}"))


def run_exact_bounded(
    shell_radius: int,
    *,
    timeout_seconds: float,
    method: str = "unguided_gcts",
    solve_kwargs: Optional[Mapping[str, object]] = None,
    ranker_weights: Optional[Mapping[str, float]] = None,
) -> RunSummary:
    """Run exact GCTS with an external wall-clock bound.

    A timeout does not masquerade as an incomplete optimum.  Since legacy
    solve() exposes no partial incumbent or counters, those fields remain null.
    """

    context = multiprocessing.get_context("spawn")
    output = context.Queue()
    process = context.Process(
        target=_exact_worker,
        args=(shell_radius, method, solve_kwargs or {}, ranker_weights, output),
    )
    started = time.perf_counter()
    process.start()
    process.join(timeout_seconds)
    elapsed = time.perf_counter() - started
    if process.is_alive():
        process.terminate()
        process.join()
        return RunSummary(
            shell_radius, method, False, False, None, None, None, None,
            None, None, elapsed, "wall_clock_timeout",
            (solve_kwargs or {}).get("max_expanded_nodes"),
        )
    try:
        # A multiprocessing queue's feeder thread can lag very slightly behind
        # the worker exit observed above.
        status, payload = output.get(timeout=1.0)
    except Empty:
        status, payload = "error", f"worker exited with code {process.exitcode}"
    if status == "ok":
        return RunSummary(**payload)
    return RunSummary(
        shell_radius, method, False, False, None, None, None, None,
        None, None, elapsed, str(payload),
        (solve_kwargs or {}).get("max_expanded_nodes"),
    )


def benchmark(
    radii: Sequence[int],
    timeout_seconds: float,
    max_expanded_nodes: Optional[int],
    evaluation_budgets: Sequence[int] = (50, 100, 250, 500),
) -> Mapping[str, object]:
    ranker, training = train_radius_two_ranker(epochs=10)
    instances = []
    runs = []
    for radius in radii:
        _, summary = _instance(radius)
        instances.append(asdict(summary))
        runs.append(asdict(run_greedy(radius)))
        runs.append(asdict(run_exact_bounded(
            radius,
            timeout_seconds=timeout_seconds,
            method="unguided_gcts",
            solve_kwargs={
                "frontier_memo": False,
                "max_expanded_nodes": max_expanded_nodes,
            },
        )))
        # This row automatically becomes a real memoization ablation when the
        # enhanced solver exposes frontier_memo; legacy solvers safely ignore
        # the keyword and therefore produce identical search counters.
        runs.append(asdict(run_exact_bounded(
            radius,
            timeout_seconds=timeout_seconds,
            method="frontier_memo_gcts",
            solve_kwargs={
                "frontier_memo": True,
                "max_expanded_nodes": max_expanded_nodes,
            },
        )))
        if radius == 3:
            for budget in evaluation_budgets:
                # All rows share branch partitioning, node budget, incumbent,
                # and objective.  The four-way ablation separates ordering
                # from frontier memoization and their combination.
                if budget != max_expanded_nodes:
                    runs.append(asdict(run_exact_bounded(
                        radius,
                        timeout_seconds=timeout_seconds,
                        method="unguided_gcts",
                        solve_kwargs={
                            "frontier_memo": False,
                            "max_expanded_nodes": budget,
                        },
                    )))
                    runs.append(asdict(run_exact_bounded(
                        radius,
                        timeout_seconds=timeout_seconds,
                        method="frontier_memo_gcts",
                        solve_kwargs={
                            "frontier_memo": True,
                            "max_expanded_nodes": budget,
                        },
                    )))
                runs.append(asdict(run_exact_bounded(
                    radius,
                    timeout_seconds=timeout_seconds,
                    method="ranked_gcts",
                    solve_kwargs={
                        "frontier_memo": False,
                        "max_expanded_nodes": budget,
                    },
                    ranker_weights=ranker.weights,
                )))
                runs.append(asdict(run_exact_bounded(
                    radius,
                    timeout_seconds=timeout_seconds,
                    method="ranked_frontier_memo_gcts",
                    solve_kwargs={
                        "frontier_memo": True,
                        "max_expanded_nodes": budget,
                    },
                    ranker_weights=ranker.weights,
                )))
    return {
        "schema_version": 1,
        "instances": instances,
        "ranking_training": asdict(training),
        "runs": runs,
        "comparison_contract": {
            "quality": (
                "matched objective and node budget; compare incumbent "
                "total_cost, and claim optimality only when optimal=true"
            ),
            "search": [
                "expanded_nodes", "memo_hits", "backtracks",
                "pruned_nodes", "runtime_seconds",
            ],
            "ranked_training_scope": "certified shell_radius=2 search only",
            "ranked_evaluation_scope": "shell_radius=3 only",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--radii", type=int, nargs="+", default=(2, 3),
        help="integer crystal crop radii (default: 2 3)",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0,
        help="wall-clock seconds allowed for each exact variant",
    )
    parser.add_argument(
        "--max-nodes", type=int, default=500,
        help="native GCTS expansion budget, or -1 for no node bound",
    )
    parser.add_argument(
        "--evaluation-budgets",
        type=int,
        nargs="+",
        default=(50, 100, 250, 500),
        help="matched node budgets for default versus ranked radius-three GCTS",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.max_nodes < -1:
        parser.error("--max-nodes must be nonnegative or -1")
    if any(budget < 0 for budget in args.evaluation_budgets):
        parser.error("--evaluation-budgets must be nonnegative")
    max_nodes = None if args.max_nodes == -1 else args.max_nodes
    print(json.dumps(
        benchmark(
            args.radii,
            args.timeout,
            max_nodes,
            tuple(dict.fromkeys(args.evaluation_budgets)),
        ),
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
