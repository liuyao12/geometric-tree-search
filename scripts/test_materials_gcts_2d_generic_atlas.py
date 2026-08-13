#!/usr/bin/env python3

from materials_gcts_2d_generic_atlas import evaluate


def main() -> None:
    graphene, hbn, janus, strained = evaluate()
    assert graphene.species_count == 1
    assert hbn.species_count == 2
    assert janus.species_count == 3
    assert strained.species_count == 2
    assert graphene.learned_components == 1
    assert hbn.learned_components == 2
    assert janus.learned_components == 2
    assert strained.learned_components == 2
    assert graphene.learned_motif_atoms == (2,)
    assert hbn.learned_motif_atoms == (2, 2)
    assert janus.learned_motif_atoms == (3, 3)
    assert strained.learned_motif_atoms == (2, 2)
    assert graphene.motif_isometry_classes == 1
    assert hbn.motif_isometry_classes == 1
    assert janus.motif_isometry_classes == 1
    assert strained.motif_isometry_classes == 1
    for case in (graphene, hbn, janus, strained):
        assert 300 <= case.seed_atoms <= 1000
        assert case.arbitrary_global_rotation_applied
        assert case.seed_cover_fraction == 1.0
        assert 1.96 < case.inferred_intrinsic_dimension < 2.04
        assert case.heldout_position_precision == 1.0
        assert case.heldout_position_recall == 1.0
        assert case.heldout_chemical_accuracy == 1.0
        assert case.macro_pose_actions == case.learned_components
        assert case.atoms_per_macro_pose_action > 1000
        assert case.atomic_decisions_avoided == (
            case.new_atoms_generated - case.macro_pose_actions)
        assert not case.target_atoms_used_for_learning
        assert not case.generator_indices_used_for_learning
        assert not case.physical_potential_used
    assert graphene.pose_marking_ablation_recall == 1.0
    assert .49 < hbn.pose_marking_ablation_recall < .51
    assert .49 < janus.pose_marking_ablation_recall < .51
    assert hbn.marked_recall_gain > .49
    assert janus.marked_recall_gain > .49
    assert strained.marked_recall_gain > .49
    assert hbn.flat_seed_only_recall < .26
    assert janus.flat_seed_only_recall < .26
    assert strained.flat_seed_only_recall < .26
    print("generic 2D planar atlas: passed")
    for case in (graphene, hbn, janus, strained):
        print(case)


if __name__ == "__main__":
    main()
