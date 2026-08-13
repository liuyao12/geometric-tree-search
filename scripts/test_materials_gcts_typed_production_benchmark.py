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
    crystal, quasicrystal = result.cases
    assert crystal.recursive_types == 1
    assert crystal.child_references == 8
    assert crystal.typed_counts == (216, 1728, 13824)
    assert quasicrystal.recursive_types == 8
    assert quasicrystal.child_references == 27
    assert quasicrystal.typed_counts == (729, 3375, 13824)
    print("typed production benchmark: passed")


if __name__ == "__main__":
    main()
