#!/usr/bin/env python3
"""Target-free three-block IQC execution with a complete parent antichain.

The historical four-parent portfolio is frozen for its one-shot confirmation.
This successor keeps the same width-eight first frontier, frozen child scoring,
and per-channel top-eight child portfolios, but does not delete four parent
subtrees before the third block.  Markings still order children and annotate
parents; all eight already-admitted parents remain executable tree branches.

No target, scorer, oracle, family label, lattice coordinate, or expected
action enters this module.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor

from materials_gcts_clusters2_future_option import (
    ChildOption, FrozenFutureOptionSpec, ParentOption,
    select_future_options)
from materials_gcts_iqc_frozen_fusion_runtime import BRANCH_VARIANTS
from materials_gcts_iqc_three_block_portfolio_execution import (
    FIRST_PARENT_WIDTH, SECOND_OPTION_TOP_K,
    FrozenThreeBlockPortfolioExecution, _complete_first_block,
    _prepare_pool, _second_worker, _third_parent_worker)
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime


COMPLETE_PARENT_WIDTH = FIRST_PARENT_WIDTH
COMPLETE_OPTION_SPEC = FrozenFutureOptionSpec(
    tuple(BRANCH_VARIANTS), top_k=SECOND_OPTION_TOP_K,
    beam_width=COMPLETE_PARENT_WIDTH)


def freeze_three_block_complete_parent_execution(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        workers: int = 4) -> FrozenThreeBlockPortfolioExecution:
    """Freeze all eight admitted parent subtrees target-free."""
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
    parents = tuple(ParentOption(
        branch.first_rank, tuple(ChildOption(
            (branch.first_rank, stable_index), scores)
            for stable_index, scores in enumerate(
                branch.second_channel_scores))) for branch in branches)
    selection = select_future_options(parents, COMPLETE_OPTION_SPEC)
    if set(selection.selected_parent_ids) != {
            branch.first_rank for branch in branches}:
        raise AssertionError("complete parent antichain was truncated")
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
        center, len(seed_positions),
        (first_radius, second_radius, third_radius), first_counts,
        len(first_states_all), first_digest, retained_first, branches,
        selection.candidate_digest, selection.selected_parent_ids,
        selected_by, child_receipt, third_counts, lineages,
        candidate_digest)
    return FrozenThreeBlockPortfolioExecution(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius), first_counts,
        len(first_states_all), first_digest, retained_first, branches,
        selection.candidate_digest,
        tuple(map(int, selection.selected_parent_ids)), selected_by,
        child_receipt, third_counts, lineages, candidate_digest,
        hashlib.sha256(repr(payload).encode()).hexdigest())


__all__ = [
    "COMPLETE_OPTION_SPEC", "COMPLETE_PARENT_WIDTH",
    "freeze_three_block_complete_parent_execution"]
