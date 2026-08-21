#!/usr/bin/env python3

from dataclasses import dataclass

from materials_gcts_marking_portfolio_tree import (
    FrozenPortfolioAction, search_marking_portfolio)


@dataclass(frozen=True)
class State:
    name: str


GRAPH = {
    "seed": (
        ("a", "A", 3., 0.),
        ("b", "B", 2., 1.),
        ("c", "C", 1., 4.),
    ),
    "A": (("a1", "X", 3., 0.), ("a2", "Y", 1., 1.)),
    "C": (("c1", "Y", 0., 4.), ("c2", "Z", 1., 2.)),
    "B": (), "X": (), "Y": (), "Z": (),
}


def expand(state):
    return tuple(FrozenPortfolioAction(
        action, State(child), (("connection", connection),
                               ("rollout", rollout)))
        for action, child, connection, rollout in GRAPH[state.name])


def test_distinct_marking_heads_survive_one_identical_tree():
    result = search_marking_portfolio(
        State("seed"), expand=expand, state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=2, beam_width=2)
    assert result.levels[0].candidate_count == 3
    assert result.levels[0].marking_heads == (
        ("connection", "A"), ("rollout", "C"))
    assert result.levels[0].retained_state_keys == ("A", "C")
    assert result.levels[1].candidate_count == 4
    assert set(result.levels[1].retained_state_keys) == {"X", "Y"}
    assert not result.target_api_present and not result.target_used


def test_same_physical_state_is_not_counted_twice():
    result = search_marking_portfolio(
        State("seed"), expand=expand, state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=2, beam_width=3)
    assert result.levels[1].candidate_count == 4
    assert result.levels[1].unique_state_count == 3
    assert len(result.levels[1].retained_state_keys) == 3
    assert result.levels[1].retained_state_keys.count("Y") == 1


def test_parent_balanced_schedule_preserves_each_rollback_lineage():
    graph = {
        "seed": (("a", "A", 3., 0.), ("b", "B", 0., 3.)),
        "A": (("a1", "A1", 3., 0.), ("a2", "A2", 0., 3.)),
        "B": (("b1", "B1", 3., 0.), ("b2", "B2", 0., 3.)),
    }

    def balanced_expand(state):
        return tuple(FrozenPortfolioAction(
            action, State(child), (("connection", connection),
                                   ("rollout", rollout)))
            for action, child, connection, rollout in graph.get(state.name, ()))

    result = search_marking_portfolio(
        State("seed"), expand=balanced_expand,
        state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=2, beam_width=4,
        beam_schedule=(2, 4),
        allocation="parent-marking-round-robin")
    assert result.beam_schedule == (2, 4)
    assert result.levels[0].retained_state_keys == ("A", "B")
    assert set(result.levels[1].retained_state_keys) == {
        "A1", "A2", "B1", "B2"}


def test_stage_local_scores_can_replace_instead_of_accumulate():
    result = search_marking_portfolio(
        State("seed"), expand=expand, state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=2, beam_width=2,
        score_aggregation="replace")
    assert result.score_aggregation == "replace"
    assert set(result.levels[1].retained_state_keys) == {"Y", "X"}
    by_state = {node.state_key: dict(node.cumulative_scores)
                for node in result.retained}
    assert by_state["X"]["connection"] == 3.
    assert by_state["Y"]["rollout"] == 4.


def test_marking_channels_allocate_before_repeating_one_cell():
    def channelled(_state):
        return (
            FrozenPortfolioAction(
                "a", State("A"), (("connection", 4.), ("rollout", 4.)),
                (("connection", "same"), ("rollout", "same"))),
            FrozenPortfolioAction(
                "b", State("B"), (("connection", 3.), ("rollout", 3.)),
                (("connection", "same"), ("rollout", "same"))),
            FrozenPortfolioAction(
                "c", State("C"), (("connection", 2.), ("rollout", 2.)),
                (("connection", "other"), ("rollout", "other"))),
        )
    result = search_marking_portfolio(
        State("seed"), expand=channelled, state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=1, beam_width=2,
        channel_diversity=True)
    assert result.channel_diversity
    assert result.levels[0].retained_state_keys == ("A", "C")


def test_candidate_digest_does_not_depend_on_marking_order():
    first = search_marking_portfolio(
        State("seed"), expand=expand, state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=1, beam_width=2)
    second = search_marking_portfolio(
        State("seed"), expand=expand, state_key=lambda row: row.name,
        marking_names=("rollout", "connection"), depth=1, beam_width=2)
    assert first.levels[0].candidate_digest == second.levels[0].candidate_digest


def test_missing_marking_score_fails_closed():
    def incomplete(_state):
        return (FrozenPortfolioAction("bad", State("A"),
                                      (("connection", 1.),)),)
    try:
        search_marking_portfolio(
            State("seed"), expand=incomplete, state_key=lambda row: row.name,
            marking_names=("connection", "rollout"), depth=1, beam_width=2)
    except ValueError:
        pass
    else:
        raise AssertionError("missing marking score was accepted")


def test_agreeing_crystal_marks_do_not_duplicate_one_physical_state():
    def crystal(_state):
        return (
            FrozenPortfolioAction(
                "translation-rule", State("cell-2"),
                (("connection", 1.), ("rollout", .7))),
            FrozenPortfolioAction(
                "symmetry-equivalent-rule", State("cell-2"),
                (("connection", .7), ("rollout", 1.))),
        )
    result = search_marking_portfolio(
        State("cell-1"), expand=crystal, state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=1, beam_width=2,
        beam_schedule=(2,), channel_diversity=True)
    assert result.levels[0].candidate_count == 2
    assert result.levels[0].unique_state_count == 1
    assert result.levels[0].retained_state_keys == ("cell-2",)


def test_empty_amorphous_frontier_does_not_hallucinate_growth():
    result = search_marking_portfolio(
        State("glass-seed"), expand=lambda _state: (),
        state_key=lambda row: row.name,
        marking_names=("connection", "rollout"), depth=4, beam_width=2,
        beam_schedule=(2, 4, 4, 8), channel_diversity=True)
    assert result.levels == ()
    assert len(result.retained) == 1
    assert result.retained[0].state_key == "glass-seed"


if __name__ == "__main__":
    test_distinct_marking_heads_survive_one_identical_tree()
    test_same_physical_state_is_not_counted_twice()
    test_parent_balanced_schedule_preserves_each_rollback_lineage()
    test_stage_local_scores_can_replace_instead_of_accumulate()
    test_marking_channels_allocate_before_repeating_one_cell()
    test_candidate_digest_does_not_depend_on_marking_order()
    test_missing_marking_score_fails_closed()
    test_agreeing_crystal_marks_do_not_duplicate_one_physical_state()
    test_empty_amorphous_frontier_does_not_hallucinate_growth()
    print("generic marking portfolio tree tests passed")
