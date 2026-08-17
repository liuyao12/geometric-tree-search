#!/usr/bin/env python3
"""Exploratory target-free lookahead audit for the IQC wave-17 fork."""
from dataclasses import dataclass
from materials_gcts_frontier_band_beam import FrontierBand, search_frontier_bands


@dataclass(frozen=True)
class IQCFrontierBeamAudit:
    candidate_ranks: tuple[int, ...]
    selected_rank: int
    selected_true_sites: int
    selected_false_sites: int
    greedy_true_sites: int
    greedy_false_sites: int
    greedy_rollback: int
    selection_uses_truth: bool
    target_used: bool
    exploratory_same_trace: bool
    confirmatory_gate_passed: bool


def audit(result):
    rows = result.regenerative_wave17_score_bands[:2]
    # Freeze the entire search input before reading posthoc truth fields.
    evidence = tuple((row.rank, row.score, row.lookahead_maximum_score)
                     for row in rows)
    roots = tuple(FrontierBand(rank, current, 0.)
                  for rank, current, _future in evidence)
    future = {rank: (FrontierBand(f"future-{rank}", 0., value),)
              for rank, _current, value in evidence}
    trace = search_frontier_bands(
        roots, lambda band: future.get(band.band_id, ()), beam_width=2,
        lookahead_depth=2, leaf_boundary_first=True)
    selected_rank = int(trace.selected_ids[0])
    truth = {row.rank: (row.true_sites, row.false_sites) for row in rows}
    return IQCFrontierBeamAudit(
        tuple(rank for rank, _current, _future in evidence), selected_rank,
        *truth[selected_rank], *truth[1], trace.greedy_rollbacks,
        False, trace.target_used, True, False)


def evaluate():
    from materials_gcts_frontier_attachment_benchmark import evaluate as grow
    return audit(grow(regenerative_wave_count=17))
