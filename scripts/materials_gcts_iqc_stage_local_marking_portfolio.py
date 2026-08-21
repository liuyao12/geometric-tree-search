#!/usr/bin/env python3
"""Apply the generic marking-portfolio tree to stage-local IQC actions.

The adapter exposes two already-frozen markings: the stage-local connection
order that constructed the terminal portfolio and the target-free rollout
value that previously replaced it greedily.  Both now expand one candidate
set; neither receives target positions or authorizes new geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_stage_local_rollout_runtime import (
    execute_stage_local_rollout_search)
from materials_gcts_marking_portfolio_tree import (
    FrozenPortfolioAction, MarkingPortfolioResult,
    search_marking_portfolio)


@dataclass(frozen=True)
class StageLocalPortfolioState:
    positions: tuple[tuple[float, float, float], ...]
    species: tuple[str, ...]


@dataclass(frozen=True)
class IQCStageLocalMarkingPortfolio:
    center: tuple[float, float, float]
    seed_atoms: int
    blocks: int
    beam_width: int
    beam_schedule: tuple[int, ...]
    allocation: str
    expansion_candidate_counts: tuple[int, ...]
    expansion_candidate_digests: tuple[str, ...]
    tree: MarkingPortfolioResult
    target_api_present: bool = False
    target_used: bool = False


def _state_key(state: StageLocalPortfolioState):
    return _digest(tuple(sorted((
        tuple(round(float(value), 8) for value in point), str(color))
        for point, color in zip(state.positions, state.species))))


def execute_iqc_stage_local_marking_portfolio(
        runtime, prefix_model, rollout_model, *, center, seed_positions,
        seed_species, public_radius, blocks=3, beam_width=2,
        beam_schedule=None,
        allocation="global-marking-round-robin",
        block_executor: Callable = execute_stage_local_rollout_search,
        ) -> IQCStageLocalMarkingPortfolio:
    """Keep connection- and rollout-ranked branches in one physical beam."""
    schedule = (tuple(map(int, beam_schedule)) if beam_schedule is not None
                else (int(beam_width),) * blocks)
    if (blocks < 1 or beam_width < 2 or len(schedule) != blocks or
            any(width < 2 for width in schedule)):
        raise ValueError("invalid IQC marking portfolio dimensions")
    seed = StageLocalPortfolioState(
        tuple(tuple(map(float, point)) for point in seed_positions),
        tuple(map(str, seed_species)))
    counts, digests = [], []

    def expand(state):
        result = block_executor(
            runtime, prefix_model, rollout_model,
            center=tuple(map(float, center)),
            seed_positions=state.positions, seed_species=state.species,
            public_radius=float(public_radius))
        if result.target_api_present or result.target_used:
            raise ValueError("target-tainted stage-local expansion")
        counts.append(len(result.candidates))
        digests.append(str(result.candidate_digest))
        return tuple(FrozenPortfolioAction(
            action_id=row.action_key,
            next_state=StageLocalPortfolioState(
                tuple(row.state.positions), tuple(row.state.species)),
            marking_scores=(("connection", -float(index)),
                            ("rollout", float(row.rollout_score))))
                     for index, row in enumerate(result.candidates))

    tree = search_marking_portfolio(
        seed, expand=expand, state_key=_state_key,
        marking_names=("connection", "rollout"),
        depth=blocks, beam_width=beam_width, beam_schedule=schedule,
        allocation=allocation)
    return IQCStageLocalMarkingPortfolio(
        tuple(map(float, center)), len(seed.positions), blocks, beam_width,
        schedule, allocation,
        tuple(counts), tuple(digests), tree)
