#!/usr/bin/env python3

from materials_gcts_iqc_relational_port_message_quotient_audit import evaluate
from materials_gcts_relational_port_message_quotient import RelationalMessageSpec


def test_finite_relational_quotient_is_honestly_red():
    report = evaluate()
    assert report["development_rows"] == 168
    assert report["development_groups"] == 16
    assert report["development_supplied_groups"] == 9
    assert report["feature_count"] == 216
    assert report["node_feature_count"] == 159
    assert report["edge_feature_count"] == 57
    assert report["finite_state_count"] == 362
    selected = report["selected_development"]
    assert selected["spec"] == {
        "feature_domain": "nodes", "bins": 3,
        "minimum_groups": 4, "top_tokens": 8,
        "aggregation": "top", "admission_threshold": .55,
    }
    assert selected["selected_exact_groups"] == 4
    assert selected["selected_groups"] == 4
    assert selected["selected_precision"] == 1.
    assert report["development_exact_empirical_p"] == .96875
    assert report["wide_candidate_count"] == 28
    assert report["wide_supplied_groups"] == (0, 5)
    assert report["wide_exact_ranks"] == ((0, 3), (3, None), (5, 1))
    assert report["wide_selected_groups"] == 0
    assert report["exact_empirical_p"] == 1.
    assert report["model_digest"] == \
        "4e8603b3d9a111be92a3fab35b345af103032a10e52842d9de6b916313f18f98"
    assert report["audit_digest"] == \
        "23de523aca3e029c9e3ef90e23f4dca25179d8f4939d4525af9cd78ef0d57b47", \
        report["audit_digest"]
    assert report["all_arms_use_identical_candidates"] is True
    assert report["wide_labels_joined_after_all_orders_freeze"] is True
    assert report["raw_ids_or_global_frame_in_state"] is False
    assert report["candidate_geometry_changed"] is False
    assert report["integrated_as_default_marking"] is False
    assert report["finite_relational_message_gate_passed"] is False


def main():
    test_finite_relational_quotient_is_honestly_red()
    print("IQC relational message quotient audit passed")


if __name__ == "__main__":
    main()
