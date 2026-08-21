"""Regression for sealed blind molecular-port ice continuation."""

from materials_gcts_ice_blind_molecular_growth_benchmark import evaluate


def test_blind_ice_growth_separates_anchor_success_from_orientation_failure() -> None:
    result = evaluate()
    assert result.train_target_raw_molecule_overlap == 0
    assert result.center_separation > result.required_separation
    assert result.target_open_count == 1
    assert result.traces_frozen_before_target
    assert not result.target_used_by_grammar_or_execution
    assert result.exact_port_geometry_certificates
    assert result.one_wave_anchor_gate_passed
    assert result.factored_first_wave_correct > 0
    assert result.factored_first_wave_wrong == 0
    assert result.factored_first_wave_precision == 1
    assert not result.sustained_blind_molecular_growth_passed
    assert result.factored_two_wave_wrong > 0
    assert result.unresolved_orientation_hypotheses > 0
    assert result.two_level_anchor_gate_passed
    assert result.unanimous_wave_anchors == (16, 8, 0)
    assert result.unanimous_correct_anchors == 24
    assert result.unanimous_wrong_anchors == 0
    assert result.unanimous_precision == 1
    assert result.exact_unseen_anchor_levels == 2
    assert result.unanimous_reached_fixed_point
    assert not result.stationary_or_exponential_claim


if __name__ == "__main__":
    test_blind_ice_growth_separates_anchor_success_from_orientation_failure()
    print("sealed blind ice anchors: two exact levels; molecular orientation remains red")
