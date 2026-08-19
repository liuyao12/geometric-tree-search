#!/usr/bin/env python3
"""Freeze target-free one-action consequences of post-self-feed IQC terminals.

The source terminal corpus contains complete three-action blocks on ten
already-consumed development nuclei.  This builder reconstructs each terminal,
orders at most eight immediately available child actions with the already
frozen pose/port marking, advances each child once, and stores aggregate local
features of the resulting frontiers.  The outer development targets are never
opened here: labels are copied verbatim from the sealed source corpus only
after every consequence vector has been reconstructed and its source digest
has matched.
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
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import (
    BRANCH_NAMES, SECTION_NAMES, _child, _local_section, action_key,
    branch_features, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as SOURCE_FIXTURE,
    EXPECTED_DATASET_DIGEST as SOURCE_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_SOURCE_SHA256,
    OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS, SUCCESSOR_FEATURE_NAMES,
    terminal_successor_features, validate_dataset as validate_source_dataset)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state


MAXIMUM_CHILDREN = 8
CHILD_FEATURE_NAMES = BRANCH_NAMES + SECTION_NAMES + SUCCESSOR_FEATURE_NAMES
SUMMARY_NAMES = ("top", "mean", "maximum")
FEATURE_NAMES = (
    ("log_child_count",)
    + tuple(f"child_color_fraction:{color}" for color in ("X", "Y", "Z"))
    + tuple(f"{summary}:{name}" for summary in SUMMARY_NAMES
            for name in CHILD_FEATURE_NAMES)
)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_consequence_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "f0a6bb826a3083f3eac3cf7f79036e5d22a7b3a3928db02c1c8a45639c6fa1c2"
EXPECTED_DATASET_DIGEST = \
    "37a234c23bcbf40c926628fb7a4424b186a0d644b73d8a9aa48f3824b396414c"


def _mean(rows, width):
    return tuple(sum(row[index] for row in rows) / len(rows)
                 for index in range(width)) if rows else (0.,) * width


def _maximum(rows, width):
    return tuple(max(row[index] for row in rows)
                 for index in range(width)) if rows else (0.,) * width


def _numerically_equal(first, second, tolerance=1e-9):
    return len(first) == len(second) and all(
        abs(float(left) - float(right)) <= tolerance
        for left, right in zip(first, second))


def _child_feature(source, state, point, descriptor, runtime):
    child = _child(
        source, runtime["connection"], runtime["state_model"], state, point,
        descriptor, SECOND_BLOCK_RADIUS)
    return child, (tuple(branch_features(child)) + _local_section(child)
                   + terminal_successor_features(
                       child, runtime["state_model"], source.group,
                       SECOND_BLOCK_RADIUS))


def terminal_consequence_features(source, state, runtime):
    """Return a bounded, target-free summary of one-step child frontiers."""
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
        -score_pose_port_state(runtime["state_model"], descriptors[point]),
        -state.proposals.votes[point], point)))[:MAXIMUM_CHILDREN]
    children = tuple(_child_feature(
        source, state, point, descriptors[point], runtime)
        for point in ordered)
    vectors = tuple(row for _child_state, row in children)
    width = len(CHILD_FEATURE_NAMES)
    if any(len(row) != width for row in vectors):
        raise AssertionError("child consequence feature schema drift")
    colors = tuple(child.actions[-1][1] for child, _row in children)
    fractions = tuple(colors.count(color) / max(1, len(colors))
                      for color in ("X", "Y", "Z"))
    top = vectors[0] if vectors else (0.,) * width
    values = (math.log1p(len(vectors)),) + fractions + top \
        + _mean(vectors, width) + _maximum(vectors, width)
    if len(values) != len(FEATURE_NAMES) or any(
            not math.isfinite(value) for value in values):
        raise AssertionError("invalid terminal consequence features")
    return values


def _evaluate_group(payload):
    group_index, center, seed_positions, seed_species, first_truth, expected = \
        payload
    runtime = load_default_runtime()
    first_source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    first_states, _counts = _complete_states_at_radius(
        first_source, runtime, TARGET_RADIUS)
    first_exact = tuple(state for state in first_states if all(
            first_truth.get(tuple(round(value, 6) for value in point)) == color
            for point, color in state.actions))
    inherited = tuple(state for state in first_exact if hashlib.sha256(
        repr(action_key(state.actions)).encode()).hexdigest()
        == expected["inherited_action_digest"])
    if len(inherited) != 1:
        raise AssertionError(f"development group {group_index} lacks inherited state")
    inherited = inherited[0]
    second_source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited.positions,
        seed_species=inherited.species)
    states, counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    if tuple(counts) != tuple(expected["second_block_counts"]):
        raise AssertionError("source candidate-count drift")

    # Reconstruct the source geometry and every inexpensive invariant feature
    # slice before copying any labels.  The stored full source digest remains
    # linked below; re-mining its recurring-support graph for every terminal
    # would dominate this one-step consequence audit without changing a pose.
    prefix_width = len(BRANCH_NAMES) + len(SECTION_NAMES)
    for stable_index, state in enumerate(states):
        label = expected["rows"][stable_index]
        scalar_prefix = tuple(branch_features(state)) + _local_section(state)
        successor = terminal_successor_features(
            state, runtime["state_model"], center, SECOND_BLOCK_RADIUS)
        expected_features = tuple(map(float, label["features"]))
        index_ok = int(label["stable_index"]) == stable_index
        colors_ok = tuple(label["action_colors"]) == tuple(
            color for _point, color in state.actions)
        prefix_ok = _numerically_equal(
            scalar_prefix, expected_features[:prefix_width])
        successor_ok = _numerically_equal(
            successor, expected_features[-len(SUCCESSOR_FEATURE_NAMES):])
        if not (index_ok and colors_ok and prefix_ok and successor_ok):
            raise AssertionError(
                f"source self-fed terminal geometry drift: group={group_index} "
                f"stable={stable_index} index={index_ok} colors={colors_ok} "
                f"prefix={prefix_ok} successor={successor_ok}")
    if len(states) != len(expected["rows"]):
        raise AssertionError("source self-fed terminal count drift")

    consequence_rows = []
    for stable_index, state in enumerate(states):
        label = expected["rows"][stable_index]
        consequence_rows.append({
            "group": group_index,
            "stable_index": stable_index,
            "features": terminal_consequence_features(
                second_source, state, runtime),
            "action_colors": tuple(color for _point, color in state.actions),
            "exact": bool(label["exact"]),
            "correct_sites": int(label["correct_sites"]),
        })
    return {
        "group": group_index,
        "center": tuple(center),
        "source_feature_digest": expected["feature_digest"],
        "source_inherited_action_digest":
            expected["inherited_action_digest"],
        "source_geometry_and_feature_slices_verified": True,
        "candidate_counts": tuple(counts),
        "rows": consequence_rows,
        "target_used_for_consequence_features": False,
    }


def build_dataset(*, workers=1):
    raw, source_payload = load_fixture_json(SOURCE_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise AssertionError("source terminal fixture byte drift")
    source = validate_source_dataset(source_payload)
    if source["dataset_digest"] != SOURCE_DATASET_DIGEST:
        raise AssertionError("source terminal dataset drift")

    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "IQC-consequence-seed")
                  for center in DEVELOPMENT_CENTERS)
    first_targets = tuple(_crop(oracle, center, TARGET_RADIUS,
                                "IQC-consequence-consumed-first-target")
                          for center in DEVELOPMENT_CENTERS)
    payloads = []
    for index, (center, seed, first, expected) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, first_targets, source["groups"])):
        first_truth = {tuple(round(value, 6) for value in point): str(color)
                       for point, color in zip(first.positions, first.species)}
        payloads.append((index, center, tuple(seed.positions),
                         tuple(seed.species), first_truth, expected))
    if workers == 1:
        groups = tuple(_evaluate_group(payload) for payload in payloads)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_evaluate_group, payloads))
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "development_groups": len(groups),
        "maximum_children": MAXIMUM_CHILDREN,
        "feature_names": FEATURE_NAMES,
        "groups": groups,
        "target_used_for_consequence_features": False,
        "labels_copied_from_consumed_development_fixture": True,
        "fresh_confirmation_claimed": False,
    }
    digest = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**body, "dataset_digest": digest}


def load_fixture_json(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    return raw, json.loads(gzip.decompress(raw))


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != digest or body["schema_version"] != 1
            or body["source_dataset_digest"] != SOURCE_DATASET_DIGEST
            or body["development_groups"] != len(DEVELOPMENT_CENTERS)
            or tuple(body["feature_names"]) != FEATURE_NAMES
            or body["maximum_children"] != MAXIMUM_CHILDREN
            or body["target_used_for_consequence_features"]
            or not body["labels_copied_from_consumed_development_fixture"]
            or body["fresh_confirmation_claimed"]):
        raise AssertionError("post-self-fed consequence dataset drift")
    rows = [row for group in body["groups"] for row in group["rows"]]
    if (len(rows) != 1278 or sum(row["exact"] for row in rows) != 142
            or any(len(row["features"]) != len(FEATURE_NAMES)
                   or len(row["action_colors"]) != 3
                   for row in rows)):
        raise AssertionError("invalid consequence row corpus")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("post-self-fed consequence dataset digest drift")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.workers <= 0:
        raise SystemExit("--workers must be positive")
    row = build_dataset(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
