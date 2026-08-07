#!/usr/bin/env python3

from materials_gcts_generic import perturb
from materials_gcts_icosahedral_modelset import (
    HIDDEN_UNIT,
    evaluate,
    infer_model,
    oracle_patch,
)


def main() -> None:
    result = evaluate()
    assert result.input_atoms == 507
    assert result.chemical_species == 3
    assert result.quadratic_unit_error < 1e-12
    assert result.maximum_lift_residual < 1e-10
    assert result.inferred_window_radius == 1.5
    assert result.inferred_species_thresholds == (0.75, 1.125)
    assert result.grown_atoms == 2229
    assert result.lift_set_precision == 1.0
    assert result.lift_set_recall == 1.0
    assert result.grown_species_accuracy == 1.0
    assert result.maximum_position_error < 1e-10
    assert result.local_overlap_forced == result.local_overlap_hidden
    assert result.local_overlap_accuracy == 1.0
    configuration, hidden_lifts = oracle_patch(3, 9.0)
    noisy = perturb(configuration, .005, 23)
    unit, lifted, window, thresholds, residual = infer_model(noisy)
    assert abs(unit - HIDDEN_UNIT) < 1e-12
    assert lifted == hidden_lifts
    assert window == 1.5
    assert thresholds == (0.75, 1.125)
    assert residual < .02
    print("icosahedral model-set growth: all assertions passed", result)


if __name__ == "__main__":
    main()
