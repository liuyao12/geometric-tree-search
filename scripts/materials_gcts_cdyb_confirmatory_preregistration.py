#!/usr/bin/env python3
"""Immutable geometry and gates for the next sealed Cd--Yb confirmation.

This module deliberately contains no oracle constructor and no scoring target.
Importing it can freeze the experiment before any atom at the confirmatory
centre is materialized.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CdYbConfirmatoryProtocol:
    version: str
    train_centers: tuple[tuple[float, float, float], ...]
    previously_opened_evaluation_center: tuple[float, float, float]
    confirmatory_center: tuple[float, float, float]
    train_seed_radius: float
    train_target_radius: float
    confirmatory_seed_radius: float
    confirmatory_target_radius: float
    oracle_max_index: int
    oracle_cube_side_angstrom: float
    shuffle_trials: int
    minimum_action_precision: float
    minimum_site_precision: float
    minimum_recoverable_action_recall: float
    maximum_empirical_p: float
    minimum_work_reduction: float
    minimum_self_fed_depth: int
    minimum_outer_atom_recall: float


PROTOCOL = CdYbConfirmatoryProtocol(
    version="cdyb-partial-macro-confirmation-v1",
    train_centers=(
        (-16.0, -8.0, 8.0),
        (14.0, -12.0, -8.0),
        (15.0, -15.0, 20.0),
        (-15.0, 20.0, -15.0),
        (-15.0, -15.0, -20.0),
    ),
    previously_opened_evaluation_center=(35.0, 30.0, 20.0),
    confirmatory_center=(35.0, 35.0, -35.0),
    train_seed_radius=7.0,
    train_target_radius=14.0,
    confirmatory_seed_radius=14.0,
    confirmatory_target_radius=25.0,
    oracle_max_index=6,
    oracle_cube_side_angstrom=120.0,
    shuffle_trials=31,
    minimum_action_precision=0.80,
    minimum_site_precision=0.95,
    minimum_recoverable_action_recall=0.50,
    maximum_empirical_p=0.05,
    minimum_work_reduction=2.0,
    minimum_self_fed_depth=3,
    minimum_outer_atom_recall=0.20,
)


def protocol_digest(protocol: CdYbConfirmatoryProtocol = PROTOCOL) -> str:
    payload = json.dumps(asdict(protocol), sort_keys=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def audit_protocol(protocol: CdYbConfirmatoryProtocol = PROTOCOL) -> dict:
    train_separation = min(math.dist(protocol.confirmatory_center, center)
                           for center in protocol.train_centers)
    prior_separation = math.dist(
        protocol.confirmatory_center,
        protocol.previously_opened_evaluation_center)
    half_side = protocol.oracle_cube_side_angstrom / 2.0
    unclipped = all(abs(value) + protocol.confirmatory_target_radius
                    <= half_side + 1e-12
                    for value in protocol.confirmatory_center)
    train_disjoint = train_separation > (
        protocol.train_target_radius + protocol.confirmatory_target_radius)
    prior_disjoint = prior_separation > 2.0 * protocol.confirmatory_target_radius
    return {
        "protocol_digest": protocol_digest(protocol),
        "minimum_train_center_separation": train_separation,
        "prior_evaluation_center_separation": prior_separation,
        "train_target_domains_disjoint": train_disjoint,
        "prior_target_domains_disjoint": prior_disjoint,
        "confirmatory_crop_unclipped": unclipped,
        "target_or_oracle_imported": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit_protocol(), indent=2, sort_keys=True))
