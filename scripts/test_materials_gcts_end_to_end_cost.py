#!/usr/bin/env python3

from materials_gcts_end_to_end_cost import evaluate


def main() -> None:
    result = evaluate()
    assert result.benchmark_passed
    assert result.all_two_level_outputs_exact
    assert result.all_reach_million_with_six_actions
    assert result.all_action_compressions_above_ten_thousand
    assert result.finite_graph_counts_exact
    assert result.iqc_fast_count_is_estimate
    assert result.iqc_fast_count_error_below_one_percent
    assert result.exact_iqc_counting_is_linear_enumeration
    assert result.no_md_speed_claim
    assert result.cases[1].fast_count_relative_error < .001
    print("end-to-end recursive GCTS cost benchmark: passed")


if __name__ == "__main__":
    main()
