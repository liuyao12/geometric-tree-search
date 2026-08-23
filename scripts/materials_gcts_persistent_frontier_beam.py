#!/usr/bin/env python3
"""Target-free receding-horizon beam over complete GCTS configurations."""

from __future__ import annotations

import math
import hashlib
from dataclasses import dataclass

from materials_gcts_frontier_attachment import score_frontier_attachments
from materials_gcts_frontier_attachment_benchmark import (
    IterativeGrowthWave, RegenerativeGrowthTrace, _augmented_frontier,
    _dominant_source_color, _subset_proposals, _without_known_sites)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_recursive_connections import (
    extend_local_cluster_types, local_cluster_types,
    merge_marked_proposal_results,
    propose_with_recursive_marking)


def semantic_channel_descriptor(proposals, band, abstraction="exact"):
    """ID-free finite channel key from frozen cluster/connection evidence."""
    if abstraction not in ("exact", "port", "coarse", "chemistry"):
        raise ValueError("unknown semantic channel abstraction")
    entries = []
    for point in band:
        vote_count = proposals.votes[point]
        states = proposals.state_votes.get(point, {})
        state_rows = []
        for state, count in sorted(
                states.items(), key=lambda item: (-item[1], item[0]))[:3]:
            exact = (state.parent_type.color_key,
                     state.parent_type.cumulative_neighbor_counts,
                     state.source_type.color_key,
                     state.source_type.cumulative_neighbor_counts,
                     state.normalized_separation_bin,
                     round(count / vote_count, 3))
            port = exact[:-1]
            coarse = (exact[0], exact[2], exact[4])
            state_rows.append({"exact": exact, "port": port,
                               "coarse": coarse,
                               "chemistry": (exact[0], exact[2])}[abstraction])
        source_colors = proposals.color_votes[point]
        target_colors = proposals.target_color_votes[point]
        source = tuple(sorted(
            (color, round(count / vote_count, 3))
            for color, count in source_colors.items()))
        target = tuple(sorted(
            (color, round(count / vote_count, 3))
            for color, count in target_colors.items()))
        parent_counts = proposals.parent_votes.get(point, {})
        if abstraction == "exact":
            entries.append((
                tuple(state_rows), source, target, len(parent_counts),
                round(max(parent_counts.values(), default=0) / vote_count, 3),
                round(math.log1p(vote_count), 3)))
        elif abstraction == "port":
            entries.append((tuple(state_rows), tuple(color for color, _ in source),
                            tuple(color for color, _ in target)))
        elif abstraction == "coarse":
            entries.append((tuple(state_rows), tuple(color for color, _ in source),
                            tuple(color for color, _ in target)))
        else:
            entries.append((tuple(sorted(set(state_rows))),
                            tuple(color for color, _ in source),
                            tuple(color for color, _ in target)))
    descriptor = tuple(sorted(entries))
    return hashlib.sha256(repr(descriptor).encode()).hexdigest()


def advance_frontier_configuration(
        connection_marker, remaining, positions, colors, band, band_colors,
        cluster_edges, center, radius_limit):
    """Apply one exact candidate band and construct its self-fed frontier."""
    positions, colors, next_remaining, _types = \
        advance_frontier_configuration_with_types(
            connection_marker, remaining, positions, colors, band,
            band_colors, cluster_edges, center, radius_limit)
    return positions, colors, next_remaining


def advance_frontier_configuration_with_types(
        connection_marker, remaining, positions, colors, band, band_colors,
        cluster_edges, center, radius_limit, prior_cluster_types=None,
        prototype_mapping_cache=None):
    """Advance a frontier and return its exact updated local type table."""
    center = tuple(center)
    positions = tuple(positions)
    colors = tuple(colors)
    band = tuple(band)
    band_colors = tuple(band_colors)
    next_positions = positions + band
    next_colors = colors + band_colors
    old_count = len(positions)
    new_indices = tuple(range(old_count, len(next_positions)))
    all_indices = tuple(range(len(next_positions)))
    old_indices = tuple(range(old_count))
    if prior_cluster_types is None:
        types = local_cluster_types(
            next_positions, next_colors, cluster_edges)
    else:
        types = extend_local_cluster_types(
            positions, colors, prior_cluster_types,
            band, band_colors, cluster_edges)
    new_parents = propose_with_recursive_marking(
        connection_marker, next_positions, types, HIDDEN_UNIT,
        parent_indices=new_indices, source_indices=all_indices,
        prototype_mapping_cache=prototype_mapping_cache)
    old_parents = propose_with_recursive_marking(
        connection_marker, next_positions, types, HIDDEN_UNIT,
        parent_indices=old_indices, source_indices=new_indices,
        prototype_mapping_cache=prototype_mapping_cache)
    next_remaining = _without_known_sites(remaining, band)
    next_remaining = merge_marked_proposal_results(
        (next_remaining, new_parents, old_parents))
    next_remaining = _without_known_sites(next_remaining, next_positions)
    next_remaining = _subset_proposals(
        next_remaining, (point for point in next_remaining.votes
                         if math.dist(point, center) <= radius_limit + 1e-8))
    return next_positions, next_colors, next_remaining, types


@dataclass(frozen=True)
class PersistentBeamDecision:
    wave: int
    lookahead_depth: int
    retained_configurations: int
    evaluated_branches: int
    selected_path_ranks: tuple[int, ...]
    first_candidate_ranks: tuple[int, ...]
    first_candidate_sites: tuple[int, ...]
    first_candidate_positions: tuple[tuple[tuple[float, float, float], ...], ...]
    first_candidate_species: tuple[tuple[object, ...], ...]
    first_candidate_value_scores: tuple[float, ...]
    terminal_frontier_candidates: int
    forced_by_frozen_prefix: bool
    target_used_for_selection: bool


@dataclass(frozen=True)
class PersistentBeamResult:
    records: tuple[IterativeGrowthWave, ...]
    traces: tuple[RegenerativeGrowthTrace, ...]
    decisions: tuple[PersistentBeamDecision, ...]
    target_used_for_selection: bool


@dataclass(frozen=True)
class _State:
    positions: tuple[tuple[float, float, float], ...]
    colors: tuple[object, ...]
    remaining: object
    path_ranks: tuple[int, ...]
    path_bands: tuple[tuple[tuple[float, float, float], ...], ...]
    path_colors: tuple[tuple[object, ...], ...]
    terminal_candidates: int
    terminal_maximum: float


def run_persistent_frontier_beam(
        frontier_marker, refinement_marker, connection_marker, proposals,
        known_positions, known_colors, cluster_edges, provisional_pool,
        center, radius_limit, *, waves=1, beam_width=4,
        branching_width=4, lookahead_depth=3, root_rank_values=None,
        candidate_snapshot_width=None, root_rank_values_by_previous=None,
        forced_root_ranks=(), frontier_markers_by_depth=None,
        refinement_markers_by_depth=None):
    """Retain complete alternative states for several depths before commit."""
    if (waves < 1 or beam_width < 2 or branching_width < 2 or
            lookahead_depth < 2):
        raise ValueError("invalid persistent-beam dimensions")
    center = tuple(center)
    base_rank_values = dict(root_rank_values or {})
    contextual_rank_values = {
        int(context): dict(values)
        for context, values in (root_rank_values_by_previous or {}).items()}
    snapshot_width = candidate_snapshot_width or branching_width
    if snapshot_width < branching_width:
        raise ValueError("candidate snapshot cannot be narrower than branching")
    minimum_separation = min(
        math.dist(point, other)
        for index, point in enumerate(known_positions)
        for other in known_positions[index + 1:])

    def within(point):
        return math.dist(point, center) <= radius_limit + 1e-8

    frontier_stages = tuple(frontier_markers_by_depth or (frontier_marker,))
    refinement_stages = tuple(
        refinement_markers_by_depth or (refinement_marker,))
    if not frontier_stages or not refinement_stages:
        raise ValueError("staged marking sequences cannot be empty")

    def score(state, absolute_depth):
        if not state.remaining.votes:
            return {}, 0.
        active_frontier = frontier_stages[min(
            absolute_depth, len(frontier_stages) - 1)]
        active_refinement = refinement_stages[min(
            absolute_depth, len(refinement_stages) - 1)]
        frontier = score_frontier_attachments(
            active_frontier, state.remaining,
            state.positions, state.colors)
        augmented = _augmented_frontier(
            state.remaining, frontier, state.positions, state.colors,
            min(provisional_pool, len(frontier)))
        scores = score_frontier_attachments(
            active_refinement, state.remaining, *augmented)
        return scores, max(scores.values(), default=0.)

    def advance(state, band, band_colors):
        return advance_frontier_configuration(
            connection_marker, state.remaining, state.positions, state.colors,
            band, band_colors, cluster_edges, center, radius_limit)

    remaining = _subset_proposals(
        proposals, (point for point in proposals.votes if within(point)))
    positions = tuple(known_positions)
    colors = tuple(known_colors)
    records = []
    traces = []
    decisions = []
    cumulative = 0
    committed_root_ranks = []
    forced_prefix = tuple(int(rank) for rank in forced_root_ranks)
    if (len(forced_prefix) > waves or
            any(rank < 1 or rank > branching_width for rank in forced_prefix)):
        raise ValueError("frozen prefix ranks are invalid")
    for wave in range(1, waves + 1):
        previous_rank = committed_root_ranks[-1] if committed_root_ranks else 0
        rank_values = contextual_rank_values.get(
            previous_rank, base_rank_values)
        root = _State(positions, colors, remaining, (), (), (),
                      len(remaining.votes), 0.)
        frontier_states = (root,)
        first_rows = None
        first_snapshot = None
        evaluated = 0
        forced_rank = (forced_prefix[wave - 1]
                       if wave <= len(forced_prefix) else None)
        search_depth = 1 if forced_rank is not None else lookahead_depth
        for depth in range(search_depth):
            children = []
            for state in frontier_states:
                scores, _maximum = score(state, wave - 1 + depth)
                if depth == 0 and state is root:
                    snapshot_levels = sorted(
                        set(scores.values()), reverse=True)[:snapshot_width]
                    first_snapshot = tuple((
                        rank,
                        tuple(sorted(point for point, value in scores.items()
                                     if abs(value - level) <= 1e-12)))
                        for rank, level in enumerate(snapshot_levels, 1))
                ranked_levels = tuple(enumerate(sorted(
                    set(scores.values()), reverse=True)[:branching_width], 1))
                if depth == 0 and forced_rank is not None:
                    ranked_levels = tuple(
                        row for row in ranked_levels if row[0] == forced_rank)
                rows = []
                for rank, level in ranked_levels:
                    band = tuple(sorted(
                        point for point, value in scores.items()
                        if abs(value - level) <= 1e-12))
                    band_colors = tuple(_dominant_source_color(
                        state.remaining, point) for point in band)
                    conflicts = any(
                        0 < math.dist(point, other) <
                        minimum_separation - 1e-8
                        for index, point in enumerate(band)
                        for other in state.positions + band[index + 1:])
                    if conflicts:
                        continue
                    child_positions, child_colors, child_remaining = advance(
                        state, band, band_colors)
                    child_shell = _State(
                        child_positions, child_colors, child_remaining,
                        state.path_ranks + (rank,),
                        state.path_bands + (band,),
                        state.path_colors + (band_colors,),
                        len(child_remaining.votes), level)
                    next_scores, next_maximum = score(
                        child_shell, wave + depth)
                    child_shell = _State(
                        child_shell.positions, child_shell.colors,
                        child_shell.remaining, child_shell.path_ranks,
                        child_shell.path_bands, child_shell.path_colors,
                        len(next_scores), next_maximum)
                    rows.append((rank, band, band_colors, child_shell))
                    children.append(child_shell)
                    evaluated += 1
                if depth == 0 and state is root:
                    first_rows = tuple(rows)
            if not children:
                break
            if depth == 0 and forced_rank is not None:
                forced_children = tuple(
                    child for child in children
                    if child.path_ranks[0] == forced_rank)
                if len(forced_children) != 1:
                    raise ValueError("frozen prefix rank is unavailable")
                frontier_states = forced_children
                continue
            frontier_states = tuple(sorted(children, key=lambda state: (
                -rank_values.get(state.path_ranks[0], 0.),
                -state.terminal_candidates, -state.terminal_maximum,
                state.path_ranks))[:beam_width])
        if not frontier_states or not frontier_states[0].path_bands:
            break
        best = frontier_states[0]
        band = best.path_bands[0]
        band_colors = best.path_colors[0]
        committed = advance(root, band, band_colors)
        positions, colors, remaining = committed
        committed_root_ranks.append(best.path_ranks[0])
        cumulative += len(band)
        records.append(IterativeGrowthWave(
            wave, len(band), -1, -1, cumulative, float("nan"),
            float("nan"), best.terminal_maximum, len(root.remaining.votes)))
        traces.append(RegenerativeGrowthTrace(wave, band, band_colors))
        first_rows = first_rows or ()
        snapshot = tuple((rank, band, tuple(_dominant_source_color(
            root.remaining, point) for point in band))
                         for rank, band in (first_snapshot or ()))
        decisions.append(PersistentBeamDecision(
            wave, lookahead_depth, len(frontier_states), evaluated,
            best.path_ranks,
            tuple(row[0] for row in snapshot),
            tuple(len(row[1]) for row in snapshot),
            tuple(row[1] for row in snapshot),
            tuple(row[2] for row in snapshot),
            tuple(rank_values.get(row[0], 0.) for row in snapshot),
            best.terminal_candidates, forced_rank is not None, False))
        if not remaining.votes:
            break
    return PersistentBeamResult(
        tuple(records), tuple(traces), tuple(decisions), False)
