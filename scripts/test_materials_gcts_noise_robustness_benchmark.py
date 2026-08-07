#!/usr/bin/env python3

from materials_gcts_noise_robustness_benchmark import evaluate


def test_noise_robustness_and_amorphous_false_positive_gate() -> None:
    result = evaluate()
    families = tuple(case.discovered_family
                     for case in result.retained_at_half_percent)
    assert families == (
        "translation_quotient", "internal_section_inflation",
        "substitution_product")
    assert tuple(case.output_atoms for case in
                 result.retained_at_half_percent) == (1728, 1969, 3375)
    assert all(case.deterministic for case in
               result.retained_at_half_percent)
    assert all(not case.deterministic for case in
               result.rejected_at_one_percent)
    assert result.amorphous_false_positive_seeds == 4
    assert result.amorphous_false_positives == 0
