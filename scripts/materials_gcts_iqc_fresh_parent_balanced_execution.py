#!/usr/bin/env python3
"""Target-blind four-block IQC execution with two parent-balanced levels."""

from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_iqc_bounded_lineage_graph_value import SPEC
from materials_gcts_iqc_bounded_lineage_value import (
    _candidate_rows, _correct, _transported_stage_features, _truth_index)
from materials_gcts_iqc_fourth_block_action_marking import \
    load_fourth_block_runtime
from materials_gcts_iqc_fourth_block_beam import parent_balanced_beam
from materials_gcts_iqc_fourth_block_parent_balanced_policy import (
    PARENT_WIDTH, load_default_result as load_parent_policy)
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, branch_features, load_default_runtime)
from materials_gcts_iqc_three_block_channel_execution import _channel_tree
from materials_gcts_iqc_three_block_lazy_joint_execution import \
    _lazy_third_parent_worker
from materials_gcts_iqc_three_block_portfolio_execution import (
    FIRST_PARENT_WIDTH, _complete_first_block, _prepare_pool, _second_worker)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)
from materials_gcts_partial_port_graph_lineage_value import (
    PartialPortGraphLineageExample, fit_partial_port_graph_lineage_value,
    score_partial_port_graph_lineage_value)


@dataclass(frozen=True)
class FrozenParentBalancedFourthCandidate:
    parent_lineage_index: int
    parent_id: int
    child_stable_index: int
    third_stable_index: int
    fourth_stable_index: int
    score: float
    actions: tuple[tuple, ...]
    all_actions: tuple[tuple, ...]


@dataclass(frozen=True)
class FrozenFreshParentBalancedExecution:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float, float, float]
    raw_three_block_execution_digest: str
    scheduled_prefix_digest: str
    lineage_model_digest: str
    fourth_policy_model_digest: str
    complete_nine_action_lineages: int
    nine_action_candidates_retained: int
    nine_action_parent_count: int
    fourth_candidates_before_balance: int
    fourth_candidates_retained: int
    fourth_parent_lineages_retained: int
    parent_width: int
    candidates: tuple[FrozenParentBalancedFourthCandidate, ...]
    candidate_digest: str
    execution_digest: str
    target_used: bool = False


def _score(model, features):
    return sum((float(value) - float(mean)) / float(scale) * float(weight)
               for value, mean, scale, weight in zip(
                   features, model["means"], model["scales"],
                   model["weights"]))


def _freeze_second_branches(
        *, center, seed_positions, seed_species,
        first_radius, second_radius, workers):
    """Freeze all eight first parents and their complete second frontiers.

    The old portfolio executor also materializes a large third-block corpus
    under a different selector.  The parent-balanced hierarchy needs only the
    first/second receipt before applying the preregistered joint-prefix
    schedule, so doing that extra geometry work would be both wasteful and a
    misleading part of the claimed bounded search cost.
    """
    runtime = load_default_runtime()
    first_states, first_counts, first_order, first_digest = \
        _complete_first_block(
            center, seed_positions, seed_species, first_radius, runtime)
    retained = tuple(first_order[:min(FIRST_PARENT_WIDTH,
                                      len(first_states))])
    if len(retained) != FIRST_PARENT_WIDTH:
        raise AssertionError("fresh execution lost a first-block parent")
    tasks = tuple((
        center, rank, stable, first_states[stable].positions,
        first_states[stable].species, first_states[stable].actions,
        second_radius) for rank, stable in enumerate(retained, 1))
    if workers == 1:
        branches = tuple(_second_worker(task) for task in tasks)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            branches = tuple(pool.map(_second_worker, tasks))
    branches = tuple(sorted(branches, key=lambda row: row.first_rank))
    if len(branches) != FIRST_PARENT_WIDTH:
        raise AssertionError("fresh execution lost a second-block branch")
    payload = (tuple(center), len(seed_positions), float(first_radius),
               float(second_radius), tuple(first_counts), len(first_states),
               first_digest, retained, branches)
    return SimpleNamespace(
        second_branches=branches,
        execution_digest=hashlib.sha256(repr(payload).encode()).hexdigest(),
        target_used=False)


def _complete_scheduled_lineages(
        *, center, seed_positions, seed_species, radii, raw, workers):
    schedule, _artifact = load_default_schedule()
    scheduled = schedule_prefixes(
        schedule=schedule, seed_positions=seed_positions,
        seed_species=seed_species, branches=raw.second_branches)
    selected = tuple(sorted((int(row[0]), int(row[1]))
                            for row in scheduled["selected_rows"]
                            if "joint" in tuple(map(str, row[2]))))
    if len(selected) != 8 or {parent for parent, _child in selected} != \
            set(range(1, 9)):
        raise AssertionError("fresh schedule did not preserve eight parents")
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
        raise AssertionError("fresh scheduled lineage completion drift")
    return lineages, scheduled["selected_prefix_digest"]


def _lineage_graphs(lineages, seed_positions, seed_species, runtime):
    cache = {}
    rows = []
    for lineage in lineages:
        actions = tuple((tuple(map(float, point)), str(color))
                        for point, color in lineage.all_actions)
        blocks = tuple(actions[start:start + 3] for start in (0, 3, 6))
        prior = ()
        graphs = []
        for block in blocks:
            key = (prior, block)
            graph = cache.get(key)
            if graph is None:
                _values, graph, _section = _transported_stage_features(
                    seed_positions=seed_positions, seed_species=seed_species,
                    prior_actions=prior, block_actions=block, runtime=runtime)
                cache[key] = graph
            graphs.append(graph)
            prior += block
        rows.append((lineage, tuple(graphs)))
    return tuple(rows)


def _fit_lineage_model():
    groups, _completion = _candidate_rows()
    examples = []
    for row in groups:
        target, _ = oracle_crop_fast(row["center"], row["radii"][2])
        truth = _truth_index(target.positions, target.species)
        for parent, _features, _colors, actions, graphs, _temporal in row["rows"]:
            examples.append(PartialPortGraphLineageExample(
                row["group"], parent, graphs,
                all(_correct(point, color, truth)
                    for point, color in actions)))
    return fit_partial_port_graph_lineage_value(
        tuple(examples), SPEC, embedding_cache={})


def _fourth_parent_worker(task):
    (center, seed_positions, seed_species, fourth_radius,
     parent_lineage_index, lineage) = task
    runtime = load_fourth_block_runtime()
    policy = load_parent_policy()["model"]
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
        action_budget=8, baseline_slots=3)
    rows = []
    for fourth_stable, state in enumerate(states):
        votes = tuple(map(int, state.proposals.votes.values()))
        future = (
            float(len(votes)), float(sum(votes)),
            float(max(votes, default=0)),
            float(sum(votes) / len(votes) if votes else 0.))
        features = tuple(map(float, branch_features(state))) + future
        rows.append((_score(policy, features), fourth_stable,
                     action_key(state.actions)))
    retained = parent_balanced_beam(
        tuple(row[0] for row in rows),
        tuple(parent_lineage_index for _row in rows),
        tuple((row[1], row[2]) for row in rows), PARENT_WIDTH)
    return len(rows), tuple(FrozenParentBalancedFourthCandidate(
        int(parent_lineage_index), int(lineage.parent_id),
        int(lineage.child_stable_index), int(lineage.third_stable_index),
        int(rows[index][1]), float(rows[index][0]), rows[index][2],
        prior + rows[index][2]) for index in retained)


def freeze_fresh_parent_balanced_execution(
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
        raise AssertionError("raw three-block execution used a target")
    lineages, prefix_digest = _complete_scheduled_lineages(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species,
        radii=(first_radius, second_radius, third_radius),
        raw=raw, workers=workers)
    runtime = load_fourth_block_runtime()
    graph_rows = _lineage_graphs(
        lineages, seed_positions, seed_species, runtime)
    lineage_model = _fit_lineage_model()
    lineage_scores = tuple(score_partial_port_graph_lineage_value(
        lineage_model, graphs) for _lineage, graphs in graph_rows)
    retained = parent_balanced_beam(
        lineage_scores, tuple(row.parent_id for row, _graphs in graph_rows),
        tuple(row.all_actions for row, _graphs in graph_rows), PARENT_WIDTH)
    selected_lineages = tuple(graph_rows[index][0] for index in retained)
    if (len(selected_lineages) != 8 * PARENT_WIDTH
            or len({row.parent_id for row in selected_lineages}) != 8):
        raise AssertionError("nine-action parent-balanced beam drift")
    tasks = tuple((center, seed_positions, seed_species, fourth_radius,
                   index, lineage)
                  for index, lineage in enumerate(selected_lineages))
    if workers == 1:
        groups = tuple(map(_fourth_parent_worker, tasks))
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_fourth_parent_worker, tasks))
    before = sum(row[0] for row in groups)
    candidates = tuple(candidate for _count, rows in groups
                       for candidate in rows)
    retained_parents = {row.parent_lineage_index for row in candidates}
    if (len(retained_parents) != len(selected_lineages)
            or any(sum(row.parent_lineage_index == parent
                       for row in candidates) != PARENT_WIDTH
                   for parent in retained_parents)):
        raise AssertionError("fresh fourth block lost a parent lineage")
    candidate_digest = hashlib.sha256(repr(tuple(
        (row.parent_lineage_index, row.fourth_stable_index, row.all_actions)
        for row in candidates)).encode()).hexdigest()
    fourth_policy_model_digest = load_parent_policy()["model_digest"]
    payload = (
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        raw.execution_digest, prefix_digest, lineage_model.model_digest,
        fourth_policy_model_digest, len(lineages),
        len(selected_lineages), 8, before, len(candidates),
        len(retained_parents), PARENT_WIDTH, candidates, candidate_digest,
        False)
    return FrozenFreshParentBalancedExecution(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius, fourth_radius),
        raw.execution_digest, prefix_digest, lineage_model.model_digest,
        fourth_policy_model_digest, len(lineages),
        len(selected_lineages), 8, before, len(candidates),
        len(retained_parents), PARENT_WIDTH, candidates, candidate_digest,
        hashlib.sha256(repr(payload).encode()).hexdigest())


__all__ = [
    "FrozenFreshParentBalancedExecution",
    "FrozenParentBalancedFourthCandidate",
    "freeze_fresh_parent_balanced_execution"]
