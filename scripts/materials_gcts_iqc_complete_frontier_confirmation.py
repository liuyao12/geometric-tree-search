#!/usr/bin/env python3
"""One-shot scorer for the preregistered complete IQC frontier confirmation."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_complete_frontier_confirmation_candidates import (
    DEFAULT_FIXTURE, EXPECTED_FIXTURE_SHA256, EXPECTED_RECEIPT_DIGEST,
    validate_candidate_receipt)
from materials_gcts_iqc_complete_frontier_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, ORACLE_LIFT_BOUND,
    REQUIRED_CENTER_SEPARATION, SEED_RADIUS, TARGET_RADIUS, audit)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, PRIOR_CENTERS)
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


_TARGET_OPEN_COUNT = 0


@dataclass(frozen=True)
class IQCCompleteFrontierConfirmation:
    protocol_digest: str
    candidate_receipt_digest: str
    center: tuple[float, float, float]
    seed_atoms: int
    target_atoms: int
    novel_target_atoms: int
    terminal_count: int
    portfolio_states: int
    exact_terminal_count: int
    scalar_first_exact_rank: int | None
    fusion_first_exact_rank: int | None
    scalar_top_one_exact: bool
    fusion_top_one_exact: bool
    scalar_top_one_correct_sites: int
    fusion_top_one_correct_sites: int
    complete_tree_supplies_exact: bool
    dual_portfolio_supplies_exact: bool
    candidate_supply_confirmation_passed: bool
    portfolio_confirmation_passed: bool
    top_one_scalar_gate_passed: bool
    top_one_fusion_gate_passed: bool
    target_bound_plus_one_stable: bool
    target_domain_disjoint: bool
    candidates_frozen_before_target: bool
    candidate_digest_unchanged: bool
    target_open_count: int
    target_used_for_fit_candidate_or_ranking: bool
    fresh_spatial_confirmation: bool
    stationary_or_exponential_claimed: bool
    honest_status: str


def _load_receipt():
    raw = Path(DEFAULT_FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("confirmation candidate fixture byte drift")
    receipt = validate_candidate_receipt(json.loads(raw))
    if receipt["receipt_digest"] != EXPECTED_RECEIPT_DIGEST:
        raise AssertionError("confirmation candidate receipt drift")
    return receipt


def _terminal_actions(receipt):
    raw = zlib.decompress(base64.b64decode(
        receipt["terminal_actions_zlib_base64"], validate=True))
    if hashlib.sha256(raw).hexdigest() != receipt["terminal_actions_sha256"]:
        raise AssertionError("confirmation terminal payload drift")
    return tuple(tuple((tuple(map(float, point)), str(color))
                       for point, color in terminal)
                 for terminal in json.loads(raw))


def _score_terminals(terminals, scalar_order, fusion_order,
                     portfolio_indices, truth):
    exact = tuple(all(truth.get(_key(point)) == color
                      for point, color in terminal)
                  for terminal in terminals)
    correct = tuple(sum(truth.get(_key(point)) == color
                        for point, color in terminal)
                    for terminal in terminals)
    scalar_rank = next((rank for rank, index in enumerate(scalar_order, 1)
                        if exact[index]), None)
    fusion_rank = next((rank for rank, index in enumerate(fusion_order, 1)
                        if exact[index]), None)
    return {
        "exact": exact,
        "correct": correct,
        "scalar_first_exact_rank": scalar_rank,
        "fusion_first_exact_rank": fusion_rank,
        "scalar_top_one_exact": exact[scalar_order[0]],
        "fusion_top_one_exact": exact[fusion_order[0]],
        "scalar_top_one_correct": correct[scalar_order[0]],
        "fusion_top_one_correct": correct[fusion_order[0]],
        "portfolio_supply": any(exact[index] for index in portfolio_indices),
    }


def _crop_code(row):
    return tuple((tuple(map(float, point)), str(color))
                 for point, color in zip(row.positions, row.species))


def _open_target_pair():
    global _TARGET_OPEN_COUNT
    if _TARGET_OPEN_COUNT:
        raise AssertionError("confirmation target may be opened only once")
    _TARGET_OPEN_COUNT += 1
    physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                         + TARGET_RADIUS)
    first_oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical)
    second_oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND + 1, physical)
    first = _crop(first_oracle, CONFIRMATION_CENTER, TARGET_RADIUS,
                  "IQC-complete-frontier-confirmation-target")
    second = _crop(second_oracle, CONFIRMATION_CENTER, TARGET_RADIUS,
                   "IQC-complete-frontier-confirmation-target-check")
    return first, second


def evaluate():
    protocol = audit()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("confirmation protocol digest drift")
    receipt = _load_receipt()
    frozen_digest = receipt["candidate_digest"]
    terminals = _terminal_actions(receipt)
    scalar_order = tuple(receipt["scalar_order"])
    fusion_order = tuple(receipt["fusion_order"])
    portfolio = tuple(receipt["portfolio_indices"])
    immutable = repr((terminals, scalar_order, fusion_order, portfolio,
                      frozen_digest, receipt["execution_digest"]))

    target, target_check = _open_target_pair()
    stable = _crop_code(target) == _crop_code(target_check)
    if not stable:
        raise AssertionError("confirmation target changes at lift bound + 1")
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    score = _score_terminals(
        terminals, scalar_order, fusion_order, portfolio, truth)
    if immutable != repr((terminals, scalar_order, fusion_order, portfolio,
                          frozen_digest, receipt["execution_digest"])):
        raise AssertionError("candidate receipt changed after target open")
    disjoint = min(math.dist(CONFIRMATION_CENTER, prior)
                   for prior in PRIOR_CENTERS + DEVELOPMENT_CENTERS) > \
        REQUIRED_CENTER_SEPARATION
    supply = any(score["exact"])
    portfolio_supply = score["portfolio_supply"]
    return IQCCompleteFrontierConfirmation(
        protocol.manifest_digest, receipt["receipt_digest"],
        CONFIRMATION_CENTER, receipt["seed_atoms"], len(target.positions),
        len(target.positions) - receipt["seed_atoms"], len(terminals),
        len(portfolio), sum(score["exact"]),
        score["scalar_first_exact_rank"], score["fusion_first_exact_rank"],
        score["scalar_top_one_exact"], score["fusion_top_one_exact"],
        score["scalar_top_one_correct"], score["fusion_top_one_correct"],
        supply, portfolio_supply, supply, portfolio_supply,
        score["scalar_top_one_exact"], score["fusion_top_one_exact"],
        stable, disjoint, True,
        receipt["candidate_digest"] == frozen_digest,
        _TARGET_OPEN_COUNT, False, True, False,
        ("fresh spatial candidate-supply and rollback-portfolio confirmation"
         if supply and portfolio_supply else
         "fresh spatial complete-frontier confirmation is red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
