#!/usr/bin/env python3

from materials_gcts_frozen_hierarchy import evaluate


def test_frozen_hierarchy_dictionary_transfers_across_guard() -> None:
    result = evaluate()
    for case in (result.crystal, result.quasicrystal):
        assert len(case.levels) == 3
        assert case.minimum_heldout_known_fraction == 1.0
        assert case.minimum_heldout_centers >= 271
        assert case.frozen_encoder_reused
        assert all(not level.heldout_refit_used for level in case.levels)
        assert min(level.heldout_promoted_fraction
                   for level in case.levels) >= .90
    assert result.benchmark_passed


if __name__ == "__main__":
    test_frozen_hierarchy_dictionary_transfers_across_guard()
    print("frozen guarded hierarchy transfer: all assertions passed")
