#!/usr/bin/env python3
"""Causal inward-port marking for frozen IQC outward productions."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_guarded_production_atlas import (
    _level_labels, _production_fingerprint, _sample)
from materials_gcts_guarded_radial_hierarchy import (
    _radius, fit_guarded_radial_hierarchy)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch_fast


@dataclass(frozen=True)
class CausalPortLevel:
    level: int
    heldout_parents: int
    supported_contexts: int
    context_coverage: float
    parent_only_exact: int
    marked_exact: int
    shuffled_best_exact: int
    shuffled_median_exact: float
    marked_beats_all_shuffles: bool


@dataclass(frozen=True)
class CausalPortBenchmark:
    training_atoms: int
    heldout_atoms: int
    sample_limit: int
    shuffle_trials: int
    levels: Tuple[CausalPortLevel, ...]
    incoming_context_uses_only_smaller_radius_atoms: bool
    heldout_geometry_used_for_fitting: bool
    level_one_marking_effect: bool
    all_levels_transfer: bool
    benchmark_passed: bool


def _quantize(value, unit):
    return round(value / max(1e-12, unit * .08))


def _incoming_context(points, labels, support, center, unit):
    """Bounded port multiset visible before an outward radial placement."""
    center_radius = _radius(points[center])
    ports = Counter(
        (labels[index], _quantize(math.dist(points[center], points[index]), unit))
        for index in support
        if index != center and _radius(points[index]) < center_radius - 1e-9)
    return tuple(sorted(ports.items()))


def _outward_production(points, labels, support, center, unit):
    center_radius = _radius(points[center])
    outward = tuple(index for index in support if
                    index == center or
                    _radius(points[index]) >= center_radius - 1e-9)
    return _production_fingerprint(points, labels, outward, center, unit)


def _modal(counter):
    return max(counter.items(), key=lambda item: (item[1], repr(item[0])))[0]


def evaluate(sample_limit=2048, shuffle_trials=30):
    training_radius = 35.0
    heldout_radius = 9.0 * HIDDEN_UNIT ** 4
    training, _ = oracle_patch_fast(11, training_radius)
    heldout, _ = oracle_patch_fast(19, heldout_radius)
    encoder = fit_guarded_radial_hierarchy(training, training_radius)
    training_levels = _level_labels(training, encoder)
    heldout_levels = _level_labels(heldout, encoder)
    reports = []
    for level, training_encoded, heldout_encoded in zip(
            encoder.levels, training_levels, heldout_levels):
        child_labels, parent_labels, spatial = training_encoded
        heldout_children, heldout_parents, heldout_spatial = heldout_encoded
        training_indices = _sample(tuple(
            index for index, point in enumerate(training.positions)
            if _radius(point) <=
            training_radius - level.dependency_radius - 1e-9), sample_limit)
        heldout_indices = _sample(tuple(
            index for index, point in enumerate(heldout.positions)
            if training_radius + level.dependency_radius + 1e-9 <=
            _radius(point) <=
            heldout_radius - level.dependency_radius - 1e-9), sample_limit)
        rows = []
        parent_only = defaultdict(Counter)
        marked = defaultdict(Counter)
        for center in training_indices:
            support = tuple(index for _, index in
                            spatial.within(center, level.radius))
            context = _incoming_context(
                training.positions, child_labels, support, center,
                encoder.length_unit)
            production = _outward_production(
                training.positions, child_labels, support, center,
                encoder.length_unit)
            parent = parent_labels[center]
            rows.append((parent, context, production))
            parent_only[parent][production] += 1
            marked[(parent, context)][production] += 1
        cases = []
        for center in heldout_indices:
            support = tuple(index for _, index in
                            heldout_spatial.within(center, level.radius))
            context = _incoming_context(
                heldout.positions, heldout_children, support, center,
                encoder.length_unit)
            production = _outward_production(
                heldout.positions, heldout_children, support, center,
                encoder.length_unit)
            parent = heldout_parents[center]
            if (parent, context) in marked:
                cases.append((parent, context, production))
        baseline_exact = sum(
            _modal(parent_only[parent]) == production
            for parent, _, production in cases)
        marked_exact = sum(
            _modal(marked[(parent, context)]) == production
            for parent, context, production in cases)
        shuffled_scores = []
        grouped_rows = defaultdict(list)
        for parent, context, production in rows:
            grouped_rows[parent].append((context, production))
        for seed in range(shuffle_trials):
            rng = random.Random(seed)
            shuffled = defaultdict(Counter)
            for parent, group in grouped_rows.items():
                productions = [production for _, production in group]
                rng.shuffle(productions)
                for (context, _), production in zip(group, productions):
                    shuffled[(parent, context)][production] += 1
            shuffled_scores.append(sum(
                _modal(shuffled[(parent, context)]) == production
                for parent, context, production in cases))
        ordered = sorted(shuffled_scores)
        median = (ordered[len(ordered) // 2] if len(ordered) % 2 else
                  (ordered[len(ordered) // 2 - 1] +
                   ordered[len(ordered) // 2]) / 2)
        reports.append(CausalPortLevel(
            level.level, len(heldout_indices), len(cases),
            len(cases) / max(1, len(heldout_indices)), baseline_exact,
            marked_exact, max(shuffled_scores, default=0), median,
            marked_exact > max(shuffled_scores, default=0)))
    level_one_effect = bool(reports and reports[0].marked_beats_all_shuffles)
    all_levels = all(report.supported_contexts > 0 and
                     report.marked_beats_all_shuffles for report in reports)
    return CausalPortBenchmark(
        len(training.positions), len(heldout.positions), sample_limit,
        shuffle_trials, tuple(reports), True, False, level_one_effect,
        all_levels, all_levels)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=2048)
    parser.add_argument("--shuffle-trials", type=int, default=30)
    arguments = parser.parse_args()
    result = evaluate(arguments.sample_limit, arguments.shuffle_trials)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
