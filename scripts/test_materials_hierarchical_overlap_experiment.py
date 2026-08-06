#!/usr/bin/env python3

from materials_hierarchical_overlap_experiment import evaluate


def main() -> None:
    result = evaluate()

    crystal = result.crystal
    assert crystal.atoms >= 200
    assert crystal.rotation_invariant
    assert crystal.level1_recurring_types > 0
    assert crystal.level2_recurring_types > 0
    assert crystal.exact_control_occurrences < crystal.exact_control_greedy_occurrences
    assert crystal.exact_control_expanded_nodes > 1

    cover = result.non_lattice_cover
    assert cover.atoms >= 200
    assert cover.nearest_support_seed_occurrences < cover.planted_occurrences
    assert cover.enumerated_occurrences == cover.planted_occurrences
    assert cover.occurrence_precision == 1.0
    assert cover.occurrence_recall == 1.0
    assert cover.cover_complete
    assert cover.overlap_required
    assert cover.overlap_excess_memberships > 0
    assert cover.multiply_covered_atoms > 0
    assert cover.level2_recurring_types == 0

    amorphous = result.amorphous_null
    assert amorphous.atoms >= 200
    assert amorphous.singleton_types == amorphous.atoms
    assert amorphous.recurring_types == 0
    assert amorphous.recurring_occurrences == 0

    print("hierarchical overlapping-cover experiment: all assertions passed")
    print(result)


if __name__ == "__main__":
    main()
