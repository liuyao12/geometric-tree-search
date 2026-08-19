#!/usr/bin/env python3
"""Freeze typed child-frontier graphs for consumed post-self-feed terminals."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_child_frontier_graph import (
    ChildFrontierAction, ChildFrontierEdge, ChildFrontierGraph,
    ChildFrontierNode, child_frontier_graph, count_bin)
from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import (
    _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as SOURCE_FIXTURE,
    EXPECTED_DATASET_DIGEST as SOURCE_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_SOURCE_SHA256,
    OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS, load_fixture_json,
    validate_dataset as validate_source_dataset)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch_fast
from materials_gcts_port_incidence_search import (
    port_incidence_state)
from materials_gcts_pose_port_state_marking import (
    pose_port_state_code, score_pose_port_state)
from materials_gcts_successor_state_marking import successor_outgoing_points


MAXIMUM_CHILDREN = 8
MAXIMUM_ROLES = 4
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_child_graph_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "4ac7f755274eb36245afa0582757b2a630f87a06ede6ca090c0671059406e144"
EXPECTED_DATASET_DIGEST = \
    "4bdd54e40094576bb561cc652614fc18ee4a062e7f92dc45397b6c534819a965"


def _role_key(role, count):
    return (str(role.parent_color), tuple(map(int, role.parent_neighbors)),
            str(role.source_color), tuple(map(int, role.source_neighbors)),
            int(role.separation_bin), count_bin(int(count)))


def _roles(state):
    return tuple(sorted(_role_key(role, count)
                        for role, count in state.roles))


def _minimum_distance(positions):
    return min(math.dist(first, second)
               for first, second in itertools.combinations(positions, 2)
               if math.dist(first, second) > 1e-8)


def _candidate_action(source, state, point, descriptor, runtime,
                      minimum_distance):
    color = str(_dominant_source_color(state.proposals, point))
    probability = score_pose_port_state(runtime["state_model"], descriptor)
    code = pose_port_state_code(
        runtime["state_model"].token_marking, descriptor,
        state_bin_width=runtime["state_model"].state_bin_width,
        channel_families=runtime["state_model"].channel_families)
    incoming = port_incidence_state(
        state.proposals, (point,), maximum_roles=MAXIMUM_ROLES,
        minimum_multiplicity=1)
    child = _child(
        source, runtime["connection"], runtime["state_model"], state, point,
        descriptor, SECOND_BLOCK_RADIUS)
    new_parent = len(child.positions) - 1
    outgoing_points = successor_outgoing_points(
        child.proposals, new_parent_index=new_parent,
        occupied_positions=child.positions, minimum_distance=minimum_distance)
    outgoing = port_incidence_state(
        child.proposals, outgoing_points, maximum_roles=MAXIMUM_ROLES,
        minimum_multiplicity=1)
    outgoing_sites = tuple((tuple(candidate), str(_dominant_source_color(
        child.proposals, candidate))) for candidate in outgoing_points)
    node = ChildFrontierNode(
        color, tuple(map(int, code)), count_bin(state.proposals.votes[point]),
        int(round(probability * 20)), _roles(incoming),
        count_bin(incoming.mass + incoming.overflow_mass), _roles(outgoing),
        count_bin(outgoing.mass + outgoing.overflow_mass),
        tuple(sorted({color for _point, color in outgoing_sites})),
        not outgoing_sites)
    return ChildFrontierAction(node, tuple(map(float, point)), outgoing_sites)


def terminal_child_graph(source, state, runtime, minimum_distance):
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
        -score_pose_port_state(runtime["state_model"], descriptors[point]),
        -state.proposals.votes[point], point)))[:MAXIMUM_CHILDREN]
    if not ordered:
        # A terminal with no child is still represented by one explicit
        # dead-end node so the graph vocabulary cannot silently drop it.
        node = ChildFrontierNode(
            "∅", (), 0, 0, (), 0, (), 0, (), True)
        actions = (ChildFrontierAction(node, (0., 0., 0.), ()),)
    else:
        actions = tuple(_candidate_action(
            source, state, point, descriptors[point], runtime,
            minimum_distance) for point in ordered)
    return child_frontier_graph(
        actions, minimum_distance=minimum_distance,
        distance_scale=HIDDEN_UNIT, distance_bin_width=.25)


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
        raise AssertionError(f"group {group_index} inherited-state drift")
    inherited = inherited[0]
    minimum_distance = _minimum_distance(inherited.positions)
    second_source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited.positions,
        seed_species=inherited.species)
    states, counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    if (tuple(counts) != tuple(expected["second_block_counts"])
            or len(states) != len(expected["rows"])):
        raise AssertionError(f"group {group_index} source candidate drift")
    rows = []
    for stable_index, state in enumerate(states):
        label = expected["rows"][stable_index]
        colors = tuple(color for _point, color in state.actions)
        if (int(label["stable_index"]) != stable_index
                or tuple(label["action_colors"]) != colors):
            raise AssertionError(f"group {group_index} stable terminal drift")
        graph = terminal_child_graph(
            second_source, state, runtime, minimum_distance)
        rows.append({
            "group": group_index,
            "stable_index": stable_index,
            "action_colors": colors,
            "graph": asdict(graph),
            "exact": bool(label["exact"]),
            "correct_sites": int(label["correct_sites"]),
        })
    return {
        "group": group_index,
        "center": tuple(center),
        "minimum_distance": minimum_distance,
        "source_feature_digest": expected["feature_digest"],
        "source_inherited_action_digest": expected["inherited_action_digest"],
        "candidate_counts": tuple(counts),
        "rows": rows,
        "target_used_for_graphs": False,
    }


def _freeze(value):
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze(item))
                            for key, item in value.items()))
    return value


def graph_from_json(row):
    nodes = tuple(ChildFrontierNode(
        str(node["action_color"]), tuple(map(int, node["channel_code"])),
        int(node["vote_bin"]), int(node["probability_bin"]),
        tuple(_freeze(item) for item in node["incoming_roles"]),
        int(node["incoming_mass_bin"]),
        tuple(_freeze(item) for item in node["outgoing_roles"]),
        int(node["outgoing_mass_bin"]), tuple(map(str, node["outgoing_colors"])),
        bool(node["dead_end"])) for node in row["nodes"])
    edges = tuple(ChildFrontierEdge(
        int(edge["left_index"]), int(edge["right_index"]),
        int(edge["separation_bin"]), bool(edge["compatible"]),
        int(edge["shared_incoming_roles_bin"]),
        int(edge["shared_outgoing_sites_bin"]),
        int(edge["conflicting_outgoing_colors_bin"]),
        bool(edge["connection_witnessed"])) for edge in row["edges"])
    return ChildFrontierGraph(
        nodes, edges, int(row["compatible_edges"]), int(row["conflict_edges"]),
        int(row["maximum_compatible_actions"]), str(row["canonical_digest"]),
        bool(row["proper_se3_invariant"]),
        bool(row["lattice_coordinates_used"]), bool(row["target_used"]))


def build_dataset(*, workers=1):
    source_raw, source_payload = load_fixture_json(SOURCE_FIXTURE)
    if hashlib.sha256(source_raw).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise AssertionError("source terminal fixture byte drift")
    source = validate_source_dataset(source_payload)
    if source["dataset_digest"] != SOURCE_DATASET_DIGEST:
        raise AssertionError("source terminal dataset drift")
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS, "IQC-child-graph-seed")
                  for center in DEVELOPMENT_CENTERS)
    first_targets = tuple(_crop(
        oracle, center, TARGET_RADIUS,
        "IQC-child-graph-consumed-first-target")
        for center in DEVELOPMENT_CENTERS)
    payloads = []
    for index, (center, seed, first, expected) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, first_targets, source["groups"])):
        truth = {tuple(round(value, 6) for value in point): str(color)
                 for point, color in zip(first.positions, first.species)}
        payloads.append((index, center, tuple(seed.positions),
                         tuple(seed.species), truth, expected))
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
        "maximum_roles": MAXIMUM_ROLES,
        "groups": groups,
        "target_used_for_graphs": False,
        "labels_copied_from_consumed_development_fixture": True,
        "fresh_confirmation_claimed": False,
    }
    digest = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**body, "dataset_digest": digest}


def load_graph_fixture(path=DEFAULT_FIXTURE):
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
            or body["maximum_children"] != MAXIMUM_CHILDREN
            or body["maximum_roles"] != MAXIMUM_ROLES
            or body["target_used_for_graphs"]
            or not body["labels_copied_from_consumed_development_fixture"]
            or body["fresh_confirmation_claimed"]):
        raise AssertionError("post-self-fed child-graph dataset drift")
    rows = [row for group in body["groups"] for row in group["rows"]]
    graphs = tuple(graph_from_json(row["graph"]) for row in rows)
    if (len(rows) != 1278 or sum(row["exact"] for row in rows) != 142
            or any(graph.target_used or not graph.proper_se3_invariant
                   or graph.lattice_coordinates_used for graph in graphs)):
        raise AssertionError("invalid child-frontier graph corpus")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("post-self-fed child-graph dataset digest drift")
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
