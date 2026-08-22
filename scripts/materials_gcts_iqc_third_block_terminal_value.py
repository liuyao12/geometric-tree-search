#!/usr/bin/env python3
"""Group-heldout value for the frozen IQC third-block terminal universe.

The expensive geometry audit has already frozen 5,091 candidate terminals.
This module derives a compact proper-SE(3)-invariant feature vector from each
terminal, its retained parent, and the four existing marking scores.  Model
capacity is selected inside each outer training fold.  Four terminals per
parent are then retained on the held-out nucleus, matching the incumbent
portfolio width.  Thirty-one deterministic label shuffles within each
``(nucleus, parent)`` stratum refit the complete nested procedure.

All labels are from consumed development annuli and enter only after the
candidate receipt was frozen.  The result is not a fresh confirmation or an
autonomous-growth claim.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_child_option_third_block_audit import (
    EXPECTED_RESULT_DIGEST as SOURCE_RESULT_DIGEST,
    THIRD_BLOCK_RADIUS, load_default_result as load_source_result)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_self_fed_terminal_dataset import (
    OUTER_ORACLE_LIFT_BOUND)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


RIDGES = (.25, 1., 4., 16.)
BEAM_PER_PARENT = 4
SHUFFLES = 31
CHANNEL_NAMES = ("base", "colored", "ports", "coupled")
SCORE_FEATURES = tuple(f"score:{name}" for name in CHANNEL_NAMES) + (
    "score:mean", "score:minimum", "score:maximum", "score:range")
GEOMETRY_FEATURES = (
    *(f"terminal-radius:{index}" for index in range(3)),
    *(f"terminal-pair-distance:{index}" for index in range(3)),
    "terminal-triangle-area",
    "terminal-color-X", "terminal-color-Y", "terminal-color-Z",
    *(f"parent-radius:{index}" for index in range(3)),
    *(f"parent-pair-distance:{index}" for index in range(3)),
    "cross-minimum", "cross-lower-quartile", "cross-mean", "cross-maximum",
    "same-color-cross-minimum", "same-color-cross-mean",
    "different-color-cross-minimum", "different-color-cross-mean",
    "inherited-cross-minimum", "inherited-cross-lower-quartile",
    "inherited-cross-mean", "inherited-cross-maximum",
    *(f"terminal-minus-parent-radius:{index}" for index in range(3)),
)
FEATURE_NAMES = SCORE_FEATURES + GEOMETRY_FEATURES
REPRESENTATIONS = (
    ("scores", tuple(range(len(SCORE_FEATURES)))),
    ("geometry", tuple(range(len(SCORE_FEATURES), len(FEATURE_NAMES)))),
    ("scores+geometry", tuple(range(len(FEATURE_NAMES)))),
)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_third_block_terminal_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "2bb4b76948cf18d051f826097e3c9839b27b9166e2089c47f0af932354bd4289"
EXPECTED_RESULT_DIGEST = \
    "cef912ace66d4e37856410a4ea572b80ef44ad9d7b35b4f3d1546ccee884b656"


@dataclass(frozen=True)
class Example:
    group: int
    parent: int
    stable_index: int
    features: tuple[float, ...]
    exact: bool
    correct_actions: int


@dataclass(frozen=True)
class FrozenValue:
    representation: str
    indices: tuple[int, ...]
    ridge: float
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: int
    model_digest: str


@dataclass(frozen=True)
class Capacity:
    representation: str
    ridge: float
    supplied_groups: int
    retained_groups: int
    first_exact_rank_sum: int


@dataclass(frozen=True)
class Fold:
    heldout_group: int
    exact_supply: bool
    selected_representation: str
    selected_ridge: float
    exact_paths: int
    retained_exact_paths: int
    retained_exact_group: bool
    first_exact_rank: int | None
    model_digest: str


def _key(point):
    return tuple(round(float(value), 6) for value in point)


def _distances(points):
    return tuple(sorted(math.dist(points[left], points[right])
                        for left in range(len(points))
                        for right in range(left + 1, len(points))))


def _radii(points, center):
    return tuple(sorted(math.dist(point, center) / THIRD_BLOCK_RADIUS
                        for point in points))


def _summary(values):
    values = tuple(sorted(values))
    if not values:
        return (0., 0., 0., 0.)
    return (values[0], values[(len(values) - 1) // 4],
            sum(values) / len(values), values[-1])


def _triangle_area(points):
    first = tuple(points[1][i] - points[0][i] for i in range(3))
    second = tuple(points[2][i] - points[0][i] for i in range(3))
    cross = (first[1] * second[2] - first[2] * second[1],
             first[2] * second[0] - first[0] * second[2],
             first[0] * second[1] - first[1] * second[0])
    return .5 * math.sqrt(sum(value * value for value in cross)) / \
        (THIRD_BLOCK_RADIUS ** 2)


def terminal_features(terminal, parent, center):
    scores = tuple(map(float, terminal["channel_scores"]))
    if len(scores) != len(CHANNEL_NAMES):
        raise AssertionError("third-block channel schema drift")
    score_features = scores + (
        sum(scores) / len(scores), min(scores), max(scores),
        max(scores) - min(scores))
    actions = tuple((tuple(map(float, point)), str(color))
                    for point, color in terminal["actions"])
    parents = tuple((tuple(map(float, point)), str(color))
                    for point, color in parent["parent_actions"])
    inherited = tuple((tuple(map(float, point)), str(color))
                      for point, color in parent["inherited_actions"])
    if len(actions) != 3 or len(parents) != 3 or len(inherited) != 3:
        raise AssertionError("terminal value expects three-action blocks")
    action_points = tuple(point for point, _color in actions)
    parent_points = tuple(point for point, _color in parents)
    inherited_points = tuple(point for point, _color in inherited)
    terminal_radii = _radii(action_points, center)
    parent_radii = _radii(parent_points, center)
    cross = tuple(math.dist(ap, pp) / THIRD_BLOCK_RADIUS
                  for ap, _ac in actions for pp, _pc in parents)
    same = tuple(math.dist(ap, pp) / THIRD_BLOCK_RADIUS
                 for ap, ac in actions for pp, pc in parents if ac == pc)
    different = tuple(math.dist(ap, pp) / THIRD_BLOCK_RADIUS
                      for ap, ac in actions for pp, pc in parents if ac != pc)
    inherited_cross = tuple(math.dist(ap, pp) / THIRD_BLOCK_RADIUS
                            for ap, _ac in actions
                            for pp, _pc in inherited)
    geometry = (
        *terminal_radii,
        *(value / THIRD_BLOCK_RADIUS for value in _distances(action_points)),
        _triangle_area(action_points),
        *(sum(color == wanted for _point, color in actions) / 3.
          for wanted in ("X", "Y", "Z")),
        *parent_radii,
        *(value / THIRD_BLOCK_RADIUS for value in _distances(parent_points)),
        *_summary(cross),
        _summary(same)[0], _summary(same)[2],
        _summary(different)[0], _summary(different)[2],
        *_summary(inherited_cross),
        *(terminal_radii[index] - parent_radii[index]
          for index in range(3)),
    )
    values = score_features + geometry
    if len(values) != len(FEATURE_NAMES) or any(
            not math.isfinite(value) for value in values):
        raise AssertionError("invalid third-block terminal features")
    return values


def _load_examples():
    source = load_source_result()
    if source["result_digest"] != SOURCE_RESULT_DIGEST:
        raise AssertionError("third-block source receipt drift")
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + THIRD_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    targets = tuple(_crop(oracle, center, THIRD_BLOCK_RADIUS,
                          "IQC-third-block-value-consumed-target")
                    for center in DEVELOPMENT_CENTERS)
    rows = []
    for receipt, target in zip(source["receipt"]["groups"], targets):
        truth = {_key(point): str(color) for point, color in
                 zip(target.positions, target.species)}
        center = tuple(map(float, receipt["center"]))
        for parent in receipt["parents"]:
            inherited_exact = all(truth.get(_key(point)) == color
                                  for point, color in parent["inherited_actions"])
            parent_exact = inherited_exact and all(
                truth.get(_key(point)) == color
                for point, color in parent["parent_actions"])
            for terminal in parent["terminals"]:
                correct = sum(truth.get(_key(point)) == color
                              for point, color in terminal["actions"])
                rows.append(Example(
                    int(receipt["group"]),
                    int(parent["parent_stable_index"]),
                    int(terminal["stable_index"]),
                    terminal_features(terminal, parent, center),
                    parent_exact and correct == 3, correct))
    digest = hashlib.sha256(repr(tuple(
        (row.group, row.parent, row.stable_index, row.features)
        for row in rows)).encode()).hexdigest()
    return tuple(rows), source, digest


def _fit(rows, representation, ridge):
    indices = representation[1]
    vectors = tuple(tuple(row.features[index] for index in indices)
                    for row in rows)
    means = tuple(sum(row[index] for row in vectors) / len(vectors)
                  for index in range(len(indices)))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (row[index] - means[index]) ** 2 for row in vectors) / len(vectors)))
                   for index in range(len(indices)))
    normalized = tuple(tuple((value - mean) / scale
                             for value, mean, scale in
                             zip(row, means, scales)) for row in vectors)
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
            for index in range(len(indices))))
    if len(contrasts) < 2:
        raise ValueError("terminal value needs two contrasted nuclei")
    average = tuple(sum(row[index] for row in contrasts) / len(contrasts)
                    for index in range(len(indices)))
    dispersion = tuple(sum((row[index] - average[index]) ** 2
                           for row in contrasts) / len(contrasts)
                       for index in range(len(indices)))
    weights = tuple(value / (ridge + variance)
                    for value, variance in zip(average, dispersion))
    payload = (representation, ridge, means, scales, weights,
               len({row.group for row in rows}))
    return FrozenValue(
        representation[0], indices, ridge, means, scales, weights,
        len({row.group for row in rows}),
        hashlib.sha256(repr(payload).encode()).hexdigest())


def _score(model, row):
    vector = tuple(row.features[index] for index in model.indices)
    return sum(weight * (value - mean) / scale
               for weight, value, mean, scale in
               zip(model.weights, vector, model.means, model.scales))


def _group_result(model, held):
    exact_paths = sum(row.exact for row in held)
    retained = []
    ranks = []
    for parent in sorted({row.parent for row in held}):
        rows = tuple(row for row in held if row.parent == parent)
        order = tuple(sorted(rows, key=lambda row: (
            -_score(model, row), row.stable_index)))
        retained.extend(order[:BEAM_PER_PARENT])
        rank = next((rank for rank, row in enumerate(order, 1)
                     if row.exact), None)
        if rank is not None:
            ranks.append(rank)
    retained_exact = sum(row.exact for row in retained)
    return exact_paths, retained_exact, bool(retained_exact), \
        min(ranks) if ranks else None


def _capacity(rows, representation, ridge):
    supplied = retained = rank_sum = 0
    for group in sorted({row.group for row in rows}):
        held = tuple(row for row in rows if row.group == group)
        if not any(row.exact for row in held):
            continue
        training = tuple(row for row in rows if row.group != group)
        result = _group_result(_fit(
            training, representation, ridge), held)
        supplied += 1
        retained += int(result[2])
        rank_sum += result[3] or 0
    return Capacity(representation[0], ridge, supplied, retained, rank_sum)


def _select_capacity(rows):
    capacities = tuple(_capacity(rows, representation, ridge)
                       for representation in REPRESENTATIONS for ridge in RIDGES)
    order = {name: index for index, (name, _indices) in
             enumerate(REPRESENTATIONS)}
    selected = min(capacities, key=lambda row: (
        -row.retained_groups, row.first_exact_rank_sum,
        order[row.representation], -row.ridge))
    representation = REPRESENTATIONS[order[selected.representation]]
    return selected, capacities, _fit(rows, representation, selected.ridge)


def _outer(rows):
    folds = []
    for heldout in sorted({row.group for row in rows}):
        held = tuple(row for row in rows if row.group == heldout)
        if not any(row.exact for row in held):
            continue
        training = tuple(row for row in rows if row.group != heldout)
        selected, _capacities, model = _select_capacity(training)
        result = _group_result(model, held)
        folds.append(Fold(
            heldout, True, selected.representation, selected.ridge,
            result[0], result[1], result[2], result[3], model.model_digest))
    return tuple(folds)


def _shuffle_labels(rows, index):
    labels = {}
    for group, parent in sorted({(row.group, row.parent) for row in rows}):
        local = [row.exact for row in rows
                 if row.group == group and row.parent == parent]
        random.Random(
            f"iqc-third-terminal-null-{index}-{group}-{parent}").shuffle(local)
        labels[group, parent] = iter(local)
    return tuple(Example(
        row.group, row.parent, row.stable_index, row.features,
        next(labels[row.group, row.parent]), row.correct_actions)
        for row in rows)


def evaluate():
    rows, source, dataset_digest = _load_examples()
    folds = _outer(rows)
    retained = sum(fold.retained_exact_group for fold in folds)
    rank_sum = sum(fold.first_exact_rank or 0 for fold in folds)
    controls = []
    for index in range(SHUFFLES):
        shuffled = _shuffle_labels(rows, index)
        null_folds = _outer(shuffled)
        # Selection is learned from shuffled labels; performance is rescored
        # against the original immutable labels on the same held-out groups.
        rescored = []
        for null_fold in null_folds:
            training = tuple(row for row in shuffled
                             if row.group != null_fold.heldout_group)
            representation = next(row for row in REPRESENTATIONS
                                  if row[0] == null_fold.selected_representation)
            model = _fit(training, representation, null_fold.selected_ridge)
            held = tuple(row for row in rows
                         if row.group == null_fold.heldout_group)
            rescored.append(_group_result(model, held))
        controls.append((sum(result[2] for result in rescored),
                         sum(result[3] or 0 for result in rescored)))
    retention_p = (1 + sum(value[0] >= retained for value in controls)) / \
        (SHUFFLES + 1)
    rank_p = (1 + sum(value[1] <= rank_sum for value in controls)) / \
        (SHUFFLES + 1)
    incumbent = source["exact_third_block_supply_groups"]
    gate = retained > incumbent and retention_p <= .05 and rank_p <= .05
    body = {
        "schema_version": 1,
        "source_result_digest": source["result_digest"],
        "dataset_digest": dataset_digest,
        "terminal_examples": len(rows),
        "exact_terminal_examples": sum(row.exact for row in rows),
        "feature_names": FEATURE_NAMES,
        "representations": tuple((name, indices)
                                 for name, indices in REPRESENTATIONS),
        "ridges": RIDGES,
        "beam_per_parent": BEAM_PER_PARENT,
        "folds": tuple(asdict(fold) for fold in folds),
        "supplied_groups": len(folds),
        "retained_exact_groups": retained,
        "retained_exact_paths": sum(fold.retained_exact_paths
                                    for fold in folds),
        "first_exact_rank_sum": rank_sum,
        "incumbent_retained_groups": incumbent,
        "shuffles": SHUFFLES,
        "shuffle_retained_groups": tuple(value[0] for value in controls),
        "shuffle_first_exact_rank_sums": tuple(value[1] for value in controls),
        "retention_p_value": retention_p,
        "rank_p_value": rank_p,
        "causal_superiority_gate_passed": gate,
        "candidate_geometry_unchanged": True,
        "same_four_per_parent_budget": True,
        "proper_se3_invariant_features": True,
        "target_used_for_candidate_generation": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["source_result_digest"] != SOURCE_RESULT_DIGEST
            or body["terminal_examples"] != 5091
            or body["exact_terminal_examples"] != 90
            or tuple(body["feature_names"]) != FEATURE_NAMES
            or body["beam_per_parent"] != BEAM_PER_PARENT
            or not body["candidate_geometry_unchanged"]
            or not body["same_four_per_parent_budget"]
            or not body["proper_se3_invariant_features"]
            or body["target_used_for_candidate_generation"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("IQC third-block terminal value drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("IQC third-block terminal value digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("IQC third-block value fixture byte drift")
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
