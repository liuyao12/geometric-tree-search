#!/usr/bin/env python3

from materials_gcts_ideal_iqc_iterated_marking import evaluate


def test_frozen_marking_reuses_actions_across_iqc_inflations() -> None:
    result = evaluate()
    assert result.atom_counts == (507, 1969, 8603)
    assert result.training_valid_actions == 222
    assert result.heldout_valid_actions == 944
    assert result.valid_action_growth_factor > 4.2
    assert result.unmarked_candidates == 1968
    assert result.histogram_matches == 612
    assert result.histogram_precision > result.unmarked_precision
    assert result.histogram_recall > .64
    assert result.captured_action_growth_factor > 2.75
    assert result.conjunctive_matches == 252
    assert result.conjunctive_precision > .64
    assert result.conjunctive_false_branch_reduction > 7.3
    assert not result.training_uses_second_transition_labels
    assert not result.full_patch_generator_claimed


if __name__ == "__main__":
    test_frozen_marking_reuses_actions_across_iqc_inflations()
    print("iterated ideal-IQC GCTS marking: all assertions passed")
