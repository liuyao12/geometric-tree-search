#!/usr/bin/env python3

from materials_gcts_matched_search_ablation import evaluate


def main() -> None:
    result = evaluate()
    assert result.benchmark_passed
    assert result.all_matched_quality
    assert result.all_markings_reduce_proposals
    assert result.all_markings_reduce_backtracks
    assert result.heldout_labels_excluded_from_training
    crystal, iqc, substitution = result.structural_sections
    assert crystal.marked_proposals == 1
    assert iqc.marked_proposals == 8603
    assert substitution.marked_proposals == 6
    learned = result.learned_local_section
    assert learned.target_accepted_actions == 252
    assert learned.marked_proposals == 392
    assert learned.marked_backtracks == 140
    assert learned.unmarked_expected_proposals == 526
    assert learned.unmarked_expected_backtracks == 274
    assert learned.backtrack_reduction is not None
    assert learned.backtrack_reduction > 1.95
    print("matched-quality GCTS search ablation: passed")


if __name__ == "__main__":
    main()
