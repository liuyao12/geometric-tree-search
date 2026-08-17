#!/usr/bin/env python3
"""Held-forward IQC audit of the frozen frontier-band lookahead policy.

Wave 17 was the exploratory fork used to choose this policy.  Every later
decision is evaluated without letting its target membership enter branch
selection.  This is a temporal hold-forward test, not a spatially independent
material sample and not an exponential-growth certificate.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


EXPLORATORY_WAVE = 17
BEAM_WIDTH = 2
LOOKAHEAD_DEPTH = 2
POLICY = "leaf-boundary-first; current marking breaks ties"


@dataclass(frozen=True)
class HeldForwardIQCBeamBenchmark:
    policy: str
    exploratory_wave: int
    beam_width: int
    lookahead_depth: int
    exploratory_selected_rank: int
    exploratory_true_sites: int
    exploratory_false_sites: int
    held_forward_decision_waves: tuple[int, ...]
    held_forward_selected_ranks: tuple[int, ...]
    held_forward_true_sites: int
    held_forward_false_sites: int
    held_forward_precision: float
    held_forward_rollbacks: int
    selection_uses_truth: bool
    target_used_for_selection: bool
    temporal_confirmation_passed: bool
    spatially_independent_confirmation: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def audit(result) -> HeldForwardIQCBeamBenchmark:
    decisions = tuple(result.regenerative_beam_decisions)
    exploratory = next((row for row in decisions
                        if row.wave == EXPLORATORY_WAVE), None)
    if exploratory is None:
        raise ValueError("the frozen policy was not executed at wave 17")
    held = tuple(row for row in decisions if row.wave > EXPLORATORY_WAVE)
    true_sites = sum(row.selected_true_sites for row in held)
    false_sites = sum(row.selected_false_sites for row in held)
    enough_future = len(held) >= 3
    clean = not any(row.target_used_for_selection for row in decisions)
    passed = enough_future and false_sites == 0 and clean
    return HeldForwardIQCBeamBenchmark(
        POLICY, EXPLORATORY_WAVE, BEAM_WIDTH, LOOKAHEAD_DEPTH,
        exploratory.selected_rank, exploratory.selected_true_sites,
        exploratory.selected_false_sites,
        tuple(row.wave for row in held),
        tuple(row.selected_rank for row in held), true_sites, false_sites,
        true_sites / (true_sites + false_sites)
        if true_sites + false_sites else 0.,
        sum(row.greedy_rollback for row in held), False,
        not clean, passed, False, False,
        ("frozen lookahead transfers to later unseen forks on the same trace"
         if passed else
         "frozen lookahead does not yet pass its held-forward IQC gate"))


def evaluate(waves: int = 24) -> HeldForwardIQCBeamBenchmark:
    from materials_gcts_frontier_attachment_benchmark import evaluate as grow
    return audit(grow(
        regenerative_wave_count=waves, beam_start_wave=EXPLORATORY_WAVE,
        beam_width=BEAM_WIDTH))


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
