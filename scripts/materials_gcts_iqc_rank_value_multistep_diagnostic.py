#!/usr/bin/env python3
"""Locate valid post-confirmation IQC channels without expanding them."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_iqc_persistent_beam_diagnostic import (
    PersistentBeamDiagnostic, evaluate as evaluate_persistent)
from materials_gcts_iqc_rank_value_confirmation import (
    CONFIRMATION_CENTER, TRAINING_OBSERVATIONS)
from materials_gcts_rank_calibrated_value import (
    FrozenRankValue, fit_rank_value)


@dataclass(frozen=True)
class RankValueMultistepDiagnostic:
    model: FrozenRankValue
    active_branching_width: int
    diagnostic_snapshot_width: int
    result: PersistentBeamDiagnostic
    second_wave_first_exact_rank: int | None
    second_wave_exact_ranks: tuple[int, ...]
    candidate_geometry_missing: bool
    sustained_exact_growth: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate():
    model = fit_rank_value(TRAINING_OBSERVATIONS)
    result = evaluate_persistent(
        lookahead_depth=2, beam_width=4, branching_width=4,
        robust_marking=True, evaluation_center=CONFIRMATION_CENTER,
        root_rank_values=model.as_mapping(), waves=2,
        candidate_snapshot_width=12)
    truths = result.wave_candidate_true_sites[1]
    falsehoods = result.wave_candidate_false_sites[1]
    exact = tuple(rank for rank, (true, false) in enumerate(
        zip(truths, falsehoods), 1) if true > 0 and false == 0)
    return RankValueMultistepDiagnostic(
        model, 4, 12, result, exact[0] if exact else None, exact,
        not bool(exact), result.all_executed_actions_exact, False,
        ("rank value sustains two exact waves" if
         result.all_executed_actions_exact else
         "rank value is exact once; valid wave-two channels lie outside width four"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
