#!/usr/bin/env python3
"""Regression for the temporal IQC port-obligation metric audit."""

from materials_gcts_iqc_port_obligation_temporal_metric_audit import evaluate


def test_temporal_metric_discriminates_but_fails_action_selection() -> None:
    row = evaluate()
    assert row["selected_spec_index"] == 15
    assert row["selected_spec"] == {
        "horizon": 8,
        "time_bins": 2,
        "separation_channels": True,
        "neighbors": 9,
        "weighted": True,
    }
    assert row["selected_development_result"]["exact"] == 8
    assert row["selected_development_result"]["sites"] == 27
    assert row["shuffle_exact_median"] == 7
    assert row["shuffle_exact_maximum"] == 8
    assert row["shuffle_upper_tail_p"] == .5
    assert row["shuffle_auc_upper_tail_p"] == .03125
    assert row["shuffle_logloss_lower_tail_p"] == .03125
    assert row["known_exact_old_rank"] == 5
    assert row["known_exact_temporal_metric_rank"] == 8
    assert row["known_false_temporal_metric_ranks"] == (1, 3, 12, 13)
    assert not row[
        "known_exact_outranks_all_four_published_false_actions"]
    assert not row["confirmation_target_reconstructed_or_reopened"]
    assert not row["external_labels_used_for_fit_spec_or_rank"]
    assert not row["candidate_geometry_changed"]
    assert not row["temporal_metric_diagnostic_passed"]
    assert not row["integrated_as_default_marking"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_temporal_metric_discriminates_but_fails_action_selection()
    print("IQC temporal obligation metric: discriminative but selection-red")
