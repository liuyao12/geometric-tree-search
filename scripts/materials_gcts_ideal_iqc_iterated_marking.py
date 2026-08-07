#!/usr/bin/env python3
"""Reuse one generic GCTS marking across two ideal-IQC inflation levels.

The marker is trained only on the 507 -> 1,969 transition.  Its settings and
training exemplars are then frozen while candidate actions from the independent
1,969 -> 8,603 oracle level are classified.  This benchmarks a recursively
reusable subset of inflation actions; it is not a complete generator for every
atom in the larger patch.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from statistics import median
from typing import Tuple

from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_section_marking import (
    ColoredPoint, MarkingExample, fit_marker_auto, predict)


@dataclass(frozen=True)
class IdealIqcIteratedMarkingBenchmark:
    atom_counts: Tuple[int, ...]
    training_valid_actions: int
    heldout_valid_actions: int
    valid_action_growth_factor: float
    unmarked_candidates: int
    unmarked_precision: float
    unmarked_false_branches: int
    histogram_candidates: int
    histogram_matches: int
    histogram_precision: float
    histogram_recall: float
    histogram_false_branches: int
    captured_action_growth_factor: float
    conjunctive_candidates: int
    conjunctive_matches: int
    conjunctive_precision: float
    conjunctive_recall: float
    conjunctive_false_branches: int
    conjunctive_false_branch_reduction: float
    histogram_neighbors: int
    histogram_threshold: float
    moment_neighbors: int
    moment_threshold: float
    training_uses_second_transition_labels: bool
    full_patch_generator_claimed: bool


def _configuration_examples(configuration, target):
    centers = configuration.positions
    origin = min(range(len(centers)),
                 key=lambda index: math.dist(centers[index], (0., 0., 0.)))
    target_sites = {tuple(round(value, 6) for value in point)
                    for point in target.positions}
    examples = []
    for source, point in enumerate(centers):
        if source == origin:
            continue
        target_point = tuple(HIDDEN_UNIT * value for value in point)
        accepted = int(tuple(round(value, 6) for value in target_point)
                       in target_sites)
        examples.append(MarkingExample(
            origin, source, accepted, 0, target_point))
    points = tuple(ColoredPoint(point, (chemical,))
                   for point, chemical
                   in zip(configuration.positions, configuration.species))
    return points, centers, tuple(examples)


def _metrics(predictions, labels):
    candidates = sum(predictions)
    matches = sum(prediction and label
                  for prediction, label in zip(predictions, labels))
    positives = sum(labels)
    return (candidates, matches,
            matches / candidates if candidates else 0.0,
            matches / positives if positives else 0.0,
            candidates - matches)


def evaluate() -> IdealIqcIteratedMarkingBenchmark:
    first, _ = oracle_patch(3, 9.0)
    second, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    third, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    first_points, first_centers, training = _configuration_examples(
        first, second)
    second_points, second_centers, heldout = _configuration_examples(
        second, third)
    nearest = [min(math.dist(point, other) for other in first_centers
                   if other != point) for point in first_centers]
    radius = 2.0 * median(nearest)
    marker = fit_marker_auto(
        first_points, first_centers, training, radius, chemical=True)
    results = predict(marker, second_points, second_centers, heldout)
    labels = [example.accepted for example in heldout]
    histogram_predictions = [
        result.histogram_score >= marker.histogram.settings.threshold
        for result in results]
    conjunction_predictions = [result.accepted for result in results]
    histogram = _metrics(histogram_predictions, labels)
    conjunction = _metrics(conjunction_predictions, labels)
    training_valid = sum(example.accepted for example in training)
    heldout_valid = sum(labels)
    unmarked_false = len(labels) - heldout_valid
    return IdealIqcIteratedMarkingBenchmark(
        (len(first.positions), len(second.positions), len(third.positions)),
        training_valid, heldout_valid, heldout_valid / training_valid,
        len(labels), heldout_valid / len(labels), unmarked_false,
        *histogram, histogram[1] / training_valid,
        *conjunction, unmarked_false / conjunction[4],
        marker.histogram.settings.neighbors,
        marker.histogram.settings.threshold,
        marker.moments.settings.neighbors,
        marker.moments.settings.threshold,
        False, False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
