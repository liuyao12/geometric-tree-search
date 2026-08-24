#!/usr/bin/env python3
"""Hybrid IQC execution supplied by a learned commuting first frontier."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from materials_gcts_iqc_commuting_parent_execution import (
    FrozenCommutingSecondFrontier, freeze_commuting_second_frontier)
from materials_gcts_iqc_fourth_block_beam import parent_balanced_beam
from materials_gcts_iqc_fourth_block_parent_balanced_policy import (
    PARENT_WIDTH, load_default_result as load_parent_policy)
from materials_gcts_iqc_fresh_parent_balanced_execution import \
    _fit_lineage_model
from materials_gcts_iqc_fresh_parent_balanced_execution_v2 import \
    _parallel_lineage_graphs
from materials_gcts_iqc_fresh_parent_balanced_execution_v3 import \
    _chunked_fourth_parents
from materials_gcts_iqc_fresh_parent_balanced_execution_v4 import (
    FrozenFreshParentBalancedExecutionV4,
    _complete_action_marginal_lineages)
from materials_gcts_partial_port_graph_lineage_value import \
    score_partial_port_graph_lineage_value


@dataclass(frozen=True)
class FrozenCommutingHybridExecution:
    first_frontier: FrozenCommutingSecondFrontier
    downstream: FrozenFreshParentBalancedExecutionV4
    execution_digest: str
    candidate_geometry_unchanged: bool = True
    target_used: bool = False


def _finish_from_commuting_second(
        *, center, seed_positions, seed_species, first_radius, second_radius,
        third_radius, fourth_radius, workers, maximum_fallbacks, second,
        stage_seconds):
    """Duplicate V4 downstream logic without mutating preregistered source."""
    started = time.perf_counter()
    lineages, scheduled, marginal = _complete_action_marginal_lineages(
        center=center, seed_positions=seed_positions,
        seed_species=seed_species,
        radii=(first_radius, second_radius, third_radius),
        raw=second, workers=workers,
        maximum_fallbacks=maximum_fallbacks)
    stage_seconds.append(("action_marginal_third_frontiers",
                          time.perf_counter() - started))
    raw_lineage_digest = hashlib.sha256(repr(tuple(
        lineage.all_actions for lineage in lineages)).encode()).hexdigest()
    if len({lineage.parent_id for lineage in lineages}) != 8:
        raise AssertionError("commuting raw receipt lost a parent")

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
        raise AssertionError("commuting lineage selection drift")

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
        raise AssertionError("commuting fourth candidate balance drift")
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


def freeze_commuting_hybrid_execution(
        *, center, seed_positions, seed_species, first_radius, second_radius,
        third_radius, fourth_radius, marking_model, workers=4,
        maximum_fallbacks=2, parent_width=8):
    """Run the existing three later blocks from closure-ranked L1 parents."""
    if (workers < 1 or parent_width != 8 or
            not 0 <= maximum_fallbacks <= 8 or
            not first_radius < second_radius < third_radius < fourth_radius):
        raise ValueError("invalid commuting hybrid execution request")
    center = tuple(map(float, center))
    positions = tuple(tuple(map(float, point)) for point in seed_positions)
    species = tuple(map(str, seed_species))
    if not positions or len(positions) != len(species):
        raise ValueError("invalid commuting hybrid seed")
    started = time.perf_counter()
    first = freeze_commuting_second_frontier(
        center=center, seed_positions=positions, seed_species=species,
        first_radius=first_radius, second_radius=second_radius,
        marking_model=marking_model, workers=workers,
        parent_width=parent_width)
    stage_seconds = [("commuting_first_and_second_frontiers",
                      time.perf_counter() - started)]
    downstream = _finish_from_commuting_second(
        center=center, seed_positions=positions, seed_species=species,
        first_radius=first_radius, second_radius=second_radius,
        third_radius=third_radius, fourth_radius=fourth_radius,
        workers=workers, maximum_fallbacks=maximum_fallbacks,
        second=first, stage_seconds=stage_seconds)
    if (first.target_used or downstream.target_used or
            downstream.second_branch_receipt_digest !=
            first.execution_digest or
            tuple(downstream.second_branches) != first.second_branches):
        raise AssertionError("commuting L1 receipt changed downstream")
    digest = hashlib.sha256(repr((
        first.execution_digest, downstream.deterministic_receipt_digest,
        marking_model.model_digest, False)).encode()).hexdigest()
    return FrozenCommutingHybridExecution(
        first, downstream, digest, True, False)


__all__ = [
    "FrozenCommutingHybridExecution", "freeze_commuting_hybrid_execution"]
