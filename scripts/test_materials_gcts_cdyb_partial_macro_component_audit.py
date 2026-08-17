#!/usr/bin/env python3

from materials_gcts_cdyb_partial_macro_component_audit import evaluate


def test_train_only_atomic_peel_is_complete_but_not_better():
    result = evaluate()
    assert result.training_windows == 5
    assert result.whole_macro_candidates == 14
    assert result.whole_macro_exact == 8
    assert result.whole_macro_mixed == 6
    assert result.whole_emitted_sites == 148
    assert result.whole_correct_sites == 110
    assert result.attached_components == 14
    assert result.attached_components_exact == 8
    assert result.attached_components_mixed == 6
    assert result.atomic_frontier_components == 14
    assert result.atomic_frontier_components_exact == 8
    assert result.atomic_frontier_components_mixed == 6
    assert result.atomic_frontier_emitted_sites == 90
    assert result.atomic_frontier_correct_sites == 62
    assert result.atomic_residual_subclusters == 10
    assert result.every_atomic_candidate_complete_cover
    assert result.every_candidate_complete_cover
    assert result.every_novel_union_preserved
    assert result.represented_novel_sites == result.original_novel_sites == 148
    assert result.target_used_only_for_training_scoring
    assert not result.evaluation_or_confirmatory_target_opened
    assert 62 / 90 < 110 / 148


if __name__ == "__main__":
    test_train_only_atomic_peel_is_complete_but_not_better()
    print("CdYb partial macro component audit: passed")
