"""Regression for Ih-trained, Ic-evaluated blind molecular growth."""

from materials_gcts_ice_cross_polytype_blind_growth_benchmark import evaluate


def test_cross_polytype_first_wave_is_exact_but_sustained_gate_is_red() -> None:
    result = evaluate()
    assert result.trained_polytype == "ice-Ih"
    assert result.evaluated_polytype == "ice-Ic"
    assert result.target_open_count == 1
    assert not result.target_used_before_scoring
    assert result.first_wave_cross_polytype_gate_passed
    assert result.factored_first_wave_correct > 0
    assert result.factored_first_wave_wrong == 0
    assert result.factored_first_wave_precision == 1
    assert not result.sustained_cross_polytype_gate_passed
    assert result.factored_two_wave_wrong > 0


if __name__ == "__main__":
    test_cross_polytype_first_wave_is_exact_but_sustained_gate_is_red()
    print("cross-polytype blind molecular growth: exact first wave, honest sustained red")
