#!/usr/bin/env python3
"""Fast static contract for the unconsumed complete-parent one-shot."""

from pathlib import Path

from materials_gcts_iqc_complete_parent_confirmation import (
    ATTEMPT_MARKER, DEFAULT_FIXTURE, _attempt_marker_bytes)
from materials_gcts_iqc_complete_parent_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST)


def test_target_opens_only_after_complete_receipt_freeze() -> None:
    source = Path(__file__).with_name(
        "materials_gcts_iqc_complete_parent_confirmation.py").read_text()
    execute = source.split("def _execute_and_score_once():", 1)[1].split(
        "def validate_result", 1)[0]
    assert execute.count("oracle_crop_fast(") == 2
    assert execute.index("guard.seed_opened()") < execute.index(
        "seed, seed_lifts = oracle_crop_fast(")
    assert execute.index("guard.receipt_frozen(receipt_digest)") < \
        execute.index("guard.target_opened()")
    assert execute.index("guard.target_opened()") < execute.index(
        "target, target_lifts = oracle_crop_fast(")
    assert execute.index("target, target_lifts = oracle_crop_fast(") < \
        execute.index("by_species = {")
    assert execute.index("by_species = {") < execute.index("guard.scored(")
    assert "freeze_three_block_complete_parent_execution(" in execute
    assert "target=" not in execute
    assert "scorer=" not in execute
    assert _attempt_marker_bytes().decode().count(
        EXPECTED_MANIFEST_DIGEST) == 1


def test_attempt_and_result_are_both_unopened_or_both_consumed() -> None:
    assert ATTEMPT_MARKER.exists() == DEFAULT_FIXTURE.exists()


if __name__ == "__main__":
    test_target_opens_only_after_complete_receipt_freeze()
    test_attempt_and_result_are_both_unopened_or_both_consumed()
    print("fresh complete-parent confirmation harness: passed")
