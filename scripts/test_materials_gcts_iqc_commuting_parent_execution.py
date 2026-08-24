#!/usr/bin/env python3
"""Controls for target-free commuting-parent execution."""

from types import SimpleNamespace
from unittest.mock import patch

from materials_gcts_iqc_commuting_parent_execution import \
    freeze_commuting_second_frontier


def test_selected_closure_parents_reach_second_frontier_unchanged() -> None:
    def state(index):
        actions = (((float(index), 0., 0.), "X"),)
        return SimpleNamespace(
            positions=((0., 0., 0.), (float(index), 0., 0.)),
            species=("X", "X"), actions=actions)

    states = tuple(state(index) for index in range(3))
    frontier = SimpleNamespace(
        states=states, candidates=(object(), object(), object()),
        target_used=False, closure=SimpleNamespace(target_used=False))
    selection = SimpleNamespace(
        selected_indices=(2, 0), candidate_digest="closure-candidates")
    runtime = {"fusion_model": SimpleNamespace(
        feature_names=("feature",), color_keys=("X",))}
    model = SimpleNamespace(
        target_used=False, feature_names=("feature",), color_keys=("X",),
        model_digest="marking-model")

    def second_worker(task):
        return SimpleNamespace(
            first_rank=task[1], first_actions=task[5], target_used=False)

    with patch(
            "materials_gcts_iqc_commuting_parent_execution."
            "load_default_runtime", return_value=runtime), patch(
            "materials_gcts_iqc_commuting_parent_execution."
            "complete_first_frontier_with_commuting_closure",
            return_value=frontier), patch(
            "materials_gcts_iqc_commuting_parent_execution."
            "select_commuting_closure_marking", return_value=selection), patch(
            "materials_gcts_iqc_commuting_parent_execution._second_worker",
            side_effect=second_worker):
        result = freeze_commuting_second_frontier(
            center=(0., 0., 0.), seed_positions=((0., 0., 0.),),
            seed_species=("X",), first_radius=1., second_radius=2.,
            marking_model=model, workers=1, parent_width=2)
    assert result.selected_first_indices == (2, 0)
    assert result.selected_first_actions == (
        states[2].actions, states[0].actions)
    assert tuple(row.first_actions for row in result.second_branches) == \
        result.selected_first_actions
    assert result.marking_model_digest == "marking-model"
    assert result.candidate_geometry_unchanged
    assert not result.target_used


if __name__ == "__main__":
    test_selected_closure_parents_reach_second_frontier_unchanged()
    print("IQC commuting parent execution tests passed")
