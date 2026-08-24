#!/usr/bin/env python3
"""Pinned stage-boundary regression for commuting hybrid IQC supply."""

from materials_gcts_iqc_commuting_hybrid_consumed_benchmark import \
    load_default_result as load_hybrid
from materials_gcts_iqc_commuting_second_supply_benchmark import \
    load_default_result as load_second


def test_first_closure_passes_and_old_child_marking_drops_supply() -> None:
    hybrid = load_hybrid()
    second = load_second()
    assert hybrid["exact_selected_first_parents"] == 2
    assert hybrid["raw_prefix_exact_counts_at_3_6_9"] == [283, 0, 0]
    assert hybrid["complete_prefix_exact_counts_at_3_6_9_12"] == \
        [128, 0, 0, 0]
    assert hybrid["complete_best_correct_actions_by_block"] == [3, 2, 3, 3]
    assert hybrid["exact_complete_twelve_action_paths"] == 0
    assert second["exact_six_action_prefixes"] == 2
    assert second["exact_six_action_pairs"] == [[4, 3], [5, 3]]
    assert second["exact_six_action_joint_and_base_ranks"] == \
        [[4, 3, 126, 90], [5, 3, 127, 90]]
    assert second["selected_exact_six_action_prefixes"] == 0
    assert not second["target_used_for_generation_fit_or_ranking"]
    assert second["consumed_diagnostic_only"]


if __name__ == "__main__":
    test_first_closure_passes_and_old_child_marking_drops_supply()
    print("IQC commuting hybrid consumed benchmark tests passed")
