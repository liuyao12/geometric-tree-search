#!/usr/bin/env python3
"""Geometry-only preregistration for the obligation-automaton confirmation.

This module imports no oracle, cropper, candidate generator, scorer, or target
fixture.  It freezes a new maximin nucleus and the complete target-open order
before any atom at that nucleus is generated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, PRIOR_CENTERS)


SOURCE_COMMIT = "c7d160071532d596ba5bf6f55705e8e5e3dbede0"
GRID_MINIMUM = -150
GRID_MAXIMUM = 150
GRID_STEP = 20
MAXIMUM_CENTER_NORM = 150.
SEED_RADIUS = 9.
TARGET_RADIUS = 14.562305898749054
ROLLOUT_RADIUS = 32.56230589874905
ROLLOUT_HORIZON = 16
SAFETY_MARGIN = 6.
REQUIRED_CENTER_SEPARATION = 2. * ROLLOUT_RADIUS + SAFETY_MARGIN
ORACLE_LIFT_BOUND = 72
CONFIRMATION_CENTER = (-110., -70., -70.)
ADDITIONAL_CONSUMED_CENTERS = ((-70., 10., 70.),)
CONSUMED_CENTERS = tuple(sorted(set(
    tuple(map(float, row)) for row in
    tuple(PRIOR_CENTERS) + tuple(DEVELOPMENT_CENTERS) +
    ADDITIONAL_CONSUMED_CENTERS)))

AUTOMATON_SPEC = {
    "count_cap": 4,
    "minimum_groups": 1,
    "weakest_states": 4,
}
EXPECTED_TRAINING_DATASET_DIGEST = \
    "aecda621ca1f0960cdd14a74995983d2483a94ed52051bd273082d0cc59ab3de"
EXPECTED_TRAINING_GEOMETRY_DIGEST = \
    "b6c599386e04c46b9dcadf710f037316224dc66e3b8e0f5e5b50d396de6cfab4"
EXPECTED_AUTOMATON_MODEL_DIGEST = \
    "ad001ae110fdb54c43950a9a37c25512cbca87605254b3a0caf6e5991465804f"
EXPECTED_AUTOMATON_AUDIT_DIGEST = \
    "ebb0abf7492d478bbd4921890a5fc95d1618b53620bebae9b08b5756be8a92ef"

ACTION_REACH_SCHEDULE = (8, 8, 8)
CANDIDATES_PER_BASE_RANKER = 8
MAXIMUM_FROZEN_CANDIDATES = 16
TARGET_OPEN_LIMIT = 1
SOURCE_FILE_HASHES = (
    ("materials_gcts_port_obligation_automaton.py",
     "c3efd11c87977638e47a2c2a930eb202c2fd4a35ad3e5e619d98996a70ae74eb"),
    ("materials_gcts_iqc_port_obligation_automaton_audit.py",
     "04786480e472a332476f94b80ffb30557d56d20c922c264d73226b8c55f80b1d"),
    ("materials_gcts_iqc_self_fed_complete_frontier_execution.py",
     "7851ee4313be33db9ac9719e68cb95234967510dc220c12698f89302bcb042fa"),
    ("materials_gcts_iqc_wide_typed_port_discharge_dataset.py",
     "2fb92c6346817b2bc60c355744c4ea168466e259ba16b3e06694d87a530ae244"),
    ("materials_gcts_iqc_relational_port_discharge_dataset.py",
     "8d56cdad27a2e7ff9bb59c8136eeae551403151324d589671e66ed329bbc2577"),
)
EXPECTED_MANIFEST_DIGEST = \
    "0a4396b0ce6a13555d5baeafede7bdfd4bd9fe82b6aa2d90b0ec6cc76a586013"

CENTER_SELECTION_RULE = (
    "over the 20-unit grid in [-150,150]^3 with norm <=150, maximize the "
    "minimum Euclidean distance from every consumed center; then minimize "
    "radial norm and break remaining ties reverse lexicographically"
)
CANDIDATE_RULE = (
    "from the colored R9 seed enumerate the complete frozen 8x8x8 "
    "three-action frontier inside public R14.562305898749054; retain the "
    "union of the first eight scalar and first eight fusion candidates"
)
VALUE_RULE = (
    "roll every retained exact candidate target-free for 16 deterministic "
    "pose-port steps inside public R32.56230589874905; map each transition "
    "to the frozen cap4 identity-free obligation state; rank by the mean "
    "posterior of the four weakest recognized states, then stable action key"
)
TARGET_OPEN_RULE = (
    "serialize and hash seed, complete candidate universe, retained IDs, "
    "all 16-step trajectories, automaton scores, and selected action before "
    "one target factory call; afterward score only and never refit, rerank, "
    "or execute again"
)
SUCCESS_GATE = {
    "oracle_bound_plus_one_stable": True,
    "target_open_count": 1,
    "candidate_portfolio_contains_exact": True,
    "selected_action_exact_sites": 3,
    "selected_action_false_sites": 0,
    "selected_rollout_steps": ROLLOUT_HORIZON,
    "raw_training_rollout_domains_disjoint": True,
}


@dataclass(frozen=True)
class PortObligationConfirmationPreregistration:
    source_commit: str
    confirmation_center: tuple[float, float, float]
    consumed_centers: int
    minimum_consumed_center_separation: float
    required_center_separation: float
    rollout_domains_disjoint: bool
    center_selection_rule: str
    center_selection_reproduced: bool
    seed_radius: float
    target_radius: float
    rollout_radius: float
    rollout_horizon: int
    oracle_lift_bound: int
    automaton_spec: dict
    expected_training_dataset_digest: str
    expected_training_geometry_digest: str
    expected_automaton_model_digest: str
    expected_automaton_audit_digest: str
    action_reach_schedule: tuple[int, ...]
    candidates_per_base_ranker: int
    maximum_frozen_candidates: int
    candidate_rule: str
    value_rule: str
    target_open_rule: str
    target_open_limit: int
    success_gate: dict
    source_file_hashes: tuple[tuple[str, str], ...]
    source_hashes_match: bool
    seed_or_target_materialized: bool
    candidates_or_scores_computed: bool
    manifest_digest: str


def _select_center():
    rows = []
    for point in itertools.product(
            range(GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3):
        point = tuple(map(float, point))
        norm = math.dist((0., 0., 0.), point)
        if norm > MAXIMUM_CENTER_NORM or point in CONSUMED_CENTERS:
            continue
        separation = min(math.dist(point, prior)
                         for prior in CONSUMED_CENTERS)
        rows.append((separation, -norm, tuple(-value for value in point),
                     point))
    if not rows:
        raise AssertionError("confirmation-center grid is empty")
    return max(rows)[-1]


def _file_hash(filename):
    return hashlib.sha256((Path(__file__).resolve().parent /
                           filename).read_bytes()).hexdigest()


def audit():
    separation = min(math.dist(CONFIRMATION_CENTER, prior)
                     for prior in CONSUMED_CENTERS)
    values = {
        "source_commit": SOURCE_COMMIT,
        "confirmation_center": CONFIRMATION_CENTER,
        "consumed_centers": len(CONSUMED_CENTERS),
        "minimum_consumed_center_separation": separation,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "rollout_domains_disjoint": separation > REQUIRED_CENTER_SEPARATION,
        "center_selection_rule": CENTER_SELECTION_RULE,
        "center_selection_reproduced": _select_center() == CONFIRMATION_CENTER,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "rollout_radius": ROLLOUT_RADIUS,
        "rollout_horizon": ROLLOUT_HORIZON,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "automaton_spec": AUTOMATON_SPEC,
        "expected_training_dataset_digest": EXPECTED_TRAINING_DATASET_DIGEST,
        "expected_training_geometry_digest": EXPECTED_TRAINING_GEOMETRY_DIGEST,
        "expected_automaton_model_digest": EXPECTED_AUTOMATON_MODEL_DIGEST,
        "expected_automaton_audit_digest": EXPECTED_AUTOMATON_AUDIT_DIGEST,
        "action_reach_schedule": ACTION_REACH_SCHEDULE,
        "candidates_per_base_ranker": CANDIDATES_PER_BASE_RANKER,
        "maximum_frozen_candidates": MAXIMUM_FROZEN_CANDIDATES,
        "candidate_rule": CANDIDATE_RULE,
        "value_rule": VALUE_RULE,
        "target_open_rule": TARGET_OPEN_RULE,
        "target_open_limit": TARGET_OPEN_LIMIT,
        "success_gate": SUCCESS_GATE,
        "source_file_hashes": SOURCE_FILE_HASHES,
        "source_hashes_match": all(_file_hash(name) == digest
                                   for name, digest in SOURCE_FILE_HASHES),
        "seed_or_target_materialized": False,
        "candidates_or_scores_computed": False,
    }
    digest = hashlib.sha256(json.dumps(
        values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return PortObligationConfirmationPreregistration(
        *values.values(), digest)


def validate_preregistration(expected_digest=EXPECTED_MANIFEST_DIGEST):
    report = audit()
    if (not report.rollout_domains_disjoint
            or not report.center_selection_reproduced
            or not report.source_hashes_match
            or report.seed_or_target_materialized
            or report.candidates_or_scores_computed
            or (expected_digest and report.manifest_digest != expected_digest)):
        raise AssertionError("port-obligation confirmation manifest drift")
    return report


def main():
    print(json.dumps(asdict(validate_preregistration()),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
