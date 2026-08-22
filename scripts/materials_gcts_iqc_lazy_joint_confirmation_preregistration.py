#!/usr/bin/env python3
"""Immutable fresh protocol for the bounded joint IQC tree executor.

The preceding five-channel confirmation is consumed and red.  Its exact
children were present but ranked fifth and seventh by the site-minimum head.
Development therefore replaced that head with a frozen whole-child marking,
selected the smallest grouped-valid fallback schedule, and added exact
unordered-action geometry memoization.  This module freezes the successor and
a new maximin nucleus without importing a cropper, executor, scorer, or learned
runtime.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

from materials_gcts_iqc_marking_library_confirmation_preregistration import (
    CONFIRMATION_CENTER as PRIOR_CONFIRMATION_CENTER,
    FIRST_BLOCK_RADIUS, GRID_MAXIMUM, GRID_MINIMUM, GRID_STEP,
    MAXIMUM_CENTER_NORM, MINIMUM_CENTER_NORM,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    PRIOR_CENTERS as PREVIOUS_PRIOR_CENTERS, SECOND_BLOCK_RADIUS,
    SEED_RADIUS, THIRD_BLOCK_RADIUS)


SOURCE_COMMIT = "08ac646f8c571081552582896eb1b32eb27a6971"
PRIOR_CENTERS = tuple(sorted(set(
    tuple(PREVIOUS_PRIOR_CENTERS) + (PRIOR_CONFIRMATION_CENTER,))))
CONFIRMATION_CENTER = (160., -180., -140.)
POSITION_TOLERANCE = 1e-5
EXECUTION_WORKERS = 4
COMPLETE_PARENT_WIDTH = 8
JOINT_CHILD_TOP_K = 1
BASE_FALLBACK_TOP_K = 5
MAXIMUM_EXPANDED_PREFIXES = 48
EXPECTED_ACTIONS_PER_BLOCK = 3
EXPECTED_LINEAGE_ACTIONS = 9
MAXIMUM_EXECUTION_WALL_SECONDS = 1200.
TARGET_OPEN_LIMIT = 1
ONE_SHOT_EXECUTION_LIMIT = 1

SOURCE_FILE_SHA256 = {
    "materials_gcts_iqc_marking_library_confirmation_preregistration.py":
        "d9f42fe138f82c14b76fd1760e395f9c0fa5d11801e691e78b6bfe445bac62b8",
    "materials_gcts_iqc_three_block_lazy_joint_execution.py":
        "7f323ba9ca7a138b8125e1729fdd4998e27867f1820dd045d9c18d985c052200",
    "materials_gcts_joint_prefix_schedule.py":
        "c5ce17d22d3022f8fa269929cdf6075c25a18fd906c48d7f85c6b23a14ba3799",
    "materials_gcts_joint_child_action_marking.py":
        "45885eeda44bbe393ff17f1f9d1e4a81c08b2126a662181fb4e37215f4899082",
    "materials_gcts_iqc_frozen_fusion_runtime.py":
        "d8e8e04c208b27b98502d12475d3f09638523116ef810adda9f6407a7b64c4c0",
    "materials_gcts_iqc_three_block_channel_execution.py":
        "7c80e3ab14d523b4dae276992c3e8ebf077d0eb5e5fbe7609dedbdde60ad560b",
    "materials_gcts_iqc_three_block_portfolio_execution.py":
        "0eb3477864dbdf2de4496b4b3eb3fe90756054956642b68886aadbef31d9b3e3",
    "materials_gcts_iqc_self_fed_complete_frontier_execution.py":
        "7851ee4313be33db9ac9719e68cb95234967510dc220c12698f89302bcb042fa",
    "materials_gcts_icosahedral_modelset.py":
        "3270fec8ebd7747546f1dd36b174d8204d9ec295253c0c3933ce6e2765c63044",
}

JOINT_MARKING_FIXTURE_SHA256 = \
    "4c8c3c6ee41e1277e59934c11c4e531a498edb0fa24fa1f876c3ba11998023df"
JOINT_MARKING_MODEL_DIGEST = \
    "99e459ee26914377f4e6525dd4bfbb50822e22de6f5d43d1eb4ae5e76ce136f7"
JOINT_MARKING_ARTIFACT_DIGEST = \
    "98b32b6944ddb0516d5e6e22aed72019b6b2cb7f2f5d8de70d83de1e9c08f2c2"
PREFIX_SCHEDULE_FIXTURE_SHA256 = \
    "d0fc14e912c268923a2a55b6cb0a6a9f8181805bd0596f718599c8e699cb0195"
PREFIX_SCHEDULE_ARTIFACT_DIGEST = \
    "4e5c57d6a2ad15a374f9f973869f693e84a63c4e38cba829907054b74d895fe7"
CONSUMED_SUPPLY_FIXTURE_SHA256 = \
    "ca0711bf1dc571168de0e29fcbceb069beff5c844c457882a535f5b2e4716e38"
CONSUMED_SUPPLY_RESULT_DIGEST = \
    "3548377de5a2fd697f9bfd44cc465fc21529205b7742d0aece588abf31e819a8"
CACHE_PARITY_FIXTURE_SHA256 = \
    "5041b2f7d29b549992ef2733b8beff6c6e099e2ec3be2675b66a73b7aebf020e"
CACHE_PARITY_RESULT_DIGEST = \
    "0875d226c9f24ba302be58f50ba2e636ab013b677201d8c084d92b61f1b3c03f"
PRIOR_CONFIRMATION_FIXTURE_SHA256 = \
    "b061c69a32b4f9016389d5f428b88c7c58bf3d1dd0cd1a9a8ac12910aaf32656"
PRIOR_CONFIRMATION_RESULT_DIGEST = \
    "7120c4b369f52d4ba3cdc741a37729495ac8333bf1055af3a73d4e036519eb3d"


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
        rows.append((separation, -norm, tuple(-value for value in point),
                     point))
    if not rows:
        raise AssertionError("empty lazy-joint confirmation grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 1,
    "source_commit": SOURCE_COMMIT,
    "source_file_sha256": SOURCE_FILE_SHA256,
    "geometry_rule": "fourth literal-prior-center maximin grid",
    "prior_centers": PRIOR_CENTERS,
    "confirmation_center": CONFIRMATION_CENTER,
    "grid": (GRID_MINIMUM, GRID_MAXIMUM, GRID_STEP),
    "center_norm_bounds": (MINIMUM_CENTER_NORM, MAXIMUM_CENTER_NORM),
    "minimum_required_domain_separation":
        MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    "radii": (SEED_RADIUS, FIRST_BLOCK_RADIUS, SECOND_BLOCK_RADIUS,
              THIRD_BLOCK_RADIUS),
    "position_tolerance": POSITION_TOLERANCE,
    "execution_workers": EXECUTION_WORKERS,
    "complete_parent_width": COMPLETE_PARENT_WIDTH,
    "joint_child_top_k_per_parent": JOINT_CHILD_TOP_K,
    "base_fallback_top_k_per_parent": BASE_FALLBACK_TOP_K,
    "maximum_expanded_prefixes": MAXIMUM_EXPANDED_PREFIXES,
    "expected_actions_per_block": EXPECTED_ACTIONS_PER_BLOCK,
    "expected_lineage_actions": EXPECTED_LINEAGE_ACTIONS,
    "maximum_execution_wall_seconds": MAXIMUM_EXECUTION_WALL_SECONDS,
    "joint_marking_fixture_sha256": JOINT_MARKING_FIXTURE_SHA256,
    "joint_marking_model_digest": JOINT_MARKING_MODEL_DIGEST,
    "joint_marking_artifact_digest": JOINT_MARKING_ARTIFACT_DIGEST,
    "prefix_schedule_fixture_sha256": PREFIX_SCHEDULE_FIXTURE_SHA256,
    "prefix_schedule_artifact_digest": PREFIX_SCHEDULE_ARTIFACT_DIGEST,
    "consumed_supply_fixture_sha256": CONSUMED_SUPPLY_FIXTURE_SHA256,
    "consumed_supply_result_digest": CONSUMED_SUPPLY_RESULT_DIGEST,
    "cache_parity_fixture_sha256": CACHE_PARITY_FIXTURE_SHA256,
    "cache_parity_result_digest": CACHE_PARITY_RESULT_DIGEST,
    "prior_confirmation_fixture_sha256":
        PRIOR_CONFIRMATION_FIXTURE_SHA256,
    "prior_confirmation_result_digest": PRIOR_CONFIRMATION_RESULT_DIGEST,
    "target_order": (
        "validate committed protocol and all source/model hashes",
        "open R9 seed exactly once",
        "freeze complete second queue and bounded third-prefix receipt",
        "serialize receipt and execution telemetry",
        "open R32.5623 target exactly once",
        "score immutable nine-action lineages at 1e-5 tolerance",
    ),
    "target_open_limit": TARGET_OPEN_LIMIT,
    "one_shot_execution_limit": ONE_SHOT_EXECUTION_LIMIT,
    "success_gate": {
        "all_eight_admitted_parents_executed": True,
        "expanded_prefixes_maximum": MAXIMUM_EXPANDED_PREFIXES,
        "expanded_prefixes_less_than_eager_library": True,
        "geometry_cache_saves_expansions": True,
        "grouped_consumed_exact_supply": "6/6",
        "receipt_target_used": False,
        "target_open_count": 1,
        "exact_nine_action_lineages_minimum": 1,
        "execution_wall_seconds_maximum": MAXIMUM_EXECUTION_WALL_SECONDS,
        "position_tolerance": POSITION_TOLERANCE,
        "species_exact": True,
        "receipt_unchanged_after_target_open": True,
        "fresh_domain_separated_from_all_89_prior_centers": True,
    },
    "claim_if_gate_passes":
        "fresh bounded joint-marking three-block exact candidate supply",
    "winner_selected_or_validated": False,
    "autonomous_growth_claimed": False,
    "stationary_or_exponential_claimed": False,
    "rerun_or_fallback_after_scoring_allowed": False,
}
EXPECTED_MANIFEST_DIGEST = (
    "d40084591f790418fda8e5ca25fcf13749c597f06b4d6119242dcfda27af752a")


def source_file_digests(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in SOURCE_FILE_SHA256}


def validate_preregistration(*, verify_sources=True):
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (len(PRIOR_CENTERS) != 89 or len(set(PRIOR_CENTERS)) != 89 or
            select_confirmation_center() != CONFIRMATION_CENTER or
            separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION or
            MANIFEST["winner_selected_or_validated"] or
            MANIFEST["autonomous_growth_claimed"] or
            MANIFEST["stationary_or_exponential_claimed"] or
            MANIFEST["rerun_or_fallback_after_scoring_allowed"] or
            (EXPECTED_MANIFEST_DIGEST and
             digest != EXPECTED_MANIFEST_DIGEST)):
        raise AssertionError("lazy-joint preregistration drift")
    if verify_sources and source_file_digests() != SOURCE_FILE_SHA256:
        raise AssertionError("lazy-joint source hash drift")
    return digest


class OneShotOrderGuard:
    def __init__(self):
        self.state = "created"
        self.seed_open_count = 0
        self.execution_count = 0
        self.target_open_count = 0
        self.score_count = 0
        self.receipt_digest = None
        self.execution_wall_seconds = None

    def protocol_verified(self):
        if self.state != "created":
            raise RuntimeError("protocol order violation")
        validate_preregistration()
        self.state = "protocol-verified"

    def seed_opened(self):
        if self.state != "protocol-verified" or self.seed_open_count:
            raise RuntimeError("seed order violation")
        self.seed_open_count = 1
        self.state = "seed-opened"

    def execution_started(self):
        if self.state != "seed-opened" or self.execution_count:
            raise RuntimeError("execution order violation")
        self.execution_count = 1
        self.state = "executing"

    def receipt_frozen(self, digest, elapsed_seconds):
        if (self.state != "executing" or not isinstance(digest, str) or
                len(digest) != 64 or not math.isfinite(elapsed_seconds) or
                elapsed_seconds <= 0):
            raise RuntimeError("receipt order violation")
        int(digest, 16)
        self.receipt_digest = digest
        self.execution_wall_seconds = float(elapsed_seconds)
        self.state = "receipt-frozen"

    def target_opened(self):
        if self.state != "receipt-frozen" or self.target_open_count:
            raise RuntimeError("target order violation")
        self.target_open_count = 1
        self.state = "target-opened"

    def scored(self, digest):
        if (self.state != "target-opened" or self.score_count or
                digest != self.receipt_digest):
            raise RuntimeError("score order violation")
        self.score_count = 1
        self.state = "scored"

    def audit(self):
        return {
            "state": self.state,
            "seed_open_count": self.seed_open_count,
            "execution_count": self.execution_count,
            "target_open_count": self.target_open_count,
            "score_count": self.score_count,
            "receipt_digest": self.receipt_digest,
            "execution_wall_seconds": self.execution_wall_seconds,
        }


if __name__ == "__main__":
    print(validate_preregistration())
