#!/usr/bin/env python3
"""Regression for closure-conditioned second-frontier supply."""

from materials_gcts_iqc_commuting_child_supply_benchmark import \
    load_default_result


def test_child_marking_exposes_consumed_transfer_failure() -> None:
    row = load_default_result()
    assert row["selected_first_parents"] == 8
    assert row["second_candidates"] == 1220
    assert row["selected_child_width_per_parent"] == 16
    assert row["selected_six_action_prefixes"] == 128
    assert row["exact_six_action_prefixes"] == 2
    assert row["exact_six_action_pairs"] == [[4, 3], [5, 3]]
    assert row["selected_exact_six_action_prefixes"] == 0
    assert row["selected_exact_six_action_pairs"] == []
    assert row["exact_six_action_child_ranks"] == \
        [[4, 3, 132], [5, 3, 133]]
    assert not row["target_used_for_generation_fit_or_ranking"]
    assert row["conditional_child_model_diagnostic_only"]


if __name__ == "__main__":
    test_child_marking_exposes_consumed_transfer_failure()
    print("IQC commuting child-supply benchmark tests passed")
