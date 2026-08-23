#!/usr/bin/env python3
"""Parallel graph-feature execution for a second fresh IQC confirmation."""

from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor

from materials_gcts_iqc_fourth_block_beam import parent_balanced_beam
from materials_gcts_iqc_fourth_block_parent_balanced_policy import (
    PARENT_WIDTH, load_default_result as load_parent_policy)
from materials_gcts_iqc_fourth_block_action_marking import \
    load_fourth_block_runtime
from materials_gcts_iqc_bounded_lineage_value import \
    _transported_stage_features
from materials_gcts_iqc_fresh_parent_balanced_execution import (
    FrozenFreshParentBalancedExecution, _complete_scheduled_lineages,
    _fit_lineage_model, _fourth_parent_worker, _freeze_second_branches,
    _prepare_pool)
from materials_gcts_partial_port_graph_lineage_value import \
    score_partial_port_graph_lineage_value


def _transported_graph_chunk(task):
    seed_positions, seed_species, items = task
    runtime = load_fourth_block_runtime()
    rows = []
    for stable_index, prior, block in items:
        _values, graph, _section = _transported_stage_features(
            seed_positions=seed_positions, seed_species=seed_species,
            prior_actions=prior, block_actions=block, runtime=runtime)
        rows.append((stable_index, graph))
    return tuple(rows)


def _parallel_lineage_graphs(
        lineages, seed_positions, seed_species, workers):
    keys = {}
    lineage_keys = []
    for lineage in lineages:
        actions = tuple((tuple(map(float, point)), str(color))
                        for point, color in lineage.all_actions)
        prior = ()
        row = []
        for start in (0, 3, 6):
            block = actions[start:start + 3]
            key = (prior, block)
            if key not in keys:
                keys[key] = len(keys)
            row.append(keys[key])
            prior += block
        lineage_keys.append(tuple(row))
    items = tuple((stable_index, prior, block)
                  for (prior, block), stable_index in keys.items())
    chunks = tuple(items[offset::workers] for offset in range(workers)
                   if items[offset::workers])
    tasks = tuple((tuple(seed_positions), tuple(seed_species), chunk)
                  for chunk in chunks)
    if workers == 1:
        results = tuple(_transported_graph_chunk(task) for task in tasks)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(_transported_graph_chunk, tasks))
    graphs = {stable_index: graph for result in results
              for stable_index, graph in result}
    if len(graphs) != len(items):
        raise AssertionError("parallel transported graph cache incomplete")
    return tuple((lineage, tuple(graphs[index] for index in row))
                 for lineage, row in zip(lineages, lineage_keys))


def freeze_fresh_parent_balanced_execution_v2(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        fourth_radius: float, workers: int = 4,
        ) -> FrozenFreshParentBalancedExecution:
    if (workers < 1 or not first_radius < second_radius < third_radius <
            fourth_radius):
        raise ValueError("invalid fresh parent-balanced schedule")
    center = tuple(map(float, center))
    seed_positions = tuple(tuple(map(float, point))
                           for point in seed_positions)
    seed_species = tuple(map(str, seed_species))
    if not seed_positions or len(seed_positions) != len(seed_species):
        raise ValueError("invalid fresh parent-balanced seed")
    raw = _freeze_second_branches(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species, first_radius=first_radius,
        second_radius=second_radius, workers=workers)
    if raw.target_used:
        raise AssertionError("second-branch receipt used a target")
    lineages, prefix_digest = _complete_scheduled_lineages(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species,
        radii=(first_radius, second_radius, third_radius),
        raw=raw, workers=workers)
    graph_rows = _parallel_lineage_graphs(
        lineages, seed_positions, seed_species, workers)
    lineage_model = _fit_lineage_model()
    scores = tuple(score_partial_port_graph_lineage_value(
        lineage_model, graphs) for _lineage, graphs in graph_rows)
    retained = parent_balanced_beam(
        scores, tuple(lineage.parent_id for lineage, _graphs in graph_rows),
        tuple(lineage.all_actions for lineage, _graphs in graph_rows),
        PARENT_WIDTH)
    selected = tuple(graph_rows[index][0] for index in retained)
    if (len(selected) != 8 * PARENT_WIDTH or
            len({lineage.parent_id for lineage in selected}) != 8):
        raise AssertionError("parallel nine-action parent beam drift")
    tasks = tuple((center, seed_positions, seed_species, fourth_radius,
                   index, lineage) for index, lineage in enumerate(selected))
    if workers == 1:
        groups = tuple(map(_fourth_parent_worker, tasks))
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_fourth_parent_worker, tasks))
    before = sum(count for count, _rows in groups)
    candidates = tuple(candidate for _count, rows in groups
                       for candidate in rows)
    retained_parents = {row.parent_lineage_index for row in candidates}
    if (len(retained_parents) != len(selected) or any(
            sum(row.parent_lineage_index == parent for row in candidates) !=
            PARENT_WIDTH for parent in retained_parents)):
        raise AssertionError("parallel fourth block lost a parent lineage")
    candidate_digest = hashlib.sha256(repr(tuple(
        (row.parent_lineage_index, row.fourth_stable_index, row.all_actions)
        for row in candidates)).encode()).hexdigest()
    policy_digest = load_parent_policy()["model_digest"]
    payload = (
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        raw.execution_digest, prefix_digest, lineage_model.model_digest,
        policy_digest, len(lineages), len(selected), 8, before,
        len(candidates), len(retained_parents), PARENT_WIDTH, candidates,
        candidate_digest, False)
    return FrozenFreshParentBalancedExecution(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        raw.execution_digest, prefix_digest, lineage_model.model_digest,
        policy_digest, len(lineages), len(selected), 8, before,
        len(candidates), len(retained_parents), PARENT_WIDTH, candidates,
        candidate_digest, hashlib.sha256(repr(payload).encode()).hexdigest())


__all__ = ["freeze_fresh_parent_balanced_execution_v2"]
