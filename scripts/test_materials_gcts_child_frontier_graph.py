#!/usr/bin/env python3
"""Fast invariance and conflict controls for child-frontier graphs."""

from materials_gcts_child_frontier_graph import (
    ChildFrontierAction, ChildFrontierNode, child_frontier_graph,
    child_frontier_graph_embedding)


def _node(color, code, incoming, outgoing, dead=False):
    return ChildFrontierNode(
        color, code, 2, 3, tuple(incoming), 2, tuple(outgoing), 2,
        ("X",), dead)


def test_permutation_translation_rotation_and_failure_edges():
    first = ChildFrontierAction(
        _node("X", (1, 0), (("p", "X"),), (("q", "Y"),)),
        (0., 0., 0.), (((0., 2., 0.), "Y"),))
    second = ChildFrontierAction(
        _node("Y", (0, 1), (("p", "X"),), (("q", "X"),)),
        (2., 0., 0.), (((0., 2., 0.), "X"),))
    graph = child_frontier_graph(
        (first, second), minimum_distance=1., distance_scale=1.)
    assert graph.conflict_edges == 1
    assert graph.maximum_compatible_actions == 1
    assert graph.edges[0].conflicting_outgoing_colors_bin > 0
    # Rotate (x,y,z)->(-y,x,z), translate, and reverse input order.
    def move(point):
        return (7. - point[1], -3. + point[0], 5. + point[2])
    moved = tuple(ChildFrontierAction(
        row.node, move(row.point),
        tuple((move(point), color) for point, color in row.outgoing_sites))
        for row in reversed((first, second)))
    transformed = child_frontier_graph(
        moved, minimum_distance=1., distance_scale=1.)
    assert transformed.canonical_digest == graph.canonical_digest
    assert child_frontier_graph_embedding(transformed) == \
        child_frontier_graph_embedding(graph)
    assert graph.proper_se3_invariant and not graph.lattice_coordinates_used
    assert not graph.target_used


if __name__ == "__main__":
    test_permutation_translation_rotation_and_failure_edges()
    print("child-frontier graph tests passed")
