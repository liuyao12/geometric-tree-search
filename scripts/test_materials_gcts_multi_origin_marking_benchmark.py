#!/usr/bin/env python3

from materials_gcts_multi_origin_marking_benchmark import evaluate


def test_marking_rejects_false_branches_on_unseen_parent_centres() -> None:
    result = evaluate()
    assert result.training_origins == 83
    assert result.heldout_origins == 90
    assert result.training_candidates == 2261
    assert result.heldout_candidates == 2441
    assert result.unmarked_precision < .10
    assert result.histogram_precision > .60
    assert result.moment_precision > .50
    assert result.conjunctive_precision > .70
    assert result.conjunctive_recall > .50
    assert result.marked_false_branches <= 40
    assert result.false_branch_reduction >= 50
    assert result.materialized_target_centers == 159
    assert result.verified_target_centers == 120
    assert result.verified_target_mean_error < .15
    assert result.fixed_points_excluded
    assert not result.split_uses_target_labels
    assert result.settings_selected_by_parent_group_cv
    assert result.conservative_precision > .80
    assert result.conservative_recall > .30
    assert result.conservative_false_branch_reduction > 150


if __name__ == "__main__":
    test_marking_rejects_false_branches_on_unseen_parent_centres()
    print("multi-origin experimental marking benchmark: all assertions passed")
