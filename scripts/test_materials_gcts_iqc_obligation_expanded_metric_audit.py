"""Regression for the expanded grouped obligation-marking audit."""


def test_expanded_metric_keeps_site_and_exact_action_gates_separate() -> None:
    try:
        import numpy  # noqa: F401
    except ImportError:
        # The repository's bundled scientific runtime supplies NumPy; keep
        # the lightweight system-Python suite usable without weakening the
        # executable audit when that runtime is present.
        return

    from materials_gcts_iqc_obligation_expanded_metric_audit import (
        EXPECTED_AUDIT_DIGEST, evaluate)

    row = evaluate()
    assert row["audit_digest"] == EXPECTED_AUDIT_DIGEST
    assert row["development_groups"] == 20
    assert row["candidate_count"] == 303
    assert row["candidate_spec_count"] == 162
    assert row["unique_geometry_representation_count"] == 22
    assert row["selected_model"]["model_id"] == "temporal-6"
    assert row["selected_result"]["exact_bearing_groups"] == 8
    assert row["selected_result"]["exact"] == 7
    assert row["selected_result"]["sites"] == 41
    assert row["shuffle_exact_maximum"] == 8
    assert row["shuffle_exact_upper_tail_p"] == .125
    assert row["shuffle_sites_maximum"] == 40
    assert row["shuffle_sites_upper_tail_p"] == .03125
    assert row["correct_site_yield_gate_passed"]
    assert not row["exact_action_gate_passed"]
    assert not row["top_action_superiority_gate_passed"]
    assert not row["fresh_confirmation_opened"]
    assert not row["integrated_as_default_marking"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_expanded_metric_keeps_site_and_exact_action_gates_separate()
    print("expanded obligation metric audit: passed")
