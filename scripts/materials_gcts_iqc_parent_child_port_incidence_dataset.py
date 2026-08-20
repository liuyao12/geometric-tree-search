#!/usr/bin/env python3
"""Freeze exact six-node parent→child port-incidence graphs for IQC GCTS."""

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
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_parent_child_macro_dataset import (
    DEFAULT_FIXTURE as MACRO_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_MACRO_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_MACRO_SHA256,
    validate_dataset as validate_macro_dataset)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _replay_first_terminal)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_parent_child_port_incidence_transition import (
    combine_port_incidence_transition_blocks,
    port_incidence_transition_block)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_parent_child_port_incidence_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "6bb33e131fa621e26db65168cf65f5629be6ce9871ae5707588a3096bbdf2f7e"
EXPECTED_DATASET_DIGEST = \
    "6a4b402292f8046d653edb686b6cb49091f2d8d9e4ae45b0fe183a7fb923217a"


def _worker(payload):
    index, center, seed_positions, seed_species, macro_group = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    parent_actions = tuple((tuple(point), str(color)) for point, color in
                           macro_group["rows"][0]["parent_actions"])
    if any(tuple((tuple(point), str(color)) for point, color in
                 row["parent_actions"]) != parent_actions
           for row in macro_group["rows"]):
        raise AssertionError("group parent action changed across children")
    parent_state = _replay_first_terminal(source, runtime, parent_actions)
    vocabulary = runtime["grouped_vocabulary"]
    support = vocabulary.training_group_support
    frozen = vocabulary.vocabulary
    parent = port_incidence_transition_block(
        frozen, support, tuple(source.seed_positions),
        tuple(source.seed_species),
        tuple(point for point, _color in parent_actions),
        tuple(color for _point, color in parent_actions), "parent")
    scale = float(macro_group["nearest_neighbor_scale"])
    geometry = []
    for row in macro_group["rows"]:
        child_actions = tuple((tuple(point), str(color))
                              for point, color in row["child_actions"])
        child = port_incidence_transition_block(
            frozen, support, tuple(parent_state.positions),
            tuple(parent_state.species),
            tuple(point for point, _color in child_actions),
            tuple(color for _point, color in child_actions), "child")
        graph = combine_port_incidence_transition_blocks(
            parent, child, distance_scale=scale)
        if (graph.target_used or graph.lattice_coordinates_used
                or len(graph.nodes) != 6 or len(graph.incidence_edges) != 15
                or any(node.support_type_id for node in graph.nodes)):
            raise AssertionError("invalid frozen transition-incidence graph")
        geometry.append({
            "group": index,
            "stable_index": int(row["stable_index"]),
            "graph": asdict(graph),
        })
    geometry = tuple(geometry)
    geometry_digest = hashlib.sha256(canonical_json(geometry)).hexdigest()
    rows = tuple({
        **item,
        "exact": bool(label["exact"]),
        "correct_sites": int(label["correct_sites"]),
    } for item, label in zip(geometry, macro_group["rows"]))
    return {
        "group": index,
        "center": tuple(center),
        "geometry_digest_before_labels": geometry_digest,
        "rows": rows,
        "labels_joined_after_geometry_frozen": True,
        "target_used_for_geometry": False,
    }


def _prepare_pool():
    import concurrent.futures.process as process
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def build_dataset(*, workers=1):
    raw = MACRO_FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_MACRO_SHA256:
        raise AssertionError("macro fixture byte drift")
    macro = validate_macro_dataset(json.loads(gzip.decompress(raw)))
    if macro["dataset_digest"] != EXPECTED_MACRO_DIGEST:
        raise AssertionError("macro dataset digest drift")
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "IQC-parent-child-incidence-seed")
                  for center in DEVELOPMENT_CENTERS)
    payloads = tuple((index, center, tuple(seed.positions),
                      tuple(seed.species), group)
                     for index, (center, seed, group) in enumerate(zip(
                         DEVELOPMENT_CENTERS, seeds, macro["groups"])))
    if workers == 1:
        groups = tuple(_worker(row) for row in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_worker, payloads))
    body = {
        "schema_version": 1,
        "macro_dataset_digest": macro["dataset_digest"],
        "development_groups": len(groups),
        "examples": sum(len(group["rows"]) for group in groups),
        "exact_examples": sum(row["exact"] for group in groups
                              for row in group["rows"]),
        "groups": groups,
        "nodes_per_graph": 6,
        "incidence_edges_per_graph": 15,
        "raw_type_ids_in_graph": False,
        "proper_se3_invariant": True,
        "candidate_geometry_unchanged": True,
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
            or body["development_groups"] != 10
            or body["examples"] != 1278
            or body["exact_examples"] != 142
            or body["nodes_per_graph"] != 6
            or body["incidence_edges_per_graph"] != 15
            or body["raw_type_ids_in_graph"]
            or not body["proper_se3_invariant"]
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_geometry"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]):
        raise AssertionError("parent-child incidence dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("parent-child incidence dataset digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("parent-child incidence fixture drift")
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
