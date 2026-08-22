#!/usr/bin/env python3
"""Executable checks for the frozen target-blind prefix scheduler."""

from __future__ import annotations

from types import SimpleNamespace

from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)


def _branch(parent):
    first = (((0., 0., 0.), "X"), ((1., 0., 0.), "Y"),
             ((0., 1., 0.), "Z"))
    children = tuple((
        ((2. + child * .1, 0., 0.), "X"),
        ((2. + child * .1, 1., 0.), "Y"),
        ((2. + child * .1, 0., 1.), "Z"))
        for child in range(8))
    scores = tuple((float(8 - child), float(child), 0., 0.)
                   for child in range(8))
    return SimpleNamespace(
        first_rank=parent, first_actions=first, second_actions=children,
        second_channel_scores=scores)


def test_frozen_schedule():
    schedule, artifact = load_default_schedule()
    assert schedule.parent_width == 8
    assert schedule.joint_top_k == 1
    assert schedule.base_top_k == 5
    assert schedule.maximum_prefixes == 48
    assert artifact["selected"]["supplied_exact_child_groups"] == 6
    assert artifact["selected"]["total_exact_child_groups"] == 6
    seed_positions = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    seed_species = ("X", "Y", "Z")
    result = schedule_prefixes(
        schedule=schedule, seed_positions=seed_positions,
        seed_species=seed_species,
        branches=tuple(_branch(parent) for parent in range(1, 9)))
    assert len(result["selected_rows"]) <= 48
    assert len(result["selected_rows"]) + len(result["deferred_rows"]) == 64
    assert len(result["complete_queue_digest"]) == 64
    assert len(result["selected_prefix_digest"]) == 64
    assert not result["model"].target_used_for_scoring


if __name__ == "__main__":
    test_frozen_schedule()
    print("joint prefix schedule tests passed")
