#!/usr/bin/env python3
"""Full-width IQC execution with one action-marginal fallback per parent."""

from __future__ import annotations

import hashlib
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from materials_gcts_action_marginal_prefix_schedule import \
    select_action_marginal_prefixes
from materials_gcts_iqc_fourth_block_beam import parent_balanced_beam
from materials_gcts_iqc_fourth_block_parent_balanced_policy import \
    PARENT_WIDTH, load_default_result as load_parent_policy
from materials_gcts_iqc_fresh_parent_balanced_execution import (
    FrozenParentBalancedFourthCandidate, _fit_lineage_model,
    _freeze_second_branches, _prepare_pool, _score)
from materials_gcts_iqc_fresh_parent_balanced_execution_v2 import \
    _parallel_lineage_graphs
from materials_gcts_iqc_fresh_parent_balanced_execution_v3 import \
    _chunked_fourth_parents
from materials_gcts_iqc_three_block_lazy_joint_execution import \
    _lazy_third_parent_worker
from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)
from materials_gcts_partial_port_graph_lineage_value import \
    score_partial_port_graph_lineage_value


@dataclass(frozen=True)
class FrozenFreshParentBalancedExecutionV4:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float, float, float]
    second_branch_receipt_digest: str
    second_branches: tuple
    complete_prefix_queue_digest: str
    action_marginal_prefix_digest: str
    action_marginal_prefix_rows: tuple
    selected_prefixes: int
    joint_prefixes: int
    diverse_fallback_prefixes: int
    maximum_diverse_fallbacks: int
    universal_avoidance_required: bool
    base_tail_when_unsaturated: bool
    lineage_model_digest: str
    fourth_policy_model_digest: str
    raw_nine_action_lineages: tuple
    raw_nine_action_lineage_digest: str
    raw_nine_action_parent_count: int
    selected_nine_action_lineage_indices: tuple[int, ...]
    selected_nine_action_parent_count: int
    fourth_candidates_before_balance: int
    candidates: tuple[FrozenParentBalancedFourthCandidate, ...]
    parent_width: int
    candidate_digest: str
    deterministic_receipt_digest: str
    stage_seconds: tuple[tuple[str, float], ...]
    target_used: bool = False


def _complete_action_marginal_lineages(
        *, center, seed_positions, seed_species, radii, raw, workers,
        maximum_fallbacks=4, require_universal_avoidance=True,
        base_tail_when_unsaturated=True):
    schedule, _artifact = load_default_schedule()
    scheduled = schedule_prefixes(
        schedule=schedule, seed_positions=seed_positions,
        seed_species=seed_species, branches=raw.second_branches)
    marginal = select_action_marginal_prefixes(
        scheduled=scheduled, branches=raw.second_branches,
        maximum_fallbacks=maximum_fallbacks,
        require_universal_avoidance=require_universal_avoidance,
        base_tail_when_unsaturated=base_tail_when_unsaturated)
    selected = tuple((int(row[0]), int(row[1]))
                     for row in marginal["selected_rows"])
    fallback_limit = (len(raw.second_branches) if maximum_fallbacks is None
                      else maximum_fallbacks)
    if (not 8 <= len(selected) <= 8 + fallback_limit or
            {parent for parent, _child in selected} != set(range(1, 9)) or
            any(not 1 <= sum(row[0] == parent for row in selected) <= 2
                for parent in range(1, 9))):
        raise AssertionError("action-marginal schedule lost parent balance")
    branch_by_parent = {int(row.first_rank): row
                        for row in raw.second_branches}
    tasks = []
    for parent, child in selected:
        branch = branch_by_parent[parent]
        tasks.append((
            tuple(center), tuple(seed_positions), tuple(seed_species),
            branch.first_actions,
            ((child, branch.second_actions[child]),), parent, *radii))
    if workers == 1:
        results = tuple(_lazy_third_parent_worker(task) for task in tasks)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(_lazy_third_parent_worker, tasks))
    lineages = tuple(lineage for worker_rows, _telemetry in results
                     for _counts, child_rows in worker_rows
                     for lineage in child_rows)
    if not lineages or {(row.parent_id, row.child_stable_index)
                        for row in lineages} != set(selected):
        raise AssertionError("action-marginal lineage completion drift")
    return lineages, scheduled, marginal


def freeze_fresh_parent_balanced_execution_v4(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        fourth_radius: float, workers: int = 4,
        ) -> FrozenFreshParentBalancedExecutionV4:
    if (workers < 1 or not first_radius < second_radius < third_radius <
            fourth_radius):
        raise ValueError("invalid V4 parent-balanced schedule")
    center = tuple(map(float, center))
    seed_positions = tuple(tuple(map(float, point))
                           for point in seed_positions)
    seed_species = tuple(map(str, seed_species))
    if not seed_positions or len(seed_positions) != len(seed_species):
        raise ValueError("invalid V4 parent-balanced seed")
    stage_seconds = []

    started = time.perf_counter()
    second = _freeze_second_branches(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species, first_radius=first_radius,
        second_radius=second_radius, workers=workers)
    stage_seconds.append(("first_and_second_frontiers",
                          time.perf_counter() - started))

    started = time.perf_counter()
    lineages, scheduled, marginal = _complete_action_marginal_lineages(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species,
        radii=(first_radius, second_radius, third_radius),
        raw=second, workers=workers)
    stage_seconds.append(("action_marginal_third_frontiers",
                          time.perf_counter() - started))
    raw_lineage_digest = hashlib.sha256(repr(tuple(
        lineage.all_actions for lineage in lineages)).encode()).hexdigest()
    if len({lineage.parent_id for lineage in lineages}) != 8:
        raise AssertionError("V4 raw receipt lost a parent")

    started = time.perf_counter()
    graph_rows = _parallel_lineage_graphs(
        lineages, seed_positions, seed_species, workers)
    stage_seconds.append(("transported_port_graphs",
                          time.perf_counter() - started))

    started = time.perf_counter()
    lineage_model = _fit_lineage_model()
    scores = tuple(score_partial_port_graph_lineage_value(
        lineage_model, graphs) for _lineage, graphs in graph_rows)
    retained = parent_balanced_beam(
        scores, tuple(lineage.parent_id for lineage, _graphs in graph_rows),
        tuple(lineage.all_actions for lineage, _graphs in graph_rows),
        PARENT_WIDTH)
    selected_lineages = tuple(graph_rows[index][0] for index in retained)
    stage_seconds.append(("lineage_model_fit_and_selection",
                          time.perf_counter() - started))
    if (len(selected_lineages) != 8 * PARENT_WIDTH or
            len({lineage.parent_id for lineage in selected_lineages}) != 8):
        raise AssertionError("V4 lineage selection drift")

    started = time.perf_counter()
    tasks = tuple((center, seed_positions, seed_species, fourth_radius,
                   index, lineage) for index, lineage
                  in enumerate(selected_lineages))
    groups = _chunked_fourth_parents(tasks, workers)
    stage_seconds.append(("chunked_fourth_frontiers",
                          time.perf_counter() - started))
    before = sum(count for _parent, count, _rows in groups)
    candidates = tuple(candidate for _parent, _count, rows in groups
                       for candidate in rows)
    if len(candidates) != len(selected_lineages) * PARENT_WIDTH:
        raise AssertionError("V4 fourth candidate balance drift")
    candidate_digest = hashlib.sha256(repr(tuple(
        (row.parent_lineage_index, row.fourth_stable_index, row.all_actions)
        for row in candidates)).encode()).hexdigest()
    policy_digest = load_parent_policy()["model_digest"]
    deterministic_payload = (
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        second.execution_digest, second.second_branches,
        scheduled["complete_queue_digest"],
        marginal["selected_prefix_digest"], len(marginal["selected_rows"]),
        len(marginal["joint_rows"]),
        len(marginal["diverse_fallback_rows"]),
        int(marginal["maximum_fallbacks"]),
        bool(marginal["universal_avoidance_required"]),
        bool(marginal["base_tail_when_unsaturated"]),
        lineage_model.model_digest, policy_digest, lineages,
        raw_lineage_digest, retained, before, candidates, PARENT_WIDTH,
        candidate_digest, False)
    deterministic_digest = hashlib.sha256(
        repr(deterministic_payload).encode()).hexdigest()
    return FrozenFreshParentBalancedExecutionV4(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        second.execution_digest, tuple(second.second_branches),
        scheduled["complete_queue_digest"],
        marginal["selected_prefix_digest"],
        tuple(marginal["selected_rows"]), len(marginal["selected_rows"]),
        len(marginal["joint_rows"]),
        len(marginal["diverse_fallback_rows"]),
        int(marginal["maximum_fallbacks"]),
        bool(marginal["universal_avoidance_required"]),
        bool(marginal["base_tail_when_unsaturated"]),
        lineage_model.model_digest, policy_digest, lineages,
        raw_lineage_digest, 8, tuple(map(int, retained)), 8, before,
        candidates, PARENT_WIDTH, candidate_digest, deterministic_digest,
        tuple((name, float(seconds)) for name, seconds in stage_seconds))


__all__ = [
    "FrozenFreshParentBalancedExecutionV4",
    "freeze_fresh_parent_balanced_execution_v4"]
