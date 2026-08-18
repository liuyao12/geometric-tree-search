#!/usr/bin/env python3
"""Regression for the train-only recurrent IQC cluster quotient."""

from materials_gcts_iqc_recurrent_prototype_connection_audit import evaluate


def main():
    report = evaluate()
    assert report.training_groups == 10
    assert report.validation_groups == 8
    assert report.selected_prototype_minimum_groups == 2
    assert report.selected_groups_with_correct_candidates == 8
    assert report.selected_groups_with_exact_path == 8
    assert report.supply_gate_passed
    assert report.cluster_vocabulary_fit_on_training_seeds_only
    assert report.connection_fit_uses_training_targets_only
    assert report.validation_targets_used_only_for_supply_scoring
    assert not report.next_confirmation_seed_or_target_accessed
    selected = next(row for row in report.audits
                    if row.prototype_minimum_groups == 2)
    assert selected.recurrent_prototypes == 455
    assert selected.exact_path_available_by_validation_group == (
        True, True, True, True, True, True, True, True)
    print("IQC recurrent prototype connection audit passed")


if __name__ == "__main__":
    main()
