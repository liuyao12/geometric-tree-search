#!/usr/bin/env python3
"""Build a grouped IQC parent→child cluster-of-clusters corpus.

Each example is a six-action macro: three inherited first-block actions and
three second-block actions.  Its descriptor is translation invariant,
proper-SE(3) invariant, permutation invariant within each block, colored, and
normalized by the target-free seed nearest-neighbor scale.  Existing consumed
development labels are joined only after every macro geometry is frozen.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import action_key, load_default_runtime
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as SOURCE_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_SOURCE_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_SOURCE_SHA256,
    SECOND_BLOCK_RADIUS, load_fixture_json as load_source_fixture,
    validate_dataset as validate_source_dataset)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


COLORS = ("X", "Y", "Z")
FEATURE_NAMES = tuple(
    [f"parent_count_{color}" for color in COLORS]
    + [f"child_count_{color}" for color in COLORS]
    + [f"parent_distance_{index}" for index in range(3)]
    + [f"child_distance_{index}" for index in range(3)]
    + [f"cross_distance_{index}" for index in range(9)]
    + ["centroid_separation"]
    + [f"parent_radius_{name}" for name in ("mean", "std", "max")]
    + [f"child_radius_{name}" for name in ("mean", "std", "max")]
    + [f"child_nearest_parent_{index}" for index in range(3)]
    + [f"cross_connection_fraction_{value}" for value in ("1p5", "2p5", "4")]
    + ["proper_chirality"]
    + [f"cross_{left}_{right}_{stat}"
       for left in COLORS for right in COLORS
       for stat in ("count", "minimum", "mean")]
)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_parent_child_macro_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "e8855625ad7fcff40bf0f414fbd95a12e14b4aee3067f9169878a06c5af4aa1a"
EXPECTED_DATASET_DIGEST = \
    "b4841e21d3fce35d80d1c9611d253bbb269d0bb52ce3e7e8f5e056b44b6cd181"


def _mean_std_max(values):
    mean = sum(values) / len(values)
    return mean, math.sqrt(sum((value - mean) ** 2 for value in values)
                           / len(values)), max(values)


def _centroid(points):
    return tuple(sum(point[axis] for point in points) / len(points)
                 for axis in range(3))


def _sub(left, right):
    return tuple(a - b for a, b in zip(left, right))


def _triple(first, second, third):
    return (
        first[0] * (second[1] * third[2] - second[2] * third[1])
        - first[1] * (second[0] * third[2] - second[2] * third[0])
        + first[2] * (second[0] * third[1] - second[1] * third[0]))


def _canonical_block(block, all_actions):
    return tuple(sorted(block, key=lambda item: (
        item[1], tuple(sorted(
            (other[1], round(math.dist(item[0], other[0]), 8))
            for other in all_actions if other is not item)))))


def macro_features(parent_actions, child_actions, scale):
    parent = tuple((tuple(map(float, point)), str(color))
                   for point, color in parent_actions)
    child = tuple((tuple(map(float, point)), str(color))
                  for point, color in child_actions)
    if len(parent) != 3 or len(child) != 3 or scale <= 0:
        raise ValueError("macro descriptor requires two three-action blocks")
    all_actions = parent + child
    parent = _canonical_block(parent, all_actions)
    child = _canonical_block(child, all_actions)
    p_points = tuple(row[0] for row in parent)
    c_points = tuple(row[0] for row in child)
    p_center, c_center = _centroid(p_points), _centroid(c_points)
    p_distances = tuple(sorted(math.dist(left, right) / scale
                               for index, left in enumerate(p_points)
                               for right in p_points[index + 1:]))
    c_distances = tuple(sorted(math.dist(left, right) / scale
                               for index, left in enumerate(c_points)
                               for right in c_points[index + 1:]))
    cross = tuple(math.dist(left, right) / scale
                  for left in p_points for right in c_points)
    p_radii = tuple(math.dist(point, p_center) / scale for point in p_points)
    c_radii = tuple(math.dist(point, c_center) / scale for point in c_points)
    nearest = tuple(sorted(min(math.dist(child_point, parent_point)
                               for parent_point in p_points) / scale
                           for child_point in c_points))
    direction = _sub(c_center, p_center)
    chirality = _triple(
        _sub(p_points[1], p_points[0]),
        _sub(p_points[2], p_points[0]), direction) / scale ** 3
    colored_cross = []
    for left_color in COLORS:
        for right_color in COLORS:
            values = tuple(math.dist(left[0], right[0]) / scale
                           for left in parent if left[1] == left_color
                           for right in child if right[1] == right_color)
            colored_cross.extend((
                len(values) / 9., min(values, default=0.),
                sum(values) / len(values) if values else 0.))
    features = tuple(
        [sum(color == expected for _point, color in parent) / 3.
         for expected in COLORS]
        + [sum(color == expected for _point, color in child) / 3.
           for expected in COLORS]
        + list(p_distances) + list(c_distances) + sorted(cross)
        + [math.dist(p_center, c_center) / scale]
        + list(_mean_std_max(p_radii)) + list(_mean_std_max(c_radii))
        + list(nearest)
        + [sum(value <= threshold for value in cross) / len(cross)
           for threshold in (1.5, 2.5, 4.)]
        + [chirality] + colored_cross)
    if len(features) != len(FEATURE_NAMES) or not all(map(math.isfinite, features)):
        raise AssertionError("macro feature schema drift")
    return features


def _minimum_distance(positions):
    return min(math.dist(left, right)
               for index, left in enumerate(positions)
               for right in positions[index + 1:]
               if math.dist(left, right) > 1e-8)


def _worker(payload):
    group_index, center, seed_positions, seed_species, expected = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    first_states, first_counts = _complete_states_at_radius(
        source, runtime, TARGET_RADIUS)
    first_states = tuple(sorted(first_states,
                                key=lambda state: action_key(state.actions)))
    inherited = tuple(state for state in first_states
                      if hashlib.sha256(repr(action_key(
                          state.actions)).encode()).hexdigest()
                      == expected["inherited_action_digest"])
    if len(inherited) != 1:
        raise AssertionError("inherited parent action digest drift")
    inherited = inherited[0]
    second_source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(inherited.positions),
        seed_species=tuple(inherited.species))
    second_states, second_counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    second_states = tuple(sorted(second_states,
                                 key=lambda state: action_key(state.actions)))
    expected_rows = tuple(expected["rows"])
    if (len(second_states) != len(expected_rows)
            or tuple(second_counts) != tuple(expected["second_block_counts"])):
        raise AssertionError("macro child candidate universe drift")
    scale = _minimum_distance(seed_positions)
    geometry = tuple({
        "group": group_index,
        "stable_index": stable_index,
        "features": macro_features(
            inherited.actions, state.actions, scale),
        "parent_actions": action_key(inherited.actions),
        "child_actions": action_key(state.actions),
    } for stable_index, state in enumerate(second_states))
    geometry_digest = hashlib.sha256(canonical_json(geometry)).hexdigest()
    rows = tuple({
        **row,
        "exact": bool(label["exact"]),
        "correct_sites": int(label["correct_sites"]),
    } for row, label in zip(geometry, expected_rows))
    return {
        "group": group_index,
        "center": tuple(center),
        "seed_atoms": len(seed_positions),
        "nearest_neighbor_scale": scale,
        "first_candidate_counts": tuple(first_counts),
        "second_candidate_counts": tuple(second_counts),
        "inherited_action_digest": expected["inherited_action_digest"],
        "geometry_digest_before_labels": geometry_digest,
        "rows": rows,
        "target_used_for_geometry": False,
        "labels_copied_after_geometry_frozen": True,
    }


def _prepare_pool():
    import concurrent.futures.process as process
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def build_dataset(*, workers=1):
    raw, payload = load_source_fixture(SOURCE_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise AssertionError("source terminal fixture byte drift")
    source = validate_source_dataset(payload)
    if source["dataset_digest"] != EXPECTED_SOURCE_DIGEST:
        raise AssertionError("source terminal dataset drift")
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "IQC-parent-child-macro-seed")
                  for center in DEVELOPMENT_CENTERS)
    payloads = tuple((
        index, center, tuple(seed.positions), tuple(seed.species), expected)
        for index, (center, seed, expected) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, source["groups"])))
    if workers == 1:
        groups = tuple(_worker(row) for row in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_worker, payloads))
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "development_groups": len(groups),
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "examples": sum(len(group["rows"]) for group in groups),
        "exact_examples": sum(row["exact"] for group in groups
                              for row in group["rows"]),
        "groups": groups,
        "proper_se3_invariant": True,
        "translation_invariant": True,
        "permutation_invariant_within_blocks": True,
        "chirality_preserved": True,
        "target_used_for_geometry": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
    }
    return {**body, "dataset_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["source_dataset_digest"] != EXPECTED_SOURCE_DIGEST
            or body["development_groups"] != 10
            or body["feature_count"] != len(FEATURE_NAMES)
            or not body["proper_se3_invariant"]
            or not body["translation_invariant"]
            or not body["permutation_invariant_within_blocks"]
            or not body["chirality_preserved"]
            or body["target_used_for_geometry"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]):
        raise AssertionError("parent-child macro dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("parent-child macro dataset digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("parent-child macro fixture byte drift")
    return validate_dataset(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = build_dataset(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
