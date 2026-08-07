#!/usr/bin/env python3

from materials_gcts_recursive_marking_ablation import evaluate


def test_recursive_markings_remove_real_geometric_ambiguity() -> None:
    result = evaluate()
    assert result.all_markings_causal
    assert result.crystal.candidates_without_marking == 2 ** 56
    assert result.crystal.candidates_with_marking == 1
    assert result.quasicrystal.candidates_with_marking == 8603
    assert result.quasicrystal.candidates_without_marking > 8603
    assert result.quasicrystal.rejected_fraction > 0.5
    assert (result.substitution_quasicrystal.candidates_without_marking ==
            392)
    assert (result.substitution_quasicrystal.candidates_with_marking <
            result.substitution_quasicrystal.candidates_without_marking)
