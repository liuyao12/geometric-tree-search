"""Fast pre-execution contract for the second one-shot harness."""

import inspect

import materials_gcts_iqc_parent_balanced_confirmation_v2 as confirmation


def test_second_harness_freezes_receipt_before_tolerant_scoring():
    source = inspect.getsource(confirmation._execute_and_score_once)
    assert source.index("guard.receipt_frozen") < \
        source.index("guard.target_opened") < \
        source.index("colored_position_index")
    assert "target_sites\": target_sites" in source
    assert "rerun_or_fallback_allowed\": False" in source
    assert confirmation.EXPECTED_FIXTURE_SHA256
    assert confirmation.EXPECTED_RESULT_DIGEST


def test_second_confirmation_is_valid_and_honestly_red():
    row = confirmation.load_default_result()
    assert row["complete_nine_action_lineages"] == 1114
    assert row["nine_action_candidates_retained"] == 64
    assert row["fourth_candidates_retained"] == 512
    assert row["exact_terminal_blocks"] == 8
    assert row["exact_four_block_candidates"] == 0
    assert row["best_correct_actions"] == 11
    assert not row["fresh_parent_balanced_fourth_block_supply_confirmed"]
    assert row["execution_seconds"] > 1200
    assert row["receipt_unchanged_after_target"]
    assert row["target_order_audit"]["target_open_count"] == 1
    assert not row["target_used_for_candidate_or_ranking"]
    assert not row["rerun_or_fallback_allowed"]


if __name__ == "__main__":
    test_second_harness_freezes_receipt_before_tolerant_scoring()
    test_second_confirmation_is_valid_and_honestly_red()
    print("second parent-balanced confirmation contract: passed")
