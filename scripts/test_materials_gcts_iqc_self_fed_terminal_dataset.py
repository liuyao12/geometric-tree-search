#!/usr/bin/env python3

import hashlib
from types import SimpleNamespace

import materials_gcts_iqc_self_fed_terminal_dataset as dataset
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE, EXPECTED_DATASET_DIGEST, EXPECTED_FIXTURE_SHA256,
    FEATURE_NAMES, SUCCESSOR_FEATURE_NAMES, graph_from_json,
    load_fixture_json, validate_dataset)


def test_feature_schema_is_finite_and_translation_invariant():
    assert len(SUCCESSOR_FEATURE_NAMES) == 16
    assert len(set(FEATURE_NAMES)) == len(FEATURE_NAMES)
    old_descriptors = dataset._descriptors
    old_score = dataset.score_pose_port_state
    old_color = dataset._dominant_source_color
    dataset._descriptors = lambda _p, _s, proposals, _width: {
        point: (index + 1) / 4 for index, point in
        enumerate(sorted(proposals.votes))}
    dataset.score_pose_port_state = lambda _model, value: value
    dataset._dominant_source_color = lambda proposals, point: \
        proposals.colors[point]
    try:
        def state(shift):
            def moved(point):
                return tuple(value + delta for value, delta in zip(point, shift))
            points = tuple(map(moved, ((2., 0., 0.), (3., 0., 0.),
                                       (2., 1., 0.))))
            proposals = SimpleNamespace(
                votes={points[0]: 3, points[1]: 2, points[2]: 1},
                colors={points[0]: "X", points[1]: "Y", points[2]: "X"})
            actions = tuple((moved(point), color) for point, color in (
                ((1., 0., 0.), "X"), ((0., 1., 0.), "Y"),
                ((0., 0., 1.), "Z")))
            return SimpleNamespace(
                positions=(), species=(), proposals=proposals,
                actions=actions, probabilities=(.8, .7, .6), votes=(3, 2, 1))
        first = dataset.terminal_successor_features(
            state((0., 0., 0.)), object(), (0., 0., 0.), 5.)
        second = dataset.terminal_successor_features(
            state((10., -4., 7.)), object(), (10., -4., 7.), 5.)
        assert first == second
        assert len(first) == len(SUCCESSOR_FEATURE_NAMES)
    finally:
        dataset._descriptors = old_descriptors
        dataset.score_pose_port_state = old_score
        dataset._dominant_source_color = old_color


def test_persisted_dataset_is_grouped_complete_and_target_safe():
    raw, payload = load_fixture_json(DEFAULT_FIXTURE)
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256
    row = validate_dataset(payload)
    assert row["dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert row["development_groups"] == 10
    assert sum(len(group["rows"]) for group in row["groups"]) == 1278
    assert sum(group["exact_second_block_terminals"]
               for group in row["groups"]) == 142
    assert sum(group["exact_second_block_terminals"] > 0
               for group in row["groups"]) == 9
    graph = graph_from_json(row["groups"][0]["rows"][0]["graph"])
    assert graph.nodes and graph.incidence_edges and not graph.target_used


if __name__ == "__main__":
    test_feature_schema_is_finite_and_translation_invariant()
    test_persisted_dataset_is_grouped_complete_and_target_safe()
    print("self-fed terminal dataset tests passed")
