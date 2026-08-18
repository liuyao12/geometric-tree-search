#!/usr/bin/env python3
"""Preregister an expanded disjoint IQC development corpus.

This module contains geometry and protocol metadata only.  It deliberately
does not import an oracle, seed cropper, target factory, candidate generator,
or scorer.  The declared centers must be committed before a separate harness
may materialize any of their atoms.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass


SOURCE_COMMIT = "524171a55a1a07b7acf3e2c79b99cf5fa4a7f2c8"
TARGET_RADIUS = 14.562305898749054
REQUIRED_CENTER_SEPARATION = 2. * TARGET_RADIUS
PRIOR_DEVELOPMENT_CENTERS = (
    (0., 0., 0.), (30., 0., 0.), (18., 25., 14.),
    (-20., 20., 20.), (20., -25., 20.), (-20., -20., -25.),
    (-25., 20., -20.), (-25., -20., 20.), (30., -25., -20.),
    (0., 0., -50.),
)
RESERVED_CONFIRMATION_CENTER = (0., 50., 0.)
EXPANDED_DEVELOPMENT_CENTERS = (
    (10., 30., -30.),
    (10., 10., 50.),
    (50., 10., -30.),
    (50., 10., 30.),
    (-70., -10., -10.),
    (-50., -50., -10.),
    (-50., -10., -50.),
    (-50., -10., 50.),
)
SELECTION_RULE = (
    "lexicographic greedy centers from the fixed Cartesian grid "
    "{-70,-50,-30,-10,10,30,50,70}^3 inside radius 105; require distance "
    ">36 from every prior, reserved, and earlier selected center"
)


@dataclass(frozen=True)
class ExpandedDevelopmentPreregistration:
    source_commit: str
    target_radius: float
    required_center_separation: float
    prior_development_centers: tuple[tuple[float, float, float], ...]
    reserved_confirmation_center: tuple[float, float, float]
    expanded_development_centers: tuple[tuple[float, float, float], ...]
    selection_rule: str
    minimum_new_to_existing_or_reserved_separation: float
    minimum_new_to_new_separation: float
    domains_disjoint: bool
    seed_or_target_materialized: bool
    candidate_or_score_computed: bool
    manifest_digest: str


def _minimum_cross(left, right):
    return min(math.dist(first, second) for first in left for second in right)


def audit() -> ExpandedDevelopmentPreregistration:
    existing = PRIOR_DEVELOPMENT_CENTERS + (RESERVED_CONFIRMATION_CENTER,)
    cross = _minimum_cross(EXPANDED_DEVELOPMENT_CENTERS, existing)
    pairwise = min(math.dist(first, second)
                   for index, first in enumerate(EXPANDED_DEVELOPMENT_CENTERS)
                   for second in EXPANDED_DEVELOPMENT_CENTERS[index + 1:])
    disjoint = cross > REQUIRED_CENTER_SEPARATION and \
        pairwise > REQUIRED_CENTER_SEPARATION
    payload = {
        "source_commit": SOURCE_COMMIT,
        "target_radius": TARGET_RADIUS,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "prior_development_centers": PRIOR_DEVELOPMENT_CENTERS,
        "reserved_confirmation_center": RESERVED_CONFIRMATION_CENTER,
        "expanded_development_centers": EXPANDED_DEVELOPMENT_CENTERS,
        "selection_rule": SELECTION_RULE,
        "minimum_new_to_existing_or_reserved_separation": cross,
        "minimum_new_to_new_separation": pairwise,
        "domains_disjoint": disjoint,
        "seed_or_target_materialized": False,
        "candidate_or_score_computed": False,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return ExpandedDevelopmentPreregistration(
        SOURCE_COMMIT, TARGET_RADIUS, REQUIRED_CENTER_SEPARATION,
        PRIOR_DEVELOPMENT_CENTERS, RESERVED_CONFIRMATION_CENTER,
        EXPANDED_DEVELOPMENT_CENTERS, SELECTION_RULE, cross, pairwise,
        disjoint, False, False, digest)


def main():
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

