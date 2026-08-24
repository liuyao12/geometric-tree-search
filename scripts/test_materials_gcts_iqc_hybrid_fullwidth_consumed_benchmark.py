#!/usr/bin/env python3
"""Pinned full-width evidence for the bounded hybrid IQC executor."""

from materials_gcts_iqc_hybrid_fullwidth_consumed_benchmark import \
    load_default_result


def test_bounded_hybrid_retains_exact_fallback_and_complete_paths():
    row = load_default_result()
    assert row["selected_prefixes"] == 12
    assert row["raw_exact_nine_action_lineages"] == 6
    assert row["raw_joint_exact_lineages"] == 3
    assert row["raw_fallback_exact_lineages"] == 3
    assert row["selected_exact_nine_action_lineages"] == 6
    assert row["exact_terminal_fourth_blocks"] == 475
    assert row["exact_complete_twelve_action_paths"] == 42
    assert row["best_complete_correct_actions"] == 12
    assert row["runtime_gate_passed"]
    assert row["receipt_unchanged_after_target"]
    assert not row["candidate_selection_target_used"]
    assert not row["fresh_confirmation_claimed"]


if __name__ == "__main__":
    test_bounded_hybrid_retains_exact_fallback_and_complete_paths()
    print("IQC bounded hybrid full-width tests passed")
