#!/usr/bin/env python3

from materials_gcts_hierarchical_cover_benchmark import evaluate


def test_clusters_of_clusters_compile_to_exact_overlapping_covers() -> None:
    result = evaluate()
    assert result.structured_exact
    assert result.structured_prototypes_replay
    assert result.structured_uses_overlaps
    assert result.structured_has_three_levels
    assert result.disorder_rejected
    assert result.crystal.maximum_macro_reference_compression > 1.0
    assert result.quasicrystal.maximum_macro_reference_compression > 1.0
    # Geometry-bearing replay is now real, but one modal production covers
    # only 30--33% of occurrences.  The benchmark remains red until the
    # grammar learns context-marked production alternatives.
    assert not result.reusable_production_gate_passed
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_clusters_of_clusters_compile_to_exact_overlapping_covers()
    print("hierarchical overlapping-cover grammar: all assertions passed")
