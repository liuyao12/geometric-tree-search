#!/usr/bin/env python3
"""Target-free first-parent supply from a certified commuting closure."""

from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from materials_gcts_iqc_commuting_closure_marking import \
    select_commuting_closure_marking
from materials_gcts_iqc_commuting_frontier_closure import \
    complete_first_frontier_with_commuting_closure
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_iqc_three_block_portfolio_execution import (
    _prepare_pool, _second_worker)


@dataclass(frozen=True)
class FrozenCommutingSecondFrontier:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float]
    marking_model_digest: str
    closure_candidate_digest: str
    selected_first_indices: tuple[int, ...]
    selected_first_actions: tuple[tuple, ...]
    second_branches: tuple
    selection_digest: str
    execution_digest: str
    candidate_geometry_unchanged: bool = True
    target_used: bool = False


def freeze_commuting_second_frontier(
        *, center, seed_positions, seed_species, first_radius, second_radius,
        marking_model, workers=4, parent_width=8, action_count=3,
        initial_action_width=8):
    """Select commuting first parents, then enumerate exact second branches."""
    center = tuple(map(float, center))
    positions = tuple(tuple(map(float, point)) for point in seed_positions)
    species = tuple(map(str, seed_species))
    if (not positions or len(positions) != len(species) or
            workers < 1 or parent_width < 1 or
            not 0 < first_radius < second_radius or
            marking_model.target_used):
        raise ValueError("invalid commuting second-frontier request")
    runtime = load_default_runtime()
    if (tuple(marking_model.feature_names) !=
            tuple(runtime["fusion_model"].feature_names) or
            tuple(marking_model.color_keys) !=
            tuple(runtime["fusion_model"].color_keys)):
        raise ValueError("commuting marking schema does not match runtime")
    frontier = complete_first_frontier_with_commuting_closure(
        center=center, seed_positions=positions, seed_species=species,
        radius=float(first_radius), runtime=runtime,
        action_count=action_count,
        initial_action_width=initial_action_width,
        maximum_action_universe=initial_action_width)
    selection = select_commuting_closure_marking(
        marking_model, frontier, width=parent_width)
    if len(selection.selected_indices) != parent_width:
        raise AssertionError("commuting closure did not supply parent width")
    selected_states = tuple(frontier.states[index]
                            for index in selection.selected_indices)
    selected_actions = tuple(action_key(state.actions)
                             for state in selected_states)
    tasks = tuple((
        center, rank, stable, state.positions, state.species, state.actions,
        float(second_radius))
        for rank, (stable, state) in enumerate(zip(
            selection.selected_indices, selected_states), 1))
    if workers == 1:
        branches = tuple(_second_worker(task) for task in tasks)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            branches = tuple(pool.map(_second_worker, tasks))
    branches = tuple(sorted(branches, key=lambda row: row.first_rank))
    if (len(branches) != parent_width or
            tuple(row.first_actions for row in branches) != selected_actions):
        raise AssertionError("commuting parent identity changed downstream")
    selection_payload = (
        marking_model.model_digest, selection.candidate_digest,
        selection.selected_indices, selected_actions)
    selection_digest = hashlib.sha256(
        repr(selection_payload).encode()).hexdigest()
    execution_payload = (
        center, len(positions), (float(first_radius), float(second_radius)),
        selection_payload, branches, False)
    execution_digest = hashlib.sha256(
        repr(execution_payload).encode()).hexdigest()
    return FrozenCommutingSecondFrontier(
        center, len(positions), (float(first_radius), float(second_radius)),
        marking_model.model_digest, selection.candidate_digest,
        selection.selected_indices, selected_actions, branches,
        selection_digest, execution_digest, True, False)


__all__ = [
    "FrozenCommutingSecondFrontier", "freeze_commuting_second_frontier"]
