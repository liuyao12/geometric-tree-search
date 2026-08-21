#!/usr/bin/env python3

from materials_gcts_iqc_external_recurrent_branch_transfer_audit import (
    evaluate)


def test_external_recurrent_value_is_disjoint_but_does_not_restore_supply():
    row = evaluate()
    assert row["training_groups_total"] == 30
    assert row["training_groups_admitted"] == 29
    assert row["training_groups_excluded_for_domain_overlap"] == (9,)
    assert row["minimum_admitted_center_separation"] > \
        row["required_center_separation"]
    assert row["maximum_excluded_center_separation"] < \
        row["required_center_separation"]
    assert row["raw_atom_domain_disjoint_by_closed_ball_certificate"]
    assert row["training_examples"] == 338
    assert row["training_positive_examples"] == 195
    assert len(row["training_feature_names"]) == 9
    assert row["training_selected_neighbors"] == 9
    assert row["training_supplied_groups"] == 20
    assert row["training_selected_exact_groups"] == 19
    assert row["training_selection_precision"] == .95
    assert row["frozen_model_digest"] == \
        "b160aa5660c784697e9ce8454890ba5b20717b34062e58aa2e8c84ce54c6b20e"
    assert row["wide_candidate_count"] == 28
    assert row["wide_affected_groups"] == 3
    assert row["wide_recoverable_exact_groups"] == 2
    assert row["wide_selected_exact_groups"] == 1
    assert row["wide_exact_ranks"] == (1, None, 10)
    assert row["wide_selected_false_groups"] == 2
    assert row["wide_false_branches_rejected"] == 24
    assert row["wide_false_unsatisfied_branches"] == 26
    assert row["wide_exact_unsatisfied_branches"] == 2
    assert row["supplied_groups_after_transfer"] == 8
    assert row["supplied_groups"] == 9
    assert row["shuffle_trials"] == 31
    assert row["shuffle_selected_exact_median"] == 1
    assert row["shuffle_selected_exact_maximum"] == 1
    assert row["selected_exact_empirical_p"] == 1.0
    assert row["candidate_digest"] == \
        "958d8dadc285af9744cf61d936a0799d8756e784c4a788003afdb878656850a1"
    assert row["frozen_order_digest"] == \
        "7f7e8180d5aadf7008c97907629beba365055d5779d9c6f6c39547013142dd6f"
    assert row["audit_digest"] == \
        "125ac2573bec99f50d8d96c32c3e6b5d6c8632005971cdb8e82674641ff9ee1a"
    assert row["all_null_candidate_digests_identical"]
    assert not row["wide_labels_used_for_fit_capacity_or_order"]
    assert not row["raw_coordinates_ids_or_group_used_as_model_feature"]
    assert row["labels_joined_after_order_freeze"]
    assert row["candidate_geometry_unchanged"]
    assert not row["integrated_as_default_marking"]
    assert not row["external_recurrent_transfer_gate_passed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_external_recurrent_value_is_disjoint_but_does_not_restore_supply()
    print("external recurrent IQC branch transfer audit passed")
