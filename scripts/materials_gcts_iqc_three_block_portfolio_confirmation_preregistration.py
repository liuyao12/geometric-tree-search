#!/usr/bin/env python3
"""Immutable preregistration for one fresh three-block IQC portfolio test.

This file is deliberately geometry- and protocol-only.  It imports no IQC
oracle, cropper, executor, scorer, or learned runtime.  The confirmation center
is the deterministic maximin point of a finite public grid after excluding the
86 literal centers used by earlier IQC development or confirmation work.

The protocol tests *candidate supply*: a bounded target-blind GCTS portfolio
must contain an exact nine-action (three actions per block) lineage on a fresh
nucleus.  It does not select a winner and therefore cannot establish
autonomous, stationary, or exponential growth by itself.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path


SOURCE_COMMIT = "800285b59ce65631d8c0da5c1e0d3ae01d6da18c"
GRID_MINIMUM = -280
GRID_MAXIMUM = 280
GRID_STEP = 20
MINIMUM_CENTER_NORM = 180.
MAXIMUM_CENTER_NORM = 280.
SPATIAL_GUARD = 3.
SEED_RADIUS = 9.
FIRST_BLOCK_RADIUS = 14.562305898749054
SECOND_BLOCK_RADIUS = 23.562305898749052
THIRD_BLOCK_RADIUS = 32.56230589874905
MINIMUM_REQUIRED_DOMAIN_SEPARATION = 2 * (
    THIRD_BLOCK_RADIUS + SPATIAL_GUARD)
EXECUTION_WORKERS = 4
FIRST_PARENT_WIDTH = 8
SECOND_OPTION_TOP_K = 8
SECOND_PARENT_WIDTH = 4
CHANNEL_NAMES = ("base", "colored", "ports", "coupled")
EXPECTED_ACTIONS_PER_BLOCK = 3
EXPECTED_LINEAGE_ACTIONS = 9
TARGET_OPEN_LIMIT = 1
ONE_SHOT_EXECUTION_LIMIT = 1
CONFIRMATION_CENTER = (-220., 80., 140.)

# Literal snapshot collected before selecting CONFIRMATION_CENTER.  The fresh
# protocol never discovers prior centers dynamically, which would make later
# source edits silently move the test location.
PRIOR_CENTERS = (
    (-140.0, -200.0, 80.0), (-140.0, -20.0, 40.0),
    (-140.0, 0.0, -60.0), (-140.0, 60.0, 0.0),
    (-110.0, -70.0, -70.0), (-110.0, -10.0, -10.0),
    (-80.0, -60.0, 120.0), (-80.0, 120.0, 60.0),
    (-70.0, -70.0, 30.0), (-70.0, -10.0, -10.0),
    (-70.0, 10.0, 70.0), (-70.0, 30.0, -50.0),
    (-60.0, -140.0, -40.0), (-60.0, 40.0, -140.0),
    (-60.0, 40.0, 40.0), (-60.0, 40.0, 140.0),
    (-60.0, 140.0, -40.0), (-50.0, -50.0, -10.0),
    (-50.0, -10.0, -50.0), (-50.0, -10.0, 50.0),
    (-50.0, 0.0, 0.0), (-50.0, 50.0, -10.0),
    (-25.0, -20.0, 20.0), (-25.0, 20.0, -20.0),
    (-20.0, -80.0, 20.0), (-20.0, -60.0, -60.0),
    (-20.0, -60.0, 60.0), (-20.0, -20.0, -25.0),
    (-20.0, 20.0, 20.0), (-20.0, 60.0, -60.0),
    (-20.0, 60.0, 60.0), (-18.5, -1.5, 1.5),
    (-17.5, 2.5, -1.5), (-16.0, 0.0, 0.0),
    (-14.5, -2.5, -1.5), (-13.5, 1.5, 1.5),
    (-10.0, -10.0, -90.0), (-10.0, -10.0, 90.0),
    (-4.0, 20.0, 0.0), (0.0, -120.0, -160.0),
    (0.0, -80.0, -20.0), (0.0, -50.0, 0.0),
    (0.0, 0.0, -50.0), (0.0, 0.0, 0.0),
    (0.0, 0.0, 50.0), (0.0, 8.0, -20.0),
    (0.0, 8.0, 20.0), (0.0, 50.0, 0.0),
    (0.0, 80.0, 0.0), (8.0, -12.0, -12.0),
    (8.0, -12.0, 12.0), (10.0, 10.0, 50.0),
    (10.0, 30.0, -70.0), (10.0, 30.0, -30.0),
    (16.0, 8.0, -4.0), (18.0, 25.0, 14.0),
    (20.0, -25.0, 20.0), (20.0, 20.0, -25.0),
    (20.0, 60.0, 140.0), (30.0, -70.0, -50.0),
    (30.0, -25.0, -20.0), (30.0, 0.0, 0.0),
    (30.0, 50.0, 50.0), (30.0, 70.0, -50.0),
    (40.0, -140.0, 60.0), (40.0, -60.0, 140.0),
    (40.0, -40.0, -80.0), (40.0, -40.0, 60.0),
    (40.0, 60.0, -140.0), (40.0, 140.0, 60.0),
    (50.0, 10.0, -70.0), (50.0, 10.0, -30.0),
    (50.0, 10.0, 30.0), (50.0, 10.0, 70.0),
    (50.0, 50.0, 0.0), (60.0, -140.0, -20.0),
    (60.0, -60.0, 20.0), (60.0, 60.0, 0.0),
    (60.0, 140.0, -20.0), (70.0, -50.0, -30.0),
    (80.0, -20.0, 0.0), (120.0, -60.0, 80.0),
    (120.0, -40.0, -220.0), (140.0, -40.0, -60.0),
    (140.0, 40.0, -60.0), (140.0, 40.0, 60.0),
)

SOURCE_FILE_SHA256 = {
    "materials_gcts_equivariant_port_fusion_value.py":
        "ab5fec4f6e572dc3a5324c5692d7ba7b1cecb40f8899b3aef6cc3e4687642559",
    "materials_gcts_iqc_frozen_fusion_artifact.py":
        "2026a624e03f599573501b27daa373302cd264f96afa6369313354063669fde9",
    "materials_gcts_iqc_frozen_fusion_runtime.py":
        "2d990643594255484f5e44138bd47509229115a4e62ee133bd8c8f9a049287c9",
    "materials_gcts_iqc_self_fed_complete_frontier_execution.py":
        "7851ee4313be33db9ac9719e68cb95234967510dc220c12698f89302bcb042fa",
    "materials_gcts_iqc_three_block_channel_execution.py":
        "a72a3817191f324225c595b08d5e68bd796f6d12f6092030d09eb9a23f2f0390",
    "materials_gcts_clusters2_future_option.py":
        "968993861553f3f5d2e14f22e9c20428b8cfd3044eab1fed797ac89fb5797987",
    "materials_gcts_recurrent_branch_value.py":
        "dcbac5886f131ef01c81b3753107ac1cf44e41b093e20ffcf4595287d2d91a2f",
    "materials_gcts_iqc_three_block_portfolio_execution.py":
        "0eb3477864dbdf2de4496b4b3eb3fe90756054956642b68886aadbef31d9b3e3",
    "materials_gcts_icosahedral_modelset.py":
        "3270fec8ebd7747546f1dd36b174d8204d9ec295253c0c3933ce6e2765c63044",
}

FROZEN_RUNTIME_FIXTURE_SHA256 = \
    "6ab3b23317207577a2805a27f3fa399d312e9c2eefa7d9c858731bd9a456f6d5"
FROZEN_RUNTIME_ARTIFACT_DIGEST = \
    "fbdbdf307227921ad24d11b81aea31e9835acf50ae2359d0807cc184b96c623c"
FROZEN_FUSION_MODEL_DIGEST = \
    "505b65481e3fe2cc25a284ba8dc175e3a794465c2c7bd726f5448c1fac6bbef5"
DEVELOPMENT_REHEARSAL_FIXTURE_SHA256 = \
    "557a3be2daab28c069f8886d0c7339563e82b196548eabb7084a68f981e7e67b"
DEVELOPMENT_REHEARSAL_RECEIPT_DIGEST = \
    "2228dd53fc97e1a41b43a50b0a56adf6e4573c330204e20404e07ed1b484c65a"
DEVELOPMENT_REHEARSAL_RESULT_DIGEST = \
    "557be761cd7393bc33a9235d85deaed2e7adbff26968e688aaa4fd67f95354eb"


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def select_confirmation_center():
    rows = []
    for integer_point in itertools.product(range(
            GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3):
        point = tuple(map(float, integer_point))
        norm = math.dist((0., 0., 0.), point)
        if (norm < MINIMUM_CENTER_NORM or norm > MAXIMUM_CENTER_NORM or
                point in PRIOR_CENTERS):
            continue
        separation = min(math.dist(point, prior) for prior in PRIOR_CENTERS)
        if separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION:
            continue
        # Maximize separation, then minimize norm, then choose the
        # lexicographically smallest coordinate tuple.
        rows.append((separation, -norm, tuple(-value for value in point),
                     point))
    if not rows:
        raise AssertionError("empty fresh-center grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 1,
    "source_commit": SOURCE_COMMIT,
    "source_file_sha256": SOURCE_FILE_SHA256,
    "geometry_rule": "literal-prior-center maximin grid",
    "grid_minimum": GRID_MINIMUM,
    "grid_maximum": GRID_MAXIMUM,
    "grid_step": GRID_STEP,
    "minimum_center_norm": MINIMUM_CENTER_NORM,
    "maximum_center_norm": MAXIMUM_CENTER_NORM,
    "spatial_guard": SPATIAL_GUARD,
    "prior_centers": PRIOR_CENTERS,
    "confirmation_center": CONFIRMATION_CENTER,
    "minimum_required_domain_separation":
        MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    "seed_radius": SEED_RADIUS,
    "first_block_radius": FIRST_BLOCK_RADIUS,
    "second_block_radius": SECOND_BLOCK_RADIUS,
    "third_block_radius": THIRD_BLOCK_RADIUS,
    "execution_workers": EXECUTION_WORKERS,
    "first_parent_width": FIRST_PARENT_WIDTH,
    "second_option_top_k_per_channel": SECOND_OPTION_TOP_K,
    "second_parent_width": SECOND_PARENT_WIDTH,
    "channel_names": CHANNEL_NAMES,
    "expected_actions_per_block": EXPECTED_ACTIONS_PER_BLOCK,
    "expected_lineage_actions": EXPECTED_LINEAGE_ACTIONS,
    "frozen_runtime_fixture_sha256": FROZEN_RUNTIME_FIXTURE_SHA256,
    "frozen_runtime_artifact_digest": FROZEN_RUNTIME_ARTIFACT_DIGEST,
    "frozen_fusion_model_digest": FROZEN_FUSION_MODEL_DIGEST,
    "development_rehearsal_fixture_sha256":
        DEVELOPMENT_REHEARSAL_FIXTURE_SHA256,
    "development_rehearsal_receipt_digest":
        DEVELOPMENT_REHEARSAL_RECEIPT_DIGEST,
    "development_rehearsal_result_digest":
        DEVELOPMENT_REHEARSAL_RESULT_DIGEST,
    "oracle_contract": "exact local compact-inverse-image crop",
    "target_order": (
        "validate protocol and source hashes",
        "open fresh seed exactly once",
        "freeze and serialize complete target-blind receipt",
        "open third-radius target exactly once",
        "score immutable lineages without further execution or fitting",
    ),
    "target_open_limit": TARGET_OPEN_LIMIT,
    "one_shot_execution_limit": ONE_SHOT_EXECUTION_LIMIT,
    "success_gate": {
        "receipt_target_used": False,
        "target_open_count": 1,
        "lineage_actions": EXPECTED_LINEAGE_ACTIONS,
        "exact_lineages_minimum": 1,
        "exact_position_species_for_every_action": True,
        "receipt_unchanged_after_target_open": True,
        "fresh_domain_separated_from_every_prior_center": True,
    },
    "claim_if_gate_passes":
        "fresh bounded three-block exact candidate supply",
    "winner_selected_or_validated": False,
    "autonomous_growth_claimed": False,
    "stationary_or_exponential_claimed": False,
    "rerun_or_fallback_after_scoring_allowed": False,
}

EXPECTED_MANIFEST_DIGEST = \
    "08497963a68547f67330f71f1d37ac76823188555b141d7fd2d71b0ab7d85954"


def source_file_digests(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in SOURCE_FILE_SHA256}


def validate_preregistration(*, verify_sources=True):
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    reproduced = select_confirmation_center()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (len(PRIOR_CENTERS) != 86 or len(set(PRIOR_CENTERS)) != 86 or
            reproduced != CONFIRMATION_CENTER or
            separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION or
            not MINIMUM_CENTER_NORM <= math.dist(
                (0., 0., 0.), CONFIRMATION_CENTER) <= MAXIMUM_CENTER_NORM or
            MANIFEST["winner_selected_or_validated"] or
            MANIFEST["autonomous_growth_claimed"] or
            MANIFEST["stationary_or_exponential_claimed"] or
            MANIFEST["rerun_or_fallback_after_scoring_allowed"] or
            (EXPECTED_MANIFEST_DIGEST and
             digest != EXPECTED_MANIFEST_DIGEST)):
        raise AssertionError("three-block portfolio preregistration drift")
    if verify_sources and source_file_digests() != SOURCE_FILE_SHA256:
        raise AssertionError("three-block source hash drift")
    return digest


class OneShotOrderGuard:
    """Mechanical seed/receipt/target/score ordering for the one-shot run."""

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
