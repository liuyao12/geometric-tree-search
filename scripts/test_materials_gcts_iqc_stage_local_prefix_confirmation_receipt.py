#!/usr/bin/env python3
"""Immutable regression for the consumed stage-local IQC confirmation."""

import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_obligation_expanded_dataset import _digest


FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_stage_local_prefix_confirmation_v1.json.gz"
EXPECTED_SHA256 = \
    "6ed5ba97a4821f12150ae3c63b478d7a06bf3eb413551d7c00d4b14ff3a73e05"
EXPECTED_RESULT_DIGEST = \
    "b88228237b399a6c7ced68109fdb898b3c04bb453281d6d0dd0039dba9470f9e"


def test_stage_local_confirmation_is_preserved_honestly_red():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    assert body.pop("result_digest") == EXPECTED_RESULT_DIGEST
    assert _digest(body) == EXPECTED_RESULT_DIGEST
    assert row["protocol_digest"] == \
        "1c8d6cc734514a79fb78f09cb788dc5dc3a68eeb265ca0a354fa7bd82557aec8"
    assert row["model_digest"] == \
        "28db73d00f9a38a134ef5b31322763fa7872376df2b23e44281d0a1207242a56"
    assert row["seed_atoms"] == 476
    assert row["target_atoms"] == 2019
    assert row["target_open_count"] == 1
    assert row["target_opened_after_both_traces_froze"]
    assert not row["target_used_for_candidate_ranking_or_execution"]
    assert not row["candidate_geometry_changed_after_target"]
    assert row["marked_score"]["correct_sites"] == 2
    assert row["marked_score"]["wrong_sites"] == 7
    assert row["marked_score"]["exact_waves"] == 0
    assert row["baseline_score"]["correct_sites"] == 4
    assert row["baseline_score"]["wrong_sites"] == 5
    assert row["baseline_score"]["exact_waves"] == 0
    assert not row["fresh_confirmation_passed"]
    assert not row["exact_self_fed_continuation"]
    assert not row["autonomous_finite_continuation_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_stage_local_confirmation_is_preserved_honestly_red()
    print("red stage-local IQC confirmation receipt preserved")
