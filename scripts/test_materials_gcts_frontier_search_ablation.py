#!/usr/bin/env python3

from materials_gcts_frontier_search_ablation import evaluate


def test_incoming_marking_beats_matched_frontier_controls() -> None:
    result = evaluate(30)
    assert result.matched_correct_sites == 120
    assert result.marked.proposal_checks == 120
    assert result.marked.failed_branches == 0
    assert result.overlap_vote_baseline.proposal_checks == 232
    assert result.overlap_vote_baseline.failed_branches == 112
    assert result.shuffled_runs == 30
    assert result.shuffled_best_checks > result.marked.proposal_checks
    assert result.marked_vs_overlap_reduction > 1.9
    assert result.marked_vs_shuffle_median_reduction > 30
    assert result.marking_beats_every_shuffle
    assert not result.heldout_labels_used_for_training
    assert result.candidate_set_identical
    assert result.benchmark_passed


if __name__ == "__main__":
    test_incoming_marking_beats_matched_frontier_controls()
    print("matched-quality live-frontier GCTS ablation: all assertions passed")
