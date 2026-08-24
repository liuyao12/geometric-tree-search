#!/usr/bin/env python3
"""Regression for the closure-conditioned parent→child incidence ablation."""

from materials_gcts_iqc_commuting_child_incidence_fit import \
    load_default_ablation


def test_frozen_incidence_ablation_is_honestly_outside_top_16() -> None:
    result = load_default_ablation()
    order2 = result["orders"]["2"]
    order3 = result["orders"]["3"]

    assert order2["development_exact_branches_supplied"] == 12
    assert order3["development_exact_branches_supplied"] == 9
    assert sorted(row[2] for row in order2["consumed_exact_ranks"]) == [69, 71]
    assert sorted(row[2] for row in order3["consumed_exact_ranks"]) == [78, 80]
    assert not result["top_k_gate_passed"]
    assert not order2["candidate_generation_target_used"]
    assert not order3["candidate_generation_target_used"]
    assert order2["consumed_labels_opened_after_scores"]
    assert order3["consumed_labels_opened_after_scores"]


if __name__ == "__main__":
    test_frozen_incidence_ablation_is_honestly_outside_top_16()
    print("commuting child incidence ablation: passed")
