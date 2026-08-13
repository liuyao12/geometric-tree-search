#!/usr/bin/env python3

from materials_gcts_self_fed_graph_benchmark import evaluate


def test_graph_regenerates_three_scales_from_its_own_outputs() -> None:
    result = evaluate()
    assert result.training_atoms == 507
    assert result.initial_atoms == 1969
    assert result.sites_by_recursive_level == (652, 996, 720)
    assert result.exact_added_sites == 2368
    assert result.final_atoms == 4337
    assert result.exact_nonempty_waves == 9
    assert result.recursive_levels_regenerated == 3
    assert not result.heldout_atoms_inserted
    assert not result.oracle_colors_used_for_insertion
    assert result.self_fed_multiscale_growth
    assert not result.exponential_growth
    assert result.benchmark_passed


if __name__ == "__main__":
    test_graph_regenerates_three_scales_from_its_own_outputs()
    print("self-fed multiscale cover graph: benchmark passed")
