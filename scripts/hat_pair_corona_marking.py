#!/usr/bin/env python3
"""Train Hat markings from two-hat local corona completion labels.

Workflow:

1. enumerate every legal placement of a second Hat against a fixed seed Hat;
2. for each seed+candidate pair, run a local tree search that tries to fill the
   original angle-deficit points around that two-tile patch;
3. label pair contacts positive if that local 1-corona completion succeeds and
   negative otherwise;
4. train the rank-3 marking from those positive equalities and negative
   disequality clauses;
5. benchmark the learned marking against unmarked GCTS.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from hat_marking_search import build_hat_orientations, segment_payload
from hat_sample_marking import (
    ProbeClause,
    ProbePair,
    benchmark_spec,
    contact_pairs_for_placement,
    mark_scheme,
    online_training_args,
    placement_contact_pair_counts,
    point_candidate_graph_metrics,
    probe_map,
    train_coloring,
    validate_positive_paths,
)
from turtle_gcts_rl import (
    Candidate,
    EpisodeResult,
    FrontierPoint,
    MAX_ANGLE,
    Placement,
    Point,
    TurtleState,
    candidate_keeps_boundary_alive,
    candidate_moves_for_frontier,
    frontier,
    key,
    max_corona,
    norm,
    order_candidates,
    place,
    mark_compatible_candidate,
    reward_for,
    run_tree_search,
)


def seed_state(orientations: list) -> tuple[TurtleState, Placement]:
    state = TurtleState(orientations)
    seed_placement = place(orientations[0], (0, 0, 0), "seed")
    state.add_placement(seed_placement, depth=0)
    return state, seed_placement


def two_hat_candidates(orientations: list, limit: int = 0) -> list[Candidate]:
    state, _ = seed_state(orientations)
    by_key: dict[str, Candidate] = {}
    for point in frontier(state):
        for candidate in candidate_moves_for_frontier(point, state):
            by_key.setdefault(candidate.pk, candidate)
    candidates = sorted(
        by_key.values(),
        key=lambda item: (norm(item.translation), item.orientation.idx, item.pk),
    )
    return candidates[:limit] if limit > 0 else candidates


def target_frontier_keys(state: TurtleState) -> tuple[str, ...]:
    return tuple(sorted(point_key for point_key, (_, value, _) in state.sums.items() if value < MAX_ANGLE))


def completion_reward(completed: int, total: int, tile_count: int, reason: str) -> float:
    reward = completed * 20.0 + tile_count
    if total and completed >= total:
        reward += 100.0
    if reason.startswith("dead") or reason in {"filtered_dead_frontier", "no_target_frontier_candidate"}:
        reward -= 25.0
    return reward


def complete_pair_corona(
    orientations: list,
    second: Candidate,
    args: argparse.Namespace,
    seed: int,
) -> tuple[bool, bool, EpisodeResult, list[Placement]]:
    started = time.perf_counter()
    deadline = started + args.pair_wall_time_ms / 1000.0 if args.pair_wall_time_ms > 0 else None
    rng = random.Random(seed)
    state, seed_placement = seed_state(orientations)
    second_placement = place(second.orientation, second.translation, second.pk)
    state.add_placement(second_placement, depth=1)
    targets = target_frontier_keys(state)
    total_targets = len(targets)
    nodes = 0
    forced_moves = 0
    branch_moves = 0
    dead_frontier_checks = 0
    stopped_reason = "searching"
    best_placements = state.placements[:]
    best_completed = sum(1 for point_key in targets if state.sums.get(point_key, (None, 0, 0))[1] >= MAX_ANGLE)
    best_reward = completion_reward(best_completed, total_targets, len(state.placements), "seed_pair")
    cutoff_observed = False

    def out_of_time() -> bool:
        if args.pair_exhaustive:
            return False
        return deadline is not None and time.perf_counter() >= deadline

    def target_points() -> list[FrontierPoint]:
        points = []
        for point_key in targets:
            current = state.sums.get(point_key)
            if current is None:
                continue
            point, value, depth = current
            if value < MAX_ANGLE:
                points.append(FrontierPoint(point, value, depth))
        return sorted(points, key=lambda item: (item.added_depth, norm(item.point), item.value, key(item.point)))

    def remember(reason: str) -> None:
        nonlocal best_completed, best_placements, best_reward, stopped_reason
        completed = total_targets - len(target_points())
        reward = completion_reward(completed, total_targets, len(state.placements), reason)
        if reward > best_reward or (
            math.isclose(reward, best_reward)
            and (completed, len(state.placements)) > (best_completed, len(best_placements))
        ):
            best_completed = completed
            best_placements = state.placements[:]
            best_reward = reward
            stopped_reason = reason

    def choose_target_option() -> tuple[str, tuple[FrontierPoint, list[Candidate]] | None]:
        options: list[tuple[FrontierPoint, list[Candidate]]] = []
        target_options = target_points()
        if args.pair_frontier_limit > 0 and not args.pair_exhaustive:
            target_options = target_options[: args.pair_frontier_limit]
        for point in target_options:
            candidates = candidate_moves_for_frontier(point, state)
            if not candidates:
                return f"dead_target_frontier:{key(point.point)}", None
            limited = (
                candidates
                if args.pair_exhaustive or args.pair_candidate_limit <= 0
                else candidates[: args.pair_candidate_limit]
            )
            options.append((point, limited))
        if not options:
            return "complete_pair_corona", None
        return "ok", sorted(
            options,
            key=lambda item: (
                len(item[1]),
                item[0].added_depth,
                norm(item[0].point),
                item[0].value,
            ),
        )[0]

    def search() -> bool:
        nonlocal nodes, forced_moves, branch_moves, dead_frontier_checks, stopped_reason, cutoff_observed
        if out_of_time():
            cutoff_observed = True
            stopped_reason = "wall_time_ms"
            remember(stopped_reason)
            return False
        if args.pair_node_limit > 0 and nodes >= args.pair_node_limit:
            cutoff_observed = True
            stopped_reason = "node_limit"
            remember(stopped_reason)
            return False
        if args.pair_max_tiles > 0 and len(state.placements) >= args.pair_max_tiles:
            cutoff_observed = True
            stopped_reason = "max_tiles"
            remember(stopped_reason)
            return False

        status, option = choose_target_option()
        if status == "complete_pair_corona":
            stopped_reason = status
            remember(stopped_reason)
            return True
        if status != "ok" or option is None:
            stopped_reason = status
            remember(stopped_reason)
            return False

        _, raw_candidates = option
        order_limit = 0 if args.pair_exhaustive else args.pair_candidate_limit
        candidates = order_candidates(raw_candidates, state, {}, rng, args.pair_policy, order_limit)
        filtered = []
        for candidate in candidates:
            if args.pair_boundary_alive and not args.pair_exhaustive and len(candidates) > 1:
                dead_frontier_checks += 1
                if not candidate_keeps_boundary_alive(candidate, state):
                    continue
            filtered.append(candidate)
        if not filtered:
            stopped_reason = "filtered_dead_frontier"
            remember(stopped_reason)
            return False

        is_forced = len(filtered) == 1
        for candidate in filtered:
            if out_of_time() or (args.pair_node_limit > 0 and nodes >= args.pair_node_limit):
                cutoff_observed = True
                break
            nodes += 1
            if is_forced:
                forced_moves += 1
            else:
                branch_moves += 1
            state.add_placement(place(candidate.orientation, candidate.translation, candidate.pk), depth=len(state.placements))
            if search():
                return True
            state.remove_last_placement()
        remember("exhausted")
        return False

    success = search()
    if stopped_reason == "searching":
        stopped_reason = "complete_pair_corona" if success else "exhausted"
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result = EpisodeResult(
        policy="pair-corona",
        seed=seed,
        elapsed_ms=elapsed_ms,
        tile_count=len(best_placements),
        corona=max_corona(best_placements),
        reward=completion_reward(best_completed, total_targets, len(best_placements), stopped_reason),
        stopped_reason=stopped_reason,
        decisions=forced_moves + branch_moves,
        forced_moves=forced_moves,
        branch_moves=branch_moves,
        dead_frontier_checks=dead_frontier_checks,
        placements=best_placements,
        trajectory=[],
    )
    proof_complete = success or (
        not cutoff_observed
        and (args.pair_exhaustive or stopped_reason.startswith("dead_target_frontier:"))
    )
    return success, proof_complete, result, best_placements


def proven_negative(result: EpisodeResult, proof_complete: bool) -> bool:
    return proof_complete and (
        result.stopped_reason == "exhausted" or result.stopped_reason.startswith("dead_target_frontier:")
    )


def validate_seed_pair_marking(spec, candidates: list[Candidate], rows: list[dict[str, object]]) -> dict[str, object]:
    labels = {str(row["placement_key"]): str(row["label"]) for row in rows}
    marked_orientations = build_hat_orientations(spec)
    marked_state, _ = seed_state(marked_orientations)
    passed: Counter[str] = Counter()
    failed: Counter[str] = Counter()
    negative_passes = []
    positive_failures = []
    for candidate in candidates:
        label = labels[candidate.pk]
        marked_candidate = mark_compatible_candidate(
            marked_orientations[candidate.orientation.idx],
            candidate,
            marked_state,
        )
        if marked_candidate is None:
            failed[label] += 1
            if label == "positive":
                positive_failures.append(candidate.pk)
        else:
            passed[label] += 1
            if label == "negative":
                negative_passes.append(candidate.pk)
    return {
        "passed": dict(passed),
        "failed": dict(failed),
        "negative_passes": negative_passes,
        "positive_failures": positive_failures,
        "negative_pass_count": len(negative_passes),
        "positive_failure_count": len(positive_failures),
    }


def train_from_pair_labels(args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(None)
    scheme = mark_scheme(args.probe_mode, args.lattice_reach, args.channels, args.lattice_base)
    candidates = two_hat_candidates(orientations, args.pair_limit)
    _, seed_placement = seed_state(orientations)
    seed_probe_map = probe_map([seed_placement], scheme)
    good_counts: Counter[ProbePair] = Counter()
    bad_counts: Counter[ProbePair] = Counter()
    bad_clauses: Counter[ProbeClause] = Counter()
    positive_paths: list[list[Placement]] = []
    rows = []
    positive_patch_rows = []
    started = time.perf_counter()

    for index, candidate in enumerate(candidates):
        candidate_placement = place(candidate.orientation, candidate.translation, candidate.pk)
        contacts = tuple(sorted(contact_pairs_for_placement(candidate_placement, seed_probe_map, scheme)))
        success, proof_complete, result, path = complete_pair_corona(orientations, candidate, args, args.seed + index * 17)
        label = "positive" if success else "negative" if proven_negative(result, proof_complete) else "inconclusive"
        if contacts:
            if label == "positive":
                good_counts.update(contacts)
                good_counts.update(placement_contact_pair_counts(path, scheme, neighbors_only=False))
                positive_paths.append(path)
            elif label == "negative":
                bad_counts.update(contacts)
                bad_clauses[contacts] += 1
        rows.append(
            {
                "index": index,
                "placement_key": candidate.pk,
                "orientation": candidate.orientation.idx,
                "translation": list(candidate.translation),
                "contacts": len(contacts),
                "label": label,
                "proof_complete": proof_complete,
                "stop": result.stopped_reason,
                "elapsed_ms": result.elapsed_ms,
                "tiles": result.tile_count,
                "decisions": result.decisions,
            }
        )

    for run_index in range(args.positive_patch_runs):
        run_seed = args.seed + args.positive_patch_seed_offset + run_index * 101
        result = run_tree_search(
            orientations=orientations,
            weights={},
            seed=run_seed,
            policy=args.pair_policy,
            target_tiles=args.positive_patch_target_tiles,
            target_corona=args.positive_patch_target_corona,
            max_steps=args.positive_patch_max_steps,
            node_limit=args.positive_patch_node_limit,
            wall_time_ms=args.positive_patch_wall_time_ms,
            frontier_limit=args.frontier_limit,
            candidate_limit=args.candidate_limit,
            boundary_alive=not args.no_boundary_alive,
        )
        if result.corona >= args.positive_patch_min_corona:
            good_counts.update(placement_contact_pair_counts(result.placements, scheme, neighbors_only=False))
            positive_paths.append(result.placements)
            accepted = True
        else:
            accepted = False
        positive_patch_rows.append(
            {
                "run": run_index,
                "seed": run_seed,
                "accepted": accepted,
                "elapsed_ms": result.elapsed_ms,
                "tiles": result.tile_count,
                "corona": result.corona,
                "decisions": result.decisions,
                "stop": result.stopped_reason,
            }
        )

    inconclusive_count = sum(1 for row in rows if row["label"] == "inconclusive")
    dataset_complete = inconclusive_count == 0 and args.pair_limit == 0
    if args.require_complete_dataset and not dataset_complete:
        raise RuntimeError(
            f"fixed marking refused: {inconclusive_count} pair labels are inconclusive and "
            f"pair_limit={args.pair_limit}; enumerate every pair and remove all local search caps, "
            "or rerun without --require-complete-dataset for an exploratory artifact"
        )

    sample: dict[str, object] = {
        "good_counts": good_counts,
        "branch_equalities": good_counts,
        "bad_counts": bad_counts,
        "bad_clauses": bad_clauses,
        "positive_paths": positive_paths,
        "episodes": [
            {
                "episode": 0,
                "tiles": max((len(path) for path in positive_paths), default=0),
                "stop": "pair_corona_dataset",
                "positive_pairs": sum(1 for row in rows if row["label"] == "positive"),
                "negative_pairs": sum(1 for row in rows if row["label"] == "negative"),
            }
        ],
    }
    training_args = online_training_args(args)
    spec, diagnostics = train_coloring(sample, training_args, scheme)
    validation = validate_positive_paths(spec, sample)
    seed_pair_validation = validate_seed_pair_marking(spec, candidates, rows)
    graph_metrics = {
        "baseline": point_candidate_graph_metrics(None, args),
        "marked": point_candidate_graph_metrics(spec, args),
    }
    benchmark = benchmark_spec(spec, args)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "config": vars(args),
        "marking_support": [
            {
                "name": mark.name,
                "point": list(mark.point),
                "component": mark.component,
                "edge": mark.edge,
                "offset": list(mark.offset) if mark.offset is not None else None,
            }
            for mark in scheme
        ],
        "dataset": {
            "complete": dataset_complete,
            "candidate_pairs": len(candidates),
            "positive_pairs": sum(1 for row in rows if row["label"] == "positive"),
            "negative_pairs": sum(1 for row in rows if row["label"] == "negative"),
            "inconclusive_pairs": sum(1 for row in rows if row["label"] == "inconclusive"),
            "contactless_pairs": sum(1 for row in rows if row["contacts"] == 0),
            "good_contact_observations": sum(good_counts.values()),
            "bad_contact_observations": sum(bad_counts.values()),
            "unique_good_contacts": len(good_counts),
            "unique_bad_contacts": len(bad_counts),
            "bad_clauses": len(bad_clauses),
            "positive_patch_runs": positive_patch_rows,
            "rows": rows,
        },
        "marking": {
            "name": spec.name,
            "frozen": dataset_complete,
            "segments": segment_payload(spec),
        },
        "training": diagnostics,
        "positive_path_validation": validation,
        "seed_pair_marking_validation": seed_pair_validation,
        "single_tile_candidate_graph": graph_metrics,
        "benchmark": benchmark,
    }


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-mode", choices=["lattice"], default="lattice")
    parser.add_argument("--lattice-base", choices=["tile", "boundary"], default="boundary")
    parser.add_argument("--lattice-reach", type=int, default=1)
    parser.add_argument("--channels", type=int, choices=[1, 3], default=3)
    parser.add_argument("--side-action", choices=["opposite", "constant"], default="constant")
    parser.add_argument("--assignment-mode", choices=["random", "coloring"], default="random")
    parser.add_argument("--assignment-seed", type=int, default=0)
    parser.add_argument("--assignment-trials", type=int, default=200)
    parser.add_argument("--assignment-steps", type=int, default=0)
    parser.add_argument("--assignment-lock-initial", action="store_true")
    parser.add_argument("--assignment-fill-unassigned", action="store_true")
    parser.add_argument("--min-good", type=int, default=1)
    parser.add_argument("--min-bad", type=int, default=1)
    parser.add_argument("--online-min-good", type=int, default=1)
    parser.add_argument("--online-min-bad", type=int, default=1)
    parser.add_argument("--max-good-for-bad", type=int, default=0)
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--frontier-limit", type=int, default=9)
    parser.add_argument("--candidate-limit", type=int, default=10)
    parser.add_argument("--pair-limit", type=int, default=0, help="Limit enumerated two-hat candidates; 0 means all.")
    parser.add_argument(
        "--pair-exhaustive",
        action="store_true",
        help="Exhaustively search the finite local tree that fills the original two-hat frontier; capped failures become inconclusive unless this completes.",
    )
    parser.add_argument("--pair-frontier-limit", type=int, default=12)
    parser.add_argument("--pair-candidate-limit", type=int, default=12)
    parser.add_argument("--pair-node-limit", type=int, default=1500)
    parser.add_argument("--pair-wall-time-ms", type=int, default=1000)
    parser.add_argument("--pair-max-tiles", type=int, default=24)
    parser.add_argument(
        "--require-complete-dataset",
        action="store_true",
        help="Refuse to train/freeze a marking if any two-tile placement remains inconclusive.",
    )
    parser.add_argument("--pair-policy", choices=["heuristic", "random"], default="heuristic")
    parser.add_argument("--pair-boundary-alive", action="store_true")
    parser.add_argument(
        "--positive-patch-runs",
        type=int,
        default=0,
        help="Add contacts from this many successful unmarked GCTS patches as protected positive equalities.",
    )
    parser.add_argument("--positive-patch-seed-offset", type=int, default=10_000)
    parser.add_argument("--positive-patch-target-tiles", type=int, default=120)
    parser.add_argument("--positive-patch-target-corona", type=int, default=5)
    parser.add_argument("--positive-patch-min-corona", type=int, default=5)
    parser.add_argument("--positive-patch-max-steps", type=int, default=160)
    parser.add_argument("--positive-patch-node-limit", type=int, default=8000)
    parser.add_argument("--positive-patch-wall-time-ms", type=int, default=20000)
    parser.add_argument("--benchmark-target-tiles", type=int, default=120)
    parser.add_argument("--benchmark-target-corona", type=int, default=5)
    parser.add_argument("--benchmark-max-steps", type=int, default=160)
    parser.add_argument("--node-limit", type=int, default=8000)
    parser.add_argument("--wall-time-ms", type=int, default=20000)
    parser.add_argument("--no-boundary-alive", action="store_true")
    parser.add_argument("--static-filter-boundary", choices=["off", "geometric", "marked", "both"], default="geometric")
    parser.add_argument("--static-filter-frontier", action="store_true")
    parser.add_argument("--output", default="runs/hat-pair-corona-marking.json")
    return parser.parse_args()


def main() -> None:
    args = read_args()
    args.episodes = 1
    payload = train_from_pair_labels(args)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "dataset": {k: v for k, v in payload["dataset"].items() if k != "rows"},
                "training": payload["training"],
                "positive_path_validation": payload["positive_path_validation"],
                "seed_pair_marking_validation": payload["seed_pair_marking_validation"],
                "single_tile_candidate_graph": payload["single_tile_candidate_graph"],
                "benchmark": payload["benchmark"],
            },
            indent=2,
        )
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
