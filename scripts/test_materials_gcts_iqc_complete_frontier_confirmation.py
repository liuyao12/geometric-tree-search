#!/usr/bin/env python3

from materials_gcts_iqc_complete_frontier_confirmation import _score_terminals
from materials_gcts_iqc_incidence_token_preflight import _key


def test_pure_posthoc_scorer_separates_supply_portfolio_and_top_one():
    terminals = (
        (((0., 0., 0.), "X"), ((1., 0., 0.), "Y")),
        (((0., 0., 0.), "X"), ((2., 0., 0.), "Z")),
        (((1., 0., 0.), "Y"), ((2., 0., 0.), "Z")),
    )
    truth = {
        _key((0., 0., 0.)): "X", _key((1., 0., 0.)): "Y",
        _key((2., 0., 0.)): "Q"}
    score = _score_terminals(terminals, (1, 0, 2), (2, 0, 1), (1, 0), truth)
    assert score["exact"] == (True, False, False)
    assert score["scalar_first_exact_rank"] == 2
    assert score["fusion_first_exact_rank"] == 2
    assert not score["scalar_top_one_exact"]
    assert not score["fusion_top_one_exact"]
    assert score["portfolio_supply"]


if __name__ == "__main__":
    test_pure_posthoc_scorer_separates_supply_portfolio_and_top_one()
    print("complete-frontier confirmation scorer tests passed")
