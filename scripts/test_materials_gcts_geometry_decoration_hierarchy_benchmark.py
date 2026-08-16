#!/usr/bin/env python3
"""Regression for geometry-first cluster-of-clusters decoration transfer."""

from materials_gcts_geometry_decoration_hierarchy_benchmark import evaluate


def test_geometry_decoration_hierarchy_benchmark():
    result = evaluate(maximum_nodes=3)
    assert result.training_atoms == 4405
    assert result.heldout_atoms == 873
    assert result.promoted_geometry_types == result.quotient_macro_types
    assert result.promoted_train_occurrences > 0
    assert result.promoted_geometry_types == 457
    assert result.heldout_promoted_occurrences == 13
    assert result.heldout_known_decoration_occurrences == 0
    assert result.heldout_macro_child_role_samples == 27
    assert result.heldout_macro_role_context_coverage == 1.
    assert result.heldout_macro_role_decoration_accuracy == 5 / 27
    assert result.heldout_primitive_modal_accuracy_on_same_samples == 2 / 27
    assert result.macro_role_empirical_p_value == .1875
    assert not result.macro_role_beats_shuffled_controls
    assert result.selected_macro_boundary_schema == "boundary_fine"
    assert result.heldout_macro_boundary_decoration_accuracy == 5 / 27
    assert result.macro_boundary_empirical_p_value == .125
    assert result.heldout_macro_boundary_unique_children == 19
    assert result.heldout_macro_boundary_consensus_accuracy == 3 / 19
    assert result.macro_boundary_consensus_empirical_p_value == .21875
    assert result.heldout_macro_child_train_seen_alternative_samples == 9
    assert result.heldout_macro_boundary_unique_children_with_train_seen_alternative == 7
    assert result.heldout_promoted_occurrences >= \
        result.heldout_known_decoration_occurrences
    assert result.geometry_fit_before_target_opened
    assert not result.heldout_used_for_fit_mining_or_quotient
    assert result.target_positions_used_for_reencoding
    assert not result.autonomous_growth_claimed
    assert result.hierarchy_decoration_gate_passed == (
        result.heldout_known_decoration_occurrence_coverage >= .9 and
        result.heldout_known_decoration_atom_coverage >= .95)


if __name__ == "__main__":
    test_geometry_decoration_hierarchy_benchmark()
    print("geometry-decoration hierarchy benchmark: assertions passed")
