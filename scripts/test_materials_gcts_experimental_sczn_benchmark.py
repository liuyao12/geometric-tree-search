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


if __name__ == "__main__":
    test_experimental_quasicrystal_has_learned_supercluster_signal()
    print("experimental Sc-Zn hierarchy benchmark: all assertions passed")
