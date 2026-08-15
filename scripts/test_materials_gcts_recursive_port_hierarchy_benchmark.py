#!/usr/bin/env python3

from materials_gcts_recursive_port_hierarchy_benchmark import evaluate


def test_cross_family_recursive_hierarchy_regression():
    cases = evaluate()
    assert tuple(case.system for case in cases) == (
        "NaCl-rocksalt", "Icosahedral-6D-model-set",
        "Cd5.7Yb-offcenter-seed")
    assert tuple(case.level_positive_macro_counts for case in cases) == (
        (3, 0), (75, 11, 0), (2, 0))
    assert tuple(case.level_total_mdl_savings for case in cases) == (
        (6, 0), (339, 31, 0), (4, 0))
    assert max(cases[1].level_atom_supports[1]) == 94
    assert all(case.termination_reason == "no_positive_mdl"
               for case in cases)
    assert all(case.converged_no_positive_mdl for case in cases)
    assert all(case.actual_promotion_available for case in cases)
    assert all(case.constants_and_labels_unused for case in cases)
    assert all(case.stationary_witnesses == 0 for case in cases)
    assert all(not case.real_stationary_semantics_certified for case in cases)


if __name__ == "__main__":
    test_cross_family_recursive_hierarchy_regression()
    print("recursive port hierarchy cross-family benchmark: passed")
