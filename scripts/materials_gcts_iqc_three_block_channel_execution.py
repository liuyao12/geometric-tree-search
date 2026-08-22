#!/usr/bin/env python3
"""Target-free committed three-block IQC GCTS execution.

The first two blocks are exactly the already frozen rule that passed the
spatial rollback confirmation: one fusion-selected first terminal, then the
two-marking second-block portfolio followed by its public rollback metric.
The selected second state is self-fed into the compute-matched third block,
which spends eight expansions as three scalar leaders plus one leader from
each of five frozen pose/port channels.

This module accepts only a colored seed, a public center, and increasing
public radii.  It exposes no target, scorer, oracle, expected action, family
label, or lattice coordinate.  The output is an immutable portfolio of exact
candidate geometries for a later one-shot scorer.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, action_key, freeze_nucleus,
    load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import _rollout
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _second_block_candidates, _trace_score)
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _bounded_at_radius, _complete_states_at_radius)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES
from materials_gcts_pose_port_state_marking import (
    select_pose_port_channel_diverse)
from materials_gcts_recursive_connections import local_cluster_types


THIRD_ACTION_BUDGET = 8
THIRD_BASELINE_SLOTS = 3
THIRD_DEPTH = 3


@dataclass(frozen=True)
class FrozenThreeBlockTerminal:
    stable_index: int
    third_actions: tuple[tuple, ...]
    all_actions: tuple[tuple, ...]


@dataclass(frozen=True)
class FrozenThreeBlockChannelExecution:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float, float]
    first_candidate_counts: tuple[int, ...]
    first_candidate_digest: str
    first_selected_stable_index: int
    first_actions: tuple[tuple, ...]
    first_action_orders: int
    second_candidate_counts: tuple[int, ...]
    second_candidate_count: int
    second_candidate_digest: str
    second_model_digests: tuple[tuple[str, str], ...]
    second_retained: tuple[tuple[int, str, float], ...]
    second_selected_stable_index: int
    second_actions: tuple[tuple, ...]
    third_candidate_counts: tuple[int, ...]
    terminals: tuple[FrozenThreeBlockTerminal, ...]
    candidate_digest: str
    execution_digest: str
    target_used: bool = False


def _point_key(point):
    return tuple(round(float(value), 6) for value in point)


def _state_key(state):
    return tuple(sorted((str(color), *_point_key(point))
                        for point, color in zip(
                            state.positions, state.species)))


def _initial_state(source, runtime, radius):
    frontier = _bounded_at_radius(
        runtime["connection"], source,
        local_cluster_types(source.seed_positions, source.seed_species,
                            CLUSTER_EDGES), radius)
    return FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ())


def _replay_action_set(source, runtime, actions, radius):
    actions = tuple((tuple(map(float, point)), str(color))
                    for point, color in actions)
    finals = {}
    valid_orders = 0

    def visit(state, remaining):
        nonlocal valid_orders
        if not remaining:
            valid_orders += 1
            finals.setdefault(_state_key(state), state)
            return
        descriptors = _descriptors(
            state.positions, state.species, state.proposals,
            UPSTREAM_ANGULAR_BIN_WIDTH)
        by_key = {}
        for point in state.proposals.votes:
            by_key.setdefault(_point_key(point), []).append(point)
        for index, (stored_point, color) in enumerate(remaining):
            matches = tuple(point for point in by_key.get(
                _point_key(stored_point), ()) if str(_dominant_source_color(
                    state.proposals, point)) == color)
            if len(matches) != 1:
                continue
            point = matches[0]
            child = _child(
                source, runtime["connection"], runtime["state_model"],
                state, point, descriptors[point], radius)
            visit(child, remaining[:index] + remaining[index + 1:])

    visit(_initial_state(source, runtime, radius), actions)
    if valid_orders < 1 or len(finals) != 1:
        raise AssertionError(
            "frozen unordered actions did not replay to one colored state")
    return next(iter(finals.values())), valid_orders


def _channel_diverse_points(state, runtime):
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    if len(descriptors) <= THIRD_ACTION_BUDGET:
        return tuple(sorted(descriptors)), descriptors
    selected = select_pose_port_channel_diverse(
        runtime["state_model"], descriptors,
        budget=THIRD_ACTION_BUDGET,
        baseline_slots=THIRD_BASELINE_SLOTS,
        votes=state.proposals.votes,
        tie_keys={point: point for point in descriptors})
    return selected, descriptors


def _channel_tree(source, runtime, radius, telemetry=None,
                  use_geometry_cache=True):
    states = (_initial_state(source, runtime, radius),)
    counts = []
    geometry_cache = {} if use_geometry_cache else None
    cache_hits = cache_misses = 0
    for _depth in range(THIRD_DEPTH):
        children = {}
        for state in states:
            points, descriptors = _channel_diverse_points(state, runtime)
            for point in points:
                color = str(_dominant_source_color(state.proposals, point))
                geometry_key = action_key(
                    state.actions + ((tuple(point), color),))
                if geometry_cache is not None and geometry_key in geometry_cache:
                    cache_hits += 1
                else:
                    cache_misses += 1
                child = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], radius,
                    geometry_cache=geometry_cache)
                key = action_key(child.actions)
                prior = children.get(key)
                if prior is None or (child.cumulative, child.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = child
        states = tuple(sorted(children.values(),
                              key=lambda row: action_key(row.actions)))
        counts.append(len(states))
    if telemetry is not None:
        telemetry.update({
            "geometry_cache_hits": cache_hits,
            "geometry_cache_misses": cache_misses,
            "naive_geometry_expansions": cache_hits + cache_misses,
            "saved_geometry_expansions": cache_hits,
            "unique_geometry_expansions": cache_misses,
        })
    return states, tuple(counts)


def freeze_three_block_channel_execution(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        ) -> FrozenThreeBlockChannelExecution:
    """Freeze a committed nine-action lineage portfolio without a target."""
    if (len(seed_positions) != len(seed_species) or not seed_positions or
            min(first_radius, second_radius, third_radius) <= 0 or
            not first_radius < second_radius < third_radius):
        raise ValueError("invalid seed or public radius schedule")
    center = tuple(map(float, center))
    seed_positions = tuple(tuple(map(float, point))
                           for point in seed_positions)
    seed_species = tuple(map(str, seed_species))
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=center, seed_positions=seed_positions,
        seed_species=seed_species)

    first = freeze_nucleus(
        runtime, center=center, seed_positions=seed_positions,
        seed_species=seed_species, target_radius=first_radius)
    first_terminal = first.terminals[first.fusion_stable_index]
    first_state, first_orders = _replay_action_set(
        source, runtime, first_terminal.actions, first_radius)
    first_actions = action_key(first_state.actions)

    second_source = SimpleNamespace(
        group=center, seed_positions=first_state.positions,
        seed_species=first_state.species)
    second_states, second_counts = _complete_states_at_radius(
        second_source, runtime, second_radius)
    second_states = tuple(sorted(
        second_states, key=lambda state: action_key(state.actions)))
    rows, retained, second_digest, model_digests = \
        _second_block_candidates(second_source, second_states, runtime)
    traced = tuple({
        "stable_index": int(row["stable_index"]),
        "marking": str(row["marking"]),
        "rollback_score": _trace_score(
            _rollout(second_source, row["state"], runtime)),
    } for row in retained)
    selected = min(traced, key=lambda row: (
        -row["rollback_score"], row["stable_index"]))
    second_state = second_states[selected["stable_index"]]
    second_actions = action_key(second_state.actions)

    third_source = SimpleNamespace(
        group=center, seed_positions=second_state.positions,
        seed_species=second_state.species)
    third_states, third_counts = _channel_tree(
        third_source, runtime, third_radius)
    terminals = tuple(FrozenThreeBlockTerminal(
        stable_index, action_key(state.actions),
        first_actions + second_actions + action_key(state.actions))
        for stable_index, state in enumerate(third_states))
    candidate_digest = hashlib.sha256(repr(tuple(
        terminal.all_actions for terminal in terminals)).encode()).hexdigest()
    retained_receipt = tuple((
        row["stable_index"], row["marking"], row["rollback_score"])
        for row in traced)
    model_receipt = tuple(sorted((str(key), str(value))
                                 for key, value in model_digests.items()))
    payload = (
        center, len(seed_positions), (first_radius, second_radius, third_radius),
        first.candidate_counts_by_depth, first.candidate_digest,
        first.fusion_stable_index, first_actions, first_orders,
        second_counts, len(rows), second_digest, model_receipt,
        retained_receipt, selected["stable_index"], second_actions,
        third_counts, terminals, candidate_digest)
    return FrozenThreeBlockChannelExecution(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius),
        tuple(first.candidate_counts_by_depth), first.candidate_digest,
        int(first.fusion_stable_index), first_actions, first_orders,
        tuple(second_counts), len(rows), second_digest, model_receipt,
        retained_receipt, int(selected["stable_index"]), second_actions,
        third_counts, terminals, candidate_digest,
        hashlib.sha256(repr(payload).encode()).hexdigest())


__all__ = [
    "FrozenThreeBlockChannelExecution", "FrozenThreeBlockTerminal",
    "freeze_three_block_channel_execution"]
