#!/usr/bin/env python3
"""Train Hat lattice/probe markings from unguided GCTS samples.

This intentionally does not use the H7/H8 substitution patch. It samples local
candidate moves from unmarked Hat growth, treats one-step boundary-viability
failures as negative evidence, and solves a small equality/inequality coloring
problem over lattice-site variables. The default mode is a direct A2-lattice
support whose channels transform with the lattice symmetry group.
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
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

from hat_marking_search import (
    HAT_VERTS,
    MarkingSpec,
    build_hat_orientations,
    doubled_midpoint,
    edge_component,
    segment_payload,
    summarize,
)
from turtle_gcts_rl import (
    Candidate,
    EpisodeResult,
    FrontierPoint,
    Placement,
    Point,
    TurtleState,
    add,
    candidate_keeps_boundary_alive,
    candidate_moves_for_frontier,
    choose_frontier_option,
    frontier,
    interiors,
    key,
    mark_compatible_candidate,
    map_component,
    max_corona,
    norm,
    order_candidates,
    place,
    project_raw,
    reward_for,
    run_mark_filter_tree_search,
    run_tree_search,
    scale,
    sub,
    transform_linear,
    valid_candidate,
)


@dataclass(frozen=True)
class LocalMark:
    name: str
    point: Point
    component: int
    edge: int | None = None
    offset: Point | None = None


ProbeVar = tuple[str, str]
BaseProbeVar = str
ProbePair = tuple[ProbeVar, ProbeVar]
ProbeClause = tuple[ProbePair, ...]
BranchContext = frozenset[ProbePair]
ProbeOffsets = list[dict[str, list[Point]]]
MarkScheme = tuple[LocalMark, ...]
PathItem = tuple[int, Point, str]
AssignmentValue = Optional[int]


UNIT_OFFSETS: tuple[Point, ...] = (
    (1, -1, 0),
    (1, 0, -1),
    (0, 1, -1),
    (-1, 1, 0),
    (-1, 0, 1),
    (0, -1, 1),
)


def dot2(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def outward_directions() -> tuple[Point, ...]:
    doubled_vertices = [scale(point, 2) for point in HAT_VERTS]
    projected = [project_raw(point) for point in doubled_vertices]
    centroid = (
        sum(point[0] for point in projected) / len(projected),
        sum(point[1] for point in projected) / len(projected),
    )
    offsets: list[Point] = []
    for edge_index in range(len(HAT_VERTS)):
        midpoint = project_raw(doubled_midpoint(edge_index))
        outward = (midpoint[0] - centroid[0], midpoint[1] - centroid[1])
        offsets.append(max(UNIT_OFFSETS, key=lambda offset: dot2(project_raw(offset), outward)))
    return tuple(offsets)


def probe_offsets(mode: str) -> ProbeOffsets:
    outward = outward_directions()
    probes: ProbeOffsets = []
    for edge_index, direction in enumerate(outward):
        if mode == "midpoint":
            doubled = scale(direction, 2)
            probes.append({"out": [doubled], "in": [neg(doubled)]})
            continue
        if mode != "a2":
            raise ValueError(f"unknown probe mode: {mode}")
        source = HAT_VERTS[edge_index]
        target = HAT_VERTS[(edge_index + 1) % len(HAT_VERTS)]
        midpoint = doubled_midpoint(edge_index)
        out_points = [scale(add(source, direction), 2), scale(add(target, direction), 2)]
        in_points = [scale(sub(source, direction), 2), scale(sub(target, direction), 2)]
        probes.append(
            {
                "out": [sub(point, midpoint) for point in out_points],
                "in": [sub(point, midpoint) for point in in_points],
            }
        )
    return probes


def tile_support_points() -> set[Point]:
    return set(HAT_VERTS).union(interiors(HAT_VERTS))


def boundary_support_points() -> set[Point]:
    return set(HAT_VERTS)


def lattice_site_points(reach: int, base: str = "tile") -> tuple[Point, ...]:
    if base == "tile":
        points = tile_support_points()
    elif base == "boundary":
        points = boundary_support_points()
    else:
        raise ValueError(f"unknown lattice base: {base}")
    frontier_points = set(points)
    for _ in range(reach):
        next_frontier = set()
        for point in frontier_points:
            for offset in UNIT_OFFSETS:
                neighbor = add(point, offset)
                if neighbor not in points:
                    next_frontier.add(neighbor)
        points.update(next_frontier)
        frontier_points = next_frontier
    return tuple(sorted((scale(point, 2) for point in points), key=key))


def mark_scheme(mode: str, lattice_reach: int, channels: int, lattice_base: str = "tile") -> MarkScheme:
    if mode == "lattice":
        return tuple(
            LocalMark(f"{key(point)}:c{component}", point, component)
            for point in lattice_site_points(lattice_reach, lattice_base)
            for component in range(channels)
        )

    offsets = probe_offsets(mode)
    marks: list[LocalMark] = []
    for edge, edge_offsets in enumerate(offsets):
        for sign, sign_offsets in edge_offsets.items():
            for offset in sign_offsets:
                marks.append(
                    LocalMark(
                        f"e{edge}:{sign}",
                        add(doubled_midpoint(edge), offset),
                        edge_component(edge),
                        edge,
                        offset,
                    )
                )
    return tuple(marks)


def neg(point: Point) -> Point:
    return (-point[0], -point[1], -point[2])


@lru_cache(maxsize=None)
def base_var_names(scheme: MarkScheme) -> tuple[BaseProbeVar, ...]:
    return tuple(sorted({mark.name for mark in scheme}))


@lru_cache(maxsize=None)
def all_probe_vars(scheme: MarkScheme) -> tuple[ProbeVar, ...]:
    return tuple((side, name) for side in ("fore", "rear") for name in base_var_names(scheme))


@lru_cache(maxsize=None)
def all_base_probe_vars(scheme: MarkScheme) -> tuple[BaseProbeVar, ...]:
    return base_var_names(scheme)


def side_factor(side: str, side_action: str = "opposite") -> int:
    if side_action == "opposite":
        return -1 if side == "rear" else 1
    if side_action == "constant":
        return 1
    raise ValueError(f"unknown side action: {side_action}")


def base_probe_var(variable: ProbeVar) -> BaseProbeVar:
    return variable[1]


@lru_cache(maxsize=None)
def intratile_probe_groups(scheme: MarkScheme) -> tuple[tuple[ProbeVar, ...], ...]:
    groups: dict[tuple[str, str, int], set[ProbeVar]] = defaultdict(set)
    for side in ("fore", "rear"):
        for mark in scheme:
            groups[(side, key(mark.point), mark.component)].add((side, mark.name))
    return tuple(tuple(sorted(group)) for group in groups.values() if len(group) > 1)


@lru_cache(maxsize=None)
def probe_entry_template(
    scheme: MarkScheme,
    orientation_sym,
    is_reflected: bool,
) -> tuple[tuple[Point, int, ProbeVar], ...]:
    side = "rear" if is_reflected else "fore"
    entries: list[tuple[Point, int, ProbeVar]] = []
    for mark in scheme:
        point = transform_linear(mark.point, orientation_sym)
        component = map_component(mark.component, orientation_sym)
        entries.append((point, component, (side, mark.name)))
    return tuple(entries)


def probe_entries_for(placement: Placement, scheme: MarkScheme) -> list[tuple[tuple[str, int], ProbeVar]]:
    mark_translation = scale(placement.translation, placement.orientation.mark_scale)
    return [
        ((key(add(point, mark_translation)), component), variable)
        for point, component, variable in probe_entry_template(
            scheme,
            placement.orientation.sym,
            placement.orientation.is_reflected,
        )
    ]
    return entries


def probe_map(placements: list[Placement], scheme: MarkScheme) -> dict[tuple[str, int], set[ProbeVar]]:
    out: dict[tuple[str, int], set[ProbeVar]] = defaultdict(set)
    for placement in placements:
        for mark_key, variable in probe_entries_for(placement, scheme):
            out[mark_key].add(variable)
    return out


def placement_occupancy_keys(placement: Placement) -> set[str]:
    return {key(entry.point) for entry in placement.occupancy}


def neighboring_placements(placement: Placement, placements: list[Placement]) -> list[Placement]:
    occupied = placement_occupancy_keys(placement)
    return [other for other in placements if occupied.intersection(placement_occupancy_keys(other))]


def contact_pairs_for_placement_against(
    placement: Placement,
    placements: list[Placement],
    scheme: MarkScheme,
    neighbors_only: bool = True,
) -> set[ProbePair]:
    contacts = neighboring_placements(placement, placements) if neighbors_only else placements
    return contact_pairs_for_placement(placement, probe_map(contacts, scheme), scheme)


def contact_pairs_for_candidate(candidate: Candidate, state: TurtleState, scheme: MarkScheme) -> set[ProbePair]:
    candidate_placement = place(candidate.orientation, candidate.translation, candidate.pk)
    return contact_pairs_for_placement_against(candidate_placement, state.placements, scheme, neighbors_only=False)


def neighbor_contact_pairs_for_candidate(candidate: Candidate, state: TurtleState, scheme: MarkScheme) -> set[ProbePair]:
    candidate_placement = place(candidate.orientation, candidate.translation, candidate.pk)
    return contact_pairs_for_placement_against(candidate_placement, state.placements, scheme, neighbors_only=True)


def contact_pairs_for_placement(
    placement: Placement,
    existing: dict[tuple[str, int], set[ProbeVar]],
    scheme: MarkScheme,
) -> set[ProbePair]:
    return contact_pairs_for_entries(probe_entries_for(placement, scheme), existing)


def contact_pairs_for_entries(
    entries: list[tuple[tuple[str, int], ProbeVar]],
    existing: dict[tuple[str, int], set[ProbeVar]],
) -> set[ProbePair]:
    pairs: set[ProbePair] = set()
    for mark_key, variable in entries:
        for previous in existing.get(mark_key, ()):
            left, right = sorted((variable, previous))
            pairs.add((left, right))
    return pairs


def extend_probe_map(
    existing: dict[tuple[str, int], set[ProbeVar]],
    placement: Placement,
    scheme: MarkScheme,
) -> dict[tuple[str, int], set[ProbeVar]]:
    out = {mark_key: set(variables) for mark_key, variables in existing.items()}
    for mark_key, variable in probe_entries_for(placement, scheme):
        out.setdefault(mark_key, set()).add(variable)
    return out


def push_probe_map(
    existing: dict[tuple[str, int], set[ProbeVar]],
    placement: Placement,
    scheme: MarkScheme,
) -> list[tuple[tuple[str, int], ProbeVar]]:
    return push_probe_entries(existing, probe_entries_for(placement, scheme))


def push_probe_entries(
    existing: dict[tuple[str, int], set[ProbeVar]],
    entries: list[tuple[tuple[str, int], ProbeVar]],
) -> list[tuple[tuple[str, int], ProbeVar]]:
    added: list[tuple[tuple[str, int], ProbeVar]] = []
    for mark_key, variable in entries:
        variables = existing.setdefault(mark_key, set())
        if variable not in variables:
            variables.add(variable)
            added.append((mark_key, variable))
    return added


def pop_probe_map(
    existing: dict[tuple[str, int], set[ProbeVar]],
    added: list[tuple[tuple[str, int], ProbeVar]],
) -> None:
    for mark_key, variable in reversed(added):
        variables = existing.get(mark_key)
        if variables is None:
            continue
        variables.discard(variable)
        if not variables:
            del existing[mark_key]


def choose_candidate(candidates: list[Candidate], rng: random.Random, policy: str) -> Candidate:
    if policy == "random":
        return rng.choice(candidates)
    return min(candidates, key=lambda item: (-item.line_matches, item.new_points, -item.overlap_points, norm(item.translation), item.orientation.idx))


def sample_contacts(args: argparse.Namespace, scheme: MarkScheme) -> dict[str, object]:
    if args.sample_source == "online-tree":
        return sample_online_tree_contacts(args, scheme)
    if args.sample_source == "tree-path":
        return sample_tree_path_contacts(args, scheme)

    orientations = build_hat_orientations(None)
    good_counts: Counter[ProbePair] = Counter()
    bad_counts: Counter[ProbePair] = Counter()
    episode_summaries = []
    positive_paths = []
    rng = random.Random(args.seed)

    for episode in range(args.episodes):
        state = TurtleState(orientations)
        state.add_placement(place(orientations[0], (0, 0, 0), "seed"), depth=0)
        sampled_good = sampled_bad = 0
        stop = "max_steps"
        for _ in range(args.max_steps):
            options = []
            for point in frontier(state)[: args.frontier_limit]:
                candidates = candidate_moves_for_frontier(point, state)
                if not candidates:
                    stop = f"dead_frontier:{key(point.point)}"
                    options = []
                    break
                options.extend(candidates[: args.candidate_limit])
            if not options:
                break

            seen = {}
            for candidate in options:
                seen.setdefault(candidate.pk, candidate)
            options = list(seen.values())
            alive_candidates = []
            for candidate in options:
                pairs = contact_pairs_for_candidate(candidate, state, scheme)
                if not pairs:
                    continue
                alive = candidate_keeps_boundary_alive(candidate, state)
                if alive:
                    alive_candidates.append(candidate)
                    good_counts.update(pairs)
                    sampled_good += len(pairs)
                else:
                    bad_counts.update(pairs)
                    sampled_bad += len(pairs)

            if not alive_candidates:
                stop = "no_boundary_alive_candidate"
                break
            chosen = choose_candidate(alive_candidates, rng, args.rollout_policy)
            state.add_placement(place(chosen.orientation, chosen.translation, chosen.pk), depth=len(state.placements))
            if len(state.placements) >= args.sample_target_tiles:
                stop = "sample_target_tiles"
                break
        episode_summaries.append(
            {
                "episode": episode,
                "tiles": len(state.placements),
                "stop": stop,
                "sampled_good_contacts": sampled_good,
                "sampled_bad_contacts": sampled_bad,
            }
        )
        positive_paths.append(state.placements[:])

    return {
        "good_counts": good_counts,
        "bad_counts": bad_counts,
        "episodes": episode_summaries,
        "positive_paths": positive_paths,
    }


def sample_tree_path_contacts(args: argparse.Namespace, scheme: MarkScheme) -> dict[str, object]:
    orientations = build_hat_orientations(None)
    good_counts: Counter[ProbePair] = Counter()
    bad_counts: Counter[ProbePair] = Counter()
    episode_summaries = []
    positive_paths = []

    for episode in range(args.episodes):
        seed = args.seed + episode * 101
        result = run_tree_search(
            orientations=orientations,
            weights={},
            seed=seed,
            policy=args.tree_policy,
            target_tiles=args.sample_target_tiles,
            target_corona=args.benchmark_target_corona,
            max_steps=args.max_steps,
            node_limit=args.node_limit,
            wall_time_ms=args.sample_wall_time_ms,
            frontier_limit=args.frontier_limit,
            candidate_limit=args.candidate_limit,
            boundary_alive=not args.no_boundary_alive,
        )
        placements = result.placements
        state = TurtleState(orientations)
        if not placements:
            episode_summaries.append({"episode": episode, "tiles": 0, "stop": result.stopped_reason})
            continue
        state.add_placement(placements[0], depth=0)
        sampled_good = sampled_bad = 0
        for next_placement in placements[1:]:
            existing = probe_map(state.placements, scheme)
            path_pairs = contact_pairs_for_placement(next_placement, existing, scheme)
            good_counts.update(path_pairs)
            sampled_good += len(path_pairs)

            options = []
            for point in frontier(state)[: args.frontier_limit]:
                candidates = candidate_moves_for_frontier(point, state)
                if not candidates:
                    continue
                options.extend(candidates[: args.candidate_limit])
            seen = {}
            for candidate in options:
                seen.setdefault(candidate.pk, candidate)
            for candidate in seen.values():
                pairs = contact_pairs_for_candidate(candidate, state, scheme)
                if not pairs:
                    continue
                if candidate_keeps_boundary_alive(candidate, state):
                    if args.include_alive_alternatives:
                        good_counts.update(pairs)
                        sampled_good += len(pairs)
                else:
                    bad_counts.update(pairs)
                    sampled_bad += len(pairs)
            state.add_placement(next_placement, depth=len(state.placements))

        episode_summaries.append(
            {
                "episode": episode,
                "tiles": len(placements),
                "stop": result.stopped_reason,
                "decisions": result.decisions,
                "sampled_good_contacts": sampled_good,
                "sampled_bad_contacts": sampled_bad,
            }
        )
        positive_paths.append(placements[:])

    return {
        "good_counts": good_counts,
        "bad_counts": bad_counts,
        "episodes": episode_summaries,
        "positive_paths": positive_paths,
    }


def online_training_args(args: argparse.Namespace) -> argparse.Namespace:
    if getattr(args, "sample_source", None) != "online-tree":
        return args
    values = vars(args).copy()
    values["min_good"] = args.online_min_good
    values["min_bad"] = args.online_min_bad
    return argparse.Namespace(**values)


def path_to_placements(path: list[PathItem], orientations: list) -> list[Placement]:
    return [
        place(orientations[orientation_idx], translation, placement_key, depth=depth)
        for depth, (orientation_idx, translation, placement_key) in enumerate(path)
    ]


def state_from_path(path: list[PathItem], orientations: list) -> TurtleState:
    state = TurtleState(orientations)
    for depth, (orientation_idx, translation, placement_key) in enumerate(path):
        state.add_placement(place(orientations[orientation_idx], translation, placement_key), depth=depth)
    return state


def path_contact_pair_counts(
    path: list[PathItem],
    orientations: list,
    scheme: MarkScheme,
    neighbors_only: bool,
) -> Counter[ProbePair]:
    counts: Counter[ProbePair] = Counter()
    placements: list[Placement] = []
    for depth, (orientation_idx, translation, placement_key) in enumerate(path):
        placement = place(orientations[orientation_idx], translation, placement_key, depth=depth)
        if placements:
            counts.update(contact_pairs_for_placement_against(placement, placements, scheme, neighbors_only))
        placements.append(placement)
    return counts


def placement_contact_pair_counts(
    placements: list[Placement],
    scheme: MarkScheme,
    neighbors_only: bool,
) -> Counter[ProbePair]:
    counts: Counter[ProbePair] = Counter()
    previous: list[Placement] = []
    for placement in placements:
        if previous:
            counts.update(contact_pairs_for_placement_against(placement, previous, scheme, neighbors_only))
        previous.append(placement)
    return counts


def bad_pairs_for_candidate(
    candidate: Candidate,
    state: TurtleState,
    scheme: MarkScheme,
    neighbors_only: bool,
    limit: int,
    rng: random.Random | None = None,
) -> list[ProbePair]:
    pairs = (
        neighbor_contact_pairs_for_candidate(candidate, state, scheme)
        if neighbors_only
        else contact_pairs_for_candidate(candidate, state, scheme)
    )
    ordered = sorted(pairs)
    if limit > 0 and len(ordered) > limit:
        if rng is not None:
            rng.shuffle(ordered)
        ordered = sorted(ordered[:limit])
    return ordered


def active_bad_constraints(counts: Counter, min_bad: int) -> int:
    return sum(1 for count in counts.values() if count >= min_bad)


def branch_union_find(
    scheme: MarkScheme,
    branch_equalities: Counter[ProbePair],
    side_action: str,
    min_good: int,
) -> SignedUnionFind:
    union_find, _, _ = fresh_intratile_union_find(scheme, side_action)
    for (left, right), count in branch_equalities.items():
        if count >= min_good:
            union_find.union(
                base_probe_var(left),
                base_probe_var(right),
                signed_probe_relation(left, right, side_action),
            )
    return union_find


def pair_can_witness_disequality(pair: ProbePair, union_find: SignedUnionFind, side_action: str) -> bool:
    left, right = pair
    left_root, left_sign = union_find.find(base_probe_var(left))
    right_root, right_sign = union_find.find(base_probe_var(right))
    if union_find.zero[left_root] or union_find.zero[right_root]:
        return False
    left_coeff = side_factor(left[0], side_action) * left_sign
    right_coeff = side_factor(right[0], side_action) * right_sign
    return left_root != right_root or left_coeff != right_coeff


def online_spec_for_path(
    path: list[PathItem],
    bad_counts: Counter[ProbePair],
    bad_clauses: Counter[ProbeClause],
    base_orientations: list,
    scheme: MarkScheme,
    args: argparse.Namespace,
    neighbors_only: bool,
    branch_equalities: Counter[ProbePair] | None = None,
) -> tuple[MarkingSpec | None, dict[str, object], Counter[ProbePair]]:
    good_counts = (
        branch_equalities
        if branch_equalities is not None
        else path_contact_pair_counts(path, base_orientations, scheme, neighbors_only)
    )
    active_bad = active_bad_constraints(bad_clauses, args.online_min_bad)
    if active_bad == 0:
        return None, {"active_bad_clauses": 0, "active_bad_pairs": 0, "path_good_pairs": len(good_counts)}, good_counts
    spec, diagnostics = train_coloring(
        {
            "good_counts": good_counts,
            "branch_equalities": good_counts,
            "bad_counts": bad_counts,
            "bad_clauses": bad_clauses,
        },
        online_training_args(args),
        scheme,
    )
    diagnostics["active_bad_clauses"] = active_bad
    diagnostics["active_bad_pairs"] = active_bad_constraints(bad_counts, args.online_min_bad)
    diagnostics["path_good_pairs"] = len(good_counts)
    return spec, diagnostics, good_counts


def first_mark_replay_conflict(path: list[PathItem], orientations: list) -> dict[str, object] | None:
    seen: dict[tuple[str, int], tuple[int, int]] = {}
    for depth, (orientation_idx, translation, placement_key) in enumerate(path):
        placement = place(orientations[orientation_idx], translation, placement_key)
        for mark in placement.marks:
            mark_key = (key(mark.point), mark.component)
            previous = seen.get(mark_key)
            if previous is not None and previous[0] != mark.value:
                return {
                    "depth": depth,
                    "point": mark_key[0],
                    "component": mark_key[1],
                    "previous_value": previous[0],
                    "previous_depth": previous[1],
                    "value": mark.value,
                    "orientation": orientation_idx,
                    "translation": list(translation),
                }
            seen.setdefault(mark_key, (mark.value, depth))
    return None


class CoronaTracker:
    def __init__(self) -> None:
        self.by_point: dict[str, list[int]] = defaultdict(list)
        self.adjacency: list[set[int]] = []
        self.distances: list[int] = []
        self.max_distance = 0

    def clone(self) -> "CoronaTracker":
        other = CoronaTracker()
        other.by_point = defaultdict(list, {point: indices[:] for point, indices in self.by_point.items()})
        other.adjacency = [set(neighbors) for neighbors in self.adjacency]
        other.distances = self.distances[:]
        other.max_distance = self.max_distance
        return other

    def add_placement(self, placement: Placement) -> None:
        idx = len(self.distances)
        point_keys = {key(entry.point) for entry in placement.occupancy}
        neighbors: set[int] = set()
        for point_key in point_keys:
            neighbors.update(self.by_point.get(point_key, ()))

        if not self.distances:
            distance = 0
        elif neighbors:
            distance = min(self.distances[neighbor] + 1 for neighbor in neighbors)
        else:
            distance = self.max_distance + 1

        self.distances.append(distance)
        self.adjacency.append(set(neighbors))
        for neighbor in neighbors:
            self.adjacency[neighbor].add(idx)
        for point_key in point_keys:
            self.by_point[point_key].append(idx)

        queue = [idx]
        cursor = 0
        while cursor < len(queue):
            current = queue[cursor]
            cursor += 1
            next_distance = self.distances[current] + 1
            for neighbor in self.adjacency[current]:
                if self.distances[neighbor] > next_distance:
                    self.distances[neighbor] = next_distance
                    queue.append(neighbor)
        self.max_distance = max(self.distances, default=0)


def run_online_tree_episode(
    args: argparse.Namespace,
    scheme: MarkScheme,
    bad_counts: Counter[ProbePair],
    bad_clauses: Counter[ProbeClause],
    seed: int,
    growth_callback: Callable[[int, int, int, int], None] | None = None,
) -> tuple[EpisodeResult, dict[str, object], list[PathItem]]:
    started = time.perf_counter()
    deadline = started + args.sample_wall_time_ms / 1000.0 if args.sample_wall_time_ms > 0 else None
    rng = random.Random(seed)
    weights: dict[str, float] = {}
    boundary_alive = not args.no_boundary_alive
    neighbors_only = args.online_contact_scope == "neighbors"
    bad_pair_limit = args.online_max_bad_pairs_per_tile
    target_corona = args.benchmark_target_corona
    effective_node_limit = args.node_limit if args.node_limit > 0 else max(800, target_corona * target_corona * 64)
    base_orientations = build_hat_orientations(None)
    seed_path: list[PathItem] = [(0, (0, 0, 0), "seed")]

    nodes = 0
    forced_moves = 0
    branch_moves = 0
    dead_frontier_checks = 0
    stopped_reason = "searching"
    best_path = seed_path[:]
    best_reward = reward_for(1, 0, "seed", args.sample_target_tiles, target_corona)
    best_corona = 0
    stats: Counter[str] = Counter()
    last_diagnostics: dict[str, object] = {}
    max_reported_corona = -1
    section_assignments: dict[BaseProbeVar, AssignmentValue] = {}
    bad_revision = 0
    prepare_cache: dict[
        tuple[tuple[PathItem, ...], int],
        tuple[list, TurtleState, TurtleState, MarkingSpec | None, dict[str, object]],
    ] = {}
    path_good_cache: dict[tuple[PathItem, ...], Counter[ProbePair]] = {}
    geometric_state_cache: dict[tuple[PathItem, ...], TurtleState] = {}
    orientation_cache: dict[MarkingSpec | None, list] = {None: base_orientations}
    marked_state_cache: dict[tuple[tuple[PathItem, ...], MarkingSpec], TurtleState] = {}
    corona_cache: dict[tuple[PathItem, ...], int] = {}
    frontier_option_cache: dict[tuple[PathItem, ...], tuple[str, tuple[FrontierPoint, list[Candidate]] | None]] = {}
    child_feasibility_cache: dict[tuple[tuple[PathItem, ...], int], bool] = {}
    scoped_bad_clauses: Counter[tuple[BranchContext, ProbeClause]] = Counter()
    current_spec: MarkingSpec | None = None
    current_spec_key: tuple[tuple[ProbeClause, int], ...] | None = None
    side_action = getattr(args, "side_action", "opposite")

    def active_clause_key(counts: Counter[ProbeClause]) -> tuple[tuple[ProbeClause, int], ...]:
        return tuple(sorted((clause, count) for clause, count in counts.items() if count >= args.online_min_bad))

    def orientations_for(spec: MarkingSpec | None) -> list:
        if spec in orientation_cache:
            stats["orientation_cache_hits"] += 1
            return orientation_cache[spec]
        orientations = build_hat_orientations(spec)
        orientation_cache[spec] = orientations
        stats["orientation_builds"] += 1
        return orientations

    def marked_state_for(
        path: list[PathItem],
        path_key: tuple[PathItem, ...],
        spec: MarkingSpec | None,
        orientations: list,
        geometric_state: TurtleState,
        marked_state_hint: TurtleState | None = None,
        marked_spec_hint: MarkingSpec | None = None,
    ) -> TurtleState:
        if spec is None:
            return geometric_state
        marked_key = (path_key, spec)
        marked_state = marked_state_cache.get(marked_key)
        if marked_state is not None:
            stats["marked_state_cache_hits"] += 1
            return marked_state
        if marked_state_hint is not None and marked_spec_hint == spec:
            stats["marked_state_hint_hits"] += 1
            marked_state_cache[marked_key] = marked_state_hint
            return marked_state_hint
        marked_state = state_from_path(path, orientations)
        marked_state_cache[marked_key] = marked_state
        return marked_state

    def out_of_time() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def args_with_section() -> argparse.Namespace:
        values = vars(args).copy()
        values["initial_assignments"] = section_assignments
        return argparse.Namespace(**values)

    def child_branch_good(
        candidate: Candidate,
        geometric_state: TurtleState,
        branch_good: Counter[ProbePair],
        branch_probe_map: dict[tuple[str, int], set[ProbeVar]],
        branch_context_value: BranchContext,
    ) -> tuple[
        Counter[ProbePair],
        BranchContext,
        set[ProbePair],
        list[ProbePair],
        Placement,
        list[tuple[tuple[str, int], ProbeVar]],
    ]:
        child_good = Counter(branch_good)
        child_placement = place(candidate.orientation, candidate.translation, candidate.pk)
        child_probe_entries = probe_entries_for(child_placement, scheme)
        if neighbors_only:
            contacts = contact_pairs_for_placement_against(child_placement, geometric_state.placements, scheme, True)
        else:
            contacts = contact_pairs_for_entries(child_probe_entries, branch_probe_map)
        child_good.update(contacts)
        new_equalities = sorted(
            pair
            for pair in contacts
            if branch_good.get(pair, 0) < args.online_min_good <= child_good[pair]
        )
        return (
            child_good,
            extend_branch_context(branch_context_value, contacts, child_good),
            contacts,
            new_equalities,
            child_placement,
            child_probe_entries,
        )

    def branch_context(branch_good: Counter[ProbePair]) -> BranchContext:
        return frozenset(pair for pair, count in branch_good.items() if count >= args.online_min_good)

    def extend_branch_context(
        context: BranchContext,
        contacts: set[ProbePair],
        child_good: Counter[ProbePair],
    ) -> BranchContext:
        if args.online_min_good <= 1:
            return context.union(contacts)
        return branch_context(child_good)

    def active_scoped_bad_clauses_for_context(context: BranchContext) -> Counter[ProbeClause]:
        if not getattr(args, "online_scope_bad_clauses", False):
            return Counter(bad_clauses)
        active: Counter[ProbeClause] = Counter()
        for (learned_context, clause), count in scoped_bad_clauses.items():
            if count >= args.online_min_bad and learned_context.issubset(context):
                active[clause] += count
        return active

    def active_scoped_bad_clauses(branch_good: Counter[ProbePair]) -> Counter[ProbeClause]:
        return active_scoped_bad_clauses_for_context(branch_context(branch_good))

    def child_section_feasible(
        path: list[PathItem],
        child_good: Counter[ProbePair],
        child_context: BranchContext,
    ) -> bool:
        active_bad_clauses_for_child = active_scoped_bad_clauses_for_context(child_context)
        if active_bad_constraints(active_bad_clauses_for_child, args.online_min_bad) == 0:
            return True
        cache_key = (tuple(path), bad_revision)
        cached = child_feasibility_cache.get(cache_key)
        if cached is not None:
            stats["child_section_cache_hits"] += 1
            return cached
        _, diagnostics = train_coloring(
            {
                "good_counts": child_good,
                "branch_equalities": child_good,
                "bad_counts": bad_counts,
                "bad_clauses": active_bad_clauses_for_child,
            },
            online_training_args(args_with_section()),
            scheme,
        )
        feasible = bool(diagnostics.get("assignment_satisfied", True))
        child_feasibility_cache[cache_key] = feasible
        stats["child_section_checks"] += 1
        if feasible:
            stats["child_section_feasible"] += 1
        else:
            stats["child_section_infeasible"] += 1
        return feasible

    def report_growth(corona: int, tile_count: int) -> None:
        nonlocal max_reported_corona
        if growth_callback is None or corona <= max_reported_corona:
            return
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        decisions = forced_moves + branch_moves
        for layer in range(max_reported_corona + 1, corona + 1):
            growth_callback(layer, elapsed_ms, tile_count, decisions)
        max_reported_corona = corona

    def remember(path: list[PathItem], reason: str, tile_count: int, corona: int) -> None:
        nonlocal best_path, best_reward, best_corona, stopped_reason
        current_reward = reward_for(tile_count, corona, reason, args.sample_target_tiles, target_corona)
        if current_reward > best_reward or (
            math.isclose(current_reward, best_reward)
            and (tile_count, corona) > (len(best_path), best_corona)
        ):
            best_path = path[:]
            best_reward = current_reward
            best_corona = corona
            stopped_reason = reason

    def cached_corona(path: list[PathItem], geometric_state: TurtleState) -> int:
        path_key = tuple(path)
        cached = corona_cache.get(path_key)
        if cached is None:
            cached = max_corona(geometric_state.placements)
            corona_cache[path_key] = cached
        return cached

    def prepare(
        path: list[PathItem],
        branch_good: Counter[ProbePair],
        branch_context_value: BranchContext,
        geometric_state_hint: TurtleState | None = None,
        marked_state_hint: TurtleState | None = None,
        marked_spec_hint: MarkingSpec | None = None,
    ) -> tuple[list, TurtleState, TurtleState, MarkingSpec | None] | None:
        nonlocal current_spec, current_spec_key, last_diagnostics, section_assignments
        path_key = tuple(path)
        cache_key = (path_key, bad_revision)
        cached = prepare_cache.get(cache_key)
        if cached is not None:
            orientations, marked_state, geometric_state, spec, diagnostics = cached
            last_diagnostics = diagnostics
            if diagnostics.get("assignment_satisfied", True) and "_assignments" in diagnostics:
                section_assignments = dict(diagnostics["_assignments"])  # type: ignore[arg-type]
            stats["marking_cache_hits"] += 1
            return orientations, marked_state, geometric_state, spec
        good_counts = path_good_cache.get(path_key)
        if good_counts is None:
            good_counts = Counter(branch_good)
            path_good_cache[path_key] = good_counts
        geometric_state = geometric_state_cache.get(path_key)
        if geometric_state is None:
            geometric_state = geometric_state_hint if geometric_state_hint is not None else state_from_path(path, base_orientations)
            geometric_state_cache[path_key] = geometric_state
        active_bad_clauses_for_path = active_scoped_bad_clauses_for_context(branch_context_value)
        active_key = active_clause_key(active_bad_clauses_for_path)
        if current_spec is not None and current_spec_key == active_key:
            orientations = orientations_for(current_spec)
            try:
                marked_state = marked_state_for(
                    path,
                    path_key,
                    current_spec,
                    orientations,
                    geometric_state,
                    marked_state_hint,
                    marked_spec_hint,
                )
                diagnostics = dict(last_diagnostics)
                diagnostics["section_reused"] = True
                last_diagnostics = diagnostics
                stats["section_spec_reuses"] += 1
                prepare_cache[cache_key] = (orientations, marked_state, geometric_state, current_spec, dict(diagnostics))
                return orientations, marked_state, geometric_state, current_spec
            except ValueError:
                stats["section_spec_reuse_conflicts"] += 1
        spec, diagnostics, _ = online_spec_for_path(
            path,
            bad_counts,
            active_bad_clauses_for_path,
            base_orientations,
            scheme,
            args_with_section(),
            neighbors_only,
            good_counts,
        )
        last_diagnostics = diagnostics
        if diagnostics.get("assignment_satisfied", True):
            if "_assignments" in diagnostics:
                section_assignments = dict(diagnostics["_assignments"])  # type: ignore[arg-type]
        else:
            spec = None
            stats["unsatisfied_marking_fallbacks"] += 1
        stats["marking_rebuilds"] += 1
        orientations = orientations_for(spec)
        try:
            marked_state = marked_state_for(
                path,
                path_key,
                spec,
                orientations,
                geometric_state,
                marked_state_hint,
                marked_spec_hint,
            )
            if diagnostics.get("assignment_satisfied", True) and spec is not None:
                current_spec = spec
                current_spec_key = active_key
            prepare_cache[cache_key] = (orientations, marked_state, geometric_state, spec, dict(diagnostics))
            return orientations, marked_state, geometric_state, spec
        except ValueError:
            stats["path_replay_conflicts"] += 1
            if "first_path_replay_conflict" not in last_diagnostics:
                conflict = first_mark_replay_conflict(path, orientations)
                if conflict is not None:
                    last_diagnostics["first_path_replay_conflict"] = conflict
            return None

    def learn_bad(
        candidate: Candidate,
        state: TurtleState,
        branch_good: Counter[ProbePair],
        branch_context_value: BranchContext,
        branch_union: SignedUnionFind,
        branch_probe_map: dict[tuple[str, int], set[ProbeVar]],
        reason: str,
        raw_pairs_hint: set[ProbePair] | None = None,
    ) -> int:
        nonlocal current_spec, current_spec_key, section_assignments, bad_revision
        if raw_pairs_hint is not None:
            raw_pairs = sorted(raw_pairs_hint)
        elif neighbors_only:
            raw_pairs = bad_pairs_for_candidate(candidate, state, scheme, True, 0, rng)
        else:
            candidate_placement = place(candidate.orientation, candidate.translation, candidate.pk)
            raw_pairs = sorted(contact_pairs_for_placement(candidate_placement, branch_probe_map, scheme))
        current_good = branch_good
        context = branch_context_value
        possible_pairs = [
            pair
            for pair in raw_pairs
            if current_good.get(pair, 0) <= args.max_good_for_bad
            and pair_can_witness_disequality(pair, branch_union, side_action)
        ]
        if bad_pair_limit > 0 and len(possible_pairs) > bad_pair_limit:
            rng.shuffle(possible_pairs)
            possible_pairs = sorted(possible_pairs[:bad_pair_limit])
        pairs = possible_pairs
        if not pairs:
            stats["failed_tiles_without_contact_pairs"] += 1
            return 0
        clause = tuple(pairs)
        scoped_key = (context, clause)
        before_clause = scoped_bad_clauses[scoped_key] if getattr(args, "online_scope_bad_clauses", False) else bad_clauses[clause]
        clause_will_activate = before_clause < args.online_min_bad <= before_clause + 1
        trial_bad_counts = Counter(bad_counts)
        trial_bad_clauses = active_scoped_bad_clauses_for_context(context)
        trial_bad_clauses[clause] += 1
        for pair in pairs:
            trial_bad_counts[pair] += 1
        if clause_will_activate and getattr(args, "online_validate_updates", True):
            try:
                trial_spec, trial_diagnostics = train_coloring(
                    {
                        "good_counts": current_good,
                        "branch_equalities": current_good,
                        "bad_counts": trial_bad_counts,
                        "bad_clauses": trial_bad_clauses,
                    },
                    online_training_args(args_with_section()),
                    scheme,
                )
                if not trial_diagnostics.get("assignment_satisfied", True):
                    stats["rejected_bad_clauses_unsatisfied"] += 1
                    return 0
                trial_orientations = orientations_for(trial_spec)
                trial_state = TurtleState(trial_orientations)
                for depth, placement in enumerate(state.placements):
                    orientation = trial_orientations[placement.orientation.idx]
                    trial_state.add_placement(place(orientation, placement.translation, placement.placement_key), depth=depth)
                if "_assignments" in trial_diagnostics:
                    section_assignments = dict(trial_diagnostics["_assignments"])  # type: ignore[arg-type]
                current_spec = trial_spec
                current_spec_key = active_clause_key(trial_bad_clauses)
            except ValueError:
                stats["rejected_bad_clauses_replay_conflict"] += 1
                return 0
        bad_clauses[clause] += 1
        scoped_bad_clauses[scoped_key] += 1
        if clause_will_activate:
            bad_revision += 1
        activated = 0
        for pair in pairs:
            before = bad_counts[pair]
            bad_counts[pair] += 1
            if before < args.online_min_bad <= bad_counts[pair]:
                activated += 1
        stats["learned_failed_tiles"] += 1
        stats["learned_pair_observations"] += len(pairs)
        stats["learned_clause_observations"] += 1
        stats[f"learned_tiles:{reason}"] += 1
        stats["activated_bad_pairs"] += activated
        after_clause = scoped_bad_clauses[scoped_key] if getattr(args, "online_scope_bad_clauses", False) else bad_clauses[clause]
        if before_clause < args.online_min_bad <= after_clause:
            stats["activated_bad_clauses"] += 1
        return len(pairs)

    learnable_backtrack_reasons = {"exhausted", "no_frontier", "filtered_dead_frontier"}

    def should_learn_backtrack(reason: str) -> bool:
        return reason in learnable_backtrack_reasons or reason.startswith("dead_frontier:")

    def search(
        path: list[PathItem],
        branch_good: Counter[ProbePair],
        branch_context_value: BranchContext,
        branch_union: SignedUnionFind,
        branch_probe_map: dict[tuple[str, int], set[ProbeVar]],
        geometric_state: TurtleState,
        corona_tracker: CoronaTracker,
        marked_state_hint: TurtleState | None = None,
        marked_spec_hint: MarkingSpec | None = None,
    ) -> tuple[bool, str]:
        nonlocal nodes, forced_moves, branch_moves, dead_frontier_checks, stopped_reason
        if out_of_time():
            stopped_reason = "wall_time_ms"
            prepared = prepare(path, branch_good, branch_context_value, geometric_state, marked_state_hint, marked_spec_hint)
            if prepared:
                remember(path, "wall_time_ms", len(path), corona_tracker.max_distance)
            return False, "wall_time_ms"
        if nodes >= effective_node_limit:
            stopped_reason = "node_limit"
            prepared = prepare(path, branch_good, branch_context_value, geometric_state, marked_state_hint, marked_spec_hint)
            if prepared:
                remember(path, "node_limit", len(path), corona_tracker.max_distance)
            return False, "node_limit"

        failed_here: set[str] = set()
        marked_candidate_cache: dict[tuple[MarkingSpec | None, str], Candidate | None] = {}
        marked_boundary_cache: dict[tuple[MarkingSpec | None, str], bool] = {}
        geometric_boundary_cache: dict[str, bool] = {}
        while True:
            prepared = prepare(path, branch_good, branch_context_value, geometric_state, marked_state_hint, marked_spec_hint)
            if prepared is None:
                stopped_reason = "path_replay_conflict"
                return False, "path_replay_conflict"
            orientations, marked_state, geometric_state, active_spec = prepared
            corona = corona_tracker.max_distance
            report_growth(corona, len(path))
            remember(path, "partial", len(path), corona)
            if len(path) >= args.sample_target_tiles:
                stopped_reason = "sample_target_tiles"
                remember(path, stopped_reason, len(path), corona)
                return True, stopped_reason
            if corona >= target_corona:
                stopped_reason = "target_corona"
                remember(path, stopped_reason, len(path), corona)
                return True, stopped_reason
            if len(path) >= args.max_steps:
                remember(path, "max_steps", len(path), corona)
                return False, "max_steps"
            if out_of_time():
                stopped_reason = "wall_time_ms"
                remember(path, stopped_reason, len(path), corona)
                return False, "wall_time_ms"
            if nodes >= effective_node_limit:
                stopped_reason = "node_limit"
                remember(path, stopped_reason, len(path), corona)
                return False, "node_limit"

            path_key = tuple(path)
            cached_option = frontier_option_cache.get(path_key)
            if cached_option is None:
                cached_option = choose_frontier_option(geometric_state, args.frontier_limit, args.candidate_limit)
                frontier_option_cache[path_key] = cached_option
            else:
                stats["frontier_option_cache_hits"] += 1
            status, option = cached_option
            if status != "ok" or option is None:
                remember(path, status, len(path), corona)
                return False, status

            _, raw_candidates = option
            ordered_unmarked = [
                candidate
                for candidate in order_candidates(raw_candidates, geometric_state, weights, rng, args.tree_policy, args.candidate_limit)
                if candidate.pk not in failed_here
            ]
            marked_candidates = []
            fallback_candidates = []
            marked_candidate_by_pk: dict[str, Candidate] = {}
            for candidate in ordered_unmarked:
                marked_cache_key = (active_spec, candidate.pk)
                if marked_cache_key in marked_candidate_cache:
                    stats["marked_candidate_cache_hits"] += 1
                    marked_candidate = marked_candidate_cache[marked_cache_key]
                else:
                    marked_candidate = mark_compatible_candidate(
                        orientations[candidate.orientation.idx],
                        candidate,
                        marked_state,
                    )
                    marked_candidate_cache[marked_cache_key] = marked_candidate
                if marked_candidate is None:
                    fallback_candidates.append(candidate)
                else:
                    marked_candidates.append((candidate, marked_candidate))
                    marked_candidate_by_pk[candidate.pk] = marked_candidate
            marked_candidates.sort(
                key=lambda item: (
                    -item[1].line_matches,
                    -item[1].overlap_points,
                    item[1].new_points,
                    norm(item[1].translation),
                    item[1].orientation.idx,
                )
            )
            if getattr(args, "online_hard_mark_filter", False) and marked_candidates:
                ordered = [candidate for candidate, _ in marked_candidates]
                stats["hard_mark_filtered_candidates"] += len(fallback_candidates)
            else:
                ordered = [candidate for candidate, _ in marked_candidates] + fallback_candidates
            stats["marking_preferred_candidates"] += len(marked_candidates)
            stats["marking_fallback_candidates"] += len(fallback_candidates)
            if not ordered:
                remember(path, "exhausted", len(path), corona)
                return False, "exhausted"
            child_good_by_pk: dict[
                str,
                tuple[
                    Counter[ProbePair],
                    BranchContext,
                    set[ProbePair],
                    list[ProbePair],
                    Placement,
                    list[tuple[tuple[str, int], ProbeVar]],
                ],
            ] = {}
            if getattr(args, "online_child_section_filter", False):
                feasible_candidates = []
                infeasible_candidates = []
                for candidate in ordered:
                    child_path = path + [(candidate.orientation.idx, candidate.translation, candidate.pk)]
                    child_entry = child_branch_good(
                        candidate,
                        geometric_state,
                        branch_good,
                        branch_probe_map,
                        branch_context_value,
                    )
                    child_good, child_context, _, _, _, _ = child_entry
                    child_good_by_pk[candidate.pk] = child_entry
                    if child_section_feasible(child_path, child_good, child_context):
                        feasible_candidates.append(candidate)
                    else:
                        infeasible_candidates.append(candidate)
                stats["child_section_filter_feasible_candidates"] += len(feasible_candidates)
                stats["child_section_filter_infeasible_candidates"] += len(infeasible_candidates)
                if feasible_candidates:
                    ordered = feasible_candidates
                else:
                    stats["child_section_filter_empty"] += 1

            candidates: list[Candidate] = []
            live_marked_candidates: list[Candidate] = []
            live_fallback_candidates: list[Candidate] = []
            for candidate in ordered:
                if boundary_alive and len(ordered) > 1:
                    marked_candidate = marked_candidate_by_pk.get(candidate.pk)
                    if getattr(args, "online_trust_marked_candidates", False) and marked_candidate is not None:
                        stats["trusted_marked_candidates"] += 1
                        candidates.append(candidate)
                        continue
                    dead_frontier_checks += 1
                    marked_boundary_failed = False
                    if bool(getattr(args, "online_marked_boundary_alive", False)) and marked_candidate is not None:
                        marked_boundary_key = (active_spec, candidate.pk)
                        marked_boundary_alive = marked_boundary_cache.get(marked_boundary_key)
                        if marked_boundary_alive is None:
                            marked_boundary_alive = candidate_keeps_boundary_alive(marked_candidate, marked_state)
                            marked_boundary_cache[marked_boundary_key] = marked_boundary_alive
                        else:
                            stats["marked_boundary_cache_hits"] += 1
                        marked_boundary_failed = not marked_boundary_alive
                    if marked_boundary_failed:
                        stats["marked_boundary_filtered"] += 1
                    geometric_boundary_failed = False
                    if (
                        not marked_boundary_failed
                        and (
                            not getattr(args, "online_marked_boundary_alive", False)
                            or marked_candidate is None
                        )
                    ):
                        geometric_boundary_alive = geometric_boundary_cache.get(candidate.pk)
                        if geometric_boundary_alive is None:
                            geometric_boundary_alive = candidate_keeps_boundary_alive(candidate, geometric_state)
                            geometric_boundary_cache[candidate.pk] = geometric_boundary_alive
                        else:
                            stats["geometric_boundary_cache_hits"] += 1
                        geometric_boundary_failed = not geometric_boundary_alive
                    if (
                        marked_boundary_failed
                        or geometric_boundary_failed
                    ):
                        failed_here.add(candidate.pk)
                        if getattr(args, "online_learn_boundary_failures", False):
                            learn_bad(
                                candidate,
                                geometric_state,
                                branch_good,
                                branch_context_value,
                                branch_union,
                                branch_probe_map,
                                "boundary_alive",
                            )
                        else:
                            stats["skipped_boundary_learning"] += 1
                        continue
                if candidate.pk in marked_candidate_by_pk:
                    live_marked_candidates.append(candidate)
                else:
                    live_fallback_candidates.append(candidate)
                candidates.append(candidate)

            if getattr(args, "online_hard_live_mark_filter", False) and live_marked_candidates:
                stats["hard_live_mark_filtered_candidates"] += len(live_fallback_candidates)
                candidates = live_marked_candidates

            if not candidates:
                continue

            is_forced = len(candidates) == 1
            candidate = candidates[0]
            if out_of_time():
                stopped_reason = "wall_time_ms"
                remember(path, stopped_reason, len(path), corona)
                return False, "wall_time_ms"
            if nodes >= effective_node_limit:
                stopped_reason = "node_limit"
                remember(path, stopped_reason, len(path), corona)
                return False, "node_limit"

            nodes += 1
            if is_forced:
                forced_moves += 1
            else:
                branch_moves += 1

            child_path = path + [(candidate.orientation.idx, candidate.translation, candidate.pk)]
            child_entry = child_good_by_pk.get(candidate.pk)
            if child_entry is None:
                (
                    child_good,
                    child_context,
                    child_contacts,
                    child_new_equalities,
                    child_placement,
                    child_probe_entries,
                ) = child_branch_good(
                    candidate,
                    geometric_state,
                    branch_good,
                    branch_probe_map,
                    branch_context_value,
                )
            else:
                child_good, child_context, child_contacts, child_new_equalities, child_placement, child_probe_entries = child_entry
            probe_map_added = push_probe_entries(branch_probe_map, child_probe_entries)
            child_branch_union = branch_union.clone()
            for left, right in child_new_equalities:
                child_branch_union.union(
                    base_probe_var(left),
                    base_probe_var(right),
                    signed_probe_relation(left, right, side_action),
                )
            child_geometric_state = geometric_state.clone()
            child_geometric_state.add_placement(child_placement, depth=len(path))
            child_corona_tracker = corona_tracker.clone()
            child_corona_tracker.add_placement(child_placement)
            child_marked_state_hint = None
            child_marked_spec_hint = None
            marked_candidate = marked_candidate_by_pk.get(candidate.pk)
            if active_spec is not None and marked_candidate is not None:
                child_marked_state_hint = marked_state.clone()
                child_marked_placement = place(marked_candidate.orientation, marked_candidate.translation, marked_candidate.pk)
                child_marked_state_hint.add_placement(child_marked_placement, depth=len(path))
                child_marked_spec_hint = active_spec
            child_success, child_reason = search(
                child_path,
                child_good,
                child_context,
                child_branch_union,
                branch_probe_map,
                child_geometric_state,
                child_corona_tracker,
                child_marked_state_hint,
                child_marked_spec_hint,
            )
            pop_probe_map(branch_probe_map, probe_map_added)
            if child_success:
                return True, child_reason

            failed_here.add(candidate.pk)
            if should_learn_backtrack(child_reason):
                learn_bad(
                    candidate,
                    geometric_state,
                    branch_good,
                    branch_context_value,
                    branch_union,
                    branch_probe_map,
                    "branch_backtrack",
                    child_contacts,
                )
            else:
                stats[f"skipped_branch_learning:{child_reason}"] += 1

    seed_placement = place(base_orientations[0], (0, 0, 0), "seed")
    root_geometric_state = TurtleState(base_orientations)
    root_geometric_state.add_placement(seed_placement, depth=0)
    root_corona_tracker = CoronaTracker()
    root_corona_tracker.add_placement(seed_placement)
    root_branch_union, _, _ = fresh_intratile_union_find(scheme, side_action)
    _, root_return_reason = search(
        seed_path,
        Counter(),
        frozenset(),
        root_branch_union,
        extend_probe_map({}, seed_placement, scheme),
        root_geometric_state,
        root_corona_tracker,
    )
    final_orientations = build_hat_orientations(None)
    best_placements = path_to_placements(best_path, final_orientations)
    if stopped_reason == "searching":
        stopped_reason = "exhausted"
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result = EpisodeResult(
        policy="online-tree",
        seed=seed,
        elapsed_ms=elapsed_ms,
        tile_count=len(best_placements),
        corona=max_corona(best_placements),
        reward=reward_for(len(best_placements), max_corona(best_placements), stopped_reason, args.sample_target_tiles, target_corona),
        stopped_reason=stopped_reason,
        decisions=forced_moves + branch_moves,
        forced_moves=forced_moves,
        branch_moves=branch_moves,
        dead_frontier_checks=dead_frontier_checks,
        placements=best_placements,
        trajectory=[],
    )
    stats_payload = {
        **dict(stats),
        "nodes": nodes,
        "active_bad_pairs": active_bad_constraints(bad_counts, args.online_min_bad),
        "active_bad_clauses": active_bad_constraints(bad_clauses, args.online_min_bad),
        "unique_bad_pairs": len(bad_counts),
        "unique_bad_clauses": len(bad_clauses),
        "unique_scoped_bad_clauses": len(scoped_bad_clauses),
        "scoped_bad_clause_observations": sum(scoped_bad_clauses.values()),
        "assigned_roots": sum(1 for value in section_assignments.values() if value is not None),
        "root_return_reason": root_return_reason,
        "last_coloring": last_diagnostics,
    }
    return result, stats_payload, best_path


def sample_online_tree_contacts(args: argparse.Namespace, scheme: MarkScheme) -> dict[str, object]:
    base_orientations = build_hat_orientations(None)
    good_counts: Counter[ProbePair] = Counter()
    bad_counts: Counter[ProbePair] = Counter()
    bad_clauses: Counter[ProbeClause] = Counter()
    episode_summaries = []
    positive_paths = []
    runs = []
    neighbors_only = args.online_contact_scope == "neighbors"
    final_assignments: dict[str, AssignmentValue] = {}

    for episode in range(args.episodes):
        bad_observations_before = sum(bad_counts.values())
        bad_clauses_before = sum(bad_clauses.values())
        result, stats, path = run_online_tree_episode(args, scheme, bad_counts, bad_clauses, args.seed + episode * 101)
        new_bad_observations = sum(bad_counts.values()) - bad_observations_before
        new_bad_clauses = sum(bad_clauses.values()) - bad_clauses_before
        path_good = path_contact_pair_counts(path, base_orientations, scheme, neighbors_only)
        good_counts.update(path_good)
        placements = path_to_placements(path, base_orientations)
        positive_paths.append(placements)
        summary = {
            "episode": episode,
            "tiles": result.tile_count,
            "corona": result.corona,
            "stop": result.stopped_reason,
            "decisions": result.decisions,
            "sampled_good_contacts": sum(path_good.values()),
            "sampled_bad_contacts": new_bad_observations,
            "sampled_bad_clauses": new_bad_clauses,
            "active_bad_pairs": stats["active_bad_pairs"],
            "active_bad_clauses": stats["active_bad_clauses"],
            "unique_bad_pairs": stats["unique_bad_pairs"],
            "unique_bad_clauses": stats["unique_bad_clauses"],
        }
        last_coloring = stats.get("last_coloring", {})
        if isinstance(last_coloring, dict) and isinstance(last_coloring.get("_assignments"), dict):
            final_assignments = dict(last_coloring["_assignments"])  # type: ignore[arg-type]
        episode_summaries.append(summary)
        runs.append({"summary": summary, "online": stats})

    return {
        "good_counts": good_counts,
        "bad_counts": bad_counts,
        "bad_clauses": bad_clauses,
        "final_assignments": final_assignments,
        "episodes": episode_summaries,
        "positive_paths": positive_paths,
        "online": {
            "contact_scope": args.online_contact_scope,
            "min_good": args.online_min_good,
            "min_bad": args.online_min_bad,
            "max_bad_pairs_per_tile": args.online_max_bad_pairs_per_tile,
            "runs": runs,
            "final_active_bad_pairs": active_bad_constraints(bad_counts, args.online_min_bad),
            "final_active_bad_clauses": active_bad_constraints(bad_clauses, args.online_min_bad),
            "final_unique_bad_pairs": len(bad_counts),
            "final_unique_bad_clauses": len(bad_clauses),
            "final_bad_pair_observations": sum(bad_counts.values()),
            "final_bad_clause_observations": sum(bad_clauses.values()),
        },
    }


class SignedUnionFind:
    def __init__(self, values):
        self.parents = {value: value for value in values}
        self.signs = {value: 1 for value in values}
        self.zero = {value: False for value in values}

    def clone(self) -> "SignedUnionFind":
        other = SignedUnionFind.__new__(SignedUnionFind)
        other.parents = dict(self.parents)
        other.signs = dict(self.signs)
        other.zero = dict(self.zero)
        return other

    def find(self, value):
        parent = self.parents[value]
        if parent != value:
            root, parent_sign = self.find(parent)
            self.signs[value] *= parent_sign
            self.parents[value] = root
        return self.parents[value], self.signs[value]

    def union(self, left, right, relation: int) -> bool:
        left_root, left_sign = self.find(left)
        right_root, right_sign = self.find(right)
        if left_root == right_root:
            valid = left_sign == relation * right_sign
            if not valid:
                self.zero[left_root] = True
            return valid
        if right_root < left_root:
            self.parents[left_root] = right_root
            self.signs[left_root] = relation * right_sign * left_sign
            self.zero[right_root] = self.zero[right_root] or self.zero[left_root]
        else:
            self.parents[right_root] = left_root
            self.signs[right_root] = relation * left_sign * right_sign
            self.zero[left_root] = self.zero[left_root] or self.zero[right_root]
        return True

    def is_zero(self, value) -> bool:
        root, _ = self.find(value)
        return self.zero[root]


def signed_probe_relation(left: ProbeVar, right: ProbeVar, side_action: str) -> int:
    # Actual mark values are side_factor(side) * base_value(edge, in/out).
    # Matching marks therefore induce either equality or negated equality
    # between the side-free base variables.
    return side_factor(left[0], side_action) * side_factor(right[0], side_action)


@lru_cache(maxsize=None)
def intratile_union_template(
    scheme: MarkScheme,
    side_action: str,
) -> tuple[SignedUnionFind, int, int]:
    union_find = SignedUnionFind(all_base_probe_vars(scheme))
    contradictions = 0
    equalities_used = 0
    for group in intratile_probe_groups(scheme):
        first = group[0]
        for variable in group[1:]:
            equalities_used += 1
            if not union_find.union(
                base_probe_var(first),
                base_probe_var(variable),
                signed_probe_relation(first, variable, side_action),
            ):
                contradictions += 1
    return union_find, contradictions, equalities_used


def fresh_intratile_union_find(
    scheme: MarkScheme,
    side_action: str,
) -> tuple[SignedUnionFind, int, int]:
    template, contradictions, equalities_used = intratile_union_template(scheme, side_action)
    return template.clone(), contradictions, equalities_used


def unit_bad_clauses(bad_counts: Counter[ProbePair]) -> Counter[ProbeClause]:
    return Counter({(pair,): count for pair, count in bad_counts.items()})


def probe_value(
    variable: ProbeVar,
    assignments: dict[BaseProbeVar, AssignmentValue],
    union_find: SignedUnionFind,
    side_action: str,
) -> AssignmentValue:
    root, sign = union_find.find(base_probe_var(variable))
    value = None if union_find.zero[root] else assignments[root]
    if value is None:
        return None
    return side_factor(variable[0], side_action) * sign * value


def clause_satisfied(
    clause: ProbeClause,
    assignments: dict[BaseProbeVar, AssignmentValue],
    union_find: SignedUnionFind,
    side_action: str,
) -> bool:
    for left, right in clause:
        left_value = probe_value(left, assignments, union_find, side_action)
        right_value = probe_value(right, assignments, union_find, side_action)
        if left_value is not None and right_value is not None and left_value != right_value:
            return True
    return False


def positive_pair_conflicts(
    pairs: list[ProbePair],
    assignments: dict[BaseProbeVar, AssignmentValue],
    union_find: SignedUnionFind,
    side_action: str,
) -> list[ProbePair]:
    conflicts = []
    for left, right in pairs:
        left_value = probe_value(left, assignments, union_find, side_action)
        right_value = probe_value(right, assignments, union_find, side_action)
        if left_value is not None and right_value is not None and left_value != right_value:
            conflicts.append((left, right))
    return conflicts


def unsatisfied_clauses(
    clauses: list[ProbeClause],
    assignments: dict[BaseProbeVar, AssignmentValue],
    union_find: SignedUnionFind,
    side_action: str,
) -> list[ProbeClause]:
    return [clause for clause in clauses if not clause_satisfied(clause, assignments, union_find, side_action)]


def build_spec_from_assignments(
    assignments: dict[BaseProbeVar, AssignmentValue],
    union_find: SignedUnionFind,
    side_action: str,
    args: argparse.Namespace,
    scheme: MarkScheme,
    label: str,
) -> MarkingSpec:
    fore_probe_marks = []
    rear_probe_marks = []
    fore_site_marks = []
    rear_site_marks = []
    emitted_marks = set()
    for side in ("fore", "rear"):
        for mark in scheme:
            value = probe_value((side, mark.name), assignments, union_find, side_action)
            if value is None:
                continue
            mark_key = (side, key(mark.point), mark.component, value)
            if mark_key in emitted_marks:
                continue
            emitted_marks.add(mark_key)
            if args.probe_mode == "lattice":
                item = (mark.point, mark.component, value)
                if side == "fore":
                    fore_site_marks.append(item)
                else:
                    rear_site_marks.append(item)
            else:
                if mark.edge is None or mark.offset is None:
                    raise ValueError("legacy probe mark is missing edge metadata")
                item = (mark.edge, mark.offset, value)
                if side == "fore":
                    fore_probe_marks.append(item)
                else:
                    rear_probe_marks.append(item)
    channel_count = len({mark.component for mark in scheme})
    spec = MarkingSpec(
        f"sampled-{args.probe_mode}:{label}:channels={channel_count}:episodes={args.episodes}",
        fore_probe_marks=tuple(fore_probe_marks),
        rear_probe_marks=tuple(rear_probe_marks),
        fore_site_marks=tuple(fore_site_marks),
        rear_site_marks=tuple(rear_site_marks),
    )
    return spec


def ternary_clause_assignment(
    roots: list[BaseProbeVar],
    active_clauses: list[ProbeClause],
    positive_pairs: list[ProbePair],
    union_find: SignedUnionFind,
    side_action: str,
    args: argparse.Namespace,
) -> tuple[dict[BaseProbeVar, AssignmentValue], dict[str, object]]:
    seed = getattr(args, "assignment_seed", getattr(args, "seed", 0))
    rng = random.Random(seed + len(active_clauses) * 7919 + len(roots) * 104729)
    trials = max(1, int(getattr(args, "assignment_trials", 200)))
    steps = max(0, int(getattr(args, "assignment_steps", 0)))
    domain: tuple[int, ...] = (-1, 0, 1)
    fill_unassigned = getattr(args, "assignment_fill_unassigned", False)
    fixed_star = {root for root in roots if union_find.zero[root]}
    positive_pairs_by_root: dict[BaseProbeVar, list[ProbePair]] = defaultdict(list)
    for pair in positive_pairs:
        left, right = pair
        left_root, _ = union_find.find(base_probe_var(left))
        right_root, _ = union_find.find(base_probe_var(right))
        positive_pairs_by_root[left_root].append(pair)
        if right_root != left_root:
            positive_pairs_by_root[right_root].append(pair)
    initial_raw = getattr(args, "initial_assignments", {})
    initial_by_root: dict[BaseProbeVar, AssignmentValue] = {}
    if isinstance(initial_raw, dict):
        for raw_root, raw_value in initial_raw.items():
            if raw_root not in union_find.parents:
                continue
            if raw_value is None or raw_value == "*":
                continue
            root, sign = union_find.find(raw_root)
            value = sign * int(raw_value)
            previous = initial_by_root.get(root)
            if previous is None:
                initial_by_root[root] = value
            elif previous != value:
                initial_by_root[root] = None
    initial_assignments: dict[BaseProbeVar, AssignmentValue] = {}
    for root in roots:
        initial_assignments[root] = initial_by_root.get(root)
    initial_assigned_roots = {root for root, value in initial_assignments.items() if value is not None}
    locked_roots = initial_assigned_roots if getattr(args, "assignment_lock_initial", False) else set()
    best: dict[BaseProbeVar, AssignmentValue] | None = None
    best_unsatisfied = active_clauses[:]
    best_positive_conflicts: list[ProbePair] = []
    def density_score(assignments: dict[BaseProbeVar, AssignmentValue]) -> int:
        assigned = sum(1 for value in assignments.values() if value is not None)
        return -assigned if fill_unassigned else assigned

    best_score = (len(active_clauses), len(positive_pairs), len(roots))

    UnitEdge = tuple[BaseProbeVar, int, BaseProbeVar, int]

    def unit_edges() -> list[UnitEdge] | None:
        edges: list[UnitEdge] = []
        for clause in active_clauses:
            if len(clause) != 1:
                return None
            left, right = clause[0]
            left_root, left_sign = union_find.find(base_probe_var(left))
            right_root, right_sign = union_find.find(base_probe_var(right))
            edges.append(
                (
                    left_root,
                    side_factor(left[0], side_action) * left_sign,
                    right_root,
                    side_factor(right[0], side_action) * right_sign,
                )
            )
        return edges

    def unit_edge_satisfied(edge: UnitEdge, assignments: dict[BaseProbeVar, AssignmentValue]) -> bool:
        left_root, left_coeff, right_root, right_coeff = edge
        left_value = assignments[left_root]
        right_value = assignments[right_root]
        if left_value is None or right_value is None:
            return False
        return left_coeff * left_value != right_coeff * right_value

    def unit_clause_assignment(edges: list[UnitEdge]) -> tuple[dict[BaseProbeVar, AssignmentValue], dict[str, object]]:
        incident: dict[BaseProbeVar, list[UnitEdge]] = defaultdict(list)
        for edge in edges:
            left_root, _, right_root, _ = edge
            incident[left_root].append(edge)
            incident[right_root].append(edge)

        impossible_edges = [
            edge
            for edge in edges
            if (edge[0] == edge[2] and edge[1] == edge[3]) or edge[0] in fixed_star or edge[2] in fixed_star
        ]
        if impossible_edges:
            assignments = dict(initial_assignments)
            return assignments, {
                "assignment_mode": "unit-min-conflicts",
                "assignment_satisfied": False,
                "assignment_unsatisfied_clauses": len(impossible_edges),
                "assignment_positive_conflicts": 0,
                "assignment_impossible_unit_edges": len(impossible_edges),
                "assignment_initial_assigned_roots": len(initial_assigned_roots),
                "assignment_locked_roots": len(locked_roots),
            }

        best_unit: dict[BaseProbeVar, AssignmentValue] | None = None
        best_missing: list[UnitEdge] = edges[:]
        max_steps = steps if steps > 0 else max(200, len(edges) * 8)

        def conflict_count_for(root: BaseProbeVar, value: int, assignments: dict[BaseProbeVar, AssignmentValue]) -> int:
            trial = dict(assignments)
            trial[root] = value
            return sum(1 for edge in incident[root] if not unit_edge_satisfied(edge, trial))

        for trial in range(trials):
            assignments = dict(initial_assignments)
            fill_roots = roots if fill_unassigned else incident
            for root in fill_roots:
                if root in fixed_star:
                    assignments[root] = None
                elif assignments[root] is None:
                    assignments[root] = rng.choice(domain)
            for step in range(max_steps + 1):
                missing = [edge for edge in edges if not unit_edge_satisfied(edge, assignments)]
                if len(missing) < len(best_missing):
                    best_unit = dict(assignments)
                    best_missing = missing
                if not missing:
                    positive_conflicts = positive_pair_conflicts(positive_pairs, assignments, union_find, side_action)
                    if not positive_conflicts:
                        return assignments, {
                            "assignment_mode": "unit-min-conflicts",
                            "assignment_trials": trial + 1,
                            "assignment_steps": step,
                            "assignment_satisfied": True,
                            "assignment_unsatisfied_clauses": 0,
                            "assignment_positive_conflicts": 0,
                            "assignment_initial_assigned_roots": len(initial_assigned_roots),
                            "assignment_locked_roots": len(locked_roots),
                        }
                    # Branch equalities should normally have eliminated these;
                    # erase one endpoint so the generic caller reports a safe partial section.
                    for left, right in positive_conflicts[:8]:
                        root, _ = union_find.find(base_probe_var(rng.choice((left, right))))
                        if root not in fixed_star and root not in locked_roots:
                            assignments[root] = None
                    continue
                if step >= max_steps:
                    break
                edge = rng.choice(missing)
                candidate_roots = [edge[0]] if edge[0] == edge[2] else [edge[0], edge[2]]
                proposals = []
                for root in candidate_roots:
                    if root in fixed_star or root in locked_roots:
                        continue
                    for value in domain:
                        proposals.append((conflict_count_for(root, value, assignments), rng.random(), root, value))
                if not proposals:
                    break
                _, _, root, value = min(proposals)
                assignments[root] = value

        if best_unit is None:
            best_unit = dict(initial_assignments)
        positive_conflicts = positive_pair_conflicts(positive_pairs, best_unit, union_find, side_action)
        return best_unit, {
            "assignment_mode": "unit-min-conflicts",
            "assignment_trials": trials,
            "assignment_steps": max_steps,
            "assignment_satisfied": not best_missing and not positive_conflicts,
            "assignment_unsatisfied_clauses": len(best_missing),
            "assignment_positive_conflicts": len(positive_conflicts),
            "assignment_initial_assigned_roots": len(initial_assigned_roots),
            "assignment_locked_roots": len(locked_roots),
        }

    unit = unit_edges()
    if unit is not None:
        return unit_clause_assignment(unit)

    def random_assignment() -> dict[BaseProbeVar, AssignmentValue]:
        assignments = dict(initial_assignments)
        if fill_unassigned:
            for root in roots:
                if root in fixed_star:
                    assignments[root] = None
                elif assignments[root] is None:
                    assignments[root] = rng.choice(domain)
        return assignments

    def root_options(root: BaseProbeVar, assignments: dict[BaseProbeVar, AssignmentValue]) -> tuple[AssignmentValue, ...]:
        if root in fixed_star:
            return (None,)
        if root in locked_roots:
            return (assignments[root],)
        return domain

    def candidate_repairs(clause: ProbeClause, assignments: dict[BaseProbeVar, AssignmentValue]) -> list[dict[BaseProbeVar, AssignmentValue]]:
        proposals: list[dict[BaseProbeVar, AssignmentValue]] = []
        pairs = list(clause)
        rng.shuffle(pairs)
        for left, right in pairs[:64]:
            left_root, left_sign = union_find.find(base_probe_var(left))
            right_root, right_sign = union_find.find(base_probe_var(right))
            left_coeff = side_factor(left[0], side_action) * left_sign
            right_coeff = side_factor(right[0], side_action) * right_sign
            if left_root == right_root:
                if left_coeff == right_coeff or left_root in fixed_star:
                    continue
                choices = root_options(left_root, assignments)
                for value in choices:
                    if value is not None and left_coeff * value != right_coeff * value:
                        proposals.append({left_root: value})
                if assignments[left_root] is None:
                    proposals.extend(
                        {left_root: value}
                        for value in domain
                        if left_coeff * value != right_coeff * value
                    )
                continue
            for left_value in root_options(left_root, assignments):
                for right_value in root_options(right_root, assignments):
                    if left_value is None or right_value is None:
                        continue
                    if left_coeff * left_value == right_coeff * right_value:
                        continue
                    proposal = {}
                    if left_value != assignments[left_root] and left_root not in fixed_star:
                        proposal[left_root] = left_value
                    if right_value != assignments[right_root] and right_root not in fixed_star:
                        proposal[right_root] = right_value
                    if proposal:
                        proposals.append(proposal)
        rng.shuffle(proposals)
        return proposals

    def apply_proposal(
        assignments: dict[BaseProbeVar, AssignmentValue],
        proposal: dict[BaseProbeVar, AssignmentValue],
    ) -> dict[BaseProbeVar, AssignmentValue]:
        trial = dict(assignments)
        trial.update(proposal)
        return trial

    def local_positive_conflicts(
        assignments: dict[BaseProbeVar, AssignmentValue],
        proposal: dict[BaseProbeVar, AssignmentValue],
    ) -> int:
        if not proposal:
            return 0
        trial = apply_proposal(assignments, proposal)
        affected = {
            pair
            for root in proposal
            for pair in positive_pairs_by_root.get(root, [])
        }
        return len(positive_pair_conflicts(list(affected), trial, union_find, side_action))

    def choose_positive_repair(
        assignments: dict[BaseProbeVar, AssignmentValue],
        proposals: list[dict[BaseProbeVar, AssignmentValue]],
    ) -> dict[BaseProbeVar, AssignmentValue] | None:
        if not proposals:
            return None
        scored = []
        for proposal in proposals:
            trial = apply_proposal(assignments, proposal)
            scored.append(
                (
                    len(unsatisfied_clauses(active_clauses, trial, union_find, side_action)),
                    density_score(trial),
                    rng.random(),
                    proposal,
                )
            )
        scored.sort(key=lambda item: item[:3])
        return scored[0][3]

    def choose_clause_repair(
        clause: ProbeClause,
        assignments: dict[BaseProbeVar, AssignmentValue],
        proposals: list[dict[BaseProbeVar, AssignmentValue]],
    ) -> dict[BaseProbeVar, AssignmentValue] | None:
        if not proposals:
            return None
        scored = []
        for proposal in proposals:
            trial = apply_proposal(assignments, proposal)
            if not clause_satisfied(clause, trial, union_find, side_action):
                continue
            scored.append(
                (
                    local_positive_conflicts(assignments, proposal),
                    density_score(trial),
                    rng.random(),
                    proposal,
                )
            )
        if not scored:
            return None
        scored.sort(key=lambda item: item[:3])
        return scored[0][3]

    for trial in range(trials):
        assignments = random_assignment()
        max_steps = steps if steps > 0 else max(1, len(active_clauses) * 2)
        for step in range(max_steps + 1):
            missing = unsatisfied_clauses(active_clauses, assignments, union_find, side_action)
            positive_conflicts = positive_pair_conflicts(positive_pairs, assignments, union_find, side_action)
            score = (len(missing), len(positive_conflicts), density_score(assignments))
            if score < best_score:
                best = dict(assignments)
                best_unsatisfied = missing
                best_positive_conflicts = positive_conflicts
                best_score = score
            if not missing and not positive_conflicts:
                return assignments, {
                    "assignment_mode": "random",
                    "assignment_trials": trial + 1,
                    "assignment_steps": steps,
                    "assignment_satisfied": True,
                    "assignment_unsatisfied_clauses": 0,
                    "assignment_positive_conflicts": 0,
                }
            if step >= max_steps:
                break
            if positive_conflicts:
                left, right = rng.choice(positive_conflicts)
                candidates = []
                for variable in (left, right):
                    root, _ = union_find.find(base_probe_var(variable))
                    if root not in fixed_star and root not in locked_roots and assignments[root] is not None:
                        candidates.append({root: None})
                proposal = choose_positive_repair(assignments, candidates)
                if proposal is None:
                    break
                assignments = apply_proposal(assignments, proposal)
                continue
            clause = rng.choice(missing)
            repairs = candidate_repairs(clause, assignments)
            proposal = choose_clause_repair(clause, assignments, repairs[:64])
            if proposal is None:
                break
            assignments = apply_proposal(assignments, proposal)

    if best is None:
        best = {root: 0 for root in roots}
        best_unsatisfied = unsatisfied_clauses(active_clauses, best, union_find, side_action)
        best_positive_conflicts = positive_pair_conflicts(positive_pairs, best, union_find, side_action)
    satisfied = not best_unsatisfied and not best_positive_conflicts
    return best, {
        "assignment_mode": "random",
        "assignment_trials": trials,
        "assignment_steps": steps,
        "assignment_satisfied": satisfied,
        "assignment_unsatisfied_clauses": len(best_unsatisfied),
        "assignment_positive_conflicts": len(best_positive_conflicts),
        "assignment_unsatisfied_clause_sizes": [len(clause) for clause in best_unsatisfied[:8]],
        "assignment_initial_assigned_roots": len(initial_assigned_roots),
        "assignment_locked_roots": len(locked_roots),
    }


def train_coloring(sample: dict[str, object], args: argparse.Namespace, scheme: MarkScheme) -> tuple[MarkingSpec, dict[str, object]]:
    variables = all_probe_vars(scheme)
    base_variables = all_base_probe_vars(scheme)
    good_counts: Counter[ProbePair] = sample["good_counts"]  # type: ignore[assignment]
    branch_equalities: Counter[ProbePair] = sample.get("branch_equalities", Counter())  # type: ignore[assignment]
    bad_counts: Counter[ProbePair] = sample["bad_counts"]  # type: ignore[assignment]
    bad_clauses: Counter[ProbeClause] = sample.get("bad_clauses", unit_bad_clauses(bad_counts))  # type: ignore[assignment]
    side_action = getattr(args, "side_action", "opposite")
    union_find, intratile_contradictions, intratile_equalities_used = fresh_intratile_union_find(scheme, side_action)

    branch_equalities_used = 0
    branch_equality_contradictions = 0
    if getattr(args, "assignment_mode", "coloring") == "random":
        for (left, right), count in branch_equalities.items():
            if count < args.min_good:
                continue
            branch_equalities_used += 1
            if not union_find.union(
                base_probe_var(left),
                base_probe_var(right),
                signed_probe_relation(left, right, side_action),
            ):
                branch_equality_contradictions += 1

    roots = sorted({union_find.find(variable)[0] for variable in base_variables})
    assignment_mode = getattr(args, "assignment_mode", "coloring")
    if assignment_mode == "random":
        active_clauses = []
        negative_good_filtered = 0
        negative_branch_filtered = 0
        negative_clauses_dropped = 0
        for clause, count in bad_clauses.items():
            if count < args.min_bad:
                continue
            good_filtered = tuple(pair for pair in clause if good_counts.get(pair, 0) <= args.max_good_for_bad)
            negative_good_filtered += len(clause) - len(good_filtered)
            filtered_clause = tuple(
                pair for pair in good_filtered if pair_can_witness_disequality(pair, union_find, side_action)
            )
            negative_branch_filtered += len(good_filtered) - len(filtered_clause)
            if filtered_clause:
                active_clauses.append(filtered_clause)
            else:
                negative_clauses_dropped += 1
        positive_pairs = [pair for pair, count in good_counts.items() if count >= args.min_good]
        assignments, assignment_diagnostics = ternary_clause_assignment(
            roots,
            active_clauses,
            positive_pairs,
            union_find,
            side_action,
            args,
        )
        spec = build_spec_from_assignments(assignments, union_find, side_action, args, scheme, "partial-ternary")
        channel_count = len({mark.component for mark in scheme})
        physical_site_count = len({key(mark.point) for mark in scheme})
        emitted_fore = len(spec.fore_probe_marks) + len(spec.fore_site_marks)
        emitted_rear = len(spec.rear_probe_marks) + len(spec.rear_site_marks)
        value_counts = Counter(assignments.values())
        assignment_value_counts = {"*": value_counts.get(None, 0)}
        assignment_value_counts.update({str(value): value_counts.get(value, 0) for value in (-1, 0, 1)})
        diagnostics = {
            "channels": channel_count,
            "variables": len(variables),
            "base_variables": len(base_variables),
            "local_mark_entries": len(scheme),
            "local_physical_sites": physical_site_count,
            "local_site_channels": len({(key(mark.point), mark.component) for mark in scheme}),
            "rear_value_mode": side_action,
            "positive_pairs": len(good_counts),
            "branch_equalities": len(branch_equalities),
            "negative_pairs": len(bad_counts),
            "intratile_equalities_used": intratile_equalities_used,
            "intratile_equality_contradictions": intratile_contradictions,
            "branch_equalities_used": branch_equalities_used,
            "branch_equality_contradictions": branch_equality_contradictions,
            "positive_equalities_used": 0,
            "positive_pair_constraints": len(positive_pairs),
            "positive_equality_contradictions": 0,
            "negative_clauses_used": len(active_clauses),
            "negative_clauses_dropped": negative_clauses_dropped,
            "negative_clause_edges_chosen": 0,
            "negative_inequalities_used": 0,
            "negative_already_separated": sum(
                1 for clause in active_clauses if clause_satisfied(clause, assignments, union_find, side_action)
            ),
            "negative_contradictions": int(assignment_diagnostics.get("assignment_unsatisfied_clauses", 0)),
            "negative_zero_ignored": 0,
            "negative_good_filtered": negative_good_filtered,
            "negative_branch_filtered": negative_branch_filtered,
            "zero_components": sum(1 for root in roots if union_find.zero[root]),
            "zero_base_variables": sum(1 for variable in base_variables if union_find.is_zero(variable)),
            "emitted_fore_marks": emitted_fore,
            "emitted_rear_marks": emitted_rear,
            "emitted_zero_marks": sum(
                1
                for side in ("fore", "rear")
                for mark in scheme
                if probe_value((side, mark.name), assignments, union_find, side_action) == 0
            ),
            "color_count": len({value for value in assignments.values() if value is not None}),
            "assignment_value_counts": assignment_value_counts,
            **assignment_diagnostics,
            "_assignments": assignments,
            "top_bad_pairs": [
                {"pair": [list(pair[0]), list(pair[1])], "bad": bad, "good": good_counts.get(pair, 0)}
                for pair, bad in bad_counts.most_common(12)
            ],
            "top_bad_clauses": [
                {
                    "size": len(clause),
                    "bad": bad,
                    "pairs": [[list(pair[0]), list(pair[1])] for pair in clause[:4]],
                }
                for clause, bad in bad_clauses.most_common(8)
            ],
        }
        return spec, diagnostics

    positive_contradictions = 0
    for (left, right), count in good_counts.items():
        if count >= args.min_good:
            if not union_find.union(
                base_probe_var(left),
                base_probe_var(right),
                signed_probe_relation(left, right, side_action),
            ):
                positive_contradictions += 1

    selected_negative_edges: set[tuple[BaseProbeVar, BaseProbeVar]] = set()
    pending_clause_edges: list[set[tuple[BaseProbeVar, BaseProbeVar]]] = []
    negative_already_separated = 0
    negative_contradictions = 0
    negative_zero_ignored = 0
    negative_good_filtered = 0
    negative_clauses_used = 0
    for clause, bad_count in bad_clauses.items():
        if bad_count < args.min_bad:
            continue
        negative_clauses_used += 1
        clause_edges: set[tuple[BaseProbeVar, BaseProbeVar]] = set()
        clause_already_separated = False
        for pair in clause:
            if good_counts.get(pair, 0) > args.max_good_for_bad:
                negative_good_filtered += 1
                continue
            left, right = pair
            left_root, left_sign = union_find.find(base_probe_var(left))
            right_root, right_sign = union_find.find(base_probe_var(right))
            left_coeff = side_factor(left[0], side_action) * left_sign
            right_coeff = side_factor(right[0], side_action) * right_sign
            if union_find.zero[left_root] or union_find.zero[right_root]:
                negative_zero_ignored += 1
                continue
            if left_root == right_root:
                if left_coeff != right_coeff:
                    clause_already_separated = True
                    break
                continue
            if left_coeff != right_coeff:
                clause_already_separated = True
                break
            clause_edges.add(tuple(sorted((left_root, right_root))))
        if clause_already_separated:
            negative_already_separated += 1
        elif clause_edges:
            pending_clause_edges.append(clause_edges)
        else:
            negative_contradictions += 1

    for clause_edges in sorted(pending_clause_edges, key=lambda edges: (len(edges), sorted(edges))):
        if selected_negative_edges.intersection(clause_edges):
            continue
        selected_negative_edges.add(sorted(clause_edges)[0])

    graph: dict[BaseProbeVar, set[BaseProbeVar]] = defaultdict(set)
    for left, right in selected_negative_edges:
        graph[left].add(right)
        graph[right].add(left)

    colors: dict[BaseProbeVar, int] = {}
    for root in sorted(roots, key=lambda item: -len(graph[item])):
        used = {colors[neighbor] for neighbor in graph[root] if neighbor in colors}
        color = 1
        while color in used:
            color += 1
        colors[root] = color

    def color_of(variable: ProbeVar) -> int:
        root, sign = union_find.find(base_probe_var(variable))
        if union_find.zero[root]:
            return 0
        return side_factor(variable[0], side_action) * sign * colors[root]

    fore_probe_marks = []
    rear_probe_marks = []
    fore_site_marks = []
    rear_site_marks = []
    emitted_marks = set()
    for side in ("fore", "rear"):
        for mark in scheme:
            value = color_of((side, mark.name))
            if value == 0:
                continue
            mark_key = (side, key(mark.point), mark.component, value)
            if mark_key in emitted_marks:
                continue
            emitted_marks.add(mark_key)
            if args.probe_mode == "lattice":
                item = (mark.point, mark.component, value)
                if side == "fore":
                    fore_site_marks.append(item)
                else:
                    rear_site_marks.append(item)
            else:
                if mark.edge is None or mark.offset is None:
                    raise ValueError("legacy probe mark is missing edge metadata")
                item = (mark.edge, mark.offset, value)
                if side == "fore":
                    fore_probe_marks.append(item)
                else:
                    rear_probe_marks.append(item)

    channel_count = len({mark.component for mark in scheme})
    physical_site_count = len({key(mark.point) for mark in scheme})
    spec = MarkingSpec(
        f"sampled-{args.probe_mode}:channels={channel_count}:episodes={args.episodes}:colors={max(colors.values(), default=1)}",
        fore_probe_marks=tuple(fore_probe_marks),
        rear_probe_marks=tuple(rear_probe_marks),
        fore_site_marks=tuple(fore_site_marks),
        rear_site_marks=tuple(rear_site_marks),
    )
    diagnostics = {
        "channels": channel_count,
        "variables": len(variables),
        "base_variables": len(base_variables),
        "local_mark_entries": len(scheme),
        "local_physical_sites": physical_site_count,
        "local_site_channels": len({(key(mark.point), mark.component) for mark in scheme}),
        "rear_value_mode": side_action,
        "positive_pairs": len(good_counts),
        "negative_pairs": len(bad_counts),
        "intratile_equalities_used": intratile_equalities_used,
        "intratile_equality_contradictions": intratile_contradictions,
        "positive_equalities_used": sum(1 for count in good_counts.values() if count >= args.min_good),
        "positive_equality_contradictions": positive_contradictions,
        "negative_clauses_used": negative_clauses_used,
        "negative_clause_edges_chosen": len(selected_negative_edges),
        "negative_inequalities_used": len(selected_negative_edges),
        "negative_already_separated": negative_already_separated,
        "negative_contradictions": negative_contradictions,
        "negative_zero_ignored": negative_zero_ignored,
        "negative_good_filtered": negative_good_filtered,
        "zero_components": sum(1 for root in roots if union_find.zero[root]),
        "zero_base_variables": sum(1 for variable in base_variables if union_find.is_zero(variable)),
        "emitted_fore_marks": len(fore_probe_marks) + len(fore_site_marks),
        "emitted_rear_marks": len(rear_probe_marks) + len(rear_site_marks),
        "color_count": max(colors.values(), default=1),
        "top_bad_pairs": [
            {"pair": [list(pair[0]), list(pair[1])], "bad": bad, "good": good_counts.get(pair, 0)}
            for pair, bad in bad_counts.most_common(12)
        ],
        "top_bad_clauses": [
            {
                "size": len(clause),
                "bad": bad,
                "pairs": [[list(pair[0]), list(pair[1])] for pair in clause[:4]],
            }
            for clause, bad in bad_clauses.most_common(8)
        ],
    }
    return spec, diagnostics


def benchmark_spec(spec: MarkingSpec, args: argparse.Namespace) -> dict[str, object]:
    baseline_orientations = build_hat_orientations(None)
    marked_orientations = build_hat_orientations(spec)
    common = {
        "seed": args.seed,
        "target_tiles": args.benchmark_target_tiles,
        "target_corona": args.benchmark_target_corona,
        "max_steps": args.benchmark_max_steps,
        "node_limit": args.node_limit,
        "wall_time_ms": args.wall_time_ms,
        "frontier_limit": args.frontier_limit,
        "candidate_limit": args.candidate_limit,
        "boundary_alive": not args.no_boundary_alive,
    }
    baseline = run_tree_search(orientations=baseline_orientations, weights={}, policy="heuristic", **common)
    marked = run_tree_search(orientations=marked_orientations, weights={}, policy="heuristic", **common)
    filtered, filter_stats = run_mark_filter_tree_search(
        base_orientations=baseline_orientations,
        marked_orientations=marked_orientations,
        weights={},
        policy="heuristic",
        filter_boundary_mode=getattr(args, "static_filter_boundary", "geometric"),
        filter_frontier=getattr(args, "static_filter_frontier", False),
        **common,
    )
    return {
        "baseline": summarize(baseline),
        "marked": summarize(marked),
        "marked_filter": {
            **summarize(filtered),
            **filter_stats,
        },
    }


def validate_positive_paths(spec: MarkingSpec, sample: dict[str, object]) -> dict[str, object]:
    marked_orientations = build_hat_orientations(spec)
    failures = []
    max_corona_seen = 0
    max_tiles_seen = 0
    paths: list[list[Placement]] = sample.get("positive_paths", [])  # type: ignore[assignment]
    for path_index, placements in enumerate(paths):
        state = TurtleState(marked_orientations)
        try:
            for depth, placement in enumerate(placements):
                orientation = marked_orientations[placement.orientation.idx]
                state.add_placement(place(orientation, placement.translation, placement.placement_key), depth=depth)
        except ValueError as error:
            failures.append(
                {
                    "path": path_index,
                    "depth": len(state.placements),
                    "error": str(error),
                }
            )
            continue
        max_tiles_seen = max(max_tiles_seen, len(state.placements))
        from turtle_gcts_rl import max_corona

        max_corona_seen = max(max_corona_seen, max_corona(state.placements))
    return {
        "path_count": len(paths),
        "valid": not failures,
        "failures": failures[:8],
        "max_valid_tiles": max_tiles_seen,
        "max_valid_corona": max_corona_seen,
    }


def point_candidate_graph_metrics(spec: MarkingSpec | None, args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(spec)
    state = TurtleState(orientations)
    state.add_placement(place(orientations[0], (0, 0, 0), "seed"), depth=0)
    point_rows = []
    unique_candidates = set()
    limited_unique_candidates = set()
    edges = 0
    limited_edges = 0
    dead_points = 0
    for point in frontier(state):
        candidates = candidate_moves_for_frontier(point, state)
        if not candidates:
            dead_points += 1
        limited = candidates[: args.candidate_limit] if args.candidate_limit > 0 else candidates
        edges += len(candidates)
        limited_edges += len(limited)
        for candidate in candidates:
            unique_candidates.add(candidate.pk)
        for candidate in limited:
            limited_unique_candidates.add(candidate.pk)
        point_rows.append(
            {
                "point": list(point.point),
                "frontier_value": point.value,
                "candidate_count": len(candidates),
                "limited_candidate_count": len(limited),
            }
        )
    counts = [row["limited_candidate_count"] for row in point_rows]
    return {
        "frontier_points": len(point_rows),
        "dead_points": dead_points,
        "unique_candidates": len(unique_candidates),
        "limited_unique_candidates": len(limited_unique_candidates),
        "bipartite_edges": edges,
        "limited_bipartite_edges": limited_edges,
        "forced_points": sum(1 for count in counts if count == 1),
        "max_candidates_per_point": max(counts, default=0),
        "mean_candidates_per_point": round(sum(counts) / len(counts), 3) if counts else 0.0,
        "points": point_rows,
    }


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Learn Hat lattice/probe markings from unguided GCTS samples.")
    parser.add_argument(
        "--probe-mode",
        choices=["lattice", "a2", "midpoint"],
        default="lattice",
        help="Use direct A2 lattice marking sites, legacy A2 endpoint probes, or old doubled-lattice midpoint probes.",
    )
    parser.add_argument("--lattice-reach", type=int, default=1, help="A2 graph-neighborhood radius for lattice marking support.")
    parser.add_argument(
        "--lattice-base",
        choices=["tile", "boundary"],
        default="tile",
        help="For lattice mode, expand from the whole tile support or only from boundary vertices.",
    )
    parser.add_argument("--channels", type=int, choices=[1, 3], default=3, help="Number of marking channels for direct lattice mode.")
    parser.add_argument(
        "--side-action",
        choices=["opposite", "constant"],
        default="opposite",
        help="How reflected-side mark values relate to fore-side variables during coloring.",
    )
    parser.add_argument(
        "--assignment-mode",
        choices=["random", "coloring"],
        default="random",
        help="Assign ternary mark values randomly with repair, or use the older greedy coloring abstraction.",
    )
    parser.add_argument("--assignment-seed", type=int, default=0)
    parser.add_argument("--assignment-trials", type=int, default=200)
    parser.add_argument("--assignment-steps", type=int, default=0)
    parser.add_argument(
        "--assignment-lock-initial",
        action="store_true",
        help="Treat carried non-* section values as fixed while repairing new online constraints.",
    )
    parser.add_argument(
        "--assignment-fill-unassigned",
        action="store_true",
        help="Assign unconstrained section roots randomly instead of leaving them as *.",
    )
    parser.add_argument("--sample-source", choices=["rollout", "tree-path", "online-tree"], default="tree-path")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--sample-target-tiles", type=int, default=80)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--frontier-limit", type=int, default=10)
    parser.add_argument("--candidate-limit", type=int, default=14)
    parser.add_argument("--rollout-policy", choices=["heuristic", "random"], default="heuristic")
    parser.add_argument("--tree-policy", choices=["heuristic", "random"], default="heuristic")
    parser.add_argument("--sample-wall-time-ms", type=int, default=20000)
    parser.add_argument("--include-alive-alternatives", action="store_true")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--min-good", type=int, default=2)
    parser.add_argument("--min-bad", type=int, default=3)
    parser.add_argument("--max-good-for-bad", type=int, default=0)
    parser.add_argument("--online-min-good", type=int, default=1)
    parser.add_argument("--online-min-bad", type=int, default=1)
    parser.add_argument(
        "--online-contact-scope",
        choices=["neighbors", "all"],
        default="neighbors",
        help="When learning failed-tile inequalities online, compare against neighboring tiles or every previous tile.",
    )
    parser.add_argument(
        "--online-max-bad-pairs-per-tile",
        type=int,
        default=0,
        help="Cap inequalities learned from one failed tile; 0 keeps every observed contact pair.",
    )
    parser.add_argument(
        "--no-online-validate-updates",
        dest="online_validate_updates",
        action="store_false",
        default=True,
        help="Skip the current-patch replay/satisfiability check before committing a learned clause.",
    )
    parser.add_argument(
        "--online-learn-boundary-failures",
        action="store_true",
        help="Also learn clauses from one-step boundary-alive failures; off by default for pure backtrack learning.",
    )
    parser.add_argument(
        "--online-hard-mark-filter",
        action="store_true",
        help="When the current online marking admits candidates, skip candidates that conflict with it.",
    )
    parser.add_argument(
        "--online-hard-live-mark-filter",
        action="store_true",
        help="After boundary-alive checks, skip fallback candidates only if at least one marked candidate remains live.",
    )
    parser.add_argument(
        "--online-child-section-filter",
        action="store_true",
        help="Prefer candidates whose child branch can still satisfy the learned online section.",
    )
    parser.add_argument(
        "--online-scope-bad-clauses",
        action="store_true",
        help="Apply learned bad clauses only on branches extending the tentative equality context where they were learned.",
    )
    parser.add_argument(
        "--online-marked-boundary-alive",
        action="store_true",
        help="Use the current online marking in the one-step boundary-alive filter when possible.",
    )
    parser.add_argument(
        "--online-trust-marked-candidates",
        action="store_true",
        help="Skip one-step boundary-alive lookahead for candidates admitted by the current online marking.",
    )
    parser.add_argument("--benchmark-target-tiles", type=int, default=100)
    parser.add_argument("--benchmark-target-corona", type=int, default=10)
    parser.add_argument("--benchmark-max-steps", type=int, default=150)
    parser.add_argument("--node-limit", type=int, default=8000)
    parser.add_argument("--wall-time-ms", type=int, default=30000)
    parser.add_argument("--no-boundary-alive", action="store_true")
    parser.add_argument("--output", default="runs/hat-sampled-probe-marking.json")
    return parser.parse_args()


def main() -> None:
    args = read_args()
    scheme = mark_scheme(args.probe_mode, args.lattice_reach, args.channels, args.lattice_base)
    sample = sample_contacts(args, scheme)
    training_args = online_training_args(args)
    if isinstance(sample.get("final_assignments"), dict):
        values = vars(training_args).copy()
        values["initial_assignments"] = sample["final_assignments"]
        training_args = argparse.Namespace(**values)
    spec, diagnostics = train_coloring(sample, training_args, scheme)
    positive_validation = validate_positive_paths(spec, sample)
    benchmark = benchmark_spec(spec, args)
    graph_metrics = {
        "baseline": point_candidate_graph_metrics(None, args),
        "marked": point_candidate_graph_metrics(spec, args),
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
        "online": sample.get("online"),
        "marking": {
            "name": spec.name,
            "segments": segment_payload(spec),
        },
        "sampling": {
            "episodes": sample["episodes"],
            "mean_tiles": round(sum(item["tiles"] for item in sample["episodes"]) / max(1, len(sample["episodes"])), 3),
            "max_tiles": max((item["tiles"] for item in sample["episodes"]), default=0),
        },
        "training": diagnostics,
        "positive_path_validation": positive_validation,
        "single_tile_candidate_graph": graph_metrics,
        "benchmark": benchmark,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: payload[k]
                for k in (
                    "sampling",
                    "online",
                    "training",
                    "positive_path_validation",
                    "single_tile_candidate_graph",
                    "benchmark",
                )
            },
            indent=2,
        )
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
