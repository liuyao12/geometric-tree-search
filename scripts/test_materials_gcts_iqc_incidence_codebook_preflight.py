#!/usr/bin/env python3
"""Regression for recurring IQC incidence-codebook development."""

from materials_gcts_iqc_incidence_codebook_preflight import (
    LOCAL_FAMILIES, MESSAGE_FAMILIES, evaluate)


def test_recurrent_codebook_is_compact_but_below_gate():
    report = evaluate()
    assert report.candidate_graph_digest == \
        "ddd96b159b0c3d8cbdfbc64b90ba583c17a6afd8cbdd31d93aead66b5a56e8c3"
    assert report.descriptor_digest == \
        "836837a10102c2359431bfb2427b10cbc8275ae8b21c19af020145ab1b882fd4"
    assert report.selected_spec.token_families == \
        MESSAGE_FAMILIES + LOCAL_FAMILIES
    assert report.selected_spec.nearest_prototypes == 2
    assert report.selected_spec.minimum_groups == 3
    assert report.selected_correct_by_group == \
        (0, 0, 0, 2, 2, 2, 2, 2, 1, 0)
    assert report.selected_actions == 20
    assert report.selected_correct_actions == 11
    assert report.selected_false_actions == 9
    assert report.exact_groups == 5
    selected = next(row for row in report.audits
                    if row.spec == report.selected_spec)
    assert selected.fold_prototype_counts == \
        (358, 357, 356, 358, 357, 358, 357, 357, 356, 357)
    assert selected.fold_model_digest == \
        "f6615a79d795d42df173eeb3b650c3387c0bfd1c16e0456260ed6a1e5e889afe"
    assert report.exact_candidate_geometry_changed is False
    assert report.selection_target_free is True
    assert report.next_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_recurrent_codebook_is_compact_but_below_gate()
    print("IQC incidence-codebook preflight regression passed")


if __name__ == "__main__":
    main()
