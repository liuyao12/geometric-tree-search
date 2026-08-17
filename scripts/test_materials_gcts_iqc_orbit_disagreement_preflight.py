#!/usr/bin/env python3
"""Regression for the post-confirmation orbit-disagreement audit."""

from materials_gcts_iqc_orbit_disagreement_preflight import evaluate


def test_orbit_disagreement_remains_below_ten_nucleus_gate():
    report = evaluate()
    assert report.candidate_graph_digest == \
        "ddd96b159b0c3d8cbdfbc64b90ba583c17a6afd8cbdd31d93aead66b5a56e8c3"
    assert report.descriptor_digest == \
        "e0cd70660af36cc1614db02eda6786c03e21c49da3ba194f8df0ebe432ae7047"
    assert report.fold_model_digest == \
        "898c11311d5466780125ceca59921a8b9a1cc6f5784d23bd340f727a883762e2"
    assert report.selected_correct_by_group == \
        (2, 2, 1, 2, 2, 2, 2, 2, 1, 2)
    assert report.selected_actions == 20
    assert report.selected_correct_actions == 18
    assert report.selected_false_actions == 2
    assert report.exact_groups == 8
    assert report.next_domains_disjoint is True
    assert report.next_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_orbit_disagreement_remains_below_ten_nucleus_gate()
    print("IQC orbit-disagreement preflight regression passed")


if __name__ == "__main__":
    main()
