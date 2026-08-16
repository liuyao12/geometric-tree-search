#!/usr/bin/env python3
"""Regression for sealed autonomous Cd--Yb frontier continuation."""

from materials_gcts_cdyb_autonomous_frontier_benchmark import evaluate


def test_cdyb_autonomous_frontier():
    result = evaluate()
    assert result.train_windows == 2
    assert result.train_atoms == 969
    assert result.evaluation_seed_atoms == 59
    assert result.evaluation_target_atoms == 478
    assert result.evaluation_outer_atoms == 419
    assert result.train_eval_raw_ids_disjoint
    assert result.spatial_domains_disjoint
    assert result.learned_cluster_types == 175
    assert result.recognized_seed_occurrences == 6
    assert result.seed_cluster_covered_atoms == 49
    assert result.explicit_seed_gap_atoms == 10
    assert result.selected_threshold == 0.6
    assert result.selected_by_train_only_precision_then_reach
    assert result.selected.accepted_per_wave == (3, 18, 9, 35, 7)
    assert result.selected.emitted_atoms == 179
    assert result.selected.correct_atoms == 177
    assert result.selected.wrong_atoms == 2
    assert result.selected.precision > 0.988
    assert result.selected.outer_recall > 0.422
    assert result.unfiltered_diagnostic.outer_recall > 0.68
    assert result.unfiltered_diagnostic.precision < 0.79
    assert result.strict_consensus_diagnostic.precision == 1.0
    assert result.strict_consensus_diagnostic.outer_recall < 0.05
    assert len(result.execution_trace_digest) == 64
    assert result.promoted_action_macros > 0
    assert (result.exactly_certified_action_macros ==
            result.promoted_action_macros)
    assert sum(result.promoted_macro_child_counts) == 72
    assert result.recurring_three_wave_macro_signatures == 0
    assert not result.promoted_hierarchy_stationarity_claimed
    assert result.target_factory_called_after_all_executions
    assert not result.target_labels_used_for_compile_calibration_or_execution
    assert not result.family_source_sites_internal_coordinates_or_cell_used
    assert result.finite_autonomous_continuation_passed
    assert not result.stationary_or_exponential_growth_claimed


if __name__ == "__main__":
    test_cdyb_autonomous_frontier()
    print("CdYb autonomous frontier benchmark passed")
