#!/usr/bin/env python3

from materials_gcts_simultaneous_port_cover import (
    FrozenPortCoverProblem, PortCoverAction, solve_simultaneous_port_cover)


def test_simultaneous_port_cover():
    # Every duty is marginally available, but the two required actions cannot
    # coexist.  The older stranded-role check would accept this branch.
    conflicting = FrozenPortCoverProblem(("A", "B"), (
        PortCoverAction("a", ("A",), frozenset(("b",))),
        PortCoverAction("b", ("B",), frozenset(("a",))),
    ), True)
    red = solve_simultaneous_port_cover(conflicting)
    assert red.status == "unsatisfied"
    assert red.rejectable_as_inconsistent
    assert red.uncovered_obligations == ("A", "B")

    compatible = FrozenPortCoverProblem(("A", "B"), (
        PortCoverAction("a", ("A",), marking_score=.2),
        PortCoverAction("b", ("B",), marking_score=.3),
    ), True)
    green = solve_simultaneous_port_cover(compatible)
    assert green.status == "satisfied"
    assert green.selected_ids == ("a", "b")
    assert green.covered_obligations == ("A", "B")
    assert not green.rejectable_as_inconsistent

    joint = FrozenPortCoverProblem(("A", "B"), (
        PortCoverAction("split-a", ("A",), marking_score=99.),
        PortCoverAction("split-b", ("B",), marking_score=99.),
        PortCoverAction("joint", ("B", "A"), marking_score=0.),
    ), True)
    compact = solve_simultaneous_port_cover(joint)
    assert compact.selected_ids == ("joint",)

    # An incomplete shortlist cannot manufacture an impossibility proof.
    incomplete = solve_simultaneous_port_cover(FrozenPortCoverProblem(
        ("A", "B"), conflicting.actions, False))
    assert incomplete.status == "unknown"
    assert not incomplete.rejectable_as_inconsistent

    capped = solve_simultaneous_port_cover(compatible,
                                           maximum_search_nodes=1)
    assert capped.status == "unknown"
    assert not capped.search_complete

    # Serialization and selection are invariant to candidate input order and
    # one-sided conflict declaration.
    reversed_problem = FrozenPortCoverProblem(("B", "A"), tuple(reversed((
        PortCoverAction("a", ("A",), frozenset(("b",))),
        PortCoverAction("b", ("B",)),
    ))), True)
    reversed_result = solve_simultaneous_port_cover(reversed_problem)
    assert reversed_result.status == "unsatisfied"
    assert reversed_result.candidate_digest == red.candidate_digest
    assert reversed_result.certificate_digest == red.certificate_digest

    empty = solve_simultaneous_port_cover(FrozenPortCoverProblem(
        (), (), True))
    assert empty.status == "satisfied" and empty.selected_ids == ()


if __name__ == "__main__":
    test_simultaneous_port_cover()
    print("simultaneous port-cover tests passed")
