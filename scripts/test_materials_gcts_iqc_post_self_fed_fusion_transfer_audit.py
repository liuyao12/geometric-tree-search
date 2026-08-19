#!/usr/bin/env python3

from materials_gcts_iqc_post_self_fed_fusion_transfer_audit import (
    load_default_result)


def test_reused_target_transfer_result_is_honest_and_frozen():
    row = load_default_result()
    assert not row["development_gate_passed"]
    assert row["development_beam_supplied_groups"] == 9
    assert row["candidate_count"] == 128
    assert row["exact_candidate_count"] == 62
    assert not row["selected_exact"]
    assert row["selected_correct_sites"] == 2
    assert row["first_exact_rank"] == 10
    assert row["beam_width"] == 16
    assert row["beam_supplies_exact"]
    assert row["exact_candidates_in_beam"] == 6
    assert row["candidate_geometry_unchanged"]
    assert row["candidates_frozen_before_target"]
    assert row["target_bound_plus_one_stable"]
    assert not row["target_used_for_fit_features_or_ranking"]
    assert row["consumed_target_reused"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["fresh_confirmation_authorized"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_reused_target_transfer_result_is_honest_and_frozen()
    print("post-self-fed fusion transfer-audit tests passed")
