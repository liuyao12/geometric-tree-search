#!/usr/bin/env python3

from materials_gcts_bounded_port_marking_benchmark import evaluate


def main() -> None:
    cases = evaluate(shuffled_runs=5)
    assert len(cases) == 3
    for case in cases:
        assert case.training_examples > 0
        assert case.target_examples > 0
        assert case.abstract_action_states <= case.raw_port_classes
        assert case.exact_marking_states <= 32
        assert case.backoff_states <= 64
        assert case.minimum_state_support == 32
        assert 0 <= case.exact_context_coverage <= case.backoff_context_coverage <= 1
        assert case.marked_mean_checks > 0
        assert case.unmarked_mean_checks > 0
        assert case.shuffled_mean_checks > 0
        assert case.identical_candidate_actions
        assert case.marking_state_selection_train_only
        assert case.shuffled_runs == 5
        assert 0 < case.empirical_shuffle_p_value <= 1
        assert case.material_labels_global_frame_target_tuning_unused
    print("bounded local port marking ablation: passed", cases)


if __name__ == "__main__":
    main()
