#!/usr/bin/env python3
"""Geometry-only preregistration for a fresh stage-local IQC confirmation.

This module imports no oracle, cropper, executor, scorer, or target.  It freezes
the already-fitted marking artifact, a deterministic maximin nucleus, three
self-fed waves, matched pose/port control work, and the one-open success rule.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path

from materials_gcts_iqc_obligation_expanded_preregistration import (
    CONSUMED_CENTERS, DEVELOPMENT_CENTERS)
from materials_gcts_iqc_site_resolved_confirmation_preregistration import (
    CONFIRMATION_CENTER as CONSUMED_SITE_CONFIRMATION_CENTER)


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "6fba644"
SOURCE_DATASET_DIGEST = \
    "5bab03312f0c2fd52e746bb7a2218097a7d65aaed4eb77bbf23a858646bfc961"
SOURCE_AUDIT_DIGEST = \
    "8b2449ff42240ba4f4ba4ae2fed8b0c836d278ffb14b9703ae71cdfc0341a582"
FROZEN_MODEL_DIGEST = \
    "28db73d00f9a38a134ef5b31322763fa7872376df2b23e44281d0a1207242a56"
FROZEN_MODEL_FILE_SHA256 = \
    "4b405f46f1bd89a8b422764f022266202af816b149a69be6a2b7fb5213a471c1"
SOURCE_FILE_SHA256S = (
    ("materials_gcts_iqc_frozen_stage_local_prefix_marking.py",
     "edbac4a058a74005fbad884776c2b83006c5a9c8cbef33f28b8103e5ef89d6a2"),
    ("materials_gcts_iqc_stage_local_prefix_runtime.py",
     "ee04ffaa73dde5b3b98b222b21a743ab0ceb54972f0a144812717cf03affe0f3"),
    ("materials_gcts_iqc_stage_local_prefix_dataset.py",
     "7ee6d2c7f2cbb87a50699e77b04cb2460c569b7b26d6b1054c28bfb6ee169d3f"),
    ("materials_gcts_iqc_stage_local_prefix_marking_audit.py",
     "9671204d1ab414810eb646b054f3f12841ea12af2261710b0864e59530eed3ca"),
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
RETAINED_PREFIX_BUDGET = (2, 4, 1)
SELF_FED_WAVES = 3
REQUIRED_EXACT_SITES = 3 * SELF_FED_WAVES
CONFIRMATION_CENTER = (-140., -200., 80.)
EXPECTED_MANIFEST_DIGEST = \
    "f9c7c605c8aa81e2f52787345c4fac4ae5b805bf02b3519c27d161ed80678a9f"


CONSUMED_DOMAINS = tuple(sorted(set(tuple(map(float, row)) for row in
    tuple(CONSUMED_CENTERS) + tuple(DEVELOPMENT_CENTERS) +
    (CONSUMED_SITE_CONFIRMATION_CENTER,))))

CENTER_SELECTION_RULE = (
    "form the 20-unit grid in [-260,260]^3 with norm <=260; maximize minimum "
    "distance from all 83 consumed IQC centers, then minimize norm and break "
    "ties reverse lexicographically; require target-ball separation above "
    "2*14.562305898749054+6"
)
EXECUTION_RULE = (
    "from the colored R9 seed, execute both the frozen stage-local marking "
    "and cumulative pose/port baseline for three self-fed waves inside public "
    "R14.562305898749054; at each wave enumerate 12->4->8 proposals and retain "
    "2->4->1 prefixes; freeze every candidate/action/state digest for both "
    "arms before constructing the target exactly once"
)
GATE_RULE = (
    "require the marked arm to select exact 3/3 colored sites in each of "
    "three waves (9/9 total), zero wrong sites, exact candidate and state "
    "accounting, immutable model/source hashes, target_used=false through "
    "execution, one target open after both arms freeze, and at least as many "
    "correct sites as the matched pose/port baseline; report baseline outcome "
    "without changing the gate after opening"
)


@dataclass(frozen=True)
class StageLocalPrefixConfirmationPreregistration:
    source_commit: str
    source_dataset_digest: str
    source_audit_digest: str
    frozen_model_digest: str
    frozen_model_file_sha256: str
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
    retained_prefix_budget: tuple[int, ...]
    self_fed_waves: int
    required_exact_sites: int
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
        min(math.dist(center, prior) for prior in CONSUMED_DOMAINS),
        -math.dist((0., 0., 0.), center),
        tuple(-value for value in center)))


def _source_hashes_verified():
    return all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
               for name, digest in SOURCE_FILE_SHA256S) and \
        hashlib.sha256((ROOT / "fixtures" /
            "iqc_frozen_stage_local_prefix_marking_v1.json.gz").read_bytes()
                       ).hexdigest() == FROZEN_MODEL_FILE_SHA256


def audit():
    minimum = min(math.dist(CONFIRMATION_CENTER, prior)
                  for prior in CONSUMED_DOMAINS)
    body = {
        "source_commit": SOURCE_COMMIT,
        "source_dataset_digest": SOURCE_DATASET_DIGEST,
        "source_audit_digest": SOURCE_AUDIT_DIGEST,
        "frozen_model_digest": FROZEN_MODEL_DIGEST,
        "frozen_model_file_sha256": FROZEN_MODEL_FILE_SHA256,
        "source_file_sha256s": SOURCE_FILE_SHA256S,
        "source_hashes_verified": _source_hashes_verified(),
        "consumed_domains": len(CONSUMED_DOMAINS),
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
        "retained_prefix_budget": RETAINED_PREFIX_BUDGET,
        "self_fed_waves": SELF_FED_WAVES,
        "required_exact_sites": REQUIRED_EXACT_SITES,
        "execution_rule": EXECUTION_RULE, "gate_rule": GATE_RULE,
        "oracle_cropper_executor_scorer_imported": False,
        "seed_target_candidates_scores_materialized": False,
        "fresh_confirmation_claimed": False,
    }
    digest = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return StageLocalPrefixConfirmationPreregistration(
        **body, manifest_digest=digest)


def main():
    row = audit()
    if EXPECTED_MANIFEST_DIGEST and row.manifest_digest != \
            EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("stage-local confirmation manifest drift")
    print(json.dumps(asdict(row), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
