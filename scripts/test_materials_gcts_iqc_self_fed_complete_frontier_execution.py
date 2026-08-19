#!/usr/bin/env python3

import inspect

from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    freeze_self_fed_candidates, normalize_actions)


def test_public_api_has_no_target_or_scorer():
    parameters = inspect.signature(freeze_self_fed_candidates).parameters
    assert set(parameters) == {
        "center", "seed_positions", "seed_species", "inherited_actions",
        "public_radius"}
    assert not ({"target", "truth", "oracle", "scorer"} & set(parameters))


def test_action_normalization_is_stable_and_colored():
    actions = normalize_actions((([1, 2, 3], "X"), ((4., 5., 6.), "Y")))
    assert actions == (((1., 2., 3.), "X"), ((4., 5., 6.), "Y"))


if __name__ == "__main__":
    test_public_api_has_no_target_or_scorer()
    test_action_normalization_is_stable_and_colored()
    print("self-fed complete-frontier execution tests passed")
