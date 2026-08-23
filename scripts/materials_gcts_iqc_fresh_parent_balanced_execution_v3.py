#!/usr/bin/env python3
"""Auditable and chunk-cached fresh parent-balanced IQC execution.

Version 3 retains every raw nine-action lineage before selection, separates a
deterministic receipt digest from nondeterministic wall timings, and executes
fourth-frontier parents in worker chunks so each process loads the frozen GCTS
runtime and marking policy only once.
"""

from __future__ import annotations

import hashlib
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_iqc_fourth_block_action_marking import \
    load_fourth_block_runtime
from materials_gcts_iqc_fourth_block_beam import parent_balanced_beam
from materials_gcts_iqc_fourth_block_parent_balanced_policy import (
    PARENT_WIDTH, load_default_result as load_parent_policy)
from materials_gcts_iqc_fresh_parent_balanced_execution import (
    FrozenParentBalancedFourthCandidate, _complete_scheduled_lineages,
    _fit_lineage_model, _freeze_second_branches, _prepare_pool, _score)
from materials_gcts_iqc_fresh_parent_balanced_execution_v2 import \
    _parallel_lineage_graphs
from materials_gcts_iqc_frozen_fusion_runtime import action_key, branch_features
from materials_gcts_iqc_three_block_channel_execution import _channel_tree
from materials_gcts_partial_port_graph_lineage_value import \
    score_partial_port_graph_lineage_value


@dataclass(frozen=True)
class FrozenFreshParentBalancedExecutionV3:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float, float, float]
    second_branch_receipt_digest: str
    scheduled_prefix_digest: str
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


def _fourth_parent_chunk_worker(tasks):
    """Execute several independent parents with one frozen runtime load."""
    runtime = load_fourth_block_runtime()
    policy = load_parent_policy()["model"]
    prototype_mapping_cache = {}
    groups = []
    for task in tasks:
        (center, seed_positions, seed_species, fourth_radius,
         parent_lineage_index, lineage) = task
        prior = tuple((tuple(map(float, point)), str(color))
                      for point, color in lineage.all_actions)
        source = SimpleNamespace(
            group=tuple(map(float, center)),
            seed_positions=tuple(tuple(map(float, point))
                                 for point in seed_positions) +
                           tuple(point for point, _color in prior),
            seed_species=tuple(map(str, seed_species)) +
                         tuple(color for _point, color in prior))
        states, _counts = _channel_tree(
            source, runtime, float(fourth_radius),
            prototype_mapping_cache=prototype_mapping_cache,
            action_budget=8, baseline_slots=3)
        rows = []
        for fourth_stable, state in enumerate(states):
            votes = tuple(map(int, state.proposals.votes.values()))
            future = (float(len(votes)), float(sum(votes)),
                      float(max(votes, default=0)),
                      float(sum(votes) / len(votes) if votes else 0.))
            features = tuple(map(float, branch_features(state))) + future
            rows.append((_score(policy, features), fourth_stable,
                         action_key(state.actions)))
        retained = parent_balanced_beam(
            tuple(row[0] for row in rows),
            tuple(parent_lineage_index for _row in rows),
            tuple((row[1], row[2]) for row in rows), PARENT_WIDTH)
        candidates = tuple(FrozenParentBalancedFourthCandidate(
            int(parent_lineage_index), int(lineage.parent_id),
            int(lineage.child_stable_index), int(lineage.third_stable_index),
            int(rows[index][1]), float(rows[index][0]), rows[index][2],
            prior + rows[index][2]) for index in retained)
        groups.append((int(parent_lineage_index), len(rows), candidates))
    return tuple(groups)


def _chunked_fourth_parents(tasks, workers):
    chunks = tuple(tasks[offset::workers] for offset in range(workers)
                   if tasks[offset::workers])
    if workers == 1:
        results = tuple(_fourth_parent_chunk_worker(chunk)
                        for chunk in chunks)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(_fourth_parent_chunk_worker, chunks))
    groups = tuple(sorted((row for result in results for row in result),
                          key=lambda row: row[0]))
    if tuple(row[0] for row in groups) != tuple(range(len(tasks))):
        raise AssertionError("chunked fourth-parent identity drift")
    return groups


def freeze_fresh_parent_balanced_execution_v3(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        fourth_radius: float, workers: int = 4,
        ) -> FrozenFreshParentBalancedExecutionV3:
    if (workers < 1 or not first_radius < second_radius < third_radius <
            fourth_radius):
        raise ValueError("invalid v3 parent-balanced schedule")
    center = tuple(map(float, center))
    seed_positions = tuple(tuple(map(float, point))
                           for point in seed_positions)
    seed_species = tuple(map(str, seed_species))
    if not seed_positions or len(seed_positions) != len(seed_species):
        raise ValueError("invalid v3 parent-balanced seed")
    stage_seconds = []

    started = time.perf_counter()
    second = _freeze_second_branches(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species, first_radius=first_radius,
        second_radius=second_radius, workers=workers)
    stage_seconds.append(("first_and_second_frontiers",
                          time.perf_counter() - started))

    started = time.perf_counter()
    lineages, prefix_digest = _complete_scheduled_lineages(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species,
        radii=(first_radius, second_radius, third_radius),
        raw=second, workers=workers)
    stage_seconds.append(("scheduled_third_frontiers",
                          time.perf_counter() - started))
    raw_lineage_digest = hashlib.sha256(repr(tuple(
        lineage.all_actions for lineage in lineages)).encode()).hexdigest()
    raw_parents = {lineage.parent_id for lineage in lineages}
    if len(raw_parents) != 8:
        raise AssertionError("raw nine-action receipt lost a parent")

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
    selected = tuple(graph_rows[index][0] for index in retained)
    stage_seconds.append(("lineage_model_fit_and_selection",
                          time.perf_counter() - started))
    if (len(selected) != 8 * PARENT_WIDTH or
            len({lineage.parent_id for lineage in selected}) != 8):
        raise AssertionError("v3 parent-balanced lineage selection drift")

    started = time.perf_counter()
    tasks = tuple((center, seed_positions, seed_species, fourth_radius,
                   index, lineage) for index, lineage in enumerate(selected))
    groups = _chunked_fourth_parents(tasks, workers)
    stage_seconds.append(("chunked_fourth_frontiers",
                          time.perf_counter() - started))
    before = sum(count for _parent, count, _rows in groups)
    candidates = tuple(candidate for _parent, _count, rows in groups
                       for candidate in rows)
    if (len(candidates) != len(selected) * PARENT_WIDTH or any(
            sum(row.parent_lineage_index == parent for row in candidates) !=
            PARENT_WIDTH for parent in range(len(selected)))):
        raise AssertionError("v3 fourth candidate balance drift")
    candidate_digest = hashlib.sha256(repr(tuple(
        (row.parent_lineage_index, row.fourth_stable_index, row.all_actions)
        for row in candidates)).encode()).hexdigest()
    policy_digest = load_parent_policy()["model_digest"]
    deterministic_payload = (
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        second.execution_digest, prefix_digest, lineage_model.model_digest,
        policy_digest, lineages, raw_lineage_digest, len(raw_parents),
        retained, 8, before, candidates, PARENT_WIDTH, candidate_digest,
        False)
    deterministic_digest = hashlib.sha256(
        repr(deterministic_payload).encode()).hexdigest()
    return FrozenFreshParentBalancedExecutionV3(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        second.execution_digest, prefix_digest, lineage_model.model_digest,
        policy_digest, lineages, raw_lineage_digest, len(raw_parents),
        tuple(map(int, retained)), 8, before, candidates, PARENT_WIDTH,
        candidate_digest, deterministic_digest,
        tuple((name, float(seconds)) for name, seconds in stage_seconds))


__all__ = [
    "FrozenFreshParentBalancedExecutionV3",
    "freeze_fresh_parent_balanced_execution_v3"]
