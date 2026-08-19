#!/usr/bin/env python3
"""Tests for candidate-preserving bounded marking portfolios."""

from materials_gcts_bounded_marking_portfolio import (
    MarkingOrder, bounded_marking_portfolio)


def test_portfolio_retains_each_marking_head_without_changing_candidates():
    first = MarkingOrder("topology", ("a", "b", "c"))
    second = MarkingOrder("yield", ("c", "b", "a"))
    row = bounded_marking_portfolio((first, second), candidates_per_marking=1)
    assert row.retained_candidate_ids == ("a", "c")
    assert row.retained_by_marking == (("topology", ("a",)),
                                       ("yield", ("c",)))
    reversed_candidates = bounded_marking_portfolio((
        MarkingOrder("topology", ("c", "b", "a")),
        MarkingOrder("yield", ("a", "b", "c"))),
        candidates_per_marking=1)
    assert reversed_candidates.candidate_universe_digest == \
        row.candidate_universe_digest
    try:
        bounded_marking_portfolio((
            first, MarkingOrder("wrong", ("a", "b", "d"))))
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched candidate universe was accepted")
    try:
        bounded_marking_portfolio((
            first, MarkingOrder("tainted", ("a", "b", "c"), True)))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted marking order was accepted")


if __name__ == "__main__":
    test_portfolio_retains_each_marking_head_without_changing_candidates()
    print("bounded marking portfolio tests passed")
