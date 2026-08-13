#!/usr/bin/env python3

from materials_gcts_regenerative_scaling_audit import evaluate


def test_exact_regenerative_growth_does_not_fake_exponential_scaling() -> None:
    result = evaluate()
    assert result.wave_sizes == (12, 104, 12, 4, 36, 24, 24, 12)
    assert result.cumulative_sites[-1] == 228
    assert result.all_sites_exact
    assert result.frontier_supply_grows
    assert result.largest_macro_sites == 104
    assert not result.represented_sites_per_wave_grow_by_two
    assert not result.exponential_gate_passed


if __name__ == "__main__":
    test_exact_regenerative_growth_does_not_fake_exponential_scaling()
    print("regenerative IQC scaling audit: honest red gate passed")
