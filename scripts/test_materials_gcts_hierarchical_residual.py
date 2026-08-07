#!/usr/bin/env python3

from materials_gcts_hierarchical_residual import evaluate


def test_parent_markings_extrapolate_hierarchical_displacements() -> None:
    result = evaluate()
    assert result.input_atoms == 1024
    assert result.learned_motif_atoms == 2
    assert result.learned_parent_levels == 3
    assert abs(result.learned_marking_ratio - 0.58) < 1e-8
    assert result.marking_fit_rms < 1e-9
    assert result.marking_recurrence_rms < 1e-9
    assert result.marking_fit_relative_error < 1e-8
    assert result.marking_recurrence_relative_error < 1e-8
    assert result.atom_counts == (1024, 8192, 65536)
    assert result.exact_recursive_growth
    assert result.marked_coordinate_rms < 1e-8
    assert result.flat_copy_coordinate_rms > 1e-3
    assert result.marked_improvement > 1e6
    assert result.atomwise_actions_per_macro_action == 32256.0
    assert result.rigid_motion_invariant
    assert result.random_residual_rejected
