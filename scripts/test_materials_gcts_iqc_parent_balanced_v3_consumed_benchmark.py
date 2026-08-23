"""Pre-run contract for the v3 consumed-nucleus audit."""

import inspect

import materials_gcts_iqc_parent_balanced_v3_consumed_benchmark as benchmark


def test_consumed_benchmark_freezes_raw_receipt_before_target():
    source = inspect.getsource(benchmark.evaluate)
    assert source.index("frozen_bytes = canonical_json(receipt)") < \
        source.index("oracle_crop_fast(CONSUMED_CENTER, FOURTH_RADIUS)")
    assert "serialized_receipt_digest" in source
    assert "deterministic_receipt_digest" in source
    assert "frozen_digest != execution.deterministic_receipt_digest" not in source
    assert benchmark.RUNTIME_LIMIT_SECONDS == 600.
    assert len(benchmark.EXPECTED_FIXTURE_SHA256) == 64
    assert len(benchmark.EXPECTED_RESULT_DIGEST) == 64


def test_consumed_benchmark_fixture_preserves_raw_supply_and_runtime_failure():
    row = benchmark.load_default_result()
    assert row["raw_nine_action_lineages"] == 1102
    assert row["raw_exact_nine_action_lineages"] == 3
    assert row["raw_exact_parent_count"] == 1
    assert row["selected_nine_action_lineages"] == 64
    assert row["selected_exact_nine_action_lineages"] == 3
    assert row["selected_exact_parent_count"] == 1
    assert row["all_raw_exact_parents_retained"] is True
    assert row["fourth_candidates"] == 512
    assert row["exact_fourth_candidates"] == 21
    assert row["exact_terminal_blocks"] == 476
    assert row["best_complete_correct_actions"] == 12
    assert row["total_execution_seconds"] == 2179.182173125
    assert row["runtime_gate_passed"] is False
    timings = dict(row["stage_seconds"])
    assert timings["chunked_fourth_frontiers"] == 1373.8056081250002
    assert timings["chunked_fourth_frontiers"] > .6 * \
        row["total_execution_seconds"]


if __name__ == "__main__":
    test_consumed_benchmark_freezes_raw_receipt_before_target()
    test_consumed_benchmark_fixture_preserves_raw_supply_and_runtime_failure()
    print("v3 consumed benchmark contract: passed")
