#!/usr/bin/env python3
"""Target-blind, compute-bounded IQC three-block tree execution.

All eight first-block parents and every complete second-block action remain in
the immutable receipt.  Expensive third-frontier subtrees are materialized
only for a frozen two-tier schedule: one joint-action choice and five base
fallback choices per parent.  Deferred prefixes are hashed but never scored,
fitted, or expanded.  This is a strict tree search; the lazy presentation is a
bounded antichain of independent parent branches.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_iqc_three_block_complete_parent_execution import (
    COMPLETE_PARENT_WIDTH)
from materials_gcts_iqc_three_block_marking_library_execution import (
    select_marking_library_children)
from materials_gcts_iqc_three_block_portfolio_execution import (
    FIRST_PARENT_WIDTH, FrozenPortfolioLineage, FrozenSecondBranch,
    _complete_first_block, _prepare_pool, _second_worker,
    )
from materials_gcts_iqc_three_block_channel_execution import (
    _channel_tree, _replay_action_set)
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_joint_child_action_marking import (
    EXPECTED_ARTIFACT_DIGEST as JOINT_MARKING_ARTIFACT_DIGEST,
    EXPECTED_FIXTURE_SHA256 as JOINT_MARKING_FIXTURE_SHA256,
    EXPECTED_MODEL_DIGEST as JOINT_MARKING_MODEL_DIGEST)
from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)


@dataclass(frozen=True)
class FrozenThreeBlockLazyJointExecution:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float, float]
    first_candidate_counts: tuple[int, ...]
    first_candidate_count: int
    first_candidate_digest: str
    first_retained_stable_indices: tuple[int, ...]
    second_branches: tuple[FrozenSecondBranch, ...]
    complete_second_prefixes: int
    complete_prefix_queue_digest: str
    selected_prefix_digest: str
    selected_prefix_rows: tuple[tuple, ...]
    selected_prefix_ids_by_parent: tuple[
        tuple[int, tuple[int, ...]], ...]
    deferred_prefix_count: int
    expanded_prefix_count: int
    prefix_budget: int
    expansion_tier_counts: tuple[tuple[str, int], ...]
    third_worker_tasks: int
    naive_geometry_expansions: int
    unique_geometry_expansions: int
    saved_geometry_expansions: int
    geometry_cache_hits: int
    eager_marking_library_prefix_count: int
    saved_prefix_expansions: int
    joint_marking_fixture_sha256: str
    joint_marking_model_digest: str
    joint_marking_artifact_digest: str
    schedule_artifact_digest: str
    grouped_consumed_supply_groups: int
    grouped_consumed_total_groups: int
    third_candidate_counts: tuple[tuple[int, ...], ...]
    lineages: tuple[FrozenPortfolioLineage, ...]
    candidate_digest: str
    execution_digest: str
    bounded_schedule_gate_passed: bool
    target_used: bool = False


def _lazy_third_parent_worker(payload):
    """Expand scheduled children while sharing unordered-set geometry."""
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
    totals = {
        "naive_geometry_expansions": 0,
        "unique_geometry_expansions": 0,
        "saved_geometry_expansions": 0,
        "geometry_cache_hits": 0,
    }
    for child_stable_index, second_actions in child_rows:
        second, _second_orders = _replay_action_set(
            second_source, runtime, second_actions, second_radius)
        third_source = SimpleNamespace(
            group=tuple(center), seed_positions=second.positions,
            seed_species=second.species)
        telemetry = {}
        states, counts = _channel_tree(
            third_source, runtime, third_radius, telemetry=telemetry,
            use_geometry_cache=True)
        lineages = tuple(FrozenPortfolioLineage(
            int(parent_id), int(child_stable_index), third_stable,
            action_key(first.actions), action_key(second.actions),
            action_key(state.actions), action_key(first.actions) +
            action_key(second.actions) + action_key(state.actions))
            for third_stable, state in enumerate(states))
        results.append((tuple(counts), lineages))
        for key in totals:
            totals[key] += int(telemetry[key])
    return tuple(results), tuple(sorted(totals.items()))


def freeze_three_block_lazy_joint_execution(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        workers: int = 4) -> FrozenThreeBlockLazyJointExecution:
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
    first_states = tuple((rank, stable_index,
                          first_states_all[stable_index])
                         for rank, stable_index in enumerate(
                             retained_first, 1))
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
    if len(branches) != COMPLETE_PARENT_WIDTH:
        raise AssertionError("lazy joint executor lost a first parent")

    schedule, schedule_artifact = load_default_schedule()
    scheduled = schedule_prefixes(
        schedule=schedule, seed_positions=seed_positions,
        seed_species=seed_species, branches=branches)
    selected_rows = scheduled["selected_rows"]
    selected_by_parent = []
    branch_by_parent = {branch.first_rank: branch for branch in branches}
    third_payloads = []
    for parent in range(1, COMPLETE_PARENT_WIDTH + 1):
        child_ids = tuple(row[1] for row in selected_rows
                          if row[0] == parent)
        if not child_ids:
            raise AssertionError("lazy schedule starved a retained parent")
        branch = branch_by_parent[parent]
        selected_by_parent.append((parent, child_ids))
        third_payloads.append((
            center, seed_positions, seed_species, branch.first_actions,
            tuple((child, branch.second_actions[child])
                  for child in child_ids), parent, first_radius,
            second_radius, third_radius))
    if workers == 1:
        worker_rows = tuple(_lazy_third_parent_worker(payload)
                             for payload in third_payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            worker_rows = tuple(pool.map(
                _lazy_third_parent_worker, third_payloads))
    third_groups = tuple(row[0] for row in worker_rows)
    telemetry_rows = tuple(dict(row[1]) for row in worker_rows)
    third = tuple(row for group in third_groups for row in group)
    third_counts = tuple(row[0] for row in third)
    lineages = tuple(lineage for _counts, rows in third for lineage in rows)
    candidate_digest = hashlib.sha256(repr(tuple(
        lineage.all_actions for lineage in lineages)).encode()).hexdigest()
    geometry_totals = {key: sum(row[key] for row in telemetry_rows)
                       for key in ("naive_geometry_expansions",
                                   "unique_geometry_expansions",
                                   "saved_geometry_expansions",
                                   "geometry_cache_hits")}

    # This old selection is evaluated only to count the previous eager work;
    # it does not authorize or rank a lazy prefix.
    eager = select_marking_library_children(
        branches=branches, seed_positions=seed_positions,
        seed_species=seed_species)
    eager_count = sum(len(children) for _parent, children
                      in eager["union_rows"])
    expanded = len(selected_rows)
    complete = sum(len(branch.second_actions) for branch in branches)
    selected_audit = schedule_artifact["selected"]
    bounded_gate = bool(
        expanded <= schedule.maximum_prefixes and
        expanded < eager_count and
        selected_audit["supplied_exact_child_groups"] ==
        selected_audit["total_exact_child_groups"] and
        not schedule.target_used_for_execution and
        not scheduled["model"].target_used_for_scoring)
    payload = (
        center, len(seed_positions),
        (first_radius, second_radius, third_radius), first_counts,
        len(first_states_all), first_digest, retained_first, branches,
        complete, scheduled["complete_queue_digest"],
        scheduled["selected_prefix_digest"], selected_rows,
        tuple(selected_by_parent), len(scheduled["deferred_rows"]),
        expanded, schedule.maximum_prefixes, scheduled["tier_counts"],
        len(third_payloads), geometry_totals["naive_geometry_expansions"],
        geometry_totals["unique_geometry_expansions"],
        geometry_totals["saved_geometry_expansions"],
        geometry_totals["geometry_cache_hits"], eager_count,
        eager_count - expanded,
        JOINT_MARKING_FIXTURE_SHA256, JOINT_MARKING_MODEL_DIGEST,
        JOINT_MARKING_ARTIFACT_DIGEST, schedule.artifact_digest,
        selected_audit["supplied_exact_child_groups"],
        selected_audit["total_exact_child_groups"], third_counts, lineages,
        candidate_digest, bounded_gate)
    return FrozenThreeBlockLazyJointExecution(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius), first_counts,
        len(first_states_all), first_digest, retained_first, branches,
        complete, scheduled["complete_queue_digest"],
        scheduled["selected_prefix_digest"], selected_rows,
        tuple(selected_by_parent), len(scheduled["deferred_rows"]),
        expanded, schedule.maximum_prefixes, scheduled["tier_counts"],
        len(third_payloads), geometry_totals["naive_geometry_expansions"],
        geometry_totals["unique_geometry_expansions"],
        geometry_totals["saved_geometry_expansions"],
        geometry_totals["geometry_cache_hits"], eager_count,
        eager_count - expanded,
        JOINT_MARKING_FIXTURE_SHA256, JOINT_MARKING_MODEL_DIGEST,
        JOINT_MARKING_ARTIFACT_DIGEST, schedule.artifact_digest,
        selected_audit["supplied_exact_child_groups"],
        selected_audit["total_exact_child_groups"], third_counts, lineages,
        candidate_digest, hashlib.sha256(repr(payload).encode()).hexdigest(),
        bounded_gate)


__all__ = [
    "FrozenThreeBlockLazyJointExecution",
    "freeze_three_block_lazy_joint_execution"]
