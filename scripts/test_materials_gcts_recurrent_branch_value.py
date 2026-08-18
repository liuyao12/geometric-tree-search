#!/usr/bin/env python3
"""Focused controls for the target-free recurrent branch value."""

from __future__ import annotations

from materials_gcts_recurrent_branch_value import (
    RecurrentBranchExample,
    branch_value_features,
    fit_grouped_recurrent_branch_value,
    recurrent_branch_value_digest,
    score_recurrent_branch,
)


def _corpus():
    rows = []
    for group, offset in enumerate((0., .15, -.12, .08)):
        rows.extend((
            RecurrentBranchExample(
                f"patch-{group}", (1. + offset, .2), ("A", "A", "B"), True),
            RecurrentBranchExample(
                f"patch-{group}", (-1. + offset, .7), ("A", "B", "B"), False),
        ))
    return tuple(rows)


def test_grouped_capacity_and_color_population_are_frozen():
    model, audit = fit_grouped_recurrent_branch_value(
        _corpus(), feature_names=("closure", "reach"),
        color_keys=("A", "B"), candidate_neighbors=(1, 3, 5))
    assert audit.groups == 4
    assert audit.selected_exact_groups == audit.supplied_groups == 4
    assert audit.selected_precision == 1.
    assert model.target_used is False
    assert model.feature_names[-2:] == (
        "action_population:A", "action_population:B")
    assert branch_value_features((2., 3.), ("B", "A", "A"),
                                 ("A", "B")) == (2., 3., 2., 1.)
    assert score_recurrent_branch(model, (1.02, .2), ("B", "A", "A")) > \
        score_recurrent_branch(model, (-1.02, .7), ("B", "B", "A"))


def test_input_permutation_preserves_model_and_score():
    rows = _corpus()
    first, first_audit = fit_grouped_recurrent_branch_value(
        rows, feature_names=("closure", "reach"), color_keys=("A", "B"),
        candidate_neighbors=(1, 3, 5))
    second, second_audit = fit_grouped_recurrent_branch_value(
        tuple(reversed(rows)), feature_names=("closure", "reach"),
        color_keys=("A", "B"), candidate_neighbors=(1, 3, 5))
    assert first_audit.selected_neighbors == second_audit.selected_neighbors
    assert recurrent_branch_value_digest(first) == \
        recurrent_branch_value_digest(second)
    assert score_recurrent_branch(first, (1., .2), ("A", "A", "B")) == \
        score_recurrent_branch(second, (1., .2), ("B", "A", "A"))


if __name__ == "__main__":
    test_grouped_capacity_and_color_population_are_frozen()
    test_input_permutation_preserves_model_and_score()
    print("recurrent branch value tests passed")
