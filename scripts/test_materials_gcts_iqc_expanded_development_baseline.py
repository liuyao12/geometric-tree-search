#!/usr/bin/env python3
"""Regression for the preregistered expanded IQC development baseline."""

from materials_gcts_iqc_expanded_development_baseline import evaluate


def test_frozen_quotient_on_expanded_development_corpus():
    report = evaluate()
    assert report.preregistration_digest == \
        "c21e3fa12d2b2670af48974e5fd3856383c3518887fe28669abcd4e9a6464d43"
    assert report.total_groups == 18
    assert report.expanded_oracle_lift_bound == 24
    assert report.expanded_oracle_bound_plus_one_stable is True
    assert report.expanded_seed_atoms == \
        (476, 488, 476, 476, 496, 490, 490, 490)
    assert report.expanded_target_atoms == \
        (2028, 2041, 2033, 2033, 2037, 2064, 2064, 2064)
    assert report.candidate_graph_digest == \
        "4b0058c447643240426e3a8eb92ce0128e29a4065f141a58eede36e695b7526c"
    assert report.descriptor_digest == \
        "cb15025d9a446326566f1ad151a218cb671ba25c724dcdd8489a1fd013009612"
    assert report.selected_correct_by_group == \
        (2, 0, 2, 2, 2, 2, 2, 2, 2, 0, 1, 2, 2, 2, 1, 2, 2, 2)
    assert report.selected_actions == 36
    assert report.selected_correct_actions == 30
    assert report.selected_false_actions == 6
    assert report.exact_groups == 14
    assert report.expanded_targets_materialized_after_preregistration_commit \
        is True
    assert report.reserved_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_frozen_quotient_on_expanded_development_corpus()
    print("expanded IQC development baseline regression passed")


if __name__ == "__main__":
    main()
