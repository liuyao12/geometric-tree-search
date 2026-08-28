#!/usr/bin/env python3
"""Train-only site-resolved confidence section for Cd--Yb completions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import RADIUS, TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    PACK_SEPARATION, _pack, _window_ids)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_iqc_reclustered_transfer_audit import _frozen_heldout_program
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_derivation import _site_key
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_oriented_overlap_ports import matmul, matvec
from materials_gcts_partial_completion_marking import freeze_completion_candidate
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


SEED_RADIUS = 7.
SEED_RADII = (.4 * RADIUS, .5 * RADIUS, .6 * RADIUS)
LAMBDAS = (.01, .1, 1., 10.)
AGGREGATIONS = ("minimum", "lower-quartile", "mean")
ZERO_ERROR_LOGIT_MARGINS = (0., .1, .25, .5, .75, 1., 1.5, 2.)
FEATURE_NAMES = (
    "same_species_fraction", "rhs_radial_distance_nn",
    "nearest_seed_distance_nn", "nearest_witness_distance_nn",
    "nearest_emitted_distance_nn", "rhs_local_neighbors",
    "child_site_multiplicity", "matched_child_fraction",
    "missing_children", "log_port_evidence")


@dataclass(frozen=True)
class FrozenSiteSection:
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    ridge_lambda: float
    whole_action_aggregation: str
    site_acceptance_threshold: float
    target_used: bool
    candidate_id_or_global_coordinate_feature_used: bool


@dataclass(frozen=True)
class SiteSectionAudit:
    train_windows: int
    shifted_frontiers: int
    seed_radii: tuple[float, ...]
    frozen_macro_candidates: int
    site_samples: int
    supported_sites: int
    unsupported_sites: int
    exact_actions: int
    mixed_or_wrong_actions: int
    feature_count: int
    grouped_outer_folds: int
    outer_site_logloss: float
    outer_site_auc: float
    outer_action_logloss: float
    outer_action_auc: float
    outer_aggregation_by_fold: tuple[str, ...]
    outer_site_threshold_by_fold: tuple[float, ...]
    outer_site_precision_by_fold: tuple[float, ...]
    outer_site_recall_by_fold: tuple[float, ...]
    outer_site_accepted_by_fold: tuple[int, ...]
    outer_site_threshold_precision: float
    outer_site_threshold_recall: float
    outer_site_threshold_accepted: int
    final_ridge_lambda: float
    final_action_aggregation: str
    final_site_acceptance_threshold: float
    final_threshold_oof_precision: float
    final_threshold_oof_recall: float
    final_threshold_oof_accepted: int
    nonempty_95_precision_threshold_found: bool
    group_refit_threshold_rule: str
    group_refit_outer_precision: float
    group_refit_outer_recall: float
    group_refit_outer_accepted: int
    group_refit_outer_correct: int
    group_refit_outer_precision_by_fold: tuple[float, ...]
    group_refit_outer_recall_by_fold: tuple[float, ...]
    group_refit_outer_accepted_by_fold: tuple[int, ...]
    group_refit_minimum_nonempty_fold_precision: float
    group_refit_nonempty_folds: int
    group_refit_null_correct_best: int
    group_refit_correct_empirical_p: float
    group_refit_selector_passed: bool
    group_refit_rule_exploratory_not_confirmatory: bool
    future_confirmatory_target_opened: bool
    selected_zero_error_logit_margin: float
    fixed_margin_outer_precision: float
    fixed_margin_outer_recall: float
    fixed_margin_minimum_nonempty_fold_precision: float
    fixed_margin_nonempty_folds: int
    fully_nested_margin_selection_precision: float
    fully_nested_margin_selection_recall: float
    fully_nested_margin_selection_passed: bool
    null_trials: int
    null_site_auc_median: float
    null_site_auc_best: float
    null_action_auc_median: float
    null_action_auc_best: float
    site_auc_empirical_p: float
    action_auc_empirical_p: float
    corpus_digest: str
    frozen_section_digest: str
    site_corpus_digest: str
    serialized_frozen_section: str
    model_manifest_digest: str
    frozen_section: FrozenSiteSection
    all_fit_and_selection_data_from_five_training_windows: bool
    confirmatory_or_prior_eval_nucleus_used: bool
    candidate_geometry_or_ids_changed: bool


@dataclass(frozen=True)
class _SiteRow:
    window: int
    candidate_id: str
    site_key: tuple
    features: tuple[float, ...]
    successful: bool


def score_site_confidence(section: FrozenSiteSection,
                          features: tuple[float, ...]) -> float:
    """Apply the frozen local section to one already-enumerated emitted site."""
    if len(features) != len(section.feature_names):
        raise ValueError("site feature dimension does not match frozen section")
    return _sigmoid(section.intercept + sum(
        weight * (value - mean) / scale
        for weight, value, mean, scale in zip(
            section.weights, features, section.means, section.scales)))


def aggregate_action_confidence(section: FrozenSiteSection,
                                site_confidences: tuple[float, ...]) -> float:
    """Aggregate emitted-site marks without modifying the macro candidate."""
    if not site_confidences:
        raise ValueError("an action must emit at least one scored site")
    return _aggregate(site_confidences, section.whole_action_aggregation)


def _add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def _render(prototype, rotation, translation):
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _parent_map(quotient, promoted):
    parent = {macro_id: prototype_id for prototype_id, macro_id
              in promoted.prototype_macro_types}
    result = []
    cursor = 0
    for geometry in quotient.derivation_classes:
        for _alternative in geometry.alternatives:
            macro = quotient.alternative_macros[cursor]
            result.append((macro.macro_id, parent[geometry.geometry_class_id]))
            cursor += 1
    return tuple(result)


def _distance(point, sites, scale):
    return min((math.dist(point, other) / scale for _species, other in sites),
               default=20.)


def _site_features(site, emitted_sites, seed_sites, witness_sites,
                   full_sites, child_site_counts, completion, macro,
                   candidate, scale):
    species, point = site
    centroid = tuple(sum(other[axis] for _label, other in full_sites) /
                     len(full_sites) for axis in range(3))
    same_species = (sum(label == species for label, _other in full_sites) /
                    len(full_sites))
    other_emitted = tuple(other for other in emitted_sites
                          if _site_key(other, .03) != _site_key(site, .03))
    neighbors = sum(0 < math.dist(point, other) <= 1.6 * scale
                    for _label, other in full_sites)
    return (
        same_species, math.dist(point, centroid) / scale,
        _distance(point, seed_sites, scale),
        _distance(point, witness_sites, scale),
        _distance(point, other_emitted, scale), float(neighbors),
        float(child_site_counts.get(_site_key(site, .03), 1)),
        len(completion.matched_nodes) / len(macro.child_placements),
        float(len(completion.missing_children)),
        math.log1p(candidate.descriptor.training_port_evidence))


def _frontier_rows(primitive, quotient, parent_map, species, positions,
                   namespaces, patch, seed_center,
                   seed_radius=SEED_RADIUS):
    indices = tuple(index for index, point in enumerate(positions)
                    if namespaces[index] == patch and
                    math.dist(point, seed_center) <= seed_radius + 1e-10)
    seed_species = tuple(species[index] for index in indices)
    seed_positions = tuple(positions[index] for index in indices)
    seed_sites = tuple(zip(seed_species, seed_positions))
    enumeration = enumerate_frozen_port_occurrences(
        primitive, seed_species, seed_positions)
    lower = _frozen_heldout_program(primitive, enumeration)
    frontier = enumerate_partial_promoted_completions(
        lower, quotient.alternative_macros, minimum_matched_children=1,
        minimum_child_coverage=.5, explicit_seed_sites=seed_sites,
        public_boundary=ExecutionBoundary(
            (patch * PACK_SEPARATION, 0., 0.), RADIUS),
        frozen_parent_types=parent_map)
    macros = {item.macro_id: item for item in quotient.alternative_macros}
    prototypes = {item.type_id: item for item in primitive.prototypes}
    target = {_site_key((species[index], positions[index]), .03)
              for index, value in enumerate(namespaces) if value == patch}
    seed_keys = {_site_key(site, .03) for site in seed_sites}
    rows = []
    for completion in frontier.completions:
        macro = macros[completion.macro_id]
        candidate = freeze_completion_candidate(
            lower, macro, completion,
            live_overlap_support=len(completion.matched_occurrence_ids),
            live_collision_support=0)
        rendered_children = []
        for placement in macro.child_placements:
            rotation = matmul(completion.macro_rotation, placement.rotation)
            translation = _add(completion.macro_translation, matvec(
                completion.macro_rotation, placement.translation))
            rendered_children.append((placement.node, _render(
                prototypes[placement.cluster_type], rotation, translation)))
        full_sites = tuple({ _site_key(site, .03): site
                           for _node, sites in rendered_children
                           for site in sites}.values())
        witness_nodes = set(completion.matched_nodes)
        witness_sites = tuple(site for node, sites in rendered_children
                              if node in witness_nodes for site in sites)
        emitted_sites = tuple({
            _site_key(site, .03): site
            for child in completion.missing_children for site in child.sites
            if _site_key(site, .03) not in seed_keys}.values())
        multiplicity = {}
        for _node, child_sites in rendered_children:
            for child_site in child_sites:
                key = _site_key(child_site, .03)
                multiplicity[key] = multiplicity.get(key, 0) + 1
        for emitted in emitted_sites:
            key = _site_key(emitted, .03)
            rows.append(_SiteRow(
                patch, candidate.candidate_id, key,
                _site_features(
                    emitted, emitted_sites, seed_sites, witness_sites,
                    full_sites, multiplicity, completion, macro, candidate,
                    lower.minimum_distance), key in target))
    return tuple(rows)


def _dedupe(rows):
    selected = {}
    for row in rows:
        key = row.window, row.candidate_id, row.site_key
        if key in selected and selected[key].successful != row.successful:
            raise AssertionError("site label changed across train seed shifts")
        selected.setdefault(key, row)
    return tuple(selected[key] for key in sorted(selected, key=repr))


def _sigmoid(value):
    value = max(-50., min(50., value))
    return 1 / (1 + math.exp(-value))


def _fit(rows, ridge):
    columns = tuple(zip(*(row.features for row in rows)))
    means = tuple(sum(column) / len(column) for column in columns)
    scales = tuple(max(1e-9, math.sqrt(sum((value - mean) ** 2
                                          for value in column) / len(column)))
                   for column, mean in zip(columns, means))
    data = tuple(tuple((value - mean) / scale for value, mean, scale in
                       zip(row.features, means, scales)) for row in rows)
    positive = tuple(item for item, row in zip(data, rows) if row.successful)
    negative = tuple(item for item, row in zip(data, rows)
                     if not row.successful)
    if not positive or not negative:
        return (means, scales, (0.,) * len(FEATURE_NAMES),
                math.log((len(positive) + 1) / (len(negative) + 1)))
    positive_means = tuple(sum(item[index] for item in positive) /
                           len(positive) for index in range(len(FEATURE_NAMES)))
    negative_means = tuple(sum(item[index] for item in negative) /
                           len(negative) for index in range(len(FEATURE_NAMES)))
    variances = tuple(
        (sum((item[index] - positive_means[index]) ** 2
             for item in positive) +
         sum((item[index] - negative_means[index]) ** 2
             for item in negative)) / max(1, len(rows) - 2)
        for index in range(len(FEATURE_NAMES)))
    denominators = tuple(variance + ridge for variance in variances)
    weights = tuple((left - right) / denominator for left, right, denominator
                    in zip(positive_means, negative_means, denominators))
    intercept = math.log((len(positive) + 1) / (len(negative) + 1))
    intercept -= .5 * sum(
        (left ** 2 - right ** 2) / denominator
        for left, right, denominator in
        zip(positive_means, negative_means, denominators))
    return means, scales, weights, intercept


def _predict(model, row):
    means, scales, weights, intercept = model
    return _sigmoid(intercept + sum(
        weight * (value - mean) / scale for weight, value, mean, scale in
        zip(weights, row.features, means, scales)))


def _logloss(labels, scores):
    return -sum(math.log(max(score if label else 1 - score, 1e-12))
                for label, score in zip(labels, scores)) / max(1, len(labels))


def _auc(labels, scores):
    positive = [score for label, score in zip(labels, scores) if label]
    negative = [score for label, score in zip(labels, scores) if not label]
    if not positive or not negative:
        return .5
    return (sum((left > right) + .5 * (left == right)
                for left in positive for right in negative) /
            (len(positive) * len(negative)))


def _grouped_lambda(rows, excluded=None):
    windows = tuple(window for window in sorted({row.window for row in rows})
                    if window != excluded)
    choices = []
    for ridge in LAMBDAS:
        losses = []
        for held in windows:
            fit = tuple(row for row in rows
                        if row.window not in (excluded, held))
            validation = tuple(row for row in rows if row.window == held)
            if not fit or not validation:
                continue
            model = _fit(fit, ridge)
            scores = tuple(_predict(model, row) for row in validation)
            losses.append(_logloss(
                tuple(row.successful for row in validation), scores))
        choices.append((sum(losses) / len(losses), ridge))
    return min(choices)[1]


def _aggregate(values, kind):
    values = sorted(values)
    if kind == "minimum":
        return values[0]
    if kind == "lower-quartile":
        return values[(len(values) - 1) // 4]
    return sum(values) / len(values)


def _action_rows(rows, scores, aggregation):
    grouped = {}
    for row, score in zip(rows, scores):
        grouped.setdefault((row.window, row.candidate_id), []).append(
            (row.successful, score))
    return tuple((all(label for label, _score in values),
                  _aggregate(tuple(score for _label, score in values),
                             aggregation))
                 for _key, values in sorted(grouped.items()))


def _inner_site_predictions(rows, excluded):
    discovery = tuple(row for row in rows if row.window != excluded)
    predictions = []
    prediction_rows = []
    for held in range(len(TRAIN_CENTERS)):
        if held == excluded:
            continue
        fit = tuple(row for row in discovery if row.window != held)
        validation = tuple(row for row in discovery if row.window == held)
        if not fit or not validation:
            continue
        ridge = _grouped_lambda(discovery, held)
        model = _fit(fit, ridge)
        predictions.extend(_predict(model, row) for row in validation)
        prediction_rows.extend(validation)
    return tuple(prediction_rows), tuple(predictions)


def _select_aggregation(rows, excluded):
    prediction_rows, predictions = _inner_site_predictions(rows, excluded)
    choices = []
    for kind in AGGREGATIONS:
        actions = _action_rows(prediction_rows, predictions, kind)
        choices.append((_logloss(tuple(item[0] for item in actions),
                                 tuple(item[1] for item in actions)), kind))
    return min(choices)[1]


def _threshold_metrics(labels, scores, threshold):
    accepted = tuple(index for index, score in enumerate(scores)
                     if score >= threshold)
    correct = sum(labels[index] for index in accepted)
    precision = correct / len(accepted) if accepted else 1.
    positives = sum(labels)
    recall = correct / positives if positives else 0.
    return precision, recall, len(accepted), correct


def _logit(probability):
    probability = min(1 - 1e-12, max(1e-12, probability))
    return math.log(probability / (1 - probability))


def _zero_error_threshold(rows, scores, margin):
    negative_scores = tuple(score for row, score in zip(rows, scores)
                            if not row.successful)
    if not negative_scores:
        return 1.
    return _sigmoid(_logit(max(negative_scores)) + margin)


def _fixed_margin_audit(rows, margin):
    folds = []
    for held in sorted({row.window for row in rows}):
        fit = tuple(row for row in rows if row.window != held)
        validation = tuple(row for row in rows if row.window == held)
        inner_rows, inner_scores = _inner_site_predictions(rows, held)
        threshold = _zero_error_threshold(inner_rows, inner_scores, margin)
        model = _fit(fit, _grouped_lambda(rows, held))
        scores = tuple(_predict(model, row) for row in validation)
        folds.append((held, threshold) + _threshold_metrics(
            tuple(row.successful for row in validation), scores, threshold))
    accepted = sum(item[4] for item in folds)
    correct = sum(item[5] for item in folds)
    positives = sum(row.successful for row in rows)
    nonempty = tuple(item for item in folds if item[4])
    return {
        "folds": tuple(folds),
        "precision": correct / accepted if accepted else 1.,
        "recall": correct / positives if positives else 0.,
        "accepted": accepted,
        "correct": correct,
        "minimum_nonempty_precision": min(
            (item[2] for item in nonempty), default=1.),
        "nonempty_folds": len(nonempty),
    }


def _select_zero_error_margin(rows):
    required_folds = max(2, len({row.window for row in rows}) - 1)
    choices = []
    for margin in ZERO_ERROR_LOGIT_MARGINS:
        audit = _fixed_margin_audit(rows, margin)
        if (audit["accepted"] and audit["precision"] >= .95 and
                audit["minimum_nonempty_precision"] >= .95 and
                audit["nonempty_folds"] >= required_folds):
            choices.append((audit["correct"], audit["recall"], -margin,
                            margin, audit))
    return max(choices) if choices else None


def _fully_nested_margin_audit(rows):
    folds = []
    for held in sorted({row.window for row in rows}):
        discovery = tuple(row for row in rows if row.window != held)
        selection = _select_zero_error_margin(discovery)
        margin = selection[3] if selection is not None else \
            ZERO_ERROR_LOGIT_MARGINS[-1]
        calibration_rows, calibration_scores = _inner_site_predictions(
            discovery, None)
        threshold = _zero_error_threshold(
            calibration_rows, calibration_scores, margin)
        validation = tuple(row for row in rows if row.window == held)
        model = _fit(discovery, _grouped_lambda(rows, held))
        scores = tuple(_predict(model, row) for row in validation)
        folds.append((held, margin, threshold) + _threshold_metrics(
            tuple(row.successful for row in validation), scores, threshold))
    accepted = sum(item[5] for item in folds)
    correct = sum(item[6] for item in folds)
    positives = sum(row.successful for row in rows)
    return (tuple(folds), correct / accepted if accepted else 1.,
            correct / positives if positives else 0., accepted, correct)


def _group_refit_zero_error_audit(rows):
    """Cross-fit a threshold just above every fitted training negative.

    Each outer window is untouched while the ridge and discriminant are fitted
    on the other original windows.  The threshold is not a searched margin: it
    is the next representable probability above the maximum negative score in
    that fitted discovery fold.  This deliberately trades throughput for a
    finite, nonempty cross-window precision audit.
    """
    folds = []
    for held in sorted({row.window for row in rows}):
        discovery = tuple(row for row in rows if row.window != held)
        validation = tuple(row for row in rows if row.window == held)
        model = _fit(discovery, _grouped_lambda(rows, held))
        negative_scores = tuple(_predict(model, row) for row in discovery
                                if not row.successful)
        threshold = (math.nextafter(max(negative_scores), 1.)
                     if negative_scores else 1.)
        scores = tuple(_predict(model, row) for row in validation)
        folds.append((held, threshold) + _threshold_metrics(
            tuple(row.successful for row in validation), scores, threshold))
    accepted = sum(item[4] for item in folds)
    correct = sum(item[5] for item in folds)
    positives = sum(row.successful for row in rows)
    nonempty = tuple(item for item in folds if item[4])
    return {
        "folds": tuple(folds),
        "precision": correct / accepted if accepted else 1.,
        "recall": correct / positives if positives else 0.,
        "accepted": accepted,
        "correct": correct,
        "minimum_nonempty_precision": min(
            (item[2] for item in nonempty), default=1.),
        "nonempty_folds": len(nonempty),
    }


def _nested_predictions(rows):
    site_rows = []
    site_scores = []
    aggregations = []
    action_labels = []
    action_scores = []
    for held in range(len(TRAIN_CENTERS)):
        fit = tuple(row for row in rows if row.window != held)
        validation = tuple(row for row in rows if row.window == held)
        aggregation = _select_aggregation(rows, held)
        ridge = _grouped_lambda(rows, held)
        model = _fit(fit, ridge)
        scores = tuple(_predict(model, row) for row in validation)
        actions = _action_rows(validation, scores, aggregation)
        site_rows.extend(validation)
        site_scores.extend(scores)
        action_labels.extend(item[0] for item in actions)
        action_scores.extend(item[1] for item in actions)
        aggregations.append(aggregation)
    return (tuple(site_rows), tuple(site_scores), tuple(action_labels),
            tuple(action_scores), tuple(aggregations))


def _shuffle(rows, seed):
    labels = [row.successful for row in rows]
    generator = random.Random(seed)
    for window in range(len(TRAIN_CENTERS)):
        indices = [index for index, row in enumerate(rows)
                   if row.window == window]
        values = [labels[index] for index in indices]
        generator.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(_SiteRow(
        row.window, row.candidate_id, row.site_key, row.features, labels[index])
                 for index, row in enumerate(rows))


def _digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        allow_nan=False, default=repr).encode()).hexdigest()


def evaluate():
    atoms = generate_cdyb(6, (120.,) * 3)
    windows = _window_ids(atoms, TRAIN_CENTERS)
    species, positions, namespaces = _pack(atoms, TRAIN_CENTERS, windows)
    primitive = compile_irregular_port_program(species, positions)
    quotient = quotient_macro_supports(mine_port_graph_macros(
        primitive, maximum_nodes=3,
        include_boundary_relations=True).macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    parent_map = _parent_map(quotient, promoted)
    scale = primitive.cover.minimum_distance
    offsets = ((0., 0., 0.), (scale, 0., 0.), (-scale, 0., 0.),
               (0., scale, 0.), (0., -scale, 0.),
               (0., 0., scale), (0., 0., -scale))
    raw = []
    for seed_radius in SEED_RADII:
        for patch in range(len(TRAIN_CENTERS)):
            origin = (patch * PACK_SEPARATION, 0., 0.)
            for offset in offsets:
                center = tuple(origin[axis] + offset[axis]
                               for axis in range(3))
                raw.extend(_frontier_rows(
                    primitive, quotient, parent_map, species, positions,
                    namespaces, patch, center, seed_radius))
    rows = _dedupe(raw)
    (outer_rows, outer_scores, action_labels, action_scores,
     aggregations) = _nested_predictions(rows)
    final_lambda = _grouped_lambda(rows)
    final_aggregation = _select_aggregation(rows, None)
    margin_selection = _select_zero_error_margin(rows)
    selected_margin = (margin_selection[3] if margin_selection is not None
                       else ZERO_ERROR_LOGIT_MARGINS[-1])
    margin_audit = (margin_selection[4] if margin_selection is not None
                    else _fixed_margin_audit(rows, selected_margin))
    nested_margin = _fully_nested_margin_audit(rows)
    group_refit = _group_refit_zero_error_audit(rows)
    thresholds = tuple(item[2] for item in nested_margin[0])
    fold_threshold_metrics = tuple(
        (item[3], item[4], item[5], item[6])
        for item in nested_margin[0])
    means, scales, weights, intercept = _fit(rows, final_lambda)
    final_model = (means, scales, weights, intercept)
    final_negative_scores = tuple(_predict(final_model, row) for row in rows
                                  if not row.successful)
    final_threshold = (math.nextafter(max(final_negative_scores), 1.)
                       if final_negative_scores else 1.)
    section = FrozenSiteSection(
        FEATURE_NAMES, means, scales, weights, intercept, final_lambda,
        final_aggregation, final_threshold, False, False)
    null_site_auc = []
    null_action_auc = []
    null_group_refit_correct = []
    for trial in range(31):
        shuffled = _shuffle(rows, 441_901 + trial)
        (null_rows, null_scores, null_actions, null_action_scores,
         _null_agg) = _nested_predictions(shuffled)
        null_site_auc.append(_auc(
            tuple(row.successful for row in null_rows), null_scores))
        null_action_auc.append(_auc(null_actions, null_action_scores))
        null_group_refit_correct.append(
            _group_refit_zero_error_audit(shuffled)["correct"])
    site_auc = _auc(tuple(row.successful for row in outer_rows), outer_scores)
    action_auc = _auc(action_labels, action_scores)
    corpus_payload = tuple((row.window, row.candidate_id, row.site_key,
                            row.features, row.successful) for row in rows)
    site_corpus_digest = _digest(corpus_payload)
    serialized_section = json.dumps(
        asdict(section), sort_keys=True, separators=(",", ":"),
        allow_nan=False)
    manifest_payload = {
        "schema": "cdyb-site-resolved-section-v2",
        "site_corpus_digest": site_corpus_digest,
        "serialized_frozen_section": serialized_section,
        "minimum_selection_precision": .95,
        "threshold_rule": "nextafter-maximum-fitted-negative-by-original-window",
        "seed_radii": SEED_RADII,
        "zero_error_logit_margin_grid": ZERO_ERROR_LOGIT_MARGINS,
        "selected_zero_error_logit_margin_diagnostic": selected_margin,
        "group_refit_rule_selected_after_current_corpus_was_seen": True,
        "grouping": "original-training-window",
    }
    candidate_count = len({(row.window, row.candidate_id) for row in rows})
    exact_actions = sum(all(item.successful for item in rows
                            if item.window == window and
                            item.candidate_id == candidate)
                        for window, candidate in {
                            (row.window, row.candidate_id) for row in rows})
    total_threshold_accepted = sum(item[2] for item in fold_threshold_metrics)
    total_threshold_correct = sum(item[3] for item in fold_threshold_metrics)
    return SiteSectionAudit(
        train_windows=len(TRAIN_CENTERS),
        shifted_frontiers=(len(TRAIN_CENTERS) * len(offsets) *
                           len(SEED_RADII)),
        seed_radii=SEED_RADII,
        frozen_macro_candidates=candidate_count,
        site_samples=len(rows),
        supported_sites=sum(row.successful for row in rows),
        unsupported_sites=sum(not row.successful for row in rows),
        exact_actions=exact_actions,
        mixed_or_wrong_actions=candidate_count - exact_actions,
        feature_count=len(FEATURE_NAMES),
        grouped_outer_folds=len(TRAIN_CENTERS),
        outer_site_logloss=_logloss(
            tuple(row.successful for row in outer_rows), outer_scores),
        outer_site_auc=site_auc,
        outer_action_logloss=_logloss(action_labels, action_scores),
        outer_action_auc=action_auc,
        outer_aggregation_by_fold=aggregations,
        outer_site_threshold_by_fold=thresholds,
        outer_site_precision_by_fold=tuple(item[0] for item in
                                           fold_threshold_metrics),
        outer_site_recall_by_fold=tuple(item[1] for item in
                                        fold_threshold_metrics),
        outer_site_accepted_by_fold=tuple(item[2] for item in
                                          fold_threshold_metrics),
        outer_site_threshold_precision=(
            total_threshold_correct / total_threshold_accepted
            if total_threshold_accepted else 1.),
        outer_site_threshold_recall=(
            total_threshold_correct / sum(row.successful for row in outer_rows)
            if outer_rows else 0.),
        outer_site_threshold_accepted=total_threshold_accepted,
        final_ridge_lambda=final_lambda,
        final_action_aggregation=final_aggregation,
        final_site_acceptance_threshold=final_threshold,
        final_threshold_oof_precision=group_refit["precision"],
        final_threshold_oof_recall=group_refit["recall"],
        final_threshold_oof_accepted=group_refit["accepted"],
        nonempty_95_precision_threshold_found=(
            group_refit["accepted"] > 0 and
            group_refit["precision"] >= .95),
        group_refit_threshold_rule=(
            "next representable probability above the maximum fitted "
            "negative score in each original-window discovery fold"),
        group_refit_outer_precision=group_refit["precision"],
        group_refit_outer_recall=group_refit["recall"],
        group_refit_outer_accepted=group_refit["accepted"],
        group_refit_outer_correct=group_refit["correct"],
        group_refit_outer_precision_by_fold=tuple(
            item[2] for item in group_refit["folds"]),
        group_refit_outer_recall_by_fold=tuple(
            item[3] for item in group_refit["folds"]),
        group_refit_outer_accepted_by_fold=tuple(
            item[4] for item in group_refit["folds"]),
        group_refit_minimum_nonempty_fold_precision=(
            group_refit["minimum_nonempty_precision"]),
        group_refit_nonempty_folds=group_refit["nonempty_folds"],
        group_refit_null_correct_best=max(null_group_refit_correct),
        group_refit_correct_empirical_p=(
            1 + sum(value >= group_refit["correct"]
                    for value in null_group_refit_correct)) / 32,
        group_refit_selector_passed=(
            group_refit["accepted"] > 0
            and group_refit["precision"] >= .95
            and group_refit["minimum_nonempty_precision"] >= .95
            and group_refit["nonempty_folds"] == len(TRAIN_CENTERS)),
        group_refit_rule_exploratory_not_confirmatory=True,
        future_confirmatory_target_opened=False,
        selected_zero_error_logit_margin=selected_margin,
        fixed_margin_outer_precision=margin_audit["precision"],
        fixed_margin_outer_recall=margin_audit["recall"],
        fixed_margin_minimum_nonempty_fold_precision=(
            margin_audit["minimum_nonempty_precision"]),
        fixed_margin_nonempty_folds=margin_audit["nonempty_folds"],
        fully_nested_margin_selection_precision=nested_margin[1],
        fully_nested_margin_selection_recall=nested_margin[2],
        fully_nested_margin_selection_passed=(
            nested_margin[3] > 0 and nested_margin[1] >= .95),
        null_trials=31,
        null_site_auc_median=sorted(null_site_auc)[15],
        null_site_auc_best=max(null_site_auc),
        null_action_auc_median=sorted(null_action_auc)[15],
        null_action_auc_best=max(null_action_auc),
        site_auc_empirical_p=(
            1 + sum(value >= site_auc for value in null_site_auc)) / 32,
        action_auc_empirical_p=(
            1 + sum(value >= action_auc for value in null_action_auc)) / 32,
        corpus_digest=site_corpus_digest,
        frozen_section_digest=_digest(asdict(section)),
        site_corpus_digest=site_corpus_digest,
        serialized_frozen_section=serialized_section,
        model_manifest_digest=_digest(manifest_payload),
        frozen_section=section,
        all_fit_and_selection_data_from_five_training_windows=True,
        confirmatory_or_prior_eval_nucleus_used=False,
        candidate_geometry_or_ids_changed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
