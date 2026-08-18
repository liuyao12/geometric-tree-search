#!/usr/bin/env python3
"""Immutable status of the consumed, unscored first autonomous attempt."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AutonomousAttemptStatus:
    confirmation_center: tuple[float, float, float]
    preregistration_digest: str
    seed_materialized: bool
    candidates_and_trace_computed: bool
    target_factory_called: bool
    target_bound_plus_one_stable: bool
    target_score_computed: bool
    trace_digest_recovered: bool
    same_nucleus_retry_permitted: bool
    outcome: str
    status_digest: str


def audit() -> AutonomousAttemptStatus:
    payload = {
        "confirmation_center": (-70., -70., 30.),
        "preregistration_digest":
            "a444b728dc48e30dc3a95778e20e3b5cbc6b5cde96bb91056db6e30814e1d6f4",
        "seed_materialized": True,
        "candidates_and_trace_computed": True,
        "target_factory_called": True,
        "target_bound_plus_one_stable": False,
        "target_score_computed": False,
        "trace_digest_recovered": False,
        "same_nucleus_retry_permitted": False,
        "outcome": (
            "consumed/unknown: bound-24 and bound-25 target crops differed; "
            "execution failed closed before scoring and the nucleus will not "
            "be reopened"),
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return AutonomousAttemptStatus(*payload.values(), digest)


def main():
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
