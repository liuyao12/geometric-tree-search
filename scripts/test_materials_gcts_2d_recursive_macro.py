#!/usr/bin/env python3

from materials_gcts_2d_recursive_macro import evaluate


def main() -> None:
    result = evaluate()
    assert result.seed_atoms == 746
    assert result.heldout_atoms == 2990
    assert result.motif_atoms_per_pose == 2
    assert result.pose_states == 2
    assert result.child_references_per_macro == 4
    assert result.learned_address_dimensions == 2
    assert result.explicit_position_precision == 1.0
    assert result.explicit_position_recall == 1.0
    assert result.explicit_chemical_accuracy == 1.0
    assert result.explicit_atoms_emitted == result.heldout_atoms
    assert result.implicit_level == 9
    assert result.implicit_represented_atoms == 1_048_576
    assert result.seed_equivalent_level == 4
    assert result.promoted_actions_seed_to_million == 5
    assert result.flat_motif_actions_to_million > 499_000
    assert result.recursive_action_reduction > 99_000
    assert result.pose_marking_ablation_recall == .5
    assert result.hierarchy_definitions == 10
    assert result.explicit_output_is_linear
    assert not result.heldout_atoms_used_for_learning
    assert not result.generator_indices_used_for_learning
    assert not result.physical_potential_used
    print("2D recursive address macro: passed")
    print(result)


if __name__ == "__main__":
    main()
