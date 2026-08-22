#!/usr/bin/env python3
"""Immutable fresh protocol for the five-channel IQC marking library.

The two earlier fresh confirmations remain consumed and red.  Their combined
development evidence led to one fixed change: preserve all eight parent
subtrees and union two children from a frozen ID-free local-section marking
with the top-eight contributions of four legacy markings.  This protocol
freezes that successor, a third deterministic maximin nucleus, and a strict
seed/receipt/target/score order.  It imports no cropper, executor, scorer, or
learned runtime.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

from materials_gcts_iqc_complete_parent_confirmation_preregistration import (
    CONFIRMATION_CENTER as SECOND_CONFIRMATION_CENTER,
    FIRST_BLOCK_RADIUS, GRID_MAXIMUM, GRID_MINIMUM, GRID_STEP,
    MAXIMUM_CENTER_NORM, MINIMUM_CENTER_NORM,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    PRIOR_CENTERS as SECOND_PRIOR_CENTERS, SECOND_BLOCK_RADIUS, SEED_RADIUS,
    THIRD_BLOCK_RADIUS)


SOURCE_COMMIT = "a8514f483c25546522bbc58d0d69f788d4682e01"
PRIOR_CENTERS = tuple(sorted(set(
    tuple(SECOND_PRIOR_CENTERS) + (SECOND_CONFIRMATION_CENTER,))))
CONFIRMATION_CENTER = (160., 20., 220.)
POSITION_TOLERANCE = 1e-5
EXECUTION_WORKERS = 4
FIRST_PARENT_WIDTH = 8
COMPLETE_PARENT_WIDTH = 8
LEGACY_CHILD_TOP_K = 8
LOCAL_SECTION_CHILD_TOP_K = 2
CHANNEL_NAMES = ("base", "colored", "ports", "coupled", "local-section")
EXPECTED_ACTIONS_PER_BLOCK = 3
EXPECTED_LINEAGE_ACTIONS = 9
TARGET_OPEN_LIMIT = 1
ONE_SHOT_EXECUTION_LIMIT = 1

SOURCE_FILE_SHA256 = {
    "materials_gcts_iqc_complete_parent_confirmation_preregistration.py":
        "a142ffb5e257f96d21e89b4623b440642dff6ce7998f608f491ccb37334e4a5c",
    "materials_gcts_iqc_three_block_marking_library_execution.py":
        "6e767b35c88733e8bdfb84224233b31c54f652eeb68cb349044b88c4b58aa0f5",
    "materials_gcts_local_section_child_marking.py":
        "1a572695fd45c3f6ccb85945034ceaa936e64c378091db2f731c0b21653a6928",
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

LOCAL_SECTION_FIXTURE_SHA256 = \
    "ed9791c608c98bd0d3ae9239f56ff00955323f336a016c51fcec99ebd0cc8361"
LOCAL_SECTION_MODEL_DIGEST = \
    "9b28158d2a1b6eb7edde39bd80e3ef885d04c6e0770b4905bc93f8e8cc24d714"
LOCAL_SECTION_ARTIFACT_DIGEST = \
    "9f8f3a73155b79b36d7b299a1f0db11ad082f5460569805fc8f6385770f15146"
CONSUMED_SUPPLY_FIXTURE_SHA256 = \
    "a8791ba54c6795d14cf79510e08e9bae4c03c58cf8c3e2fd9cc06e729c2ab0ac"
CONSUMED_SUPPLY_RESULT_DIGEST = \
    "bad3b0a6298c99c511b9ddff1389ef1f24094203535df37a3df5a42efdcfe742"
SECOND_CONFIRMATION_FIXTURE_SHA256 = \
    "e2945f206103078e32a3c384f25961091a66636c79e8a2690cd4bdd82adb9ef2"
SECOND_CONFIRMATION_RESULT_DIGEST = \
    "9cb6fb19af9948f902b3305640dd5e1117ec3785666f411d7541d6736ffb0153"


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
        raise AssertionError("empty marking-library confirmation grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 1,
    "source_commit": SOURCE_COMMIT,
    "source_file_sha256": SOURCE_FILE_SHA256,
    "geometry_rule": "third literal-prior-center maximin grid",
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
    "legacy_child_top_k_per_channel": LEGACY_CHILD_TOP_K,
    "local_section_child_top_k": LOCAL_SECTION_CHILD_TOP_K,
    "channel_names": CHANNEL_NAMES,
    "expected_actions_per_block": EXPECTED_ACTIONS_PER_BLOCK,
    "expected_lineage_actions": EXPECTED_LINEAGE_ACTIONS,
    "local_section_fixture_sha256": LOCAL_SECTION_FIXTURE_SHA256,
    "local_section_model_digest": LOCAL_SECTION_MODEL_DIGEST,
    "local_section_artifact_digest": LOCAL_SECTION_ARTIFACT_DIGEST,
    "consumed_supply_fixture_sha256": CONSUMED_SUPPLY_FIXTURE_SHA256,
    "consumed_supply_result_digest": CONSUMED_SUPPLY_RESULT_DIGEST,
    "second_confirmation_fixture_sha256":
        SECOND_CONFIRMATION_FIXTURE_SHA256,
    "second_confirmation_result_digest": SECOND_CONFIRMATION_RESULT_DIGEST,
    "target_order": (
        "validate committed protocol and all source/model hashes",
        "open R9 seed exactly once",
        "freeze and serialize five-channel complete-parent receipt",
        "open R32.5623 target exactly once",
        "score immutable nine-action lineages at 1e-5 tolerance",
    ),
    "target_open_limit": TARGET_OPEN_LIMIT,
    "one_shot_execution_limit": ONE_SHOT_EXECUTION_LIMIT,
    "success_gate": {
        "all_eight_admitted_parents_executed": True,
        "legacy_and_local_child_union_frozen": True,
        "receipt_target_used": False,
        "target_open_count": 1,
        "exact_nine_action_lineages_minimum": 1,
        "position_tolerance": POSITION_TOLERANCE,
        "species_exact": True,
        "receipt_unchanged_after_target_open": True,
        "fresh_domain_separated_from_all_88_prior_centers": True,
    },
    "claim_if_gate_passes":
        "fresh five-channel three-block exact candidate supply",
    "winner_selected_or_validated": False,
    "autonomous_growth_claimed": False,
    "stationary_or_exponential_claimed": False,
    "rerun_or_fallback_after_scoring_allowed": False,
}
EXPECTED_MANIFEST_DIGEST = \
    "f872a9337b317bae1b6bd0b120d7377b76032609afa5a77ccec29c4d38183523"


def source_file_digests(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in SOURCE_FILE_SHA256}


def validate_preregistration(*, verify_sources=True):
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (len(PRIOR_CENTERS) != 88 or len(set(PRIOR_CENTERS)) != 88 or
            select_confirmation_center() != CONFIRMATION_CENTER or
            separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION or
            MANIFEST["winner_selected_or_validated"] or
            MANIFEST["autonomous_growth_claimed"] or
            MANIFEST["stationary_or_exponential_claimed"] or
            MANIFEST["rerun_or_fallback_after_scoring_allowed"] or
            (EXPECTED_MANIFEST_DIGEST and
             digest != EXPECTED_MANIFEST_DIGEST)):
        raise AssertionError("marking-library preregistration drift")
    if verify_sources and source_file_digests() != SOURCE_FILE_SHA256:
        raise AssertionError("marking-library source hash drift")
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
        return {
            "state": self.state,
            "seed_open_count": self.seed_open_count,
            "target_open_count": self.target_open_count,
            "score_count": self.score_count,
            "receipt_digest": self.receipt_digest,
        }


if __name__ == "__main__":
    print(validate_preregistration())
