#!/usr/bin/env python3
"""Freeze the next autonomous IQC nucleus and recurrent branch policy.

This module performs no oracle, seed, candidate, or target construction.  It
commits the geometry-only nucleus, training artifacts, bounded search, value
model, target-open order, and posthoc gate before the new material is touched.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_pose_port_autonomous_preregistration_v2 import (
    MINIMUM_STATE_GROUPS, MINIMUM_STATE_SUPPORT, MINIMUM_TOKEN_GROUPS,
    MINIMUM_TOKEN_SUPPORT, SEED_RADIUS, STATE_BIN_WIDTH, TARGET_RADIUS,
    TOKEN_SHRINKAGE, UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_recurrent_branch_value_audit import (
    EXPECTED_CANDIDATE_DIGEST, EXPECTED_MODEL_DIGEST,
    FIXTURE as DEVELOPMENT_FIXTURE, evaluate as value_audit)


SOURCE_COMMIT = "e7bb3a1b16c7ece4a5850198ed69b5a310dba1c6"
CONFIRMATION_CENTER = (40., -40., -80.)
ORACLE_LIFT_BOUND = 44
BEAM_WIDTH = 4
ACTION_REACH_PER_CONFIGURATION = 4
SEARCH_DEPTH = 3
BRANCH_NEIGHBORS = 9
REQUIRED_CENTER_SEPARATION = 2. * TARGET_RADIUS
CENTER_SELECTION_RULE = (
    "maximize minimum Euclidean separation from the 30 frozen development "
    "centres and consumed centre over the 20-unit grid in [-100,100]^3 "
    "with radial norm in [75,105], breaking ties reverse lexicographically"
)
SEARCH_RULE = (
    "at each of three depths retain four complete configurations; each "
    "configuration expands its four highest frozen pose-port state actions; "
    "after depth three rank the immutable terminal configurations once by "
    "the frozen k=9 nearest-recurrent branch value"
)
TARGET_OPEN_RULE = (
    "construct and hash seed, candidates, terminal branch features, model, "
    "scores, selected branch, and complete trace before one target-factory "
    "call; afterward perform pure position/species scoring and never refit, "
    "rerank, or execute again"
)
ORACLE_STABILITY_RULE = (
    "the one target-factory call constructs coefficient bounds 44 and 45 "
    "and fails unless the detached radius target crops agree exactly"
)
POSTHOC_GATE = (
    "bound crops stable; exactly one target open; target absent from fit, "
    "candidates, branch features, ranking, and execution; selected depth-three "
    "branch has 3/3 exact colored sites and zero false sites"
)
SOURCE_FILE_HASHES = (
    ("materials_gcts_recurrent_branch_value.py",
     "dcbac5886f131ef01c81b3753107ac1cf44e41b093e20ffcf4595287d2d91a2f"),
    ("materials_gcts_iqc_recurrent_branch_value_audit.py",
     "d0ba8d3520173be52cc5ddc17acbdbc695af1486bdfd2b0e947c9952cd615794"),
    ("fixtures/iqc_recurrent_branch_value_training.json",
     "29621eff182f4b7ff5d5f23f695fc96cb21356545ca22b388188062daf18a9f9"),
    ("materials_gcts_iqc_pose_port_state_audit.py",
     "754dbdc374d530cb72c346de80bba9af7fbee4e81b8cab072c6d8934cd724ad0"),
    ("materials_gcts_pose_port_state_marking.py",
     "7dcd4cb7d95c4a793a0cabd0b3204817a2dc8aa9998caa0356d32ce246d77a6f"),
)


@dataclass(frozen=True)
class IQCRecurrentBranchAutonomousPreregistration:
    source_commit: str
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
    expected_development_candidate_digest: str
    expected_branch_model_digest: str
    branch_neighbors: int
    beam_width: int
    action_reach_per_configuration: int
    search_depth: int
    search_rule: str
    target_open_rule: str
    oracle_stability_rule: str
    posthoc_gate: str
    source_file_hashes: tuple[tuple[str, str], ...]
    source_hashes_match: bool
    development_gate_passed: bool
    seed_or_target_materialized: bool
    candidate_or_score_computed: bool
    manifest_digest: str


def _hash(filename):
    return hashlib.sha256((Path(__file__).resolve().parent /
                           filename).read_bytes()).hexdigest()


def audit() -> IQCRecurrentBranchAutonomousPreregistration:
    development = value_audit()
    payload = json.loads(DEVELOPMENT_FIXTURE.read_text())
    prior_centers = tuple(tuple(center)
                          for center in payload["development_centers"]) + \
        ((-50., 50., -10.),)
    separation = min(math.dist(CONFIRMATION_CENTER, center)
                     for center in prior_centers)
    hashes_match = all(_hash(filename) == digest
                       for filename, digest in SOURCE_FILE_HASHES)
    values = {
        "source_commit": SOURCE_COMMIT,
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
        "expected_development_candidate_digest": EXPECTED_CANDIDATE_DIGEST,
        "expected_branch_model_digest": EXPECTED_MODEL_DIGEST,
        "branch_neighbors": BRANCH_NEIGHBORS,
        "beam_width": BEAM_WIDTH,
        "action_reach_per_configuration": ACTION_REACH_PER_CONFIGURATION,
        "search_depth": SEARCH_DEPTH,
        "search_rule": SEARCH_RULE,
        "target_open_rule": TARGET_OPEN_RULE,
        "oracle_stability_rule": ORACLE_STABILITY_RULE,
        "posthoc_gate": POSTHOC_GATE,
        "source_file_hashes": SOURCE_FILE_HASHES,
        "source_hashes_match": hashes_match,
        "development_gate_passed": development.development_gate_passed,
        "seed_or_target_materialized": False,
        "candidate_or_score_computed": False,
    }
    digest = hashlib.sha256(json.dumps(
        values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return IQCRecurrentBranchAutonomousPreregistration(
        *values.values(), digest)


def main():
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
