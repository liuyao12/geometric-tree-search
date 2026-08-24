#!/usr/bin/env python3
"""Controls for target-free commuting frontier closure."""

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

from materials_gcts_iqc_commuting_frontier_closure import \
    commuting_frontier_closure


@dataclass(frozen=True)
class State:
    actions: tuple


def test_closure_requires_every_permutation_and_never_sees_target():
    actions = tuple((((float(index), 0., 0.), "X"),)
                    for index in range(4))
    witnessed = tuple(State(action) for action in actions)

    @dataclass(frozen=True)
    class ReplayState:
        actions: tuple

    def extend(_source, _runtime, state, action, _radius, **_caches):
        # Action zero cannot be placed after both actions two and three, so the
        # last lexicographic triple is dependency ordered, not commuting.
        if action[0][0] == 0. and {row[0][0] for row in state.actions} == {2., 3.}:
            return None
        return ReplayState(tuple(sorted(state.actions + (action,))))

    with patch(
            "materials_gcts_iqc_commuting_frontier_closure._initial_state",
            return_value=ReplayState(())), patch(
            "materials_gcts_iqc_commuting_frontier_closure."
            "_extend_witnessed_action", side_effect=extend), patch(
            "materials_gcts_iqc_commuting_frontier_closure._state_key",
            side_effect=lambda state: state.actions):
        result = commuting_frontier_closure(
            source=SimpleNamespace(), runtime={}, witnessed_states=witnessed,
            radius=1., action_count=3)
    assert result.combinations_checked == 4
    assert result.replayable_combinations == 4
    assert result.all_permutations_combinations == 3
    assert len(result.states) == 3
    assert not result.target_used


def test_closure_fails_closed_on_unbounded_action_universe():
    witnessed = tuple(State((((float(index), 0., 0.), "X"),))
                        for index in range(4))
    try:
        commuting_frontier_closure(
            source=SimpleNamespace(), runtime={},
            witnessed_states=witnessed, radius=1., action_count=3,
            maximum_action_universe=3)
    except ValueError:
        pass
    else:
        raise AssertionError("unbounded closure did not fail closed")


if __name__ == "__main__":
    test_closure_requires_every_permutation_and_never_sees_target()
    test_closure_fails_closed_on_unbounded_action_universe()
    print("IQC commuting frontier closure tests passed")
