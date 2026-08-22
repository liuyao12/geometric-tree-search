#!/usr/bin/env python3
"""Target-free IQC execution with a library of child markings.

The historical complete-parent executor retains all eight first-block
subtrees, but each of its four legacy markings contributes only its top eight
children.  This successor preserves that immutable geometry and unions a
fifth, frozen local-section channel.  The new channel contributes only two
children per parent and can rank actions but cannot create or authorize them.

No target, scorer, oracle, family label, lattice coordinate, global origin, or
expected action enters this module.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from materials_gcts_clusters2_future_option import (
    ChildOption, ParentOption, select_future_options)
from materials_gcts_iqc_three_block_complete_parent_execution import (
    COMPLETE_OPTION_SPEC, COMPLETE_PARENT_WIDTH)
from materials_gcts_iqc_three_block_portfolio_execution import (
    FIRST_PARENT_WIDTH, FrozenPortfolioLineage, FrozenSecondBranch,
    _complete_first_block, _prepare_pool, _second_worker,
    _third_parent_worker)
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_local_section_child_marking import (
    EXPECTED_ARTIFACT_DIGEST, EXPECTED_FIXTURE_SHA256,
    EXPECTED_MODEL_DIGEST, load_default_marking, select_child_ids)


LOCAL_SECTION_CHANNEL = "local-section"


@dataclass(frozen=True)
class FrozenThreeBlockMarkingLibraryExecution:
    center: tuple[float, float, float]
    seed_atoms: int
    radii: tuple[float, float, float]
    first_candidate_counts: tuple[int, ...]
    first_candidate_count: int
    first_candidate_digest: str
    first_retained_stable_indices: tuple[int, ...]
    second_branches: tuple[FrozenSecondBranch, ...]
    legacy_option_candidate_digest: str
    selected_parent_ids: tuple[int, ...]
    selected_by_channels: tuple[tuple[str, int], ...]
    legacy_child_ids_by_parent: tuple[
        tuple[int, tuple[int, ...]], ...]
    local_child_ids_by_parent: tuple[
        tuple[int, tuple[int, ...]], ...]
    selected_child_ids_by_parent: tuple[
        tuple[int, tuple[int, ...]], ...]
    local_section_fixture_sha256: str
    local_section_model_digest: str
    local_section_artifact_digest: str
    child_library_digest: str
    third_candidate_counts: tuple[tuple[int, ...], ...]
    lineages: tuple[FrozenPortfolioLineage, ...]
    candidate_digest: str
    execution_digest: str
    target_used: bool = False


def select_marking_library_children(*, branches, seed_positions,
                                    seed_species):
    """Union legacy and local selections without changing candidate geometry."""
    model, artifact = load_default_marking()
    parents = tuple(ParentOption(
        branch.first_rank, tuple(ChildOption(
            (branch.first_rank, stable_index), scores)
            for stable_index, scores in enumerate(
                branch.second_channel_scores))) for branch in branches)
    legacy_selection = select_future_options(parents, COMPLETE_OPTION_SPEC)
    expected_parents = {branch.first_rank for branch in branches}
    if set(legacy_selection.selected_parent_ids) != expected_parents:
        raise AssertionError("complete marking-library parent antichain truncated")
    legacy_lookup = {
        int(parent): tuple(int(child[1]) for child in children)
        for parent, children in legacy_selection.selected_child_ids_by_parent
    }
    legacy_rows = []
    local_rows = []
    union_rows = []
    for branch in sorted(branches, key=lambda row: row.first_rank):
        parent = int(branch.first_rank)
        legacy = legacy_lookup[parent]
        local = tuple(map(int, select_child_ids(
            model=model, seed_positions=seed_positions,
            seed_species=seed_species, branch=branch)))
        if len(local) != min(model.child_top_k, len(branch.second_actions)):
            raise AssertionError("local-section child width drift")
        union = tuple(dict.fromkeys((*legacy, *local)))
        if not set(legacy).issubset(union) or not set(local).issubset(union):
            raise AssertionError("marking-library union lost a child")
        legacy_rows.append((parent, legacy))
        local_rows.append((parent, local))
        union_rows.append((parent, union))
    selected_by = tuple((str(name), int(parent)) for name, parent
                        in legacy_selection.selected_by_channels) + tuple(
        (LOCAL_SECTION_CHANNEL, int(branch.first_rank))
        for branch in sorted(branches, key=lambda row: row.first_rank))
    digest_payload = (
        legacy_selection.candidate_digest, tuple(legacy_rows),
        tuple(local_rows), tuple(union_rows), model.model_digest,
        artifact["artifact_digest"])
    return {
        "model": model,
        "artifact": artifact,
        "legacy_selection": legacy_selection,
        "selected_by_channels": selected_by,
        "legacy_rows": tuple(legacy_rows),
        "local_rows": tuple(local_rows),
        "union_rows": tuple(union_rows),
        "digest": hashlib.sha256(repr(digest_payload).encode()).hexdigest(),
    }


def freeze_three_block_marking_library_execution(
        *, center, seed_positions, seed_species,
        first_radius: float, second_radius: float, third_radius: float,
        workers: int = 4) -> FrozenThreeBlockMarkingLibraryExecution:
    """Freeze all eight parents and the union of five child markings."""
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
    library = select_marking_library_children(
        branches=branches, seed_positions=seed_positions,
        seed_species=seed_species)
    if (len(branches) != COMPLETE_PARENT_WIDTH or
            {parent for parent, _children in library["union_rows"]} !=
            set(range(1, COMPLETE_PARENT_WIDTH + 1))):
        raise AssertionError("marking library did not preserve eight parents")

    branch_by_parent = {branch.first_rank: branch for branch in branches}
    third_payloads = []
    for parent, child_ids in library["union_rows"]:
        branch = branch_by_parent[parent]
        child_rows = tuple((child, branch.second_actions[child])
                           for child in child_ids)
        third_payloads.append((
            center, seed_positions, seed_species, branch.first_actions,
            child_rows, parent, first_radius, second_radius, third_radius))
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
    selected_parents = tuple(parent for parent, _children
                             in library["union_rows"])
    payload = (
        center, len(seed_positions),
        (first_radius, second_radius, third_radius), first_counts,
        len(first_states_all), first_digest, retained_first, branches,
        library["legacy_selection"].candidate_digest, selected_parents,
        library["selected_by_channels"], library["legacy_rows"],
        library["local_rows"], library["union_rows"],
        EXPECTED_FIXTURE_SHA256, EXPECTED_MODEL_DIGEST,
        EXPECTED_ARTIFACT_DIGEST, library["digest"], third_counts,
        lineages, candidate_digest)
    return FrozenThreeBlockMarkingLibraryExecution(
        center, len(seed_positions),
        (first_radius, second_radius, third_radius), first_counts,
        len(first_states_all), first_digest, retained_first, branches,
        library["legacy_selection"].candidate_digest, selected_parents,
        library["selected_by_channels"], library["legacy_rows"],
        library["local_rows"], library["union_rows"],
        EXPECTED_FIXTURE_SHA256, EXPECTED_MODEL_DIGEST,
        EXPECTED_ARTIFACT_DIGEST, library["digest"], third_counts,
        lineages, candidate_digest,
        hashlib.sha256(repr(payload).encode()).hexdigest())


__all__ = [
    "FrozenThreeBlockMarkingLibraryExecution", "LOCAL_SECTION_CHANNEL",
    "freeze_three_block_marking_library_execution",
    "select_marking_library_children"]
