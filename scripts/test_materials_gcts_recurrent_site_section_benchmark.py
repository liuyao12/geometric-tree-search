#!/usr/bin/env python3
"""Regression for causal colored-terminal section learning."""

from materials_gcts_recurrent_site_section_benchmark import evaluate


def test_recurrent_site_section():
    result = evaluate()
    assert result.fit_patches == (0, 1, 2, 3)
    assert result.calibration_patch == 4
    assert result.selected_train_only
    assert result.fit_site_records > 0
    assert result.calibration_records > 0
    assert result.target_factory_calls == 1
    assert result.target_opened_after_execution_and_site_prediction
    assert result.evaluation_macro_placements_frozen_before_target == 24
    assert len(result.evaluation_candidate_digest) == 64
    assert not result.target_used_during_fit_execution_or_prediction
    assert not result.descriptor_uses_absolute_frame_family_cell_or_raw_ids
    assert result.benchmark_passed == (
        result.precision_gate and result.improves_baseline)


if __name__ == "__main__":
    test_recurrent_site_section()
    print("recurrent site-section benchmark: assertions passed")
