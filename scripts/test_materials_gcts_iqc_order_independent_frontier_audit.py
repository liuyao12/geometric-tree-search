#!/usr/bin/env python3
"""Regression for the order-independent post-commit IQC frontier audit."""

from materials_gcts_incidence_token_marking import CandidateIncidenceDescriptor
from materials_gcts_iqc_order_independent_frontier_audit import (
    _fit, _fit_from_statistics, _group_token_statistics, evaluate)


def test_group_statistics_reproduce_direct_marking_fit():
    token_a = CandidateIncidenceDescriptor((("role", "a"),))
    token_b = CandidateIncidenceDescriptor((("role", "b"),))
    groups = (
        (((token_a, True), (token_b, False)),),
        (((token_a, True), (token_b, False)),),
        (((token_a, False), (token_b, True)),),
    )
    setting = (2, 2, .5)
    direct = _fit(groups, frozenset((2,)), setting)
    counted = _fit_from_statistics(
        _group_token_statistics(groups), 2, setting)
    assert direct == counted


def test_order_independent_frontier_audit_is_honest():
    report = evaluate()
    assert report.training_groups == 10
    assert report.validation_groups == 8
    assert report.training_candidates == 20_716
    assert report.training_exact_actions == 1_151
    assert report.selected_marking == (4, 2, .5)
    assert report.validation_frontier_candidates == (
        766, 678, 728, 728, 828, 634, 633, 633)
    assert report.validation_global_exact_actions == (
        73, 57, 66, 66, 75, 61, 61, 61)
    assert report.compatibility_first_exact_ranks == (3, 3, 4, 4, 1, 9, 9, 9)
    assert report.marked_first_exact_ranks == (3, 4, 3, 3, 1, 1, 1, 1)
    assert report.marked_top1_exact_by_group == (
        False, False, False, False, True, True, True, True)
    assert report.required_configuration_beam_width == 4
    assert report.all_global_frontiers_have_exact_action
    assert report.width_four_conditional_supply_gate_passed
    assert not report.top1_selection_gate_passed
    assert report.order_independent_frontier_materially_required
    assert report.training_truth_used_only_for_causal_trace_labels
    assert report.validation_truth_used_to_construct_conditional_prefix
    assert not report.heldout_truth_used_to_fit_marking
    assert not report.autonomous_growth_claimed


if __name__ == "__main__":
    test_group_statistics_reproduce_direct_marking_fit()
    test_order_independent_frontier_audit_is_honest()
    print("order-independent IQC frontier audit passed")
