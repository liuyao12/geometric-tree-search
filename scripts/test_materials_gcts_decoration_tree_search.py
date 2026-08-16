#!/usr/bin/env python3
"""Focused invariants for target-blind optional-decoration search."""

import inspect

from materials_gcts_decoration_tree_search import (
    DecorationAction, DecorationSearchPolicy, FrozenDecorationMarking,
    FrozenDecorationProblem, search_decoration_cover)


def test_search_branches_and_keeps_candidate_set_fixed():
    actions = (
        DecorationAction(0, 0, 0, 0, ((0, "A"), (1, "A")), 8),
        DecorationAction(1, 0, 0, 1, ((0, "A"), (1, "B")), 2),
        DecorationAction(2, 1, 0, 0, ((1, "A"), (2, "A")), 8),
        DecorationAction(3, 1, 0, 1, ((1, "B"), (2, "B")), 2),
    )
    problem = FrozenDecorationProblem(3, actions, (), "a" * 64)
    marking = FrozenDecorationMarking(
        ((0, ((0, 8), (1, 2))),), (), (), 2, 2)
    modal = search_decoration_cover(
        problem, {0: "A"}, marking,
        DecorationSearchPolicy("modal", beam_width=2, maximum_depth=3,
                               maximum_branches_per_state=2))
    gcts = search_decoration_cover(
        problem, {0: "A"}, marking,
        DecorationSearchPolicy("gcts", beam_width=2, maximum_depth=3,
                               maximum_branches_per_state=2))
    assert modal.candidate_digest == gcts.candidate_digest == "a" * 64
    assert "target" not in inspect.signature(search_decoration_cover).parameters
    assert dict(modal.labelled_species) == {0: "A", 1: "A", 2: "A"}
    assert not modal.target_used and not gcts.target_used
    assert modal.expanded_nodes > 0
    assert modal.conflict_rejections > 0


if __name__ == "__main__":
    test_search_branches_and_keeps_candidate_set_fixed()
    print("decoration tree-search invariants: assertions passed")
