#!/usr/bin/env python3

from materials_gcts_regenerative_scaling_audit import evaluate


def test_exact_regenerative_growth_does_not_fake_exponential_scaling() -> None:
    result = evaluate(16)
    assert result.wave_sizes == (
        12, 104, 12, 4, 36, 24, 24, 12,
        8, 24, 24, 24, 24, 12, 12, 12)
    assert result.cumulative_sites[-1] == 368
    assert result.all_sites_exact
    assert result.frontier_supply_grows
    assert result.largest_macro_sites == 104
    assert result.two_wave_supermacros == (116, 16, 60, 36, 32, 48, 36, 24)
    assert result.four_wave_supermacros == (132, 96, 80, 60)
    assert result.geometric_mean_growth_factor == 1.0
    assert result.log_sites_vs_wave_r_squared < .61
    assert not result.represented_sites_per_wave_grow_by_two
    assert not result.exponential_gate_passed


if __name__ == "__main__":
    test_exact_regenerative_growth_does_not_fake_exponential_scaling()
    print("regenerative IQC scaling audit: honest red gate passed")
