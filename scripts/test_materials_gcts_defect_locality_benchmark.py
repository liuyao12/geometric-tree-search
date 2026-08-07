#!/usr/bin/env python3

from materials_gcts_defect_locality_benchmark import evaluate


def test_consensus_quotient_does_not_replicate_local_defects() -> None:
    result = evaluate()
    assert result.total == 3
    assert result.passed == result.total
    assert all(case.discovered_family == "translation_quotient"
               for case in result.cases)
    assert all(case.consensus_motif_atoms == 8 for case in result.cases)
    assert all(case.exact_position_species_set for case in result.cases)
    assert [case.grown_atoms for case in result.cases] == [1727, 1728, 1729]
    assert all(case.defect_copies <= 1 for case in result.cases)
