#!/usr/bin/env python3

from materials_gcts_iqc_boundary_port_backoff_audit import (
    BoundaryRule, _fit_threshold, _shuffle_labels_within_group, evaluate)


def test_bounded_boundary_backoff_is_honestly_noncausal():
    row = evaluate()
    assert row["forward_unsatisfied_branches"] == 28
    assert row["forward_unsatisfied_exact"] == 2
    assert row["forward_unsatisfied_false"] == 26
    assert row["candidate_feature_count"] == 6
    assert row["selected_feature"] == "ordered_port_length_nn"
    assert row["selected_direction"] == "ge"
    assert abs(row["selected_threshold"] - 9.3709435) < 1e-12
    assert row["group_heldout_metrics"] == {
        "exact_groups_deferred": 2,
        "exact_deferred": 2,
        "false_deferred": 18,
        "false_rejected": 8,
    }
    assert (row["deferred_exact"], row["deferred_false"],
            row["rejected_exact"], row["rejected_false"]) == (2, 18, 0, 8)
    assert (row["final_exact"], row["final_false"]) == (59, 53)
    assert abs(row["final_precision"] - 59 / 112) < 1e-12
    assert row["supplied_groups_after_backoff"] == 9
    assert row["supplied_groups"] == 9
    assert row["shuffle_trials"] == 31
    assert row["shuffle_exact_deferred_median"] == 2
    assert row["shuffle_false_rejected_median"] == 8
    assert row["exact_deferred_empirical_p"] == 1.
    assert row["false_rejected_empirical_p"] == 1.
    assert row["deferred_is_not_port_satisfied"]
    assert row["candidate_geometry_unchanged"]
    assert not row["group_label_or_raw_occurrence_id_used_as_feature"]
    assert not row["target_used_for_boundary_features"]
    assert row["development_labels_used_for_family_selection"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["integrated_as_default_marking"]
    assert row["boundary_backoff_supply_gate_passed"]
    assert not row["causal_marking_gate_passed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


def test_threshold_fit_and_shuffle_are_deterministic_and_id_free():
    rows = (
        {"group": 0, "exact": True,
         "boundary_context": {"x": 2.}},
        {"group": 0, "exact": False,
         "boundary_context": {"x": 2.}},
        {"group": 1, "exact": False,
         "boundary_context": {"x": 0.}},
    )
    rule = _fit_threshold(rows, "x", "ge")
    assert isinstance(rule, BoundaryRule)
    assert rule.accepts(rows[0]) and rule.accepts(rows[1])
    assert not rule.accepts(rows[2])
    first = _shuffle_labels_within_group(rows, 0)
    second = _shuffle_labels_within_group(rows, 0)
    assert first == second
    assert sum(first) == sum(row["exact"] for row in rows)
    for group in (0, 1):
        indices = [index for index, row in enumerate(rows)
                   if row["group"] == group]
        assert sum(first[index] for index in indices) == sum(
            rows[index]["exact"] for index in indices)


if __name__ == "__main__":
    test_bounded_boundary_backoff_is_honestly_noncausal()
    test_threshold_fit_and_shuffle_are_deterministic_and_id_free()
    print("IQC boundary port backoff audit passed")
