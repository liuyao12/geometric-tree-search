#!/usr/bin/env python3
"""Live-data regression test for experimental Sc-Zn cluster learning."""

from materials_gcts_experimental_sczn_benchmark import evaluate


def test_experimental_quasicrystal_has_learned_supercluster_signal() -> None:
    result = evaluate()
    assert result.raw_rows == 41981
    assert result.unique_sites == 37531
    assert result.selected_shell_species == "Sc"
    assert result.learned_cluster_centers >= 150
    assert 4.8 < result.learned_shell_radius_angstrom < 5.1
    assert result.learned_link_lengths_angstrom == (12.0, 13.8)
    assert result.center_hierarchy_supports == (13, 38, 98)
    assert result.center_hierarchy_cover_fraction[-1] >= .70
    assert abs(result.learned_inflation_scale - 1.618) < .02
    assert result.training_inflation_precision >= .25
    assert result.heldout_inflation_precision >= .15
    assert result.marked_heldout_inflation_precision == 1.0
    assert result.marked_heldout_inflation_recall == 1.0
    assert result.marking_precision_gain > .80
    assert result.single_section_heldout_precision == .6
    assert result.pair_only_heldout_precision == 3 / 8
    assert result.geometry_only_heldout_precision == .6
    assert result.chemistry_precision_gain == 0.0
    assert result.marking_descriptor_dimensions == 29
    assert result.marking_training_samples == 12
    assert result.marking_heldout_samples == 18
    assert result.marked_heldout_candidates == 3
    assert result.marking_rotation_invariant


if __name__ == "__main__":
    test_experimental_quasicrystal_has_learned_supercluster_signal()
    print("experimental Sc-Zn hierarchy benchmark: all assertions passed")
