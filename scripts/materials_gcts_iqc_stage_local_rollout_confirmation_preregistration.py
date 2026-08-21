#!/usr/bin/env python3
"""Preregister a fresh spatial test of frozen stage-local rollout value.

This module deliberately imports no oracle, cropper, executor, or scorer.  It
freezes the exact model/source bytes, a geometry-only maximin center, matched
first-block candidate work, three self-fed blocks, and fail-closed outcomes
before any atom at the confirmation nucleus is constructed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path

from materials_gcts_iqc_stage_local_prefix_confirmation_preregistration import (
    CONFIRMATION_CENTER as PRIOR_CONFIRMATION_CENTER, CONSUMED_DOMAINS)


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "49f79f8"
SOURCE_DATASET_DIGEST = \
    "78079a89c3122100a6d0b55ab3bb47b49fa03a4f3c22e789d331863475c4058c"
SOURCE_AUDIT_DIGEST = \
    "f8c45d84339b3f10ee18a2d3cf71c4ca686c773318788c7a17afe8982087777f"
SOURCE_DATASET_FILE_SHA256 = \
    "375f4bac18092b259b0860a137fe856c00c69ae64c67c4604f1b4d568707db66"
PREFIX_MODEL_DIGEST = \
    "eeef24a2721e6418d150f97c23401df5471129c63bff9f60053f9a05dcc59665"
ROLLOUT_MODEL_DIGEST = \
    "e0f67c875da55a430e9d4eab1a429939378bd325848fa108750e37b7895dee98"
PREFIX_MODEL_FILE_SHA256 = \
    "babf27b5a98776e440a0a497c9b21ccca69f385c974fc68b56fe7882eb7cb129"
ROLLOUT_MODEL_FILE_SHA256 = \
    "1d8de219521e2a8568706a3c0467f96efef106a42553319466291fffde9644b6"
SOURCE_FILE_SHA256S = (
    ("materials_gcts_iqc_frozen_stage_local_rollout_value.py",
     "96b404f16e627301eb993c3357cd736ed511f285195b93ace66dcd780381cdaf"),
    ("materials_gcts_iqc_stage_local_rollout_runtime.py",
     "51a3291147f5d87600981dcf0f7498430746dcf4d1eac2ef430461c8a87344ef"),
    ("materials_gcts_iqc_frozen_stage_local_margin_marking.py",
     "25eae5924085ba4de4f03f23eebe8d5449d337b1d47dba41e0ccac5fc9396829"),
    ("materials_gcts_iqc_stage_local_prefix_runtime.py",
     "ee04ffaa73dde5b3b98b222b21a743ab0ceb54972f0a144812717cf03affe0f3"),
    ("materials_gcts_iqc_stage_local_augmented_rollout_value_audit.py",
     "d0912512ab2df4542f266ac091f952e786cd57d9c965cac2521f0180aba333f1"),
    ("materials_gcts_iqc_stage_local_augmented_rollout_dataset.py",
     "1a0809cdaa346dfe9f101925b23dc7b5ef7dcbd0d81747667505a7c100210afd"),
    ("materials_gcts_iqc_frozen_fusion_runtime.py",
     "2d990643594255484f5e44138bd47509229115a4e62ee133bd8c8f9a049287c9"),
)

GRID_MINIMUM = -260
GRID_MAXIMUM = 260
GRID_STEP = 20
MAXIMUM_CENTER_NORM = 260.
SEED_RADIUS = 9.
TARGET_RADIUS = 14.562305898749054
SAFETY_MARGIN = 6.
REQUIRED_CENTER_SEPARATION = 2. * TARGET_RADIUS + SAFETY_MARGIN
CANDIDATE_REACH = (12, 4, 8)
TERMINAL_PORTFOLIO_BUDGET = (4, 8, 8)
SELF_FED_BLOCKS = 3
SITES_PER_BLOCK = 3
CONFIRMATION_CENTER = (120., -40., -220.)
EXPECTED_MANIFEST_DIGEST = \
    "a7774c8cb7585db173fcc7514e44e86f1830b3a882a07271205a2b5417292dae"


USED_DOMAINS = tuple(sorted(set(CONSUMED_DOMAINS +
                                (PRIOR_CONFIRMATION_CENTER,))))
CENTER_SELECTION_RULE = (
    "form the 20-unit grid in [-260,260]^3 with norm <=260; maximize minimum "
    "distance from every prior consumed/development/confirmation center, "
    "then minimize norm and break ties reverse lexicographically"
)
EXECUTION_RULE = (
    "from the colored R9 seed, build the frozen 12->4->8 proposal tree and "
    "retain the identical 4->8->8 terminal portfolio; run the same 16-step "
    "target-free rollout for all eight terminals; select by frozen temporal-61 "
    "value; self-feed three blocks inside public R14.562305898749054; run a "
    "matched stable-prefix control; freeze all candidates, rollouts, selected "
    "actions, states, and emitted sites before constructing the target once"
)
GATE_RULE = (
    "primary transfer requires the marked first block to be exactly 3/3 "
    "colored sites with no false site, the same eight first-block candidates "
    "as the stable-prefix control, and at least as many correct sites as that "
    "control; sustained finite continuation separately requires all three "
    "self-fed blocks and 9/9 sites exact; any missing block, target use before "
    "freeze, source/model drift, duplicate emission, or accounting mismatch "
    "fails closed; neither outcome alone authorizes stationarity or exponential growth"
)


@dataclass(frozen=True)
class StageLocalRolloutConfirmationPreregistration:
    source_commit: str
    source_dataset_digest: str
    source_audit_digest: str
    source_dataset_file_sha256: str
    prefix_model_digest: str
    rollout_model_digest: str
    prefix_model_file_sha256: str
    rollout_model_file_sha256: str
    source_file_sha256s: tuple
    source_hashes_verified: bool
    consumed_domains: int
    grid_minimum: int
    grid_maximum: int
    grid_step: int
    maximum_center_norm: float
    seed_radius: float
    target_radius: float
    safety_margin: float
    required_center_separation: float
    confirmation_center: tuple[float, float, float]
    minimum_consumed_center_separation: float
    center_selection_rule: str
    center_selection_reproduced: bool
    candidate_reach: tuple[int, ...]
    terminal_portfolio_budget: tuple[int, ...]
    self_fed_blocks: int
    sites_per_block: int
    execution_rule: str
    gate_rule: str
    oracle_cropper_executor_scorer_imported: bool
    seed_target_candidates_scores_materialized: bool
    fresh_confirmation_claimed: bool
    manifest_digest: str


def _candidate_grid():
    return tuple(tuple(map(float, center)) for center in itertools.product(
        range(GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3)
        if math.dist((0., 0., 0.), center) <= MAXIMUM_CENTER_NORM)


def select_confirmation_center():
    return max(_candidate_grid(), key=lambda center: (
        min(math.dist(center, prior) for prior in USED_DOMAINS),
        -math.dist((0., 0., 0.), center),
        tuple(-value for value in center)))


def _source_hashes_verified():
    files = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                for name, digest in SOURCE_FILE_SHA256S)
    fixtures = (
        hashlib.sha256((ROOT / "fixtures" /
            "iqc_stage_local_augmented_rollout_development_v1.json.gz").read_bytes()
                       ).hexdigest() == SOURCE_DATASET_FILE_SHA256 and
        hashlib.sha256((ROOT / "fixtures" /
            "iqc_frozen_stage_local_margin_marking_v2.json.gz").read_bytes()
                       ).hexdigest() == PREFIX_MODEL_FILE_SHA256 and
        hashlib.sha256((ROOT / "fixtures" /
            "iqc_frozen_stage_local_rollout_value_v1.json.gz").read_bytes()
                       ).hexdigest() == ROLLOUT_MODEL_FILE_SHA256)
    return files and fixtures


def audit():
    minimum = min(math.dist(CONFIRMATION_CENTER, prior)
                  for prior in USED_DOMAINS)
    body = {
        "source_commit": SOURCE_COMMIT,
        "source_dataset_digest": SOURCE_DATASET_DIGEST,
        "source_audit_digest": SOURCE_AUDIT_DIGEST,
        "source_dataset_file_sha256": SOURCE_DATASET_FILE_SHA256,
        "prefix_model_digest": PREFIX_MODEL_DIGEST,
        "rollout_model_digest": ROLLOUT_MODEL_DIGEST,
        "prefix_model_file_sha256": PREFIX_MODEL_FILE_SHA256,
        "rollout_model_file_sha256": ROLLOUT_MODEL_FILE_SHA256,
        "source_file_sha256s": SOURCE_FILE_SHA256S,
        "source_hashes_verified": _source_hashes_verified(),
        "consumed_domains": len(USED_DOMAINS),
        "grid_minimum": GRID_MINIMUM, "grid_maximum": GRID_MAXIMUM,
        "grid_step": GRID_STEP, "maximum_center_norm": MAXIMUM_CENTER_NORM,
        "seed_radius": SEED_RADIUS, "target_radius": TARGET_RADIUS,
        "safety_margin": SAFETY_MARGIN,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "confirmation_center": CONFIRMATION_CENTER,
        "minimum_consumed_center_separation": minimum,
        "center_selection_rule": CENTER_SELECTION_RULE,
        "center_selection_reproduced":
            select_confirmation_center() == CONFIRMATION_CENTER,
        "candidate_reach": CANDIDATE_REACH,
        "terminal_portfolio_budget": TERMINAL_PORTFOLIO_BUDGET,
        "self_fed_blocks": SELF_FED_BLOCKS,
        "sites_per_block": SITES_PER_BLOCK,
        "execution_rule": EXECUTION_RULE, "gate_rule": GATE_RULE,
        "oracle_cropper_executor_scorer_imported": False,
        "seed_target_candidates_scores_materialized": False,
        "fresh_confirmation_claimed": False,
    }
    digest = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return StageLocalRolloutConfirmationPreregistration(
        **body, manifest_digest=digest)


def main():
    row = audit()
    if EXPECTED_MANIFEST_DIGEST and row.manifest_digest != \
            EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("stage-local rollout confirmation manifest drift")
    print(json.dumps(asdict(row), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
