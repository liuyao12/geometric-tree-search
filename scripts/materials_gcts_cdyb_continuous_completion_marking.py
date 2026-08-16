#!/usr/bin/env python3
"""Train-only continuous, ID-free marking for Cd--Yb macro completions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
from materials_gcts_partial_completion_marking import freeze_completion_candidate
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


SEED_RADIUS = 7.
LAMBDAS = (.01, .1, 1., 10.)
FEATURE_NAMES = (
    "matched_child_fraction", "log_emitted_atoms", "log_macro_atoms",
    "species_entropy", "macro_radial_rms_nn", "macro_radial_cv",
    "log_port_evidence", "log_boundary_slots", "mean_boundary_frequency",
    "log_incoming_port_kinds")


@dataclass(frozen=True)
class FrozenContinuousCompletionMarking:
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    ridge_lambda: float
    target_used: bool
    id_family_cell_origin_features_used: bool


@dataclass(frozen=True)
class ContinuousCompletionMarkingAudit:
    train_windows: int
    base_frontiers: int
    expanded_frontiers_considered: int
    seed_shift_nn: float
    base_candidates: int
    base_positive: int
    base_negative: int
    base_negative_roles: int
    expanded_candidates: int
    expanded_positive: int
    expanded_negative: int
    expanded_negative_roles: int
    expanded_corpus_admitted: bool
    admitted_candidates: int
    admitted_positive: int
    admitted_negative: int
    feature_count: int
    feature_names: tuple[str, ...]
    grouped_outer_folds: int
    outer_lopo_logloss: float
    outer_lopo_auc: float
    outer_lopo_unique_scores: int
    shift_admission_uses_all_five_labels: bool
    lopo_diagnostic_not_fully_nested: bool
    nested_outer_expansion_admitted_by_fold: tuple[bool, ...]
    nested_outer_lopo_logloss: float
    nested_outer_lopo_auc: float
    nested_outer_lopo_unique_scores: int
    selected_final_lambda: float
    frozen_model: FrozenContinuousCompletionMarking
    training_corpus_digest: str
    frozen_model_digest: str
    all_samples_from_five_training_windows: bool
    confirmatory_nucleus_opened_or_scored: bool
    target_used_outside_training_windows: bool
    raw_ids_family_cell_origin_or_prescribed_scale_used: bool
    ready_for_future_frozen_confirmatory_test: bool


@dataclass(frozen=True)
class _Row:
    window: int
    candidate_id: str
    features: tuple[float, ...]
    successful: bool


def _entropy(counts):
    total = sum(counts.values())
    return -sum((value / total) * math.log(value / total)
                for value in counts.values() if value) if total else 0.


def _features(candidate, completion, macro, minimum_distance):
    sites = tuple(macro.atom_union)
    species = {}
    for label, _point in sites:
        species[repr(label)] = species.get(repr(label), 0) + 1
    centroid = tuple(sum(point[axis] for _, point in sites) / len(sites)
                     for axis in range(3))
    radii = tuple(math.dist(point, centroid) / minimum_distance
                  for _, point in sites)
    mean_radius = sum(radii) / len(radii)
    rms = math.sqrt(sum(value * value for value in radii) / len(radii))
    deviation = math.sqrt(sum((value - mean_radius) ** 2 for value in radii) /
                          len(radii))
    emitted_atoms = sum(len(child.sites) for child in completion.missing_children)
    child_arity = len(macro.child_placements)
    slots = candidate.descriptor.alternative_boundary_slots
    return (
        len(completion.matched_nodes) / child_arity,
        math.log1p(emitted_atoms), math.log1p(len(sites)), _entropy(species),
        rms, deviation / max(mean_radius, 1e-12),
        math.log1p(candidate.descriptor.training_port_evidence),
        math.log1p(len(slots)),
        sum(item[2] / 10 for item in slots) / max(1, len(slots)),
        math.log1p(len(candidate.descriptor.anchor_incoming_ports)))


def _alternative_parent_map(quotient, promoted):
    parent = {macro_id: prototype_id for prototype_id, macro_id
              in promoted.prototype_macro_types}
    result = []
    cursor = 0
    for geometry in quotient.derivation_classes:
        for _alternative in geometry.alternatives:
            macro = quotient.alternative_macros[cursor]
            result.append((macro.macro_id, parent[geometry.geometry_class_id]))
            cursor += 1
    if cursor != len(quotient.alternative_macros):
        raise AssertionError("incomplete alternative map")
    return tuple(result)


def _frontier_rows(primitive, quotient, parent_map, train_species,
                   train_positions, namespaces, patch, seed_center):
    indices = tuple(index for index, point in enumerate(train_positions)
                    if namespaces[index] == patch and
                    math.dist(seed_center, point) <= SEED_RADIUS + 1e-10)
    species = tuple(train_species[index] for index in indices)
    positions = tuple(train_positions[index] for index in indices)
    seed_sites = tuple(zip(species, positions))
    enumeration = enumerate_frozen_port_occurrences(
        primitive, species, positions)
    lower = _frozen_heldout_program(primitive, enumeration)
    frontier = enumerate_partial_promoted_completions(
        lower, quotient.alternative_macros, minimum_matched_children=1,
        minimum_child_coverage=.5, explicit_seed_sites=seed_sites,
        public_boundary=ExecutionBoundary((patch * PACK_SEPARATION, 0., 0.),
                                          RADIUS),
        frozen_parent_types=parent_map)
    macro_by_id = {item.macro_id: item for item in quotient.alternative_macros}
    seed_keys = {_site_key(site, .03) for site in seed_sites}
    target = {_site_key((train_species[index], train_positions[index]), .03)
              for index, namespace in enumerate(namespaces)
              if namespace == patch}
    rows = []
    for completion in frontier.completions:
        macro = macro_by_id[completion.macro_id]
        candidate = freeze_completion_candidate(
            lower, macro, completion,
            live_overlap_support=len(completion.matched_occurrence_ids),
            live_collision_support=0)
        emitted = {_site_key(site, .03)
                   for child in completion.missing_children
                   for site in child.sites} - seed_keys
        rows.append(_Row(
            patch, candidate.candidate_id,
            _features(candidate, completion, macro, lower.minimum_distance),
            bool(emitted) and emitted.issubset(target)))
    return tuple(rows)


def _dedupe(rows):
    chosen = {}
    for row in rows:
        key = row.window, row.candidate_id
        if key in chosen and chosen[key].successful != row.successful:
            raise AssertionError("one train candidate has inconsistent labels")
        chosen.setdefault(key, row)
    return tuple(chosen[key] for key in sorted(chosen))


def _role_count(rows):
    return len({tuple(round(value, 3) for value in row.features)
                for row in rows if not row.successful})


def _corpus_digest(rows):
    payload = tuple((row.window, row.candidate_id,
                     tuple(float(value) for value in row.features),
                     bool(row.successful))
                    for row in sorted(rows, key=lambda item: (
                        item.window, item.candidate_id, item.features)))
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                            allow_nan=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _model_digest(model):
    serialized = json.dumps(asdict(model), sort_keys=True,
                            separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _sigmoid(value):
    if value >= 0:
        inverse = math.exp(-min(value, 50.))
        return 1 / (1 + inverse)
    exponential = math.exp(max(value, -50.))
    return exponential / (1 + exponential)


def _standardizer(rows):
    columns = tuple(zip(*(row.features for row in rows)))
    means = tuple(sum(column) / len(column) for column in columns)
    scales = tuple(max(1e-9, math.sqrt(sum((value - mean) ** 2
                                          for value in column) / len(column)))
                   for column, mean in zip(columns, means))
    return means, scales


def _fit(rows, ridge):
    means, scales = _standardizer(rows)
    values = tuple(tuple((value - mean) / scale
                         for value, mean, scale in zip(
                             row.features, means, scales)) for row in rows)
    labels = tuple(float(row.successful) for row in rows)
    weights = [0.] * len(FEATURE_NAMES)
    intercept = math.log((sum(labels) + 1) /
                         (len(labels) - sum(labels) + 1))
    for iteration in range(1200):
        predictions = tuple(_sigmoid(intercept + sum(
            weight * value for weight, value in zip(weights, row)))
                            for row in values)
        gradient0 = sum(prediction - label for prediction, label in
                        zip(predictions, labels)) / len(rows)
        gradients = [sum((prediction - label) * row[index]
                         for prediction, label, row in
                         zip(predictions, labels, values)) / len(rows) +
                     ridge * weights[index] / len(rows)
                     for index in range(len(weights))]
        rate = .12 / (1 + iteration / 300)
        intercept -= rate * gradient0
        for index in range(len(weights)):
            weights[index] -= rate * gradients[index]
    return FrozenContinuousCompletionMarking(
        FEATURE_NAMES, means, scales, tuple(weights), intercept, ridge,
        False, False)


def _predict(model, row):
    standardized = tuple((value - mean) / scale for value, mean, scale in
                         zip(row.features, model.means, model.scales))
    return _sigmoid(model.intercept + sum(weight * value for weight, value in
                                           zip(model.weights, standardized)))


def _logloss(rows, scores):
    return -sum((math.log(max(score, 1e-12)) if row.successful else
                 math.log(max(1 - score, 1e-12)))
                for row, score in zip(rows, scores)) / max(1, len(rows))


def _auc(rows, scores):
    positive = [score for row, score in zip(rows, scores) if row.successful]
    negative = [score for row, score in zip(rows, scores) if not row.successful]
    if not positive or not negative:
        return .5
    return (sum((left > right) + .5 * (left == right)
                for left in positive for right in negative) /
            (len(positive) * len(negative)))


def _select_lambda(rows, heldout_window=None):
    windows = sorted({row.window for row in rows
                      if row.window != heldout_window})
    candidates = []
    for ridge in LAMBDAS:
        losses = []
        for validation in windows:
            fit_rows = tuple(row for row in rows
                             if row.window not in (heldout_window, validation))
            validation_rows = tuple(row for row in rows
                                    if row.window == validation)
            if not fit_rows or not validation_rows:
                continue
            model = _fit(fit_rows, ridge)
            losses.append(_logloss(
                validation_rows,
                tuple(_predict(model, row) for row in validation_rows)))
        if losses:
            candidates.append((sum(losses) / len(losses), ridge))
    if not candidates:
        raise AssertionError("grouped validation cannot select ridge strength")
    return min(candidates)[1]


def evaluate():
    atoms = generate_cdyb(6, (120.,) * 3)
    windows = _window_ids(atoms, TRAIN_CENTERS)
    species, positions, namespaces = _pack(atoms, TRAIN_CENTERS, windows)
    primitive = compile_irregular_port_program(species, positions)
    quotient = quotient_macro_supports(mine_port_graph_macros(
        primitive, maximum_nodes=3,
        include_boundary_relations=True).macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    parent_map = _alternative_parent_map(quotient, promoted)
    scale = primitive.cover.minimum_distance
    offsets = ((0., 0., 0.), (scale, 0., 0.), (-scale, 0., 0.),
               (0., scale, 0.), (0., -scale, 0.),
               (0., 0., scale), (0., 0., -scale))
    base = []
    expanded = []
    for patch in range(len(TRAIN_CENTERS)):
        origin = (patch * PACK_SEPARATION, 0., 0.)
        for offset_index, offset in enumerate(offsets):
            center = tuple(origin[axis] + offset[axis] for axis in range(3))
            rows = _frontier_rows(
                primitive, quotient, parent_map, species, positions,
                namespaces, patch, center)
            expanded.extend(rows)
            if offset_index == 0:
                base.extend(rows)
    base = _dedupe(base)
    expanded = _dedupe(expanded)
    base_negative = sum(not row.successful for row in base)
    expanded_negative = sum(not row.successful for row in expanded)
    admitted_expansion = (expanded_negative > base_negative and
                          _role_count(expanded) > _role_count(base))
    rows = expanded if admitted_expansion else base
    predictions = []
    prediction_rows = []
    selected_lambdas = []
    for heldout in range(len(TRAIN_CENTERS)):
        fit_rows = tuple(row for row in rows if row.window != heldout)
        heldout_rows = tuple(row for row in rows if row.window == heldout)
        ridge = _select_lambda(rows, heldout)
        model = _fit(fit_rows, ridge)
        predictions.extend(_predict(model, row) for row in heldout_rows)
        prediction_rows.extend(heldout_rows)
        selected_lambdas.append(ridge)
    # Diagnostic only: unlike the published outer score above, each fold now
    # decides whether shifted seeds are admissible from its four discovery
    # windows.  This does not alter the already frozen final corpus or model.
    nested_decisions = []
    nested_predictions = []
    nested_prediction_rows = []
    for heldout in range(len(TRAIN_CENTERS)):
        base_fit = tuple(row for row in base if row.window != heldout)
        expanded_fit = tuple(row for row in expanded if row.window != heldout)
        decision = (
            sum(not row.successful for row in expanded_fit) >
            sum(not row.successful for row in base_fit) and
            _role_count(expanded_fit) > _role_count(base_fit))
        nested_decisions.append(decision)
        selected = expanded if decision else base
        fit_rows = tuple(row for row in selected if row.window != heldout)
        validation_rows = tuple(row for row in selected
                                if row.window == heldout)
        ridge = _select_lambda(selected, heldout)
        nested_model = _fit(fit_rows, ridge)
        nested_predictions.extend(
            _predict(nested_model, row) for row in validation_rows)
        nested_prediction_rows.extend(validation_rows)
    final_lambda = _select_lambda(rows)
    model = _fit(rows, final_lambda)
    return ContinuousCompletionMarkingAudit(
        len(TRAIN_CENTERS), len(TRAIN_CENTERS),
        len(TRAIN_CENTERS) * len(offsets), scale,
        len(base), sum(row.successful for row in base), base_negative,
        _role_count(base), len(expanded),
        sum(row.successful for row in expanded), expanded_negative,
        _role_count(expanded), admitted_expansion, len(rows),
        sum(row.successful for row in rows),
        sum(not row.successful for row in rows), len(FEATURE_NAMES),
        FEATURE_NAMES, len(TRAIN_CENTERS),
        _logloss(prediction_rows, predictions),
        _auc(prediction_rows, predictions),
        len({round(value, 12) for value in predictions}), True, True,
        tuple(nested_decisions),
        _logloss(nested_prediction_rows, nested_predictions),
        _auc(nested_prediction_rows, nested_predictions),
        len({round(value, 12) for value in nested_predictions}), final_lambda,
        model, _corpus_digest(rows), _model_digest(model),
        True, False, False, False,
        bool(rows) and len(set(row.window for row in rows)) == 5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
