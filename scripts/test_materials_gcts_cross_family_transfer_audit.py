#!/usr/bin/env python3

from materials_gcts_cross_family_transfer_audit import evaluate


def test_cross_family_gate_remains_red_without_shared_selection() -> None:
    result = evaluate()
    assert result.iqc_pair_exact_scales == 2
    assert result.fibonacci_anchor_exact_scales == 2
    assert tuple(item.accepted_sites for item in
                 result.fibonacci_anchor_scales) == (2090, 7222)
    assert all(item.precision == 1.0
               for item in result.fibonacci_anchor_scales)
    assert not result.shared_frozen_marking_selected_without_family_label
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_cross_family_gate_remains_red_without_shared_selection()
    print("cross-family generic marking selection: red audit passed")
