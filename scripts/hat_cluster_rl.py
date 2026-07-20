#!/usr/bin/env python3
"""Learn and search with whole-tile Hat clusters.

The experiment is intentionally local:

1. run ordinary GCTS to collect Hat patches;
2. mine connected whole-tile cluster templates from those patches;
3. train a small policy-gradient proposer over cluster placements;
4. evaluate greedy macro growth and a DFS macro-GCTS that branches on clusters.

Cluster templates are allowed to overlap the current patch only by exact tile
placements. New tiles are then validated through the normal occupancy and
marking conflict checks.
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
from typing import Iterable

from hat_growth_curve import load_probe_or_site_spec
from hat_marking_search import MarkingSpec, build_hat_orientations, mined_edge_marking_specs, summarize
from turtle_gcts_rl import (
    FeatureMap,
    MAX_ANGLE,
    MarkSum,
    Orientation,
    Placement,
    Point,
    Symmetry,
    TurtleState,
    add,
    add_scaled,
    aggregate_results,
    average_features,
    choose_index_by_probabilities,
    key,
    max_corona,
    norm,
    parity,
    place,
    reward_for,
    run_tree_search,
    softmax_probabilities,
    sub,
    transform_linear,
)


SymKey = tuple[int, tuple[int, int, int]]


@dataclass(frozen=True)
class TemplateTile:
    rel_sym: Symmetry
    rel_translation: Point


@dataclass(frozen=True)
class ClusterTemplate:
    idx: int
    tiles: tuple[TemplateTile, ...]
    support: int
    source_tiles: int
    signature: str


@dataclass
class PlacementStats:
    new_points: int = 0
    overlap_points: int = 0
    fill_value: int = 0
    mark_matches: int = 0

    def add(self, other: "PlacementStats") -> None:
        self.new_points += other.new_points
        self.overlap_points += other.overlap_points
        self.fill_value += other.fill_value
        self.mark_matches += other.mark_matches


@dataclass
class ClusterCandidate:
    template: ClusterTemplate
    anchor_index: int
    placements: list[Placement]
    overlap_tiles: int
    stats: PlacementStats
    corona_gain: int
    features: FeatureMap = field(default_factory=dict)

    @property
    def new_tiles(self) -> int:
        return len(self.placements)


@dataclass
class ClusterDecision:
    chosen: FeatureMap
    expected: FeatureMap
    candidates: int


@dataclass
class ClusterEpisode:
    policy: str
    seed: int
    elapsed_ms: int
    tile_count: int
    corona: int
    reward: float
    stopped_reason: str
    macro_decisions: int
    tile_moves: int
    placements: list[Placement] = field(repr=False)
    trajectory: list[ClusterDecision] = field(default_factory=list, repr=False)


def sym_key(sym: Symmetry) -> SymKey:
    return sym.sign, sym.permutation


def compose_sym(left: Symmetry, right: Symmetry) -> Symmetry:
    # transform_linear(compose_sym(a, b), p) == transform_linear(a, transform_linear(b, p))
    permutation = tuple(right.permutation[left.permutation[idx]] for idx in range(3))
    return Symmetry(left.sign * right.sign, permutation, parity(permutation))


def inverse_sym(sym: Symmetry) -> Symmetry:
    inverse = [0, 0, 0]
    for idx, value in enumerate(sym.permutation):
        inverse[value] = idx
    permutation = tuple(inverse)
    return Symmetry(sym.sign, permutation, parity(permutation))


def inverse_transform(point: Point, sym: Symmetry) -> Point:
    return transform_linear(point, inverse_sym(sym))


def orientation_by_symmetry(orientations: list[Orientation]) -> dict[SymKey, Orientation]:
    return {sym_key(orientation.sym): orientation for orientation in orientations}


def placement_key(orientation: Orientation, translation: Point) -> str:
    return f"{orientation.name}|{orientation.idx}|{key(translation)}"


def tile_shape_key(placement: Placement) -> tuple[str, ...]:
    return tuple(sorted(key(point) for point in placement.vertices))


def validate_new_placement(placement: Placement, state: TurtleState) -> PlacementStats | None:
    stats = PlacementStats()
    for entry in placement.occupancy:
        current = state.sums.get(key(entry.point))
        current_value = current[1] if current else 0
        if current_value + entry.value > MAX_ANGLE:
            return None
        if current_value == 0:
            stats.new_points += 1
        else:
            stats.overlap_points += 1
            stats.fill_value += current_value
    if stats.new_points == 0:
        return None

    for entry in placement.marks:
        previous = state.mark_sums.get((key(entry.point), entry.component))
        if not previous:
            continue
        if previous.value != entry.value:
            return None
        if entry.value != 0:
            stats.mark_matches += 1
    return stats


def placements_touch(left: Placement, right: Placement) -> bool:
    left_points = {key(entry.point) for entry in left.occupancy}
    return any(key(entry.point) in left_points for entry in right.occupancy)


def adjacency_graph(placements: list[Placement]) -> dict[int, set[int]]:
    by_point: dict[str, list[int]] = defaultdict(list)
    for idx, placement in enumerate(placements):
        for entry in placement.occupancy:
            by_point[key(entry.point)].append(idx)
    graph: dict[int, set[int]] = {idx: set() for idx in range(len(placements))}
    seen: set[tuple[int, int]] = set()
    for indices in by_point.values():
        for i, left in enumerate(indices):
            for right in indices[i + 1 :]:
                pair = (min(left, right), max(left, right))
                if pair in seen:
                    continue
                seen.add(pair)
                graph[left].add(right)
                graph[right].add(left)
    return graph


def local_tile(anchor: Placement, placement: Placement) -> TemplateTile:
    rel_translation = inverse_transform(sub(placement.translation, anchor.translation), anchor.orientation.sym)
    rel_sym = compose_sym(inverse_sym(anchor.orientation.sym), placement.orientation.sym)
    return TemplateTile(rel_sym, rel_translation)


def template_signature(tiles: Iterable[TemplateTile]) -> str:
    parts = []
    for tile in tiles:
        parts.append(
            f"{tile.rel_sym.sign}:{','.join(str(v) for v in tile.rel_sym.permutation)}@{key(tile.rel_translation)}"
        )
    return "|".join(sorted(parts))


def mine_templates_from_patch(
    placements: list[Placement],
    max_cluster_tiles: int,
    radius: int,
) -> Counter[str]:
    graph = adjacency_graph(placements)
    counts: Counter[str] = Counter()
    for anchor_idx, anchor in enumerate(placements):
        distances = {anchor_idx: 0}
        queue = [anchor_idx]
        for idx in queue:
            if distances[idx] >= radius:
                continue
            for neighbor in sorted(graph[idx]):
                if neighbor in distances:
                    continue
                distances[neighbor] = distances[idx] + 1
                queue.append(neighbor)
        selected = sorted(distances, key=lambda idx: (distances[idx], idx))[:max_cluster_tiles]
        if len(selected) <= 1:
            continue
        tiles = tuple(local_tile(anchor, placements[idx]) for idx in selected)
        counts[template_signature(tiles)] += 1
    return counts


def parse_template_signature(signature: str) -> tuple[TemplateTile, ...]:
    tiles = []
    for raw in signature.split("|"):
        sym_raw, translation_raw = raw.split("@")
        sign_raw, permutation_raw = sym_raw.split(":")
        permutation = tuple(int(value) for value in permutation_raw.split(","))
        translation = tuple(int(value) for value in translation_raw.split(","))
        tiles.append(TemplateTile(Symmetry(int(sign_raw), permutation, parity(permutation)), translation))  # type: ignore[arg-type]
    return tuple(sorted(tiles, key=lambda tile: (norm(tile.rel_translation), key(tile.rel_translation), sym_key(tile.rel_sym))))


def mine_templates(
    orientations: list[Orientation],
    args: argparse.Namespace,
) -> tuple[list[ClusterTemplate], list[dict[str, object]]]:
    counts: Counter[str] = Counter()
    samples = []
    for episode in range(args.mine_episodes):
        result = run_tree_search(
            orientations=orientations,
            weights={},
            seed=args.seed + episode * 97,
            policy=args.mine_policy,
            target_tiles=args.mine_target_tiles,
            target_corona=args.mine_target_corona,
            max_steps=args.mine_max_steps,
            node_limit=args.mine_node_limit,
            wall_time_ms=args.mine_wall_time_ms,
            frontier_limit=args.frontier_limit,
            candidate_limit=args.candidate_limit,
            boundary_alive=not args.no_boundary_alive,
        )
        samples.append(summarize(result))
        counts.update(mine_templates_from_patch(result.placements, args.max_cluster_tiles, args.cluster_radius))

    templates = []
    for signature, support in counts.most_common(args.template_limit):
        if support < args.min_template_support:
            continue
        tiles = parse_template_signature(signature)
        templates.append(
            ClusterTemplate(
                idx=len(templates),
                tiles=tiles,
                support=support,
                source_tiles=len(tiles),
                signature=signature,
            )
        )
    return templates, samples


def instantiate_template(
    template: ClusterTemplate,
    anchor_index: int,
    state: TurtleState,
    orientation_by_sym: dict[SymKey, Orientation],
) -> ClusterCandidate | None:
    anchor = state.placements[anchor_index]
    trial = state.clone()
    whole_tile_keys = {tile_shape_key(placement) for placement in trial.placements}
    overlap_tiles = 0
    added: list[Placement] = []
    stats = PlacementStats()
    for tile in template.tiles:
        orientation_sym = compose_sym(anchor.orientation.sym, tile.rel_sym)
        orientation = orientation_by_sym.get(sym_key(orientation_sym))
        if orientation is None:
            return None
        translation = add(anchor.translation, transform_linear(tile.rel_translation, anchor.orientation.sym))
        pk = placement_key(orientation, translation)
        placement = place(orientation, translation, pk, depth=len(trial.placements))
        shape_key = tile_shape_key(placement)
        if shape_key in whole_tile_keys:
            overlap_tiles += 1
            continue
        placement_stats = validate_new_placement(placement, trial)
        if placement_stats is None:
            return None
        try:
            trial.add_placement(placement, depth=len(trial.placements))
        except ValueError:
            return None
        whole_tile_keys.add(shape_key)
        stats.add(placement_stats)
        added.append(placement)

    if overlap_tiles == 0 or not added:
        return None
    return ClusterCandidate(
        template=template,
        anchor_index=anchor_index,
        placements=added,
        overlap_tiles=overlap_tiles,
        stats=stats,
        corona_gain=0,
    )


def cluster_features(
    candidate: ClusterCandidate,
    state: TurtleState,
    args: argparse.Namespace,
    current_corona: int,
) -> FeatureMap:
    template = candidate.template
    anchor_age = len(state.placements) - 1 - candidate.anchor_index
    features: FeatureMap = {
        "bias": 1.0,
        "new_tiles": candidate.new_tiles / max(1, args.max_cluster_tiles),
        "overlap_tiles": candidate.overlap_tiles / max(1, template.source_tiles),
        "template_tiles": template.source_tiles / max(1, args.max_cluster_tiles),
        "support_log": math.log1p(template.support) / math.log1p(max(2, args.mine_episodes * 40)),
        "mark_matches": min(candidate.stats.mark_matches, 80) / 80.0,
        "overlap_points": min(candidate.stats.overlap_points, 80) / 80.0,
        "compact_new_points": -candidate.stats.new_points / max(1.0, 24.0 * candidate.new_tiles),
        "fill_value": min(candidate.stats.fill_value, 240) / 240.0,
        "corona_gain": min(candidate.corona_gain, 3) / 3.0,
        "anchor_recent": 1.0 / math.sqrt(1 + max(0, anchor_age)),
        "current_tiles": min(len(state.placements), args.target_tiles) / max(1, args.target_tiles),
        "current_corona": min(current_corona, args.target_corona) / max(1, args.target_corona),
        f"template_size:{template.source_tiles}": 1.0,
        f"new_tile_count:{candidate.new_tiles}": 1.0,
    }
    if args.template_feature_limit <= 0 or template.idx < args.template_feature_limit:
        features[f"template:{template.idx}"] = 1.0
    return features


def dot(weights: dict[str, float], features: FeatureMap) -> float:
    return sum(weights.get(name, 0.0) * value for name, value in features.items())


def cluster_score(candidate: ClusterCandidate, weights: dict[str, float], policy: str) -> float:
    if policy in {"learned", "train"}:
        return dot(weights, candidate.features)
    return (
        candidate.corona_gain * 10.0
        + candidate.new_tiles * 2.0
        + candidate.stats.mark_matches * 0.04
        + math.log1p(candidate.template.support)
        + candidate.overlap_tiles * 0.5
        - candidate.stats.new_points * 0.01
    )


def generate_cluster_candidates(
    state: TurtleState,
    templates: list[ClusterTemplate],
    orientation_by_sym: dict[SymKey, Orientation],
    weights: dict[str, float],
    policy: str,
    args: argparse.Namespace,
) -> list[ClusterCandidate]:
    anchors = list(range(max(0, len(state.placements) - args.anchor_limit), len(state.placements)))
    if 0 not in anchors:
        anchors.insert(0, 0)
    candidates: list[ClusterCandidate] = []
    seen: set[tuple[str, ...]] = set()
    current_corona = max_corona(state.placements)
    for anchor_index in anchors:
        for template in templates[: args.active_template_limit]:
            candidate = instantiate_template(template, anchor_index, state, orientation_by_sym)
            if candidate is None:
                continue
            placement_keys = tuple(sorted(placement.placement_key for placement in candidate.placements))
            if placement_keys in seen:
                continue
            seen.add(placement_keys)
            candidate.features = cluster_features(candidate, state, args, current_corona)
            candidates.append(candidate)
    candidates.sort(key=lambda item: -cluster_score(item, weights, policy))
    return candidates[: args.cluster_candidate_limit]


def apply_cluster(state: TurtleState, candidate: ClusterCandidate) -> None:
    for placement in candidate.placements:
        state.add_placement(placement, depth=len(state.placements))


def undo_cluster(state: TurtleState, count: int) -> None:
    for _ in range(count):
        state.remove_last_placement()


def select_cluster(
    candidates: list[ClusterCandidate],
    weights: dict[str, float],
    rng: random.Random,
    policy: str,
    temperature: float,
    training: bool,
) -> tuple[ClusterCandidate, ClusterDecision | None]:
    if policy == "random":
        probabilities = [1.0 / len(candidates)] * len(candidates)
        index = choose_index_by_probabilities(probabilities, rng)
    else:
        scores = [cluster_score(candidate, weights, "learned" if policy == "train" else policy) for candidate in candidates]
        if training:
            probabilities = softmax_probabilities(scores, temperature)
            index = choose_index_by_probabilities(probabilities, rng)
        else:
            index = max(range(len(candidates)), key=lambda idx: scores[idx])
            probabilities = [0.0] * len(candidates)
            probabilities[index] = 1.0

    if not training:
        return candidates[index], None
    expected = average_features((probability, candidate.features) for probability, candidate in zip(probabilities, candidates))
    return candidates[index], ClusterDecision(candidates[index].features, expected, len(candidates))


def run_cluster_episode(
    orientations: list[Orientation],
    templates: list[ClusterTemplate],
    weights: dict[str, float],
    seed: int,
    policy: str,
    args: argparse.Namespace,
    training: bool = False,
) -> ClusterEpisode:
    started = time.perf_counter()
    deadline = started + args.cluster_wall_time_ms / 1000.0 if args.cluster_wall_time_ms > 0 else None
    rng = random.Random(seed)
    by_sym = orientation_by_symmetry(orientations)
    state = TurtleState(orientations)
    state.add_placement(place(orientations[0], (0, 0, 0), "seed"), depth=0)
    trajectory: list[ClusterDecision] = []
    stopped_reason = "max_cluster_steps"
    macro_decisions = 0
    tile_moves = 0

    for _ in range(args.max_cluster_steps):
        if deadline is not None and time.perf_counter() >= deadline:
            stopped_reason = "wall_time_ms"
            break
        corona = max_corona(state.placements)
        if len(state.placements) >= args.target_tiles:
            stopped_reason = "target_tiles"
            break
        if corona >= args.target_corona:
            stopped_reason = "target_corona"
            break
        candidates = generate_cluster_candidates(state, templates, by_sym, weights, policy, args)
        if not candidates:
            stopped_reason = "no_cluster_candidate"
            break
        chosen, decision = select_cluster(candidates, weights, rng, policy, args.temperature, training)
        if decision is not None:
            trajectory.append(decision)
        apply_cluster(state, chosen)
        macro_decisions += 1
        tile_moves += chosen.new_tiles
    else:
        stopped_reason = "max_cluster_steps"

    corona = max_corona(state.placements)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ClusterEpisode(
        policy=policy,
        seed=seed,
        elapsed_ms=elapsed_ms,
        tile_count=len(state.placements),
        corona=corona,
        reward=reward_for(len(state.placements), corona, stopped_reason, args.target_tiles, args.target_corona),
        stopped_reason=stopped_reason,
        macro_decisions=macro_decisions,
        tile_moves=tile_moves,
        placements=state.placements[:],
        trajectory=trajectory,
    )


def update_cluster_policy(weights: dict[str, float], result: ClusterEpisode, advantage: float, learning_rate: float) -> None:
    if not result.trajectory:
        return
    scale_value = learning_rate * max(-2.5, min(2.5, advantage)) / math.sqrt(len(result.trajectory))
    for decision in result.trajectory:
        add_scaled(weights, decision.chosen, scale_value)
        add_scaled(weights, decision.expected, -scale_value)


def summarize_cluster_episode(result: ClusterEpisode) -> dict[str, object]:
    return {
        "policy": result.policy,
        "seed": result.seed,
        "elapsed_ms": result.elapsed_ms,
        "tile_count": result.tile_count,
        "corona": result.corona,
        "reward": round(result.reward, 3),
        "stopped_reason": result.stopped_reason,
        "macro_decisions": result.macro_decisions,
        "tile_moves": result.tile_moves,
    }


def aggregate_cluster_results(policy: str, results: list[ClusterEpisode], args: argparse.Namespace) -> dict[str, object]:
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
        "success_tiles": sum(item.tile_count >= args.target_tiles for item in results),
        "success_corona": sum(item.corona >= args.target_corona for item in results),
        "stops": dict(Counter(item.stopped_reason for item in results)),
        "runs_detail": [summarize_cluster_episode(item) for item in results],
    }


def run_cluster_tree_search(
    orientations: list[Orientation],
    templates: list[ClusterTemplate],
    weights: dict[str, float],
    seed: int,
    policy: str,
    args: argparse.Namespace,
) -> ClusterEpisode:
    started = time.perf_counter()
    deadline = started + args.tree_wall_time_ms / 1000.0 if args.tree_wall_time_ms > 0 else None
    by_sym = orientation_by_symmetry(orientations)
    state = TurtleState(orientations)
    state.add_placement(place(orientations[0], (0, 0, 0), "seed"), depth=0)
    best_placements = state.placements[:]
    best_corona = 0
    best_reward = reward_for(1, 0, "seed", args.target_tiles, args.target_corona)
    stopped_reason = "searching"
    nodes = 0
    macro_decisions = 0
    tile_moves = 0
    rng = random.Random(seed)

    def out_of_time() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def remember(reason: str) -> None:
        nonlocal best_placements, best_corona, best_reward
        corona = max_corona(state.placements)
        reward = reward_for(len(state.placements), corona, reason, args.target_tiles, args.target_corona)
        if reward > best_reward or (
            math.isclose(reward, best_reward) and (len(state.placements), corona) > (len(best_placements), best_corona)
        ):
            best_placements = state.placements[:]
            best_corona = corona
            best_reward = reward

    def search() -> bool:
        nonlocal nodes, stopped_reason, macro_decisions, tile_moves
        if out_of_time():
            stopped_reason = "wall_time_ms"
            remember(stopped_reason)
            return False
        corona = max_corona(state.placements)
        remember("partial")
        if len(state.placements) >= args.target_tiles:
            stopped_reason = "target_tiles"
            remember(stopped_reason)
            return True
        if corona >= args.target_corona:
            stopped_reason = "target_corona"
            remember(stopped_reason)
            return True
        if nodes >= args.tree_node_limit:
            stopped_reason = "node_limit"
            remember(stopped_reason)
            return False
        candidates = generate_cluster_candidates(state, templates, by_sym, weights, policy, args)
        if not candidates:
            remember("no_cluster_candidate")
            return False
        if policy == "random":
            rng.shuffle(candidates)
        for candidate in candidates[: args.tree_branch_limit]:
            if out_of_time() or nodes >= args.tree_node_limit:
                break
            nodes += 1
            macro_decisions += 1
            tile_moves += candidate.new_tiles
            apply_cluster(state, candidate)
            if search():
                return True
            undo_cluster(state, candidate.new_tiles)
        remember("exhausted")
        return False

    search()
    if stopped_reason == "searching":
        stopped_reason = "exhausted"
    corona = max_corona(best_placements)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ClusterEpisode(
        policy=f"cluster-tree-{policy}",
        seed=seed,
        elapsed_ms=elapsed_ms,
        tile_count=len(best_placements),
        corona=corona,
        reward=reward_for(len(best_placements), corona, stopped_reason, args.target_tiles, args.target_corona),
        stopped_reason=stopped_reason,
        macro_decisions=macro_decisions,
        tile_moves=tile_moves,
        placements=best_placements,
    )


def train_policy(
    orientations: list[Orientation],
    templates: list[ClusterTemplate],
    args: argparse.Namespace,
) -> tuple[dict[str, float], list[dict[str, object]]]:
    weights: dict[str, float] = {}
    history = []
    baseline = 0.0
    for episode in range(args.train_episodes):
        result = run_cluster_episode(
            orientations,
            templates,
            weights,
            args.seed + 10_000 + episode,
            "train",
            args,
            training=True,
        )
        baseline = result.reward if episode == 0 else 0.85 * baseline + 0.15 * result.reward
        update_cluster_policy(weights, result, result.reward - baseline, args.learning_rate)
        if episode % max(1, args.report_every) == 0 or episode == args.train_episodes - 1:
            history.append(
                {
                    "episode": episode,
                    "baseline": round(baseline, 3),
                    "result": summarize_cluster_episode(result),
                    "weight_count": len(weights),
                }
            )
    return weights, history


def load_marking(args: argparse.Namespace) -> MarkingSpec | None:
    if args.marking == "none":
        return None
    if args.marking == "rank3":
        return load_probe_or_site_spec(Path(args.rank3_marking))
    if args.marking == "edge":
        return mined_edge_marking_specs("H8", 4)[0]
    raise ValueError(f"unknown marking: {args.marking}")


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marking", choices=["rank3", "edge", "none"], default="rank3")
    parser.add_argument("--rank3-marking", default="runs/hat-sampled-lattice-rank3-zero-tiny-minimized.json")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--target-tiles", type=int, default=180)
    parser.add_argument("--target-corona", type=int, default=8)
    parser.add_argument("--frontier-limit", type=int, default=10)
    parser.add_argument("--candidate-limit", type=int, default=10)
    parser.add_argument("--no-boundary-alive", action="store_true")

    parser.add_argument("--mine-episodes", type=int, default=3)
    parser.add_argument("--mine-policy", choices=["heuristic", "random", "learned"], default="heuristic")
    parser.add_argument("--mine-target-tiles", type=int, default=120)
    parser.add_argument("--mine-target-corona", type=int, default=7)
    parser.add_argument("--mine-max-steps", type=int, default=220)
    parser.add_argument("--mine-node-limit", type=int, default=5000)
    parser.add_argument("--mine-wall-time-ms", type=int, default=20000)
    parser.add_argument("--max-cluster-tiles", type=int, default=4)
    parser.add_argument("--cluster-radius", type=int, default=2)
    parser.add_argument("--template-limit", type=int, default=80)
    parser.add_argument("--active-template-limit", type=int, default=50)
    parser.add_argument("--min-template-support", type=int, default=1)

    parser.add_argument("--train-episodes", type=int, default=60)
    parser.add_argument("--learning-rate", type=float, default=0.18)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--report-every", type=int, default=10)
    parser.add_argument("--cluster-wall-time-ms", type=int, default=4000)
    parser.add_argument("--max-cluster-steps", type=int, default=90)
    parser.add_argument("--anchor-limit", type=int, default=24)
    parser.add_argument("--cluster-candidate-limit", type=int, default=40)
    parser.add_argument("--template-feature-limit", type=int, default=40)

    parser.add_argument("--eval-runs", type=int, default=3)
    parser.add_argument("--single-node-limit", type=int, default=24000)
    parser.add_argument("--single-wall-time-ms", type=int, default=60000)
    parser.add_argument("--single-max-steps", type=int, default=450)
    parser.add_argument("--tree-node-limit", type=int, default=6000)
    parser.add_argument("--tree-wall-time-ms", type=int, default=60000)
    parser.add_argument("--tree-branch-limit", type=int, default=16)
    parser.add_argument("--output", default="runs/hat-cluster-rl-rank3.json")
    return parser.parse_args()


def main() -> None:
    args = read_args()
    spec = load_marking(args)
    orientations = build_hat_orientations(spec)
    templates, mining_samples = mine_templates(orientations, args)
    if not templates:
        raise SystemExit("no cluster templates mined")
    weights, training_history = train_policy(orientations, templates, args)

    greedy_heuristic = [
        run_cluster_episode(orientations, templates, {}, args.seed + 20_000 + idx, "heuristic", args)
        for idx in range(args.eval_runs)
    ]
    greedy_learned = [
        run_cluster_episode(orientations, templates, weights, args.seed + 30_000 + idx, "learned", args)
        for idx in range(args.eval_runs)
    ]
    tree_heuristic = run_cluster_tree_search(orientations, templates, {}, args.seed + 40_000, "heuristic", args)
    tree_learned = run_cluster_tree_search(orientations, templates, weights, args.seed + 50_000, "learned", args)
    single_tile = run_tree_search(
        orientations=orientations,
        weights={},
        seed=args.seed,
        policy="heuristic",
        target_tiles=args.target_tiles,
        target_corona=args.target_corona,
        max_steps=args.single_max_steps,
        node_limit=args.single_node_limit,
        wall_time_ms=args.single_wall_time_ms,
        frontier_limit=args.frontier_limit,
        candidate_limit=args.candidate_limit,
        boundary_alive=not args.no_boundary_alive,
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": vars(args),
        "marking": spec.name if spec else "none",
        "mining_samples": mining_samples,
        "templates": {
            "count": len(templates),
            "all": [
                {
                    "idx": template.idx,
                    "tiles": template.source_tiles,
                    "support": template.support,
                    "signature": template.signature,
                }
                for template in templates
            ],
            "top": [
                {
                    "idx": template.idx,
                    "tiles": template.source_tiles,
                    "support": template.support,
                    "signature": template.signature,
                }
                for template in templates[:20]
            ],
        },
        "training": {
            "history": training_history,
            "weight_count": len(weights),
            "weights": dict(sorted(weights.items())),
            "top_weights": sorted(weights.items(), key=lambda item: -abs(item[1]))[:30],
        },
        "evaluation": {
            "single_tile_gcts": summarize(single_tile),
            "cluster_greedy_heuristic": aggregate_cluster_results("cluster-greedy-heuristic", greedy_heuristic, args),
            "cluster_greedy_learned": aggregate_cluster_results("cluster-greedy-learned", greedy_learned, args),
            "cluster_tree_heuristic": summarize_cluster_episode(tree_heuristic),
            "cluster_tree_learned": summarize_cluster_episode(tree_learned),
        },
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["evaluation"], indent=2))
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
