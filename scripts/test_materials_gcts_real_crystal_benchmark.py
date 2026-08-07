#!/usr/bin/env python3

from materials_gcts_real_crystal_benchmark import evaluate


def test_real_crystal_suite_grows_exactly_without_cells() -> None:
    result = evaluate()
    assert result.total == 6
    assert result.passed == result.total
    assert all(case.discovered_family == "translation_quotient"
               for case in result.cases)
    assert all(case.growth_factor == 8.0 for case in result.cases)
    assert all(case.exact_position_species_set for case in result.cases)
    complex_case = next(case for case in result.cases
                        if case.system == "Cd6Yb-1/1-approximant")
    assert complex_case.observed_cell_repeats == 2
    assert complex_case.observed_atoms == 1344
    assert complex_case.grown_atoms == 10752
