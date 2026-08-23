"""Regression for the consumed-nuclei fourth-block action marking."""

from materials_gcts_iqc_fourth_block_action_marking import \
    load_default_artifact


def test_fourth_block_action_marking_is_frozen_before_confirmation():
    artifact = load_default_artifact()
    assert artifact.development_groups == (0, 1)
    assert artifact.exact_parents_by_group == (1, 3)
    assert artifact.causal_stages == 12
    assert artifact.training_candidates == 10_721
    assert artifact.training_positive_actions == 1_044
    assert artifact.original_first_correct_ranks == (
        7, 9, 9, 11, 11, 14, 1, 14, 15, 1, 12, 12)
    assert artifact.fitted_first_correct_ranks == (1,) * 12
    assert artifact.targets_used_for_training
    assert not artifact.confirmation_target_used
    assert not artifact.raw_ids_or_absolute_coordinates_in_model
    assert not artifact.candidate_geometry_changed


if __name__ == "__main__":
    test_fourth_block_action_marking_is_frozen_before_confirmation()
    print("fourth-block action marking: passed")
