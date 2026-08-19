#!/usr/bin/env python3
"""Locate the proposal-reach bottleneck on the one unsupplied IQC nucleus.

The failed nucleus was identified by the consumed ten-centre development
audit.  Four power-of-two reach schedules are declared before candidate
construction.  For every schedule the complete reachable tree is frozen,
including scalar and fusion orders, before the consumed target is opened once.
This is diagnostic evidence only, never a fresh confirmation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_iqc_complete_terminal_frontier_audit import (
    CompleteTerminalNucleus, _crop_all, _freeze_nucleus, _score)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_incidence_token_preflight import _key


FAILED_CENTER_INDEX = 3
REACH_LADDER = ((4, 4, 8), (8, 4, 8), (8, 8, 8), (8, 8, 16))


@dataclass(frozen=True)
class ReachScheduleResult:
    schedule: tuple[int, ...]
    candidate_counts_by_depth: tuple[int, ...]
    terminal_count: int
    scalar_supply: bool
    scalar_selected_exact: bool
    scalar_selected_correct: int
    scalar_first_exact_rank: int | None
    fusion_supply: bool
    fusion_selected_exact: bool
    fusion_selected_correct: int
    fusion_first_exact_rank: int | None
    candidate_digest: str


@dataclass(frozen=True)
class IQCMissingNucleusReachAudit:
    center_index: int
    center: tuple[float, float, float]
    schedules: tuple[tuple[int, ...], ...]
    results: tuple[ReachScheduleResult, ...]
    first_supplying_schedule: tuple[int, ...] | None
    exact_geometry_reachable: bool
    candidates_frozen_before_target: bool
    target_open_count: int
    target_used_for_candidate_or_ranking: bool
    consumed_development_only: bool
    fresh_confirmation_claimed: bool
    stationary_or_exponential_claimed: bool
    receipt_digest: str
    honest_status: str


def _receipt(row: CompleteTerminalNucleus):
    return (
        row.center, row.seed_atoms, row.candidate_counts_by_depth,
        row.retained_counts_by_depth, row.candidate_digest,
        tuple(terminal.actions for terminal in row.terminals),
        row.scalar_order, row.fusion_order)


def evaluate():
    runtime = load_default_runtime()
    center = DEVELOPMENT_CENTERS[FAILED_CENTER_INDEX]
    seed = _crop_all(SEED_RADIUS, ORACLE_LIFT_BOUND)[FAILED_CENTER_INDEX]
    nuclei = tuple(_freeze_nucleus(
        runtime, center, seed, unpruned_from_depth=0, schedule=schedule)
        for schedule in REACH_LADDER)
    receipt = tuple((schedule, _receipt(row))
                    for schedule, row in zip(REACH_LADDER, nuclei))
    digest = hashlib.sha256(repr(receipt).encode()).hexdigest()
    immutable = repr(receipt)

    target = _crop_all(TARGET_RADIUS, ORACLE_LIFT_BOUND)[FAILED_CENTER_INDEX]
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    results = []
    for schedule, nucleus in zip(REACH_LADDER, nuclei):
        scalar = _score(nucleus, nucleus.scalar_order, truth)
        fusion = _score(nucleus, nucleus.fusion_order, truth)
        results.append(ReachScheduleResult(
            schedule, nucleus.candidate_counts_by_depth,
            len(nucleus.terminals), *scalar, *fusion,
            nucleus.candidate_digest))
    if immutable != repr(receipt):
        raise AssertionError("reach-ladder receipt changed after target open")
    first = next((row.schedule for row in results if row.fusion_supply), None)
    return IQCMissingNucleusReachAudit(
        FAILED_CENTER_INDEX, tuple(center), REACH_LADDER, tuple(results),
        first, first is not None, True, 1, False, True, False, False, digest,
        (f"exact terminal first appears under reach schedule {first}"
         if first else
         "exact terminal absent throughout the bounded reach ladder"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
