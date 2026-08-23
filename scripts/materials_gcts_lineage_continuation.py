#!/usr/bin/env python3
"""Target-blind continuation of a frozen block lineage.

The worker replays every prior unordered action block to one exact colored
state, then invokes the same finite channel tree for one additional block.
It contains no scorer or target API and is independent of the number of prior
blocks, so clusters-of-clusters search is no longer hard-coded to depth three.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Callable, Hashable, Sequence

from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_iqc_three_block_channel_execution import (
    _channel_tree, _replay_action_set)


@dataclass(frozen=True)
class FrozenLineageSuccessor:
    stable_index: int
    actions: tuple[tuple, ...]
    all_actions: tuple[tuple, ...]


@dataclass(frozen=True)
class FrozenLineageContinuation:
    lineage_id: Hashable
    prior_blocks: int
    prior_actions: tuple[tuple, ...]
    replay_radii: tuple[float, ...]
    next_radius: float
    valid_orders_per_block: tuple[int, ...]
    candidate_counts_by_depth: tuple[int, ...]
    successors: tuple[FrozenLineageSuccessor, ...]
    naive_geometry_expansions: int
    unique_geometry_expansions: int
    saved_geometry_expansions: int
    geometry_cache_hits: int
    candidate_digest: str
    execution_digest: str
    target_used: bool = False


def extend_frozen_lineage(
        *, lineage_id: Hashable, center: Sequence[float],
        seed_positions: Sequence[Sequence[float]],
        seed_species: Sequence[Hashable],
        prior_actions: Sequence[tuple[Sequence[float], Hashable]],
        replay_radii: Sequence[float], next_radius: float,
        runtime_loader: Callable = load_default_runtime,
        replay: Callable = _replay_action_set,
        tree: Callable = _channel_tree,
        ) -> FrozenLineageContinuation:
    center = tuple(map(float, center))
    positions = tuple(tuple(map(float, point)) for point in seed_positions)
    species = tuple(map(str, seed_species))
    actions = action_key(tuple(prior_actions))
    radii = tuple(map(float, replay_radii))
    next_radius = float(next_radius)
    if (len(center) != 3 or not all(map(math.isfinite, center))
            or not positions or len(positions) != len(species)
            or not actions or len(actions) % 3
            or len(radii) != len(actions) // 3
            or any(value <= 0 or not math.isfinite(value) for value in radii)
            or tuple(sorted(radii)) != radii or len(set(radii)) != len(radii)
            or not math.isfinite(next_radius) or next_radius <= radii[-1]):
        raise ValueError("invalid frozen lineage continuation request")
    runtime = runtime_loader()
    source = SimpleNamespace(
        group=center, seed_positions=positions, seed_species=species)
    orders = []
    replayed = []
    for block_index, radius in enumerate(radii):
        block = actions[3 * block_index:3 * block_index + 3]
        state, valid_orders = replay(source, runtime, block, radius)
        replayed.extend(action_key(state.actions))
        orders.append(int(valid_orders))
        source = SimpleNamespace(
            group=center, seed_positions=tuple(state.positions),
            seed_species=tuple(state.species))
    if tuple(replayed) != actions:
        raise AssertionError("replayed lineage changed its exact action set")
    telemetry = {}
    states, counts = tree(
        source, runtime, next_radius, telemetry=telemetry,
        use_geometry_cache=True)
    successors = tuple(FrozenLineageSuccessor(
        stable_index, action_key(state.actions),
        actions + action_key(state.actions))
        for stable_index, state in enumerate(states))
    if any(len(row.actions) != 3 or len(row.all_actions) != len(actions) + 3
           for row in successors):
        raise AssertionError("continuation tree did not emit one complete block")
    candidate_digest = hashlib.sha256(repr(tuple(
        row.all_actions for row in successors)).encode()).hexdigest()
    metrics = tuple(int(telemetry.get(key, 0)) for key in (
        "naive_geometry_expansions", "unique_geometry_expansions",
        "saved_geometry_expansions", "geometry_cache_hits"))
    payload = (lineage_id, len(radii), actions, radii, next_radius,
               tuple(orders), tuple(counts), successors, metrics,
               candidate_digest, False)
    return FrozenLineageContinuation(
        lineage_id, len(radii), actions, radii, next_radius, tuple(orders),
        tuple(counts), successors, *metrics, candidate_digest,
        hashlib.sha256(repr(payload).encode()).hexdigest())


def lineage_continuation_worker(payload):
    """Process-pool adapter; payload contains no target or correctness label."""
    return extend_frozen_lineage(**payload)


__all__ = [
    "FrozenLineageContinuation", "FrozenLineageSuccessor",
    "extend_frozen_lineage", "lineage_continuation_worker"]
