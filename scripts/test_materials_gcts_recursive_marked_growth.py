#!/usr/bin/env python3

from materials_gcts_recursive_marked_growth import evaluate


def test_recursive_marked_iqc_growth() -> None:
    result = evaluate()
    assert result.training_atoms == 507
    assert result.target_cluster_atoms == 2229
    assert result.generated_new_atoms == 1722
    assert result.recursive_actions == 1
    assert result.atomwise_action_compression == 1722.0
    assert result.position_precision == 1.0
    assert result.position_recall == 1.0
    assert result.species_precision == 1.0
    assert result.species_recall == 1.0
    assert result.marking_residual < 1e-5
