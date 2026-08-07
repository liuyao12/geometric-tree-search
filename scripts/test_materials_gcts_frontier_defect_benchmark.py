#!/usr/bin/env python3

from materials_gcts_frontier_defect_benchmark import evaluate


def test_frontier_defects_remain_local_during_parent_growth() -> None:
    result = evaluate()
    assert result.passed == result.total == 3
    assert result.output_parent_atoms == 65536
    assert result.recursive_actions == 2
    assert [case.input_atoms for case in result.cases] == [1023, 1024, 1025]
    assert [case.output_atoms for case in result.cases] == [65535, 65536, 65537]
    assert all(case.defect_instances_after_growth == 1 for case in result.cases)
    assert all(case.naive_parent_copy_instances == 64 for case in result.cases)
    assert all(case.exact_position_species_set for case in result.cases)
