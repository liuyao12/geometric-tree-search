#!/usr/bin/env python3
"""Regression for the minimal two-fallback full-width IQC gate."""

from materials_gcts_iqc_minimal_hybrid_fullwidth_benchmark import \
    load_default_result


def test_minimal_hybrid_keeps_exact_fallback_and_runtime_headroom():
    row = load_default_result()
    assert row["selected_prefixes"] == 10
    assert row["raw_nine_action_lineages"] == 1376
    assert row["raw_exact_nine_action_lineages"] == 6
    assert row["raw_fallback_exact_lineages"] == 3
    assert row["selected_exact_nine_action_lineages"] == 6
    assert row["exact_complete_twelve_action_paths"] == 42
    assert row["total_execution_seconds"] < 500.
    assert row["runtime_gate_passed"]
    assert not row["candidate_selection_target_used"]


if __name__ == "__main__":
    test_minimal_hybrid_keeps_exact_fallback_and_runtime_headroom()
    print("IQC minimal hybrid full-width tests passed")
