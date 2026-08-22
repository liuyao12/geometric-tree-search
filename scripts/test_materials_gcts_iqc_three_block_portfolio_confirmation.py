#!/usr/bin/env python3
"""Fast static contract for the unconsumed one-shot confirmation harness."""

from pathlib import Path

from materials_gcts_iqc_three_block_portfolio_confirmation import (
    ATTEMPT_MARKER, DEFAULT_FIXTURE, _attempt_marker_bytes)
from materials_gcts_iqc_three_block_portfolio_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST)


def test_harness_freezes_receipt_before_the_only_target_open() -> None:
    source = Path(__file__).with_name(
        "materials_gcts_iqc_three_block_portfolio_confirmation.py").read_text()
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
        execute.index("truth = {")
    assert execute.index("truth = {") < execute.index("guard.scored(")
    assert "freeze_three_block_portfolio_execution(" in execute
    assert "target=" not in execute
    assert "scorer=" not in execute
    assert _attempt_marker_bytes().decode().count(
        EXPECTED_MANIFEST_DIGEST) == 1


def test_fresh_fixture_is_not_opened_by_fast_contract() -> None:
    # This test intentionally does not call the oracle or confirmation.  Before
    # the one-shot run both paths are absent; afterward both exist and this
    # assertion remains a pure state/accounting check.
    assert ATTEMPT_MARKER.exists() == DEFAULT_FIXTURE.exists()


if __name__ == "__main__":
    test_harness_freezes_receipt_before_the_only_target_open()
    test_fresh_fixture_is_not_opened_by_fast_contract()
    print("fresh three-block portfolio harness: passed")
