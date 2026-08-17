#!/usr/bin/env python3
"""Nested candidate-level linear marking over joint incidence score geometry.

For every outer held-out nucleus, base token sections for the other nuclei are
cross-fitted once more before training this candidate-level section.  Thus no
candidate label from the outer nucleus, and no in-sample base score from a
meta-training nucleus, enters selection.  Exact candidate geometry is fixed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_frontier_band_marking import (
    BandTrainingExample, _fit, score_band)
from materials_gcts_incidence_token_marking import (
    score_incidence_descriptor, score_incidence_descriptor_by_channel)
from materials_gcts_iqc_incidence_geometry_selection import (
    _fit_from_groups, _ranked_antichain, _statistics)
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER, _development_groups)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


FEATURE_NAMES = (
    "detailed_score", "channel_score", "score_difference",
    "absolute_score_difference", "detailed_z", "channel_z",
    "detailed_inverse_rank", "channel_inverse_rank",
    "detailed_relative_rank", "channel_relative_rank",
    "log_detailed_orbit", "log_channel_orbit", "log_token_count",
    "log_family_count", "weighted_token_fraction")
RIDGES = (.1, 1., 10.)
TRAINING_ROWS_PER_LABEL_PER_GROUP = 64
FIT_STEPS = 240


@dataclass(frozen=True)
class RidgeAudit:
    ridge: float
    correct_by_group: tuple[int, ...]
    selected_actions: int
    correct_actions: int
    false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class JointIncidenceLinearPreflight:
    development_groups: int
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    feature_names: tuple[str, ...]
    ridges: tuple[float, ...]
    training_rows_per_label_per_group: int
    fit_steps: int
    candidate_graph_digest: str
    feature_digest: str
    ridge_audits: tuple[RidgeAudit, ...]
    selected_ridge: float
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    outer_labels_used_for_fit_or_selection: bool
    exact_candidate_geometry_changed: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _rank_map(values):
    levels = sorted(set(values), reverse=True)
    return {value: index + 1 for index, value in enumerate(levels)}, len(levels)


def _features(marking, rows):
    detailed = tuple(score_incidence_descriptor(
        marking, row.descriptor) for row in rows)
    channel = tuple(score_incidence_descriptor_by_channel(
        marking, row.descriptor) for row in rows)
    detailed_rank, detailed_levels = _rank_map(detailed)
    channel_rank, channel_levels = _rank_map(channel)
    detailed_count = Counter(detailed)
    channel_count = Counter(channel)

    def moments(values):
        mean = sum(values) / len(values)
        scale = max(1e-12, math.sqrt(sum(
            (value - mean) ** 2 for value in values) / len(values)))
        return mean, scale

    detailed_mean, detailed_scale = moments(detailed)
    channel_mean, channel_scale = moments(channel)
    result = []
    for row, first, second in zip(rows, detailed, channel):
        tokens = row.descriptor.tokens
        families = {token[0] if isinstance(token, tuple) and token else token
                    for token in tokens}
        weighted = sum(token in marking.token_weights for token in tokens) / \
            max(1, len(tokens))
        first_rank = detailed_rank[first]
        second_rank = channel_rank[second]
        result.append((
            first, second, first - second, abs(first - second),
            (first - detailed_mean) / detailed_scale,
            (second - channel_mean) / channel_scale,
            1. / first_rank, 1. / second_rank,
            first_rank / detailed_levels, second_rank / channel_levels,
            math.log1p(detailed_count[first]),
            math.log1p(channel_count[second]), math.log1p(len(tokens)),
            math.log1p(len(families)), weighted))
    return tuple(result)


def _balanced_examples(group, rows, features):
    paired = tuple(zip(rows, features))
    positive = sorted((item for item in paired if item[0].successful),
                      key=lambda item: (item[0].point, item[0].color))
    negative = sorted((item for item in paired if not item[0].successful),
                      key=lambda item: (-max(item[1][0], item[1][1]),
                                        item[0].point, item[0].color))
    selected = (positive[:TRAINING_ROWS_PER_LABEL_PER_GROUP] +
                negative[:TRAINING_ROWS_PER_LABEL_PER_GROUP])
    return tuple(BandTrainingExample(
        group, feature, row.successful, 1) for row, feature in selected)


def evaluate() -> JointIncidenceLinearPreflight:
    groups = _development_groups()
    statistics = _statistics(groups)
    selected_by_ridge = {ridge: [] for ridge in RIDGES}
    all_feature_rows = []
    for outer_index, heldout in enumerate(groups):
        train_indices = tuple(index for index in range(len(groups))
                              if index != outer_index)
        examples = []
        for inner_index in train_indices:
            base = _fit_from_groups(statistics, tuple(
                index for index in train_indices if index != inner_index))
            feature_rows = _features(base, groups[inner_index])
            examples.extend(_balanced_examples(
                groups[inner_index][0].group, groups[inner_index],
                feature_rows))
        held_base = _fit_from_groups(statistics, train_indices)
        held_features = _features(held_base, heldout)
        all_feature_rows.extend((outer_index, row.point, feature)
                                for row, feature in zip(
                                    heldout, held_features))
        for ridge in RIDGES:
            marker = _fit(tuple(examples), ridge, FEATURE_NAMES,
                          steps=FIT_STEPS)
            scored = tuple((score_band(marker, feature), row)
                           for row, feature in zip(heldout, held_features))
            selected_by_ridge[ridge].append(_ranked_antichain(
                scored, ACTIONS_PER_NUCLEUS))

    audits = []
    for ridge in RIDGES:
        correct = tuple(sum(row.successful for row in selected)
                        for selected in selected_by_ridge[ridge])
        total = sum(map(len, selected_by_ridge[ridge]))
        correct_total = sum(correct)
        audits.append(RidgeAudit(
            ridge, correct, total, correct_total, total - correct_total,
            correct_total / total if total else 0.,
            sum(count == ACTIONS_PER_NUCLEUS for count in correct)))
    chosen = max(audits, key=lambda row: (
        row.exact_groups, row.correct_actions, row.precision, row.ridge))
    passed = bool(
        chosen.selected_actions == ACTIONS_PER_NUCLEUS * len(groups) and
        chosen.correct_actions == chosen.selected_actions and
        chosen.exact_groups == len(groups))
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for group in groups for row in group)).encode()).hexdigest()
    feature_digest = hashlib.sha256(repr(tuple(all_feature_rows)).encode()).hexdigest()
    return JointIncidenceLinearPreflight(
        len(groups), tuple(map(len, groups)),
        tuple(sum(row.successful for row in group) for group in groups),
        FEATURE_NAMES, RIDGES, TRAINING_ROWS_PER_LABEL_PER_GROUP, FIT_STEPS,
        graph_digest, feature_digest, tuple(audits), chosen.ridge,
        chosen.correct_by_group, chosen.selected_actions,
        chosen.correct_actions, chosen.false_actions, chosen.precision,
        chosen.exact_groups, False, False, NEXT_CONFIRMATION_CENTER, False,
        passed,
        ("joint incidence linear section passes ten-nucleus development"
         if passed else
         "joint incidence linear section remains below the development gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
