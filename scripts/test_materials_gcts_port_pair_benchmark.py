#!/usr/bin/env python3

from materials_gcts_port_pair_benchmark import evaluate


def test_pair_section_regenerates_five_exact_waves() -> None:
    result = evaluate()
    assert result.accepted_port_pairs == 271
    assert 6.15 < result.learned_frontier_width < 6.16
    assert tuple(wave.proposed_sites for wave in result.waves) == (
        260, 192, 60, 0)
    assert all(wave.precision == 1.0 for wave in result.waves[:-1])
    assert result.exact_nonempty_waves == 3
    assert result.exact_added_atoms == 512
    assert result.final_atoms == 2481
    assert result.stalled
    assert not result.heldout_geometry_used_for_fitting
    assert not result.oracle_colors_used_for_insertion
    assert result.regenerative_growth
    assert not result.exponential_growth
    assert result.benchmark_passed


if __name__ == "__main__":
    test_pair_section_regenerates_five_exact_waves()
    print("higher-order port-pair section: three exact waves passed")
