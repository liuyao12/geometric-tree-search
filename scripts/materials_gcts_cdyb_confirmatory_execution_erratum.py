#!/usr/bin/env python3
"""Immutable record of the pre-data abort before Cd--Yb confirmation v2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConfirmatoryExecutionErratum:
    protocol_v2_digest: str
    preregistration_commit: str
    aborted_invocations: int
    abort_stage: str
    exception_type: str
    exception_summary: str
    confirmatory_seed_accessed: bool
    confirmatory_candidates_constructed: bool
    controls_or_execution_constructed: bool
    target_factory_calls: int
    target_scored: bool
    sole_permitted_correction: str
    scientific_trial_consumed: bool


ERRATUM = ConfirmatoryExecutionErratum(
    protocol_v2_digest=
    "3d4dfca24c7526baff14a2258c715e4caf0631af1c28af8ab41860b8e593c3f6",
    preregistration_commit="d2abc96dc9b352ece04a2a85d393fa8b621c5b0e",
    aborted_invocations=1,
    abort_stage="after train/model verification; before confirmatory seed",
    exception_type="AttributeError",
    exception_summary=(
        "harness read oracle/geometry fields from protocol v2 although v2 "
        "intentionally references the frozen v1 geometry manifest"),
    confirmatory_seed_accessed=False,
    confirmatory_candidates_constructed=False,
    controls_or_execution_constructed=False,
    target_factory_calls=0,
    target_scored=False,
    sole_permitted_correction=(
        "read oracle size, train centers, confirmatory center, and seed/target "
        "radii from the digest-verified v1 geometry protocol"),
    scientific_trial_consumed=False,
)


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode()).hexdigest()


ERRATUM_DIGEST = _digest(asdict(ERRATUM))


def audit_erratum() -> dict:
    return {
        "erratum_digest": ERRATUM_DIGEST,
        "pretarget_abort_only": (
            ERRATUM.aborted_invocations == 1 and
            not ERRATUM.confirmatory_seed_accessed and
            not ERRATUM.confirmatory_candidates_constructed and
            not ERRATUM.controls_or_execution_constructed and
            ERRATUM.target_factory_calls == 0 and
            not ERRATUM.target_scored and
            not ERRATUM.scientific_trial_consumed),
    }


if __name__ == "__main__":
    print(json.dumps(audit_erratum(), indent=2, sort_keys=True))
