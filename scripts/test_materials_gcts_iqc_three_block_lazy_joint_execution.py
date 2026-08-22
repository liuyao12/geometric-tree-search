#!/usr/bin/env python3
"""Fast synthetic execution check for the lazy IQC tree scheduler."""

from __future__ import annotations

from types import SimpleNamespace

import materials_gcts_iqc_three_block_lazy_joint_execution as subject
from materials_gcts_iqc_three_block_portfolio_execution import (
    FrozenPortfolioLineage, FrozenSecondBranch)


def _actions(offset):
    return (((offset, 0., 0.), "X"), ((offset, 1., 0.), "Y"),
            ((offset, 0., 1.), "Z"))


def test_lazy_execution():
    old = {name: getattr(subject, name) for name in (
        "load_default_runtime", "_complete_first_block",
        "_second_worker", "_lazy_third_parent_worker")}
    try:
        subject.load_default_runtime = lambda: {}

        def first(*_args):
            states = tuple(SimpleNamespace(
                positions=((0., 0., 0.),), species=("X",),
                actions=_actions(float(index))) for index in range(8))
            return states, (8,), tuple(range(8)), "a" * 64

        def second(payload):
            parent = payload[1]
            actions = tuple(_actions(20. + parent + child / 10.)
                            for child in range(8))
            scores = tuple((float(8 - child), float(child), 0., 0.)
                           for child in range(8))
            return FrozenSecondBranch(
                parent, payload[2], _actions(float(parent)), (8,),
                actions, scores, "b" * 64)

        def third(payload):
            parent = payload[5]
            rows = tuple(((1,), (FrozenPortfolioLineage(
                parent, child, 0, tuple(payload[3]), tuple(actions),
                _actions(50. + child), tuple(payload[3]) + tuple(actions) +
                _actions(50. + child)),))
                for child, actions in payload[4])
            count = len(rows)
            return rows, tuple(sorted({
                "naive_geometry_expansions": count * 3,
                "unique_geometry_expansions": count * 2,
                "saved_geometry_expansions": count,
                "geometry_cache_hits": count,
            }.items()))

        subject._complete_first_block = first
        subject._second_worker = second
        subject._lazy_third_parent_worker = third
        result = subject.freeze_three_block_lazy_joint_execution(
            center=(0., 0., 0.),
            seed_positions=((0., 0., 0.), (1., 0., 0.), (0., 1., 0.)),
            seed_species=("X", "Y", "Z"), first_radius=1.,
            second_radius=2., third_radius=3., workers=1)
        assert len(result.selected_prefix_ids_by_parent) == 8
        assert result.expanded_prefix_count <= 48
        assert result.expanded_prefix_count == len(result.lineages)
        assert result.complete_second_prefixes == 64
        assert result.deferred_prefix_count == 64 - result.expanded_prefix_count
        assert result.saved_prefix_expansions > 0
        assert result.saved_geometry_expansions > 0
        assert result.unique_geometry_expansions < \
            result.naive_geometry_expansions
        assert result.bounded_schedule_gate_passed
        assert not result.target_used
    finally:
        for name, value in old.items():
            setattr(subject, name, value)


if __name__ == "__main__":
    test_lazy_execution()
    print("lazy joint execution tests passed")
