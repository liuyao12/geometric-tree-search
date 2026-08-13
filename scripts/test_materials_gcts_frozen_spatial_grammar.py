#!/usr/bin/env python3

from materials_gcts_frozen_spatial_grammar_benchmark import evaluate


def test_iqc_spatial_grammar_transfers_to_heldout_halfspace() -> None:
    result = evaluate(16)
    assert result.exact_frontier_atoms == 368
    assert result.training_domains == result.heldout_domains == 4
    assert not result.heldout_geometry_used_for_fitting
    assert result.heldout_unseen_types == (0, 0, 0)
    assert result.heldout_unseen_productions == (0, 0, 0)
    assert result.heldout_atom_coverage == (1.0, 1.0, 1.0)
    assert result.heldout_production_agreement == (1.0, 1.0, 1.0)
    assert result.three_levels_transfer
    assert result.benchmark_passed


if __name__ == "__main__":
    test_iqc_spatial_grammar_transfers_to_heldout_halfspace()
    print("frozen IQC spatial grammar: all assertions passed")
