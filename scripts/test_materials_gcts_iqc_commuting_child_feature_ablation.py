#!/usr/bin/env python3
"""Regression for the consumed child-section fragmentation diagnosis."""

from materials_gcts_iqc_commuting_child_feature_ablation import \
    load_default_result


def test_coarse_sections_do_not_repair_consumed_child_transfer() -> None:
    row = load_default_result()
    assert row["training_rows"] == 3994
    assert row["positive_rows"] == 95
    assert row["consumed_candidates"] == 1220
    reps = row["representations"]
    assert reps["full"]["development_exact_branches_supplied"] == 14
    assert reps["full"]["consumed_exact_ranks"] == \
        [[4, 3, 132], [5, 3, 133]]
    assert reps["legacy-only"]["consumed_exact_ranks"] == \
        [[4, 3, 95], [5, 3, 96]]
    assert all(value["consumed_exact_supplied"] == 0
               for value in reps.values())
    assert not row["candidate_generation_target_used"]
    assert row["diagnostic_designed_after_consumed_failure"]
    assert not row["fresh_confirmation_claimed"]


if __name__ == "__main__":
    test_coarse_sections_do_not_repair_consumed_child_transfer()
    print("IQC commuting child feature-ablation tests passed")
