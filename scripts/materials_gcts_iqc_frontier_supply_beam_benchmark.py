#!/usr/bin/env python3
"""Held-forward IQC audit for option-preserving frontier-band search.

Diagnostics at waves 17--19 show that the exact band among the top four keeps
the largest compatible next frontier.  This target-free value is frozen before
wave 20.  The audit does not convert same-trace evidence into a disjoint or
stationary/exponential claim.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


BEAM_WIDTH = 4
LOOKAHEAD_DEPTH = 2
EXPLORATORY_WAVES = (17, 18, 19)
HELD_FORWARD_START = 20
OBJECTIVE = "frontier-supply"


@dataclass(frozen=True)
class FrontierSupplyBeamBenchmark:
    objective: str
    beam_width: int
    exploratory_waves: tuple[int, ...]
    exploratory_selected_ranks: tuple[int, ...]
    exploratory_true_sites: int
    exploratory_false_sites: int
    held_forward_waves: tuple[int, ...]
    held_forward_selected_ranks: tuple[int, ...]
    held_forward_true_sites: int
    held_forward_false_sites: int
    held_forward_precision: float
    held_forward_rollbacks: int
    first_failure_wave: int | None
    target_used_for_selection: bool
    temporal_gate_passed: bool
    spatially_independent_confirmation: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def audit(result) -> FrontierSupplyBeamBenchmark:
    decisions = tuple(result.regenerative_beam_decisions)
    exploratory = tuple(row for row in decisions
                        if row.wave in EXPLORATORY_WAVES)
    if tuple(row.wave for row in exploratory) != EXPLORATORY_WAVES:
        raise ValueError("frontier-supply policy must execute waves 17--19")
    if any(getattr(row, "selection_objective", OBJECTIVE) != OBJECTIVE
           for row in decisions):
        raise ValueError("unexpected branch objective")
    held = tuple(row for row in decisions if row.wave >= HELD_FORWARD_START)
    true_sites = sum(row.selected_true_sites for row in held)
    false_sites = sum(row.selected_false_sites for row in held)
    leaked = any(row.target_used_for_selection for row in decisions)
    failure = next((row.wave for row in held
                    if row.selected_false_sites), None)
    passed = len(held) >= 3 and false_sites == 0 and not leaked
    return FrontierSupplyBeamBenchmark(
        OBJECTIVE, BEAM_WIDTH, EXPLORATORY_WAVES,
        tuple(row.selected_rank for row in exploratory),
        sum(row.selected_true_sites for row in exploratory),
        sum(row.selected_false_sites for row in exploratory),
        tuple(row.wave for row in held),
        tuple(row.selected_rank for row in held), true_sites, false_sites,
        true_sites / (true_sites + false_sites)
        if true_sites + false_sites else 0.,
        sum(row.greedy_rollback for row in held), failure, leaked, passed,
        False, False,
        ("option-preserving beam stays exact on later same-trace states"
         if passed else
         "option-preserving beam fails its held-forward IQC gate"))


def evaluate(waves: int = 24) -> FrontierSupplyBeamBenchmark:
    from materials_gcts_frontier_attachment_benchmark import evaluate as grow
    return audit(grow(
        regenerative_wave_count=waves, beam_start_wave=17,
        beam_width=BEAM_WIDTH, diagnostic_waves=EXPLORATORY_WAVES,
        beam_objective=OBJECTIVE))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--waves", type=int, default=24)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.waves)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
