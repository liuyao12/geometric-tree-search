#!/usr/bin/env python3
"""Unit controls for target-free shared-action fallback selection."""

from types import SimpleNamespace

from materials_gcts_action_marginal_prefix_schedule import \
    select_action_marginal_prefixes


def _row(parent, child, sources, joint_rank, base_rank):
    return (parent, child, sources, joint_rank, 0., base_rank, 0.)


def test_joint_leaders_stay_and_fallback_avoids_universal_action():
    bad = ((9., 9., 9.), "X")
    branches = tuple(SimpleNamespace(
        first_rank=parent,
        first_actions=(((float(parent), 0., 0.), "A"),),
        second_actions=(
            (bad, ((float(parent), 1., 0.), "B")),
            (((float(parent), 2., 0.), "C"),),
            (bad, ((float(parent), 3., 0.), "D")),
        )) for parent in (1, 2, 3))
    rows = tuple(row for parent in (1, 2, 3) for row in (
        _row(parent, 0, ("joint", "base-fallback"), 1, 1),
        _row(parent, 1, ("base-fallback",), 2, 2),
        _row(parent, 2, ("base-fallback",), 3, 3)))
    result = select_action_marginal_prefixes(
        scheduled={"selected_rows": rows}, branches=branches)
    assert tuple(row[1] for row in result["joint_rows"]) == (0, 0, 0)
    assert tuple(row[1] for row in result["diverse_fallback_rows"]) == \
        (1, 1, 1)
    assert result["joint_universal_actions"] == (bad,)
    assert len(result["selected_rows"]) == 6
    assert not result["target_used"]

    bounded = select_action_marginal_prefixes(
        scheduled={"selected_rows": rows}, branches=branches,
        maximum_fallbacks=2, require_universal_avoidance=True)
    assert len(bounded["joint_rows"]) == 3
    assert len(bounded["diverse_fallback_rows"]) == 2
    assert tuple(row[1] for row in bounded["diverse_fallback_rows"]) == (1, 1)
    assert bounded["universal_avoidance_required"]


if __name__ == "__main__":
    test_joint_leaders_stay_and_fallback_avoids_universal_action()
    print("action-marginal prefix schedule tests passed")
