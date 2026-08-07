#!/usr/bin/env python3
"""Origin-held-out GCTS marking benchmark on experimental Sc-Zn data.

The inflation scale and the two bounded-section classifier settings are frozen
by ``materials_gcts_experimental_sczn_benchmark``.  This replication trains
the section exemplars on complete parent centres in one spatial checkerboard
and evaluates different parent centres in the other.  Fixed-point mappings are
excluded because they do not grow the configuration.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import List, Sequence, Tuple

import materials_gcts_experimental_sczn_benchmark as sczn


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


def _standardize(training, heldout, component: int):
    dimensions = len(training[0][component])
    means = [sum(row[component][axis] for row in training) / len(training)
             for axis in range(dimensions)]
    scales = [max(1e-6, (sum((row[component][axis] - means[axis]) ** 2
                             for row in training) / len(training)) ** .5)
              for axis in range(dimensions)]

    def transform(rows):
        return [tuple((row[component][axis] - means[axis]) / scales[axis]
                      for axis in range(dimensions)) for row in rows]
    return transform(training), transform(heldout)


def _three_neighbor_scores(training_vectors, training_labels,
                           heldout_vectors):
    scores = []
    for candidate in heldout_vectors:
        nearest: List[Tuple[float, int]] = []
        for known, label in zip(training_vectors, training_labels):
            distance = sum((left - right) ** 2
                           for left, right in zip(known, candidate))
            if len(nearest) < 3:
                nearest.append((distance, label))
                nearest.sort()
            elif distance < nearest[-1][0]:
                nearest[-1] = distance, label
                nearest.sort()
        weights = [1.0 / (math.sqrt(distance) + 1e-6)
                   for distance, _ in nearest]
        scores.append(sum(weight * label
                          for weight, (_, label) in zip(weights, nearest)) /
                      sum(weights))
    return scores


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
        candidate_indices = []
        labels = []
        for source_index, source in enumerate(centers):
            if source_index == origin_index:
                continue
            target = tuple(origin[axis] + scale *
                           (source[axis] - origin[axis])
                           for axis in range(3))
            if not all(lower[axis] <= target[axis] <= upper[axis]
                       for axis in range(3)):
                continue
            candidate_indices.append(source_index)
            error = sczn._nearest(target, centers, target_grid, tolerance)
            labels.append((int(error <= tolerance), target, error))
        histogram = sczn._atomic_section_descriptors(
            sites, centers, origin, candidate_indices, chemical=False)
        moments = sczn._atomic_moment_descriptors(
            sites, centers, origin, candidate_indices, chemical=False)
        # This split is fixed by parent position and never sees target labels.
        split = sum(math.floor(value / 16.0) for value in origin) & 1
        destination = heldout if split else training
        origin_ids = heldout_origin_ids if split else training_origin_ids
        origin_ids.add(origin_index)
        destination.extend((histogram[index], moments[index], label, origin_index,
                            index, target, error)
                           for index, (label, target, error)
                           in zip(candidate_indices, labels))

    training_labels = [row[2] for row in training]
    heldout_labels = [row[2] for row in heldout]
    histogram_training, histogram_heldout = _standardize(
        training, heldout, 0)
    moment_training, moment_heldout = _standardize(training, heldout, 1)
    histogram_scores = _three_neighbor_scores(
        histogram_training, training_labels, histogram_heldout)
    moment_scores = _three_neighbor_scores(
        moment_training, training_labels, moment_heldout)
    # Frozen by single-origin leave-one-out fitting, not this held-out set.
    histogram_predictions = [score >= .65 for score in histogram_scores]
    moment_predictions = [score >= .85 for score in moment_scores]
    conjunctive_predictions = [histogram and moment
                               for histogram, moment in
                               zip(histogram_predictions, moment_predictions)]
    histogram_result = _metrics(histogram_predictions, heldout_labels)
    moment_result = _metrics(moment_predictions, heldout_labels)
    conjunctive_result = _metrics(conjunctive_predictions, heldout_labels)
    unmarked_false = len(heldout) - sum(heldout_labels)
    marked_false = conjunctive_result[0] - conjunctive_result[1]
    accepted_origins = {row[3] for prediction, row
                        in zip(conjunctive_predictions, heldout) if prediction}
    correct_origins = {row[3] for prediction, row
                       in zip(conjunctive_predictions, heldout)
                       if prediction and row[2]}
    verified_errors = [row[6] for prediction, row
                       in zip(conjunctive_predictions, heldout)
                       if prediction and row[2]]
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
        conjunctive_result[1] * median_atoms, True, False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
