#!/usr/bin/env python3

from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_self_fed_frontier_confirmation import (
    score_frozen_terminals)


def test_posthoc_scorer_separates_supply_portfolio_and_autonomous_top_one():
    terminals = (
        (((0., 0., 0.), "X"), ((1., 0., 0.), "Y")),
        (((0., 0., 0.), "X"), ((2., 0., 0.), "Z")),
        (((1., 0., 0.), "Y"), ((2., 0., 0.), "Z")),
    )
    truth = {
        _key((0., 0., 0.)): "X", _key((1., 0., 0.)): "Y",
        _key((2., 0., 0.)): "Q"}
    score = score_frozen_terminals(
        terminals, (1, 0, 2), (2, 0, 1), (1, 0), truth)
    assert score["exact"] == (True, False, False)
    assert score["scalar_first_exact_rank"] == 2
    assert score["fusion_first_exact_rank"] == 2
    assert not score["fusion_top_one_exact"]
    assert score["portfolio_supply"]


if __name__ == "__main__":
    test_posthoc_scorer_separates_supply_portfolio_and_autonomous_top_one()
    print("self-fed frontier confirmation scorer tests passed")
