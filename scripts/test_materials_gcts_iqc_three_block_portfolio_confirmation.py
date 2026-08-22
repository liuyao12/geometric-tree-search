#!/usr/bin/env python3
"""Fast static contract for the unconsumed one-shot confirmation harness."""

from pathlib import Path

from materials_gcts_iqc_three_block_portfolio_confirmation import (
    ATTEMPT_MARKER, DEFAULT_FIXTURE, _attempt_marker_bytes,
    load_default_result)
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


def test_attempt_and_fixture_accounting_match() -> None:
    # This test intentionally does not call the oracle or confirmation.  Before
    # the one-shot run both paths are absent; afterward both exist and this
    # assertion remains a pure state/accounting check.
    assert ATTEMPT_MARKER.exists() == DEFAULT_FIXTURE.exists()


def test_one_shot_result_is_frozen_and_honestly_red() -> None:
    row = load_default_result()
    assert row["seed_atoms"] == 490
    assert row["target_atoms"] == 22848
    assert row["candidate_lineages"] == 11355
    assert row["unique_first_prefixes"] == 4
    assert row["exact_first_prefixes"] == 0
    assert row["unique_second_prefixes"] == 83
    assert row["exact_second_prefixes"] == 0
    assert row["best_correct_actions"] == 0
    assert row["exact_lineages"] == 0
    assert not row["fresh_bounded_three_block_candidate_supply_confirmed"]
    assert row["receipt"]["first_candidate_counts"] == [8, 36, 121]
    assert row["receipt"]["selected_parent_ids"] == [3, 7, 4, 1]
    assert row["receipt_digest"] == \
        "fe08675119e1e1489d93dc2e3f1bd6cbc1f9c40e9ae606ee53197675a1852e40"
    assert row["target_order_audit"] == {
        "receipt_digest": row["receipt_digest"], "score_count": 1,
        "seed_open_count": 1, "state": "scored", "target_open_count": 1}
    assert not row["target_used_for_candidate_or_ranking"]
    assert not row["winner_selected_or_validated"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_harness_freezes_receipt_before_the_only_target_open()
    test_attempt_and_fixture_accounting_match()
    test_one_shot_result_is_frozen_and_honestly_red()
    print("fresh three-block portfolio harness: passed")
