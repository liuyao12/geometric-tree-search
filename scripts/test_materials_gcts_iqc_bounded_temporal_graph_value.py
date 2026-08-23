"""Regression for cross-stage temporal IQC lineage value."""

from materials_gcts_iqc_bounded_temporal_graph_value import load_default_result


def test_temporal_lineage_value_preserves_incidence_but_stays_red():
    row = load_default_result()
    assert row["groups"] == 5
    assert row["examples"] == 5237
    assert row["positive_examples"] == 149
    assert row["temporal_actions_per_lineage"] == 9
    assert row["temporal_stages_per_lineage"] == 3
    assert row["full_feature_count"] == 2564
    assert row["outer_selected_exact_groups"] == 2
    assert row["outer_first_exact_rank_sum"] == 384
    assert tuple((fold["selected_exact"], fold["first_exact_rank"])
                 for fold in row["outer_folds"]) == (
                     (False, 324), (False, 40), (True, 1),
                     (True, 1), (False, 18))
    assert row["shuffle_controls_requested"] == 31
    assert row["shuffle_controls_executed"] == 0
    assert not row["grouped_temporal_winner_gate_passed"]
    assert row["candidate_geometry_unchanged"]
    assert not row["candidate_target_used"]
    assert row["targets_opened_after_candidate_freeze"]
    assert not row["raw_atom_ids_retained"]
    assert not row["absolute_coordinates_retained"]
    assert row["proper_se3_invariant_graphs"]
    assert row["cross_stage_incidence_preserved"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_temporal_lineage_value_preserves_incidence_but_stays_red()
    print("bounded temporal graph value: honest red")
