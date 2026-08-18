#!/usr/bin/env python3
"""Freeze ten new IQC development nuclei before any atom is generated.

This is a geometry-only manifest.  It deliberately imports no oracle,
cropper, candidate generator, marking fitter, or scorer.  The batch is for an
unchanged-policy transfer audit, not a fresh confirmation and not another
hyperparameter search.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import asdict, dataclass


SOURCE_COMMIT = "79c12bd6047c9dc6ba34564dbe574cc8a58847a1"
SEED_RADIUS = 9.0
TARGET_RADIUS = 14.562305898749054
ORACLE_LIFT_BOUND = 44
SAFETY_MARGIN = 6.0
REQUIRED_CENTER_SEPARATION = 2. * TARGET_RADIUS + SAFETY_MARGIN
FROZEN_FUSION_MODEL_DIGEST = \
    "505b65481e3fe2cc25a284ba8dc175e3a794465c2c7bd726f5448c1fac6bbef5"
FROZEN_FUSION_CAPACITY = ("incidence", 1, 2.0)

# This conservative exclusion list contains every literal IQC development,
# diagnostic, failed-attempt, and confirmation centre committed before this
# manifest.  Some small-radius diagnostics did not use the radius below; they
# remain excluded anyway so the new target balls cannot be mistaken for fresh
# evidence in a later experiment.
PRIOR_CENTERS = (
    (-70., -70., 30.), (-70., -10., -10.), (-60., 40., 40.),
    (-50., -50., -10.), (-50., -10., -50.), (-50., -10., 50.),
    (-50., 0., 0.), (-50., 50., -10.), (-25., -20., 20.),
    (-25., 20., -20.), (-20., -80., 20.), (-20., -60., -60.),
    (-20., -60., 60.), (-20., -20., -25.), (-20., 20., 20.),
    (-20., 60., -60.), (-20., 60., 60.), (-18.5, -1.5, 1.5),
    (-17.5, 2.5, -1.5), (-16., 0., 0.), (-14.5, -2.5, -1.5),
    (-13.5, 1.5, 1.5), (-4., 20., 0.), (0., -80., -20.),
    (0., -50., 0.), (0., 0., -50.), (0., 0., 0.), (0., 0., 50.),
    (0., 8., -20.), (0., 8., 20.), (0., 50., 0.), (0., 80., 0.),
    (8., -12., -12.), (8., -12., 12.), (10., 10., 50.),
    (10., 30., -30.), (16., 8., -4.), (18., 25., 14.),
    (20., -25., 20.), (20., 20., -25.), (30., -25., -20.),
    (30., 0., 0.), (40., -40., -80.), (40., -40., 60.),
    (50., 10., -30.), (50., 10., 30.), (50., 50., 0.),
    (60., -60., 20.), (60., 60., 0.), (80., -20., 0.))

DEVELOPMENT_CENTERS = (
    (-70., 30., -50.), (-10., -10., -90.), (-10., -10., 90.),
    (10., 30., -70.), (30., -70., -50.), (30., 50., 50.),
    (30., 70., -50.), (50., 10., -70.), (50., 10., 70.),
    (70., -50., -30.))

CENTER_SELECTION_RULE = (
    "lexicographic greedy points in {-90,-70,...,90}^3 with norm <= 92; "
    "require distance > 2*14.562305898749054+6 from every prior and earlier "
    "selected centre; take the first ten"
)
NO_REFIT_RULE = (
    "new atoms and labels may not change the irregular-support vocabulary, "
    "candidate geometry, scalar section, graph features, model weights, "
    "fusion capacity, rank tie rule, or search work; fit and every candidate "
    "digest freeze before any target labels open"
)
BATCH_GATE = (
    "report supplied/exact nuclei and correct moves for the frozen fusion and "
    "its frozen scalar incumbent on identical candidates; open all ten once, "
    "retain failures, and do not reinterpret the batch as confirmation"
)


@dataclass(frozen=True)
class IQCExtendedDevelopmentPreregistration:
    source_commit: str
    seed_radius: float
    target_radius: float
    oracle_lift_bound: int
    safety_margin: float
    required_center_separation: float
    prior_centers: tuple[tuple[float, float, float], ...]
    development_centers: tuple[tuple[float, float, float], ...]
    center_selection_rule: str
    minimum_prior_separation: float
    minimum_batch_separation: float
    maximum_center_norm: float
    selection_rule_reproduced: bool
    target_balls_disjoint: bool
    frozen_fusion_model_digest: str
    frozen_fusion_capacity: tuple[str, int, float]
    no_refit_rule: str
    batch_gate: str
    oracle_or_cropper_imported: bool
    seed_or_target_materialized: bool
    candidates_or_scores_computed: bool
    manifest_digest: str


def _minimum_pairwise(rows):
    return min(math.dist(first, second)
               for index, first in enumerate(rows)
               for second in rows[index + 1:])


def _select_centers():
    selected = []
    for center in itertools.product(range(-90, 91, 20), repeat=3):
        if math.dist((0., 0., 0.), center) > 92.:
            continue
        if min(math.dist(center, prior) for prior in PRIOR_CENTERS) <= \
                REQUIRED_CENTER_SEPARATION:
            continue
        if any(math.dist(center, prior) <= REQUIRED_CENTER_SEPARATION
               for prior in selected):
            continue
        selected.append(tuple(map(float, center)))
        if len(selected) == 10:
            break
    return tuple(selected)


def audit() -> IQCExtendedDevelopmentPreregistration:
    prior = min(math.dist(center, other)
                for center in DEVELOPMENT_CENTERS for other in PRIOR_CENTERS)
    batch = _minimum_pairwise(DEVELOPMENT_CENTERS)
    maximum_norm = max(math.dist((0., 0., 0.), center)
                       for center in DEVELOPMENT_CENTERS)
    reproduced = _select_centers() == DEVELOPMENT_CENTERS
    disjoint = prior > REQUIRED_CENTER_SEPARATION and \
        batch > REQUIRED_CENTER_SEPARATION and reproduced
    payload = {
        "source_commit": SOURCE_COMMIT,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "safety_margin": SAFETY_MARGIN,
        "required_center_separation": REQUIRED_CENTER_SEPARATION,
        "prior_centers": PRIOR_CENTERS,
        "development_centers": DEVELOPMENT_CENTERS,
        "center_selection_rule": CENTER_SELECTION_RULE,
        "minimum_prior_separation": prior,
        "minimum_batch_separation": batch,
        "maximum_center_norm": maximum_norm,
        "selection_rule_reproduced": reproduced,
        "target_balls_disjoint": disjoint,
        "frozen_fusion_model_digest": FROZEN_FUSION_MODEL_DIGEST,
        "frozen_fusion_capacity": FROZEN_FUSION_CAPACITY,
        "no_refit_rule": NO_REFIT_RULE,
        "batch_gate": BATCH_GATE,
        "oracle_or_cropper_imported": False,
        "seed_or_target_materialized": False,
        "candidates_or_scores_computed": False,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return IQCExtendedDevelopmentPreregistration(
        *payload.values(), digest)


if __name__ == "__main__":
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))
