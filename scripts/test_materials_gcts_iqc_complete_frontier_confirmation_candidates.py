#!/usr/bin/env python3

import base64
import hashlib
import json
import zlib
from pathlib import Path

from materials_gcts_iqc_complete_frontier_confirmation_candidates import (
    DEFAULT_FIXTURE, EXPECTED_FIXTURE_SHA256, EXPECTED_RECEIPT_DIGEST,
    _digest, validate_candidate_receipt)
from materials_gcts_iqc_complete_frontier_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST)


def _fixture():
    terminals = (((1., 0., 0.), "X"), ((2., 0., 0.), "Y"))
    terminal_bytes = json.dumps(terminals, separators=(",", ":")).encode()
    body = {
        "schema_version": 1,
        "source_commit": "test",
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "center": CONFIRMATION_CENTER,
        "seed_radius": 9.,
        "oracle_lift_bound": 60,
        "seed_atoms": 20,
        "seed_bound_plus_one_stable": True,
        "action_reach_schedule": (8, 8, 8),
        "unpruned_from_depth": 0,
        "candidate_counts_by_depth": (8, 30, 12),
        "terminal_count": 2,
        "terminal_actions_zlib_base64": base64.b64encode(
            zlib.compress(terminal_bytes, 9)).decode(),
        "terminal_actions_sha256": hashlib.sha256(terminal_bytes).hexdigest(),
        "scalar_order": (0, 1),
        "fusion_order": (1, 0),
        "per_channel_portfolio_budget": 9,
        "portfolio_indices": (0, 1),
        "candidate_digest": "a" * 64,
        "portfolio_digest": "b" * 64,
        "execution_digest": "c" * 64,
        "target_open_count": 0,
        "target_used": False,
    }
    return {**body, "receipt_digest": _digest(body)}


def test_candidate_receipt_validates_and_mutation_fails():
    fixture = _fixture()
    assert validate_candidate_receipt(fixture) is fixture
    changed = dict(fixture)
    changed["target_open_count"] = 1
    try:
        validate_candidate_receipt(changed)
    except AssertionError:
        pass
    else:
        raise AssertionError("mutated confirmation receipt did not fail")


def test_real_candidate_receipt_is_frozen_before_target():
    raw = Path(DEFAULT_FIXTURE).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256
    receipt = validate_candidate_receipt(json.loads(raw))
    assert receipt["receipt_digest"] == EXPECTED_RECEIPT_DIGEST
    assert receipt["seed_atoms"] == 473
    assert receipt["candidate_counts_by_depth"] == [8, 37, 128]
    assert receipt["terminal_count"] == 128
    assert len(receipt["portfolio_indices"]) == 18
    assert receipt["target_open_count"] == 0
    assert not receipt["target_used"]


if __name__ == "__main__":
    test_candidate_receipt_validates_and_mutation_fails()
    test_real_candidate_receipt_is_frozen_before_target()
    print("complete-frontier confirmation-candidate tests passed")
