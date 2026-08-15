#!/usr/bin/env python3

from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_stationary_hierarchy_audit import (
    _has_strong_stationary_recurrence, audit_stationary_hierarchy)


def main() -> None:
    # Pairwise A at 0/1 and B at 1/2 is not one stationary recurrence.
    assert not _has_strong_stationary_recurrence(
        ({"A": ()}, {"A": (), "B": ()}, {"B": ()}),
        (True, True, True))
    cloud, _ = oracle_patch(3, 9.0)
    program = compile_irregular_port_program(cloud.species, cloud.positions)
    result = audit_stationary_hierarchy(program)
    assert result.termination_reason == "no_positive_mdl"
    assert result.exact_occurrence_expansion_helped
    assert len(result.levels) >= 3
    assert result.levels[0].promotion_occurrences > (
        result.levels[0].evidence_occurrences)
    assert result.levels[-1].positive_mdl_macros == 0
    assert not result.three_consecutive_positive_levels
    assert not result.strong_stationary_recurrence
    assert result.target_family_cell_expected_scale_unused
    print("strong stationary hierarchy audit: passed", result)


if __name__ == "__main__":
    main()
