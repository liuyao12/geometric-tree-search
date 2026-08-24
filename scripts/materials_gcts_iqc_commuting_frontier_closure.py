#!/usr/bin/env python3
"""Target-free antichain closure of witnessed IQC frontier actions."""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, select_equivariant_port_fusion)
from materials_gcts_iqc_frozen_fusion_runtime import (
    _local_section, _partial, action_key, branch_features)
from materials_gcts_iqc_self_fed_complete_frontier_execution import \
    _complete_states_at_radius
from materials_gcts_frontier_attachment_benchmark import \
    _dominant_source_color
from materials_gcts_iqc_frozen_fusion_runtime import _child
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import \
    UPSTREAM_ANGULAR_BIN_WIDTH
from materials_gcts_iqc_three_block_channel_execution import (
    _channel_diverse_points, _initial_state, _point_key, _state_key)


@dataclass(frozen=True)
class FrozenCommutingFrontierClosure:
    action_count: int
    witnessed_states: int
    witnessed_action_universe: tuple
    combinations_checked: int
    replayable_combinations: int
    all_permutations_combinations: int
    states: tuple
    state_digest: str
    target_used: bool = False


@dataclass(frozen=True)
class FrozenCommutingFirstFrontier:
    states: tuple
    candidates: tuple
    legacy_fusion_scores: tuple[float, ...]
    base_candidate_counts: tuple[int, ...]
    base_states: int
    closure_states: int
    order: tuple[int, ...]
    candidate_digest: str
    closure: FrozenCommutingFrontierClosure
    target_used: bool = False


def commuting_frontier_closure(
        *, source, runtime, witnessed_states, radius,
        witnessed_actions=None, action_count=3,
        maximum_action_universe=32):
    """Replay every witnessed action subset and retain strict antichains.

    A retained set must replay to one identical colored state under *every*
    permutation.  The closure therefore adds no invented geometry and encodes
    exactly the simultaneous/permutable moves requested by the growth UI.
    """
    if (not isinstance(action_count, int) or action_count < 1 or
            not isinstance(maximum_action_universe, int) or
            maximum_action_universe < action_count or not witnessed_states):
        raise ValueError("invalid commuting-frontier closure request")
    actions = (tuple(sorted({action for state in witnessed_states
                             for action in action_key(state.actions)}))
               if witnessed_actions is None else
               tuple(sorted(set(witnessed_actions))))
    if len(actions) > maximum_action_universe:
        raise ValueError("witnessed action universe exceeds frozen bound")
    # Exact subset dynamic program.  A subset is retained only if every valid
    # predecessor reaches the same colored state.  Each prefix is materialized
    # once, instead of replaying it separately inside every full permutation.
    subset_states = {(): (_initial_state(source, runtime, radius), 1)}
    geometry_cache = {}
    cluster_type_cache = {}
    prototype_mapping_cache = {}
    replayable = full = 0
    states = {}
    checked = math.comb(len(actions), action_count)
    required_orders = math.factorial(action_count)
    for size in range(1, action_count + 1):
        for subset in itertools.combinations(range(len(actions)), size):
            children = []
            valid_orders = 0
            for last in subset:
                prior = tuple(index for index in subset if index != last)
                prior_row = subset_states.get(prior)
                if prior_row is None:
                    continue
                child = _extend_witnessed_action(
                    source, runtime, prior_row[0], actions[last], radius,
                    geometry_cache=geometry_cache,
                    cluster_type_cache=cluster_type_cache,
                    prototype_mapping_cache=prototype_mapping_cache)
                if child is None:
                    continue
                children.append(child)
                valid_orders += prior_row[1]
            if not children or len({_state_key(row) for row in children}) != 1:
                continue
            subset_states[subset] = (children[0], valid_orders)
            if size != action_count:
                continue
            replayable += 1
            if valid_orders != required_orders:
                continue
            full += 1
            states[action_key(children[0].actions)] = children[0]
    ordered = tuple(states[key] for key in sorted(states))
    digest = hashlib.sha256(repr(tuple(
        action_key(state.actions) for state in ordered)).encode()).hexdigest()
    return FrozenCommutingFrontierClosure(
        action_count, len(witnessed_states), actions, checked, replayable,
        full, ordered, digest, False)


def _extend_witnessed_action(
        source, runtime, state, action, radius, *, geometry_cache=None,
        cluster_type_cache=None, prototype_mapping_cache=None):
    stored_point, color = action
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    matches = tuple(point for point in state.proposals.votes
                    if _point_key(point) == _point_key(stored_point) and
                    str(_dominant_source_color(state.proposals, point)) ==
                    str(color))
    if len(matches) != 1:
        return None
    point = matches[0]
    return _child(
        source, runtime["connection"], runtime["state_model"], state, point,
        descriptors[point], radius, geometry_cache=geometry_cache,
        cluster_type_cache=cluster_type_cache,
        prototype_mapping_cache=prototype_mapping_cache)


def complete_first_frontier_with_commuting_closure(
        *, center, seed_positions, seed_species, radius, runtime,
        action_count=3, initial_action_width=8,
        maximum_action_universe=32):
    """Rank the union of the bounded tree and its certified antichain closure."""
    source = SimpleNamespace(
        group=tuple(map(float, center)),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed_positions),
        seed_species=tuple(map(str, seed_species)))
    base, counts = _complete_states_at_radius(source, runtime, radius)
    base = tuple(sorted(base, key=lambda state: action_key(state.actions)))
    initial = _initial_state(source, runtime, radius)
    points, _descriptors_by_point, _scores, _codes = \
        _channel_diverse_points(
            initial, runtime, action_budget=initial_action_width,
            baseline_slots=min(3, initial_action_width))
    witnessed_actions = tuple((
        tuple(point), str(_dominant_source_color(initial.proposals, point)))
        for point in points)
    closure = commuting_frontier_closure(
        source=source, runtime=runtime, witnessed_states=base, radius=radius,
        witnessed_actions=witnessed_actions,
        action_count=action_count,
        maximum_action_universe=maximum_action_universe)
    by_action = {action_key(state.actions): state for state in base}
    for state in closure.states:
        by_action.setdefault(action_key(state.actions), state)
    states = tuple(by_action[key] for key in sorted(by_action))
    candidates = []
    for stable_index, state in enumerate(states):
        partial, graph = _partial(
            source, state, runtime["grouped_vocabulary"])
        features = tuple(branch_features(state)) + _local_section(state) + \
            partial
        candidates.append(EquivariantPortFusionCandidate(
            features, tuple(color for _point, color in state.actions), graph,
            stable_index))
    selection = select_equivariant_port_fusion(
        runtime["fusion_model"], tuple(candidates))
    order = tuple(sorted(range(len(states)), key=lambda index: (
        -selection.fused_scores[index], index)))
    digest = hashlib.sha256(repr(tuple(
        (action_key(state.actions), selection.fused_scores[index])
        for index, state in enumerate(states))).encode()).hexdigest()
    return FrozenCommutingFirstFrontier(
        states, tuple(candidates), tuple(selection.fused_scores),
        tuple(counts), len(base), len(closure.states), order, digest, closure,
        False)


__all__ = [
    "FrozenCommutingFirstFrontier", "FrozenCommutingFrontierClosure",
    "commuting_frontier_closure",
    "complete_first_frontier_with_commuting_closure"]
