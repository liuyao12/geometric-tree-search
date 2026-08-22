"""Regression for the finite graph bounded-IQC lineage audit."""

from materials_gcts_iqc_bounded_lineage_graph_value import load_default_result


def test_bounded_lineage_graph_value_is_grouped_and_honestly_red():
    row = load_default_result()
    assert row["groups"] == 5
    assert row["examples"] == 5237
    assert row["positive_examples"] == 149
    assert row["stage_graphs_per_lineage"] == 3
    assert row["full_feature_count"] == 2816
    assert row["outer_selected_exact_groups"] == 0
    assert row["outer_first_exact_rank_sum"] == 95
    assert tuple(fold["first_exact_rank"] for fold in row["outer_folds"]) == \
        (20, 6, 6, 2, 61)
    assert row["shuffle_controls_requested"] == 31
    assert row["shuffle_controls_executed"] == 0
    assert not row["grouped_graph_winner_gate_passed"]
    assert row["candidate_geometry_unchanged"]
    assert not row["candidate_target_used"]
    assert row["targets_opened_after_candidate_freeze"]
    assert not row["raw_ids_or_absolute_coordinates_in_graphs"]
    assert row["proper_se3_invariant_graphs"]
    assert row["development_targets_consumed"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_bounded_lineage_graph_value_is_grouped_and_honestly_red()
    print("bounded lineage graph value: honest red")
