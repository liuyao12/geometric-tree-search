#!/usr/bin/env python3
"""Slow regression for the consumed-nucleus obligation backoff audit."""

from materials_gcts_iqc_port_obligation_backoff_audit import evaluate


def test_backoff_improves_coverage_but_fails_value_transfer() -> None:
    row = evaluate()
    assert row["selected_spec_index"] == 3
    assert row["selected_development_result"]["exact"] == 8
    assert row["selected_development_result"]["sites"] == 27
    assert row["selected_development_result"]["minimum_coverage"] == .75
    assert row["shuffle_upper_tail_p"] == .1875
    assert row["known_exact_original_recognized_fraction"] == .125
    assert row["known_exact_backoff_recognized_fraction"] == .75
    assert row["known_exact_old_rank"] == 5
    assert row["known_exact_new_rank"] == 8
    assert not row["known_exact_outranks_all_four_published_false_actions"]
    assert not row["confirmation_target_reconstructed_or_reopened"]
    assert not row["candidate_geometry_changed"]
    assert not row["backoff_transfer_diagnostic_passed"]
    assert not row["integrated_as_default_marking"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_backoff_improves_coverage_but_fails_value_transfer()
    print("IQC obligation backoff audit: honest red")
