#!/usr/bin/env python3

from materials_gcts_portfolio_terminal_value import (
    PortfolioTerminalCandidate, PortfolioTerminalExample, TerminalRepresentation,
    fit_grouped_portfolio_terminal_value, select_portfolio_terminal)


def test_grouped_terminal_value_selects_representation_without_target():
    rows = []
    for group in range(6):
        rows.extend((
            PortfolioTerminalExample(group, (-1., 0.), ("X",), True),
            PortfolioTerminalExample(group, (1., 0.), ("Y",), False),
        ))
    model, audit = fit_grouped_portfolio_terminal_value(
        rows, feature_names=("signal", "noise"), color_keys=("X", "Y"),
        representations=(TerminalRepresentation("signal", (0,)),
                         TerminalRepresentation("noise", (1,))),
        candidate_neighbors=(1, 3))
    assert audit.selected_representation == "signal"
    assert audit.selected_exact_groups == 6
    assert audit.supplied_groups == 6
    assert not audit.target_used
    selected = select_portfolio_terminal(model, tuple(
        PortfolioTerminalCandidate(row, index)
        for index, row in enumerate(rows[:2])))
    assert selected.certified_exact
    assert not selected.mixed_top_tie


def test_mixed_top_tie_fails_closed():
    rows = []
    for group in range(5):
        rows.extend((
            PortfolioTerminalExample(group, (0.,), ("X",), True),
            PortfolioTerminalExample(group, (0.,), ("X",), False),
        ))
    model, audit = fit_grouped_portfolio_terminal_value(
        rows, feature_names=("alias",), color_keys=("X",),
        representations=(TerminalRepresentation("same", (0,)),),
        candidate_neighbors=(1,))
    assert audit.selected_exact_groups == 0
    selected = select_portfolio_terminal(model, tuple(
        PortfolioTerminalCandidate(row, index)
        for index, row in enumerate(rows[:2])))
    assert not selected.certified_exact
    assert selected.mixed_top_tie


if __name__ == "__main__":
    test_grouped_terminal_value_selects_representation_without_target()
    test_mixed_top_tie_fails_closed()
    print("portfolio terminal value passed")
