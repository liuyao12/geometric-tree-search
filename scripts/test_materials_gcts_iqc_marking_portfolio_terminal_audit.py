#!/usr/bin/env python3

from materials_gcts_iqc_marking_portfolio_terminal_audit import evaluate


def test_real_iqc_marking_portfolio_terminal_value_improves_but_stays_red():
    report = evaluate()
    assert report.groups == 20
    assert report.folds == 5
    assert report.terminal_training_examples == 1006
    assert report.selected_representations == (
        "ports", "base", "base", "base", "base")
    assert report.selected_neighbors == (3, 9, 5, 1, 9)
    assert (report.single_coupled_selected_exact,
            report.single_coupled_terminal_supply) == (15, 16)
    assert (report.portfolio_selected_exact,
            report.portfolio_terminal_supply) == (13, 18)
    assert report.portfolio_selected_correct_moves == 51
    assert report.terminal_value_selected_exact == 16
    assert report.terminal_value_stable_selected_exact == 16
    assert report.terminal_value_terminal_supply == 18
    assert report.terminal_value_selected_correct_moves == 54
    assert report.terminal_value_mixed_top_ties == 0
    assert report.terminal_value_gain_over_portfolio == 3
    assert report.terminal_value_gain_over_single_coupled == 1
    assert report.exact_path_supply_failures == 2
    assert report.supplied_but_misranked == 2
    assert report.ridge_broad_selected_exact == 12
    assert report.ridge_merged_selected_exact == 10
    assert report.ridge_control_rejected
    assert report.common_beam_budget_preserved
    assert not report.scientific_gate_passed
    assert not report.fresh_confirmation_authorized
    assert report.terminal_corpus_digest == \
        "9625d469f8d6b1e6956cf56690aeb919fe6b465a28374b7f2d61e2067e11ed81"
    assert report.portfolio_trace_digest == \
        "56b41e6a3d25223d844260c6c1a011d688f585794be064eb55d9e078bad8c47f"
    assert report.terminal_value_trace_digest == \
        "3eb94332bd850eff19b1612ca3d833b15bdcd7044240a5226381731495afee37"
    assert not report.target_used


if __name__ == "__main__":
    test_real_iqc_marking_portfolio_terminal_value_improves_but_stays_red()
    print("IQC marking portfolio terminal audit passed")
