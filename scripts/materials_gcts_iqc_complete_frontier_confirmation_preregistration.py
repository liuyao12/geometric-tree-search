#!/usr/bin/env python3
"""Preregister one fresh IQC confirmation of complete terminal supply.

This manifest is geometry-only.  It imports no model-set oracle, cropper,
candidate generator, execution adapter, target, or scorer.  It freezes a new
spatial nucleus, source bytes, bounded tree, dual-rank rollback portfolio, and
separate supply/selection claims before any seed or target atom is generated.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, PRIOR_CENTERS)


SOURCE_COMMIT = "0434a37d311fbc8ed1cd0744d59b48999b8e9bf8"
CONFIRMATION_CENTER = (-110., -10., -10.)
SEED_RADIUS = 9.0
TARGET_RADIUS = 14.562305898749054
ORACLE_LIFT_BOUND = 60
SAFETY_MARGIN = 6.0
REQUIRED_CENTER_SEPARATION = 2. * TARGET_RADIUS + SAFETY_MARGIN
ACTION_REACH_SCHEDULE = (8, 8, 8)
UNPRUNED_FROM_DEPTH = 0
DUAL_PORTFOLIO_PER_CHANNEL = 9
MAXIMUM_DUAL_PORTFOLIO_STATES = 18
FROZEN_MODEL_DIGEST = \
    "505b65481e3fe2cc25a284ba8dc175e3a794465c2c7bd726f5448c1fac6bbef5"
SOURCE_SHA256 = (
    ("materials_gcts_iqc_frozen_fusion_runtime.py",
     "2d990643594255484f5e44138bd47509229115a4e62ee133bd8c8f9a049287c9"),
    ("materials_gcts_iqc_complete_frontier_confirmation_execution.py",
     "0ade56391857dc023f99734a509ead6b1b37c32b5440f4f05b8ae9c5036edd67"),
    ("materials_gcts_dual_rank_terminal_portfolio.py",
     "b0074dcbf07138d57f8d82f36597694057e3fe183ce81d2b215bdb22df10fa4a"),
    ("materials_gcts_iqc_complete_terminal_frontier_audit.py",
     "48691c4f997d4f4531016054d4983b3b4c8d20412daa999297c7a08b6b2ec6f4"),
    ("fixtures/iqc_frozen_terminal_fusion_v1.json.bz2",
     "6ab3b23317207577a2805a27f3fa399d312e9c2eefa7d9c858731bd9a456f6d5"),
    ("fixtures/iqc_complete_frontier_development_audit_v1.json",
     "f00a04ecb1e29653e06352294ce8296b62fa3ebae0422007373afc60b5eba367"),
)
CENTER_SELECTION_RULE = (
    "first lexicographic point in {-110,-90,...,110}^3 with norm <=112 "
    "and distance >2*target_radius+6 from every prior and extended-"
    "development centre"
)
EXECUTION_ORDER = (
    "verify protocol/source hashes; generate seed only; freeze every terminal, "
    "scalar/fusion order, dual portfolio, and receipt digest; serialize receipt; "
    "open target exactly once at lift bounds 60 and 61; score only afterward; "
    "never refit, re-enumerate, rerank, retry, or choose another centre"
)
SUPPLY_GATE = (
    "full frozen tree contains at least one exact colored three-action terminal"
)
PORTFOLIO_GATE = (
    "the frozen top-nine scalar/fusion union contains at least one exact terminal"
)
TOP_ONE_GATE = (
    "report scalar and fusion top-one exactness separately; neither is required "
    "to call candidate supply confirmed"
)
EXPECTED_MANIFEST_DIGEST = \
    "d125a9e724a84f7cffc2e4136e3c5e97bbc4e67ea757eb480c20afe16137b193"


@dataclass(frozen=True)
class IQCCompleteFrontierConfirmationPreregistration:
    source_commit: str
    confirmation_center: tuple[float, float, float]
    seed_radius: float
    target_radius: float
    oracle_lift_bound: int
    safety_margin: float
    required_center_separation: float
    minimum_prior_separation: float
    center_selection_rule: str
    center_selection_reproduced: bool
    target_domain_disjoint: bool
    action_reach_schedule: tuple[int, ...]
    unpruned_from_depth: int
    dual_portfolio_per_channel: int
    maximum_dual_portfolio_states: int
    frozen_model_digest: str
    source_sha256: tuple[tuple[str, str], ...]
    execution_order: str
    supply_gate: str
    portfolio_gate: str
    top_one_gate: str
    oracle_or_cropper_imported: bool
    seed_or_target_materialized: bool
    candidates_or_scores_computed: bool
    manifest_digest: str


def _select_center():
    used = PRIOR_CENTERS + DEVELOPMENT_CENTERS
    for center in itertools.product(range(-110, 111, 20), repeat=3):
        if math.dist((0., 0., 0.), center) > 112.:
            continue
        if min(math.dist(center, prior) for prior in used) <= \
                REQUIRED_CENTER_SEPARATION:
            continue
        return tuple(map(float, center))
    raise AssertionError("no confirmation center satisfies frozen geometry rule")


def audit():
    used = PRIOR_CENTERS + DEVELOPMENT_CENTERS
    separation = min(math.dist(CONFIRMATION_CENTER, prior) for prior in used)
    reproduced = _select_center() == CONFIRMATION_CENTER
    disjoint = separation > REQUIRED_CENTER_SEPARATION and reproduced
    payload = {
        "source_commit": SOURCE_COMMIT,
        "confirmation_center": CONFIRMATION_CENTER,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "safety_margin": SAFETY_MARGIN,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "minimum_prior_separation": separation,
        "center_selection_rule": CENTER_SELECTION_RULE,
        "center_selection_reproduced": reproduced,
        "target_domain_disjoint": disjoint,
        "action_reach_schedule": ACTION_REACH_SCHEDULE,
        "unpruned_from_depth": UNPRUNED_FROM_DEPTH,
        "dual_portfolio_per_channel": DUAL_PORTFOLIO_PER_CHANNEL,
        "maximum_dual_portfolio_states": MAXIMUM_DUAL_PORTFOLIO_STATES,
        "frozen_model_digest": FROZEN_MODEL_DIGEST,
        "source_sha256": SOURCE_SHA256,
        "execution_order": EXECUTION_ORDER,
        "supply_gate": SUPPLY_GATE,
        "portfolio_gate": PORTFOLIO_GATE,
        "top_one_gate": TOP_ONE_GATE,
        "oracle_or_cropper_imported": False,
        "seed_or_target_materialized": False,
        "candidates_or_scores_computed": False,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return IQCCompleteFrontierConfirmationPreregistration(
        *payload.values(), digest)


if __name__ == "__main__":
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))
