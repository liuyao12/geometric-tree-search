#!/usr/bin/env python3

from materials_gcts_iqc_third_block_terminal_value import load_default_result


def test_group_heldout_third_block_terminal_value():
    row = load_default_result()
    assert row["terminal_examples"] == 5091
    assert row["exact_terminal_examples"] == 90
    assert row["supplied_groups"] == 6
    assert row["retained_exact_groups"] == 2
    assert row["retained_exact_paths"] == 4
    assert row["incumbent_retained_groups"] == 3
    assert row["retention_p_value"] == .4375
    assert row["rank_p_value"] == .21875
    assert not row["causal_superiority_gate_passed"]
    assert len(row["folds"]) == 6
    assert row["beam_per_parent"] == 4
    assert row["candidate_geometry_unchanged"]
    assert row["same_four_per_parent_budget"]
    assert row["proper_se3_invariant_features"]
    assert not row["target_used_for_candidate_generation"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_commit_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_group_heldout_third_block_terminal_value()
    print("IQC third-block terminal future value: passed")
