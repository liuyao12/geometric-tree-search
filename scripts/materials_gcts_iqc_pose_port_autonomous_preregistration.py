#!/usr/bin/env python3
"""Freeze a new autonomous IQC pose-port confirmation before materializing it.

This manifest contains protocol metadata only.  It imports no oracle, cropper,
candidate generator, marking fitter, executor, or scorer.  The confirmation
nucleus must remain unopened until this file and its source hashes are
committed.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


SOURCE_COMMIT = "b7356f82d7c085f9f5a6b4bb683bf5b597533b2b"
CONFIRMATION_CENTER = (-70., -70., 30.)
SEED_RADIUS = 9.
TARGET_RADIUS = 14.562305898749054
ORACLE_LIFT_BOUND = 24
REQUIRED_CENTER_SEPARATION = 2. * TARGET_RADIUS
PRIOR_CENTERS = (
    (0., 0., 0.), (30., 0., 0.), (18., 25., 14.),
    (-20., 20., 20.), (20., -25., 20.), (-20., -20., -25.),
    (-25., 20., -20.), (-25., -20., 20.), (30., -25., -20.),
    (0., 0., -50.), (0., 50., 0.),
    (10., 30., -30.), (10., 10., 50.), (50., 10., -30.),
    (50., 10., 30.), (-70., -10., -10.), (-50., -50., -10.),
    (-50., -10., -50.), (-50., -10., 50.),
)
CENTER_SELECTION_RULE = (
    "lexicographically first point in {-70,-50,-30,-10,10,30,50,70}^3 "
    "inside radius 105 and farther than 36 from every prior development or "
    "consumed confirmation center"
)
UPSTREAM_ANGULAR_BIN_WIDTH = .125
STATE_BIN_WIDTH = 1.
MINIMUM_TOKEN_SUPPORT = 4
MINIMUM_TOKEN_GROUPS = 2
TOKEN_SHRINKAGE = .5
MINIMUM_STATE_SUPPORT = 8
MINIMUM_STATE_GROUPS = 2
EXPECTED_MODEL_DIGEST = \
    "9b83898155f5d729499c441bcbafa6491b553196fe87de756cb6281b8b856b13"
EXPECTED_DEVELOPMENT_CANDIDATE_DIGEST = \
    "a241b449374deadd73ff32fc48f45c87412e0fa8073c6fac35848e5bc5e785b4"
BEAM_WIDTH = 4
ACTION_REACH_PER_CONFIGURATION = 4
SEARCH_DEPTH = 3
BRANCH_VALUE = (
    "sum log frozen pose-port state probability; stable ties by raw frozen "
    "vote multiplicity, candidate point, then configuration action tuple"
)
TARGET_OPEN_RULE = (
    "fit and hash the unchanged ten-nucleus model; materialize only the new "
    "seed; execute and serialize all depth-three beam candidates, selected "
    "branch, sites, and digests; only then open the outer target exactly once"
)
ORACLE_STABILITY_RULE = (
    "seed and target crops use lift bound 24; the single target-factory call "
    "also constructs bound 25 and fails unless the two detached crops agree"
)
POSTHOC_GATE = (
    "selected depth-three branch emits three novel sites and all three match "
    "the opened target in coordinate and species with zero false sites"
)
SOURCE_FILE_HASHES = (
    ("materials_gcts_pose_port_state_marking.py",
     "7dcd4cb7d95c4a793a0cabd0b3204817a2dc8aa9998caa0356d32ce246d77a6f"),
    ("materials_gcts_iqc_pose_port_state_audit.py",
     "754dbdc374d530cb72c346de80bba9af7fbee4e81b8cab072c6d8934cd724ad0"),
    ("materials_gcts_incidence_token_marking.py",
     "6851cadc59c06208e80349c39d54f5da05100eac09fefe61285c9d5f47c54dd0"),
    ("materials_gcts_persistent_frontier_beam.py",
     "5ef42a59cce1c5658b9d7b96eb32b6ecbde90e8eab5bedad6c74567baaba9020"),
    ("materials_gcts_iqc_recurrent_prototype_connection_audit.py",
     "29db1548af9f4d8320b953a9dfc2f55cef78cfdc6a093ddf2ed99a94740a71a6"),
    ("materials_gcts_iqc_expanded_development_baseline.py",
     "9e454dbe21bd24314d97ee664222a613f1cef55c41e7bd108e4d826412474b41"),
    ("materials_gcts_icosahedral_modelset.py",
     "4b26fdc72051f7cafba9fd4bd8ea7ab2778dba5344373d668f19f8442365315a"),
)


@dataclass(frozen=True)
class IQCPosePortAutonomousPreregistration:
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


def audit() -> IQCPosePortAutonomousPreregistration:
    separation = min(math.dist(CONFIRMATION_CENTER, center)
                     for center in PRIOR_CENTERS)
    hashes_match = all(_actual_hash(filename) == digest
                       for filename, digest in SOURCE_FILE_HASHES)
    payload = {
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
    return IQCPosePortAutonomousPreregistration(
        SOURCE_COMMIT, CONFIRMATION_CENTER, SEED_RADIUS, TARGET_RADIUS,
        ORACLE_LIFT_BOUND,
        REQUIRED_CENTER_SEPARATION, separation,
        separation > REQUIRED_CENTER_SEPARATION, CENTER_SELECTION_RULE,
        UPSTREAM_ANGULAR_BIN_WIDTH, STATE_BIN_WIDTH, MINIMUM_TOKEN_SUPPORT,
        MINIMUM_TOKEN_GROUPS, TOKEN_SHRINKAGE, MINIMUM_STATE_SUPPORT,
        MINIMUM_STATE_GROUPS, EXPECTED_MODEL_DIGEST,
        EXPECTED_DEVELOPMENT_CANDIDATE_DIGEST, BEAM_WIDTH,
        ACTION_REACH_PER_CONFIGURATION, SEARCH_DEPTH, BRANCH_VALUE,
        TARGET_OPEN_RULE, ORACLE_STABILITY_RULE, POSTHOC_GATE,
        SOURCE_FILE_HASHES, hashes_match,
        False, False, digest)


def main():
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
