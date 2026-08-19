#!/usr/bin/env python3
"""Audit the consumed ten-centre frozen-fusion development receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_iqc_extended_fusion_development_benchmark import (
    validate_candidate_receipt)


ROOT = Path(__file__).resolve().parent
CANDIDATE_FIXTURE = ROOT / "fixtures/iqc_extended_fusion_candidates_v1.json"
RESULT_FIXTURE = ROOT / \
    "fixtures/iqc_extended_fusion_development_result.json"
EXPECTED_CANDIDATE_SHA256 = \
    "9a535bedcf7d22e8d533aa90d821de81d01a14a4013381f680e722a80efd21fa"
EXPECTED_CANDIDATE_RECEIPT_DIGEST = \
    "c19f9b99260e944ec3511dc92889dccf83ddacf2354dd3019b2a6319d4042da3"
EXPECTED_RESULT_SHA256 = \
    "45fa11ef5cde4644835d6d929ca36d60e6607461e123c69f56d324658691d551"


@dataclass(frozen=True)
class ExtendedFusionDevelopmentAudit:
    nuclei: int
    selected_sites: int
    scalar_terminal_supply: int
    scalar_selected_exact: int
    scalar_selected_correct: int
    fusion_terminal_supply: int
    fusion_selected_exact: int
    fusion_selected_correct: int
    exact_candidate_missing_nuclei: int
    fusion_changed_selected_terminal_nuclei: int
    fusion_changed_outcome_nuclei: int
    bound_plus_one_stable: bool
    pairwise_disjoint: bool
    target_open_count: int
    target_used_before_scoring: bool
    development_transfer_gate_passed: bool
    incremental_fusion_advantage: bool
    candidate_supply_gate_passed: bool
    stationary_or_exponential_claimed: bool
    honest_status: str


def evaluate():
    candidate_bytes = CANDIDATE_FIXTURE.read_bytes()
    if hashlib.sha256(candidate_bytes).hexdigest() != \
            EXPECTED_CANDIDATE_SHA256:
        raise AssertionError("extended fusion candidate fixture drift")
    candidates = validate_candidate_receipt(json.loads(candidate_bytes))
    if candidates["receipt_digest"] != EXPECTED_CANDIDATE_RECEIPT_DIGEST:
        raise AssertionError("extended fusion candidate receipt drift")
    result_bytes = RESULT_FIXTURE.read_bytes()
    if hashlib.sha256(result_bytes).hexdigest() != EXPECTED_RESULT_SHA256:
        raise AssertionError("extended fusion result fixture drift")
    result = json.loads(result_bytes)
    nuclei = result["centers"]
    if (result["candidate_receipt_digest"] != candidates["receipt_digest"]
            or result["candidate_digests"] != [
                row["candidate_digest"] for row in candidates["nuclei"]]
            or result["seed_atoms"] != [
                row["seed_atoms"] for row in candidates["nuclei"]]
            or result["terminal_counts"] != [
                row["terminal_count"] for row in candidates["nuclei"]]
            or len(nuclei) != 10 or result["selected_sites"] != 30
            or result["scalar_terminal_supply"] != 6
            or result["scalar_selected_exact"] != 6
            or result["scalar_selected_correct"] != 23
            or result["fusion_terminal_supply"] != 6
            or result["fusion_selected_exact"] != 6
            or result["fusion_selected_correct"] != 23
            or not all(result["bound_plus_one_stable_by_center"])
            or not result["target_domains_pairwise_disjoint"]
            or result["target_open_count"] != 1
            or result["target_used_for_fit_features_candidates_or_ranking"]
            or result["fresh_confirmation_claimed"]
            or result["stationary_or_exponential_claimed"]):
        raise AssertionError("extended fusion development result drift")
    changed = sum(row["scalar_stable_index"] != row["fusion_stable_index"]
                  for row in candidates["nuclei"])
    changed_outcome = sum(
        (first, second) != (third, fourth)
        for first, second, third, fourth in zip(
            result["scalar_selected_exact_by_center"],
            result["scalar_selected_correct_by_center"],
            result["fusion_selected_exact_by_center"],
            result["fusion_selected_correct_by_center"]))
    transfer = bool(result["fusion_noninferior_to_scalar"]
                    and result["fusion_selected_exact"] >= 6
                    and result["fusion_selected_correct"] >= 23)
    incremental = bool(
        result["fusion_selected_exact"] > result["scalar_selected_exact"]
        or result["fusion_selected_correct"] >
           result["scalar_selected_correct"])
    supply = result["fusion_terminal_supply"] == len(nuclei)
    return ExtendedFusionDevelopmentAudit(
        len(nuclei), result["selected_sites"],
        result["scalar_terminal_supply"], result["scalar_selected_exact"],
        result["scalar_selected_correct"], result["fusion_terminal_supply"],
        result["fusion_selected_exact"], result["fusion_selected_correct"],
        len(nuclei) - result["fusion_terminal_supply"], changed,
        changed_outcome, all(result["bound_plus_one_stable_by_center"]),
        result["target_domains_pairwise_disjoint"],
        result["target_open_count"], False, transfer, incremental, supply,
        False,
        "frozen policy transfers, graph fusion ties scalar, candidate supply "
        "fails on four nuclei")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report.__dict__, indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
