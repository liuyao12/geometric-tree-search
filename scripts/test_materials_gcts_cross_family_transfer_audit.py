#!/usr/bin/env python3

from materials_gcts_cross_family_transfer_audit import _learn_anchor, evaluate
from materials_gcts_fibonacci_3d import PHI, make_input
from materials_gcts_generic import AtomicConfiguration


def test_family_blind_selector_chooses_two_exact_markings() -> None:
    result = evaluate()
    assert result.crystal_selected_hypothesis == "translation_quotient"
    assert result.crystal_exact_scales == 2
    assert result.iqc_pair_exact_scales == 2
    assert result.fibonacci_anchor_exact_scales == 2
    assert tuple(item.accepted_sites for item in
                 result.fibonacci_anchor_scales) == (2090, 7222)
    assert all(item.precision == 1.0
               for item in result.fibonacci_anchor_scales)
    assert result.iqc_anchor_support == 61
    assert result.fibonacci_anchor_support == 216
    assert result.selector_iqc_hypothesis == "port_pair"
    assert result.selector_fibonacci_hypothesis == "anchor"
    assert result.shared_frozen_marking_selected_without_family_label
    assert result.benchmark_passed


def test_anchor_learning_is_translation_invariant() -> None:
    source = make_input(9)
    shift = (3.75, -8.5, 11.25)
    moved = AtomicConfiguration(
        source.name, tuple(tuple(point[axis] + shift[axis]
                                 for axis in range(3))
                           for point in source.positions), source.species,
        None, False, source.provenance)
    support, anchor = _learn_anchor(
        moved, PHI, (1.1, 1.7, 2.4, 3.0))
    assert support == 216
    assert all(abs(anchor[axis] - shift[axis]) < 1e-4 for axis in range(3))


if __name__ == "__main__":
    test_family_blind_selector_chooses_two_exact_markings()
    test_anchor_learning_is_translation_invariant()
    print("cross-family generic marking selection: benchmark passed")
