#!/usr/bin/env python3

from materials_gcts_2d_moire import evaluate


def main() -> None:
    aligned, commensurate, quasiperiodic = evaluate()
    for case in (aligned, commensurate, quasiperiodic):
        assert 500 <= case.seed_atoms <= 1000
        assert 1.96 < case.inferred_intrinsic_dimension < 2.04
        assert case.chemical_species == 2
        assert case.learned_sheets == 2
        assert case.learned_cluster_isometry_classes == 1
        assert case.learned_cluster_pose_states == 2
        assert case.seed_cover_fraction == 1.0
        assert case.heldout_position_precision == 1.0
        assert case.heldout_position_recall == 1.0
        assert case.heldout_chemical_accuracy == 1.0
        assert 3.9 < case.areal_growth_per_radius_doubling < 4.1
        assert case.projected_actions_to_million <= 6
        assert not case.heldout_positions_used_for_learning
        assert not case.crystallographic_label_used_for_learning
        assert not case.physical_potential_used
    assert aligned.common_translation_rank == 2
    assert aligned.relative_pose_marking_degrees < 1e-6
    assert "aligned" in aligned.classification
    assert commensurate.common_translation_rank == 2
    assert 21.7 < commensurate.relative_pose_marking_degrees < 21.9
    assert "commensurate" in commensurate.classification
    assert quasiperiodic.common_translation_rank == 0
    assert 29.9 < quasiperiodic.relative_pose_marking_degrees <= 30.0
    assert "quasiperiodic" in quasiperiodic.classification
    print("2D moire GCTS benchmark: passed")
    for case in (aligned, commensurate, quasiperiodic):
        print(case)


if __name__ == "__main__":
    main()
