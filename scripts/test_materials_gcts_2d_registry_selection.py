#!/usr/bin/env python3

from materials_gcts_2d_registry_selection import evaluate


def main() -> None:
    result = evaluate()
    aligned, commensurate, quasiperiodic = result.cases
    assert aligned.seed_atoms == 932
    assert commensurate.seed_atoms == 932
    assert quasiperiodic.seed_atoms == 932
    assert aligned.registry_states_by_window == (2, 2, 2)
    assert max(commensurate.registry_states_by_window) <= 16
    assert quasiperiodic.registry_states_by_window == (10, 33, 71)
    assert aligned.local_vocabulary_bounded
    assert commensurate.local_vocabulary_bounded
    assert not quasiperiodic.local_vocabulary_bounded
    assert aligned.seed_local_marking_heldout_coverage == 1.0
    assert commensurate.seed_local_marking_heldout_coverage > .99
    assert commensurate.pose_fallback_fraction < .01
    assert .29 < quasiperiodic.seed_local_marking_heldout_coverage < .32
    assert quasiperiodic.vocabulary_growth_exponent > .85
    assert quasiperiodic.heldout_registry_states > 200
    assert quasiperiodic.selected_marking_states == 2
    assert quasiperiodic.pose_fallback_fraction == 1.0
    assert "relative-pose macro" in quasiperiodic.selected_representation
    for case in result.cases:
        assert case.selected_position_precision == 1.0
        assert case.selected_position_recall == 1.0
        assert case.selected_chemical_accuracy == 1.0
        assert case.pose_macro_recall_if_used == 1.0
        assert case.representation_selected_without_family_label
        assert not case.heldout_atoms_used_for_selection
        assert not case.physical_potential_used
    assert result.commensurate_local_marking_selected
    assert result.quasiperiodic_pose_macro_selected
    assert result.growing_local_vocabulary_rejected
    assert result.all_selected_growth_exact
    print("2D registry model selection: passed")
    print(result)


if __name__ == "__main__":
    main()
