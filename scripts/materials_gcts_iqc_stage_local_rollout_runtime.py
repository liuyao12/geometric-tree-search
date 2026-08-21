#!/usr/bin/env python3
"""Target-free stage-local IQC terminal portfolio and rollout ranking."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, action_key)
from materials_gcts_iqc_frozen_stage_local_margin_marking import (
    FrozenStageLocalPrefixMarking)
from materials_gcts_iqc_frozen_stage_local_prefix_marking import (
    score_depth_model)
from materials_gcts_iqc_frozen_stage_local_rollout_value import (
    FrozenStageLocalRolloutValue, score_rollout)
from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_stage_local_prefix_runtime import (
    _execute_prefix_search, state_features)
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout


TERMINAL_PORTFOLIO_BUDGET = (4, 8, 8)


@dataclass(frozen=True)
class StageLocalRolloutCandidate:
    action_key: tuple
    rollout_score: float
    trace_digest: str
    transition_digest: str
    state: FusionSearchState


@dataclass(frozen=True)
class StageLocalRolloutSearchResult:
    center: tuple[float, float, float]
    seed_atoms: int
    candidate_counts_by_depth: tuple[int, ...]
    retained_counts_by_depth: tuple[int, ...]
    candidates: tuple[StageLocalRolloutCandidate, ...]
    selected_index: int
    selected_state: FusionSearchState
    candidate_digest: str
    prefix_model_digest: str
    rollout_model_digest: str
    target_api_present: bool = False
    target_used: bool = False


def execute_stage_local_rollout_search(
        runtime, prefix_model: FrozenStageLocalPrefixMarking,
        rollout_model: FrozenStageLocalRolloutValue, *, center,
        seed_positions, seed_species, public_radius):
    if prefix_model.fresh_confirmation_target_used or \
            prefix_model.candidate_geometry_authorized or rollout_model.target_used:
        raise ValueError("target-tainted stage-local model")
    depth_models = {row.depth: row for row in prefix_model.depth_models}
    prefix = _execute_prefix_search(
        runtime, center=center, seed_positions=seed_positions,
        seed_species=seed_species, public_radius=public_radius,
        candidate_reach=prefix_model.candidate_reach,
        retained_budget=TERMINAL_PORTFOLIO_BUDGET,
        score_state=lambda depth, state: score_depth_model(
            depth_models[depth], state_features(state)),
        model_digest=prefix_model.model_digest)
    source = SimpleNamespace(
        group=tuple(map(float, center)),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed_positions),
        seed_species=tuple(map(str, seed_species)))
    candidates = []
    for state in prefix.final_states:
        trace, transitions = _rollout(
            source, state, runtime, relational=True)
        if trace["target_used"] or len(transitions) > 16:
            raise AssertionError("invalid target-free stage-local rollout")
        candidates.append(StageLocalRolloutCandidate(
            action_key(state.actions),
            score_rollout(rollout_model, transitions, trace),
            _digest(trace), _digest(tuple(transitions)), state))
    if not candidates:
        raise AssertionError("stage-local terminal portfolio is empty")
    selected = min(range(len(candidates)), key=lambda index: (
        -candidates[index].rollout_score,
        repr(candidates[index].action_key)))
    digest = _digest(tuple((
        row.action_key, row.trace_digest, row.transition_digest)
                          for row in candidates))
    return StageLocalRolloutSearchResult(
        tuple(map(float, center)), len(seed_positions),
        prefix.candidate_counts_by_depth, prefix.retained_counts_by_depth,
        tuple(candidates), selected, candidates[selected].state, digest,
        prefix_model.model_digest, rollout_model.model_digest)


def execute_self_fed_rollout_blocks(
        runtime, prefix_model, rollout_model, *, center, seed_positions,
        seed_species, public_radius, blocks):
    positions, species, results = tuple(seed_positions), tuple(seed_species), []
    for _block in range(blocks):
        result = execute_stage_local_rollout_search(
            runtime, prefix_model, rollout_model, center=center,
            seed_positions=positions, seed_species=species,
            public_radius=public_radius)
        selected = result.selected_state
        if len(selected.positions) != len(positions) + 3:
            raise AssertionError("one stage-local block must emit three sites")
        results.append(result)
        positions, species = selected.positions, selected.species
    return tuple(results), positions, species
