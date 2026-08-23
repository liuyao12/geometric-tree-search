"""Fast contract for the one-shot fresh parent-balanced confirmation."""

import inspect

import materials_gcts_iqc_parent_balanced_confirmation as confirmation


def test_confirmation_orders_receipt_before_target_and_has_no_retry_path():
    source = inspect.getsource(confirmation._execute_and_score_once)
    assert source.index("guard.receipt_frozen") < \
        source.index("guard.target_opened") < \
        source.index("oracle_crop_fast(\n        CONFIRMATION_CENTER, FOURTH_RADIUS)")
    assert "rerun_or_fallback_allowed\": False" in source
    assert "winner_selected_or_validated\": False" in source
    assert confirmation.EXPECTED_RESULT_DIGEST


def test_scoring_helpers_are_colored_and_deterministic():
    truth = {(1., 2., 3.): "A", (4., 5., 6.): "B"}
    assert confirmation._action_labels(
        (((1., 2., 3.), "A"), ((4., 5., 6.), "B")), truth) == \
        (True, True)
    assert confirmation._action_labels(
        (((1., 2., 3.), "B"),), truth) == (False,)


def test_consumed_attempt_is_preserved_as_honest_red():
    row = confirmation.load_default_result()
    assert row["complete_nine_action_lineages"] == 1183
    assert row["nine_action_candidates_retained"] == 64
    assert row["fourth_candidates_retained"] == 512
    assert row["exact_four_block_candidates"] == 0
    assert row["best_correct_actions"] == 0
    assert not row["fresh_parent_balanced_fourth_block_supply_confirmed"]
    assert row["receipt_serialized_before_target"]
    assert row["receipt_unchanged_after_target"]
    assert row["target_order_audit"]["target_open_count"] == 1
    assert not row["target_used_for_candidate_or_ranking"]
    assert not row["rerun_or_fallback_allowed"]


if __name__ == "__main__":
    test_confirmation_orders_receipt_before_target_and_has_no_retry_path()
    test_scoring_helpers_are_colored_and_deterministic()
    test_consumed_attempt_is_preserved_as_honest_red()
    print("fresh parent-balanced confirmation contract: passed")
