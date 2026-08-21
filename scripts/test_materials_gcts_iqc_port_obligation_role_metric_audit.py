#!/usr/bin/env python3
"""Regression for the grouped IQC role-conditioned obligation audit."""

from materials_gcts_iqc_port_obligation_role_metric_audit import evaluate


def test_role_metric_is_an_honest_noncausal_negative() -> None:
    row = evaluate()
    assert row["selected_spec_index"] == 5
    assert row["selected_spec"] == {
        "horizon": 4,
        "separation_channels": False,
        "pair_channels": False,
        "neighbors": 7,
        "weighted": True,
    }
    assert row["selected_development_result"]["exact"] == 8
    assert row["selected_development_result"]["sites"] == 27
    assert row["shuffle_exact_median"] == 7
    assert row["shuffle_exact_maximum"] == 9
    assert row["shuffle_upper_tail_p"] == .5
    assert row["shuffle_auc_upper_tail_p"] == .03125
    assert row["shuffle_logloss_lower_tail_p"] == .03125
    assert row["known_exact_old_rank"] == 5
    assert row["known_exact_role_metric_rank"] == 13
    assert row["known_false_role_metric_ranks"] == (3, 6, 7, 8)
    assert not row[
        "known_exact_outranks_all_four_published_false_actions"]
    assert not row["confirmation_target_reconstructed_or_reopened"]
    assert not row["external_labels_used_for_fit_spec_or_rank"]
    assert not row["candidate_geometry_changed"]
    assert not row["role_metric_diagnostic_passed"]
    assert not row["integrated_as_default_marking"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_role_metric_is_an_honest_noncausal_negative()
    print("IQC role-conditioned obligation metric: honest red")
