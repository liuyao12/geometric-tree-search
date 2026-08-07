#!/usr/bin/env python3
"""Origin-held-out GCTS marking benchmark on experimental Sc-Zn data.

The inflation scale comes from ``materials_gcts_experimental_sczn_benchmark``.
The material-generic section marker chooses its own settings by holding out
complete training parent centres, then evaluates different parent centres in
the other spatial checkerboard.  A frozen precision-first setting is reported
as a second operating point.  Fixed-point mappings are excluded because they
do not grow the configuration.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Sequence

import materials_gcts_experimental_sczn_benchmark as sczn
from materials_gcts_section_marking import (
    ColoredPoint, MarkingExample, SectionSettings, fit_marker,
    fit_marker_auto, predict)


@dataclass(frozen=True)
class MultiOriginMarkingBenchmark:
    learned_scale: float
    training_origins: int
    heldout_origins: int
    training_candidates: int
    training_matches: int
    heldout_candidates: int
    heldout_matches: int
    unmarked_precision: float
    histogram_marked_candidates: int
    histogram_matches: int
    histogram_precision: float
    histogram_recall: float
    moment_marked_candidates: int
    moment_matches: int
    moment_precision: float
    moment_recall: float
    conjunctive_marked_candidates: int
    conjunctive_matches: int
    conjunctive_precision: float
    conjunctive_recall: float
    unmarked_false_branches: int
    marked_false_branches: int
    false_branch_reduction: float
    heldout_parent_actions: int
    correct_parent_actions: int
    materialized_target_centers: int
    verified_target_centers: int
    verified_target_mean_error: float
    represented_atom_instances: int
    fixed_points_excluded: bool
    split_uses_target_labels: bool
    settings_selected_by_parent_group_cv: bool
    histogram_neighbors: int
    histogram_threshold: float
    moment_neighbors: int
    moment_threshold: float
    conservative_marked_candidates: int
    conservative_matches: int
    conservative_precision: float
    conservative_recall: float
    conservative_false_branch_reduction: float


def _metrics(predictions: Sequence[bool], labels: Sequence[int]):
    candidates = sum(predictions)
    matches = sum(prediction and label
                  for prediction, label in zip(predictions, labels))
    positives = sum(labels)
    return (candidates, matches,
            matches / candidates if candidates else 0.0,
            matches / positives if positives else 0.0)


def evaluate() -> MultiOriginMarkingBenchmark:
    sites, _ = sczn.parse_cif(sczn.download_cif())
    _, clusters = sczn.infer_shell_clusters(sites)
    centers = [cluster.center for cluster in clusters]
    learned = sczn.fit_inflation(centers)
    scale = learned.scale
    tolerance = .45
    target_grid = sczn._spatial_index(centers, tolerance)
    lower = tuple(min(point[axis] for point in centers) + 1.0
                  for axis in range(3))
    upper = tuple(max(point[axis] for point in centers) - 1.0
                  for axis in range(3))
    training = []
    heldout = []
    training_origin_ids = set()
    heldout_origin_ids = set()

    for origin_index, origin in enumerate(centers):
        for source_index, source in enumerate(centers):
            if source_index == origin_index:
                continue
            target = tuple(origin[axis] + scale *
                           (source[axis] - origin[axis])
                           for axis in range(3))
            if not all(lower[axis] <= target[axis] <= upper[axis]
                       for axis in range(3)):
                continue
            error = sczn._nearest(target, centers, target_grid, tolerance)
            example = MarkingExample(
                origin_index, source_index, int(error <= tolerance),
                origin_index, target)
            # This split is fixed by parent position and never sees target labels.
            split = sum(math.floor(value / 16.0) for value in origin) & 1
            destination = heldout if split else training
            origin_ids = heldout_origin_ids if split else training_origin_ids
            origin_ids.add(origin_index)
            destination.append((example, error))

    point_cloud = tuple(ColoredPoint(site.position, site.species)
                        for site in sites)
    training_examples = tuple(row[0] for row in training)
    heldout_examples = tuple(row[0] for row in heldout)
    marker = fit_marker_auto(
        point_cloud, centers, training_examples, 7.8,
        (3.5, 5.5, 7.8), chemical=False)
    results = predict(marker, point_cloud, centers, heldout_examples)
    conservative_marker = fit_marker(
        point_cloud, centers, training_examples, 7.8,
        SectionSettings(3, .65), SectionSettings(3, .85),
        (3.5, 5.5, 7.8), chemical=False)
    conservative_predictions = predict(
        conservative_marker, point_cloud, centers, heldout_examples)
    training_labels = [example.accepted for example in training_examples]
    heldout_labels = [example.accepted for example in heldout_examples]
    histogram_predictions = [
        result.histogram_score >= marker.histogram.settings.threshold
        for result in results]
    moment_predictions = [
        result.moment_score >= marker.moments.settings.threshold
        for result in results]
    conjunctive_predictions = [result.accepted for result in results]
    histogram_result = _metrics(histogram_predictions, heldout_labels)
    moment_result = _metrics(moment_predictions, heldout_labels)
    conjunctive_result = _metrics(conjunctive_predictions, heldout_labels)
    conservative_result = _metrics(
        [result.accepted for result in conservative_predictions],
        heldout_labels)
    unmarked_false = len(heldout) - sum(heldout_labels)
    marked_false = conjunctive_result[0] - conjunctive_result[1]
    accepted_origins = {result.example.parent for result
                        in results if result.accepted}
    correct_origins = {result.example.parent for result in results
                       if result.accepted and result.example.accepted}
    verified_errors = [error for result, (_, error) in zip(results, heldout)
                       if result.accepted and result.example.accepted]
    median_atoms = sorted(sum(sczn._distance(cluster.center, site.position) <= 7.8
                              for site in sites)
                          for cluster in clusters)[len(clusters) // 2]
    return MultiOriginMarkingBenchmark(
        scale, len(training_origin_ids), len(heldout_origin_ids),
        len(training), sum(training_labels), len(heldout), sum(heldout_labels),
        sum(heldout_labels) / len(heldout),
        *histogram_result, *moment_result, *conjunctive_result,
        unmarked_false, marked_false,
        unmarked_false / marked_false if marked_false else float("inf"),
        len(accepted_origins), len(correct_origins),
        conjunctive_result[0], conjunctive_result[1],
        sum(verified_errors) / len(verified_errors),
        conjunctive_result[1] * median_atoms, True, False, True,
        marker.histogram.settings.neighbors,
        marker.histogram.settings.threshold,
        marker.moments.settings.neighbors,
        marker.moments.settings.threshold,
        conservative_result[0], conservative_result[1],
        conservative_result[2], conservative_result[3],
        unmarked_false / (conservative_result[0] - conservative_result[1]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
