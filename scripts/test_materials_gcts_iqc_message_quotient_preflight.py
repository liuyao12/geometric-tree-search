#!/usr/bin/env python3
"""Regression for finite IQC message-color quotient development."""

from materials_gcts_iqc_message_quotient_preflight import (
    MessageQuotientSpec, evaluate)
from materials_gcts_iqc_joint_incidence_graph_preflight import JointFitSpec


def test_finite_message_quotients_compress_but_remain_below_gate():
    report = evaluate()
    assert report.selected_quotient == MessageQuotientSpec(
        4, "coarse", "incidence")
    assert report.selected_fit == JointFitSpec(4, 2, .5)
    assert report.selected_correct_by_group == \
        (2, 0, 2, 2, 2, 2, 2, 2, 1, 0)
    assert report.selected_actions == 20
    assert report.selected_correct_actions == 15
    assert report.selected_false_actions == 5
    assert report.exact_groups == 7
    selected = next(row for row in report.audits
                    if row.quotient == report.selected_quotient and
                    row.fit == report.selected_fit)
    assert selected.node_types == 457
    assert selected.graph_types == 976
    assert selected.descriptor_digest == \
        "836837a10102c2359431bfb2427b10cbc8275ae8b21c19af020145ab1b882fd4"
    assert selected.model_digest == \
        "c31e423eafa0bbaa014d002d6e90d3a2187f07a15c3f1b840b75bf2b0df641e6"
    assert report.exact_candidate_geometry_changed is False
    assert report.selection_target_free is True
    assert report.next_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_finite_message_quotients_compress_but_remain_below_gate()
    print("IQC message-quotient preflight regression passed")


if __name__ == "__main__":
    main()

