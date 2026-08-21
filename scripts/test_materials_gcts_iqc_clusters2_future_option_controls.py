#!/usr/bin/env python3

from materials_gcts_iqc_clusters2_future_option_controls import evaluate


def test_consumed_future_option_controls_are_honest():
    row = evaluate()
    assert row.parents == 8
    assert row.channels == 4
    assert row.learned_selected_parents == (7, 1, 8, 5)
    assert row.learned_exact_path_rank == 3
    assert row.learned_retains_exact_path
    assert row.every_channel_marginal_preserved
    assert not row.target_used_for_shuffle_or_selection
    assert row.consumed_target_used_only_for_scoring
    assert not row.fresh_confirmation_claimed
    assert not row.causal_superiority_gate_passed


if __name__ == "__main__":
    test_consumed_future_option_controls_are_honest()
    print("consumed clusters-squared option controls: passed")
