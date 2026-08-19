#!/usr/bin/env python3
"""Fast immutable audit of the fresh IQC complete-frontier confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_iqc_complete_frontier_confirmation_candidates import (
    DEFAULT_FIXTURE as CANDIDATE_FIXTURE, EXPECTED_FIXTURE_SHA256,
    EXPECTED_RECEIPT_DIGEST, validate_candidate_receipt)
from materials_gcts_iqc_complete_frontier_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST)


RESULT_FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_complete_frontier_confirmation_result_v1.json"
EXPECTED_RESULT_SHA256 = \
    "35abf7d90a05c29ae00c794fd1551b011ec293f04395fc06d32b867a86a81a63"


@dataclass(frozen=True)
class CompleteFrontierConfirmationAudit:
    center: tuple[float, float, float]
    seed_atoms: int
    target_atoms: int
    novel_target_atoms: int
    terminal_count: int
    exact_terminal_count: int
    portfolio_states: int
    scalar_first_exact_rank: int
    fusion_first_exact_rank: int
    candidate_supply_confirmed: bool
    rollback_portfolio_confirmed: bool
    top_one_scalar_confirmed: bool
    top_one_fusion_confirmed: bool
    target_order_clean: bool
    fresh_spatial_confirmation: bool
    stationary_or_exponential_claimed: bool
    honest_status: str


def evaluate():
    candidate_raw = Path(CANDIDATE_FIXTURE).read_bytes()
    if hashlib.sha256(candidate_raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("confirmation candidate fixture drift")
    candidate = validate_candidate_receipt(json.loads(candidate_raw))
    result_raw = RESULT_FIXTURE.read_bytes()
    if hashlib.sha256(result_raw).hexdigest() != EXPECTED_RESULT_SHA256:
        raise AssertionError("confirmation result fixture drift")
    result = json.loads(result_raw)
    if (candidate["receipt_digest"] != EXPECTED_RECEIPT_DIGEST
            or result["candidate_receipt_digest"] != EXPECTED_RECEIPT_DIGEST
            or result["protocol_digest"] != EXPECTED_MANIFEST_DIGEST
            or tuple(result["center"]) != CONFIRMATION_CENTER
            or result["terminal_count"] != candidate["terminal_count"]
            or result["portfolio_states"] != len(candidate["portfolio_indices"])
            or result["target_open_count"] != 1
            or result["target_used_for_fit_candidate_or_ranking"]
            or not result["candidate_digest_unchanged"]
            or not result["target_bound_plus_one_stable"]
            or not result["target_domain_disjoint"]
            or result["stationary_or_exponential_claimed"]):
        raise AssertionError("confirmation provenance or leakage gate drift")
    supply = bool(result["candidate_supply_confirmation_passed"]
                  and result["complete_tree_supplies_exact"]
                  and result["exact_terminal_count"] > 0)
    portfolio = bool(result["portfolio_confirmation_passed"]
                     and result["dual_portfolio_supplies_exact"])
    clean = bool(result["candidates_frozen_before_target"]
                 and result["candidate_digest_unchanged"]
                 and result["target_open_count"] == 1
                 and not result["target_used_for_fit_candidate_or_ranking"])
    return CompleteFrontierConfirmationAudit(
        CONFIRMATION_CENTER, result["seed_atoms"], result["target_atoms"],
        result["novel_target_atoms"], result["terminal_count"],
        result["exact_terminal_count"], result["portfolio_states"],
        result["scalar_first_exact_rank"],
        result["fusion_first_exact_rank"], supply, portfolio,
        result["top_one_scalar_gate_passed"],
        result["top_one_fusion_gate_passed"], clean,
        result["fresh_spatial_confirmation"], False,
        result["honest_status"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report.__dict__, indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
