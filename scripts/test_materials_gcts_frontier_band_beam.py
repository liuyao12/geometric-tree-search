#!/usr/bin/env python3
from materials_gcts_frontier_band_beam import FrontierBand, search_frontier_bands


def test_boundary_lookahead_rolls_back_wrong_greedy_branch():
    wrong = FrontierBand("greedy-wrong", 1.0, 0.0)
    exact = FrontierBand("rank2-exact", .9998, 0.0)
    children = {
        "greedy-wrong": (FrontierBand("dead", .2, -.8),),
        "rank2-exact": (FrontierBand("consistent", .9, .7),),
    }
    trace = search_frontier_bands(
        (wrong, exact), lambda band: children.get(band.band_id, ()),
        beam_width=2, lookahead_depth=2)
    assert trace.selected_ids == ("rank2-exact", "consistent")
    assert trace.greedy_rollbacks == 1
    assert trace.explored_nodes == 4
    assert not trace.target_used


def test_leaf_value_can_override_a_slightly_better_immediate_mark():
    roots = (FrontierBand("wrong", .9997444, 0.),
             FrontierBand("exact", .9995567, 0.))
    future = {
        "wrong": (FrontierBand("weak-future", 0., .9997197),),
        "exact": (FrontierBand("strong-future", 0., .9997951),),
    }
    trace = search_frontier_bands(
        roots, lambda band: future.get(band.band_id, ()),
        beam_width=2, lookahead_depth=2, leaf_boundary_first=True)
    assert trace.selected_ids[0] == "exact"
    assert trace.greedy_rollbacks == 1


if __name__ == "__main__":
    test_boundary_lookahead_rolls_back_wrong_greedy_branch()
    test_leaf_value_can_override_a_slightly_better_immediate_mark()
    print("frontier-band beam tests: passed")
