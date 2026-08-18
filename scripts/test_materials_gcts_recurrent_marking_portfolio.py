#!/usr/bin/env python3

from materials_gcts_recurrent_branch_value import RecurrentBranchExample, _fit
from materials_gcts_recurrent_marking_portfolio import (
    FrozenBranchMarking, MarkingPortfolioCandidate,
    select_marking_portfolio_beam)
from materials_gcts_recurrent_state_diverse_beam import RecurrentStateBeamSpec


def test_portfolio_shares_one_fixed_beam_across_markings():
    rows = tuple(RecurrentBranchExample(
        group, (float(signal), float(-signal)), ("X",), signal > 0)
        for group in range(4) for signal in (-2, -1, 1, 2))
    first = _fit(rows, ("left", "right"), ("X",), 1, .5)
    swapped_rows = tuple(RecurrentBranchExample(
        row.group, (row.features[1], row.features[0]), row.action_colors,
        not row.successful) for row in rows)
    second = _fit(swapped_rows, ("right", "left"), ("X",), 1, .5)
    library = (
        FrozenBranchMarking("left", (0, 1), first),
        FrozenBranchMarking("right", (1, 0), second),
    )
    candidates = tuple(MarkingPortfolioCandidate(
        (float(signal), float(-signal)), ("X",), signal)
        for signal in (-2, -1, 1, 2))
    selected = select_marking_portfolio_beam(
        library, candidates, RecurrentStateBeamSpec(1., 2, 2))
    assert len(selected) == 2
    assert len({row.tie_key for row in selected}) == 2
    assert {row.tie_key for row in selected} & {-2, -1}
    assert {row.tie_key for row in selected} & {1, 2}


if __name__ == "__main__":
    test_portfolio_shares_one_fixed_beam_across_markings()
    print("recurrent marking portfolio passed")
