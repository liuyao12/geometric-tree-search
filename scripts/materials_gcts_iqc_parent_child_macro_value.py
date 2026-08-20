#!/usr/bin/env python3
"""Nested value audit for six-action IQC clusters-of-clusters."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_branch_local_integrated_beam_diagnostic import (
    DEFAULT_FIXTURE as BEAM_FIXTURE,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_BEAM_SHA256,
    EXPECTED_RESULT_DIGEST as EXPECTED_BEAM_DIGEST,
    validate_result as validate_beam)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_parent_child_macro_dataset import (
    DEFAULT_FIXTURE as DATASET_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_DATASET_SHA256,
    FEATURE_NAMES, macro_features, validate_dataset)


RIDGES = (.25, 1., 4., 16.)
SHUFFLES = 31
SHUFFLE_SEED = 20260820
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_parent_child_macro_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "72d33c6f622bd8c3d76b9b037400931b3eeae688d4351ae3ffb932be96348108"
EXPECTED_AUDIT_DIGEST = \
    "dd6ef4e13e5f25c7bd542a044510ad2fe033a1e797eb58642b8245a7ea8b18c5"


@dataclass(frozen=True)
class Example:
    group: int
    stable_index: int
    features: tuple[float, ...]
    exact: bool
    correct_sites: int


@dataclass(frozen=True)
class Representation:
    name: str
    indices: tuple[int, ...]


@dataclass(frozen=True)
class Model:
    representation: Representation
    ridge: float
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: int
    model_digest: str


def _representations():
    all_indices = tuple(range(len(FEATURE_NAMES)))
    chirality = FEATURE_NAMES.index("proper_chirality")
    block = tuple(index for index, name in enumerate(FEATURE_NAMES)
                  if (name.startswith("parent_")
                      or name.startswith("child_")
                      or name.startswith("centroid_")
                      or name.startswith("cross_connection")))
    cross = tuple(index for index, name in enumerate(FEATURE_NAMES)
                  if (name.startswith("parent_count")
                      or name.startswith("child_count")
                      or name.startswith("cross_")
                      or name == "centroid_separation"
                      or name.startswith("child_nearest")))
    return (
        Representation("block-geometry", block),
        Representation("cross-geometry", cross),
        Representation("achiral-all", tuple(index for index in all_indices
                                             if index != chirality)),
        Representation("chiral-all", all_indices),
    )


def _load_json(path):
    raw = path.read_bytes()
    return raw, json.loads(gzip.decompress(raw))


def _load_examples():
    raw, payload = _load_json(DATASET_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_DATASET_SHA256:
        raise AssertionError("macro dataset fixture byte drift")
    dataset = validate_dataset(payload)
    if dataset["dataset_digest"] != EXPECTED_DATASET_DIGEST:
        raise AssertionError("macro dataset digest drift")
    rows = tuple(Example(
        int(row["group"]), int(row["stable_index"]),
        tuple(map(float, row["features"])), bool(row["exact"]),
        int(row["correct_sites"]))
        for group in dataset["groups"] for row in group["rows"])
    return rows, dataset


def _fit(rows, representation, ridge):
    projected = tuple(tuple(row.features[index]
                            for index in representation.indices)
                      for row in rows)
    width = len(representation.indices)
    means = tuple(sum(vector[index] for vector in projected) / len(projected)
                  for index in range(width))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (vector[index] - means[index]) ** 2 for vector in projected)
        / len(projected))) for index in range(width))
    normalized = tuple(tuple((value - mean) / scale
                             for value, mean, scale in
                             zip(vector, means, scales))
                       for vector in projected)
    contrasts = []
    for group in sorted({row.group for row in rows}):
        positive = tuple(vector for row, vector in zip(rows, normalized)
                         if row.group == group and row.exact)
        negative = tuple(vector for row, vector in zip(rows, normalized)
                         if row.group == group and not row.exact)
        if not positive or not negative:
            continue
        contrasts.append(tuple(
            sum(vector[index] for vector in positive) / len(positive)
            - sum(vector[index] for vector in negative) / len(negative)
            for index in range(width)))
    if len(contrasts) < 2:
        raise ValueError("macro value needs two contrasted nuclei")
    average = tuple(sum(row[index] for row in contrasts) / len(contrasts)
                    for index in range(width))
    dispersion = tuple(sum((row[index] - average[index]) ** 2
                           for row in contrasts) / len(contrasts)
                       for index in range(width))
    weights = tuple(value / (ridge + variance)
                    for value, variance in zip(average, dispersion))
    payload = (representation, ridge, means, scales, weights,
               len({row.group for row in rows}))
    return Model(
        representation, ridge, means, scales, weights,
        len({row.group for row in rows}),
        hashlib.sha256(repr(payload).encode()).hexdigest())


def _score(model, features):
    vector = tuple(features[index]
                   for index in model.representation.indices)
    return sum(weight * (value - mean) / scale
               for weight, value, mean, scale in
               zip(model.weights, vector, model.means, model.scales))


def _group_result(model, rows):
    order = tuple(sorted(range(len(rows)), key=lambda index: (
        -_score(model, rows[index].features), rows[index].stable_index)))
    selected = rows[order[0]]
    first_exact_rank = next((rank for rank, index in enumerate(order, 1)
                             if rows[index].exact), None)
    return selected, first_exact_rank


def _capacity(rows, representation, ridge):
    exact = correct = rank_sum = supplied = 0
    for group in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != group)
        held = tuple(row for row in rows if row.group == group)
        selected, rank = _group_result(_fit(
            training, representation, ridge), held)
        if rank is None:
            continue
        supplied += 1
        exact += int(selected.exact)
        correct += selected.correct_sites
        rank_sum += rank
    return supplied, exact, correct, rank_sum


def _select(rows):
    representations = _representations()
    candidates = tuple((
        _capacity(rows, representation, ridge), representation, ridge)
        for representation in representations for ridge in RIDGES)
    order = {row.name: index for index, row in enumerate(representations)}
    capacity, representation, ridge = min(candidates, key=lambda row: (
        -row[0][1], -row[0][2], row[0][3],
        len(row[1].indices), order[row[1].name], -row[2]))
    return capacity, representation, ridge, _fit(rows, representation, ridge)


def _confirmation(model):
    raw, payload = _load_json(BEAM_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_BEAM_SHA256:
        raise AssertionError("branch beam fixture byte drift")
    beam = validate_beam(payload)
    if beam["result_digest"] != EXPECTED_BEAM_DIGEST:
        raise AssertionError("branch beam result drift")
    # The ideal IQC seed scale is fixed by the frozen development corpus; all
    # ten groups agree to numerical precision.  Use their deterministic mean,
    # not confirmation labels or an oracle target.
    _rows, dataset = _load_examples()
    scale = sum(group["nearest_neighbor_scale"]
                for group in dataset["groups"]) / dataset["development_groups"]
    candidates = tuple((
        int(branch["first_rank"]),
        macro_features(branch["first_actions"],
                       branch["selected_second_actions"], scale))
        for branch in beam["receipt"]["branches"])
    order = tuple(rank for rank, _features in sorted(
        candidates, key=lambda row: (-_score(model, row[1]), row[0])))
    scored = {int(row["first_rank"]): row
              for row in beam["scored_branches"]}
    exact_paths = tuple(rank for rank in order
                        if scored[rank]["first_exact"]
                        and scored[rank]["second_exact"])
    return {
        "candidate_count": len(candidates),
        "candidate_digest": hashlib.sha256(
            canonical_json(candidates)).hexdigest(),
        "order": order,
        "selected_first_rank": order[0],
        "selected_end_to_end_exact": order[0] in exact_paths,
        "exact_path_ranks": tuple(order.index(rank) + 1
                                  for rank in exact_paths),
        "target_used_for_features_or_ranking": False,
        "consumed_beam_labels_used_after_order": True,
    }


def evaluate():
    rows, dataset = _load_examples()
    folds = []
    for heldout in range(dataset["development_groups"]):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        capacity, representation, ridge, model = _select(training)
        selected, rank = _group_result(model, held)
        folds.append({
            "heldout_group": heldout,
            "terminal_supply": rank is not None,
            "selected_representation": representation.name,
            "selected_ridge": ridge,
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "first_exact_rank": rank,
            "inner_capacity": capacity,
        })
    final_capacity, representation, ridge, model = _select(rows)
    supplied = sum(row["terminal_supply"] for row in folds)
    nested_exact = sum(row["selected_exact"] for row in folds
                       if row["terminal_supply"])
    nested_correct = sum(row["selected_correct_sites"] for row in folds)
    development_selected = tuple(_group_result(model, tuple(
        row for row in rows if row.group == group))[0]
        for group in range(dataset["development_groups"]))
    development_exact = sum(row.exact for row in development_selected)
    development_correct = sum(row.correct_sites for row in
                              development_selected)

    rng = random.Random(SHUFFLE_SEED)
    null_exact = []
    for _shuffle in range(SHUFFLES):
        shuffled = []
        for group in range(dataset["development_groups"]):
            group_rows = tuple(row for row in rows if row.group == group)
            labels = [(row.exact, row.correct_sites) for row in group_rows]
            rng.shuffle(labels)
            shuffled.extend(Example(
                row.group, row.stable_index, row.features, exact, correct)
                for row, (exact, correct) in zip(group_rows, labels))
        shuffled_model = _fit(tuple(shuffled), representation, ridge)
        selected_real = tuple(_group_result(shuffled_model, tuple(
            row for row in rows if row.group == group))[0]
            for group in range(dataset["development_groups"]))
        null_exact.append(sum(row.exact for row in selected_real))
    shuffle_p = (1 + sum(value >= development_exact for value in null_exact)) \
        / (SHUFFLES + 1)
    confirmation = _confirmation(model)
    body = {
        "schema_version": 1,
        "dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "examples": len(rows),
        "exact_examples": sum(row.exact for row in rows),
        "representations": [asdict(row) for row in _representations()],
        "ridges": RIDGES,
        "folds": folds,
        "nested_supplied_groups": supplied,
        "nested_selected_exact_groups": nested_exact,
        "nested_selected_correct_sites": nested_correct,
        "development_selected_exact_groups": development_exact,
        "development_selected_correct_sites": development_correct,
        "final_capacity": final_capacity,
        "final_representation": representation.name,
        "final_ridge": ridge,
        "final_model_digest": model.model_digest,
        "shuffle_exact_counts": tuple(null_exact),
        "shuffle_p": shuffle_p,
        "confirmation": confirmation,
        "candidate_geometry_unchanged": True,
        "target_used_for_macro_fit_or_ranking": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "audit_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["dataset_digest"] != EXPECTED_DATASET_DIGEST
            or body["development_groups"] != 10
            or body["examples"] != 1278
            or body["exact_examples"] != 142
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_macro_fit_or_ranking"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("parent-child macro value drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("parent-child macro value digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("parent-child macro value fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
