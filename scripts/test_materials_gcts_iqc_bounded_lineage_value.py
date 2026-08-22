"""Regression for the grouped bounded IQC lineage winner audit."""

from materials_gcts_iqc_bounded_lineage_value import load_default_result


def test_bounded_lineage_value_is_grouped_and_target_blind():
    row = load_default_result()
    assert row["groups"] == 5
    assert row["examples"] > 0
    assert row["positive_examples"] > 0
    assert len(row["outer_folds"]) == 5
    assert all(case["exact_lineages"] > 0 for case in row["cases"])
    # A selector that wins 0/5 groups is already causally red; running label
    # nulls cannot rescue it and would only spend computation.
    assert row["outer_selected_exact_groups"] == 0
    assert row["outer_first_exact_rank_sum"] == 528
    assert len(row["shuffle_controls"]) == 0
    assert not row["candidate_target_used"]
    assert row["targets_opened_after_candidate_freeze"]
    assert not row["raw_ids_or_absolute_coordinates_in_features"]
    assert not row["lattice_module_family_or_target_fields_in_features"]
    assert row["development_targets_consumed"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]
    assert row["grouped_winner_gate_passed"] == (
        row["outer_selected_exact_groups"] >= 4 and
        row["shuffle_p_value"] <= .05)


if __name__ == "__main__":
    test_bounded_lineage_value_is_grouped_and_target_blind()
    print("grouped bounded lineage value: passed")
