#!/usr/bin/env python3

from materials_gcts_clusters2_future_option import (
    ChildOption, FrozenFutureOptionSpec, ParentOption,
    select_future_options)


def _parents(order=("a", "b", "c")):
    rows = {
        "a": ParentOption("a", (
            ChildOption("a0", (.9, .1)), ChildOption("a1", (.8, .2)))),
        "b": ParentOption("b", (
            ChildOption("b0", (.2, .95)), ChildOption("b1", (.1, .85)))),
        "c": ParentOption("c", (
            ChildOption("c0", (.7, .7)), ChildOption("c1", (.6, .6)))),
    }
    return tuple(rows[key] for key in order)


def test_channel_diversity_and_candidate_identity():
    spec = FrozenFutureOptionSpec(("section", "ports"), top_k=2,
                                  beam_width=2)
    forward = select_future_options(_parents(), spec)
    reversed_input = select_future_options(_parents(("c", "b", "a")), spec)
    assert forward.selected_parent_ids == ("a", "b")
    assert forward.selected_by_channels == (("section", "a"),
                                             ("ports", "b"))
    assert dict(forward.selected_child_ids_by_parent) == {
        "a": ("a0", "a1"), "b": ("b0", "b1")}
    assert forward.candidate_digest == reversed_input.candidate_digest
    assert forward.selected_parent_ids == reversed_input.selected_parent_ids
    assert not forward.target_used


def test_future_option_uses_more_than_one_child():
    parents = (
        ParentOption("spike", (
            ChildOption(0, (1.,)), ChildOption(1, (0.,)))),
        ParentOption("depth", (
            ChildOption(0, (.7,)), ChildOption(1, (.7,)))),
    )
    top_one = select_future_options(
        parents, FrozenFutureOptionSpec(("mark",), 1, 1))
    top_two = select_future_options(
        parents, FrozenFutureOptionSpec(("mark",), 2, 1))
    assert top_one.selected_parent_ids == ("spike",)
    assert top_two.selected_parent_ids == ("depth",)


if __name__ == "__main__":
    test_channel_diversity_and_candidate_identity()
    test_future_option_uses_more_than_one_child()
    print("clusters-squared future-option marking: passed")
