#!/usr/bin/env python3

from materials_gcts_cdyb_missing_type_diagnostic import evaluate


def test_missing_cdyb_types_have_train_only_recurrence_diagnosis():
    result = evaluate()
    assert result.frozen_types == 80
    assert result.heldout_transferred_types == 53
    assert result.missing_types == 27
    assert result.transferred.types == 53
    assert result.missing.types == 27
    assert result.missing.train_patch_prevalence_histogram == ((2, 27),)
    assert result.missing_train_atoms_not_covered_by_transferred_types == 165
    assert result.missing_types_with_zero_unique_train_atoms == 7
    assert result.strict_majority_threshold == 3
    assert result.strict_majority_selected_ids == (75, 76)
    assert result.strict_majority_heldout_transferred_types == 2
    assert result.strict_majority_heldout_occurrences == 4
    assert result.strict_majority_minimum_namespaces == 1
    assert not result.strict_majority_every_type_transferred
    assert not result.leakage_safe_rule_succeeds
    assert (result.strict_majority_train_covered_atoms +
            result.strict_majority_train_residual_atoms == 2385)
    assert result.strict_majority_heldout_transferred_types <= \
        result.strict_majority_selected_types
    assert result.leakage_safe_rule_succeeds == (
        result.strict_majority_every_type_transferred and
        result.strict_majority_train_residual_atoms >= 0)


if __name__ == "__main__":
    test_missing_cdyb_types_have_train_only_recurrence_diagnosis()
    print("CdYb missing-type diagnostic: assertions passed")
