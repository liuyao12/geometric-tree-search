#!/usr/bin/env python3

from materials_gcts_2d_robustness import evaluate


def main() -> None:
    result = evaluate()
    assert result.clean_seed_atoms == 746
    assert 0.025 < result.missing_seed_fraction < 0.05
    assert result.coordinate_noise_sigma == .006
    assert result.learned_components == 2
    assert result.learned_motif_atoms == (2, 2)
    assert result.minimum_translation_support > .80
    assert result.registered_position_precision >= .98
    assert result.registered_position_recall >= .98
    assert result.registered_chemical_accuracy == 1.0
    assert result.registered_rms_error < .08
    assert .48 < result.pose_marking_ablation_recall < .52
    assert result.marking_recall_gain > .47
    assert not result.target_atoms_used_for_learning
    assert not result.physical_potential_used
    print("2D planar robustness: passed")
    print(result)


if __name__ == "__main__":
    main()
