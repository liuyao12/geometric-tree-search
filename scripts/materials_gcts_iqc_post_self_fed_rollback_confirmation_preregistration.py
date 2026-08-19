#!/usr/bin/env python3
"""Immutable preregistration for a fresh two-block IQC rollback test.

This module is deliberately geometry-only.  It neither imports an oracle nor
constructs a seed or target.  The center is the deterministic maximin point on
a finite public grid after excluding every earlier IQC development or
confirmation center recorded when this protocol was frozen.
"""

from __future__ import annotations

import hashlib
import itertools
import math

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    EXPECTED_ARTIFACT_DIGEST, EXPECTED_FUSION_MODEL_DIGEST)
from materials_gcts_iqc_post_self_fed_marking_portfolio import (
    EXPECTED_AUDIT_DIGEST as PORTFOLIO_AUDIT_DIGEST)
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
    EXPECTED_DATASET_DIGEST as PORT_DISCHARGE_DATASET_DIGEST,
    ROLLOUT_RADIUS)
from materials_gcts_iqc_post_self_fed_port_discharge_value import (
    EXPECTED_AUDIT_DIGEST as PORT_DISCHARGE_AUDIT_DIGEST)
from materials_gcts_iqc_self_fed_terminal_dataset import SECOND_BLOCK_RADIUS


SOURCE_COMMIT = "817d8d59d56de13133e23e701fb2ad68dbd67601"
GRID_MINIMUM = -110
GRID_MAXIMUM = 110
GRID_STEP = 20
MAXIMUM_CENTER_NORM = 100.
PRIOR_NONDEVELOPMENT_CENTERS = (
    (-110., -10., -10.), (-70., -70., 30.), (-50., 0., 0.),
    (-50., 50., -10.), (-25., -20., 20.), (-25., 20., -20.),
    (-20., -20., -25.), (-20., 20., 20.), (-16., 0., 0.),
    (0., -50., 0.), (0., 0., -50.), (0., 0., 50.), (0., 50., 0.),
    (18., 25., 14.), (20., -25., 20.), (20., 20., -25.),
    (30., -25., -20.), (30., 0., 0.), (40., -40., -80.),
    (50., 50., 0.),
)
PRIOR_CENTERS = tuple(sorted(set(
    tuple(map(float, center)) for center in
    tuple(DEVELOPMENT_CENTERS) + PRIOR_NONDEVELOPMENT_CENTERS)))
CONFIRMATION_CENTER = (-70., 10., 70.)
ROLLBACK_METRIC = "frontier_vote_mass"
ROLLBACK_HORIZON = 12
MAXIMUM_RETAINED_CANDIDATES = 2
TARGET_OPEN_LIMIT = 1


def select_confirmation_center():
    rows = []
    for point in itertools.product(
            range(GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3):
        point = tuple(map(float, point))
        norm = math.dist((0., 0., 0.), point)
        if norm > MAXIMUM_CENTER_NORM or point in PRIOR_CENTERS:
            continue
        separation = min(math.dist(point, prior) for prior in PRIOR_CENTERS)
        rows.append((separation, -norm, tuple(-value for value in point),
                     point))
    if not rows:
        raise AssertionError("empty confirmation-center grid")
    return max(rows)[-1]


MANIFEST = {
    "schema_version": 1,
    "source_commit": SOURCE_COMMIT,
    "geometry_rule": "maximin-grid-with-norm-cap",
    "grid_minimum": GRID_MINIMUM,
    "grid_maximum": GRID_MAXIMUM,
    "grid_step": GRID_STEP,
    "maximum_center_norm": MAXIMUM_CENTER_NORM,
    "prior_centers": PRIOR_CENTERS,
    "confirmation_center": CONFIRMATION_CENTER,
    "seed_radius": SEED_RADIUS,
    "first_block_radius": TARGET_RADIUS,
    "second_block_radius": SECOND_BLOCK_RADIUS,
    "rollout_radius": ROLLOUT_RADIUS,
    "minimum_required_domain_separation": 2 * SECOND_BLOCK_RADIUS,
    "frozen_runtime_artifact_digest": EXPECTED_ARTIFACT_DIGEST,
    "frozen_runtime_fusion_model_digest": EXPECTED_FUSION_MODEL_DIGEST,
    "marking_portfolio_audit_digest": PORTFOLIO_AUDIT_DIGEST,
    "port_discharge_dataset_digest": PORT_DISCHARGE_DATASET_DIGEST,
    "port_discharge_audit_digest": PORT_DISCHARGE_AUDIT_DIGEST,
    "rollback_metric": ROLLBACK_METRIC,
    "rollback_horizon": ROLLBACK_HORIZON,
    "maximum_retained_candidates": MAXIMUM_RETAINED_CANDIDATES,
    "target_open_limit": TARGET_OPEN_LIMIT,
    "candidate_and_rollout_receipt_frozen_before_target": True,
    "first_block_selected_target_free": True,
    "second_block_candidates_selected_target_free": True,
    "success_gate": {
        "first_block_exact_actions": 3,
        "portfolio_contains_exact_second_block": True,
        "rollback_selected_exact_second_block": True,
        "end_to_end_correct_actions": 6,
        "target_open_count": 1,
        "raw_training_target_domains_disjoint": True,
    },
    "fresh_confirmation_claim_only_if_gate_passes": True,
    "stationary_or_exponential_claimed": False,
}
EXPECTED_MANIFEST_DIGEST = \
    "695b49cb5b5845e4312b21182d5f2dc33e55012de1564ed30fbdd381017ad725"


def validate_preregistration():
    digest = hashlib.sha256(canonical_json(MANIFEST)).hexdigest()
    reproduced = select_confirmation_center()
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in PRIOR_CENTERS)
    if (reproduced != CONFIRMATION_CENTER
            or separation <= 2 * SECOND_BLOCK_RADIUS
            or math.dist((0., 0., 0.), CONFIRMATION_CENTER)
            > MAXIMUM_CENTER_NORM
            or MANIFEST["stationary_or_exponential_claimed"]
            or not MANIFEST["candidate_and_rollout_receipt_frozen_before_target"]
            or digest != EXPECTED_MANIFEST_DIGEST):
        raise AssertionError("rollback confirmation preregistration drift")
    return digest


if __name__ == "__main__":
    print(validate_preregistration())
