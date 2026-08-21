#!/usr/bin/env python3
"""Geometry-only preregistration for site-resolved self-fed IQC transfer.

This module imports no oracle, cropper, executor, target, or marking fitter.
It freezes a maximin nucleus, the already-published model/source artifacts,
three self-fed waves, and the success/failure rule before atom access.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math

from materials_gcts_iqc_obligation_expanded_preregistration import (
    CONSUMED_CENTERS, DEVELOPMENT_CENTERS)


SOURCE_COMMIT = "d07c051"
SOURCE_DATASET_DIGEST = \
    "5450f477d3968007bcf5a722f9380645dffd972ddd71691af8a9796cfd30e1df"
SITE_LABEL_DATASET_DIGEST = \
    "dfa9ddfc2d770f09c292fc4652c73f5c11ad7f0e61c43b36f71eed7e246dfddf"
SITE_MODEL_AUDIT_DIGEST = \
    "c765264cb0a2b5f1a432c3c03b5ee58fcc3d0ed9ad4565757eedbc69815c7a4c"
FROZEN_MODEL_DIGEST = \
    "891e8badab355abfdeeed5d83a05c62cf34f22962cf193d3ead283a43c6afccc"
SELECTED_SPEC = (("neighbors", 7), ("weighted", True),
                 ("aggregation", "mean"))
SOURCE_FILE_SHA256S = (
    ("materials_gcts_iqc_obligation_site_resolved_audit.py",
     "7e493ac16f291ad084e2f5a27195680f11fd8cae61d104d105078ac9cfba3acf"),
    ("materials_gcts_iqc_obligation_expanded_dataset.py",
     "90d05fd77790926d417da9102a763832de8ff7545459b1e75cdf041d841c6d9c"),
    ("materials_gcts_iqc_obligation_expanded_site_labels.py",
     "ac484d194f0e1545ae8c99db138abf3ec0c94fb202a7e0f0edf011b53b28d8c1"),
    ("materials_gcts_iqc_self_fed_complete_frontier_execution.py",
     "7851ee4313be33db9ac9719e68cb95234967510dc220c12698f89302bcb042fa"),
    ("materials_gcts_iqc_wide_typed_port_discharge_dataset.py",
     "2fb92c6346817b2bc60c355744c4ea168466e259ba16b3e06694d87a530ae244"),
    ("materials_gcts_dual_rank_terminal_portfolio.py",
     "b0074dcbf07138d57f8d82f36597694057e3fe183ce81d2b215bdb22df10fa4a"),
)

GRID_MINIMUM = -200
GRID_MAXIMUM = 200
GRID_STEP = 20
MAXIMUM_CENTER_NORM = 200.
SEED_RADIUS = 9.
TARGET_RADIUS = 14.562305898749054
ROLLOUT_RADIUS = 32.56230589874905
SAFETY_MARGIN = 6.
REQUIRED_CENTER_SEPARATION = 2. * ROLLOUT_RADIUS + SAFETY_MARGIN
CONFIRMATION_CENTER = (0., -120., -160.)
ORACLE_LIFT_BOUND = 108
ACTION_REACH_SCHEDULE = (8, 8, 8)
CANDIDATES_PER_BASE_RANKER = 8
MAXIMUM_FROZEN_CANDIDATES = 16
SELF_FED_WAVES = 3
REQUIRED_EXACT_SITES = 3 * SELF_FED_WAVES
EXPECTED_MANIFEST_DIGEST = \
    "2ac5cd886255452766ec1802f67582d4aed3544c22efe199d908bcfd70a1d2d8"

CONSUMED_DOMAINS = tuple(sorted(set(tuple(map(float, row)) for row in
    tuple(CONSUMED_CENTERS) + tuple(DEVELOPMENT_CENTERS))))

CENTER_SELECTION_RULE = (
    "form the 20-unit grid in [-200,200]^3 with norm <=200; discard points "
    "within 2*32.56230589874905+6 of every consumed centre; maximize the "
    "minimum consumed-centre distance, then minimize norm and break ties "
    "reverse lexicographically"
)
EXECUTION_RULE = (
    "from the colored R9 seed, repeat three times: enumerate the complete "
    "8x8x8 terminal tree inside public R14.562305898749054, retain the union "
    "of the first eight scalar and first eight fusion candidates, roll each "
    "for sixteen target-free relational steps, rank its unchanged compatible "
    "three-site terminal by the frozen site-resolved model, commit top-one, "
    "and use the resulting colored state as the next wave seed"
)
GATE_RULE = (
    "freeze all three wave candidate sets, site scores, selected action IDs, "
    "and execution hashes before one target open; require exact candidate "
    "supply and exact selected 3/3 colored sites at every wave, 9/9 total, "
    "bound+1 crop equality, no target use before scoring, and no retry; "
    "failure consumes the nucleus and leaves autonomous/stationary/exponential "
    "claims red"
)


@dataclass(frozen=True)
class SiteResolvedConfirmationPreregistration:
    source_commit: str
    source_dataset_digest: str
    site_label_dataset_digest: str
    site_model_audit_digest: str
    frozen_model_digest: str
    selected_spec: tuple
    source_file_sha256s: tuple
    consumed_domains: int
    grid_minimum: int
    grid_maximum: int
    grid_step: int
    maximum_center_norm: float
    seed_radius: float
    target_radius: float
    rollout_radius: float
    safety_margin: float
    required_center_separation: float
    confirmation_center: tuple[float, float, float]
    minimum_consumed_center_separation: float
    center_selection_rule: str
    center_selection_reproduced: bool
    oracle_lift_bound: int
    action_reach_schedule: tuple[int, ...]
    candidates_per_base_ranker: int
    maximum_frozen_candidates: int
    self_fed_waves: int
    required_exact_sites: int
    execution_rule: str
    gate_rule: str
    oracle_cropper_executor_or_target_imported: bool
    confirmation_atoms_candidates_scores_or_labels_materialized: bool
    fresh_confirmation_claimed: bool
    manifest_digest: str


def _candidate_grid():
    return tuple(tuple(map(float, point)) for point in itertools.product(
        range(GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3)
        if math.dist((0., 0., 0.), point) <= MAXIMUM_CENTER_NORM and
        min(math.dist(point, prior) for prior in CONSUMED_DOMAINS) >
        REQUIRED_CENTER_SEPARATION)


def _select_center():
    return max(_candidate_grid(), key=lambda point: (
        min(math.dist(point, prior) for prior in CONSUMED_DOMAINS),
        -math.dist((0., 0., 0.), point), tuple(-value for value in point)))


def audit() -> SiteResolvedConfirmationPreregistration:
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in CONSUMED_DOMAINS)
    reproduced = _select_center() == CONFIRMATION_CENTER
    body = {
        "source_commit": SOURCE_COMMIT,
        "source_dataset_digest": SOURCE_DATASET_DIGEST,
        "site_label_dataset_digest": SITE_LABEL_DATASET_DIGEST,
        "site_model_audit_digest": SITE_MODEL_AUDIT_DIGEST,
        "frozen_model_digest": FROZEN_MODEL_DIGEST,
        "selected_spec": SELECTED_SPEC,
        "source_file_sha256s": SOURCE_FILE_SHA256S,
        "consumed_domains": len(CONSUMED_DOMAINS),
        "grid_minimum": GRID_MINIMUM, "grid_maximum": GRID_MAXIMUM,
        "grid_step": GRID_STEP, "maximum_center_norm": MAXIMUM_CENTER_NORM,
        "seed_radius": SEED_RADIUS, "target_radius": TARGET_RADIUS,
        "rollout_radius": ROLLOUT_RADIUS,
        "safety_margin": SAFETY_MARGIN,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "confirmation_center": CONFIRMATION_CENTER,
        "minimum_consumed_center_separation": separation,
        "center_selection_rule": CENTER_SELECTION_RULE,
        "center_selection_reproduced": reproduced,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "action_reach_schedule": ACTION_REACH_SCHEDULE,
        "candidates_per_base_ranker": CANDIDATES_PER_BASE_RANKER,
        "maximum_frozen_candidates": MAXIMUM_FROZEN_CANDIDATES,
        "self_fed_waves": SELF_FED_WAVES,
        "required_exact_sites": REQUIRED_EXACT_SITES,
        "execution_rule": EXECUTION_RULE, "gate_rule": GATE_RULE,
        "oracle_cropper_executor_or_target_imported": False,
        "confirmation_atoms_candidates_scores_or_labels_materialized": False,
        "fresh_confirmation_claimed": False,
    }
    digest = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return SiteResolvedConfirmationPreregistration(*body.values(), digest)


def main():
    row = audit()
    if EXPECTED_MANIFEST_DIGEST and row.manifest_digest != \
            EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("site-resolved confirmation manifest drift")
    print(json.dumps(asdict(row), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
