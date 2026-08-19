#!/usr/bin/env python3
"""Fast immutable audit of the consumed self-fed IQC confirmation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_self_fed_frontier_candidates import (
    EXPECTED_RECEIPT_DIGEST)
from materials_gcts_iqc_self_fed_frontier_preregistration import (
    EXPECTED_MANIFEST_DIGEST)


FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_self_fed_frontier_confirmation_result_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "1624c0a3543db2cf14e6aa3ce3e3b8c29bfb442f4e32976be7db898e730dbc2b"


def audit():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("self-fed confirmation result byte drift")
    row = json.loads(raw)
    if (row["protocol_digest"] != EXPECTED_MANIFEST_DIGEST
            or row["candidate_receipt_digest"] != EXPECTED_RECEIPT_DIGEST
            or row["target_open_count"] != 1
            or row["target_used_for_fit_candidate_or_ranking"]
            or not row["candidate_digest_unchanged"]
            or not row["candidates_frozen_before_outer_target"]
            or not row["target_bound_plus_one_stable"]
            or not row["inherited_branch_pre_target_selected"]
            or not row["inherited_branch_posthoc_exact"]
            or not row["self_fed_configuration_used_as_seed"]
            or row["terminal_count"] != 128
            or row["exact_terminal_count"] != 62
            or not row["complete_tree_supplies_exact"]
            or row["dual_portfolio_supplies_exact"]
            or row["fusion_first_exact_rank"] != 16
            or row["fusion_top_one_correct_sites"] != 2
            or row["fusion_top_one_exact"]
            or row["six_action_autonomous_gate_passed"]
            or row["stationary_or_exponential_claimed"]):
        raise AssertionError("self-fed confirmation scientific result drift")
    return row


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
