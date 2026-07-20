#!/usr/bin/env python3
"""Benchmark Hat growth by first-hit corona layer times."""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from hat_marking_search import (
    MarkingSpec,
    build_hat_orientations,
    mined_edge_marking_specs,
    substitution_orientation_placements,
)
from hat_sample_marking import ProbeClause, ProbePair, mark_scheme, run_online_tree_episode
from turtle_gcts_rl import (
    Candidate,
    FrontierPoint,
    Placement,
    Point,
    TurtleState,
    candidate_keeps_boundary_alive,
    choose_frontier_option,
    key,
    mark_compatible_candidate,
    max_corona,
    order_candidates,
    place,
    reward_for,
    run_mark_filter_tree_search,
    run_tree_search,
    sub,
)


def load_probe_or_site_spec(path: Path) -> MarkingSpec:
    data = json.loads(path.read_text(encoding="utf-8"))
    segments = data["marking"]["segments"]
    if not isinstance(segments, dict):
        raise ValueError(f"{path} does not contain dict-valued marking.segments")

    def convert_probe(items: object) -> tuple[tuple[int, Point, int], ...]:
        return tuple((int(edge), tuple(offset), int(value)) for edge, offset, value in items)  # type: ignore[misc]

    def convert_site(items: object) -> tuple[tuple[Point, int, int], ...]:
        out = []
        for item in items:  # type: ignore[union-attr]
            if len(item) == 2:
                point, value = item
                component = 0
            else:
                point, component, value = item
            out.append((tuple(point), int(component), int(value)))
        return tuple(out)

    return MarkingSpec(
        str(data["marking"]["name"]),
        fore_probe_marks=convert_probe(segments.get("probe_fore", [])),
        rear_probe_marks=convert_probe(segments.get("probe_rear", [])),
        fore_site_marks=convert_site(segments.get("site_fore", [])),
        rear_site_marks=convert_site(segments.get("site_rear", [])),
    )


def run_growth_series(name: str, spec: MarkingSpec | None, args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(spec)
    hits: dict[int, dict[str, int]] = {}

    def callback(layer: int, elapsed_ms: int, tile_count: int, decisions: int) -> None:
        if layer == 0 or layer > args.max_layers or layer in hits:
            return
        hits[layer] = {
            "layer": layer,
            "elapsed_ms": elapsed_ms,
            "tile_count": tile_count,
            "decisions": decisions,
        }

    result = run_tree_search(
        orientations=orientations,
        weights={},
        seed=args.seed,
        policy="heuristic",
        target_tiles=args.target_tiles,
        target_corona=args.max_layers,
        max_steps=args.max_steps,
        node_limit=args.node_limit,
        wall_time_ms=args.wall_time_ms,
        frontier_limit=args.frontier_limit,
        candidate_limit=args.candidate_limit,
        boundary_alive=not args.no_boundary_alive,
        growth_callback=callback,
    )
    return {
        "name": name,
        "kind": "gcts",
        "summary": {
            "elapsed_ms": result.elapsed_ms,
            "tile_count": result.tile_count,
            "corona": result.corona,
            "stopped_reason": result.stopped_reason,
            "decisions": result.decisions,
            "forced_moves": result.forced_moves,
            "branch_moves": result.branch_moves,
            "dead_frontier_checks": result.dead_frontier_checks,
        },
        "hits": [hits[layer] for layer in sorted(hits)],
    }


def run_mark_filter_growth_series(name: str, spec: MarkingSpec, args: argparse.Namespace) -> dict[str, object]:
    base_orientations = build_hat_orientations(None)
    marked_orientations = build_hat_orientations(spec)
    hits: dict[int, dict[str, int]] = {}

    def callback(layer: int, elapsed_ms: int, tile_count: int, decisions: int) -> None:
        if layer == 0 or layer > args.max_layers or layer in hits:
            return
        hits[layer] = {
            "layer": layer,
            "elapsed_ms": elapsed_ms,
            "tile_count": tile_count,
            "decisions": decisions,
        }

    result, filter_stats = run_mark_filter_tree_search(
        base_orientations=base_orientations,
        marked_orientations=marked_orientations,
        weights={},
        seed=args.seed,
        policy=args.policy,
        target_tiles=args.target_tiles,
        target_corona=args.max_layers,
        max_steps=args.max_steps,
        node_limit=args.node_limit,
        wall_time_ms=args.wall_time_ms,
        frontier_limit=args.frontier_limit,
        candidate_limit=args.candidate_limit,
        boundary_alive=not args.no_boundary_alive,
        filter_boundary_mode=args.static_filter_boundary,
        filter_frontier=args.static_filter_frontier,
        growth_callback=callback,
    )
    return {
        "name": name,
        "kind": "gcts-mark-filter",
        "summary": {
            "elapsed_ms": result.elapsed_ms,
            "tile_count": result.tile_count,
            "corona": result.corona,
            "stopped_reason": result.stopped_reason,
            "decisions": result.decisions,
            "forced_moves": result.forced_moves,
            "branch_moves": result.branch_moves,
            "dead_frontier_checks": result.dead_frontier_checks,
            **filter_stats,
        },
        "hits": [hits[layer] for layer in sorted(hits)],
    }


def inverse_transform(point: Point, sym) -> Point:
    out = [0, 0, 0]
    for source_index, target_index in enumerate(sym.permutation):
        out[target_index] = sym.sign * point[source_index]
    return (out[0], out[1], out[2])


def placement_occupancy_keys(placement: Placement) -> set[str]:
    return {key(entry.point) for entry in placement.occupancy}


def candidate_occupancy_keys(candidate: Candidate) -> set[str]:
    return {
        key(
            (
                entry.point[0] + candidate.translation[0],
                entry.point[1] + candidate.translation[1],
                entry.point[2] + candidate.translation[2],
            )
        )
        for entry in candidate.orientation.occupancy
    }


def load_negative_pair_oracle(path: Path) -> set[tuple[int, Point]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("dataset", {}).get("rows", [])
    return {
        (int(row["orientation"]), tuple(row["translation"]))
        for row in rows
        if row.get("label") == "negative"
    }


def load_residual_negative_pair_oracle(path: Path, spec: MarkingSpec) -> set[tuple[int, Point]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("dataset", {}).get("rows", [])
    base_orientations = build_hat_orientations(None)
    marked_orientations = build_hat_orientations(spec)
    marked_state = TurtleState(marked_orientations)
    marked_state.add_placement(place(marked_orientations[0], (0, 0, 0), "seed"), depth=0)
    dummy_frontier = FrontierPoint((0, 0, 0), 0, 0)
    residual = set()
    for row in rows:
        if row.get("label") != "negative":
            continue
        orientation_idx = int(row["orientation"])
        translation = tuple(row["translation"])
        candidate = Candidate(
            orientation=base_orientations[orientation_idx],
            translation=translation,
            pk=str(row["placement_key"]),
            frontier=dummy_frontier,
            anchor_value=0,
            score=0,
            line_matches=0,
            new_points=0,
            overlap_points=0,
            fill_value=0,
        )
        if mark_compatible_candidate(marked_orientations[orientation_idx], candidate, marked_state) is not None:
            residual.add((orientation_idx, translation))
    return residual


def run_pair_oracle_growth_series(name: str, args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(None)
    negative_pairs = load_negative_pair_oracle(Path(args.lattice_marking))
    orientation_by_vertices = {tuple(sorted(orientation.vertices)): orientation.idx for orientation in orientations}
    hits: dict[int, dict[str, int]] = {}
    started = time.perf_counter()
    deadline = started + args.wall_time_ms / 1000.0 if args.wall_time_ms > 0 else None
    rng = random.Random(args.seed)
    effective_node_limit = args.node_limit if args.node_limit > 0 else max(800, args.max_layers * args.max_layers * 64)
    state = TurtleState(orientations)
    seed_placement = place(orientations[0], (0, 0, 0), "seed")
    state.add_placement(seed_placement, depth=0)
    occupancy_stack = [placement_occupancy_keys(seed_placement)]

    nodes = 0
    forced_moves = 0
    branch_moves = 0
    dead_frontier_checks = 0
    pair_oracle_checks = 0
    pair_oracle_filtered = 0
    best_placements = state.placements[:]
    best_corona = 0
    best_reward = reward_for(1, 0, "seed", args.target_tiles, args.max_layers)
    stopped_reason = "searching"
    max_reported_corona = -1

    def out_of_time() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def callback(layer: int, elapsed_ms: int, tile_count: int, decisions: int) -> None:
        if layer == 0 or layer > args.max_layers or layer in hits:
            return
        hits[layer] = {
            "layer": layer,
            "elapsed_ms": elapsed_ms,
            "tile_count": tile_count,
            "decisions": decisions,
        }

    def report_growth(corona: int) -> None:
        nonlocal max_reported_corona
        if corona <= max_reported_corona:
            return
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        decisions = forced_moves + branch_moves
        for layer in range(max_reported_corona + 1, corona + 1):
            callback(layer, elapsed_ms, len(state.placements), decisions)
        max_reported_corona = corona

    def remember(reason: str, corona: int | None = None) -> None:
        nonlocal best_placements, best_corona, best_reward, stopped_reason
        if corona is None:
            corona = max_corona(state.placements)
        current_reward = reward_for(len(state.placements), corona, reason, args.target_tiles, args.max_layers)
        if current_reward > best_reward or (
            math.isclose(current_reward, best_reward)
            and (len(state.placements), corona) > (len(best_placements), best_corona)
        ):
            best_placements = state.placements[:]
            best_corona = corona
            best_reward = current_reward
            stopped_reason = reason

    def relative_signature(reference: Placement, candidate: Candidate) -> tuple[int, Point]:
        local_vertices = tuple(
            sorted(inverse_transform(point, reference.orientation.sym) for point in candidate.orientation.vertices)
        )
        orientation_idx = orientation_by_vertices[local_vertices]
        local_translation = inverse_transform(sub(candidate.translation, reference.translation), reference.orientation.sym)
        return orientation_idx, local_translation

    def pair_oracle_allows(candidate: Candidate) -> bool:
        nonlocal pair_oracle_checks
        candidate_keys = candidate_occupancy_keys(candidate)
        for placement, placement_keys in zip(state.placements, occupancy_stack):
            if candidate_keys.isdisjoint(placement_keys):
                continue
            pair_oracle_checks += 1
            if relative_signature(placement, candidate) in negative_pairs:
                return False
        return True

    def search() -> bool:
        nonlocal nodes, forced_moves, branch_moves, dead_frontier_checks, pair_oracle_filtered, stopped_reason
        if out_of_time():
            stopped_reason = "wall_time_ms"
            remember(stopped_reason)
            return False
        corona = max_corona(state.placements)
        report_growth(corona)
        remember("partial", corona)
        if len(state.placements) >= args.target_tiles:
            stopped_reason = "target_tiles"
            remember(stopped_reason, corona)
            return True
        if corona >= args.max_layers:
            stopped_reason = "target_corona"
            remember(stopped_reason, corona)
            return True
        if len(state.placements) >= args.max_steps:
            remember("max_steps", corona)
            return False
        if nodes >= effective_node_limit:
            stopped_reason = "node_limit"
            remember(stopped_reason, corona)
            return False

        status, option = choose_frontier_option(state, args.frontier_limit, args.candidate_limit)
        if status != "ok" or option is None:
            remember(status)
            return False

        _, raw_candidates = option
        candidates = order_candidates(raw_candidates, state, {}, rng, args.policy, args.candidate_limit)
        filtered_candidates = []
        for candidate in candidates:
            if not pair_oracle_allows(candidate):
                pair_oracle_filtered += 1
                continue
            if not args.no_boundary_alive and len(candidates) > 1:
                dead_frontier_checks += 1
                if not candidate_keeps_boundary_alive(candidate, state):
                    continue
            filtered_candidates.append(candidate)
        if not filtered_candidates:
            remember("pair_oracle_dead_frontier")
            return False

        is_forced = len(filtered_candidates) == 1
        for candidate in filtered_candidates:
            if out_of_time():
                stopped_reason = "wall_time_ms"
                break
            if nodes >= effective_node_limit:
                stopped_reason = "node_limit"
                break
            nodes += 1
            if is_forced:
                forced_moves += 1
            else:
                branch_moves += 1
            placement = place(candidate.orientation, candidate.translation, candidate.pk)
            state.add_placement(placement, depth=len(state.placements))
            occupancy_stack.append(placement_occupancy_keys(placement))
            if search():
                return True
            occupancy_stack.pop()
            state.remove_last_placement()
        remember("exhausted")
        return False

    search()
    if stopped_reason == "searching":
        stopped_reason = "exhausted"
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "name": name,
        "kind": "gcts-pair-oracle-filter",
        "summary": {
            "elapsed_ms": elapsed_ms,
            "tile_count": len(best_placements),
            "corona": max_corona(best_placements),
            "stopped_reason": stopped_reason,
            "decisions": forced_moves + branch_moves,
            "forced_moves": forced_moves,
            "branch_moves": branch_moves,
            "dead_frontier_checks": dead_frontier_checks,
            "pair_oracle_checks": pair_oracle_checks,
            "pair_oracle_filtered_candidates": pair_oracle_filtered,
            "negative_pair_labels": len(negative_pairs),
        },
        "hits": [hits[layer] for layer in sorted(hits)],
    }


def run_residual_pair_growth_series(name: str, spec: MarkingSpec, args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(None)
    marked_orientations = build_hat_orientations(spec)
    residual_negative_pairs = load_residual_negative_pair_oracle(Path(args.lattice_marking), spec)
    orientation_by_vertices = {tuple(sorted(orientation.vertices)): orientation.idx for orientation in orientations}
    hits: dict[int, dict[str, int]] = {}
    started = time.perf_counter()
    deadline = started + args.wall_time_ms / 1000.0 if args.wall_time_ms > 0 else None
    rng = random.Random(args.seed)
    effective_node_limit = args.node_limit if args.node_limit > 0 else max(800, args.max_layers * args.max_layers * 64)
    state = TurtleState(orientations)
    marked_state = TurtleState(marked_orientations)
    seed_placement = place(orientations[0], (0, 0, 0), "seed")
    marked_seed = place(marked_orientations[0], (0, 0, 0), "seed")
    state.add_placement(seed_placement, depth=0)
    marked_state.add_placement(marked_seed, depth=0)
    occupancy_stack = [placement_occupancy_keys(seed_placement)]

    nodes = 0
    forced_moves = 0
    branch_moves = 0
    dead_frontier_checks = 0
    marked_filtered = 0
    residual_checks = 0
    residual_filtered = 0
    best_placements = state.placements[:]
    best_corona = 0
    best_reward = reward_for(1, 0, "seed", args.target_tiles, args.max_layers)
    stopped_reason = "searching"
    max_reported_corona = -1

    def out_of_time() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def callback(layer: int, elapsed_ms: int, tile_count: int, decisions: int) -> None:
        if layer == 0 or layer > args.max_layers or layer in hits:
            return
        hits[layer] = {
            "layer": layer,
            "elapsed_ms": elapsed_ms,
            "tile_count": tile_count,
            "decisions": decisions,
        }

    def report_growth(corona: int) -> None:
        nonlocal max_reported_corona
        if corona <= max_reported_corona:
            return
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        decisions = forced_moves + branch_moves
        for layer in range(max_reported_corona + 1, corona + 1):
            callback(layer, elapsed_ms, len(state.placements), decisions)
        max_reported_corona = corona

    def remember(reason: str, corona: int | None = None) -> None:
        nonlocal best_placements, best_corona, best_reward, stopped_reason
        if corona is None:
            corona = max_corona(state.placements)
        current_reward = reward_for(len(state.placements), corona, reason, args.target_tiles, args.max_layers)
        if current_reward > best_reward or (
            math.isclose(current_reward, best_reward)
            and (len(state.placements), corona) > (len(best_placements), best_corona)
        ):
            best_placements = state.placements[:]
            best_corona = corona
            best_reward = current_reward
            stopped_reason = reason

    def relative_signature(reference: Placement, candidate: Candidate) -> tuple[int, Point]:
        local_vertices = tuple(
            sorted(inverse_transform(point, reference.orientation.sym) for point in candidate.orientation.vertices)
        )
        orientation_idx = orientation_by_vertices[local_vertices]
        local_translation = inverse_transform(sub(candidate.translation, reference.translation), reference.orientation.sym)
        return orientation_idx, local_translation

    def residual_pair_allows(candidate: Candidate) -> bool:
        nonlocal residual_checks
        if not residual_negative_pairs:
            return True
        candidate_keys = candidate_occupancy_keys(candidate)
        for placement, placement_keys in zip(state.placements, occupancy_stack):
            if candidate_keys.isdisjoint(placement_keys):
                continue
            residual_checks += 1
            if relative_signature(placement, candidate) in residual_negative_pairs:
                return False
        return True

    def search() -> bool:
        nonlocal nodes, forced_moves, branch_moves, dead_frontier_checks
        nonlocal marked_filtered, residual_filtered, stopped_reason
        if out_of_time():
            stopped_reason = "wall_time_ms"
            remember(stopped_reason)
            return False
        corona = max_corona(state.placements)
        report_growth(corona)
        remember("partial", corona)
        if len(state.placements) >= args.target_tiles:
            stopped_reason = "target_tiles"
            remember(stopped_reason, corona)
            return True
        if corona >= args.max_layers:
            stopped_reason = "target_corona"
            remember(stopped_reason, corona)
            return True
        if len(state.placements) >= args.max_steps:
            remember("max_steps", corona)
            return False
        if nodes >= effective_node_limit:
            stopped_reason = "node_limit"
            remember(stopped_reason, corona)
            return False

        status, option = choose_frontier_option(state, args.frontier_limit, args.candidate_limit)
        if status != "ok" or option is None:
            remember(status)
            return False

        _, raw_candidates = option
        candidates = order_candidates(raw_candidates, state, {}, rng, args.policy, args.candidate_limit)
        filtered_candidates = []
        for candidate in candidates:
            marked_candidate = mark_compatible_candidate(
                marked_orientations[candidate.orientation.idx],
                candidate,
                marked_state,
            )
            if marked_candidate is None:
                marked_filtered += 1
                continue
            if not residual_pair_allows(candidate):
                residual_filtered += 1
                continue
            if not args.no_boundary_alive and len(candidates) > 1:
                dead_frontier_checks += 1
                if not candidate_keeps_boundary_alive(candidate, state):
                    continue
            filtered_candidates.append((candidate, marked_candidate))
        if not filtered_candidates:
            remember("residual_pair_dead_frontier")
            return False

        is_forced = len(filtered_candidates) == 1
        for candidate, marked_candidate in filtered_candidates:
            if out_of_time():
                stopped_reason = "wall_time_ms"
                break
            if nodes >= effective_node_limit:
                stopped_reason = "node_limit"
                break
            nodes += 1
            if is_forced:
                forced_moves += 1
            else:
                branch_moves += 1
            placement = place(candidate.orientation, candidate.translation, candidate.pk)
            marked_placement = place(marked_candidate.orientation, marked_candidate.translation, marked_candidate.pk)
            state.add_placement(placement, depth=len(state.placements))
            marked_state.add_placement(marked_placement, depth=len(marked_state.placements))
            occupancy_stack.append(placement_occupancy_keys(placement))
            if search():
                return True
            occupancy_stack.pop()
            marked_state.remove_last_placement()
            state.remove_last_placement()
        remember("exhausted")
        return False

    search()
    if stopped_reason == "searching":
        stopped_reason = "exhausted"
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "name": name,
        "kind": "gcts-marking-residual-pair-filter",
        "summary": {
            "elapsed_ms": elapsed_ms,
            "tile_count": len(best_placements),
            "corona": max_corona(best_placements),
            "stopped_reason": stopped_reason,
            "decisions": forced_moves + branch_moves,
            "forced_moves": forced_moves,
            "branch_moves": branch_moves,
            "dead_frontier_checks": dead_frontier_checks,
            "mark_filtered_candidates": marked_filtered,
            "residual_pair_checks": residual_checks,
            "residual_pair_filtered_candidates": residual_filtered,
            "residual_negative_pair_labels": len(residual_negative_pairs),
        },
        "hits": [hits[layer] for layer in sorted(hits)],
    }


def online_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        sample_wall_time_ms=args.wall_time_ms,
        sample_target_tiles=args.target_tiles,
        benchmark_target_corona=args.max_layers,
        max_steps=args.max_steps,
        node_limit=args.node_limit,
        frontier_limit=args.frontier_limit,
        candidate_limit=args.candidate_limit,
        no_boundary_alive=args.no_boundary_alive,
        tree_policy=args.policy,
        online_contact_scope=args.online_contact_scope,
        online_max_bad_pairs_per_tile=args.online_max_bad_pairs_per_tile,
        online_min_good=args.online_min_good,
        online_min_bad=args.online_min_bad,
        min_good=args.online_min_good,
        min_bad=args.online_min_bad,
        max_good_for_bad=args.max_good_for_bad,
        side_action=args.side_action,
        assignment_mode=args.assignment_mode,
        assignment_seed=args.assignment_seed,
        assignment_trials=args.assignment_trials,
        assignment_steps=args.assignment_steps,
        assignment_lock_initial=args.assignment_lock_initial,
        assignment_fill_unassigned=args.assignment_fill_unassigned,
        online_validate_updates=not args.no_online_validate_updates,
        online_learn_boundary_failures=args.online_learn_boundary_failures,
        online_hard_mark_filter=args.online_hard_mark_filter,
        online_hard_live_mark_filter=args.online_hard_live_mark_filter,
        online_child_section_filter=args.online_child_section_filter,
        online_scope_bad_clauses=args.online_scope_bad_clauses,
        online_marked_boundary_alive=args.online_marked_boundary_alive,
        online_trust_marked_candidates=args.online_trust_marked_candidates,
        probe_mode=args.probe_mode,
        episodes=1,
    )


def run_online_growth_series(args: argparse.Namespace) -> dict[str, object]:
    scheme = mark_scheme(args.probe_mode, args.lattice_reach, args.channels, args.lattice_base)
    learned_args = online_args(args)
    bad_counts: Counter[ProbePair] = Counter()
    bad_clauses: Counter[ProbeClause] = Counter()
    hits: dict[int, dict[str, int]] = {}

    def callback(layer: int, elapsed_ms: int, tile_count: int, decisions: int) -> None:
        if layer == 0 or layer > args.max_layers or layer in hits:
            return
        hits[layer] = {
            "layer": layer,
            "elapsed_ms": elapsed_ms,
            "tile_count": tile_count,
            "decisions": decisions,
        }

    result, stats, _ = run_online_tree_episode(
        learned_args,
        scheme,
        bad_counts,
        bad_clauses,
        args.seed,
        growth_callback=callback,
    )
    last_coloring = stats.get("last_coloring", {})
    if not isinstance(last_coloring, dict):
        last_coloring = {}
    return {
        "name": "online-learned GCTS",
        "kind": "online-gcts",
        "summary": {
            "elapsed_ms": result.elapsed_ms,
            "tile_count": result.tile_count,
            "corona": result.corona,
            "stopped_reason": result.stopped_reason,
            "decisions": result.decisions,
            "forced_moves": result.forced_moves,
            "branch_moves": result.branch_moves,
            "dead_frontier_checks": result.dead_frontier_checks,
            "active_bad_clauses": stats.get("active_bad_clauses", 0),
            "unique_bad_clauses": stats.get("unique_bad_clauses", 0),
            "active_bad_pairs": stats.get("active_bad_pairs", 0),
            "unique_bad_pairs": stats.get("unique_bad_pairs", 0),
            "unique_scoped_bad_clauses": stats.get("unique_scoped_bad_clauses", 0),
            "scoped_bad_clause_observations": stats.get("scoped_bad_clause_observations", 0),
            "marking_rebuilds": stats.get("marking_rebuilds", 0),
            "marking_cache_hits": stats.get("marking_cache_hits", 0),
            "orientation_builds": stats.get("orientation_builds", 0),
            "orientation_cache_hits": stats.get("orientation_cache_hits", 0),
            "marked_state_cache_hits": stats.get("marked_state_cache_hits", 0),
            "marked_state_hint_hits": stats.get("marked_state_hint_hits", 0),
            "frontier_option_cache_hits": stats.get("frontier_option_cache_hits", 0),
            "section_spec_reuses": stats.get("section_spec_reuses", 0),
            "section_spec_reuse_conflicts": stats.get("section_spec_reuse_conflicts", 0),
            "marked_candidate_cache_hits": stats.get("marked_candidate_cache_hits", 0),
            "marked_boundary_cache_hits": stats.get("marked_boundary_cache_hits", 0),
            "geometric_boundary_cache_hits": stats.get("geometric_boundary_cache_hits", 0),
            "branch_union_cache_hits": stats.get("branch_union_cache_hits", 0),
            "assigned_roots": stats.get("assigned_roots", 0),
            "assignment_satisfied": last_coloring.get("assignment_satisfied"),
            "assignment_positive_conflicts": last_coloring.get("assignment_positive_conflicts"),
            "assignment_value_counts": last_coloring.get("assignment_value_counts"),
            "path_replay_conflicts": stats.get("path_replay_conflicts", 0),
            "hard_mark_filtered_candidates": stats.get("hard_mark_filtered_candidates", 0),
            "hard_live_mark_filtered_candidates": stats.get("hard_live_mark_filtered_candidates", 0),
            "marked_boundary_filtered": stats.get("marked_boundary_filtered", 0),
            "trusted_marked_candidates": stats.get("trusted_marked_candidates", 0),
            "child_section_checks": stats.get("child_section_checks", 0),
            "child_section_feasible": stats.get("child_section_feasible", 0),
            "child_section_infeasible": stats.get("child_section_infeasible", 0),
            "child_section_filter_feasible_candidates": stats.get("child_section_filter_feasible_candidates", 0),
            "child_section_filter_infeasible_candidates": stats.get("child_section_filter_infeasible_candidates", 0),
            "child_section_filter_empty": stats.get("child_section_filter_empty", 0),
            "rejected_bad_clauses_unsatisfied": stats.get("rejected_bad_clauses_unsatisfied", 0),
            "rejected_bad_clauses_replay_conflict": stats.get("rejected_bad_clauses_replay_conflict", 0),
        },
        "hits": [hits[layer] for layer in sorted(hits)],
    }


def substitution_series(args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(None)
    started = time.perf_counter()
    raw = substitution_orientation_placements(orientations, args.substitution_tile, args.substitution_levels)
    placements = [place(orientation, translation, f"substitution-{shape_idx}") for shape_idx, _, orientation, translation in raw]
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    corona = max_corona(placements)
    layers = min(args.max_layers, corona)
    return {
        "name": f"{args.substitution_tile} substitution L{args.substitution_levels}",
        "kind": "substitution",
        "summary": {
            "elapsed_ms": elapsed_ms,
            "tile_count": len(placements),
            "corona": corona,
            "stopped_reason": "generated_patch",
            "decisions": 0,
        },
        "hits": [
            {"layer": layer, "elapsed_ms": elapsed_ms, "tile_count": len(placements), "decisions": 0}
            for layer in range(1, layers + 1)
        ],
    }


def load_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def plot_growth(payload: dict[str, object], output: Path, metric: str = "elapsed_ms") -> None:
    series = payload["series"]  # type: ignore[index]
    max_layers = int(payload["config"]["max_layers"])  # type: ignore[index]
    metric_labels = {
        "elapsed_ms": ("wall-clock time", "log milliseconds"),
        "decisions": ("search decisions", "log decisions"),
    }
    metric_name, metric_scale = metric_labels[metric]
    values = []
    for item in series:  # type: ignore[assignment]
        values.extend(max(1, int(hit[metric])) for hit in item["hits"])
    max_value = max(values or [1])
    min_value = 1
    max_log = math.log10(max_value)
    min_log = math.log10(min_value)
    if math.isclose(max_log, min_log):
        max_log += 1

    width, height = 1160, 720
    margin_left, margin_right = 100, 260
    margin_top, margin_bottom = 86, 90
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    image = Image.new("RGB", (width, height), "#fbfaf7")
    draw = ImageDraw.Draw(image)
    title_font = load_font(24)
    label_font = load_font(14)
    small_font = load_font(12)
    colors = ["#0072b2", "#d55e00", "#009e73", "#cc79a7", "#332288"]

    def x_for(layer: int) -> float:
        if max_layers <= 1:
            return margin_left
        return margin_left + (layer - 1) * plot_w / (max_layers - 1)

    def y_for(raw_value: int) -> float:
        value = math.log10(max(1, raw_value))
        ratio = (value - min_log) / (max_log - min_log)
        return margin_top + plot_h * (1 - ratio)

    draw.text((margin_left, 28), "Hat GCTS Growth Curve", fill="#1f2933", font=title_font)
    draw.text((margin_left, 58), f"First {metric_name} to reach each corona layer; y-axis is {metric_scale}.", fill="#52606d", font=small_font)

    # Grid and axes.
    draw.line((margin_left, margin_top, margin_left, margin_top + plot_h), fill="#52606d", width=2)
    draw.line((margin_left, margin_top + plot_h, margin_left + plot_w, margin_top + plot_h), fill="#52606d", width=2)
    for layer in range(1, max_layers + 1):
        x = x_for(layer)
        draw.line((x, margin_top, x, margin_top + plot_h), fill="#e4e7eb")
        draw.text((x - 5, margin_top + plot_h + 14), str(layer), fill="#1f2933", font=small_font)
    tick = 1
    ticks = []
    while tick <= max_value * 1.1:
        ticks.append(tick)
        tick *= 10
    for tick in ticks:
        if tick > max_value * 1.1:
            continue
        y = y_for(tick)
        draw.line((margin_left, y, margin_left + plot_w, y), fill="#e4e7eb")
        if metric == "elapsed_ms":
            label = f"{tick} ms" if tick < 1000 else f"{tick / 1000:g} s"
        else:
            label = str(tick)
        draw.text((18, y - 7), label, fill="#52606d", font=small_font)
    draw.text((margin_left + plot_w / 2 - 36, height - 38), "corona layer", fill="#1f2933", font=label_font)

    for index, item in enumerate(series):  # type: ignore[assignment]
        color = colors[index % len(colors)]
        points = [(x_for(int(hit["layer"])), y_for(int(hit[metric]))) for hit in item["hits"]]
        if len(points) > 1:
            draw.line(points, fill=color, width=3)
        for x, y in points:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color, outline="#1f2933")
        legend_x = margin_left + plot_w + 34
        legend_y = margin_top + index * 72
        draw.line((legend_x, legend_y + 8, legend_x + 30, legend_y + 8), fill=color, width=4)
        draw.text((legend_x + 42, legend_y), item["name"], fill="#1f2933", font=label_font)
        summary = item["summary"]
        detail = f"corona {summary['corona']}, {summary['tile_count']} tiles, {summary['elapsed_ms']} ms"
        draw.text((legend_x + 42, legend_y + 22), detail, fill="#52606d", font=small_font)
        draw.text((legend_x + 42, legend_y + 40), str(summary["stopped_reason"]), fill="#52606d", font=small_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-layers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--target-tiles", type=int, default=400)
    parser.add_argument("--max-steps", type=int, default=450)
    parser.add_argument("--node-limit", type=int, default=24000)
    parser.add_argument("--wall-time-ms", type=int, default=60000)
    parser.add_argument("--frontier-limit", type=int, default=10)
    parser.add_argument("--candidate-limit", type=int, default=10)
    parser.add_argument("--policy", choices=["heuristic", "random"], default="heuristic")
    parser.add_argument("--no-boundary-alive", action="store_true")
    parser.add_argument("--lattice-marking", default="runs/hat-sampled-lattice-zero-smoke.json")
    parser.add_argument("--probe-mode", choices=["lattice", "a2", "midpoint"], default="lattice")
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
    parser.add_argument("--online-min-good", type=int, default=1)
    parser.add_argument("--online-min-bad", type=int, default=1)
    parser.add_argument("--max-good-for-bad", type=int, default=0)
    parser.add_argument("--online-contact-scope", choices=["neighbors", "all"], default="neighbors")
    parser.add_argument("--online-max-bad-pairs-per-tile", type=int, default=0)
    parser.add_argument("--online-learn-boundary-failures", action="store_true")
    parser.add_argument("--online-hard-mark-filter", action="store_true")
    parser.add_argument("--online-hard-live-mark-filter", action="store_true")
    parser.add_argument("--online-child-section-filter", action="store_true")
    parser.add_argument("--online-scope-bad-clauses", action="store_true")
    parser.add_argument("--online-marked-boundary-alive", action="store_true")
    parser.add_argument("--online-trust-marked-candidates", action="store_true")
    parser.add_argument("--no-online-validate-updates", action="store_true")
    parser.add_argument("--include-static-marking", action="store_true")
    parser.add_argument("--include-static-filter-marking", action="store_true")
    parser.add_argument("--static-filter-boundary", choices=["off", "geometric", "marked", "both"], default="geometric")
    parser.add_argument("--static-filter-frontier", action="store_true")
    parser.add_argument("--include-pair-oracle-filter", action="store_true")
    parser.add_argument("--include-residual-pair-filter", action="store_true")
    parser.add_argument("--include-edge-marked", action="store_true")
    parser.add_argument("--include-substitution", action="store_true")
    parser.add_argument("--substitution-tile", choices=["H7", "H8"], default="H8")
    parser.add_argument("--substitution-levels", type=int, default=4)
    parser.add_argument("--output", default="runs/hat-growth-curve.json")
    parser.add_argument("--plot", default="runs/hat-growth-curve.png")
    parser.add_argument("--plot-metric", choices=["elapsed_ms", "decisions"], default="elapsed_ms")
    return parser.parse_args()


def main() -> None:
    args = read_args()
    series = [
        run_growth_series("unmarked GCTS", None, args),
        run_online_growth_series(args),
    ]
    if args.include_static_marking:
        series.append(run_growth_series("learned lattice marking", load_probe_or_site_spec(Path(args.lattice_marking)), args))
    if args.include_static_filter_marking:
        series.append(
            run_mark_filter_growth_series(
                "pair-corona marking filter",
                load_probe_or_site_spec(Path(args.lattice_marking)),
                args,
            )
        )
    if args.include_pair_oracle_filter:
        series.append(run_pair_oracle_growth_series("pair-corona oracle filter", args))
    if args.include_residual_pair_filter:
        series.append(
            run_residual_pair_growth_series(
                "rank-3 marking + residual pair filter",
                load_probe_or_site_spec(Path(args.lattice_marking)),
                args,
            )
        )
    if args.include_edge_marked:
        series.append(run_growth_series("H7/H8 edge-marked GCTS", mined_edge_marking_specs("H8", 4)[0], args))
    if args.include_substitution:
        series.append(substitution_series(args))
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": vars(args),
        "series": series,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    plot_growth(payload, Path(args.plot), args.plot_metric)
    print(json.dumps({"series": series}, indent=2))
    print(f"wrote {output}")
    print(f"wrote {args.plot}")


if __name__ == "__main__":
    main()
