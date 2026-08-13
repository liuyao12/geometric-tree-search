#!/usr/bin/env python3

from materials_gcts_spatial_macro_audit import evaluate


def test_temporal_waves_are_not_mislabeled_as_spatial_macro_hierarchy() -> None:
    result = evaluate(16)
    assert result.waves == 16
    assert result.exact_sites == 368
    assert result.spatial_patch_occurrences >= result.spatial_patch_types
    assert result.window_width == 4
    assert result.recurrent_multisite_types == 2
    assert result.largest_recurrent_patch_sites == 2
    assert result.hierarchy_depth_proved == 1
    assert result.spatial_recurrence_gate_passed
    assert not result.exponential_macro_gate_passed


if __name__ == "__main__":
    test_temporal_waves_are_not_mislabeled_as_spatial_macro_hierarchy()
    print("spatial IQC macro audit: honest hierarchy gate passed")
