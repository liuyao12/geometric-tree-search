#!/usr/bin/env python3
"""Build ID-free parent→child boundary-obligation transitions for IQC GCTS."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import _partial, load_default_runtime
from materials_gcts_iqc_parent_child_macro_dataset import (
    DEFAULT_FIXTURE as MACRO_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_MACRO_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_MACRO_SHA256,
    validate_dataset as validate_macro_dataset)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _replay_first_terminal)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as SOURCE_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_SOURCE_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_SOURCE_SHA256,
    load_fixture_json as load_source_fixture,
    validate_dataset as validate_source_dataset)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


COLORS = ("X", "Y", "Z")
GRAPH_FEATURE_NAMES = (
    "node_count", "isolated_fraction", "overlap_edge_fraction",
    "incidence_edge_fraction", "witnessed_incidence_fraction",
    "matched_fraction_min", "matched_fraction_mean", "matched_fraction_max",
    "training_support_min", "training_support_mean", "training_support_max",
    "action_color_X", "action_color_Y", "action_color_Z",
    "separation_mean", "separation_std", "separation_min", "separation_max",
    "chirality_negative", "chirality_zero", "chirality_positive",
    "shared_species_per_relation", "shared_profiles_per_relation",
)
FEATURE_NAMES = tuple(
    [f"parent_{name}" for name in GRAPH_FEATURE_NAMES]
    + [f"child_{name}" for name in GRAPH_FEATURE_NAMES]
    + [f"delta_{name}" for name in GRAPH_FEATURE_NAMES])
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_parent_child_port_transition_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "35d06843ef5a5433023b05c95a229981178a8be889bfe84e8a994796b18c7441"
EXPECTED_DATASET_DIGEST = \
    "8d6cf2ec3c23b8c370af6dd361ebbf2f77fbd6941214960b90cd7d303beab85d"


def _mean_std_min_max(values):
    if not values:
        return 0., 0., 0., 0.
    mean = sum(values) / len(values)
    return (mean, math.sqrt(sum((value - mean) ** 2 for value in values)
                            / len(values)), min(values), max(values))


def _species_token(value):
    text = repr(value)
    return next((color for color in COLORS if f"'{color}'" in text), "?")


def graph_features(graph):
    nodes = tuple(graph.get("nodes", ()))
    edges = tuple(graph.get("edges", ()))
    incidence = tuple(graph.get("incidence_edges", ()))
    relations = edges + incidence
    node_count = len(nodes)
    pair_capacity = max(1, node_count * (node_count - 1) / 2)
    matched = tuple(float(node["matched_atoms"])
                    / max(1., float(node["prototype_atoms"]))
                    for node in nodes)
    support = tuple(float(node["training_group_support"]) / 10.
                    for node in nodes)
    matched_stats = _mean_std_min_max(matched)
    support_stats = _mean_std_min_max(support)
    separations = tuple(float(edge["separation_bin"]) / 100.
                        for edge in relations)
    separation_stats = _mean_std_min_max(separations)
    chiralities = tuple(int(edge["chirality"]) for edge in relations)
    relation_count = max(1, len(relations))
    shared_species = sum(sum(int(count) for _species, count in
                             edge.get("shared_species", ()))
                         for edge in relations)
    shared_profiles = sum(len(edge.get("shared_distance_profiles", ()))
                          for edge in relations)
    result = (
        node_count / 3., float(graph.get("isolated_nodes", 0))
        / max(1, node_count), len(edges) / pair_capacity,
        len(incidence) / pair_capacity,
        sum(bool(edge.get("connection_witnessed", False))
            for edge in incidence) / max(1, len(incidence)),
        matched_stats[2], matched_stats[0], matched_stats[3],
        support_stats[2], support_stats[0], support_stats[3],
        *(sum(_species_token(node.get("action_species")) == color
              for node in nodes) / max(1, node_count) for color in COLORS),
        separation_stats[0], separation_stats[1],
        separation_stats[2], separation_stats[3],
        sum(value < 0 for value in chiralities) / relation_count,
        sum(value == 0 for value in chiralities) / relation_count,
        sum(value > 0 for value in chiralities) / relation_count,
        shared_species / relation_count, shared_profiles / relation_count,
    )
    if len(result) != len(GRAPH_FEATURE_NAMES) or not all(map(math.isfinite, result)):
        raise AssertionError("port-transition graph feature drift")
    return tuple(result)


def transition_features(parent_graph, child_graph):
    parent = graph_features(parent_graph)
    child = graph_features(child_graph)
    return parent + child + tuple(right - left
                                  for left, right in zip(parent, child))


def _worker(payload):
    group_index, center, seed_positions, seed_species, macro_group, source_group = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    parent_actions = tuple((tuple(point), str(color)) for point, color in
                           macro_group["rows"][0]["parent_actions"])
    parent_state = _replay_first_terminal(source, runtime, parent_actions)
    _partial_features, parent_graph = _partial(
        source, parent_state, runtime["grouped_vocabulary"])
    parent_json = asdict(parent_graph)
    if parent_json["target_used"] or parent_json["lattice_coordinates_used"]:
        raise AssertionError("parent graph leaks target/lattice state")
    geometry = tuple({
        "group": group_index,
        "stable_index": int(macro_row["stable_index"]),
        "features": transition_features(parent_json, source_row["graph"]),
    } for macro_row, source_row in zip(
        macro_group["rows"], source_group["rows"]))
    geometry_digest = hashlib.sha256(canonical_json(geometry)).hexdigest()
    rows = tuple({
        **row,
        "exact": bool(macro_row["exact"]),
        "correct_sites": int(macro_row["correct_sites"]),
    } for row, macro_row in zip(geometry, macro_group["rows"]))
    return {
        "group": group_index,
        "center": tuple(center),
        "parent_graph_digest": parent_json["canonical_digest"],
        "geometry_digest_before_labels": geometry_digest,
        "rows": rows,
        "raw_type_ids_in_features": False,
        "target_used_for_geometry": False,
        "labels_joined_after_geometry_frozen": True,
    }


def _prepare_pool():
    import concurrent.futures.process as process
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def build_dataset(*, workers=1):
    macro_raw = MACRO_FIXTURE.read_bytes()
    if hashlib.sha256(macro_raw).hexdigest() != EXPECTED_MACRO_SHA256:
        raise AssertionError("macro fixture byte drift")
    macro = validate_macro_dataset(json.loads(gzip.decompress(macro_raw)))
    if macro["dataset_digest"] != EXPECTED_MACRO_DIGEST:
        raise AssertionError("macro dataset digest drift")
    source_raw, source_payload = load_source_fixture(SOURCE_FIXTURE)
    if hashlib.sha256(source_raw).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise AssertionError("source fixture byte drift")
    source = validate_source_dataset(source_payload)
    if source["dataset_digest"] != EXPECTED_SOURCE_DIGEST:
        raise AssertionError("source dataset digest drift")
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "IQC-port-transition-seed")
                  for center in DEVELOPMENT_CENTERS)
    payloads = tuple((
        index, center, tuple(seed.positions), tuple(seed.species),
        macro_group, source_group)
        for index, (center, seed, macro_group, source_group) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, macro["groups"], source["groups"])))
    if workers == 1:
        groups = tuple(_worker(row) for row in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_worker, payloads))
    body = {
        "schema_version": 1,
        "macro_dataset_digest": macro["dataset_digest"],
        "source_dataset_digest": source["dataset_digest"],
        "development_groups": len(groups),
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "examples": sum(len(group["rows"]) for group in groups),
        "exact_examples": sum(row["exact"] for group in groups
                              for row in group["rows"]),
        "groups": groups,
        "raw_type_ids_in_features": False,
        "proper_se3_invariant": True,
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
            or body["macro_dataset_digest"] != EXPECTED_MACRO_DIGEST
            or body["source_dataset_digest"] != EXPECTED_SOURCE_DIGEST
            or body["development_groups"] != 10
            or body["feature_count"] != len(FEATURE_NAMES)
            or body["raw_type_ids_in_features"]
            or not body["proper_se3_invariant"]
            or body["target_used_for_geometry"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]):
        raise AssertionError("parent-child port-transition dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("port-transition dataset digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("port-transition fixture byte drift")
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
