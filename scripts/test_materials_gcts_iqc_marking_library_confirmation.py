#!/usr/bin/env python3
"""Regression for the one-shot five-channel IQC result."""

from pathlib import Path

from materials_gcts_iqc_marking_library_confirmation import (
    load_default_result)
from materials_gcts_iqc_marking_library_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST)


def test_confirmation_runner_enforces_target_order() -> None:
    source = Path(__file__).with_name(
        "materials_gcts_iqc_marking_library_confirmation.py").read_text()
    execute = source.split("def _execute_and_score_once():", 1)[1].split(
        "def validate_result", 1)[0]
    assert execute.index("guard.protocol_verified()") < \
        execute.index("guard.seed_opened()") < \
        execute.index("freeze_three_block_marking_library_execution(") < \
        execute.index("guard.receipt_frozen(") < \
        execute.index("guard.target_opened()") < \
        execute.index("target, target_ids = oracle_crop_fast(") < \
        execute.index("guard.scored(")


def test_fresh_result_is_honestly_classified() -> None:
    row = load_default_result()
    assert row["protocol_digest"] == EXPECTED_MANIFEST_DIGEST
    assert row["receipt_serialized_before_target"]
    assert row["receipt_unchanged_after_target"]
    assert not row["target_used_for_candidate_or_ranking"]
    assert len(row["receipt"]["selected_parent_ids"]) == 8
    assert row["target_order_audit"]["target_open_count"] == 1
    assert not row["winner_selected_or_validated"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]
    assert not row["rerun_or_fallback_allowed"]


if __name__ == "__main__":
    test_confirmation_runner_enforces_target_order()
    test_fresh_result_is_honestly_classified()
    print("fresh five-channel IQC result: passed")
