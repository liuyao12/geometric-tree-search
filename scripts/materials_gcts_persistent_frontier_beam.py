#!/usr/bin/env python3
"""Target-free receding-horizon beam over complete GCTS configurations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from materials_gcts_frontier_attachment import score_frontier_attachments
from materials_gcts_frontier_attachment_benchmark import (
    IterativeGrowthWave, RegenerativeGrowthTrace, _augmented_frontier,
    _dominant_source_color, _subset_proposals, _without_known_sites)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_recursive_connections import (
    local_cluster_types, merge_marked_proposal_results,
    propose_with_recursive_marking)


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
        branching_width=4, lookahead_depth=3, root_rank_values=None):
    """Retain complete alternative states for several depths before commit."""
    if (waves < 1 or beam_width < 2 or branching_width < 2 or
            lookahead_depth < 2):
        raise ValueError("invalid persistent-beam dimensions")
    center = tuple(center)
    rank_values = dict(root_rank_values or {})
    minimum_separation = min(
        math.dist(point, other)
        for index, point in enumerate(known_positions)
        for other in known_positions[index + 1:])

    def within(point):
        return math.dist(point, center) <= radius_limit + 1e-8

    def score(state):
        if not state.remaining.votes:
            return {}, 0.
        frontier = score_frontier_attachments(
            frontier_marker, state.remaining,
            state.positions, state.colors)
        augmented = _augmented_frontier(
            state.remaining, frontier, state.positions, state.colors,
            min(provisional_pool, len(frontier)))
        scores = score_frontier_attachments(
            refinement_marker, state.remaining, *augmented)
        return scores, max(scores.values(), default=0.)

    def advance(state, band, band_colors):
        positions = state.positions + band
        colors = state.colors + band_colors
        old_count = len(state.positions)
        new_indices = tuple(range(old_count, len(positions)))
        all_indices = tuple(range(len(positions)))
        old_indices = tuple(range(old_count))
        types = local_cluster_types(positions, colors, cluster_edges)
        new_parents = propose_with_recursive_marking(
            connection_marker, positions, types, HIDDEN_UNIT,
            parent_indices=new_indices, source_indices=all_indices)
        old_parents = propose_with_recursive_marking(
            connection_marker, positions, types, HIDDEN_UNIT,
            parent_indices=old_indices, source_indices=new_indices)
        remaining = _without_known_sites(state.remaining, band)
        remaining = merge_marked_proposal_results(
            (remaining, new_parents, old_parents))
        remaining = _without_known_sites(remaining, positions)
        remaining = _subset_proposals(
            remaining, (point for point in remaining.votes if within(point)))
        return positions, colors, remaining

    remaining = _subset_proposals(
        proposals, (point for point in proposals.votes if within(point)))
    positions = tuple(known_positions)
    colors = tuple(known_colors)
    records = []
    traces = []
    decisions = []
    cumulative = 0
    for wave in range(1, waves + 1):
        root = _State(positions, colors, remaining, (), (), (),
                      len(remaining.votes), 0.)
        frontier_states = (root,)
        first_rows = None
        evaluated = 0
        for depth in range(lookahead_depth):
            children = []
            for state in frontier_states:
                scores, _maximum = score(state)
                levels = sorted(set(scores.values()), reverse=True)[
                    :branching_width]
                rows = []
                for rank, level in enumerate(levels, 1):
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
                    next_scores, next_maximum = score(child_shell)
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
        cumulative += len(band)
        records.append(IterativeGrowthWave(
            wave, len(band), -1, -1, cumulative, float("nan"),
            float("nan"), best.terminal_maximum, len(root.remaining.votes)))
        traces.append(RegenerativeGrowthTrace(wave, band, band_colors))
        first_rows = first_rows or ()
        decisions.append(PersistentBeamDecision(
            wave, lookahead_depth, len(frontier_states), evaluated,
            best.path_ranks,
            tuple(row[0] for row in first_rows),
            tuple(len(row[1]) for row in first_rows),
            tuple(row[1] for row in first_rows),
            tuple(row[2] for row in first_rows),
            tuple(rank_values.get(row[0], 0.) for row in first_rows),
            best.terminal_candidates, False))
        if not remaining.votes:
            break
    return PersistentBeamResult(
        tuple(records), tuple(traces), tuple(decisions), False)
