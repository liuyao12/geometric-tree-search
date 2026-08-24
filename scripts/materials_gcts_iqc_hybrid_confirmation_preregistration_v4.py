#!/usr/bin/env python3
"""Preregister the fresh two-fallback full-width IQC confirmation."""

from __future__ import annotations

import hashlib
import itertools
import math
from pathlib import Path

from materials_gcts_iqc_parent_balanced_confirmation_preregistration import (
    ACTION_MARKING_FIXTURE_SHA256, ACTION_MARKING_MODEL_DIGEST,
    FIFTH_RESERVED_RADIUS, FIRST_RADIUS, FOURTH_RADIUS, GRID_MAXIMUM,
    GRID_MINIMUM, GRID_STEP, MAXIMUM_CENTER_NORM, MINIMUM_CENTER_NORM,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, PARENT_POLICY_FIXTURE_SHA256,
    PARENT_POLICY_MODEL_DIGEST, PARENT_WIDTH, SECOND_RADIUS, SEED_RADIUS,
    SPATIAL_GUARD, THIRD_RADIUS, canonical_json)
from materials_gcts_iqc_parent_balanced_confirmation_preregistration_v3 \
    import CONFIRMATION_CENTER as V3_CENTER, PRIOR_CENTERS as V3_PRIORS


PRIOR_CENTERS = tuple(sorted(set(V3_PRIORS + (V3_CENTER,))))
CONFIRMATION_CENTER = (360., 0., 0.)
EXECUTION_WORKERS = 4
MAXIMUM_FALLBACKS = 2
POSITION_TOLERANCE = 1e-5
RUNTIME_LIMIT_SECONDS = 600.
TARGET_OPEN_LIMIT = 1
ONE_SHOT_EXECUTION_LIMIT = 1
MINIMAL_DEVELOPMENT_FIXTURE_SHA256 = \
    "bb9f67bffd2144a6c30e469f95514bdde5742251d59a97116c0253be00e6205c"
MINIMAL_DEVELOPMENT_RESULT_DIGEST = \
    "c43e774cda1e7ccaaa8d475bcc8cba8fbaff581b61996fb9bc80e767954fb719"
JOINT_SCHEDULE_FIXTURE_SHA256 = \
    "d0fc14e912c268923a2a55b6cb0a6a9f8181805bd0596f718599c8e699cb0195"
JOINT_SCHEDULE_ARTIFACT_DIGEST = \
    "4e5c57d6a2ad15a374f9f973869f693e84a63c4e38cba829907054b74d895fe7"

SOURCE_FILE_SHA256 = {
    'materials_gcts_action_marginal_prefix_schedule.py':
        'e2da338d518bff5013822c1733bad70f945ee041da4f42bf8af3efec1d89c355',
    'materials_gcts_colored_position_scorer.py':
        '9e4e7122263abeb5e66953f738f4e815bf1fa5ba28df0d7704812cec962373f8',
    'materials_gcts_icosahedral_modelset.py':
        '3270fec8ebd7747546f1dd36b174d8204d9ec295253c0c3933ce6e2765c63044',
    'materials_gcts_incidence_token_marking.py':
        '71f4ef3f13bfd66f8f15529a35dd9de9c8325c9705748fb96875c55decbc95c3',
    'materials_gcts_iqc_bounded_lineage_graph_value.py':
        '5b620746c62c566895ebaebc9f7e0f0034e3a2cef82b3b4bb1f6c8b90c30cb52',
    'materials_gcts_iqc_bounded_lineage_value.py':
        'c9b94f172321d08dfb775885695bdcb0c00390ec8e2853a8e674bb6d92220436',
    'materials_gcts_iqc_fourth_block_action_marking.py':
        '0c10fa12803b7a4428ef1a5892d2df7e5d92a26767498157bda917367467a0c0',
    'materials_gcts_iqc_fourth_block_beam.py':
        '4eeb5c7bf3bd836a01a6ff24e609a7e3f5c4a26b4e26a994661d9f4b016de76b',
    'materials_gcts_iqc_fourth_block_parent_balanced_policy.py':
        '26140b933728b27975e091efb41083af9949536edc357102f8d98f31f3b17a2c',
    'materials_gcts_iqc_fresh_parent_balanced_execution.py':
        'a33f9839312213c7c18241ccc5f97668541fa47f4dfa77f39b79bbdbad43bd64',
    'materials_gcts_iqc_fresh_parent_balanced_execution_v2.py':
        '3e968051994ae8cf9fa286c1fe4914b85b0f9aebe86b1f56e09ad11f32258fca',
    'materials_gcts_iqc_fresh_parent_balanced_execution_v3.py':
        'ad74133077644932513f00a48ddea3b2345badc167a904ba4ec12a9966d48e23',
    'materials_gcts_iqc_fresh_parent_balanced_execution_v4.py':
        'ce305951ed0f9fb5132b33fe1b157b3e2cb3bb6795b28e487b08f32d913d7626',
    'materials_gcts_iqc_frozen_fusion_artifact.py':
        '2026a624e03f599573501b27daa373302cd264f96afa6369313354063669fde9',
    'materials_gcts_iqc_frozen_fusion_runtime.py':
        'a6af070ef222cb6bc8a09c2411b5ae46161fdf1a79f4e7723940c0db1be018bd',
    'materials_gcts_iqc_hybrid_fullwidth_consumed_benchmark.py':
        '68c4359f397ee4f7c0dd464e59c18706d2eaa7e5ba9280dc568db85057a4f838',
    'materials_gcts_iqc_minimal_hybrid_fullwidth_benchmark.py':
        'b64fdeba8b3e2a76d3dc620e8aa9b9245dceb25356242967545fee90a58f7372',
    'materials_gcts_iqc_pose_port_state_audit.py':
        '04030bafcb1e400d342ed424dbfecedf65783b5228810b260560d75825cc7c49',
    'materials_gcts_iqc_three_block_channel_execution.py':
        'ce45ba3d4217f08bbda964ebe677bbf4ddd94c35c97f69f591a561fb91330195',
    'materials_gcts_iqc_three_block_lazy_joint_execution.py':
        '7f323ba9ca7a138b8125e1729fdd4998e27867f1820dd045d9c18d985c052200',
    'materials_gcts_iqc_three_block_portfolio_execution.py':
        '0eb3477864dbdf2de4496b4b3eb3fe90756054956642b68886aadbef31d9b3e3',
    'materials_gcts_joint_prefix_schedule.py':
        'c5ce17d22d3022f8fa269929cdf6075c25a18fd906c48d7f85c6b23a14ba3799',
    'materials_gcts_lineage_continuation.py':
        '29fc79d68d2dcd58956358e571ffb432b2d27baecda953ab92acb8582a783754',
    'materials_gcts_partial_irregular_section.py':
        'abd54678da140bc4022e77548750c05e97f461a488b5f8b88c39fce6e814ac00',
    'materials_gcts_partial_port_graph_lineage_value.py':
        '9d5e0979618c89954604d850580f3b7e46b5826c0c35e6cae1b88faba894b038',
    'materials_gcts_persistent_frontier_beam.py':
        '6ba728c9b125ca12c708378f53f2f36fc07162b0e18ebe362f28a2a05c456be2',
    'materials_gcts_port_incidence_search.py':
        'aebf5484a0dd93cdfddce14779263676e9d38f9eff2dfc2b9086d7e467ee6d2d',
    'materials_gcts_pose_port_state_marking.py':
        'a76beffdd3014ab2b28aaa30172d2d2583d395e52ff349f19a00ea2eb93bd2ce',
    'materials_gcts_pose_port_state_serialization.py':
        '38d49e7910268ad9bb0c11353eda9ab5a37cfeb5301f1e971601a3fe70545225',
    'materials_gcts_recursive_connections.py':
        '259469b76a755bb15f23c63590646659f26ac00a18e81ce59b1791488528cdd1',
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
        raise AssertionError("empty V4 hybrid confirmation-center grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 4,
    "protocol_kind": "fresh two-fallback full-width parent-balanced IQC",
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
    "maximum_action_marginal_fallbacks": MAXIMUM_FALLBACKS,
    "position_tolerance": POSITION_TOLERANCE,
    "runtime_limit_seconds": RUNTIME_LIMIT_SECONDS,
    "source_file_sha256": SOURCE_FILE_SHA256,
    "minimal_development_fixture_sha256":
        MINIMAL_DEVELOPMENT_FIXTURE_SHA256,
    "minimal_development_result_digest":
        MINIMAL_DEVELOPMENT_RESULT_DIGEST,
    "joint_schedule_fixture_sha256": JOINT_SCHEDULE_FIXTURE_SHA256,
    "joint_schedule_artifact_digest": JOINT_SCHEDULE_ARTIFACT_DIGEST,
    "parent_policy_fixture_sha256": PARENT_POLICY_FIXTURE_SHA256,
    "action_marking_fixture_sha256": ACTION_MARKING_FIXTURE_SHA256,
    "parent_policy_model_digest": PARENT_POLICY_MODEL_DIGEST,
    "action_marking_model_digest": ACTION_MARKING_MODEL_DIGEST,
    "target_order": (
        "verify protocol, source hashes, geometry and frozen artifacts",
        "open only the fresh radius-9 seed",
        "freeze and serialize every hybrid raw nine-action lineage",
        "select 64 parents and freeze all 512 twelve-action candidates",
        "open the radius-41.562 target exactly once",
        "score without refit, fallback, retry or policy change",
    ),
    "success_gate": {
        "target_used_for_execution": False,
        "target_open_count": 1,
        "raw_exact_nine_action_lineages_minimum": 1,
        "selected_exact_nine_action_lineages_minimum": 1,
        "exact_complete_twelve_action_paths_minimum": 1,
        "receipt_unchanged_after_target": True,
        "runtime_seconds_maximum": RUNTIME_LIMIT_SECONDS,
    },
    "claim_if_gate_passes":
        "fresh exact twelve-action IQC candidate supply",
    "autonomous_sustained_growth_claimed": False,
    "stationary_or_exponential_claimed": False,
    "target_or_oracle_opened_during_preregistration": False,
    "rerun_or_fallback_after_scoring_allowed": False,
}
EXPECTED_MANIFEST_DIGEST = \
    "32058dcfc07a91cfc6ec2ede8ee7375ea65f87a2bbfe956f1be56e9b753ceb2e"


def source_file_digests(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in SOURCE_FILE_SHA256}


def validate_preregistration(*, verify_sources=True, pin=True):
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (select_confirmation_center() != CONFIRMATION_CENTER or
            separation <= MINIMUM_REQUIRED_DOMAIN_SEPARATION or
            MANIFEST["target_or_oracle_opened_during_preregistration"] or
            MANIFEST["autonomous_sustained_growth_claimed"] or
            MANIFEST["stationary_or_exponential_claimed"] or
            MANIFEST["rerun_or_fallback_after_scoring_allowed"] or
            MANIFEST["maximum_action_marginal_fallbacks"] != 2 or
            (pin and digest != EXPECTED_MANIFEST_DIGEST)):
        raise AssertionError("V4 hybrid preregistration drift")
    if verify_sources and source_file_digests() != SOURCE_FILE_SHA256:
        raise AssertionError("V4 hybrid source hash drift")
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
            raise RuntimeError("V4 protocol order violation")
        validate_preregistration()
        self.state = "protocol-verified"

    def seed_opened(self):
        if self.state != "protocol-verified" or self.seed_open_count:
            raise RuntimeError("V4 seed order violation")
        self.seed_open_count += 1
        self.state = "seed-opened"

    def receipt_frozen(self, digest):
        if (self.state != "seed-opened" or not isinstance(digest, str) or
                len(digest) != 64):
            raise RuntimeError("V4 receipt order violation")
        int(digest, 16)
        self.receipt_digest = digest
        self.state = "receipt-frozen"

    def target_opened(self):
        if self.state != "receipt-frozen" or self.target_open_count:
            raise RuntimeError("V4 target order violation")
        self.target_open_count += 1
        self.state = "target-opened"

    def scored(self, digest):
        if (self.state != "target-opened" or self.score_count or
                digest != self.receipt_digest):
            raise RuntimeError("V4 score order violation")
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
    print(validate_preregistration(pin=False))
