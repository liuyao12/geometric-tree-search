#!/usr/bin/env python3
"""Slow exact five-wave IQC induced-submacro gate."""

from materials_gcts_iqc_action_submacro_audit import evaluate


def test_exact_iqc_waves_have_no_repeated_induced_submacro_yet():
    result = evaluate()
    assert (result.training_atoms, result.seed_atoms) == (887, 231)
    assert result.accepted_action_nodes == 59
    assert result.action_macro_child_counts == (3, 17, 3, 1, 26, 4, 4, 1)
    assert result.connected_induced_candidates == 5254
    assert result.exact_canonical_classes == 5254
    assert result.rejected_insufficient_disjoint_evidence == 5254
    assert result.rejected_nonpositive_mdl == 0
    assert result.admitted_submacro_types == 0
    assert result.exact_action_node_cover
    assert not result.target_used


if __name__ == "__main__":
    test_exact_iqc_waves_have_no_repeated_induced_submacro_yet()
    print("exact five-wave IQC submacro audit: honest zero")
