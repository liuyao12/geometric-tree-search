#!/usr/bin/env python3

from materials_gcts_metric_port_benchmark import evaluate


def test_metric_ports_transfer_without_heldout_geometry() -> None:
    result = evaluate()
    assert result.training_atoms == 507
    assert result.training_parents == 93
    assert result.evaluation_atoms == 1969
    assert result.proposed_sites == result.true_sites == 380
    assert result.precision == 1.0
    assert result.recall > .05
    assert result.minimum_votes == 2
    assert result.maximum_votes == 3
    assert result.supercluster_sizes == (240, 140)
    assert result.parallel_supercluster_actions == 2
    assert result.site_per_supercluster_action == 190.0
    assert result.precision_gain > 6.0
    assert not result.heldout_geometry_used_for_fitting
    assert not result.physical_potential_used
    assert result.benchmark_passed


if __name__ == "__main__":
    test_metric_ports_transfer_without_heldout_geometry()
    print("scale-normalized motif-centre ports: benchmark passed")
