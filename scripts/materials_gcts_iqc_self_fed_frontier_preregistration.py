#!/usr/bin/env python3
"""Preregister one self-fed second IQC frontier block before enumeration.

The inherited three-action branch was selected by the frozen fusion order and
serialized before its first target was opened.  This manifest binds that
branch, a larger public radius, the complete second ``8 -> 8 -> 8`` tree, and
separate supply/portfolio/top-one claims.  It imports no oracle, cropper,
candidate builder, target, or scorer.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "9cf541a11b93979ff3fc0fee12d61a62329bd164"
CONFIRMATION_CENTER = (-110., -10., -10.)
ORIGINAL_SEED_RADIUS = 9.0
FIRST_BLOCK_RADIUS = 14.562305898749054
SECOND_BLOCK_RADIUS = FIRST_BLOCK_RADIUS + ORIGINAL_SEED_RADIUS
ORACLE_LIFT_BOUND = 72
ACTION_REACH_SCHEDULE = (8, 8, 8)
DUAL_PORTFOLIO_PER_CHANNEL = 9
MAXIMUM_DUAL_PORTFOLIO_STATES = 18
FIRST_BLOCK_RECEIPT_DIGEST = \
    "b4e7d872d36519cd9415265c8fba65be4de82a166eb852fc086d33ac4ad4f1ae"
FIRST_BLOCK_RESULT_DIGEST = \
    "35abf7d90a05c29ae00c794fd1551b011ec293f04395fc06d32b867a86a81a63"
INHERITED_FUSION_STABLE_INDEX = 101
INHERITED_ACTION_DIGEST = \
    "313f9bd76111605485cc931c813d89e06add54f43bc246c2e0c1d5b2d924c7e8"
FROZEN_MODEL_DIGEST = \
    "505b65481e3fe2cc25a284ba8dc175e3a794465c2c7bd726f5448c1fac6bbef5"
SOURCE_SHA256 = (
    ("materials_gcts_iqc_self_fed_complete_frontier_execution.py",
     "7851ee4313be33db9ac9719e68cb95234967510dc220c12698f89302bcb042fa"),
    ("materials_gcts_iqc_frozen_fusion_runtime.py",
     "2d990643594255484f5e44138bd47509229115a4e62ee133bd8c8f9a049287c9"),
    ("materials_gcts_iqc_complete_terminal_frontier_audit.py",
     "48691c4f997d4f4531016054d4983b3b4c8d20412daa999297c7a08b6b2ec6f4"),
    ("materials_gcts_iqc_complete_frontier_confirmation_execution.py",
     "0ade56391857dc023f99734a509ead6b1b37c32b5440f4f05b8ae9c5036edd67"),
    ("materials_gcts_dual_rank_terminal_portfolio.py",
     "b0074dcbf07138d57f8d82f36597694057e3fe183ce81d2b215bdb22df10fa4a"),
    ("fixtures/iqc_frozen_terminal_fusion_v1.json.bz2",
     "6ab3b23317207577a2805a27f3fa399d312e9c2eefa7d9c858731bd9a456f6d5"),
    ("fixtures/iqc_complete_frontier_confirmation_candidates_v1.json",
     "7727841852ca4688f6ed99557c0e5bb452e4f25117747cd99d3f01520423a5a1"),
)
BOUNDARY_RULE = (
    "retain the confirmed center and extend its public radius by exactly the "
    "original seed radius: R2 = R1 + Rseed"
)
EXECUTION_ORDER = (
    "verify protocol/source/first-receipt hashes; regenerate the original seed "
    "only; replay the frozen fusion-index-101 branch uniquely; use its complete "
    "colored configuration as the second seed; enumerate and serialize every "
    "second-block terminal/order/portfolio; commit that receipt; only then open "
    "the radius-R2 target once at lift bounds 72 and 73; score without refit, "
    "reranking, retry, alternate radius, or alternate inherited branch"
)
SUPPLY_GATE = "the complete second block contains an exact colored terminal"
PORTFOLIO_GATE = (
    "the frozen top-nine scalar/fusion union contains an exact second-block terminal"
)
AUTONOMOUS_GATE = (
    "the frozen fusion top-one second-block terminal is exact; together with the "
    "already pre-target-selected exact inherited branch this certifies six "
    "self-fed actions, but not stationary or exponential growth"
)
EXPECTED_MANIFEST_DIGEST = \
    "a5b35f8cfba26736db4c716fdd837dd7808d7d098e95647dbe45bcb4f9e20631"


@dataclass(frozen=True)
class IQCSelfFedFrontierPreregistration:
    source_commit: str
    confirmation_center: tuple[float, float, float]
    original_seed_radius: float
    first_block_radius: float
    second_block_radius: float
    oracle_lift_bound: int
    action_reach_schedule: tuple[int, ...]
    dual_portfolio_per_channel: int
    maximum_dual_portfolio_states: int
    first_block_receipt_digest: str
    first_block_result_digest: str
    inherited_fusion_stable_index: int
    inherited_action_digest: str
    frozen_model_digest: str
    source_sha256: tuple[tuple[str, str], ...]
    boundary_rule: str
    boundary_rule_reproduced: bool
    execution_order: str
    supply_gate: str
    portfolio_gate: str
    autonomous_gate: str
    oracle_or_cropper_imported: bool
    second_block_candidates_computed: bool
    outer_target_materialized: bool
    manifest_digest: str


def audit():
    for relative, expected in SOURCE_SHA256:
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f"self-fed source drift: {relative}")
    reproduced = math.isclose(
        SECOND_BLOCK_RADIUS, FIRST_BLOCK_RADIUS + ORIGINAL_SEED_RADIUS,
        rel_tol=0., abs_tol=1e-12)
    payload = {
        "source_commit": SOURCE_COMMIT,
        "confirmation_center": CONFIRMATION_CENTER,
        "original_seed_radius": ORIGINAL_SEED_RADIUS,
        "first_block_radius": FIRST_BLOCK_RADIUS,
        "second_block_radius": SECOND_BLOCK_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "action_reach_schedule": ACTION_REACH_SCHEDULE,
        "dual_portfolio_per_channel": DUAL_PORTFOLIO_PER_CHANNEL,
        "maximum_dual_portfolio_states": MAXIMUM_DUAL_PORTFOLIO_STATES,
        "first_block_receipt_digest": FIRST_BLOCK_RECEIPT_DIGEST,
        "first_block_result_digest": FIRST_BLOCK_RESULT_DIGEST,
        "inherited_fusion_stable_index": INHERITED_FUSION_STABLE_INDEX,
        "inherited_action_digest": INHERITED_ACTION_DIGEST,
        "frozen_model_digest": FROZEN_MODEL_DIGEST,
        "source_sha256": SOURCE_SHA256,
        "boundary_rule": BOUNDARY_RULE,
        "boundary_rule_reproduced": reproduced,
        "execution_order": EXECUTION_ORDER,
        "supply_gate": SUPPLY_GATE,
        "portfolio_gate": PORTFOLIO_GATE,
        "autonomous_gate": AUTONOMOUS_GATE,
        "oracle_or_cropper_imported": False,
        "second_block_candidates_computed": False,
        "outer_target_materialized": False,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return IQCSelfFedFrontierPreregistration(*payload.values(), digest)


if __name__ == "__main__":
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))
