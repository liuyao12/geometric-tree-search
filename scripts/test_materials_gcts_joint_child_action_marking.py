#!/usr/bin/env python3
"""Fast invariants for the frozen joint child-action marking."""

import math

from materials_gcts_joint_child_action_marking import (
    joint_child_action_features, load_default_marking,
    select_joint_child_ids)


def _transform(point):
    x, y, z = point
    return (-y + 7., x - 3., z + 11.)


def _branch(transform=lambda point: point, reverse=False):
    first = (((0., 0., 0.), "X"), ((2., 0., 0.), "Y"),
             ((0., 2., 0.), "Z"))
    children = (
        (((3., 0., 0.), "X"), ((0., 3., 0.), "Y"),
         ((0., 0., 3.), "Z")),
        (((4., 0., 0.), "X"), ((0., 4., 0.), "Y"),
         ((0., 0., 4.), "Z")),
    )
    convert = lambda actions: tuple((transform(point), color)
                                    for point, color in actions)
    return {
        "first_actions": convert(first),
        "second_actions": tuple(convert(tuple(reversed(actions))
                                          if reverse else actions)
                                for actions in children),
        "second_channel_scores": ((.1, .2, .3, .4),
                                  (.4, .3, .2, .1)),
    }


def test_joint_model_is_frozen_and_se3_invariant() -> None:
    model, artifact = load_default_marking()
    assert artifact["training_rows"] == 4016
    assert artifact["positive_rows"] == 12
    assert artifact["selected"]["supplied_exact_child_groups"] == 6
    assert artifact["selected"]["total_exact_child_groups"] == 6
    assert artifact["selected"]["incremental_action_marking_groups"] == 4
    assert model.ridge_lambda == 1000.
    assert model.positive_weight == 1.
    assert model.child_top_k == 1
    assert len(model.feature_names) == 502
    assert model.target_used_for_fitting
    assert not model.target_used_for_scoring
    assert not artifact["candidate_id_or_global_frame_feature"]

    seed = ((-1., 0., 0.), (0., -1., 0.), (0., 0., -1.))
    colors = ("X", "Y", "Z")
    original = joint_child_action_features(
        seed_positions=seed, seed_species=colors, branch=_branch(),
        schema=model.site_schema)
    transformed = joint_child_action_features(
        seed_positions=tuple(_transform(point) for point in seed),
        seed_species=colors, branch=_branch(_transform, reverse=True),
        schema=model.site_schema)
    assert len(original) == len(transformed) == 2
    assert all(math.isclose(first, second, abs_tol=1e-10)
               for row, other in zip(original, transformed)
               for first, second in zip(row, other))
    selected = select_joint_child_ids(
        model=model, seed_positions=seed, seed_species=colors,
        branch=_branch())
    assert len(selected) == 1 and selected[0] in (0, 1)


if __name__ == "__main__":
    test_joint_model_is_frozen_and_se3_invariant()
    print("frozen joint child-action marking: passed")
