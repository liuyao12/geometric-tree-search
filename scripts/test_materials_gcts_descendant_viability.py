#!/usr/bin/env python3

from materials_gcts_descendant_viability import (
    FrozenViabilityNode, label_descendant_viability)


def node(key, parent, value):
    return FrozenViabilityNode(
        "patch-a", key, parent, (float(value),), ("X",))


def test_only_actual_ancestors_of_successful_terminals_are_viable():
    stages = (
        (node("a", None, 1), node("b", None, 2)),
        (node("ac", "a", 3), node("bd", "b", 4)),
        (node("ace", "ac", 5), node("bdf", "bd", 6)),
    )
    examples, audit = label_descendant_viability(stages, ("ace",))
    assert tuple(tuple(row.viable for row in level) for level in examples) == (
        (True, False), (True, False), (True, False))
    assert audit.nodes_by_stage == (2, 2, 2)
    assert audit.viable_by_stage == (1, 1, 1)
    assert audit.successful_terminals == 1
    assert audit.all_parent_edges_frozen
    assert not audit.target_used_during_tree_construction


def test_unfrozen_parent_edge_and_unknown_terminal_fail_closed():
    bad = ((node("a", None, 1),), (node("b", "missing", 2),))
    try:
        label_descendant_viability(bad, ("b",))
        raise AssertionError("unfrozen parent was accepted")
    except ValueError:
        pass
    good = ((node("a", None, 1),), (node("b", "a", 2),))
    try:
        label_descendant_viability(good, ("unknown",))
        raise AssertionError("unknown terminal was accepted")
    except ValueError:
        pass


if __name__ == "__main__":
    test_only_actual_ancestors_of_successful_terminals_are_viable()
    test_unfrozen_parent_edge_and_unknown_terminal_fail_closed()
    print("descendant viability passed")
