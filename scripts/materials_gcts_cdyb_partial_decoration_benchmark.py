#!/usr/bin/env python3
"""Disjoint real-material Cd--Yb test for factorized decoration sections."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_geometry_decoration_vocabulary_benchmark import _decorations
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_partial_decoration_sections_benchmark import (
    _fit_tree, _predict, _scores)


TRAIN_CENTERS = ((-16., -8., 8.), (14., -12., -8.))
EVAL_CENTER = (15., 14., 8.)
RADIUS = 14.


@dataclass(frozen=True)
class CdYbPartialDecorationAudit:
    train_windows: int
    train_atoms: int
    eval_atoms: int
    center_separation: float
    raw_atom_ids_disjoint: bool
    geometry_types: int
    train_geometry_occurrences: int
    eval_geometry_occurrences: int
    eval_atoms_geometry_covered: int
    eval_geometry_atom_coverage: float
    train_full_decoration_alternatives: int
    modal_exact_accuracy: float
    factor_exact_accuracy: float
    modal_site_accuracy: float
    factor_site_accuracy: float
    factor_predictions_unseen_as_whole: int
    unseen_whole_predictions_exact: int
    factor_improves_exact: bool
    factor_improves_sites: bool
    residual_gap_atoms: int
    selected_gap_knn_neighbors: int
    train_gap_marking_spatial_cv_accuracy: float
    heldout_gap_marking_correct_atoms: int
    heldout_gap_marking_accuracy: float
    heldout_gap_species_counts: tuple[tuple[str, int], ...]
    heldout_gap_predicted_species_counts: tuple[tuple[str, int], ...]
    heldout_gap_confusion: tuple[tuple[str, str, int], ...]
    complete_cover_with_gap_clusters: bool
    target_labels_used_for_geometry_fit_or_factor_fit: bool
    source_sites_internal_coordinates_or_family_label_used: bool
    decoration_gate_passed: bool
    partial_section_gate_passed: bool
    limitation: str


def _gap_features(positions, occurrences, type_count, nn_scale):
    nearest_by_type = defaultdict(list)
    for occurrence in occurrences:
        nearest_by_type[occurrence.type_id].append(occurrence.translation)
    result = []
    for index, point in enumerate(positions):
        neighbors = sorted(math.dist(point, other)
                           for other_index, other in enumerate(positions)
                           if other_index != index)[:12]
        neighbors += [6. * nn_scale] * (12 - len(neighbors))
        cluster_distances = []
        for type_id in range(type_count):
            distance = min((math.dist(point, center)
                            for center in nearest_by_type.get(type_id, ())),
                           default=6. * nn_scale)
            cluster_distances.append(min(6., distance / nn_scale))
        result.append(tuple(min(6., value / nn_scale)
                            for value in neighbors) +
                      tuple(cluster_distances))
    return tuple(result)


def _standardize(train, target):
    width = len(train[0])
    means = tuple(sum(row[index] for row in train) / len(train)
                  for index in range(width))
    scales = tuple((sum((row[index] - means[index]) ** 2 for row in train) /
                    len(train)) ** .5 or 1. for index in range(width))
    transform = lambda rows: tuple(tuple(
        (row[index] - means[index]) / scales[index]
        for index in range(width)) for row in rows)
    return transform(train), transform(target)


def _knn(train_features, train_labels, target_features, neighbors):
    result = []
    for target in target_features:
        ranked = sorted((
            sum((left - right) ** 2 for left, right in zip(row, target)),
            repr(label), label)
            for row, label in zip(train_features, train_labels))
        votes = Counter(item[2] for item in ranked[:neighbors])
        result.append(max(votes.items(),
                          key=lambda item: (item[1], repr(item[0])))[0])
    return tuple(result)


def evaluate():
    atoms = generate_cdyb(4, (60.,) * 3)
    train_ids = tuple(index for index, point in enumerate(atoms.positions)
                      if any(math.dist(center, point) <= RADIUS
                             for center in TRAIN_CENTERS))
    eval_ids = tuple(index for index, point in enumerate(atoms.positions)
                     if math.dist(EVAL_CENTER, point) <= RADIUS)
    train_positions = tuple(atoms.positions[index] for index in train_ids)
    train_species = tuple(atoms.symbols[index] for index in train_ids)
    eval_positions = tuple(atoms.positions[index] for index in eval_ids)
    eval_species = tuple(atoms.symbols[index] for index in eval_ids)

    geometry = compile_irregular_port_program(
        tuple("*" for _ in train_positions), train_positions)
    train_rows = _decorations(
        geometry, train_species, train_positions, geometry.occurrences,
        geometry.occurrence_supports)
    by_type = defaultdict(list)
    for type_id, decoration in train_rows:
        by_type[type_id].append(decoration)
    models = {type_id: _fit_tree(rows) for type_id, rows in by_type.items()}
    modes = {type_id: max(Counter(rows).items(),
                          key=lambda item: (item[1], repr(item[0])))[0]
             for type_id, rows in by_type.items()}

    enumeration = enumerate_frozen_port_occurrences(
        geometry, tuple("*" for _ in eval_positions), eval_positions)
    eval_rows = _decorations(
        geometry, eval_species, eval_positions, enumeration.occurrences,
        enumeration.occurrence_supports)
    actual = []
    modal = []
    factor = []
    unseen = unseen_exact = 0
    alternatives = {type_id: set(rows) for type_id, rows in by_type.items()}
    for type_id, decoration in eval_rows:
        predicted = _predict(models[type_id])
        actual.append(decoration)
        modal.append(modes[type_id])
        factor.append(predicted)
        if predicted not in alternatives[type_id]:
            unseen += 1
            unseen_exact += predicted == decoration
    modal_exact, modal_sites, total_sites = _scores(actual, modal)
    factor_exact, factor_sites, _ = _scores(actual, factor)
    covered = {atom for _occurrence, support in
               enumeration.occurrence_supports for atom in support}
    train_nn = tuple(min(math.dist(point, other)
                         for other_index, other in enumerate(train_positions)
                         if other_index != index)
                     for index, point in enumerate(train_positions))
    nn_scale = median(train_nn)
    train_features = _gap_features(
        train_positions, geometry.occurrences, len(geometry.prototypes),
        nn_scale)
    eval_features = _gap_features(
        eval_positions, enumeration.occurrences, len(geometry.prototypes),
        nn_scale)
    ordered = tuple(sorted(range(len(train_positions)),
                           key=lambda index: train_positions[index][0]))
    folds = tuple(tuple(ordered[
        fold * len(ordered) // 5:(fold + 1) * len(ordered) // 5])
                  for fold in range(5))
    knn_scores = []
    for neighbors in (1, 3, 5, 9, 15):
        correct = total = 0
        for validation in folds:
            validation_set = set(validation)
            fit_ids = tuple(index for index in range(len(train_positions))
                            if index not in validation_set)
            fit_raw = tuple(train_features[index] for index in fit_ids)
            validation_raw = tuple(train_features[index]
                                   for index in validation)
            fit, transformed_validation = _standardize(
                fit_raw, validation_raw)
            predicted = _knn(
                fit, tuple(train_species[index] for index in fit_ids),
                transformed_validation, neighbors)
            correct += sum(label == train_species[index]
                           for label, index in zip(predicted, validation))
            total += len(validation)
        knn_scores.append((correct / total, -neighbors, neighbors))
    cv_accuracy, _negative_neighbors, selected_neighbors = max(knn_scores)
    standardized_train, standardized_eval = _standardize(
        train_features, eval_features)
    eval_predictions = _knn(
        standardized_train, train_species, standardized_eval,
        selected_neighbors)
    residual = tuple(sorted(set(range(len(eval_positions))) - covered))
    gap_correct = sum(eval_predictions[index] == eval_species[index]
                      for index in residual)
    gap_accuracy = gap_correct / max(1, len(residual))
    gap_species = Counter(eval_species[index] for index in residual)
    gap_predicted = Counter(eval_predictions[index] for index in residual)
    gap_confusion = Counter((eval_species[index], eval_predictions[index])
                            for index in residual)
    exact_accuracy = factor_exact / max(1, len(actual))
    site_accuracy = factor_sites / max(1, total_sites)
    decoration_gate = exact_accuracy >= .9 and site_accuracy >= .99
    gate = decoration_gate and gap_accuracy >= .99
    return CdYbPartialDecorationAudit(
        len(TRAIN_CENTERS), len(train_ids), len(eval_ids),
        min(math.dist(center, EVAL_CENTER) for center in TRAIN_CENTERS),
        not set(train_ids).intersection(eval_ids), len(geometry.prototypes),
        len(geometry.occurrences), len(enumeration.occurrences), len(covered),
        len(covered) / max(1, len(eval_ids)),
        sum(len(set(rows)) for rows in by_type.values()),
        modal_exact / max(1, len(actual)), exact_accuracy,
        modal_sites / max(1, total_sites), site_accuracy, unseen, unseen_exact,
        factor_exact > modal_exact, factor_sites > modal_sites,
        len(residual), selected_neighbors, cv_accuracy, gap_correct,
        gap_accuracy, tuple(sorted(gap_species.items())),
        tuple(sorted(gap_predicted.items())),
        tuple(sorted((actual, predicted, count)
                     for (actual, predicted), count in gap_confusion.items())),
        len(covered) + len(residual) == len(eval_positions),
        False, False, decoration_gate, gate,
        "The published cut-and-project oracle constructs two disjoint crops, "
        "but the learner receives only positions/species. This scores frozen "
        "geometry/decorations and bounded singleton-gap markings on supplied "
        "coordinates; it is not autonomous growth.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
