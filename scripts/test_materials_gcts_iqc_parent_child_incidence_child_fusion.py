#!/usr/bin/env python3
"""Regression for the consumed incidence/child fusion plateau."""

from materials_gcts_iqc_parent_child_incidence_child_fusion import (
    load_default_result)


def test_parent_child_incidence_child_fusion():
    row = load_default_result()
    assert row["development_groups"] == 10
    assert row["examples"] == 1278
    assert row["best_selected_exact_groups"] == 8
    assert row["best_selected_correct_sites"] == 26
    assert row["all_weights_same_accuracy_plateau"] is True
    assert row["candidate_sets_identical"] is True
    assert row["exploratory_consumed_weight_sweep"] is True
    assert row["target_used_for_fit_or_ranking"] is False
    assert row["autonomous_commit_claimed"] is False


if __name__ == "__main__":
    test_parent_child_incidence_child_fusion()
    print("IQC parent-child incidence/child fusion tests passed")
