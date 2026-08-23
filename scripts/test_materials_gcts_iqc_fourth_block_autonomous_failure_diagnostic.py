"""Regression for the post-hoc group-4 shortlist failure diagnosis."""

from materials_gcts_iqc_fourth_block_autonomous_failure_diagnostic import \
    load_default_result


def test_failure_is_parent_diversity_pruning_not_missing_supply():
    row = load_default_result()
    assert row["full_candidates"] == 8_649
    assert row["exact_candidates"] == 96
    assert row["exact_parent_count"] == 2
    assert row["first_exact_global_rank"] == 116
    assert row["failed_global_shortlist_size"] == 32
    assert row["failed_global_shortlist_exact"] == 0
    assert tuple(parent["first_exact_within_parent_rank"]
                 for parent in row["exact_parent_audit"]) == (2, 2)
    assert row["parent_balanced_width"] == 2
    assert row["parent_balanced_candidates"] == 128
    assert row["parent_balanced_exact_candidates"] == 2
    assert row["parent_balanced_exact_parent_count"] == 2
    assert row["failure_kind"] == \
        "global pruning destroyed parent diversity"
    assert row["target_consumed_only_for_posthoc_diagnosis"]
    assert not row["confirmation_retried"]
    assert not row["fresh_parent_balanced_confirmation_claimed"]
    assert not row["autonomous_growth_claimed"]


if __name__ == "__main__":
    test_failure_is_parent_diversity_pruning_not_missing_supply()
    print("fourth-block autonomous failure diagnostic: passed")
