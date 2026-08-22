#!/usr/bin/env python3
"""Fast static contract for the unconsumed complete-parent one-shot."""

from pathlib import Path

from materials_gcts_iqc_complete_parent_confirmation import (
    ATTEMPT_MARKER, DEFAULT_FIXTURE, _attempt_marker_bytes,
    load_default_result)
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


def test_second_one_shot_is_frozen_and_honestly_red() -> None:
    row = load_default_result()
    assert row["seed_atoms"] == 487
    assert row["target_atoms"] == 22801
    assert row["candidate_lineages"] == 17228
    assert row["unique_candidate_actions"] == 57
    assert row["exact_first_prefixes"] == 2
    assert row["exact_second_prefixes"] == 0
    assert row["best_correct_actions"] == 8
    assert row["exact_lineages"] == 0
    assert not row["fresh_complete_parent_three_block_supply_confirmed"]
    assert set(row["receipt"]["selected_parent_ids"]) == set(range(1, 9))
    assert row["receipt"]["first_candidate_counts"] == [8, 36, 120]
    assert row["receipt_digest"] == \
        "99fd8bac19a0b23d88b4a927f0d4091af975f796caacf6af93842b3055488a07"
    assert row["target_order_audit"]["state"] == "scored"
    assert row["target_order_audit"]["target_open_count"] == 1
    assert not row["target_used_for_candidate_or_ranking"]
    assert not row["winner_selected_or_validated"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_target_opens_only_after_complete_receipt_freeze()
    test_attempt_and_result_are_both_unopened_or_both_consumed()
    test_second_one_shot_is_frozen_and_honestly_red()
    print("fresh complete-parent confirmation harness: passed")
