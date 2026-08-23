#!/usr/bin/env python3
"""Geometry-only preregistration for a fresh parent-balanced IQC test."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

from materials_gcts_iqc_three_block_portfolio_confirmation_preregistration \
    import PRIOR_CENTERS as EARLIER_PRIOR_CENTERS


GRID_MINIMUM = -360
GRID_MAXIMUM = 360
GRID_STEP = 20
MINIMUM_CENTER_NORM = 220.
MAXIMUM_CENTER_NORM = 360.
SPATIAL_GUARD = 3.
SEED_RADIUS = 9.
FIRST_RADIUS = 14.562305898749054
SECOND_RADIUS = 23.562305898749052
THIRD_RADIUS = 32.56230589874905
FOURTH_RADIUS = 41.56230589874905
FIFTH_RESERVED_RADIUS = 50.56230589874905
MINIMUM_REQUIRED_DOMAIN_SEPARATION = 2 * (
    FIFTH_RESERVED_RADIUS + SPATIAL_GUARD)
EXECUTION_WORKERS = 4
PARENT_WIDTH = 8
TARGET_OPEN_LIMIT = 1
ONE_SHOT_EXECUTION_LIMIT = 1
CONFIRMATION_CENTER = (280., 220., 0.)

# The five fourth-block beam centers are literal here.  One duplicates an
# earlier center and is removed by the deterministic set normalization.
FOURTH_BLOCK_PRIOR_CENTERS = (
    (-70., 10., 70.), (-220., 80., 140.), (20., 220., -160.),
    (160., 20., 220.), (160., -180., -140.))
PRIOR_CENTERS = tuple(sorted(set(
    tuple(map(tuple, EARLIER_PRIOR_CENTERS)) + FOURTH_BLOCK_PRIOR_CENTERS)))

SOURCE_FILE_SHA256 = {
    "materials_gcts_iqc_fresh_parent_balanced_execution.py":
        "a33f9839312213c7c18241ccc5f97668541fa47f4dfa77f39b79bbdbad43bd64",
    "materials_gcts_iqc_bounded_lineage_graph_value.py":
        "5b620746c62c566895ebaebc9f7e0f0034e3a2cef82b3b4bb1f6c8b90c30cb52",
    "materials_gcts_iqc_bounded_lineage_value.py":
        "c9b94f172321d08dfb775885695bdcb0c00390ec8e2853a8e674bb6d92220436",
    "materials_gcts_iqc_fourth_block_parent_balanced_policy.py":
        "26140b933728b27975e091efb41083af9949536edc357102f8d98f31f3b17a2c",
    "materials_gcts_iqc_fourth_block_action_marking.py":
        "0c10fa12803b7a4428ef1a5892d2df7e5d92a26767498157bda917367467a0c0",
    "materials_gcts_iqc_fourth_block_beam.py":
        "4eeb5c7bf3bd836a01a6ff24e609a7e3f5c4a26b4e26a994661d9f4b016de76b",
    "materials_gcts_iqc_three_block_portfolio_execution.py":
        "0eb3477864dbdf2de4496b4b3eb3fe90756054956642b68886aadbef31d9b3e3",
    "materials_gcts_iqc_three_block_channel_execution.py":
        "fb3161d2a4b8bbe7310c0bfbc431c38b5a68a0dae75975355ce68712663f371f",
    "materials_gcts_iqc_three_block_lazy_joint_execution.py":
        "7f323ba9ca7a138b8125e1729fdd4998e27867f1820dd045d9c18d985c052200",
    "materials_gcts_iqc_frozen_fusion_runtime.py":
        "523ec3e9b04cbac00420a5ff008764002e295febc469ba3f6692c56e97b2d9d1",
    "materials_gcts_icosahedral_modelset.py":
        "3270fec8ebd7747546f1dd36b174d8204d9ec295253c0c3933ce6e2765c63044",
    "materials_gcts_joint_prefix_schedule.py":
        "c5ce17d22d3022f8fa269929cdf6075c25a18fd906c48d7f85c6b23a14ba3799",
    "materials_gcts_lineage_continuation.py":
        "29fc79d68d2dcd58956358e571ffb432b2d27baecda953ab92acb8582a783754",
    "materials_gcts_partial_port_graph_lineage_value.py":
        "9d5e0979618c89954604d850580f3b7e46b5826c0c35e6cae1b88faba894b038",
}
PARENT_POLICY_FIXTURE_SHA256 = \
    "1644b8b2e7f67105b144218799f2d8ef21c95998efa4f6d99d7dac20a339807a"
ACTION_MARKING_FIXTURE_SHA256 = \
    "e70e2b2f7401a4127b8f7ba1cd9a1d118376ddc34bfe55f5ea459ff2f0cded6e"
PARENT_POLICY_MODEL_DIGEST = \
    "e1319485581f330ef66b8c9c812978c85f4ecf98bfdcc793376860c1911a1fd6"
ACTION_MARKING_MODEL_DIGEST = \
    "5f30f3424d18194ac3b584a66f16a1d32778206d2ce75e01171e7de0e8be7563"


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def select_confirmation_center():
    rows = []
    for integer in itertools.product(range(
            GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3):
        point = tuple(map(float, integer))
        norm_squared = sum(value * value for value in point)
        if (not MINIMUM_CENTER_NORM ** 2 <= norm_squared <=
                MAXIMUM_CENTER_NORM ** 2
                or point in PRIOR_CENTERS):
            continue
        # All grid and prior coordinates are integer or half-integer. Squared
        # distances are therefore exact binary values; avoiding sqrt removes
        # a cross-runtime tie instability in the maximin center.
        separation_squared = min(sum(
            (point[axis] - prior[axis]) ** 2 for axis in range(3))
            for prior in PRIOR_CENTERS)
        if separation_squared <= MINIMUM_REQUIRED_DOMAIN_SEPARATION ** 2:
            continue
        rows.append((separation_squared, -norm_squared,
                     tuple(-value for value in point), point))
    if not rows:
        raise AssertionError("empty parent-balanced fresh-center grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 1,
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
    "source_file_sha256": SOURCE_FILE_SHA256,
    "parent_policy_fixture_sha256": PARENT_POLICY_FIXTURE_SHA256,
    "action_marking_fixture_sha256": ACTION_MARKING_FIXTURE_SHA256,
    "parent_policy_model_digest": PARENT_POLICY_MODEL_DIGEST,
    "action_marking_model_digest": ACTION_MARKING_MODEL_DIGEST,
    "target_order": (
        "validate manifest and source hashes",
        "open the seed exactly once",
        "freeze complete three-block parents and width-eight fourth children",
        "serialize the target-blind receipt",
        "open the fourth-radius target exactly once",
        "score without refit, rerank, retry, or further execution",
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
    "e9094088dea2870b4d84121c09eba2c97761736d7b3fcf254b6b8ca290925d69"


def source_file_digests(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in SOURCE_FILE_SHA256}


def validate_preregistration(*, verify_sources=True):
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    reproduced = select_confirmation_center()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (reproduced != CONFIRMATION_CENTER
            or separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION
            or CONFIRMATION_CENTER in PRIOR_CENTERS
            or MANIFEST["winner_selected_or_validated"]
            or MANIFEST["autonomous_growth_claimed"]
            or MANIFEST["stationary_or_exponential_claimed"]
            or MANIFEST["rerun_or_fallback_after_scoring_allowed"]
            or (EXPECTED_MANIFEST_DIGEST and
                digest != EXPECTED_MANIFEST_DIGEST)):
        raise AssertionError("parent-balanced preregistration drift")
    if verify_sources and source_file_digests() != SOURCE_FILE_SHA256:
        raise AssertionError("parent-balanced source hash drift")
    return digest


class OneShotOrderGuard:
    """Enforce protocol -> seed -> receipt -> target -> score exactly once."""

    def __init__(self):
        self.state = "created"
        self.seed_open_count = 0
        self.target_open_count = 0
        self.score_count = 0
        self.receipt_digest = None

    def protocol_verified(self):
        if self.state != "created":
            raise RuntimeError("protocol verification order violation")
        validate_preregistration()
        self.state = "protocol-verified"

    def seed_opened(self):
        if self.state != "protocol-verified" or self.seed_open_count:
            raise RuntimeError("fresh seed order violation")
        self.seed_open_count += 1
        self.state = "seed-opened"

    def receipt_frozen(self, digest):
        if (self.state != "seed-opened" or not isinstance(digest, str) or
                len(digest) != 64):
            raise RuntimeError("receipt freeze order violation")
        int(digest, 16)
        self.receipt_digest = digest
        self.state = "receipt-frozen"

    def target_opened(self):
        if self.state != "receipt-frozen" or self.target_open_count:
            raise RuntimeError("fresh target order violation")
        self.target_open_count += 1
        self.state = "target-opened"

    def scored(self, unchanged_receipt_digest):
        if (self.state != "target-opened" or self.score_count or
                unchanged_receipt_digest != self.receipt_digest):
            raise RuntimeError("post-target scoring order violation")
        self.score_count += 1
        self.state = "scored"

    def audit(self):
        return {
            "state": self.state,
            "seed_open_count": self.seed_open_count,
            "target_open_count": self.target_open_count,
            "score_count": self.score_count,
            "receipt_digest": self.receipt_digest,
        }


if __name__ == "__main__":
    print(validate_preregistration())
