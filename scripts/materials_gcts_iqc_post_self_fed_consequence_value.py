#!/usr/bin/env python3
"""Nested whole-nucleus value for target-free post-self-feed consequences."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_post_self_fed_consequence_dataset import (
    CHILD_FEATURE_NAMES, DEFAULT_FIXTURE as CONSEQUENCE_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_CONSEQUENCE_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_CONSEQUENCE_SHA256,
    FEATURE_NAMES as CONSEQUENCE_FEATURE_NAMES,
    load_fixture_json as load_consequence_fixture,
    validate_dataset as validate_consequence_dataset)
from materials_gcts_iqc_post_self_fed_fusion_value import (
    MINIMUM_SELECTED_CORRECT_SITES,
    MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS,
    load_default_result as load_baseline_result)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as SOURCE_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_SOURCE_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_SOURCE_SHA256,
    FEATURE_NAMES as SOURCE_FEATURE_NAMES, load_fixture_json as load_source,
    validate_dataset as validate_source)


RIDGES = (.25, 1., 4., 16.)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_consequence_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "0e6b9fdfc220fd49c45bea1dff4e937ebdf6793a838377b22a5d8d5eab9e07a0"
EXPECTED_AUDIT_DIGEST = \
    "1c3151b0eb0d4b611a4d2787856420d6a0fd88e883f74c70e7b9025d78e083aa"


@dataclass(frozen=True)
class Example:
    group: int
    stable_index: int
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    exact: bool
    correct_sites: int


@dataclass(frozen=True)
class Representation:
    name: str
    indices: tuple[int, ...]


@dataclass(frozen=True)
class Capacity:
    representation: str
    ridge: float
    supplied_groups: int
    selected_exact_groups: int
    selected_correct_sites: int
    first_exact_rank_sum: int


@dataclass(frozen=True)
class FrozenConsequenceValue:
    representation: Representation
    ridge: float
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: int
    model_digest: str
    target_used: bool = False


@dataclass(frozen=True)
class HeldoutFold:
    heldout_group: int
    terminal_supply: bool
    selected_representation: str
    selected_ridge: float
    selected_stable_index: int
    selected_exact: bool
    selected_correct_sites: int
    first_exact_rank: int | None


def _representations():
    source_width = len(SOURCE_FEATURE_NAMES)
    prefix = tuple(range(source_width, source_width + 4))
    child_width = len(CHILD_FEATURE_NAMES)
    if len(CONSEQUENCE_FEATURE_NAMES) != 4 + 3 * child_width:
        raise AssertionError("consequence representation schema drift")
    branch_width = 31
    successor_width = 16
    summary_offsets = tuple(source_width + 4 + slot * child_width
                            for slot in range(3))
    successor = tuple(index for offset in summary_offsets
                      for index in range(
                          offset + child_width - successor_width,
                          offset + child_width))
    branch_successor = tuple(index for offset in summary_offsets
        for index in (*range(offset, offset + branch_width),
                      *range(offset + child_width - successor_width,
                             offset + child_width)))
    top = tuple(range(summary_offsets[0], summary_offsets[0] + child_width))
    source = tuple(range(source_width))
    all_consequence = tuple(range(source_width,
                                  source_width + len(CONSEQUENCE_FEATURE_NAMES)))
    return (
        Representation("source-linear", source),
        Representation("successor-consequence", prefix + successor),
        Representation("branch+successor-consequence",
                       prefix + branch_successor),
        Representation("top-child-consequence", prefix + top),
        Representation("source+successor-consequence",
                       source + prefix + successor),
        Representation("source+top-child-consequence", source + prefix + top),
        Representation("source+all-consequences", source + all_consequence),
    )


def _load_examples():
    source_raw, source_payload = load_source(SOURCE_FIXTURE)
    consequence_raw, consequence_payload = load_consequence_fixture(
        CONSEQUENCE_FIXTURE)
    if hashlib.sha256(source_raw).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise AssertionError("source terminal fixture byte drift")
    if hashlib.sha256(consequence_raw).hexdigest() != \
            EXPECTED_CONSEQUENCE_SHA256:
        raise AssertionError("consequence fixture byte drift")
    source = validate_source(source_payload)
    consequence = validate_consequence_dataset(consequence_payload)
    if (source["dataset_digest"] != EXPECTED_SOURCE_DIGEST
            or consequence["dataset_digest"] !=
               EXPECTED_CONSEQUENCE_DIGEST):
        raise AssertionError("consequence/source dataset drift")
    source_rows = {(int(row["group"]), int(row["stable_index"])): row
                   for group in source["groups"] for row in group["rows"]}
    rows = []
    for group in consequence["groups"]:
        for row in group["rows"]:
            key = int(row["group"]), int(row["stable_index"])
            prior = source_rows[key]
            if (bool(row["exact"]) != bool(prior["exact"])
                    or int(row["correct_sites"]) !=
                       int(prior["correct_sites"])
                    or tuple(row["action_colors"]) !=
                       tuple(prior["action_colors"])):
                raise AssertionError("consequence/source label drift")
            rows.append(Example(
                key[0], key[1], tuple(map(float, prior["features"]))
                + tuple(map(float, row["features"])),
                tuple(map(str, row["action_colors"])), bool(row["exact"]),
                int(row["correct_sites"])))
    return tuple(rows), source, consequence


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
        raise ValueError("consequence value needs two contrasted nuclei")
    average = tuple(sum(row[index] for row in contrasts) / len(contrasts)
                    for index in range(width))
    dispersion = tuple(sum((row[index] - average[index]) ** 2
                           for row in contrasts) / len(contrasts)
                       for index in range(width))
    weights = tuple(value / (ridge + variance)
                    for value, variance in zip(average, dispersion))
    payload = (representation, ridge, means, scales, weights,
               len({row.group for row in rows}))
    return FrozenConsequenceValue(
        representation, ridge, means, scales, weights,
        len({row.group for row in rows}),
        hashlib.sha256(repr(payload).encode()).hexdigest())


def _score(model, row):
    vector = tuple(row.features[index]
                   for index in model.representation.indices)
    return sum(weight * (value - mean) / scale
               for weight, value, mean, scale in
               zip(model.weights, vector, model.means, model.scales))


def _group_result(model, held):
    order = tuple(sorted(range(len(held)), key=lambda index: (
        -_score(model, held[index]), held[index].stable_index)))
    supplied = any(row.exact for row in held)
    selected = held[order[0]]
    rank = next((rank for rank, index in enumerate(order, 1)
                 if held[index].exact), None)
    return supplied, selected, rank


def _capacity(rows, representation, ridge):
    supplied = exact = correct = rank_sum = 0
    for group in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != group)
        held = tuple(row for row in rows if row.group == group)
        result = _group_result(_fit(
            training, representation, ridge), held)
        if not result[0]:
            continue
        supplied += 1
        exact += int(result[1].exact)
        correct += result[1].correct_sites
        rank_sum += result[2] or 0
    return Capacity(representation.name, ridge, supplied, exact,
                    correct, rank_sum)


def _select_capacity(rows, representations):
    capacities = tuple(_capacity(rows, representation, ridge)
                       for representation in representations
                       for ridge in RIDGES)
    order = {row.name: index for index, row in enumerate(representations)}
    selected = min(capacities, key=lambda row: (
        -row.selected_exact_groups, -row.selected_correct_sites,
        row.first_exact_rank_sum, order[row.representation], -row.ridge))
    representation = representations[order[selected.representation]]
    return selected, capacities, _fit(rows, representation, selected.ridge)


def evaluate():
    rows, source, consequence = _load_examples()
    representations = _representations()
    folds = []
    for heldout in range(consequence["development_groups"]):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        selected, _capacities, model = _select_capacity(
            training, representations)
        supplied, chosen, rank = _group_result(model, held)
        folds.append(HeldoutFold(
            heldout, supplied, selected.representation, selected.ridge,
            chosen.stable_index, chosen.exact, chosen.correct_sites, rank))
    final_selected, final_capacities, final_model = _select_capacity(
        rows, representations)
    selected_exact = sum(fold.selected_exact for fold in folds)
    selected_correct = sum(fold.selected_correct_sites for fold in folds)
    baseline = load_baseline_result()
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "consequence_dataset_digest": consequence["dataset_digest"],
        "development_groups": consequence["development_groups"],
        "terminal_examples": len(rows),
        "exact_examples": sum(row.exact for row in rows),
        "feature_count": len(rows[0].features),
        "representations": [asdict(row) for row in representations],
        "ridges": RIDGES,
        "folds": [asdict(fold) for fold in folds],
        "nested_supplied_groups": sum(fold.terminal_supply for fold in folds),
        "nested_selected_exact_groups": selected_exact,
        "nested_selected_correct_sites": selected_correct,
        "nested_first_exact_rank_sum": sum(
            fold.first_exact_rank or 0 for fold in folds),
        "final_selected_capacity": asdict(final_selected),
        "final_capacities": [asdict(row) for row in final_capacities],
        "final_model_digest": final_model.model_digest,
        "baseline_selected_exact_groups":
            baseline["nested_selected_exact_groups"],
        "baseline_selected_correct_sites":
            baseline["nested_selected_correct_sites"],
        "minimum_selected_exact_supplied_groups":
            MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS,
        "minimum_selected_correct_sites": MINIMUM_SELECTED_CORRECT_SITES,
        "development_gate_passed": (
            selected_exact >= MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS
            and selected_correct >= MINIMUM_SELECTED_CORRECT_SITES),
        "candidate_geometry_unchanged": True,
        "children_advanced_target_free": True,
        "target_used_for_consequence_fit_or_ranking": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "audit_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["source_dataset_digest"] != EXPECTED_SOURCE_DIGEST
            or body["consequence_dataset_digest"] !=
               EXPECTED_CONSEQUENCE_DIGEST
            or body["development_groups"] != 10
            or body["terminal_examples"] != 1278
            or body["exact_examples"] != 142
            or not body["candidate_geometry_unchanged"]
            or not body["children_advanced_target_free"]
            or body["target_used_for_consequence_fit_or_ranking"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("post-self-fed consequence-value result drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("post-self-fed consequence-value audit drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("post-self-fed consequence-value fixture drift")
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
