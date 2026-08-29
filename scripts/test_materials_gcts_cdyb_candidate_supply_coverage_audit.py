#!/usr/bin/env python3
"""Regression for the Cd--Yb candidate-supply coverage diagnosis."""

from materials_gcts_cdyb_candidate_supply_coverage_audit import evaluate


def test_cdyb_candidate_supply_coverage_audit():
    report = evaluate()
    assert report.training_windows == 5
    assert report.reserved_windows == 2
    assert report.training_atoms == 2385
    assert report.reserved_atoms == 959
    assert report.support_types == 274
    assert report.macro_alternatives == 181
    assert report.maximum_macro_children == 3
    assert report.coverage_options == (1 / 3, 1 / 2)
    relaxed, baseline = report.development
    assert relaxed.minimum_child_coverage == 1 / 3
    assert relaxed.action_rows == 26
    assert relaxed.exact_actions == 14
    assert relaxed.wrong_actions == 1
    assert relaxed.wrong_sites == 10
    assert not relaxed.every_fold_nonempty
    assert not relaxed.zero_wrong_action_gate
    assert baseline.minimum_child_coverage == .5
    assert baseline.action_rows == 14
    assert baseline.exact_actions == 8
    assert baseline.wrong_actions == baseline.wrong_sites == 0
    assert baseline.zero_wrong_action_gate
    assert report.selected_coverage == .5
    assert not report.relaxed_coverage_selected
    assert not report.candidate_supply_extension_safe

    starved, active = report.reserves
    assert starved.recognized_seed_occurrences == 32
    assert starved.recognized_seed_types == 17
    assert starved.macro_anchor_type_overlap == 0
    assert starved.macro_anchor_occurrences == 0
    assert starved.frame_hypotheses == 0
    assert starved.whole_candidates == 0
    assert starved.primitive_port_candidates == 345
    assert starved.primitive_exact_candidates == 204
    assert starved.primitive_exact_site_union == 292
    assert starved.primitive_inexact_candidates == 141
    assert starved.promoted_parents == 0

    assert active.recognized_seed_occurrences == 12
    assert active.recognized_seed_types == 10
    assert active.macro_anchor_type_overlap == 4
    assert active.macro_anchor_occurrences == 4
    assert active.frame_hypotheses == 25
    assert active.whole_candidates == 12
    assert active.primitive_port_candidates == 348
    assert active.primitive_exact_candidates == 134
    assert active.primitive_inexact_candidates == 214
    assert active.accepted_sections_by_wave == (4, 4, 3)
    assert active.emitted_sites == active.correct_sites == 81
    assert active.wrong_sites == 0
    assert active.promoted_parents == 11
    assert active.self_fed

    assert report.baseline_zero_candidate_reserve == 1
    assert report.selected_zero_candidate_reserve == 1
    assert report.primitive_fallback_has_exact_supply
    assert report.selected_total_emitted == report.selected_total_correct == 81
    assert report.selected_total_wrong == 0
    assert report.selected_total_parents == 11
    assert not report.target_used_during_selection_enumeration_ranking_or_execution
    assert report.reserves_previously_consumed
    assert len(report.audit_digest) == 64


if __name__ == "__main__":
    test_cdyb_candidate_supply_coverage_audit()
    print("CdYb candidate-supply coverage audit: passed")
