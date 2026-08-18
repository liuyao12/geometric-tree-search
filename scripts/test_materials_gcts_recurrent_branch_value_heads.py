#!/usr/bin/env python3

from materials_gcts_recurrent_branch_value_heads import (
    DepthBranchExample, fit_grouped_depth_branch_values,
    score_depth_branch)


def test_depth_heads_leave_out_whole_groups_and_select_independent_capacity():
    rows = []
    for group in range(5):
        for depth in (1, 2):
            rows.extend((
                DepthBranchExample(group, depth, (float(depth), -1.),
                                   ("A",) * depth, True),
                DepthBranchExample(group, depth, (float(depth), 1.),
                                   ("B",) * depth, False),
            ))
    model, audit = fit_grouped_depth_branch_values(
        rows, feature_names=("depth", "signal"), color_keys=("A", "B"),
        candidate_neighbors=(1, 3), beta_prior=.5)
    assert audit.groups == 5
    assert audit.depths == (1, 2)
    assert audit.supplied_stages == 10
    assert audit.selected_exact_stages == 10
    assert audit.selected_precision == 1.
    assert tuple(depth for depth, _head in model.heads) == (1, 2)
    assert score_depth_branch(model, 2, (2., -1.), ("A", "A")) > \
        score_depth_branch(model, 2, (2., 1.), ("B", "B"))


def test_mixed_top_score_tie_never_counts_as_selected():
    rows = []
    for group in range(4):
        rows.extend((
            DepthBranchExample(group, 1, (0.,), ("A",), True),
            DepthBranchExample(group, 1, (0.,), ("A",), False),
        ))
    _model, audit = fit_grouped_depth_branch_values(
        rows, feature_names=("collision",), color_keys=("A",),
        candidate_neighbors=(1,), beta_prior=.5)
    assert audit.supplied_stages == 4
    assert audit.selected_exact_stages == 0


if __name__ == "__main__":
    test_depth_heads_leave_out_whole_groups_and_select_independent_capacity()
    test_mixed_top_score_tie_never_counts_as_selected()
    print("depth-conditioned recurrent branch values passed")
