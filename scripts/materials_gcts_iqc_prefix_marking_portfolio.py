#!/usr/bin/env python3
"""Prefix-level IQC tree that preserves two frozen marking views.

The existing stage-local executor prunes each three-action block with one
learned section score.  This adapter instead gives the learned section and the
older pose/port connection score the same immutable candidate geometry.  A
parent-balanced 4→8→8 beam prevents one partial configuration from erasing all
children of another.  It remains target-free and changes no physical proposal.
"""

from __future__ import annotations

from types import SimpleNamespace

from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, action_key)
from materials_gcts_iqc_frozen_stage_local_prefix_marking import (
    score_depth_model)
from materials_gcts_iqc_frozen_stage_local_rollout_value import score_rollout
from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_stage_local_prefix_dataset import _seed_frontier
from materials_gcts_iqc_stage_local_prefix_runtime import state_features
from materials_gcts_iqc_stage_local_rollout_runtime import (
    StageLocalRolloutCandidate, StageLocalRolloutSearchResult)
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout
from materials_gcts_marking_portfolio_tree import (
    FrozenPortfolioAction, search_marking_portfolio)
from materials_gcts_pose_port_state_marking import score_pose_port_state


PREFIX_PORTFOLIO_BUDGET = (4, 8, 8)


def build_stage_local_prefix_portfolio_tree(
        runtime, prefix_model, *, center, seed_positions, seed_species,
        public_radius, candidate_reach=None,
        retained_budget=PREFIX_PORTFOLIO_BUDGET,
        allocation="parent-marking-round-robin"):
    if prefix_model.fresh_confirmation_target_used or \
            prefix_model.candidate_geometry_authorized:
        raise ValueError("target-tainted prefix marking portfolio")
    reach = (tuple(map(int, candidate_reach))
             if candidate_reach is not None
             else tuple(prefix_model.candidate_reach))
    budget = tuple(map(int, retained_budget))
    if len(reach) != len(budget) or any(value < 2 for value in budget):
        raise ValueError("invalid prefix portfolio dimensions")
    depth_models = {row.depth: row for row in prefix_model.depth_models}
    source = SimpleNamespace(
        group=tuple(map(float, center)),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed_positions),
        seed_species=tuple(map(str, seed_species)))
    frontier = _seed_frontier(runtime, source, public_radius)
    seed = FusionSearchState(
        source.seed_positions, source.seed_species, frontier,
        (), (), (), 0., ())

    def expand(state):
        depth = len(state.actions) + 1
        descriptors = _descriptors(
            state.positions, state.species, state.proposals,
            UPSTREAM_ANGULAR_BIN_WIDTH)
        ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
            -score_pose_port_state(runtime["state_model"], descriptors[point]),
            -state.proposals.votes[point], point)))[:reach[depth - 1]]
        children = {}
        for point in ordered:
            child = _child(
                source, runtime["connection"], runtime["state_model"],
                state, point, descriptors[point], public_radius)
            key = action_key(child.actions)
            prior = children.get(key)
            if prior is None or (child.cumulative, child.actions) > \
                    (prior.cumulative, prior.actions):
                children[key] = child
        actions = []
        for key, child in sorted(children.items(), key=lambda row: repr(row[0])):
            model = depth_models[depth]
            features = state_features(child)
            section = tuple(round(((float(features[index]) - mean) / scale) / 2.)
                            for index, mean, scale in zip(
                                model.feature_indices, model.means, model.scales))
            pose_port = tuple(sorted(child.channel_marks))
            actions.append(FrozenPortfolioAction(
                key, child,
                (("section", score_depth_model(
                    model, features)),
                 ("pose-port", float(child.cumulative))),
                (("section", section), ("pose-port", pose_port))))
        return tuple(actions)

    tree = search_marking_portfolio(
        seed, expand=expand, state_key=lambda state: action_key(state.actions),
        marking_names=("section", "pose-port"), depth=len(reach),
        beam_width=max(budget), beam_schedule=budget,
        allocation=allocation, score_aggregation="replace",
        channel_diversity=True)
    return source, tree


def execute_stage_local_prefix_portfolio(
        runtime, prefix_model, rollout_model, *, center, seed_positions,
        seed_species, public_radius, candidate_reach=None,
        retained_budget=PREFIX_PORTFOLIO_BUDGET,
        allocation="parent-marking-round-robin"):
    if rollout_model.target_used:
        raise ValueError("target-tainted prefix marking portfolio")
    source, tree = build_stage_local_prefix_portfolio_tree(
        runtime, prefix_model, center=center, seed_positions=seed_positions,
        seed_species=seed_species, public_radius=public_radius,
        candidate_reach=candidate_reach, retained_budget=retained_budget,
        allocation=allocation)
    reach = (tuple(map(int, candidate_reach))
             if candidate_reach is not None
             else tuple(prefix_model.candidate_reach))
    budget = tuple(map(int, retained_budget))
    candidates = []
    for node in tree.retained:
        state = node.state
        trace, transitions = _rollout(source, state, runtime, relational=True)
        if trace["target_used"] or len(transitions) > 16:
            raise AssertionError("invalid target-free prefix rollout")
        candidates.append(StageLocalRolloutCandidate(
            action_key(state.actions),
            float(score_rollout(rollout_model, transitions, trace)),
            _digest(trace), _digest(tuple(transitions)), state))
    if not candidates:
        raise AssertionError("prefix marking portfolio is empty")
    selected = min(range(len(candidates)), key=lambda index: (
        -candidates[index].rollout_score,
        repr(candidates[index].action_key)))
    digest = _digest(tuple((row.action_key, row.trace_digest,
                            row.transition_digest) for row in candidates))
    model_digest = _digest((prefix_model.model_digest, "prefix-portfolio-v1",
                            reach, budget))
    return StageLocalRolloutSearchResult(
        source.group, len(source.seed_positions),
        tuple(level.candidate_count for level in tree.levels),
        tuple(len(level.retained_state_keys) for level in tree.levels),
        tuple(candidates), selected, candidates[selected].state, digest,
        model_digest, rollout_model.model_digest)
