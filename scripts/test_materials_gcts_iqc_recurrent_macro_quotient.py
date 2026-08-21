#!/usr/bin/env python3
"""Regression and invariance tests for the recurrent IQC macro quotient."""

from __future__ import annotations

from materials_gcts_iqc_recurrent_macro_quotient import (
    canonical_colored_triangle, evaluate)


def test_triangle_key_quotients_node_order_but_not_chemistry():
    first = canonical_colored_triangle(
        ("X", "Y", "Z"), (1., 2., 3.), .25)
    # permutation (2,0,1): pair distances become d20,d21,d01
    second = canonical_colored_triangle(
        ("Z", "X", "Y"), (2., 3., 1.), .25)
    mutated = canonical_colored_triangle(
        ("Z", "X", "X"), (2., 3., 1.), .25)
    assert first == second
    assert first != mutated


def test_real_grouped_quotient_is_honest_and_replay_exact():
    report = evaluate()
    assert report["development_groups"] == 17
    assert report["candidate_occurrences"] == 168
    assert report["exact_candidate_occurrences"] == 72
    assert report["all_exact_alternatives_replayable"]
    assert not report["candidate_geometry_changed_by_quotient"]
    assert not report["raw_coordinates_or_occurrence_ids_used_as_semantic_key"]
    assert not report["wide_atoms_or_labels_used"]
    assert report["shuffle_trials"] == 31


if __name__ == "__main__":
    test_triangle_key_quotients_node_order_but_not_chemistry()
    test_real_grouped_quotient_is_honest_and_replay_exact()
    print("recurrent macro quotient tests passed")
