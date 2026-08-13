#!/usr/bin/env python3

from materials_gcts_spatial_sector_benchmark import evaluate


def test_iqc_frontier_hierarchy_is_spatial_not_temporal() -> None:
    result = evaluate(16)
    assert result.exact_frontier_atoms == 368
    assert result.spatial_domains == 8
    assert result.exact_cover_each_level
    assert not result.construction_order_used
    assert result.second_level_cluster_of_clusters
    assert result.three_level_spatial_hierarchy
    assert result.largest_recurrent_supports == (3, 11, 37)
    assert result.minimum_support_amplification > 3.0
    assert result.exponential_support_gate_passed
    assert result.projected_additional_promotions_to_million == 9
    assert not result.million_projection_verified
    assert result.benchmark_passed


if __name__ == "__main__":
    test_iqc_frontier_hierarchy_is_spatial_not_temporal()
    print("IQC spatial sector hierarchy: all assertions passed")
