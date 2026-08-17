#!/usr/bin/env python3
"""Target-free beam search over immutable GCTS frontier-band choices."""
from dataclasses import dataclass
from typing import Callable, Hashable


@dataclass(frozen=True)
class FrontierBand:
    band_id: Hashable
    marking_score: float
    boundary_score: float
    payload: object = None


@dataclass(frozen=True)
class BeamTrace:
    selected_ids: tuple[Hashable, ...]
    explored_nodes: int
    greedy_rollbacks: int
    target_used: bool


def search_frontier_bands(
    roots: tuple[FrontierBand, ...],
    expand: Callable[[FrontierBand], tuple[FrontierBand, ...]], *,
    beam_width: int = 2, lookahead_depth: int = 2,
) -> BeamTrace:
    if beam_width < 1 or lookahead_depth < 1:
        raise ValueError("beam width and lookahead must be positive")
    # A path score keeps the learned local marking, but future boundary
    # consistency is the certificate that can overturn a greedy first step.
    beam = tuple(((band,), band.marking_score + band.boundary_score)
                 for band in roots)
    explored = len(beam)
    greedy = max(roots, key=lambda row: (row.marking_score, repr(row.band_id)))
    for _ in range(1, lookahead_depth):
        candidates = []
        for path, score in beam:
            children = expand(path[-1])
            explored += len(children)
            if not children:
                candidates.append((path, score))
            for child in children:
                candidates.append((path + (child,), score +
                                   child.marking_score + child.boundary_score))
        beam = tuple(sorted(candidates, key=lambda row: (
            -row[1], tuple(map(repr, (item.band_id for item in row[0])))))
                     [:beam_width])
    best = beam[0][0]
    return BeamTrace(tuple(item.band_id for item in best), explored,
                     int(best[0].band_id != greedy.band_id), False)
