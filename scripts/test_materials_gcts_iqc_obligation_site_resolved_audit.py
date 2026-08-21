"""Regression for site-resolved scoring of immutable IQC terminals."""


def test_site_resolved_marking_beats_grouped_nulls_without_splicing() -> None:
    try:
        import numpy  # noqa: F401
    except ImportError:
        return

    from materials_gcts_iqc_obligation_site_resolved_audit import (
        EXPECTED_AUDIT_DIGEST, evaluate)

    row = evaluate()
    assert row["audit_digest"] == EXPECTED_AUDIT_DIGEST
    assert row["development_groups"] == 20
    assert row["candidate_count"] == 303
    assert row["site_occurrence_count"] == 909
    assert row["selected_spec"] == {
        "neighbors": 7, "weighted": True, "aggregation": "mean"}
    assert row["selected_result"]["exact"] == 8
    assert row["selected_result"]["exact_bearing_groups"] == 8
    assert row["selected_result"]["sites"] == 45
    assert row["frozen_model_digest"] == \
        "891e8badab355abfdeeed5d83a05c62cf34f22962cf193d3ead283a43c6afccc"
    assert row["frozen_model_feature_count"] == 839
    assert row["frozen_model_training_site_count"] == 909
    assert row["shuffle_exact_maximum"] == 7
    assert row["shuffle_sites_maximum"] == 39
    assert row["shuffle_exact_upper_tail_p"] == .03125
    assert row["shuffle_sites_upper_tail_p"] == .03125
    assert row["site_resolved_exact_action_gate_passed"]
    assert not row["candidate_geometry_changed"]
    assert not row["branches_spliced_or_sites_moved"]
    assert row["whole_compatible_terminal_remains_commit_unit"]
    assert not row["targets_used_for_receipts_or_ranking"]
    assert not row["fresh_confirmation_opened"]
    assert not row["integrated_as_default_marking"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_site_resolved_marking_beats_grouped_nulls_without_splicing()
    print("site-resolved obligation marking: passed")
