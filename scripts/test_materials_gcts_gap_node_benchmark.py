#!/usr/bin/env python3

from materials_gcts_gap_node_benchmark import evaluate


def test_bounded_section_gap_node_grows_four_self_fed_levels() -> None:
    result = evaluate()
    assert result.training_atoms == 507
    assert result.initial_atoms == 1969
    assert result.sites_by_recursive_level == (3304, 1332, 300, 2520, 780, 120)
    assert result.exact_added_sites == 8356
    assert result.final_atoms == 10325
    assert result.section_rejections == 420
    assert result.recursive_levels_regenerated == 6
    assert not result.heldout_atoms_inserted
    assert not result.hidden_model_used_for_fitting
    assert result.exact_self_fed_growth
    assert not result.exponential_growth
    assert result.benchmark_passed


if __name__ == "__main__":
    test_bounded_section_gap_node_grows_four_self_fed_levels()
    print("bounded-section gap node: benchmark passed")
