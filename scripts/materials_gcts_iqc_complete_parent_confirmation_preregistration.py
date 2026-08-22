#!/usr/bin/env python3
"""Immutable second fresh IQC protocol for the complete-parent successor.

The first fresh confirmation is consumed and remains red.  Its posthoc
diagnostic localized the failure to deletion of four already-admitted parent
subtrees.  This protocol freezes the successor that keeps the complete
width-eight parent antichain, a numerical position tolerance of 1e-5, and a
new deterministic maximin nucleus.  It imports no oracle, cropper, executor,
scorer, or learned runtime.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

from materials_gcts_iqc_three_block_portfolio_confirmation_preregistration import (
    CONFIRMATION_CENTER as FIRST_CONFIRMATION_CENTER,
    FIRST_BLOCK_RADIUS, FROZEN_FUSION_MODEL_DIGEST,
    FROZEN_RUNTIME_ARTIFACT_DIGEST, FROZEN_RUNTIME_FIXTURE_SHA256,
    GRID_MAXIMUM, GRID_MINIMUM, GRID_STEP, MAXIMUM_CENTER_NORM,
    MINIMUM_CENTER_NORM, MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    PRIOR_CENTERS as FIRST_PRIOR_CENTERS, SECOND_BLOCK_RADIUS, SEED_RADIUS,
    THIRD_BLOCK_RADIUS)


SOURCE_COMMIT = "202d23d38a4365a7909f5ffe74d112d0e05d17e2"
PRIOR_CENTERS = tuple(sorted(set(
    tuple(FIRST_PRIOR_CENTERS) + (FIRST_CONFIRMATION_CENTER,))))
CONFIRMATION_CENTER = (20., 220., -160.)
POSITION_TOLERANCE = 1e-5
EXECUTION_WORKERS = 4
FIRST_PARENT_WIDTH = 8
COMPLETE_PARENT_WIDTH = 8
SECOND_OPTION_TOP_K = 8
CHANNEL_NAMES = ("base", "colored", "ports", "coupled")
EXPECTED_ACTIONS_PER_BLOCK = 3
EXPECTED_LINEAGE_ACTIONS = 9
TARGET_OPEN_LIMIT = 1
ONE_SHOT_EXECUTION_LIMIT = 1

SOURCE_FILE_SHA256 = {
    "materials_gcts_iqc_three_block_portfolio_confirmation_preregistration.py":
        "dbb75235f8303f956e5c3f95a88d2c6b9ba47d330c0536751531b02fa202635c",
    "materials_gcts_iqc_three_block_complete_parent_execution.py":
        "847afd6062cdc76f3f503ae20df75c2195a013653fa72a38dad3d8c6fb8bb232",
    "materials_gcts_iqc_three_block_portfolio_execution.py":
        "0eb3477864dbdf2de4496b4b3eb3fe90756054956642b68886aadbef31d9b3e3",
    "materials_gcts_equivariant_port_fusion_value.py":
        "ab5fec4f6e572dc3a5324c5692d7ba7b1cecb40f8899b3aef6cc3e4687642559",
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
    "materials_gcts_icosahedral_modelset.py":
        "3270fec8ebd7747546f1dd36b174d8204d9ec295253c0c3933ce6e2765c63044",
}

FIRST_CONFIRMATION_FIXTURE_SHA256 = \
    "40667fe8363e977c194d9a5ab276b975b7db3ae0713260528b504374ff09454e"
FIRST_CONFIRMATION_RESULT_DIGEST = \
    "a11358dc96349d7ad8b40645b5eb4fb1783fc482f6113f2b4bc14b7a52bdc6d6"
COMPLETE_PARENT_DIAGNOSTIC_FIXTURE_SHA256 = \
    "38343bb94b15e0f2f21527c3dda3fabbb1fb89c6961222a3357f4f202b016e70"
COMPLETE_PARENT_DIAGNOSTIC_RESULT_DIGEST = \
    "f6117d72502c6db123eca9ccdaa4d88047de09fda26d6e38ec03f58b1bca4923"


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
        raise AssertionError("empty successor confirmation-center grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 1,
    "source_commit": SOURCE_COMMIT,
    "source_file_sha256": SOURCE_FILE_SHA256,
    "geometry_rule": "next literal-prior-center maximin grid",
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
    "first_parent_width": FIRST_PARENT_WIDTH,
    "complete_parent_width": COMPLETE_PARENT_WIDTH,
    "second_option_top_k_per_channel": SECOND_OPTION_TOP_K,
    "channel_names": CHANNEL_NAMES,
    "expected_actions_per_block": EXPECTED_ACTIONS_PER_BLOCK,
    "expected_lineage_actions": EXPECTED_LINEAGE_ACTIONS,
    "runtime_fixture_sha256": FROZEN_RUNTIME_FIXTURE_SHA256,
    "runtime_artifact_digest": FROZEN_RUNTIME_ARTIFACT_DIGEST,
    "fusion_model_digest": FROZEN_FUSION_MODEL_DIGEST,
    "first_confirmation_fixture_sha256":
        FIRST_CONFIRMATION_FIXTURE_SHA256,
    "first_confirmation_result_digest": FIRST_CONFIRMATION_RESULT_DIGEST,
    "complete_parent_diagnostic_fixture_sha256":
        COMPLETE_PARENT_DIAGNOSTIC_FIXTURE_SHA256,
    "complete_parent_diagnostic_result_digest":
        COMPLETE_PARENT_DIAGNOSTIC_RESULT_DIGEST,
    "target_order": (
        "validate committed protocol and source hashes",
        "open R9 seed exactly once",
        "freeze and serialize complete-parent receipt",
        "open R32.5623 target exactly once",
        "score receipt at frozen 1e-5 position/species tolerance",
    ),
    "target_open_limit": TARGET_OPEN_LIMIT,
    "one_shot_execution_limit": ONE_SHOT_EXECUTION_LIMIT,
    "success_gate": {
        "all_eight_admitted_parents_executed": True,
        "receipt_target_used": False,
        "target_open_count": 1,
        "exact_nine_action_lineages_minimum": 1,
        "position_tolerance": POSITION_TOLERANCE,
        "species_exact": True,
        "receipt_unchanged_after_target_open": True,
        "fresh_domain_separated_from_all_87_prior_centers": True,
    },
    "claim_if_gate_passes":
        "fresh complete-parent three-block exact candidate supply",
    "winner_selected_or_validated": False,
    "autonomous_growth_claimed": False,
    "stationary_or_exponential_claimed": False,
    "rerun_or_fallback_after_scoring_allowed": False,
}
EXPECTED_MANIFEST_DIGEST = \
    "ccb327f939111c99fe33e3eca5bfeaf7ef41cbe6377418a8d6f745b699027630"


def source_file_digests(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in SOURCE_FILE_SHA256}


def validate_preregistration(*, verify_sources=True):
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (len(PRIOR_CENTERS) != 87 or len(set(PRIOR_CENTERS)) != 87 or
            select_confirmation_center() != CONFIRMATION_CENTER or
            separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION or
            MANIFEST["winner_selected_or_validated"] or
            MANIFEST["autonomous_growth_claimed"] or
            MANIFEST["stationary_or_exponential_claimed"] or
            MANIFEST["rerun_or_fallback_after_scoring_allowed"] or
            (EXPECTED_MANIFEST_DIGEST and
             digest != EXPECTED_MANIFEST_DIGEST)):
        raise AssertionError("complete-parent preregistration drift")
    if verify_sources and source_file_digests() != SOURCE_FILE_SHA256:
        raise AssertionError("complete-parent source hash drift")
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
            raise RuntimeError("protocol order violation")
        validate_preregistration()
        self.state = "protocol-verified"

    def seed_opened(self):
        if self.state != "protocol-verified" or self.seed_open_count:
            raise RuntimeError("seed order violation")
        self.seed_open_count = 1
        self.state = "seed-opened"

    def receipt_frozen(self, digest):
        if (self.state != "seed-opened" or not isinstance(digest, str) or
                len(digest) != 64):
            raise RuntimeError("receipt order violation")
        int(digest, 16)
        self.receipt_digest = digest
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
        return {"state": self.state,
                "seed_open_count": self.seed_open_count,
                "target_open_count": self.target_open_count,
                "score_count": self.score_count,
                "receipt_digest": self.receipt_digest}


if __name__ == "__main__":
    print(validate_preregistration())
