#!/usr/bin/env python3

from collections import Counter

from materials_gcts_frontier_band_marking import (
    BAND_FEATURE_NAMES, BandTrainingExample, fit_grouped_band_marker,
    frontier_score_bands, score_band)
from materials_gcts_recursive_connections import MarkedProposalResult


def _proposals():
    points = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    return MarkedProposalResult(
        Counter({points[0]: 4, points[1]: 2, points[2]: 1}), 0, None,
        {point: Counter({"Cd": index + 1})
         for index, point in enumerate(points)},
        {point: Counter({"Yb": 1}) for point in points},
        {point: Counter({("port", index): index + 1})
         for index, point in enumerate(points)},
        {point: Counter({index: index + 1})
         for index, point in enumerate(points)})


def test_band_descriptor_and_grouped_fit_are_finite_and_target_free():
    proposals = _proposals()
    scores = {(1., 0., 0.): .9, (0., 1., 0.): .7, (0., 0., 1.): .7}
    bands = frontier_score_bands(proposals, scores)
    reversed_bands = frontier_score_bands(
        proposals, dict(reversed(tuple(scores.items()))))
    assert tuple(len(row.positions) for row in bands) == (1, 2)
    assert reversed_bands == bands
    assert all(len(row.features) == len(BAND_FEATURE_NAMES) for row in bands)
    rows = tuple(BandTrainingExample(
        group, tuple(value + offset for value in bands[index].features),
        index == 0, len(bands[index].positions))
        for group, offset in (("a", 0.), ("b", .02), ("c", -.02))
        for index in range(2))
    marker, audit = fit_grouped_band_marker(rows, ridges=(.1, 1.))
    assert audit.groups == 3
    assert audit.examples == 6
    assert audit.selected_correct_actions / audit.selected_actions >= .95
    assert all(0. <= score_band(marker, row.features) <= 1. for row in rows)


if __name__ == "__main__":
    test_band_descriptor_and_grouped_fit_are_finite_and_target_free()
    print("frontier band marking tests: passed")
