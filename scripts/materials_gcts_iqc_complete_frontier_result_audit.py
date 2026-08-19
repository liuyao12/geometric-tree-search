#!/usr/bin/env python3
"""Fast verifier for the consumed IQC complete-frontier development result."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_complete_frontier_development_audit_v1.json"
EXPECTED_SHA256 = \
    "f00a04ecb1e29653e06352294ce8296b62fa3ebae0422007373afc60b5eba367"


@dataclass(frozen=True)
class CompleteFrontierResultAudit:
    nuclei: int
    baseline_supply: int
    final_only_supply: int
    second_depth_supply: int
    complete_frozen_reach_supply: int
    widened_supply: int
    minimum_dual_budget: int
    maximum_dual_states: int
    fusion_top_one_exact: int
    candidate_supply_gate_passed: bool
    top_one_selection_gate_passed: bool
    fresh_confirmation_claimed: bool
    stationary_or_exponential_claimed: bool
    honest_status: str


def evaluate():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise AssertionError("complete-frontier result fixture drift")
    data = json.loads(raw)
    rows = data["beam_ablation"]
    if (data["schema_version"] != 1 or len(rows) != 5
            or data["target_used_for_candidate_or_ranking"]
            or data["fresh_confirmation_claimed"]
            or data["stationary_or_exponential_claimed"]):
        raise AssertionError("complete-frontier audit contract drift")
    final, second, root, root8, widened = rows
    ladder = data["missing_nucleus_reach_ladder"]
    if (final["exact_supply"] != 6
            or second["exact_supply"] != 6
            or root["exact_supply"] != 9
            or root8["exact_supply"] != 9
            or widened["exact_supply"] != 10
            or widened["schedule"] != [8, 8, 8]
            or max(widened["scalar_first_exact_ranks"]) != 9
            or max(widened["fusion_first_exact_ranks"]) != 15
            or widened["minimum_dual_portfolio_per_channel"] != 9
            or ladder["first_supplying_schedule"] != [8, 8, 8]
            or ladder["exact_supply"] != [False, False, True, True]):
        raise AssertionError("complete-frontier scientific result drift")
    supply = widened["exact_supply"] == 10
    top_one = widened["fusion_top_one_exact"] == 10
    return CompleteFrontierResultAudit(
        10, 6, final["exact_supply"], second["exact_supply"],
        root["exact_supply"], widened["exact_supply"],
        widened["minimum_dual_portfolio_per_channel"],
        widened["maximum_dual_portfolio_size"],
        widened["fusion_top_one_exact"], supply, top_one, False, False,
        data["honest_status"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report.__dict__, indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
