#!/usr/bin/env python3
"""Target-free tree search driven by the frozen stage-local IQC marking."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from types import SimpleNamespace

from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, _local_section, action_key, branch_features)
from materials_gcts_iqc_frozen_stage_local_prefix_marking import (
    FrozenStageLocalPrefixMarking, score_depth_model)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
    _frontier_summary)
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_stage_local_prefix_dataset import _seed_frontier
from materials_gcts_pose_port_state_marking import score_pose_port_state


@dataclass(frozen=True)
class StageLocalPrefixSearchResult:
    center: tuple[float, float, float]
    seed_atoms: int
    candidate_counts_by_depth: tuple[int, ...]
    retained_counts_by_depth: tuple[int, ...]
    retained_action_keys_by_depth: tuple[tuple, ...]
    final_states: tuple[FusionSearchState, ...]
    model_digest: str
    geometry_digest: str
    target_api_present: bool = False
    target_used: bool = False


def state_features(state):
    return tuple(branch_features(state)) + tuple(_local_section(state)) + \
        tuple(map(float, _frontier_summary(state.proposals)))


def _execute_prefix_search(
        runtime, *, center, seed_positions, seed_species, public_radius,
        candidate_reach, retained_budget, score_state, model_digest):
    source = SimpleNamespace(
        group=tuple(map(float, center)),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed_positions),
        seed_species=tuple(map(str, seed_species)))
    frontier = _seed_frontier(runtime, source, public_radius)
    states = (FusionSearchState(
        source.seed_positions, source.seed_species, frontier,
        (), (), (), 0., ()),)
    counts, retained, keys = [], [], []
    for depth, (reach, budget) in enumerate(zip(
            candidate_reach, retained_budget), start=1):
        children = {}
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(
                    runtime["state_model"], descriptors[point]),
                -state.proposals.votes[point], point)))[:reach]
            for point in ordered:
                candidate = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], public_radius)
                key = action_key(candidate.actions)
                prior = children.get(key)
                if prior is None or \
                        (candidate.cumulative, candidate.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = candidate
        stage = tuple(children.values())
        scored = tuple(sorted(stage, key=lambda candidate: (
            -score_state(depth, candidate),
            repr(action_key(candidate.actions)))))
        states = scored[:budget]
        counts.append(len(stage))
        retained.append(len(states))
        keys.append(tuple(action_key(state.actions) for state in states))
    geometry = tuple((counts, retained, keys))
    return StageLocalPrefixSearchResult(
        source.group, len(source.seed_positions), tuple(counts),
        tuple(retained), tuple(keys), states, model_digest,
        hashlib.sha256(repr(geometry).encode()).hexdigest())


def execute_stage_local_prefix_search(
        runtime, model: FrozenStageLocalPrefixMarking, *, center,
        seed_positions, seed_species, public_radius):
    if model.fresh_confirmation_target_used or model.candidate_geometry_authorized:
        raise ValueError("stage-local model is not a rank-only frozen artifact")
    depth_models = {row.depth: row for row in model.depth_models}
    if tuple(sorted(depth_models)) != tuple(
            range(1, len(model.depth_models) + 1)):
        raise AssertionError("frozen depth-model order drift")
    return _execute_prefix_search(
        runtime, center=center, seed_positions=seed_positions,
        seed_species=seed_species, public_radius=public_radius,
        candidate_reach=model.candidate_reach,
        retained_budget=model.retained_prefix_budget,
        score_state=lambda depth, state: score_depth_model(
            depth_models[depth], state_features(state)),
        model_digest=model.model_digest)


def execute_pose_port_prefix_baseline(
        runtime, *, center, seed_positions, seed_species, public_radius,
        candidate_reach=(12, 4, 8), retained_budget=(2, 4, 1)):
    """Matched-work baseline using only cumulative pose/port probability."""
    return _execute_prefix_search(
        runtime, center=center, seed_positions=seed_positions,
        seed_species=seed_species, public_radius=public_radius,
        candidate_reach=tuple(candidate_reach),
        retained_budget=tuple(retained_budget),
        score_state=lambda _depth, state: state.cumulative,
        model_digest="pose-port-cumulative-baseline")
