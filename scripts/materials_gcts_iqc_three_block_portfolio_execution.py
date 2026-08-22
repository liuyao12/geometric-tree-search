#!/usr/bin/env python3
"""Target-free three-block clusters-squared IQC portfolio execution.

The complete first block is ranked by the frozen fusion value and retains the
top eight parents.  Every parent is self-fed independently into the complete
second block.  Four frozen recurrent marking heads value each first parent by
its best eight second-block options; a channel-diverse width-four parent beam
and its immutable child portfolios are retained.  Every retained six-action
lineage then receives the compute-matched pose/port channel-diverse third
block.

This is a strict tree search over exact frozen candidate geometry.  It accepts
no target, scorer, oracle, family label, lattice coordinate, or expected
action.  A later one-shot scorer may distinguish complete-tree supply,
bounded-portfolio supply, and winner quality without changing this receipt.
"""

from __future__ import annotations

import concurrent.futures.process as process
import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_clusters2_future_option import (
    ChildOption, FrozenFutureOptionSpec, ParentOption,
    select_future_options)
from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, select_equivariant_port_fusion)
from materials_gcts_iqc_frozen_fusion_runtime import (
    BRANCH_VARIANTS, _local_section, _partial, action_key, branch_features,
    load_default_runtime)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_three_block_channel_execution import (
    _channel_tree, _replay_action_set)
from materials_gcts_recurrent_branch_value import score_recurrent_branch


FIRST_PARENT_WIDTH = 8
SECOND_OPTION_TOP_K = 8
SECOND_PARENT_WIDTH = 4
CHANNEL_NAMES = tuple(BRANCH_VARIANTS)
OPTION_SPEC = FrozenFutureOptionSpec(
    CHANNEL_NAMES, top_k=SECOND_OPTION_TOP_K,
    beam_width=SECOND_PARENT_WIDTH)


@dataclass(frozen=True)
class FrozenSecondBranch:
    first_rank: int
    first_stable_index: int
    first_actions: tuple[tuple, ...]
    second_candidate_counts: tuple[int, ...]
    second_actions: tuple[tuple[tuple, ...], ...]
    second_channel_scores: tuple[tuple[float, ...], ...]
    child_score_digest: str
    target_used: bool = False


@dataclass(frozen=True)
class FrozenPortfolioLineage:
    parent_id: int
    child_stable_index: int
    third_stable_index: int
    first_actions: tuple[tuple, ...]
    second_actions: tuple[tuple, ...]
    third_actions: tuple[tuple, ...]
    all_actions: tuple[tuple, ...]


@dataclass(frozen=True)
class FrozenThreeBlockPortfolioExecution:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float, float]
    first_candidate_counts: tuple[int, ...]
    first_candidate_count: int
    first_candidate_digest: str
    first_retained_stable_indices: tuple[int, ...]
    second_branches: tuple[FrozenSecondBranch, ...]
    option_candidate_digest: str
    selected_parent_ids: tuple[int, ...]
    selected_by_channels: tuple[tuple[str, int], ...]
    selected_child_ids_by_parent: tuple[
        tuple[int, tuple[tuple[int, int], ...]], ...]
    third_candidate_counts: tuple[tuple[int, ...], ...]
    lineages: tuple[FrozenPortfolioLineage, ...]
    candidate_digest: str
    execution_digest: str
    target_used: bool = False


def _prepare_pool():
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def _complete_first_block(center, seed_positions, seed_species, radius,
                          runtime):
    """Reproduce the sealed deferred-pruning stable-index tie contract."""
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    states, counts = _complete_states_at_radius(source, runtime, radius)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
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
    return states, tuple(counts), order, digest


def _second_worker(payload):
    (center, first_rank, first_stable_index, first_positions,
     first_species, first_actions, second_radius) = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(first_positions),
        seed_species=tuple(first_species))
    states, counts = _complete_states_at_radius(
        source, runtime, second_radius)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    action_rows = tuple(action_key(state.actions) for state in states)
    score_rows = []
    for state in states:
        full = branch_features(state)
        colors = tuple(color for _point, color in state.actions)
        score_rows.append(tuple(score_recurrent_branch(
            runtime["branch_models"][name][2],
            tuple(full[index] for index in BRANCH_VARIANTS[name]), colors)
            for name in CHANNEL_NAMES))
    score_rows = tuple(score_rows)
    digest = hashlib.sha256(repr(tuple(zip(
        action_rows, score_rows))).encode()).hexdigest()
    return FrozenSecondBranch(
        int(first_rank), int(first_stable_index), action_key(first_actions),
        tuple(counts), action_rows, score_rows, digest)


def _third_parent_worker(payload):
    (center, seed_positions, seed_species, first_actions, child_rows,
     parent_id, first_radius, second_radius, third_radius) = payload
    runtime = load_default_runtime()
    original = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    first, _first_orders = _replay_action_set(
        original, runtime, first_actions, first_radius)
    second_source = SimpleNamespace(
        group=tuple(center), seed_positions=first.positions,
        seed_species=first.species)
    results = []
    for child_stable_index, second_actions in child_rows:
        second, _second_orders = _replay_action_set(
            second_source, runtime, second_actions, second_radius)
        third_source = SimpleNamespace(
            group=tuple(center), seed_positions=second.positions,
            seed_species=second.species)
        states, counts = _channel_tree(third_source, runtime, third_radius)
        lineages = tuple(FrozenPortfolioLineage(
            int(parent_id), int(child_stable_index), third_stable,
            action_key(first.actions), action_key(second.actions),
            action_key(state.actions), action_key(first.actions) +
            action_key(second.actions) + action_key(state.actions))
            for third_stable, state in enumerate(states))
        results.append((tuple(counts), lineages))
    return tuple(results)


def freeze_three_block_portfolio_execution(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        workers: int = 4) -> FrozenThreeBlockPortfolioExecution:
    """Freeze the bounded clusters-squared lineage portfolio target-free."""
    if (len(seed_positions) != len(seed_species) or not seed_positions or
            min(first_radius, second_radius, third_radius) <= 0 or
            not first_radius < second_radius < third_radius or workers < 1):
        raise ValueError("invalid seed, radius schedule, or worker count")
    center = tuple(map(float, center))
    seed_positions = tuple(tuple(map(float, point))
                           for point in seed_positions)
    seed_species = tuple(map(str, seed_species))
    runtime = load_default_runtime()
    first_states_all, first_counts, first_order, first_digest = \
        _complete_first_block(
            center, seed_positions, seed_species, first_radius, runtime)
    retained_first = tuple(first_order[:min(
        FIRST_PARENT_WIDTH, len(first_states_all))])
    first_states = []
    for rank, stable_index in enumerate(retained_first, 1):
        state = first_states_all[stable_index]
        first_states.append((rank, stable_index, state))
    second_payloads = tuple((
        center, rank, stable, state.positions, state.species, state.actions,
        second_radius) for rank, stable, state in first_states)
    if workers == 1:
        branches = tuple(_second_worker(payload)
                         for payload in second_payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            branches = tuple(pool.map(_second_worker, second_payloads))
    branches = tuple(sorted(branches, key=lambda row: row.first_rank))
    parents = tuple(ParentOption(
        branch.first_rank, tuple(ChildOption(
            (branch.first_rank, stable_index), scores)
            for stable_index, scores in enumerate(
                branch.second_channel_scores))) for branch in branches)
    selection = select_future_options(parents, OPTION_SPEC)
    branch_by_parent = {branch.first_rank: branch for branch in branches}
    third_payloads = []
    child_receipt = []
    for parent_id, child_ids in selection.selected_child_ids_by_parent:
        branch = branch_by_parent[int(parent_id)]
        child_ids = tuple((int(child[0]), int(child[1]))
                          for child in child_ids)
        child_receipt.append((int(parent_id), child_ids))
        child_rows = []
        for child_parent, child_stable in child_ids:
            if child_parent != parent_id:
                raise AssertionError("child option parent identity drift")
            child_rows.append((
                child_stable, branch.second_actions[child_stable]))
        third_payloads.append((
            center, seed_positions, seed_species, branch.first_actions,
            tuple(child_rows), int(parent_id), first_radius, second_radius,
            third_radius))
    if workers == 1:
        third_groups = tuple(_third_parent_worker(payload)
                             for payload in third_payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            third_groups = tuple(pool.map(
                _third_parent_worker, third_payloads))
    third = tuple(row for group in third_groups for row in group)
    third_counts = tuple(row[0] for row in third)
    lineages = tuple(lineage for _counts, rows in third for lineage in rows)
    candidate_digest = hashlib.sha256(repr(tuple(
        lineage.all_actions for lineage in lineages)).encode()).hexdigest()
    child_receipt = tuple(child_receipt)
    selected_by = tuple((str(name), int(parent))
                        for name, parent in selection.selected_by_channels)
    payload = (
        center, len(seed_positions), (first_radius, second_radius, third_radius),
        first_counts, len(first_states_all), first_digest, retained_first,
        branches,
        selection.candidate_digest, selection.selected_parent_ids,
        selected_by, child_receipt, third_counts, lineages, candidate_digest)
    return FrozenThreeBlockPortfolioExecution(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius),
        first_counts, len(first_states_all), first_digest, retained_first,
        branches,
        selection.candidate_digest,
        tuple(map(int, selection.selected_parent_ids)), selected_by,
        child_receipt, third_counts, lineages, candidate_digest,
        hashlib.sha256(repr(payload).encode()).hexdigest())


__all__ = [
    "FrozenPortfolioLineage", "FrozenSecondBranch",
    "FrozenThreeBlockPortfolioExecution",
    "freeze_three_block_portfolio_execution"]
