#!/usr/bin/env python3
from types import SimpleNamespace
from materials_gcts_iqc_frontier_beam_audit import audit


def test_frozen_real_wave17_numbers_select_exact_sibling_without_truth():
    rows = (
        SimpleNamespace(rank=1, score=.9997443893166221,
                        lookahead_maximum_score=.9997196564773163,
                        true_sites=0, false_sites=60),
        SimpleNamespace(rank=2, score=.9995566664221786,
                        lookahead_maximum_score=.9997950674961632,
                        true_sites=48, false_sites=0),
    )
    result = audit(SimpleNamespace(regenerative_wave17_score_bands=rows))
    assert result.selected_rank == 2
    assert (result.selected_true_sites, result.selected_false_sites) == (48, 0)
    assert (result.greedy_true_sites, result.greedy_false_sites) == (0, 60)
    assert result.greedy_rollback == 1
    assert not result.selection_uses_truth and not result.target_used
    assert result.exploratory_same_trace
    assert not result.confirmatory_gate_passed


if __name__ == "__main__":
    test_frozen_real_wave17_numbers_select_exact_sibling_without_truth()
    print("IQC frontier beam audit tests: passed")
