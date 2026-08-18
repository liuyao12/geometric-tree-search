#!/usr/bin/env python3
"""Exact parity and invariance tests for incremental cluster compatibility."""

from materials_gcts_cluster_prototype_compatibility import (
    fit_prototype_compatibility_context, score_prototype_insertions)
from materials_gcts_recursive_connections import (
    learn_recurrent_cluster_prototypes, local_cluster_types,
    map_to_prototypes)


EDGES = (1.1, 1.6, 2.2)


def _residuals(types, prototypes):
    mapped = map_to_prototypes(types, prototypes)
    return tuple(sum(abs(left - right) for left, right in zip(
        row.cumulative_neighbor_counts,
        prototype.cumulative_neighbor_counts))
        for row, prototype in zip(types, mapped))


def main():
    positions = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.),
                 (1., 1., 0.), (0., 0., 1.))
    colors = ("A", "B", "A", "B", "A")
    second = tuple((x + 4., y - 3., z + 2.) for x, y, z in positions)
    groups = (local_cluster_types(positions, colors, EDGES),
              local_cluster_types(second, colors, EDGES))
    prototypes = learn_recurrent_cluster_prototypes(groups, minimum_groups=2)
    inserted = ((1., 0., 1.), (1., 1., 1.))
    inserted_colors = ("B", "A")
    context = fit_prototype_compatibility_context(
        positions, colors, EDGES, prototypes)
    score = score_prototype_insertions(
        context, inserted, inserted_colors)
    full_types = local_cluster_types(
        positions + inserted, colors + inserted_colors, EDGES)
    expected = _residuals(full_types, prototypes)
    baseline = _residuals(groups[0], prototypes)
    assert score.inserted_residuals == expected[-2:]
    assert score.existing_residual_delta == \
        sum(expected[:-2]) - sum(baseline)
    assert score.total_residual_delta == sum(expected) - sum(baseline)
    assert score.affected_existing_atoms == 5
    assert not score.target_used

    # Proper rigid motion and input permutation cannot change the score.
    moved = tuple((-y + 7., x - 5., z + 3.) for x, y, z in positions)
    moved_inserted = tuple((-y + 7., x - 5., z + 3.)
                           for x, y, z in inserted)
    moved_context = fit_prototype_compatibility_context(
        moved[::-1], colors[::-1], EDGES, prototypes)
    moved_score = score_prototype_insertions(
        moved_context, moved_inserted[::-1], inserted_colors[::-1])
    assert moved_score.inserted_residuals == \
        score.inserted_residuals[::-1]
    assert moved_score.existing_residual_delta == \
        score.existing_residual_delta
    assert moved_score.total_residual_delta == score.total_residual_delta
    try:
        score_prototype_insertions(context, (positions[0],), (colors[0],))
    except ValueError:
        pass
    else:
        raise AssertionError("known-site insertion must fail closed")
    print("cluster prototype compatibility passed")


if __name__ == "__main__":
    main()
