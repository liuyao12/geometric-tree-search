#!/usr/bin/env python3

from materials_gcts_on_policy_branch_aggregation import (
    fit_group_sealed_on_policy_values)
from materials_gcts_recurrent_branch_value_heads import (
    DepthBranchExample, score_depth_branch)


def _row(group, depth, signal, successful):
    return DepthBranchExample(
        group, depth, (float(depth), float(signal)),
        ("good" if signal > 0 else "bad",) * depth, successful)


def test_group_sealed_fit_retains_conflicting_outcomes():
    broad = []
    policy = []
    for group in range(6):
        for depth in (1, 2):
            broad.extend((_row(group, depth, 1, True),
                          _row(group, depth, -1, False)))
            policy.append(_row(group, depth, 1, True))
    # The identical invariant state has two observed futures.  Both labels must
    # survive; insertion order cannot silently make it deterministic.
    policy.append(_row(0, 1, 1, False))
    model, audit = fit_group_sealed_on_policy_values(
        broad, policy, heldout_groups=(4, 5),
        feature_names=("depth", "signal"), color_keys=("bad", "good"),
        neighbors_by_depth=((1, 1), (2, 1)))
    assert audit.training_groups == 4
    assert audit.heldout_seen_during_fit is False
    assert audit.target_used is False
    assert audit.conflicting_descriptor_groups == 1
    assert audit.merged_examples == 17
    assert score_depth_branch(model, 2, (2., 1.), ("good", "good")) > \
        score_depth_branch(model, 2, (2., -1.), ("bad", "bad"))


def test_heldout_rows_never_affect_frozen_model():
    broad = []
    policy = []
    for group in range(5):
        broad.extend((_row(group, 1, 1, True),
                      _row(group, 1, -1, False)))
        policy.append(_row(group, 1, 1, True))
    model_a, audit_a = fit_group_sealed_on_policy_values(
        broad, policy, heldout_groups=(4,),
        feature_names=("depth", "signal"), color_keys=("bad", "good"),
        neighbors_by_depth=((1, 1),))
    changed = tuple(policy) + (_row(4, 1, -1, True),)
    model_b, audit_b = fit_group_sealed_on_policy_values(
        broad, changed, heldout_groups=(4,),
        feature_names=("depth", "signal"), color_keys=("bad", "good"),
        neighbors_by_depth=((1, 1),))
    assert model_a == model_b
    assert audit_a.training_example_digest == audit_b.training_example_digest
    assert audit_a.model_digest == audit_b.model_digest


if __name__ == "__main__":
    test_group_sealed_fit_retains_conflicting_outcomes()
    test_heldout_rows_never_affect_frozen_model()
    print("group-sealed on-policy branch aggregation passed")
