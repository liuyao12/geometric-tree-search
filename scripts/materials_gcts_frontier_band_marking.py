#!/usr/bin/env python3
"""Fit a bounded, target-free marking over whole frontier score bands."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence


BAND_FEATURE_NAMES = (
    "site_score",
    "score_below_frontier_maximum",
    "score_z_within_frontier",
    "inverse_rank",
    "relative_rank",
    "log_band_sites",
    "log_frontier_sites",
    "mean_log_votes",
    "mean_source_color_purity",
    "mean_target_color_purity",
    "mean_log_state_multiplicity",
    "mean_state_purity",
    "mean_state_entropy",
    "mean_log_parent_multiplicity",
    "mean_parent_purity",
)


@dataclass(frozen=True)
class FrontierBand:
    rank: int
    score: float
    positions: tuple[tuple[float, float, float], ...]
    features: tuple[float, ...]


@dataclass(frozen=True)
class BandTrainingExample:
    group: Hashable
    features: tuple[float, ...]
    successful: bool
    emitted_sites: int


@dataclass(frozen=True)
class FrozenFrontierBandMarker:
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    ridge: float


@dataclass(frozen=True)
class BandMarkerAudit:
    groups: int
    examples: int
    positives: int
    ridge: float
    out_of_fold_logloss: float
    minimum_precision: float
    threshold: float
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    selected_correct_sites: int


def _purity(counter) -> float:
    total = sum(counter.values())
    return max(counter.values(), default=0) / total if total else 0.


def _entropy(counter) -> float:
    total = sum(counter.values())
    if not total:
        return 0.
    return -sum((count / total) * math.log(count / total)
                for count in counter.values() if count)


def frontier_score_bands(proposals, scores: Mapping, *, maximum_bands=24):
    """Describe the highest whole score bands without using target labels."""
    if maximum_bands < 1 or not scores:
        return ()
    levels = sorted(set(float(value) for value in scores.values()),
                    reverse=True)
    # A canonical summation order keeps the descriptor independent of mapping
    # insertion order down to the serialized floating-point payload.
    values = tuple(sorted(float(value) for value in scores.values()))
    mean = sum(values) / len(values)
    scale = max(1e-12, math.sqrt(sum((value - mean) ** 2
                                    for value in values) / len(values)))
    total_bands = len(levels)
    result = []
    for rank, level in enumerate(levels[:maximum_bands], 1):
        band = tuple(sorted(point for point, value in scores.items()
                            if abs(value - level) <= 1e-12))
        vote_counts = tuple(proposals.votes[point] for point in band)
        source = tuple(proposals.color_votes.get(point, {}) for point in band)
        target = tuple(proposals.target_color_votes.get(point, {})
                       for point in band)
        states = tuple(proposals.state_votes.get(point, {}) for point in band)
        parents = tuple(proposals.parent_votes.get(point, {}) for point in band)

        def average(rows, function):
            return sum(function(row) for row in rows) / max(1, len(rows))

        features = (
            level,
            level - levels[0],
            (level - mean) / scale,
            1. / rank,
            rank / total_bands,
            math.log1p(len(band)),
            math.log1p(len(scores)),
            sum(math.log1p(count) for count in vote_counts) /
            max(1, len(vote_counts)),
            average(source, _purity),
            average(target, _purity),
            average(states, lambda row: math.log1p(sum(row.values()))),
            average(states, _purity),
            average(states, _entropy),
            average(parents, lambda row: math.log1p(sum(row.values()))),
            average(parents, _purity),
        )
        result.append(FrontierBand(rank, level, band, features))
    return tuple(result)


def _sigmoid(value):
    if value >= 0:
        inverse = math.exp(-min(value, 50.))
        return 1. / (1. + inverse)
    exponential = math.exp(max(value, -50.))
    return exponential / (1. + exponential)


def _fit(examples: Sequence[BandTrainingExample], ridge: float,
         feature_names: Sequence[str], *, steps=600):
    if not examples or ridge <= 0:
        raise ValueError("band marking needs examples and positive ridge")
    names = tuple(feature_names)
    width = len(names)
    if not names or len(set(names)) != width:
        raise ValueError("band feature names must be nonempty and unique")
    if any(len(row.features) != width for row in examples):
        raise ValueError("band feature rows do not match the frozen schema")
    means = tuple(sum(row.features[index] for row in examples) / len(examples)
                  for index in range(width))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (row.features[index] - means[index]) ** 2 for row in examples) /
        len(examples))) for index in range(width))
    normalized = tuple((tuple(
        (row.features[index] - means[index]) / scales[index]
        for index in range(width)), float(row.successful)) for row in examples)
    positives = sum(row.successful for row in examples)
    intercept = math.log((positives + 1) / (len(examples) - positives + 1))
    weights = [0.] * width
    first = [0.] * width
    second = [0.] * width
    intercept_first = intercept_second = 0.
    for step in range(1, steps + 1):
        gradients = [0.] * width
        gradient0 = 0.
        for features, label in normalized:
            probability = _sigmoid(intercept + sum(
                weight * value for weight, value in zip(weights, features)))
            error = probability - label
            gradient0 += error
            for index, value in enumerate(features):
                gradients[index] += error * value
        inverse = 1. / len(normalized)
        gradient0 *= inverse
        gradients = [value * inverse + ridge * weights[index] * inverse
                     for index, value in enumerate(gradients)]
        beta_one, beta_two, rate = .9, .999, .04
        intercept_first = beta_one * intercept_first + (1 - beta_one) * gradient0
        intercept_second = beta_two * intercept_second + \
            (1 - beta_two) * gradient0 ** 2
        intercept -= rate * (intercept_first / (1 - beta_one ** step)) / (
            math.sqrt(intercept_second / (1 - beta_two ** step)) + 1e-8)
        for index, gradient in enumerate(gradients):
            first[index] = beta_one * first[index] + (1 - beta_one) * gradient
            second[index] = beta_two * second[index] + \
                (1 - beta_two) * gradient ** 2
            weights[index] -= rate * (first[index] /
                (1 - beta_one ** step)) / (math.sqrt(second[index] /
                (1 - beta_two ** step)) + 1e-8)
    return FrozenFrontierBandMarker(
        names, means, scales, tuple(weights), intercept, ridge)


def score_band(marker: FrozenFrontierBandMarker, features) -> float:
    if not marker.feature_names or len(features) != len(marker.feature_names):
        raise ValueError("band marker schema mismatch")
    normalized = tuple((value - mean) / scale for value, mean, scale in
                       zip(features, marker.means, marker.scales))
    return _sigmoid(marker.intercept + sum(
        weight * value for weight, value in zip(marker.weights, normalized)))


def _logloss(examples, scores):
    return -sum(math.log(max(1e-12, score if row.successful else 1 - score))
                for row, score in zip(examples, scores)) / len(examples)


def fit_grouped_band_marker(examples: Sequence[BandTrainingExample], *,
                            ridges=(.01, .1, 1., 10.),
                            minimum_precision=.95,
                            feature_names=BAND_FEATURE_NAMES,
                            fit_steps=600):
    """Fit with group-heldout ridge selection and a frozen OOF threshold."""
    examples = tuple(examples)
    feature_names = tuple(feature_names)
    groups = tuple(sorted({row.group for row in examples}, key=repr))
    if (len(groups) < 3 or not 0. < minimum_precision <= 1. or
            fit_steps < 50 or
            not any(row.successful for row in examples) or
            all(row.successful for row in examples)):
        raise ValueError("band marking needs three groups and both outcomes")
    candidates = []
    for ridge in ridges:
        fold_losses = []
        for group in groups:
            training = tuple(row for row in examples if row.group != group)
            heldout = tuple(row for row in examples if row.group == group)
            marker = _fit(training, ridge, feature_names, steps=fit_steps)
            fold_losses.append(_logloss(
                heldout, tuple(score_band(marker, row.features)
                               for row in heldout)))
        candidates.append((sum(fold_losses) / len(fold_losses), ridge))
    loss, ridge = min(candidates)
    scored = []
    for group in groups:
        training = tuple(row for row in examples if row.group != group)
        marker = _fit(training, ridge, feature_names, steps=fit_steps)
        scored.extend((row, score_band(marker, row.features))
                      for row in examples if row.group == group)
    feasible = []
    for threshold in sorted({score for _row, score in scored}, reverse=True):
        selected = tuple(row for row, score in scored
                         if score >= threshold - 1e-15)
        false = sum(not row.successful for row in selected)
        correct = sum(row.successful for row in selected)
        correct_sites = sum(row.emitted_sites for row in selected
                            if row.successful)
        precision = correct / len(selected) if selected else 0.
        if correct and precision >= minimum_precision:
            feasible.append((correct_sites, correct, precision,
                             threshold, len(selected)))
    if feasible:
        correct_sites, correct, _precision, threshold, selected = max(feasible)
    else:
        correct_sites = correct = selected = 0
        threshold = float("inf")
    final = _fit(examples, ridge, feature_names, steps=fit_steps)
    return final, BandMarkerAudit(
        len(groups), len(examples), sum(row.successful for row in examples),
        ridge, loss, minimum_precision, threshold, selected, correct,
        selected - correct,
        correct_sites)
