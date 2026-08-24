#!/usr/bin/env python3
"""Schema controls for commuting-closure marking."""

from types import SimpleNamespace
from unittest.mock import patch

from materials_gcts_iqc_commuting_closure_marking import (
    closure_representations, select_commuting_closure_marking)


def test_representations_are_finite_and_include_connection_sections():
    names = tuple(["depth"] + [f"feature-{index}" for index in range(30)] +
                  ["partial-min-fraction", "partial-connected-action-pairs"])
    rows = closure_representations(names)
    assert tuple(row.name for row in rows) == (
        "incidence", "action-local", "action-plus-incidence", "full")
    assert rows[0].feature_indices == (31, 32)
    assert rows[1].feature_indices == tuple(range(31))
    assert rows[-1].feature_indices == tuple(range(33))


def test_selector_ranks_only_the_frozen_closure_subset():
    def state(value):
        return SimpleNamespace(actions=(((float(value), 0., 0.), "X"),))

    states = tuple(state(value) for value in range(4))
    candidates = tuple(SimpleNamespace(tie_key=f"candidate-{value}")
                       for value in range(4))
    frontier = SimpleNamespace(
        states=states, candidates=candidates, target_used=False,
        closure=SimpleNamespace(
            states=(states[1], states[3]), target_used=False))
    model = SimpleNamespace(target_used=False, model_digest="frozen-model")
    fitted = SimpleNamespace(fused_scores=(.1, .9))
    with patch(
            "materials_gcts_iqc_commuting_closure_marking."
            "select_equivariant_port_fusion", return_value=fitted):
        selected = select_commuting_closure_marking(
            model, frontier, width=1)
    assert selected.candidate_indices == (1, 3)
    assert selected.ranked_candidate_indices == (3, 1)
    assert selected.selected_indices == (3,)
    assert selected.model_digest == "frozen-model"
    assert selected.candidate_geometry_unchanged
    assert not selected.target_used


if __name__ == "__main__":
    test_representations_are_finite_and_include_connection_sections()
    test_selector_ranks_only_the_frozen_closure_subset()
    print("IQC commuting closure marking tests passed")
