#!/usr/bin/env python3
"""Train Hat mark values directly from branch-success and branch-failure signals.

This is deliberately a small bandit/RL environment over the marking section:

1. collect signals from online Hat GCTS;
2. collapse positive overlaps into branch-local equality roots;
3. sample ternary/{*} values for roots that appear in failed-branch clauses;
4. reward assignments that satisfy failed-branch disequalities and prune the
   single-seed candidate graph without violating positive equalities;
5. optionally repeat at larger lattice reach while keeping channels/action fixed.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hat_marking_search import MarkingSpec, build_hat_orientations, segment_payload, summarize
from hat_sample_marking import (
    AssignmentValue,
    BaseProbeVar,
    MarkScheme,
    ProbeClause,
    ProbePair,
    active_bad_constraints,
    base_probe_var,
    build_spec_from_assignments,
    clause_satisfied,
    fresh_intratile_union_find,
    mark_scheme,
    online_training_args,
    pair_can_witness_disequality,
    path_contact_pair_counts,
    path_to_placements,
    point_candidate_graph_metrics,
    positive_pair_conflicts,
    run_online_tree_episode,
    signed_probe_relation,
    validate_positive_paths,
)
from turtle_gcts_rl import Point, run_tree_search


VALUES: tuple[AssignmentValue, ...] = (None, -1, 0, 1)


@dataclass
class SignalSet:
    reach: int
    scheme: MarkScheme
    good_counts: Counter[ProbePair]
    bad_counts: Counter[ProbePair]
    bad_clauses: Counter[ProbeClause]
    sample: dict[str, object]
    collector_summary: dict[str, object]


@dataclass
class TrainingState:
    union_find: object
    roots: list[BaseProbeVar]
    active_roots: list[BaseProbeVar]
    active_clauses: list[tuple[ProbeClause, int]]
    positive_pairs: list[ProbePair]
    baseline_graph: dict[str, object]


@dataclass
class ScoredAssignment:
    reward: float
    assignments: dict[BaseProbeVar, AssignmentValue]
    metrics: dict[str, object]
    spec: MarkingSpec


def softmax(logits: list[float]) -> list[float]:
    high = max(logits)
    exps = [math.exp(value - high) for value in logits]
    total = sum(exps)
    return [value / total for value in exps]


def sample_index(probs: list[float], rng: random.Random) -> int:
    threshold = rng.random()
    cumulative = 0.0
    for idx, prob in enumerate(probs):
        cumulative += prob
        if threshold <= cumulative:
            return idx
    return len(probs) - 1


def online_signal_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        sample_wall_time_ms=args.signal_wall_time_ms,
        sample_target_tiles=args.signal_target_tiles,
        benchmark_target_corona=args.signal_target_corona,
        max_steps=args.signal_max_steps,
        node_limit=args.signal_node_limit,
        frontier_limit=args.frontier_limit,
        candidate_limit=args.candidate_limit,
        no_boundary_alive=args.no_boundary_alive,
        tree_policy=args.tree_policy,
        online_contact_scope=args.online_contact_scope,
        online_max_bad_pairs_per_tile=args.online_max_bad_pairs_per_tile,
        online_min_good=args.online_min_good,
        online_min_bad=args.online_min_bad,
        min_good=args.online_min_good,
        min_bad=args.online_min_bad,
        max_good_for_bad=args.max_good_for_bad,
        side_action=args.side_action,
        assignment_mode="random",
        assignment_seed=args.seed,
        assignment_trials=1,
        assignment_steps=0,
        assignment_lock_initial=True,
        assignment_fill_unassigned=False,
        online_validate_updates=not args.no_online_validate_updates,
        online_learn_boundary_failures=args.online_learn_boundary_failures,
        online_hard_mark_filter=False,
        online_hard_live_mark_filter=False,
        online_child_section_filter=False,
        online_scope_bad_clauses=args.online_scope_bad_clauses,
        online_marked_boundary_alive=args.online_marked_boundary_alive,
        online_trust_marked_candidates=False,
        probe_mode=args.probe_mode,
        episodes=1,
    )


def collect_signals(args: argparse.Namespace, reach: int) -> SignalSet:
    scheme = mark_scheme(args.probe_mode, reach, args.channels, args.lattice_base)
    run_args = online_signal_args(args)
    bad_counts: Counter[ProbePair] = Counter()
    bad_clauses: Counter[ProbeClause] = Counter()
    base_orientations = build_hat_orientations(None)
    positive_paths = []
    good_counts: Counter[ProbePair] = Counter()
    run_summaries = []
    for episode in range(args.signal_episodes):
        seed = args.seed + episode * 101
        result, stats, path = run_online_tree_episode(run_args, scheme, bad_counts, bad_clauses, seed)
        path_good = path_contact_pair_counts(path, base_orientations, scheme, run_args.online_contact_scope == "neighbors")
        good_counts.update(path_good)
        positive_paths.append(path_to_placements(path, base_orientations))
        run_summaries.append(
            {
                "episode": episode,
                "seed": seed,
                "elapsed_ms": result.elapsed_ms,
                "tile_count": result.tile_count,
                "corona": result.corona,
                "decisions": result.decisions,
                "branch_moves": result.branch_moves,
                "forced_moves": result.forced_moves,
                "stop": result.stopped_reason,
                "active_bad_clauses": stats.get("active_bad_clauses", 0),
                "unique_bad_clauses": stats.get("unique_bad_clauses", 0),
                "unique_bad_pairs": stats.get("unique_bad_pairs", 0),
            }
        )
    sample: dict[str, object] = {
        "good_counts": good_counts,
        "branch_equalities": good_counts,
        "bad_counts": bad_counts,
        "bad_clauses": bad_clauses,
        "positive_paths": positive_paths,
        "episodes": run_summaries,
    }
    return SignalSet(
        reach=reach,
        scheme=scheme,
        good_counts=good_counts,
        bad_counts=bad_counts,
        bad_clauses=bad_clauses,
        sample=sample,
        collector_summary={
            "runs": run_summaries,
            "good_pairs": len(good_counts),
            "good_observations": sum(good_counts.values()),
            "bad_pairs": len(bad_counts),
            "bad_pair_observations": sum(bad_counts.values()),
            "bad_clauses": len(bad_clauses),
            "bad_clause_observations": sum(bad_clauses.values()),
        },
    )


def roots_for_pair(pair: ProbePair, union_find, side_action: str) -> tuple[BaseProbeVar, BaseProbeVar]:
    left, right = pair
    left_root, _ = union_find.find(base_probe_var(left))
    right_root, _ = union_find.find(base_probe_var(right))
    return left_root, right_root


def build_training_state(signals: SignalSet, args: argparse.Namespace) -> TrainingState:
    union_find, _, _ = fresh_intratile_union_find(signals.scheme, args.side_action)
    for (left, right), count in signals.good_counts.items():
        if count < args.online_min_good:
            continue
        union_find.union(
            base_probe_var(left),
            base_probe_var(right),
            signed_probe_relation(left, right, args.side_action),
        )

    roots = sorted({union_find.find(variable)[0] for variable in union_find.parents})
    active_clauses: list[tuple[ProbeClause, int]] = []
    active_roots = set()
    for clause, count in signals.bad_clauses.items():
        if count < args.online_min_bad:
            continue
        filtered = tuple(
            pair
            for pair in clause
            if signals.good_counts.get(pair, 0) <= args.max_good_for_bad
            and pair_can_witness_disequality(pair, union_find, args.side_action)
        )
        if not filtered:
            continue
        active_clauses.append((filtered, count))
        for pair in filtered:
            active_roots.update(roots_for_pair(pair, union_find, args.side_action))

    graph_args = graph_metric_args(args)
    return TrainingState(
        union_find=union_find,
        roots=roots,
        active_roots=sorted(root for root in active_roots if not union_find.zero[root]),
        active_clauses=active_clauses,
        positive_pairs=[pair for pair, count in signals.good_counts.items() if count >= args.online_min_good],
        baseline_graph=point_candidate_graph_metrics(None, graph_args),
    )


def graph_metric_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        candidate_limit=args.candidate_limit,
        frontier_limit=args.frontier_limit,
        seed=args.seed,
        benchmark_target_tiles=args.benchmark_target_tiles,
        benchmark_target_corona=args.benchmark_target_corona,
        benchmark_max_steps=args.benchmark_max_steps,
        node_limit=args.benchmark_node_limit,
        wall_time_ms=args.benchmark_wall_time_ms,
        no_boundary_alive=args.no_boundary_alive,
    )


def initial_logits(active_roots: list[BaseProbeVar], args: argparse.Namespace) -> dict[BaseProbeVar, list[float]]:
    return {root: [args.star_bias, 0.0, 0.0, 0.0] for root in active_roots}


def sample_assignment(
    state: TrainingState,
    logits: dict[BaseProbeVar, list[float]],
    rng: random.Random,
) -> dict[BaseProbeVar, AssignmentValue]:
    assignments = {root: None for root in state.roots}
    for root in state.active_roots:
        if state.union_find.zero[root]:
            continue
        idx = sample_index(softmax(logits[root]), rng)
        assignments[root] = VALUES[idx]
    return assignments


def assignment_value_counts(assignments: dict[BaseProbeVar, AssignmentValue]) -> dict[str, int]:
    counts = Counter(assignments.values())
    return {"*": counts.get(None, 0), "-1": counts.get(-1, 0), "0": counts.get(0, 0), "1": counts.get(1, 0)}


def score_assignment(
    assignments: dict[BaseProbeVar, AssignmentValue],
    state: TrainingState,
    signals: SignalSet,
    args: argparse.Namespace,
) -> ScoredAssignment:
    total_clause_weight = sum(weight for _, weight in state.active_clauses)
    satisfied_weight = sum(
        weight
        for clause, weight in state.active_clauses
        if clause_satisfied(clause, assignments, state.union_find, args.side_action)
    )
    positive_conflicts = positive_pair_conflicts(state.positive_pairs, assignments, state.union_find, args.side_action)
    active_assigned = sum(1 for root in state.active_roots if assignments[root] is not None)
    density = active_assigned / max(1, len(state.active_roots))
    clause_fraction = satisfied_weight / max(1, total_clause_weight)

    spec = build_spec_from_assignments(assignments, state.union_find, args.side_action, args, signals.scheme, "rl-section")
    graph = point_candidate_graph_metrics(spec, graph_metric_args(args))
    base_edges = max(1, int(state.baseline_graph["limited_bipartite_edges"]))
    base_unique = max(1, int(state.baseline_graph["limited_unique_candidates"]))
    edge_reduction = (base_edges - int(graph["limited_bipartite_edges"])) / base_edges
    unique_reduction = (base_unique - int(graph["limited_unique_candidates"])) / base_unique

    reward = (
        args.clause_reward * clause_fraction
        + args.edge_reward * edge_reduction
        + args.unique_reward * unique_reduction
        + args.density_reward * density
        - args.positive_conflict_penalty * len(positive_conflicts)
    )
    metrics = {
        "reward": round(reward, 6),
        "clause_fraction": round(clause_fraction, 6),
        "satisfied_clause_weight": satisfied_weight,
        "total_clause_weight": total_clause_weight,
        "positive_conflicts": len(positive_conflicts),
        "active_roots": len(state.active_roots),
        "assigned_active_roots": active_assigned,
        "density": round(density, 6),
        "candidate_edge_reduction": round(edge_reduction, 6),
        "candidate_unique_reduction": round(unique_reduction, 6),
        "baseline_limited_edges": state.baseline_graph["limited_bipartite_edges"],
        "marked_limited_edges": graph["limited_bipartite_edges"],
        "baseline_limited_unique_candidates": state.baseline_graph["limited_unique_candidates"],
        "marked_limited_unique_candidates": graph["limited_unique_candidates"],
        "assignment_value_counts": assignment_value_counts(assignments),
    }
    return ScoredAssignment(reward=reward, assignments=assignments, metrics=metrics, spec=spec)


def update_logits(
    logits: dict[BaseProbeVar, list[float]],
    elites: list[ScoredAssignment],
    active_roots: list[BaseProbeVar],
    args: argparse.Namespace,
) -> None:
    if not elites:
        return
    smoothing = args.elite_smoothing
    for root in active_roots:
        counts = [smoothing] * len(VALUES)
        for elite in elites:
            value = elite.assignments[root]
            counts[VALUES.index(value)] += 1.0
        total = sum(counts)
        target = [math.log(count / total) for count in counts]
        current = logits[root]
        for idx, value in enumerate(target):
            current[idx] = (1.0 - args.learning_rate) * current[idx] + args.learning_rate * value


def train_reach(signals: SignalSet, args: argparse.Namespace) -> tuple[ScoredAssignment, dict[str, object]]:
    state = build_training_state(signals, args)
    rng = random.Random(args.seed + signals.reach * 1009)
    logits = initial_logits(state.active_roots, args)
    search_cache: dict[MarkingSpec, tuple[float, dict[str, object]]] = {}
    best: ScoredAssignment | None = None
    checkpoints = []
    for episode in range(args.train_episodes):
        batch = [
            score_assignment(sample_assignment(state, logits, rng), state, signals, args)
            for _ in range(args.batch_size)
        ]
        batch.sort(key=lambda item: item.reward, reverse=True)
        if args.search_eval_elites > 0:
            for item in batch[: min(args.search_eval_elites, len(batch))]:
                local_reward = item.reward
                search_score, search_summary = search_eval(item.spec, args, search_cache)
                item.reward = local_reward + args.search_reward_weight * search_score
                item.metrics["local_reward"] = round(local_reward, 6)
                item.metrics["search_score"] = round(search_score, 6)
                item.metrics["search_eval"] = search_summary
                item.metrics["reward"] = round(item.reward, 6)
            batch.sort(key=lambda item: item.reward, reverse=True)
        elite_count = max(1, int(math.ceil(args.batch_size * args.elite_fraction)))
        elites = batch[:elite_count]
        update_logits(logits, elites, state.active_roots, args)
        if best is None or batch[0].reward > best.reward:
            best = batch[0]
        if episode == 0 or (episode + 1) % args.report_every == 0 or episode + 1 == args.train_episodes:
            checkpoints.append(
                {
                    "episode": episode + 1,
                    "best_reward": round(best.reward, 6),
                    "batch_best": batch[0].metrics,
                    "batch_mean_reward": round(sum(item.reward for item in batch) / len(batch), 6),
                    "elite_mean_reward": round(sum(item.reward for item in elites) / len(elites), 6),
                }
            )
    if best is None:
        raise RuntimeError("training produced no assignments")
    diagnostics = {
        "reach": signals.reach,
        "root_count": len(state.roots),
        "active_roots": len(state.active_roots),
        "active_bad_clauses": len(state.active_clauses),
        "active_bad_clause_weight": sum(weight for _, weight in state.active_clauses),
        "positive_pairs": len(state.positive_pairs),
        "baseline_graph": state.baseline_graph,
        "search_evaluations": len(search_cache),
        "checkpoints": checkpoints,
        "top_logits": {
            root: {str(VALUES[idx] if VALUES[idx] is not None else "*"): round(value, 4) for idx, value in enumerate(values)}
            for root, values in sorted(logits.items())[:20]
        },
    }
    return best, diagnostics


def benchmark_final(spec: MarkingSpec, args: argparse.Namespace) -> dict[str, object]:
    baseline_orientations = build_hat_orientations(None)
    marked_orientations = build_hat_orientations(spec)
    common = {
        "seed": args.seed,
        "target_tiles": args.benchmark_target_tiles,
        "target_corona": args.benchmark_target_corona,
        "max_steps": args.benchmark_max_steps,
        "node_limit": args.benchmark_node_limit,
        "wall_time_ms": args.benchmark_wall_time_ms,
        "frontier_limit": args.frontier_limit,
        "candidate_limit": args.candidate_limit,
        "boundary_alive": not args.no_boundary_alive,
    }
    baseline = run_tree_search(orientations=baseline_orientations, weights={}, policy="heuristic", **common)
    marked = run_tree_search(orientations=marked_orientations, weights={}, policy="heuristic", **common)
    return {"baseline": summarize(baseline), "marked": summarize(marked)}


def search_eval(
    spec: MarkingSpec,
    args: argparse.Namespace,
    cache: dict[MarkingSpec, tuple[float, dict[str, object]]],
) -> tuple[float, dict[str, object]]:
    cached = cache.get(spec)
    if cached is not None:
        return cached
    result = run_tree_search(
        orientations=build_hat_orientations(spec),
        weights={},
        seed=args.seed,
        policy=args.tree_policy,
        target_tiles=args.search_eval_target_tiles,
        target_corona=args.search_eval_target_corona,
        max_steps=args.search_eval_max_steps,
        node_limit=args.search_eval_node_limit,
        wall_time_ms=args.search_eval_wall_time_ms,
        frontier_limit=args.frontier_limit,
        candidate_limit=args.candidate_limit,
        boundary_alive=not args.no_boundary_alive,
    )
    summary = summarize(result)
    score = float(result.reward) - args.search_decision_penalty * result.decisions
    cached = (score, summary)
    cache[spec] = cached
    return cached


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-mode", choices=["lattice"], default="lattice")
    parser.add_argument("--lattice-base", choices=["tile", "boundary"], default="boundary")
    parser.add_argument("--lattice-reach", type=int, default=1)
    parser.add_argument("--max-lattice-reach", type=int, default=1)
    parser.add_argument("--channels", type=int, choices=[1, 3], default=3)
    parser.add_argument("--side-action", choices=["opposite", "constant"], default="constant")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--frontier-limit", type=int, default=9)
    parser.add_argument("--candidate-limit", type=int, default=10)
    parser.add_argument("--tree-policy", choices=["heuristic", "random"], default="heuristic")
    parser.add_argument("--no-boundary-alive", action="store_true")
    parser.add_argument("--online-contact-scope", choices=["neighbors", "all"], default="all")
    parser.add_argument("--online-max-bad-pairs-per-tile", type=int, default=0)
    parser.add_argument("--online-min-good", type=int, default=1)
    parser.add_argument("--online-min-bad", type=int, default=1)
    parser.add_argument("--max-good-for-bad", type=int, default=0)
    parser.add_argument("--online-scope-bad-clauses", action="store_true")
    parser.add_argument("--online-marked-boundary-alive", action="store_true")
    parser.add_argument("--online-learn-boundary-failures", action="store_true")
    parser.add_argument("--no-online-validate-updates", action="store_true")
    parser.add_argument("--signal-episodes", type=int, default=1)
    parser.add_argument("--signal-target-tiles", type=int, default=120)
    parser.add_argument("--signal-target-corona", type=int, default=5)
    parser.add_argument("--signal-max-steps", type=int, default=160)
    parser.add_argument("--signal-node-limit", type=int, default=8000)
    parser.add_argument("--signal-wall-time-ms", type=int, default=20000)
    parser.add_argument("--train-episodes", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=48)
    parser.add_argument("--elite-fraction", type=float, default=0.2)
    parser.add_argument("--elite-smoothing", type=float, default=0.25)
    parser.add_argument("--learning-rate", type=float, default=0.6)
    parser.add_argument("--star-bias", type=float, default=-0.4)
    parser.add_argument("--clause-reward", type=float, default=100.0)
    parser.add_argument("--edge-reward", type=float, default=30.0)
    parser.add_argument("--unique-reward", type=float, default=20.0)
    parser.add_argument("--density-reward", type=float, default=10.0)
    parser.add_argument("--positive-conflict-penalty", type=float, default=1000.0)
    parser.add_argument(
        "--search-eval-elites",
        type=int,
        default=0,
        help="Run short marked GCTS evaluations for this many locally elite sections per training episode.",
    )
    parser.add_argument("--search-reward-weight", type=float, default=1.0)
    parser.add_argument("--search-decision-penalty", type=float, default=0.01)
    parser.add_argument("--search-eval-target-tiles", type=int, default=80)
    parser.add_argument("--search-eval-target-corona", type=int, default=5)
    parser.add_argument("--search-eval-max-steps", type=int, default=120)
    parser.add_argument("--search-eval-node-limit", type=int, default=1500)
    parser.add_argument("--search-eval-wall-time-ms", type=int, default=2500)
    parser.add_argument("--report-every", type=int, default=5)
    parser.add_argument("--benchmark-target-tiles", type=int, default=120)
    parser.add_argument("--benchmark-target-corona", type=int, default=5)
    parser.add_argument("--benchmark-max-steps", type=int, default=160)
    parser.add_argument("--benchmark-node-limit", type=int, default=8000)
    parser.add_argument("--benchmark-wall-time-ms", type=int, default=20000)
    parser.add_argument("--skip-final-benchmark", action="store_true")
    parser.add_argument("--output", default="runs/hat-marking-rl.json")
    return parser.parse_args()


def main() -> None:
    args = read_args()
    args.episodes = args.train_episodes
    started = time.perf_counter()
    reach_results = []
    best_overall: ScoredAssignment | None = None
    best_signals: SignalSet | None = None
    best_training: dict[str, object] | None = None
    for reach in range(args.lattice_reach, args.max_lattice_reach + 1):
        signals = collect_signals(args, reach)
        best, training = train_reach(signals, args)
        reach_result = {
            "reach": reach,
            "signals": signals.collector_summary,
            "training": training,
            "best_metrics": best.metrics,
        }
        reach_results.append(reach_result)
        if best_overall is None or best.reward > best_overall.reward:
            best_overall = best
            best_signals = signals
            best_training = training

    if best_overall is None or best_signals is None or best_training is None:
        raise RuntimeError("no reach produced a trained marking")

    positive_validation = validate_positive_paths(best_overall.spec, best_signals.sample)
    graph_args = graph_metric_args(args)
    graph_metrics = {
        "baseline": point_candidate_graph_metrics(None, graph_args),
        "marked": point_candidate_graph_metrics(best_overall.spec, graph_args),
    }
    benchmark = None if args.skip_final_benchmark else benchmark_final(best_overall.spec, args)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "config": vars(args),
        "best_reach": best_signals.reach,
        "marking_support": [
            {
                "name": mark.name,
                "point": list(mark.point),
                "component": mark.component,
                "edge": mark.edge,
                "offset": list(mark.offset) if mark.offset is not None else None,
            }
            for mark in best_signals.scheme
        ],
        "marking": {
            "name": best_overall.spec.name,
            "segments": segment_payload(best_overall.spec),
        },
        "best_metrics": best_overall.metrics,
        "positive_path_validation": positive_validation,
        "single_tile_candidate_graph": graph_metrics,
        "benchmark": benchmark,
        "reach_results": reach_results,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "best_reach": payload["best_reach"],
                "best_metrics": payload["best_metrics"],
                "positive_path_validation": payload["positive_path_validation"],
                "single_tile_candidate_graph": payload["single_tile_candidate_graph"],
                "benchmark": payload["benchmark"],
            },
            indent=2,
        )
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
