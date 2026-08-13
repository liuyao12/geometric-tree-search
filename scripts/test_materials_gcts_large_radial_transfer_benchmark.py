#!/usr/bin/env python3

from materials_gcts_large_radial_transfer_benchmark import evaluate


def test_three_level_iqc_hierarchy_transfers_across_radial_guard() -> None:
    result = evaluate()
    assert result.training_atoms > 20_000
    assert result.heldout_oracle_atoms == 155097
    assert result.all_raw_domains_disjoint
    assert result.three_nonempty_levels
    assert result.minimum_known_fraction == 0.0
    assert result.minimum_promoted_fraction >= .95
    assert result.amorphous_promoted_fractions[0] < .5
    assert result.amorphous_promoted_fractions[2] < .5
    assert result.amorphous_rejected_at_first_and_third_level
    assert result.benchmark_passed


if __name__ == "__main__":
    test_three_level_iqc_hierarchy_transfers_across_radial_guard()
    print("large guarded radial IQC transfer: all assertions passed")
