#!/usr/bin/env python3

from materials_gcts_incoming_port_ablation import evaluate


def test_inward_atom_halo_is_not_mislabeled_as_causal_gcts() -> None:
    result = evaluate()
    assert result.crystal.hierarchy_level == 3
    assert result.crystal.oracle_seen_fraction == 1.0
    assert result.crystal.rhs_alternatives == result.crystal.parent_types
    assert result.crystal.modal_backtracks == 0
    assert not result.crystal.marking_causal
    # With the richer train-selected IQC parent colors, each parent has one
    # cover derivation. Marking cannot improve an already forced move.
    assert result.quasicrystal.hierarchy_level == 2
    assert result.quasicrystal.rhs_alternatives == result.quasicrystal.parent_types
    assert result.quasicrystal.modal_backtracks == 0
    assert not result.quasicrystal.marking_causal
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_inward_atom_halo_is_not_mislabeled_as_causal_gcts()
    print("causal incoming-port search ablation: honest red gate passed")
