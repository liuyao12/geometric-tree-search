#!/usr/bin/env python3
"""Learn a bounded recurrent clusters-of-clusters quotient on IQC macros.

The parent semantic type is a colored three-site proper-metric graph with a
train-selected distance resolution.  Every occurrence nevertheless retains
its exact proper-SE(3) production alternatives and port witnesses, so the
quotient may rank or select immutable geometry but can never invent it.
Capacity is selected by leave-one-nucleus-out development performance and the
entire selection is repeated under 31 within-nucleus label shuffles.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
import random

from materials_gcts_iqc_recurrent_macro_geometry_dataset import (
    load_fixture, validate_dataset)


DISTANCE_WIDTHS = (0., .125, .25, .5, 1., 2., 4.)
MINIMUM_GROUPS = (2, 3)
ADMISSION_POSTERIOR = .5
SHUFFLES = 31
SHUFFLE_SEED = 180_773


@dataclass(frozen=True)
class MacroQuotientSpec:
    distance_width: float
    minimum_groups: int


@dataclass(frozen=True)
class MacroQuotientSelection:
    spec: MacroQuotientSpec
    supplied_groups: int
    selected_exact_groups: int
    selected_groups: int
    selected_precision: float
    supplied_group_recall: float
    recognized_candidates: int
    recognized_exact_candidates: int
    exact_candidates: int
    exact_candidate_coverage: float
    recognized_semantic_types: int


@dataclass(frozen=True)
class FrozenMacroSemanticType:
    type_id: str
    semantic_key: tuple
    training_groups: tuple[int, ...]
    positive_occurrences: int
    negative_occurrences: int
    posterior: float
    exact_action_alternatives: tuple[str, ...]
    exact_derivation_alternatives: tuple[str, ...]


@dataclass(frozen=True)
class FrozenMacroQuotient:
    spec: MacroQuotientSpec
    global_positive_rate: float
    types: tuple[FrozenMacroSemanticType, ...]
    model_digest: str


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _pair_matrix(colors, distances):
    matrix = [[0.] * 3 for _ in range(3)]
    cursor = 0
    for left in range(3):
        for right in range(left + 1, 3):
            matrix[left][right] = matrix[right][left] = float(
                distances[cursor])
            cursor += 1
    return tuple(colors), matrix


def canonical_colored_triangle(colors, distances, width=0.):
    """Canonical O(3)-metric parent key; exact terminals retain chirality."""
    colors, matrix = _pair_matrix(colors, distances)
    rows = []
    for order in itertools.permutations(range(3)):
        ordered_distances = tuple(
            matrix[order[left]][order[right]]
            for left in range(3) for right in range(left + 1, 3))
        metric = tuple(int(round(value / width)) for value in ordered_distances) \
            if width else tuple(round(value, 6)
                                for value in ordered_distances)
        rows.append((tuple(colors[index] for index in order), metric))
    return min(rows)


def row_action_geometry(row):
    nodes = tuple(row["geometry"]["nodes"])
    colors = tuple(node["species"] for node in nodes)
    points = tuple(tuple(node["local_nn"]) for node in nodes)
    distances = tuple(math.dist(points[left], points[right])
                      for left in range(3)
                      for right in range(left + 1, 3))
    return colors, distances


def semantic_key(row, width):
    return canonical_colored_triangle(*row_action_geometry(row), width)


def _rows(payload, labels=None):
    rows = []
    for group in payload["groups"]:
        for row in group["rows"]:
            rows.append({
                "group": int(group["group"]),
                "candidate_id": row["candidate_id"],
                "exact": bool(row["exact"]),
                "fit_label": bool(row["exact"]),
                "row": row,
            })
    if labels is not None:
        if len(labels) != len(rows):
            raise ValueError("macro label vector does not align")
        for row, label in zip(rows, labels):
            row["fit_label"] = bool(label)
    return tuple(rows)


def fit_macro_quotient(rows, spec):
    grouped = defaultdict(list)
    for row in rows:
        grouped[semantic_key(row["row"], spec.distance_width)].append(row)
    total_positive = sum(row["fit_label"] for row in rows)
    global_rate = (total_positive + 1.) / (len(rows) + 2.)
    types = []
    for key, occurrences in grouped.items():
        groups = tuple(sorted({row["group"] for row in occurrences}))
        if len(groups) < spec.minimum_groups:
            continue
        positive = sum(row["fit_label"] for row in occurrences)
        negative = len(occurrences) - positive
        action_alternatives = tuple(sorted({
            _digest({
                "colors": row_action_geometry(row["row"])[0],
                "distances": tuple(round(value, 6)
                                   for value in row_action_geometry(
                                       row["row"])[1]),
            }) for row in occurrences}))
        derivations = tuple(sorted({alternative
            for row in occurrences
            for alternative in row["row"]["production_alternative_ids"]}))
        types.append(FrozenMacroSemanticType(
            _digest(key), key, groups, positive, negative,
            (positive + 1.) / (len(occurrences) + 2.),
            action_alternatives, derivations))
    types = tuple(sorted(types, key=lambda row: row.type_id))
    body = {
        "spec": asdict(spec),
        "global_positive_rate": global_rate,
        "types": tuple(asdict(row) for row in types),
    }
    return FrozenMacroQuotient(spec, global_rate, types, _digest(body))


def _score(model, row):
    key = semantic_key(row["row"], model.spec.distance_width)
    match = next((item for item in model.types
                  if item.semantic_key == key), None)
    return match.posterior if match else model.global_positive_rate


def _select_one(model, rows):
    if not rows:
        return None
    selected = min(rows, key=lambda row: (
        -_score(model, row), row["candidate_id"]))
    return selected if _score(model, selected) >= ADMISSION_POSTERIOR else None


def _cross_validate(rows, spec):
    groups = tuple(sorted({row["group"] for row in rows}))
    selected = []
    recognized = recognized_exact = exact = 0
    type_ids = set()
    for heldout in groups:
        training = tuple(row for row in rows if row["group"] != heldout)
        testing = tuple(row for row in rows if row["group"] == heldout)
        model = fit_macro_quotient(training, spec)
        known = {row.semantic_key: row.type_id for row in model.types}
        for row in testing:
            exact += int(row["exact"])
            key = semantic_key(row["row"], spec.distance_width)
            if key in known:
                recognized += 1
                recognized_exact += int(row["exact"])
                type_ids.add(known[key])
        choice = _select_one(model, testing)
        if choice is not None:
            selected.append(choice)
    supplied = sum(any(row["exact"] for row in rows if row["group"] == group)
                   for group in groups)
    correct = sum(row["exact"] for row in selected)
    return MacroQuotientSelection(
        spec, supplied, correct, len(selected),
        correct / len(selected) if selected else 0.,
        correct / supplied if supplied else 0., recognized,
        recognized_exact, exact, recognized_exact / exact if exact else 0.,
        len(type_ids))


def select_spec(rows):
    audits = tuple(_cross_validate(rows, MacroQuotientSpec(width, groups))
                   for width in DISTANCE_WIDTHS
                   for groups in MINIMUM_GROUPS)
    selected = max(audits, key=lambda row: (
        row.selected_exact_groups, row.recognized_exact_candidates,
        -row.recognized_candidates + row.recognized_exact_candidates,
        row.recognized_semantic_types,
        -row.spec.distance_width, row.spec.minimum_groups))
    return selected, audits


def _shuffle(rows, trial):
    labels = [None] * len(rows)
    rng = random.Random(SHUFFLE_SEED + trial)
    for group in sorted({row["group"] for row in rows}):
        indices = [index for index, row in enumerate(rows)
                   if row["group"] == group]
        values = [rows[index]["exact"] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(labels)


def evaluate():
    payload = load_fixture()
    validate_dataset(payload)
    rows = _rows(payload)
    selected, audits = select_spec(rows)
    model = fit_macro_quotient(rows, selected.spec)
    nulls = []
    for trial in range(SHUFFLES):
        shuffled_rows = _rows(payload, _shuffle(rows, trial))
        null_selected, _null_audits = select_spec(shuffled_rows)
        nulls.append(null_selected.selected_exact_groups)

    admitted_occurrences = sum(
        1 for row in rows
        if any(item.semantic_key == semantic_key(
            row["row"], model.spec.distance_width) for item in model.types))
    semantic_tokens_saved = sum(
        max(0, (len(item.training_groups) - 1) *
            (len(item.semantic_key[0]) + len(item.semantic_key[1])) - 1)
        for item in model.types)
    exact_replay = all(
        len(row["row"]["geometry"]["nodes"]) == 3 and
        all(node["port_witnesses"]
            for node in row["row"]["geometry"]["nodes"])
        for row in rows)
    p_value = (1 + sum(value >= selected.selected_exact_groups
                       for value in nulls)) / (SHUFFLES + 1)
    body = {
        "source_dataset_digest": payload["dataset_digest"],
        "development_groups": len(payload["groups"]),
        "candidate_occurrences": len(rows),
        "exact_candidate_occurrences": sum(row["exact"] for row in rows),
        "candidate_specs": tuple(asdict(row.spec) for row in audits),
        "selection_audits": tuple(asdict(row) for row in audits),
        "selected_spec": asdict(selected.spec),
        "selected_supplied_groups": selected.supplied_groups,
        "selected_exact_groups": selected.selected_exact_groups,
        "selected_precision": selected.selected_precision,
        "selected_supplied_group_recall": selected.supplied_group_recall,
        "admission_posterior": ADMISSION_POSTERIOR,
        "selected_exact_candidate_coverage":
            selected.exact_candidate_coverage,
        "frozen_semantic_types": len(model.types),
        "frozen_positive_types": sum(
            row.positive_occurrences > row.negative_occurrences
            for row in model.types),
        "frozen_negative_types": sum(
            row.negative_occurrences >= row.positive_occurrences
            for row in model.types),
        "admitted_candidate_occurrences": admitted_occurrences,
        "exact_action_alternatives": len({alternative
            for row in model.types
            for alternative in row.exact_action_alternatives}),
        "exact_derivation_alternatives": len({alternative
            for row in model.types
            for alternative in row.exact_derivation_alternatives}),
        "semantic_description_tokens_saved": semantic_tokens_saved,
        "all_exact_alternatives_replayable": exact_replay,
        "model_digest": model.model_digest,
        "shuffle_trials": SHUFFLES,
        "shuffle_selected_exact_median": sorted(nulls)[SHUFFLES // 2],
        "shuffle_selected_exact_maximum": max(nulls),
        "selected_exact_empirical_p": p_value,
        "within_nucleus_label_shuffles": True,
        "candidate_geometry_changed_by_quotient": False,
        "raw_coordinates_or_occurrence_ids_used_as_semantic_key": False,
        "wide_atoms_or_labels_used": False,
        "integrated_for_external_transfer": False,
        "development_quotient_gate_passed": bool(
            selected.selected_exact_groups == selected.supplied_groups and
            selected.selected_precision == 1. and p_value <= .05 and
            semantic_tokens_saved > 0 and exact_replay),
    }
    body["honest_status"] = (
        "bounded recurrent macro quotient passes grouped development"
        if body["development_quotient_gate_passed"] else
        "bounded recurrent macro quotient remains below grouped development")
    body["audit_digest"] = _digest(body)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True)
          if args.json else report["honest_status"])


if __name__ == "__main__":
    main()
