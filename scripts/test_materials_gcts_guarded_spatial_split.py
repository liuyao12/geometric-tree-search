#!/usr/bin/env python3

from materials_gcts_guarded_spatial_split import evaluate


def test_large_crystal_and_iqc_have_disjoint_three_level_domains() -> None:
    result = evaluate()
    assert result.crystal.atoms == 13_824
    assert result.quasicrystal.atoms == 8_603
    for case in (result.crystal, result.quasicrystal):
        assert len(case.levels) == 3
        assert case.minimum_training_centers >= 100
        assert case.minimum_heldout_centers >= 100
        assert case.all_domains_disjoint
    assert result.three_level_split_feasible
    assert result.benchmark_passed


if __name__ == "__main__":
    test_large_crystal_and_iqc_have_disjoint_three_level_domains()
    print("guarded crystal/IQC spatial split: all assertions passed")
