#!/usr/bin/env python3

from materials_gcts_typed_production_benchmark import evaluate


def main() -> None:
    result = evaluate()
    assert result.benchmark_passed
    assert result.same_recursive_executor
    assert not result.family_label_used
    assert result.amorphous_rejected
    assert not result.continuous_internal_section_compiled
    assert result.all_two_level_counts_exact
    assert result.all_rigid_motion_invariant
    crystal, quasicrystal, planar = result.cases
    assert crystal.recursive_types == 1
    assert crystal.child_references == 8
    assert crystal.typed_counts == (216, 1728, 13824)
    assert quasicrystal.recursive_types == 8
    assert quasicrystal.child_references == 27
    assert quasicrystal.typed_counts == (729, 3375, 13824)
    assert planar.recursive_types == 2
    assert planar.child_references == 8
    assert planar.typed_counts == (1024, 4096, 16384)
    assert planar.materialized_atom_counts == (746, 2954, 11696)
    assert planar.count_reference_kind == "recursive address envelope"
    print("typed production benchmark: passed")


if __name__ == "__main__":
    main()
