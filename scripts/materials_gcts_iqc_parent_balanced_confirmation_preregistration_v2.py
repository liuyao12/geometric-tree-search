#!/usr/bin/env python3
"""Second geometry-only preregistration after the consumed scorer failure."""

from __future__ import annotations

import hashlib
import itertools
import math
from pathlib import Path

from materials_gcts_iqc_parent_balanced_confirmation_preregistration import (
    ACTION_MARKING_FIXTURE_SHA256, ACTION_MARKING_MODEL_DIGEST,
    EXECUTION_WORKERS, FIFTH_RESERVED_RADIUS, FIRST_RADIUS, FOURTH_RADIUS,
    GRID_MAXIMUM, GRID_MINIMUM, GRID_STEP, MANIFEST as V1_MANIFEST,
    MAXIMUM_CENTER_NORM, MINIMUM_CENTER_NORM,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, PARENT_POLICY_FIXTURE_SHA256,
    PARENT_POLICY_MODEL_DIGEST, PARENT_WIDTH, PRIOR_CENTERS as V1_PRIORS,
    SECOND_RADIUS, SEED_RADIUS, SOURCE_FILE_SHA256 as V1_SOURCE_FILE_SHA256,
    SPATIAL_GUARD, THIRD_RADIUS, canonical_json)


FAILED_V1_CENTER = tuple(V1_MANIFEST["confirmation_center"])
PRIOR_CENTERS = tuple(sorted(set(V1_PRIORS + (FAILED_V1_CENTER,))))
CONFIRMATION_CENTER = (-280., 160., -160.)
TARGET_OPEN_LIMIT = 1
ONE_SHOT_EXECUTION_LIMIT = 1
POSITION_TOLERANCE = 1e-5

SOURCE_FILE_SHA256 = dict(V1_SOURCE_FILE_SHA256) | {
    "materials_gcts_iqc_fresh_parent_balanced_execution_v2.py":
        "3e968051994ae8cf9fa286c1fe4914b85b0f9aebe86b1f56e09ad11f32258fca",
    "materials_gcts_colored_position_scorer.py":
        "9e4e7122263abeb5e66953f738f4e815bf1fa5ba28df0d7704812cec962373f8",
    "materials_gcts_iqc_parent_balanced_confirmation_preregistration.py":
        "4d24181951b46bd4f01e4ac55de3362a2571331b6eb508a5677a71a0e0be48e3",
}


def select_confirmation_center():
    rows = []
    for integer in itertools.product(range(
            GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3):
        point = tuple(map(float, integer))
        norm_squared = sum(value * value for value in point)
        if (not MINIMUM_CENTER_NORM ** 2 <= norm_squared <=
                MAXIMUM_CENTER_NORM ** 2 or point in PRIOR_CENTERS):
            continue
        separation_squared = min(sum(
            (point[axis] - prior[axis]) ** 2 for axis in range(3))
            for prior in PRIOR_CENTERS)
        if separation_squared <= MINIMUM_REQUIRED_DOMAIN_SEPARATION ** 2:
            continue
        rows.append((separation_squared, -norm_squared,
                     tuple(-value for value in point), point))
    if not rows:
        raise AssertionError("empty second parent-balanced center grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 2,
    "reason_for_new_nucleus":
        "v1 target consumed by an eight-decimal exact-lookup scorer bug",
    "v1_target_reopened_or_rescored": False,
    "v1_center_added_to_prior_domains": True,
    "geometry_rule": "literal-prior-center maximin grid",
    "grid": (GRID_MINIMUM, GRID_MAXIMUM, GRID_STEP),
    "center_norm_interval": (MINIMUM_CENTER_NORM, MAXIMUM_CENTER_NORM),
    "prior_centers": PRIOR_CENTERS,
    "confirmation_center": CONFIRMATION_CENTER,
    "spatial_guard": SPATIAL_GUARD,
    "minimum_required_domain_separation":
        MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    "radii": (SEED_RADIUS, FIRST_RADIUS, SECOND_RADIUS, THIRD_RADIUS,
              FOURTH_RADIUS),
    "fifth_reserved_radius": FIFTH_RESERVED_RADIUS,
    "workers": EXECUTION_WORKERS,
    "parent_width": PARENT_WIDTH,
    "position_scorer": {
        "kind": "species-aware finite-distance matcher",
        "tolerance": POSITION_TOLERANCE,
        "scorer_source": "materials_gcts_colored_position_scorer.py",
    },
    "source_file_sha256": SOURCE_FILE_SHA256,
    "parent_policy_fixture_sha256": PARENT_POLICY_FIXTURE_SHA256,
    "action_marking_fixture_sha256": ACTION_MARKING_FIXTURE_SHA256,
    "parent_policy_model_digest": PARENT_POLICY_MODEL_DIGEST,
    "action_marking_model_digest": ACTION_MARKING_MODEL_DIGEST,
    "target_order": (
        "validate v2 manifest, source hashes, and tolerant scorer",
        "open the second fresh seed exactly once",
        "freeze the parallel parent-balanced 512-candidate receipt",
        "serialize the target-blind receipt",
        "open the fourth-radius target exactly once",
        "score with frozen 1e-5 matcher without refit or retry",
    ),
    "target_open_limit": TARGET_OPEN_LIMIT,
    "one_shot_execution_limit": ONE_SHOT_EXECUTION_LIMIT,
    "success_gate": {
        "target_used_for_execution": False,
        "target_open_count": 1,
        "all_parent_lineages_retain_width_eight": True,
        "exact_four_block_candidates_minimum": 1,
        "receipt_unchanged_after_target": True,
        "domain_separation_reserves_fifth_radius": True,
    },
    "claim_if_gate_passes":
        "fresh parent-balanced exact fourth-block candidate supply",
    "winner_selected_or_validated": False,
    "autonomous_growth_claimed": False,
    "stationary_or_exponential_claimed": False,
    "rerun_or_fallback_after_scoring_allowed": False,
}
EXPECTED_MANIFEST_DIGEST = \
    "fd7c67850219353d01eca752c278a2bf210b69d239252d4bbb2a7df37edb1a77"


def source_file_digests(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in SOURCE_FILE_SHA256}


def validate_preregistration(*, verify_sources=True):
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (select_confirmation_center() != CONFIRMATION_CENTER or
            FAILED_V1_CENTER not in PRIOR_CENTERS or
            separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION or
            MANIFEST["v1_target_reopened_or_rescored"] or
            MANIFEST["winner_selected_or_validated"] or
            MANIFEST["autonomous_growth_claimed"] or
            MANIFEST["stationary_or_exponential_claimed"] or
            MANIFEST["rerun_or_fallback_after_scoring_allowed"] or
            (EXPECTED_MANIFEST_DIGEST and
             digest != EXPECTED_MANIFEST_DIGEST)):
        raise AssertionError("second parent-balanced preregistration drift")
    if verify_sources and source_file_digests() != SOURCE_FILE_SHA256:
        raise AssertionError("second parent-balanced source hash drift")
    return digest


class OneShotOrderGuard:
    def __init__(self):
        self.state = "created"
        self.seed_open_count = 0
        self.target_open_count = 0
        self.score_count = 0
        self.receipt_digest = None

    def protocol_verified(self):
        if self.state != "created":
            raise RuntimeError("v2 protocol order violation")
        validate_preregistration()
        self.state = "protocol-verified"

    def seed_opened(self):
        if self.state != "protocol-verified" or self.seed_open_count:
            raise RuntimeError("v2 seed order violation")
        self.seed_open_count += 1
        self.state = "seed-opened"

    def receipt_frozen(self, digest):
        if (self.state != "seed-opened" or not isinstance(digest, str) or
                len(digest) != 64):
            raise RuntimeError("v2 receipt order violation")
        int(digest, 16)
        self.receipt_digest = digest
        self.state = "receipt-frozen"

    def target_opened(self):
        if self.state != "receipt-frozen" or self.target_open_count:
            raise RuntimeError("v2 target order violation")
        self.target_open_count += 1
        self.state = "target-opened"

    def scored(self, digest):
        if (self.state != "target-opened" or self.score_count or
                digest != self.receipt_digest):
            raise RuntimeError("v2 score order violation")
        self.score_count += 1
        self.state = "scored"

    def audit(self):
        return {"state": self.state,
                "seed_open_count": self.seed_open_count,
                "target_open_count": self.target_open_count,
                "score_count": self.score_count,
                "receipt_digest": self.receipt_digest}


if __name__ == "__main__":
    print(validate_preregistration())
