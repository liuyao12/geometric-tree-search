#!/usr/bin/env python3
"""Local GCTS + RL experiments for the marked Turtle tiling.

This is intentionally self-contained and stdlib-only. It ports the Turtle
geometry and straight-line matching rules from apps/turtle-tiling-game/app.js,
then runs a frontier/candidate growth loop with an optional learned linear
policy over candidate moves.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


Point = tuple[int, int, int]
FeatureMap = dict[str, float]

MAX_ANGLE = 12
MARK_REACH = 3
SQRT2 = math.sqrt(2.0)
SQRT6 = math.sqrt(6.0)

TURTLE_VERTS: list[Point] = [
    (3, -2, -1),
    (2, 0, -2),
    (0, 1, -1),
    (0, 2, -2),
    (-1, 3, -2),
    (-2, 2, 0),
    (-1, 0, 1),
    (-2, 0, 2),
    (-2, -1, 3),
    (0, -2, 2),
    (1, -4, 3),
    (2, -4, 2),
    (3, -5, 2),
    (4, -4, 0),
]

TURTLE_ANGLES = [6, 4, 9, 4, 3, 4, 9, 4, 3, 8, 3, 8, 3, 4]
TURTLE_STRIPES = [(0, 10, 1), (2, 8, -1), (0, 6, -1), (4, 12, -1)]
PERMS = [
    (0, 1, 2),
    (0, 2, 1),
    (1, 0, 2),
    (1, 2, 0),
    (2, 0, 1),
    (2, 1, 0),
]


def key(point: Point) -> str:
    return f"{point[0]},{point[1]},{point[2]}"


def add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(point: Point, value: int) -> Point:
    return (point[0] * value, point[1] * value, point[2] * value)


def norm(point: Point) -> int:
    return abs(point[0]) + abs(point[1]) + abs(point[2])


def gcd2(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a or 1


def gcd3(a: int, b: int, c: int) -> int:
    return gcd2(gcd2(a, b), c)


def primitive(a: Point, b: Point) -> tuple[int, Point]:
    delta = sub(b, a)
    steps = gcd3(delta[0], delta[1], delta[2])
    return steps, (delta[0] // steps, delta[1] // steps, delta[2] // steps)


def segment_points(a: Point, b: Point, extra: int = 0) -> list[Point]:
    steps, step = primitive(a, b)
    return [add(a, scale(step, i - extra)) for i in range(steps + 1 + 2 * extra)]


def component_for(a: Point, b: Point) -> int:
    _, step = primitive(a, b)
    for idx in range(3):
        other = [j for j in range(3) if j != idx]
        if step[other[0]] == step[other[1]] and step[idx] == -2 * step[other[0]]:
            return idx
    return 0


def parity(perm: tuple[int, int, int]) -> int:
    inversions = int(perm[0] > perm[1]) + int(perm[0] > perm[2]) + int(perm[1] > perm[2])
    return 1 if inversions % 2 == 0 else -1


def project_raw(point: Point) -> tuple[float, float]:
    x, y, z = point
    return ((z - x) / SQRT2, (2 * y - x - z) / SQRT6)


def point_in_poly(pt: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    inside = False
    px, py = pt
    j = len(poly) - 1
    for i, a in enumerate(poly):
        b = poly[j]
        ax, ay = a
        bx, by = b
        cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
        dot = (px - ax) * (px - bx) + (py - ay) * (py - by)
        if abs(cross) < 1e-7 and dot <= 1e-7:
            return False
        if (ay > py) != (by > py) and px < ((bx - ax) * (py - ay)) / (by - ay) + ax:
            inside = not inside
        j = i
    return inside


def interiors(verts: list[Point]) -> list[Point]:
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    vertex_keys = {key(p) for p in verts}
    poly = [project_raw(p) for p in verts]
    out: list[Point] = []
    for x in range(min(xs), max(xs) + 1):
        for y in range(min(ys), max(ys) + 1):
            point = (x, y, -x - y)
            if key(point) not in vertex_keys and point_in_poly(project_raw(point), poly):
                out.append(point)
    return out


@dataclass(frozen=True)
class Symmetry:
    sign: int
    permutation: tuple[int, int, int]
    plane_sign: int


@dataclass(frozen=True)
class Occupancy:
    point: Point
    value: int
    kind: str = "vertex"


@dataclass(frozen=True)
class Mark:
    point: Point
    component: int
    value: int


@dataclass(frozen=True)
class Segment:
    p1: Point
    p2: Point
    component: int
    value: int


@dataclass(frozen=True)
class Orientation:
    idx: int
    name: str
    sym: Symmetry
    is_reflected: bool
    vertices: tuple[Point, ...]
    occupancy: tuple[Occupancy, ...]
    marks: tuple[Mark, ...]
    segments: tuple[Segment, ...]
    mark_scale: int = 1


@dataclass
class Placement:
    orientation: Orientation
    translation: Point
    vertices: tuple[Point, ...]
    occupancy: tuple[Occupancy, ...]
    marks: tuple[Mark, ...]
    segments: tuple[Segment, ...]
    placement_key: str
    depth: int = 0


@dataclass(frozen=True)
class FrontierPoint:
    point: Point
    value: int
    added_depth: int


@dataclass(frozen=True)
class Candidate:
    orientation: Orientation
    translation: Point
    pk: str
    frontier: FrontierPoint
    anchor_value: int
    score: int
    line_matches: int
    new_points: int
    overlap_points: int
    fill_value: int


@dataclass
class Decision:
    chosen: FeatureMap
    expected: FeatureMap
    candidates: int
    forced: bool


@dataclass
class EpisodeResult:
    policy: str
    seed: int
    elapsed_ms: int
    tile_count: int
    corona: int
    reward: float
    stopped_reason: str
    decisions: int
    forced_moves: int
    branch_moves: int
    dead_frontier_checks: int
    placements: list[Placement] = field(repr=False)
    trajectory: list[Decision] = field(default_factory=list, repr=False)


@dataclass
class MarkSum:
    value: int
    count: int = 1


def all_symmetries() -> list[Symmetry]:
    return [Symmetry(sign, perm, parity(perm)) for sign in (1, -1) for perm in PERMS]


def transform_linear(point: Point, sym: Symmetry) -> Point:
    return tuple(sym.sign * point[i] for i in sym.permutation)  # type: ignore[return-value]


def map_component(component: int, sym: Symmetry) -> int:
    return sym.permutation.index(component)


def segment_signature(segment: Segment) -> str:
    endpoints = sorted((key(segment.p1), key(segment.p2)))
    return f"{endpoints[0]}>{endpoints[1]}:{segment.value}"


def orientation_signature(orientation: Orientation) -> str:
    vertices = ";".join(sorted(key(point) for point in orientation.vertices))
    segments = ";".join(sorted(segment_signature(seg) for seg in orientation.segments))
    return f"{vertices}|mark_scale={orientation.mark_scale}|{segments}"


def orient_tile(
    verts: list[Point],
    occupancy: list[Occupancy],
    stripes: list[Segment],
    sym: Symmetry,
    idx: int,
    name: str,
    mark_scale: int = 1,
    mark_reach: int = MARK_REACH,
) -> Orientation:
    vertices = tuple(transform_linear(point, sym) for point in verts)
    next_occupancy = tuple(
        Occupancy(transform_linear(entry.point, sym), entry.value, entry.kind) for entry in occupancy
    )
    marks: list[Mark] = []
    segments: list[Segment] = []
    for segment in stripes:
        p1 = transform_linear(segment.p1, sym)
        p2 = transform_linear(segment.p2, sym)
        component = map_component(segment.component, sym)
        value = segment.value * sym.plane_sign
        for point in segment_points(p1, p2, mark_reach):
            marks.append(Mark(point, component, value))
        segments.append(Segment(p1, p2, component, value))
    return Orientation(
        idx=idx,
        name=name,
        sym=sym,
        is_reflected=sym.plane_sign < 0,
        vertices=vertices,
        occupancy=next_occupancy,
        marks=tuple(marks),
        segments=tuple(segments),
        mark_scale=mark_scale,
    )


def unique_orientations(orientations: Iterable[Orientation]) -> list[Orientation]:
    seen: set[str] = set()
    out: list[Orientation] = []
    for orientation in orientations:
        signature = orientation_signature(orientation)
        if signature in seen:
            continue
        seen.add(signature)
        out.append(
            Orientation(
                idx=len(out),
                name=orientation.name,
                sym=orientation.sym,
                is_reflected=orientation.is_reflected,
                vertices=orientation.vertices,
                occupancy=orientation.occupancy,
                marks=orientation.marks,
                segments=orientation.segments,
                mark_scale=orientation.mark_scale,
            )
        )
    return out


def build_turtle_orientations(marked: bool = True) -> list[Orientation]:
    turtle_occupancy = [
        *(Occupancy(point, TURTLE_ANGLES[idx], "vertex") for idx, point in enumerate(TURTLE_VERTS)),
        *(Occupancy(point, MAX_ANGLE, "interior") for point in interiors(TURTLE_VERTS)),
    ]
    stripe_segments = []
    if marked:
        for source, target, value in TURTLE_STRIPES:
            p1, p2 = TURTLE_VERTS[source], TURTLE_VERTS[target]
            stripe_segments.append(Segment(p1, p2, component_for(p1, p2), value))
    return unique_orientations(
        orient_tile(TURTLE_VERTS, turtle_occupancy, stripe_segments, sym, idx, "Turtle")
        for idx, sym in enumerate(all_symmetries())
    )


def place(orientation: Orientation, translation: Point, placement_key: str = "", depth: int = 0) -> Placement:
    mark_translation = scale(translation, orientation.mark_scale)
    return Placement(
        orientation=orientation,
        translation=translation,
        vertices=tuple(add(point, translation) for point in orientation.vertices),
        occupancy=tuple(
            Occupancy(add(entry.point, translation), entry.value, entry.kind) for entry in orientation.occupancy
        ),
        marks=tuple(Mark(add(entry.point, mark_translation), entry.component, entry.value) for entry in orientation.marks),
        segments=tuple(
            Segment(
                add(segment.p1, mark_translation),
                add(segment.p2, mark_translation),
                segment.component,
                segment.value,
            )
            for segment in orientation.segments
        ),
        placement_key=placement_key or f"{orientation.name}|{orientation.idx}|{key(translation)}",
        depth=depth,
    )


class TurtleState:
    def __init__(self, orientations: list[Orientation]):
        self.orientations = orientations
        self.placements: list[Placement] = []
        self.sums: dict[str, tuple[Point, int, int]] = {}
        self.mark_sums: dict[tuple[str, int], MarkSum] = {}
        self.used: set[str] = set()

    def clone(self) -> "TurtleState":
        other = TurtleState(self.orientations)
        other.placements = self.placements[:]
        other.sums = dict(self.sums)
        other.mark_sums = {k: MarkSum(v.value, v.count) for k, v in self.mark_sums.items()}
        other.used = set(self.used)
        return other

    def add_placement(self, placement: Placement, depth: int | None = None) -> None:
        added_depth = len(self.placements) if depth is None else depth
        self.placements.append(placement)
        self.used.add(placement.placement_key)
        for entry in placement.occupancy:
            point_key = key(entry.point)
            if point_key in self.sums:
                point, value, first_depth = self.sums[point_key]
                self.sums[point_key] = (point, value + entry.value, first_depth)
            else:
                self.sums[point_key] = (entry.point, entry.value, added_depth)
        for entry in placement.marks:
            mark_key = (key(entry.point), entry.component)
            previous = self.mark_sums.get(mark_key)
            if previous and previous.value != entry.value:
                raise ValueError("mark conflict reached state; candidate validation failed")
            if previous:
                self.mark_sums[mark_key] = MarkSum(previous.value, previous.count + 1)
            else:
                self.mark_sums[mark_key] = MarkSum(entry.value, 1)

    def remove_last_placement(self) -> Placement:
        if len(self.placements) <= 1:
            raise ValueError("refusing to remove the seed placement")
        placement = self.placements.pop()
        self.used.discard(placement.placement_key)
        for entry in placement.occupancy:
            point_key = key(entry.point)
            point, value, first_depth = self.sums[point_key]
            next_value = value - entry.value
            if next_value <= 0:
                del self.sums[point_key]
            else:
                self.sums[point_key] = (point, next_value, first_depth)
        for entry in placement.marks:
            mark_key = (key(entry.point), entry.component)
            previous = self.mark_sums[mark_key]
            if previous.count <= 1:
                del self.mark_sums[mark_key]
            else:
                self.mark_sums[mark_key] = MarkSum(previous.value, previous.count - 1)
        return placement


def frontier(state: TurtleState) -> list[FrontierPoint]:
    points = [
        FrontierPoint(point, value, depth)
        for point, value, depth in state.sums.values()
        if value < MAX_ANGLE
    ]
    return sorted(points, key=lambda item: (item.added_depth, norm(item.point), item.value))


def valid_candidate(
    orientation: Orientation,
    translation: Point,
    state: TurtleState,
    frontier_point: FrontierPoint,
    anchor_value: int,
) -> Candidate | None:
    pk = f"{orientation.name}|{orientation.idx}|{key(translation)}"
    if pk in state.used:
        return None

    new_points = 0
    overlap_points = 0
    fill_value = 0
    for entry in orientation.occupancy:
        point = add(entry.point, translation)
        current = state.sums.get(key(point))
        current_value = current[1] if current else 0
        if current_value == 0:
            new_points += 1
        else:
            overlap_points += 1
            fill_value += current_value
        if current_value + entry.value > MAX_ANGLE:
            return None
    if new_points == 0:
        return None

    line_matches = 0
    mark_translation = scale(translation, orientation.mark_scale)
    for entry in orientation.marks:
        point = add(entry.point, mark_translation)
        previous = state.mark_sums.get((key(point), entry.component))
        if not previous:
            continue
        if previous.value != entry.value:
            return None
        if entry.value != 0:
            line_matches += 1

    return Candidate(
        orientation=orientation,
        translation=translation,
        pk=pk,
        frontier=frontier_point,
        anchor_value=anchor_value,
        score=line_matches * 100 - new_points,
        line_matches=line_matches,
        new_points=new_points,
        overlap_points=overlap_points,
        fill_value=fill_value,
    )


def mark_compatible_candidate(
    orientation: Orientation,
    geometric_candidate: Candidate,
    state: TurtleState,
) -> Candidate | None:
    if geometric_candidate.pk in state.used:
        return None

    line_matches = 0
    mark_translation = scale(geometric_candidate.translation, orientation.mark_scale)
    for entry in orientation.marks:
        point = add(entry.point, mark_translation)
        previous = state.mark_sums.get((key(point), entry.component))
        if not previous:
            continue
        if previous.value != entry.value:
            return None
        if entry.value != 0:
            line_matches += 1

    return Candidate(
        orientation=orientation,
        translation=geometric_candidate.translation,
        pk=geometric_candidate.pk,
        frontier=geometric_candidate.frontier,
        anchor_value=geometric_candidate.anchor_value,
        score=line_matches * 100 - geometric_candidate.new_points,
        line_matches=line_matches,
        new_points=geometric_candidate.new_points,
        overlap_points=geometric_candidate.overlap_points,
        fill_value=geometric_candidate.fill_value,
    )


def candidate_moves_for_frontier(point: FrontierPoint, state: TurtleState) -> list[Candidate]:
    need = MAX_ANGLE - point.value
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for orientation in state.orientations:
        for anchor in orientation.occupancy:
            if anchor.value > need:
                continue
            translation = sub(point.point, anchor.point)
            candidate = valid_candidate(orientation, translation, state, point, anchor.value)
            if candidate and candidate.pk not in seen:
                seen.add(candidate.pk)
                candidates.append(candidate)
    return sorted(
        candidates,
        key=lambda item: (
            -item.line_matches,
            item.new_points,
            -item.overlap_points,
            norm(item.translation),
            item.orientation.idx,
        ),
    )


def has_candidate_for_frontier(point: FrontierPoint, state: TurtleState) -> bool:
    need = MAX_ANGLE - point.value
    for orientation in state.orientations:
        for anchor in orientation.occupancy:
            if anchor.value > need:
                continue
            translation = sub(point.point, anchor.point)
            if valid_candidate(orientation, translation, state, point, anchor.value):
                return True
    return False


def option_sort_key(option: tuple[FrontierPoint, list[Candidate]]) -> tuple[int, int, int, int, int]:
    point, candidates = option
    best_score = candidates[0].score if candidates else -10**9
    return (point.added_depth, len(candidates), norm(point.point), point.value, -best_score)


def candidate_keeps_boundary_alive(candidate: Candidate, state: TurtleState) -> bool:
    trial = state.clone()
    trial.add_placement(place(candidate.orientation, candidate.translation, candidate.pk), depth=len(state.placements))
    affected = []
    for entry in candidate.orientation.occupancy:
        point = add(entry.point, candidate.translation)
        current = trial.sums.get(key(point))
        if current and current[1] < MAX_ANGLE:
            affected.append(FrontierPoint(current[0], current[1], current[2]))
    return all(has_candidate_for_frontier(point, trial) for point in affected)


def candidate_features(candidate: Candidate, option_size: int, state: TurtleState) -> FeatureMap:
    frontier_need = MAX_ANGLE - candidate.frontier.value
    t = candidate.translation
    feature_map: FeatureMap = {
        "bias": 1.0,
        "line_match": min(candidate.line_matches, 12) / 12.0,
        "compact_new_points": -candidate.new_points / 24.0,
        "overlap_points": min(candidate.overlap_points, 12) / 12.0,
        "fill_value": min(candidate.fill_value, 72) / 72.0,
        "frontier_fill": candidate.frontier.value / MAX_ANGLE,
        "frontier_need": frontier_need / MAX_ANGLE,
        "frontier_norm": min(norm(candidate.frontier.point), 80) / 80.0,
        "option_inverse_width": 1.0 / math.sqrt(max(1, option_size)),
        "reflected": 1.0 if candidate.orientation.is_reflected else -1.0,
        f"orientation:{candidate.orientation.idx}": 1.0,
        f"anchor_angle:{candidate.anchor_value}": 1.0,
        f"frontier_value:{candidate.frontier.value}": 1.0,
        f"mod2:{t[0] % 2},{t[1] % 2}": 1.0,
        f"mod3:{t[0] % 3},{t[1] % 3}": 1.0,
    }
    if state.placements:
        seed = state.placements[0].translation
        feature_map[f"root_vector_mod4:{(t[0] - seed[0]) % 4},{(t[1] - seed[1]) % 4}"] = 1.0
    return feature_map


def dot(weights: dict[str, float], features: FeatureMap) -> float:
    return sum(weights.get(name, 0.0) * value for name, value in features.items())


def add_scaled(target: dict[str, float], features: FeatureMap, scale_value: float) -> None:
    for name, value in features.items():
        target[name] = target.get(name, 0.0) + value * scale_value
        if abs(target[name]) < 1e-12:
            del target[name]


def average_features(weighted: Iterable[tuple[float, FeatureMap]]) -> FeatureMap:
    out: FeatureMap = {}
    for probability, features in weighted:
        add_scaled(out, features, probability)
    return out


def softmax_probabilities(scores: list[float], temperature: float) -> list[float]:
    temp = max(1e-6, temperature)
    scaled = [score / temp for score in scores]
    top = max(scaled)
    exps = [math.exp(max(-60.0, min(60.0, score - top))) for score in scaled]
    total = sum(exps)
    return [value / total for value in exps]


def choose_index_by_probabilities(probabilities: list[float], rng: random.Random) -> int:
    roll = rng.random()
    cumulative = 0.0
    for idx, probability in enumerate(probabilities):
        cumulative += probability
        if roll <= cumulative:
            return idx
    return len(probabilities) - 1


def select_candidate(
    candidates: list[Candidate],
    state: TurtleState,
    weights: dict[str, float],
    rng: random.Random,
    policy: str,
    temperature: float,
    training: bool,
) -> tuple[Candidate, Decision | None]:
    feature_sets = [candidate_features(candidate, len(candidates), state) for candidate in candidates]
    if len(candidates) == 1:
        return candidates[0], Decision(feature_sets[0], feature_sets[0], 1, True) if training else None

    if policy == "random":
        idx = rng.randrange(len(candidates))
        probabilities = [1.0 / len(candidates)] * len(candidates)
    elif policy == "heuristic":
        idx = max(
            range(len(candidates)),
            key=lambda i: (
                candidates[i].line_matches,
                candidates[i].overlap_points,
                -candidates[i].new_points,
                -norm(candidates[i].translation),
            ),
        )
        probabilities = [0.0] * len(candidates)
        probabilities[idx] = 1.0
    elif policy in {"learned", "train"}:
        scores = [dot(weights, features) for features in feature_sets]
        if training:
            probabilities = softmax_probabilities(scores, temperature)
            idx = choose_index_by_probabilities(probabilities, rng)
        else:
            idx = max(range(len(candidates)), key=lambda i: scores[i])
            probabilities = [0.0] * len(candidates)
            probabilities[idx] = 1.0
    else:
        raise ValueError(f"unknown policy: {policy}")

    if not training:
        return candidates[idx], None
    expected = average_features(zip(probabilities, feature_sets))
    return candidates[idx], Decision(feature_sets[idx], expected, len(candidates), False)


def order_candidates(
    candidates: list[Candidate],
    state: TurtleState,
    weights: dict[str, float],
    rng: random.Random,
    policy: str,
    candidate_limit: int,
) -> list[Candidate]:
    if candidate_limit > 0:
        candidates = candidates[:candidate_limit]
    if policy == "random":
        shuffled = candidates[:]
        rng.shuffle(shuffled)
        return shuffled
    if policy == "heuristic":
        return sorted(
            candidates,
            key=lambda item: (
                -item.line_matches,
                -item.overlap_points,
                item.new_points,
                norm(item.translation),
                item.orientation.idx,
            ),
        )
    if policy == "learned":
        return sorted(
            candidates,
            key=lambda item: -dot(weights, candidate_features(item, len(candidates), state)),
        )
    raise ValueError(f"unknown policy: {policy}")


def choose_frontier_option(
    state: TurtleState,
    frontier_limit: int,
    candidate_limit: int,
) -> tuple[str, tuple[FrontierPoint, list[Candidate]] | None]:
    options: list[tuple[FrontierPoint, list[Candidate]]] = []
    for point in frontier(state)[:frontier_limit]:
        candidates = candidate_moves_for_frontier(point, state)
        if not candidates:
            return f"dead_frontier:{key(point.point)}", None
        options.append((point, candidates[:candidate_limit] if candidate_limit > 0 else candidates))
    if not options:
        return "no_frontier", None
    forced = [option for option in options if len(option[1]) == 1]
    return "ok", sorted(forced or options, key=option_sort_key)[0]


def max_corona(placements: list[Placement]) -> int:
    if not placements:
        return 0
    coronas = [math.inf] * len(placements)
    coronas[0] = 0
    by_point: dict[str, list[int]] = defaultdict(list)
    for idx, placement in enumerate(placements):
        for entry in placement.occupancy:
            by_point[key(entry.point)].append(idx)
    queue = [0]
    for idx in queue:
        for entry in placements[idx].occupancy:
            for neighbor in by_point.get(key(entry.point), []):
                if coronas[neighbor] > coronas[idx] + 1:
                    coronas[neighbor] = coronas[idx] + 1
                    queue.append(neighbor)
    finite = [value for value in coronas if math.isfinite(value)]
    return int(max(finite)) if finite else 0


def reward_for(tile_count: int, corona: int, stopped_reason: str, target_tiles: int, target_corona: int) -> float:
    reward = tile_count + 9.0 * corona
    if tile_count >= target_tiles:
        reward += 40.0
    if corona >= target_corona:
        reward += 30.0
    if stopped_reason.startswith("dead"):
        reward -= 20.0
    return reward


def run_tree_search(
    orientations: list[Orientation],
    weights: dict[str, float],
    seed: int,
    policy: str,
    target_tiles: int,
    target_corona: int,
    max_steps: int,
    node_limit: int,
    wall_time_ms: int,
    frontier_limit: int,
    candidate_limit: int,
    boundary_alive: bool,
    growth_callback: Callable[[int, int, int, int], None] | None = None,
) -> EpisodeResult:
    started = time.perf_counter()
    deadline = started + wall_time_ms / 1000.0 if wall_time_ms > 0 else None
    rng = random.Random(seed)
    state = TurtleState(orientations)
    state.add_placement(place(orientations[0], (0, 0, 0), "seed"), depth=0)

    effective_node_limit = node_limit if node_limit > 0 else max(800, target_corona * target_corona * 64)
    nodes = 0
    forced_moves = 0
    branch_moves = 0
    dead_frontier_checks = 0
    best_placements = state.placements[:]
    best_corona = 0
    best_reward = reward_for(1, 0, "seed", target_tiles, target_corona)
    stopped_reason = "searching"
    max_reported_corona = -1

    def out_of_time() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def report_growth(corona: int) -> None:
        nonlocal max_reported_corona
        if growth_callback is None or corona <= max_reported_corona:
            return
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        decisions = forced_moves + branch_moves
        for layer in range(max_reported_corona + 1, corona + 1):
            growth_callback(layer, elapsed_ms, len(state.placements), decisions)
        max_reported_corona = corona

    def remember(reason: str, corona: int | None = None) -> None:
        nonlocal best_placements, best_corona, best_reward
        if corona is None:
            corona = max_corona(state.placements)
        current_reward = reward_for(len(state.placements), corona, reason, target_tiles, target_corona)
        if current_reward > best_reward or (
            math.isclose(current_reward, best_reward)
            and (len(state.placements), corona) > (len(best_placements), best_corona)
        ):
            best_placements = state.placements[:]
            best_corona = corona
            best_reward = current_reward
            stopped_reason = reason

    def search() -> bool:
        nonlocal nodes, forced_moves, branch_moves, dead_frontier_checks, stopped_reason
        if out_of_time():
            stopped_reason = "wall_time_ms"
            remember("wall_time_ms")
            return False
        corona = max_corona(state.placements)
        report_growth(corona)
        remember("partial", corona)
        if len(state.placements) >= target_tiles:
            stopped_reason = "target_tiles"
            remember(stopped_reason, corona)
            return True
        if corona >= target_corona:
            stopped_reason = "target_corona"
            remember(stopped_reason, corona)
            return True
        if len(state.placements) >= max_steps:
            remember("max_steps", corona)
            return False
        if nodes >= effective_node_limit:
            stopped_reason = "node_limit"
            remember("node_limit", corona)
            return False

        status, option = choose_frontier_option(state, frontier_limit, candidate_limit)
        if status != "ok" or option is None:
            remember(status)
            return False

        _, raw_candidates = option
        candidates = order_candidates(raw_candidates, state, weights, rng, policy, candidate_limit)
        filtered_candidates = []
        for candidate in candidates:
            if boundary_alive and len(candidates) > 1:
                dead_frontier_checks += 1
                if not candidate_keeps_boundary_alive(candidate, state):
                    continue
            filtered_candidates.append(candidate)
        if not filtered_candidates:
            remember("filtered_dead_frontier")
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
            state.add_placement(place(candidate.orientation, candidate.translation, candidate.pk), depth=len(state.placements))
            if search():
                return True
            state.remove_last_placement()
        remember("exhausted")
        return False

    search()
    if stopped_reason == "searching":
        stopped_reason = "exhausted"
    corona = max_corona(best_placements)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return EpisodeResult(
        policy=f"gcts-{policy}",
        seed=seed,
        elapsed_ms=elapsed_ms,
        tile_count=len(best_placements),
        corona=corona,
        reward=reward_for(len(best_placements), corona, stopped_reason, target_tiles, target_corona),
        stopped_reason=stopped_reason,
        decisions=forced_moves + branch_moves,
        forced_moves=forced_moves,
        branch_moves=branch_moves,
        dead_frontier_checks=dead_frontier_checks,
        placements=best_placements,
        trajectory=[],
    )


def run_mark_filter_tree_search(
    base_orientations: list[Orientation],
    marked_orientations: list[Orientation],
    weights: dict[str, float],
    seed: int,
    policy: str,
    target_tiles: int,
    target_corona: int,
    max_steps: int,
    node_limit: int,
    wall_time_ms: int,
    frontier_limit: int,
    candidate_limit: int,
    boundary_alive: bool,
    filter_boundary_mode: str = "geometric",
    filter_frontier: bool = False,
    growth_callback: Callable[[int, int, int, int], None] | None = None,
) -> tuple[EpisodeResult, dict[str, int]]:
    """Run GCTS with geometric ordering and a separate marked compatibility filter."""
    if len(base_orientations) != len(marked_orientations):
        raise ValueError("base and marked orientation lists must have the same length")
    if filter_boundary_mode not in {"off", "geometric", "marked", "both"}:
        raise ValueError(f"unknown filter_boundary_mode: {filter_boundary_mode}")

    started = time.perf_counter()
    deadline = started + wall_time_ms / 1000.0 if wall_time_ms > 0 else None
    rng = random.Random(seed)
    geometric_state = TurtleState(base_orientations)
    needs_marked_geometry = boundary_alive and filter_boundary_mode in {"marked", "both"}
    marked_state = TurtleState(marked_orientations) if needs_marked_geometry else None
    mark_sums: dict[tuple[Point, int], MarkSum] = {}
    mark_stack: list[tuple[tuple[Point, int], int | None, int]] = []
    translated_mark_cache: dict[tuple[int, Point], tuple[tuple[Point, int, int], ...]] = {}
    geometric_state.add_placement(place(base_orientations[0], (0, 0, 0), "seed"), depth=0)
    if marked_state is not None:
        marked_state.add_placement(place(marked_orientations[0], (0, 0, 0), "seed"), depth=0)

    effective_node_limit = node_limit if node_limit > 0 else max(800, target_corona * target_corona * 64)
    nodes = 0
    forced_moves = 0
    branch_moves = 0
    dead_frontier_checks = 0
    best_placements = geometric_state.placements[:]
    best_corona = 0
    best_reward = reward_for(1, 0, "seed", target_tiles, target_corona)
    stopped_reason = "searching"
    max_reported_corona = -1
    stats: Counter[str] = Counter()

    def out_of_time() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def translated_mark_entries(orientation: Orientation, translation: Point) -> tuple[tuple[Point, int, int], ...]:
        cache_key = (orientation.idx, translation)
        cached = translated_mark_cache.get(cache_key)
        if cached is not None:
            stats["translated_mark_cache_hits"] += 1
            return cached
        mark_translation = scale(translation, orientation.mark_scale)
        entries = tuple(
            (add(entry.point, mark_translation), entry.component, entry.value)
            for entry in orientation.marks
        )
        translated_mark_cache[cache_key] = entries
        return entries

    def add_mark_values(orientation: Orientation, translation: Point) -> int:
        stack_start = len(mark_stack)
        for point, component, value in translated_mark_entries(orientation, translation):
            mark_key = (point, component)
            previous = mark_sums.get(mark_key)
            mark_stack.append((mark_key, previous.value if previous else None, previous.count if previous else 0))
            if previous:
                if previous.value != value:
                    raise ValueError("mark conflict reached state; candidate validation failed")
                mark_sums[mark_key] = MarkSum(previous.value, previous.count + 1)
            else:
                mark_sums[mark_key] = MarkSum(value, 1)
        return stack_start

    def restore_mark_values(stack_start: int) -> None:
        while len(mark_stack) > stack_start:
            mark_key, previous_value, previous_count = mark_stack.pop()
            if previous_count == 0 or previous_value is None:
                del mark_sums[mark_key]
            else:
                mark_sums[mark_key] = MarkSum(previous_value, previous_count)

    def fast_mark_compatible_candidate(marked_orientation: Orientation, candidate: Candidate) -> Candidate | None:
        line_matches = 0
        for point, component, value in translated_mark_entries(marked_orientation, candidate.translation):
            previous = mark_sums.get((point, component))
            if not previous:
                continue
            if previous.value != value:
                return None
            if value != 0:
                line_matches += 1
        return Candidate(
            orientation=marked_orientation,
            translation=candidate.translation,
            pk=candidate.pk,
            frontier=candidate.frontier,
            anchor_value=candidate.anchor_value,
            score=line_matches * 100 - candidate.new_points,
            line_matches=line_matches,
            new_points=candidate.new_points,
            overlap_points=candidate.overlap_points,
            fill_value=candidate.fill_value,
        )

    add_mark_values(marked_orientations[0], (0, 0, 0))

    def choose_mark_filtered_frontier_option() -> tuple[
        str,
        tuple[FrontierPoint, list[Candidate], list[tuple[Candidate, Candidate]]] | None,
    ]:
        options: list[tuple[FrontierPoint, list[Candidate], list[tuple[Candidate, Candidate]]]] = []
        for point in frontier(geometric_state)[:frontier_limit]:
            raw_candidates = candidate_moves_for_frontier(point, geometric_state)
            if not raw_candidates:
                return f"dead_frontier:{key(point.point)}", None
            if candidate_limit > 0:
                raw_candidates = raw_candidates[:candidate_limit]
            marked_pairs = []
            for candidate in raw_candidates:
                marked_candidate = fast_mark_compatible_candidate(marked_orientations[candidate.orientation.idx], candidate)
                if marked_candidate is not None:
                    marked_pairs.append((candidate, marked_candidate))
            stats["frontier_options_checked"] += 1
            stats["frontier_raw_candidates"] += len(raw_candidates)
            stats["frontier_mark_filtered_candidates"] += len(raw_candidates) - len(marked_pairs)
            if not marked_pairs:
                return f"mark_filtered_dead_frontier:{key(point.point)}", None
            options.append((point, raw_candidates, marked_pairs))
        if not options:
            return "no_frontier", None

        def filtered_option_sort_key(
            option: tuple[FrontierPoint, list[Candidate], list[tuple[Candidate, Candidate]]],
        ) -> tuple[int, int, int, int, int]:
            point, raw_candidates, marked_pairs = option
            best_score = raw_candidates[0].score if raw_candidates else -10**9
            return (point.added_depth, len(marked_pairs), norm(point.point), point.value, -best_score)

        forced = [option for option in options if len(option[2]) == 1]
        return "ok", sorted(forced or options, key=filtered_option_sort_key)[0]

    def report_growth(corona: int) -> None:
        nonlocal max_reported_corona
        if growth_callback is None or corona <= max_reported_corona:
            return
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        decisions = forced_moves + branch_moves
        for layer in range(max_reported_corona + 1, corona + 1):
            growth_callback(layer, elapsed_ms, len(geometric_state.placements), decisions)
        max_reported_corona = corona

    def remember(reason: str, corona: int | None = None) -> None:
        nonlocal best_placements, best_corona, best_reward, stopped_reason
        if corona is None:
            corona = max_corona(geometric_state.placements)
        current_reward = reward_for(len(geometric_state.placements), corona, reason, target_tiles, target_corona)
        if current_reward > best_reward or (
            math.isclose(current_reward, best_reward)
            and (len(geometric_state.placements), corona) > (len(best_placements), best_corona)
        ):
            best_placements = geometric_state.placements[:]
            best_corona = corona
            best_reward = current_reward
            stopped_reason = reason

    def boundary_ok(candidate: Candidate, marked_candidate: Candidate, raw_count: int) -> bool:
        nonlocal dead_frontier_checks
        if not boundary_alive or raw_count <= 1 or filter_boundary_mode == "off":
            return True
        dead_frontier_checks += 1
        if filter_boundary_mode in {"geometric", "both"} and not candidate_keeps_boundary_alive(
            candidate, geometric_state
        ):
            stats["geometric_boundary_filtered"] += 1
            return False
        if filter_boundary_mode in {"marked", "both"}:
            if marked_state is None:
                raise ValueError("marked boundary mode requires a marked state")
            if not candidate_keeps_boundary_alive(marked_candidate, marked_state):
                stats["marked_boundary_filtered"] += 1
                return False
        return True

    def search() -> bool:
        nonlocal nodes, forced_moves, branch_moves, stopped_reason
        if out_of_time():
            stopped_reason = "wall_time_ms"
            remember("wall_time_ms")
            return False
        corona = max_corona(geometric_state.placements)
        report_growth(corona)
        remember("partial", corona)
        if len(geometric_state.placements) >= target_tiles:
            stopped_reason = "target_tiles"
            remember(stopped_reason, corona)
            return True
        if corona >= target_corona:
            stopped_reason = "target_corona"
            remember(stopped_reason, corona)
            return True
        if len(geometric_state.placements) >= max_steps:
            remember("max_steps", corona)
            return False
        if nodes >= effective_node_limit:
            stopped_reason = "node_limit"
            remember("node_limit", corona)
            return False

        if filter_frontier:
            status, filtered_option = choose_mark_filtered_frontier_option()
            if status != "ok" or filtered_option is None:
                remember(status)
                return False
            _, raw_candidates, candidate_pairs = filtered_option
            boundary_option_size = len(raw_candidates)
            pair_by_key = {candidate.pk: (candidate, marked_candidate) for candidate, marked_candidate in candidate_pairs}
            candidates = [
                pair_by_key[candidate.pk]
                for candidate in order_candidates(raw_candidates, geometric_state, weights, rng, policy, candidate_limit)
                if candidate.pk in pair_by_key
            ]
        else:
            status, option = choose_frontier_option(geometric_state, frontier_limit, candidate_limit)
            if status != "ok" or option is None:
                remember(status)
                return False

            _, raw_candidates = option
            ordered_candidates = order_candidates(raw_candidates, geometric_state, weights, rng, policy, candidate_limit)
            boundary_option_size = len(ordered_candidates)
            candidates = []
            for candidate in ordered_candidates:
                marked_orientation = marked_orientations[candidate.orientation.idx]
                marked_candidate = fast_mark_compatible_candidate(marked_orientation, candidate)
                if marked_candidate is None:
                    stats["mark_filtered_candidates"] += 1
                    continue
                candidates.append((candidate, marked_candidate))

        filtered_candidates: list[tuple[Candidate, Candidate]] = []
        for candidate, marked_candidate in candidates:
            if boundary_ok(candidate, marked_candidate, boundary_option_size):
                filtered_candidates.append((candidate, marked_candidate))
            else:
                stats["boundary_filtered_candidates"] += 1
        stats["candidate_options"] += 1
        stats["raw_candidates"] += len(raw_candidates)
        stats["kept_candidates"] += len(filtered_candidates)

        if not filtered_candidates:
            remember("mark_filtered_dead_frontier" if stats["mark_filtered_candidates"] else "filtered_dead_frontier")
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
            geometric_state.add_placement(
                place(candidate.orientation, candidate.translation, candidate.pk), depth=len(geometric_state.placements)
            )
            stack_start = add_mark_values(marked_candidate.orientation, marked_candidate.translation)
            if marked_state is not None:
                marked_state.add_placement(
                    place(marked_candidate.orientation, marked_candidate.translation, marked_candidate.pk),
                    depth=len(marked_state.placements),
                )
            if search():
                return True
            if marked_state is not None:
                marked_state.remove_last_placement()
            restore_mark_values(stack_start)
            geometric_state.remove_last_placement()
        remember("exhausted")
        return False

    search()
    if stopped_reason == "searching":
        stopped_reason = "exhausted"
    corona = max_corona(best_placements)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result = EpisodeResult(
        policy=f"gcts-{policy}-mark-filter",
        seed=seed,
        elapsed_ms=elapsed_ms,
        tile_count=len(best_placements),
        corona=corona,
        reward=reward_for(len(best_placements), corona, stopped_reason, target_tiles, target_corona),
        stopped_reason=stopped_reason,
        decisions=forced_moves + branch_moves,
        forced_moves=forced_moves,
        branch_moves=branch_moves,
        dead_frontier_checks=dead_frontier_checks,
        placements=best_placements,
        trajectory=[],
    )
    return result, dict(stats)


def run_episode(
    orientations: list[Orientation],
    weights: dict[str, float],
    seed: int,
    policy: str,
    target_tiles: int,
    target_corona: int,
    max_steps: int,
    wall_time_ms: int,
    frontier_limit: int,
    candidate_limit: int,
    boundary_alive: bool,
    temperature: float,
    training: bool = False,
) -> EpisodeResult:
    started = time.perf_counter()
    deadline = started + wall_time_ms / 1000.0 if wall_time_ms > 0 else None
    rng = random.Random(seed)
    state = TurtleState(orientations)
    state.add_placement(place(orientations[0], (0, 0, 0), "seed"), depth=0)
    trajectory: list[Decision] = []
    stopped_reason = "target"
    forced_moves = 0
    branch_moves = 0
    dead_frontier_checks = 0

    for _ in range(max_steps):
        if deadline is not None and time.perf_counter() >= deadline:
            stopped_reason = "wall_time_ms"
            break
        if len(state.placements) >= target_tiles:
            stopped_reason = "target_tiles"
            break
        if max_corona(state.placements) >= target_corona:
            stopped_reason = "target_corona"
            break

        status, option = choose_frontier_option(state, frontier_limit, candidate_limit)
        if status != "ok" or option is None:
            stopped_reason = status
            break
        _, candidates = option
        if boundary_alive and len(candidates) > 1:
            filtered = []
            for candidate in candidates:
                dead_frontier_checks += 1
                if candidate_keeps_boundary_alive(candidate, state):
                    filtered.append(candidate)
            if filtered:
                candidates = filtered

        candidate, decision = select_candidate(
            candidates, state, weights, rng, "learned" if policy == "train" else policy, temperature, training
        )
        if decision:
            trajectory.append(decision)
        if len(candidates) == 1:
            forced_moves += 1
        else:
            branch_moves += 1
        state.add_placement(place(candidate.orientation, candidate.translation, candidate.pk), depth=len(state.placements))
    else:
        stopped_reason = "max_steps"

    corona = max_corona(state.placements)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    reward = reward_for(len(state.placements), corona, stopped_reason, target_tiles, target_corona)
    return EpisodeResult(
        policy=policy,
        seed=seed,
        elapsed_ms=elapsed_ms,
        tile_count=len(state.placements),
        corona=corona,
        reward=reward,
        stopped_reason=stopped_reason,
        decisions=forced_moves + branch_moves,
        forced_moves=forced_moves,
        branch_moves=branch_moves,
        dead_frontier_checks=dead_frontier_checks,
        placements=state.placements,
        trajectory=trajectory,
    )


def update_policy(weights: dict[str, float], result: EpisodeResult, advantage: float, learning_rate: float) -> None:
    if not result.trajectory:
        return
    scale_value = learning_rate * max(-2.5, min(2.5, advantage)) / math.sqrt(len(result.trajectory))
    for decision in result.trajectory:
        add_scaled(weights, decision.chosen, scale_value)
        add_scaled(weights, decision.expected, -scale_value)


def summarize_result(result: EpisodeResult) -> dict[str, object]:
    return {
        "policy": result.policy,
        "seed": result.seed,
        "elapsed_ms": result.elapsed_ms,
        "tile_count": result.tile_count,
        "corona": result.corona,
        "reward": round(result.reward, 3),
        "stopped_reason": result.stopped_reason,
        "decisions": result.decisions,
        "forced_moves": result.forced_moves,
        "branch_moves": result.branch_moves,
        "dead_frontier_checks": result.dead_frontier_checks,
    }


def aggregate_results(
    policy: str,
    results: list[EpisodeResult],
    target_tiles: int,
    target_corona: int,
) -> dict[str, object]:
    if not results:
        return {"policy": policy, "runs": 0}
    return {
        "policy": policy,
        "runs": len(results),
        "mean_elapsed_ms": round(sum(item.elapsed_ms for item in results) / len(results), 1),
        "mean_tile_count": round(sum(item.tile_count for item in results) / len(results), 2),
        "max_tile_count": max(item.tile_count for item in results),
        "mean_corona": round(sum(item.corona for item in results) / len(results), 2),
        "max_corona": max(item.corona for item in results),
        "success_tiles": sum(item.tile_count >= target_tiles for item in results),
        "success_corona": sum(item.corona >= target_corona for item in results),
        "stops": dict(Counter(item.stopped_reason.split(":")[0] for item in results)),
        "runs_detail": [summarize_result(item) for item in results],
    }


def placement_summary(placements: list[Placement], limit: int = 400) -> list[dict[str, object]]:
    return [
        {
            "orientation": placement.orientation.idx,
            "reflected": placement.orientation.is_reflected,
            "translation": list(placement.translation),
            "depth": placement.depth,
        }
        for placement in placements[:limit]
    ]


def macro_signatures(placements: list[Placement], limit: int = 20) -> dict[str, object]:
    orientation_counts = Counter(str(placement.orientation.idx) for placement in placements)
    reflected_counts = Counter("reflected" if placement.orientation.is_reflected else "direct" for placement in placements)

    by_point: dict[str, list[int]] = defaultdict(list)
    for idx, placement in enumerate(placements):
        for entry in placement.occupancy:
            by_point[key(entry.point)].append(idx)

    neighbor_counts: Counter[str] = Counter()
    seen_pairs: set[tuple[int, int]] = set()
    for indices in by_point.values():
        if len(indices) < 2:
            continue
        for i, left in enumerate(indices):
            for right in indices[i + 1 :]:
                pair = (min(left, right), max(left, right))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                a, b = placements[pair[0]], placements[pair[1]]
                rel = sub(b.translation, a.translation)
                signature = f"{a.orientation.idx}->{b.orientation.idx}|{key(rel)}"
                neighbor_counts[signature] += 1

    mod3_counts = Counter(f"{p.translation[0] % 3},{p.translation[1] % 3}" for p in placements)
    return {
        "orientation_counts": orientation_counts.most_common(limit),
        "reflection_counts": reflected_counts.most_common(),
        "translation_mod3_counts": mod3_counts.most_common(limit),
        "neighbor_signatures": neighbor_counts.most_common(limit),
    }


def load_policy(path: str | None) -> dict[str, float]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "weights" in data:
        return {str(k): float(v) for k, v in data["weights"].items()}
    return {str(k): float(v) for k, v in data.items()}


def save_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def top_weights(weights: dict[str, float], limit: int = 30) -> list[tuple[str, float]]:
    return [(name, round(value, 5)) for name, value in sorted(weights.items(), key=lambda item: -abs(item[1]))[:limit]]


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local GCTS + RL experiments on the marked Turtle tiling.")
    parser.add_argument("--mode", choices=["train", "eval"], default="train")
    parser.add_argument("--search-mode", choices=["tree", "greedy"], default="tree")
    parser.add_argument("--episodes", type=int, default=30, help="training episodes")
    parser.add_argument("--eval-runs", type=int, default=1)
    parser.add_argument("--baseline-runs", type=int, default=1)
    parser.add_argument("--target-tiles", type=int, default=90)
    parser.add_argument("--target-corona", type=int, default=6)
    parser.add_argument("--max-steps", type=int, default=140)
    parser.add_argument("--node-limit", type=int, default=3000)
    parser.add_argument("--wall-time-ms", type=int, default=30000)
    parser.add_argument("--frontier-limit", type=int, default=12)
    parser.add_argument("--candidate-limit", type=int, default=18)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--temperature", type=float, default=0.75)
    parser.add_argument("--policy-in")
    parser.add_argument("--policy-out")
    parser.add_argument("--output", default="runs/turtle-gcts-rl.json")
    parser.add_argument("--unmarked", action="store_true", help="ignore stripe matching rules")
    parser.add_argument("--no-boundary-alive", action="store_true", help="skip one-step boundary viability filtering")
    parser.add_argument("--placement-limit", type=int, default=400)
    return parser.parse_args()


def main() -> None:
    args = read_args()
    orientations = build_turtle_orientations(marked=not args.unmarked)
    weights = load_policy(args.policy_in)
    boundary_alive = not args.no_boundary_alive
    checkpoints: list[dict[str, object]] = []
    training_results: list[EpisodeResult] = []
    best_result: EpisodeResult | None = None
    best_training_result: EpisodeResult | None = None

    if args.mode == "train":
        recent_rewards: list[float] = []
        for episode in range(args.episodes):
            result = run_episode(
                orientations=orientations,
                weights=weights,
                seed=args.seed + episode * 17,
                policy="train",
                target_tiles=args.target_tiles,
                target_corona=args.target_corona,
                max_steps=args.max_steps,
                wall_time_ms=args.wall_time_ms,
                frontier_limit=args.frontier_limit,
                candidate_limit=args.candidate_limit,
                boundary_alive=boundary_alive,
                temperature=args.temperature,
                training=True,
            )
            training_results.append(result)
            recent_rewards.append(result.reward)
            if len(recent_rewards) > 24:
                recent_rewards.pop(0)
            mean_reward = sum(recent_rewards) / len(recent_rewards)
            variance = sum((value - mean_reward) ** 2 for value in recent_rewards) / max(1, len(recent_rewards) - 1)
            std_reward = math.sqrt(variance) or 1.0
            update_policy(weights, result, (result.reward - mean_reward) / std_reward, args.learning_rate)
            if best_result is None or result.reward > best_result.reward:
                best_result = result
            if best_training_result is None or result.reward > best_training_result.reward:
                best_training_result = result
            if episode == 0 or (episode + 1) % max(1, args.episodes // 10) == 0:
                window = training_results[-max(1, min(10, len(training_results))):]
                checkpoints.append(
                    {
                        "episode": episode + 1,
                        "mean_reward_last": round(sum(item.reward for item in window) / len(window), 3),
                        "mean_tiles_last": round(sum(item.tile_count for item in window) / len(window), 2),
                        "max_tiles_so_far": max(item.tile_count for item in training_results),
                        "max_corona_so_far": max(item.corona for item in training_results),
                    }
                )

    eval_results: dict[str, list[EpisodeResult]] = {}
    for policy in ("random", "heuristic", "learned"):
        if policy == "learned" and not weights:
            continue
        runs = []
        total_runs = args.eval_runs if policy == "learned" else args.baseline_runs
        for idx in range(total_runs):
            run_seed = args.seed + 10_000 + idx * 101 + len(policy)
            if args.search_mode == "tree":
                runs.append(
                    run_tree_search(
                        orientations=orientations,
                        weights=weights,
                        seed=run_seed,
                        policy=policy,
                        target_tiles=args.target_tiles,
                        target_corona=args.target_corona,
                        max_steps=args.max_steps,
                        node_limit=args.node_limit,
                        wall_time_ms=args.wall_time_ms,
                        frontier_limit=args.frontier_limit,
                        candidate_limit=args.candidate_limit,
                        boundary_alive=boundary_alive,
                    )
                )
            else:
                runs.append(
                    run_episode(
                        orientations=orientations,
                        weights=weights,
                        seed=run_seed,
                        policy=policy,
                        target_tiles=args.target_tiles,
                        target_corona=args.target_corona,
                        max_steps=args.max_steps,
                        wall_time_ms=args.wall_time_ms,
                        frontier_limit=args.frontier_limit,
                        candidate_limit=args.candidate_limit,
                        boundary_alive=boundary_alive,
                        temperature=args.temperature,
                        training=False,
                    )
                )
        eval_results[policy] = runs
        for item in runs:
            if best_result is None or item.reward > best_result.reward:
                best_result = item

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "mode": args.mode,
            "search_mode": args.search_mode,
            "episodes": args.episodes,
            "eval_runs": args.eval_runs,
            "baseline_runs": args.baseline_runs,
            "target_tiles": args.target_tiles,
            "target_corona": args.target_corona,
            "max_steps": args.max_steps,
            "node_limit": args.node_limit,
            "wall_time_ms": args.wall_time_ms,
            "frontier_limit": args.frontier_limit,
            "candidate_limit": args.candidate_limit,
            "seed": args.seed,
            "learning_rate": args.learning_rate,
            "temperature": args.temperature,
            "marked": not args.unmarked,
            "boundary_alive": boundary_alive,
        },
        "geometry": {
            "tile": "marked_turtle" if not args.unmarked else "unmarked_turtle",
            "orientations": len(orientations),
            "occupancy_points": len(orientations[0].occupancy),
            "mark_points": len(orientations[0].marks),
        },
        "training": {
            "episodes": len(training_results),
            "checkpoints": checkpoints,
            "best_training_run": summarize_result(best_training_result) if best_training_result else None,
        },
        "evaluation": [
            aggregate_results(policy, runs, args.target_tiles, args.target_corona)
            for policy, runs in eval_results.items()
        ],
        "learned_weights_top": top_weights(weights),
        "weights": weights,
        "best_patch": {
            "summary": summarize_result(best_result) if best_result else None,
            "placements": placement_summary(best_result.placements, args.placement_limit) if best_result else [],
            "macro_signatures": macro_signatures(best_result.placements) if best_result else {},
        },
    }

    save_json(args.output, payload)
    if args.policy_out:
        save_json(args.policy_out, {"generated_at": payload["generated_at"], "weights": weights})

    print(json.dumps({k: payload[k] for k in ("config", "geometry", "training", "evaluation", "learned_weights_top")}, indent=2))
    print(f"wrote {args.output}")
    if args.policy_out:
        print(f"wrote {args.policy_out}")


if __name__ == "__main__":
    main()
