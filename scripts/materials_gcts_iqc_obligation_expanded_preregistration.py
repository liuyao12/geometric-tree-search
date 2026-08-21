#!/usr/bin/env python3
"""Geometry-only preregistration of expanded IQC obligation development.

This module imports no oracle, cropper, executor, marking fitter, scorer, or
target fixture.  It freezes twenty new development nuclei whose *complete
rollout dependency balls* are disjoint from one another and from every prior
IQC development/confirmation centre.  The batch is consumed development data,
not a fresh confirmation, and every result must remain in the corpus.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, PRIOR_CENTERS)


SOURCE_COMMIT = "ef499a4"
GRID_MINIMUM = -240
GRID_MAXIMUM = 240
GRID_STEP = 30
MAXIMUM_CENTER_NORM = 240.
BATCH_SIZE = 20
SEED_RADIUS = 9.
TARGET_RADIUS = 14.562305898749054
ROLLOUT_RADIUS = 32.56230589874905
ROLLOUT_HORIZON = 16
SAFETY_MARGIN = 6.
REQUIRED_CENTER_SEPARATION = 2. * ROLLOUT_RADIUS + SAFETY_MARGIN
ORACLE_LIFT_BOUND = 120
ACTION_REACH_SCHEDULE = (8, 8, 8)
CANDIDATES_PER_BASE_RANKER = 8
MAXIMUM_FROZEN_CANDIDATES = 16
SHUFFLES = 31
SHUFFLE_SEED = 781337
EXPECTED_MANIFEST_DIGEST = \
    "c13c73a3215b1ad3e3ff4a3a1e56bf8f25616cfa14698030b63538208523156e"

ADDITIONAL_CONSUMED_CENTERS = (
    (-110., -70., -70.),  # consumed obligation confirmation
    (-70., 10., 70.),     # retired/consumed autonomous attempt
)
CONSUMED_CENTERS = tuple(sorted(set(
    tuple(map(float, row)) for row in
    tuple(PRIOR_CENTERS) + tuple(DEVELOPMENT_CENTERS) +
    ADDITIONAL_CONSUMED_CENTERS)))

DEVELOPMENT_CENTERS = (
    (210., 60., -90.), (210., 60., 90.), (60., 210., 90.),
    (-150., 180., 30.), (60., -210., 90.), (-240., 0., 0.),
    (60., 90., 210.), (60., 90., -210.), (60., -90., 210.),
    (-120., -90., 180.), (-30., 210., -90.), (-90., 60., -210.),
    (210., -90., 60.), (90., -210., -60.), (-90., 120., 180.),
    (0., -150., -180.), (120., 180., -90.), (180., -90., -120.),
    (-60., -210., -60.), (-180., 120., -90.),
)

CENTER_SELECTION_RULE = (
    "form the 30-unit grid in [-240,240]^3 with norm <=240; discard points "
    "within 2*32.56230589874905+6 of a consumed centre; repeatedly select "
    "the point maximizing its minimum distance from consumed and already "
    "selected centres, then minimize radial norm and break ties reverse "
    "lexicographically; retain twenty"
)
CANDIDATE_RULE = (
    "for every colored R9 seed, enumerate the complete frozen 8x8x8 "
    "three-action frontier inside public R14.562305898749054; retain the "
    "union of the first eight scalar and first eight fusion candidates"
)
GEOMETRY_FREEZE_RULE = (
    "roll every retained action for sixteen deterministic pose-port steps "
    "inside public R32.56230589874905 and serialize all identity-free "
    "relational transitions before constructing or joining that nucleus' "
    "R14.562305898749054 target"
)
DEVELOPMENT_GATE = (
    "retain every nucleus including zero-supply and label-trivial cases; "
    "fit/spec-select only by leave-one-nucleus-out replay; repeat full "
    "selection after 31 within-nucleus label shuffles; require top-action "
    "superiority p<=.05 before any new confirmation is eligible"
)


@dataclass(frozen=True)
class IQCObligationExpandedPreregistration:
    source_commit: str
    consumed_centers: int
    development_centers: tuple[tuple[float, float, float], ...]
    batch_size: int
    grid_minimum: int
    grid_maximum: int
    grid_step: int
    maximum_center_norm: float
    seed_radius: float
    target_radius: float
    rollout_radius: float
    rollout_horizon: int
    safety_margin: float
    required_center_separation: float
    minimum_consumed_center_separation: float
    minimum_batch_center_separation: float
    rollout_domains_disjoint: bool
    center_selection_rule: str
    center_selection_reproduced: bool
    oracle_lift_bound: int
    action_reach_schedule: tuple[int, ...]
    candidates_per_base_ranker: int
    maximum_frozen_candidates: int
    candidate_rule: str
    geometry_freeze_rule: str
    shuffle_trials: int
    shuffle_seed: int
    development_gate: str
    oracle_or_cropper_imported: bool
    seed_target_candidates_or_scores_materialized: bool
    fresh_confirmation_claimed: bool
    manifest_digest: str


def _candidate_grid():
    return tuple(tuple(map(float, center)) for center in itertools.product(
        range(GRID_MINIMUM, GRID_MAXIMUM + 1, GRID_STEP), repeat=3)
        if math.dist((0., 0., 0.), center) <= MAXIMUM_CENTER_NORM
        and min(math.dist(center, prior)
                for prior in CONSUMED_CENTERS) >
        REQUIRED_CENTER_SEPARATION)


def _select_centers():
    candidates = _candidate_grid()
    selected = []
    consumed = set(CONSUMED_CENTERS)
    while len(selected) < BATCH_SIZE:
        pool = tuple(center for center in candidates
                     if center not in selected and all(
                         math.dist(center, prior) >
                         REQUIRED_CENTER_SEPARATION for prior in selected))
        if not pool:
            raise AssertionError("insufficient disjoint development centres")
        selected.append(max(pool, key=lambda center: (
            min(math.dist(center, prior)
                for prior in consumed | set(selected)),
            -math.dist((0., 0., 0.), center),
            tuple(-value for value in center))))
    return tuple(selected)


def _minimum_pairwise(rows):
    return min(math.dist(left, right)
               for index, left in enumerate(rows)
               for right in rows[index + 1:])


def audit() -> IQCObligationExpandedPreregistration:
    minimum_consumed = min(math.dist(center, prior)
                           for center in DEVELOPMENT_CENTERS
                           for prior in CONSUMED_CENTERS)
    minimum_batch = _minimum_pairwise(DEVELOPMENT_CENTERS)
    reproduced = _select_centers() == DEVELOPMENT_CENTERS
    disjoint = (minimum_consumed > REQUIRED_CENTER_SEPARATION and
                minimum_batch > REQUIRED_CENTER_SEPARATION and reproduced)
    body = {
        "source_commit": SOURCE_COMMIT,
        "consumed_centers": len(CONSUMED_CENTERS),
        "development_centers": DEVELOPMENT_CENTERS,
        "batch_size": BATCH_SIZE,
        "grid_minimum": GRID_MINIMUM,
        "grid_maximum": GRID_MAXIMUM,
        "grid_step": GRID_STEP,
        "maximum_center_norm": MAXIMUM_CENTER_NORM,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "rollout_radius": ROLLOUT_RADIUS,
        "rollout_horizon": ROLLOUT_HORIZON,
        "safety_margin": SAFETY_MARGIN,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "minimum_consumed_center_separation": minimum_consumed,
        "minimum_batch_center_separation": minimum_batch,
        "rollout_domains_disjoint": disjoint,
        "center_selection_rule": CENTER_SELECTION_RULE,
        "center_selection_reproduced": reproduced,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "action_reach_schedule": ACTION_REACH_SCHEDULE,
        "candidates_per_base_ranker": CANDIDATES_PER_BASE_RANKER,
        "maximum_frozen_candidates": MAXIMUM_FROZEN_CANDIDATES,
        "candidate_rule": CANDIDATE_RULE,
        "geometry_freeze_rule": GEOMETRY_FREEZE_RULE,
        "shuffle_trials": SHUFFLES,
        "shuffle_seed": SHUFFLE_SEED,
        "development_gate": DEVELOPMENT_GATE,
        "oracle_or_cropper_imported": False,
        "seed_target_candidates_or_scores_materialized": False,
        "fresh_confirmation_claimed": False,
    }
    digest = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return IQCObligationExpandedPreregistration(*body.values(), digest)


def main():
    row = audit()
    if row.manifest_digest != EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("expanded obligation manifest drift")
    print(json.dumps(asdict(row), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
