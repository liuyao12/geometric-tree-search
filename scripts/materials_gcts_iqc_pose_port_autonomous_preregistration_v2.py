#!/usr/bin/env python3
"""Freeze the replacement autonomous IQC nucleus after attempt one failed."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_pose_port_autonomous_attempt_status import (
    audit as attempt_status)
from materials_gcts_iqc_pose_port_autonomous_preregistration import (
    ACTION_REACH_PER_CONFIGURATION, BEAM_WIDTH, BRANCH_VALUE,
    CONFIRMATION_CENTER as CONSUMED_CENTER, EXPECTED_DEVELOPMENT_CANDIDATE_DIGEST,
    EXPECTED_MODEL_DIGEST, MINIMUM_STATE_GROUPS, MINIMUM_STATE_SUPPORT,
    MINIMUM_TOKEN_GROUPS, MINIMUM_TOKEN_SUPPORT, POSTHOC_GATE, PRIOR_CENTERS,
    REQUIRED_CENTER_SEPARATION, SEARCH_DEPTH, SEED_RADIUS, SOURCE_COMMIT,
    SOURCE_FILE_HASHES, STATE_BIN_WIDTH, TARGET_OPEN_RULE, TARGET_RADIUS,
    TOKEN_SHRINKAGE, UPSTREAM_ANGULAR_BIN_WIDTH)


CONFIRMATION_CENTER = (-50., 50., -10.)
ORACLE_LIFT_BOUND = 32
EXPECTED_ATTEMPT_STATUS_DIGEST = \
    "358f45bfc0b0ce2fc4fe02a03462a86abee91044f0f59f9e3e48668ac9034085"
CENTER_SELECTION_RULE = (
    "minimum Euclidean norm then lexicographic point in "
    "{-70,-50,-30,-10,10,30,50,70}^3 inside radius 105, farther than 36 "
    "from every prior development, consumed confirmation, and failed-attempt "
    "center"
)
ORACLE_STABILITY_RULE = (
    "seed and target crops use lift bound 32; the single target-factory call "
    "also constructs bound 33 and fails unless detached crops agree"
)


@dataclass(frozen=True)
class IQCPosePortAutonomousPreregistrationV2:
    source_commit: str
    prior_attempt_status_digest: str
    prior_attempt_consumed_unknown: bool
    confirmation_center: tuple[float, float, float]
    seed_radius: float
    target_radius: float
    oracle_lift_bound: int
    required_center_separation: float
    minimum_prior_center_separation: float
    domains_disjoint: bool
    center_selection_rule: str
    upstream_angular_bin_width: float
    state_bin_width: float
    minimum_token_support: int
    minimum_token_groups: int
    token_shrinkage: float
    minimum_state_support: int
    minimum_state_groups: int
    expected_model_digest: str
    expected_development_candidate_digest: str
    beam_width: int
    action_reach_per_configuration: int
    search_depth: int
    branch_value: str
    target_open_rule: str
    oracle_stability_rule: str
    posthoc_gate: str
    source_file_hashes: tuple[tuple[str, str], ...]
    source_hashes_match: bool
    seed_or_target_materialized: bool
    candidate_or_score_computed: bool
    manifest_digest: str


def _actual_hash(filename: str) -> str:
    return hashlib.sha256((Path(__file__).resolve().parent /
                           filename).read_bytes()).hexdigest()


def audit() -> IQCPosePortAutonomousPreregistrationV2:
    prior_status = attempt_status()
    if prior_status.status_digest != EXPECTED_ATTEMPT_STATUS_DIGEST:
        raise AssertionError("prior autonomous-attempt status drift")
    prior = PRIOR_CENTERS + (CONSUMED_CENTER,)
    separation = min(math.dist(CONFIRMATION_CENTER, center)
                     for center in prior)
    hashes_match = all(_actual_hash(filename) == digest
                       for filename, digest in SOURCE_FILE_HASHES)
    payload = {
        "source_commit": SOURCE_COMMIT,
        "prior_attempt_status_digest": prior_status.status_digest,
        "prior_attempt_consumed_unknown":
            not prior_status.same_nucleus_retry_permitted,
        "confirmation_center": CONFIRMATION_CENTER,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "minimum_prior_center_separation": separation,
        "domains_disjoint": separation > REQUIRED_CENTER_SEPARATION,
        "center_selection_rule": CENTER_SELECTION_RULE,
        "upstream_angular_bin_width": UPSTREAM_ANGULAR_BIN_WIDTH,
        "state_bin_width": STATE_BIN_WIDTH,
        "minimum_token_support": MINIMUM_TOKEN_SUPPORT,
        "minimum_token_groups": MINIMUM_TOKEN_GROUPS,
        "token_shrinkage": TOKEN_SHRINKAGE,
        "minimum_state_support": MINIMUM_STATE_SUPPORT,
        "minimum_state_groups": MINIMUM_STATE_GROUPS,
        "expected_model_digest": EXPECTED_MODEL_DIGEST,
        "expected_development_candidate_digest":
            EXPECTED_DEVELOPMENT_CANDIDATE_DIGEST,
        "beam_width": BEAM_WIDTH,
        "action_reach_per_configuration": ACTION_REACH_PER_CONFIGURATION,
        "search_depth": SEARCH_DEPTH,
        "branch_value": BRANCH_VALUE,
        "target_open_rule": TARGET_OPEN_RULE,
        "oracle_stability_rule": ORACLE_STABILITY_RULE,
        "posthoc_gate": POSTHOC_GATE,
        "source_file_hashes": SOURCE_FILE_HASHES,
        "source_hashes_match": hashes_match,
        "seed_or_target_materialized": False,
        "candidate_or_score_computed": False,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return IQCPosePortAutonomousPreregistrationV2(
        *payload.values(), digest)


def main():
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
