#!/usr/bin/env python3
"""Replay wide IQC branches into the shared internal port-incidence schema.

The unchanged wide candidate universe previously serialized only each branch's
next successor port.  That is not the same object as the development corpus's
three witnessed internal placements.  This companion fixture replays every
already-frozen wide branch, records the incoming port of each of its three
actions, canonicalizes the result with ``materials_gcts_port_incidence_graph``,
and only then joins the existing immutable wide labels.

The first-block inherited branch is already consumed development evidence and
is used to reconstruct the second-block seed exactly as in the source fixture.
No second-block target atom or exact/false row label enters graph generation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import math
import os
import pickle
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_exact_port_instance_dataset import (
    _payloads as _source_payloads, load_default_dataset as load_label_dataset)
from materials_gcts_iqc_extended_development_preregistration import (
    TARGET_RADIUS as FIRST_BLOCK_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    ACTION_REACH_SCHEDULE, _bounded_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import SECOND_BLOCK_RADIUS
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES
from materials_gcts_iqc_simultaneous_port_cover_dataset import _minimum_distance
from materials_gcts_port_incidence_graph import (
    SCHEMA_VERSION as GRAPH_SCHEMA_VERSION, canonical_port_incidence_graph)
from materials_gcts_recursive_connections import local_cluster_types
from materials_gcts_pose_port_state_marking import score_pose_port_state


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_wide_port_incidence_dataset_v1.json.gz"
SCHEMA_VERSION = 1
EXPECTED_FIXTURE_SHA256 = \
    "6d6e8443a9ff6cb0edcf9eee37debd7d830ecacdbff05911f52367c78653f6a9"
EXPECTED_DATASET_DIGEST = \
    "fac9ca6bc60fef02aeab0faa898da73b64894f67a9e65bd01c7e4c2fb97a3c42"


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _state_code(state):
    return (state.parent_type.color_key,
            tuple(state.parent_type.cumulative_neighbor_counts),
            state.source_type.color_key,
            tuple(state.source_type.cumulative_neighbor_counts),
            int(state.normalized_separation_bin))


def _replay_internal_graph(source, runtime, actions, radius,
                           minimum_distance):
    frontier = _bounded_at_radius(
        runtime["connection"], source, local_cluster_types(
            source.seed_positions, source.seed_species, CLUSTER_EDGES), radius)
    state = FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ())
    records = []
    for expected_point, expected_color in actions:
        point = tuple(expected_point)
        if point not in state.proposals.votes:
            raise AssertionError("frozen branch action is absent on replay")
        color = str(_dominant_source_color(state.proposals, point))
        if color != str(expected_color):
            raise AssertionError("frozen branch color changed on replay")
        pair_actions = state.proposals.pair_actions
        if pair_actions is None or not pair_actions.get(point):
            raise AssertionError("replayed action has no exact pair witness")
        witnesses = []
        for action in pair_actions[point]:
            witnesses.append({
                "state": _state_code(action.state),
                "parent_position": tuple(state.positions[action.parent_index]),
                "parent_species": str(state.species[action.parent_index]),
                "source_position": tuple(state.positions[action.source_index]),
                "source_species": str(state.species[action.source_index]),
            })
        records.append({
            "point": point, "species": color,
            "port_witnesses": tuple(witnesses),
        })
        descriptors = _descriptors(
            state.positions, state.species, state.proposals,
            UPSTREAM_ANGULAR_BIN_WIDTH)
        state = _child(
            source, runtime["connection"], runtime["state_model"], state,
            point, descriptors[point], radius)
    if action_key(state.actions) != action_key(actions):
        raise AssertionError("replayed branch action set drifted")
    return canonical_port_incidence_graph(
        source.group, records, minimum_distance)


def _initial_state(source, runtime, radius):
    frontier = _bounded_at_radius(
        runtime["connection"], source, local_cluster_types(
            source.seed_positions, source.seed_species, CLUSTER_EDGES), radius)
    return FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ())


def _ordered_frontier(state, runtime, reach):
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    points = tuple(sorted(state.proposals.votes, key=lambda point: (
        -score_pose_port_state(runtime["state_model"], descriptors[point]),
        -state.proposals.votes[point], point)))[:reach]
    return points, descriptors


def _reconstruct_inherited(source, runtime, first_truth, expected_digest,
                           radius):
    states = (_initial_state(source, runtime, radius),)
    for reach in ACTION_REACH_SCHEDULE:
        children = {}
        for state in states:
            points, descriptors = _ordered_frontier(state, runtime, reach)
            for point in points:
                color = str(_dominant_source_color(state.proposals, point))
                if first_truth.get(tuple(round(value, 6)
                                         for value in point)) != color:
                    continue
                child = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], radius)
                key = action_key(child.actions)
                prior = children.get(key)
                if prior is None or (child.cumulative, child.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = child
        states = tuple(children.values())
        if not states:
            raise AssertionError("exact inherited branch disappeared")
    matches = tuple(state for state in states if hashlib.sha256(
        repr(action_key(state.actions)).encode()).hexdigest() == expected_digest)
    if len(matches) != 1:
        raise AssertionError("inherited branch did not replay uniquely")
    return matches[0]


def _graph_matrix(graph):
    matrix = [[0.] * 3 for _ in range(3)]
    cursor = 0
    for left in range(3):
        for right in range(left + 1, 3):
            value = float(graph["pair_distances_nn"][cursor])
            matrix[left][right] = matrix[right][left] = value
            cursor += 1
    return matrix


def _partial_graph_match(center, actions, minimum_distance, graph,
                         tolerance=2e-5):
    colors = tuple(graph["node_colors"])
    radial = tuple(map(float, graph["center_distances_nn"]))
    matrix = _graph_matrix(graph)
    for target_nodes in itertools.permutations(range(3), len(actions)):
        if any(str(action[1]) != str(colors[target]) or abs(
                math.dist(action[0], center) / minimum_distance -
                radial[target]) > tolerance
                for action, target in zip(actions, target_nodes)):
            continue
        valid = True
        for left in range(len(actions)):
            for right in range(left + 1, len(actions)):
                if abs(math.dist(actions[left][0], actions[right][0]) /
                       minimum_distance -
                       matrix[target_nodes[left]][target_nodes[right]]) > \
                        tolerance:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            return True
    return False


def _reconstruct_retained(source, runtime, retained_geometry, radius,
                          minimum_distance):
    states = (_initial_state(source, runtime, radius),)
    graphs = tuple(row["complete_branch_action_graph"]
                   for row in retained_geometry)
    for reach in ACTION_REACH_SCHEDULE:
        children = {}
        for state in states:
            points, descriptors = _ordered_frontier(state, runtime, reach)
            for point in points:
                color = str(_dominant_source_color(state.proposals, point))
                partial = state.actions + ((tuple(point), color),)
                if not any(_partial_graph_match(
                        source.group, partial, minimum_distance, graph)
                           for graph in graphs):
                    continue
                child = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], radius)
                key = action_key(child.actions)
                prior = children.get(key)
                if prior is None or (child.cumulative, child.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = child
        states = tuple(children.values())
        if not states:
            raise AssertionError("receipt-constrained replay lost all branches")
    by_digest = {hashlib.sha256(repr(action_key(state.actions)).encode()
                                ).hexdigest(): state for state in states}
    result = {}
    for row in retained_geometry:
        digest = str(row["source_action_digest"])
        if digest not in by_digest:
            raise AssertionError(
                f"retained branch {row['stable_index']} was not reconstructed")
        result[int(row["stable_index"])] = by_digest[digest]
    return result


def _geometry_payload(source_payload):
    (group_index, center, seed_positions, seed_species, first_truth, upstream,
     retained_stable_indices, candidate_universe_digest) = source_payload
    runtime = load_default_runtime()
    first_source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    inherited = _reconstruct_inherited(
        first_source, runtime, first_truth,
        upstream["inherited_action_digest"], upstream["first_radius"])
    source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited.positions,
        seed_species=inherited.species)
    minimum_distance = _minimum_distance(source.seed_positions)
    retained = _reconstruct_retained(
        source, runtime, upstream["retained_geometry"], SECOND_BLOCK_RADIUS,
        minimum_distance)
    rows = []
    for stable_index in retained_stable_indices:
        state = retained[int(stable_index)]
        graph = _replay_internal_graph(
            source, runtime, state.actions, SECOND_BLOCK_RADIUS,
            minimum_distance)
        rows.append({
            "stable_index": int(stable_index),
            "source_action_digest": hashlib.sha256(
                repr(action_key(state.actions)).encode()).hexdigest(),
            "port_incidence_graph": graph,
        })
    geometry_digest = _digest(rows)
    return {
        "group": int(group_index),
        "center": tuple(center),
        "candidate_universe_digest": str(candidate_universe_digest),
        "minimum_distance": minimum_distance,
        "frozen_graph_digest_before_label_join": geometry_digest,
        "rows": tuple(rows),
        "second_block_target_used_for_graphs": False,
        "exact_labels_used_for_graphs": False,
        "first_block_consumed_target_used_to_reconstruct_seed": True,
    }


def _sanitized_payloads():
    payloads, portfolio = _source_payloads()
    geometry_source = load_label_dataset()
    geometry_groups = {int(group["group"]): group
                       for group in geometry_source["groups"]}
    result = []
    for payload in payloads:
        (group_index, center, seed_positions, seed_species, first_truth,
         expected, retained_stable_indices, candidate_universe_digest) = payload
        # The child process receives no row labels or target sites.  Only the
        # already-frozen inherited branch and candidate-count receipt survive.
        upstream = {
            "first_radius": FIRST_BLOCK_RADIUS,
            "inherited_action_digest": expected["inherited_action_digest"],
            "second_block_counts": tuple(expected["second_block_counts"]),
            "retained_geometry": tuple({
                "stable_index": int(row["stable_index"]),
                "source_action_digest": str(row["source_action_digest"]),
                "complete_branch_action_graph":
                    row["complete_branch_action_graph"],
            } for row in geometry_groups[int(group_index)]["rows"]),
        }
        result.append((
            group_index, center, seed_positions, seed_species, first_truth,
            upstream, retained_stable_indices, candidate_universe_digest))
    return tuple(result), portfolio


def _parallel_groups(payloads, workers):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    with tempfile.TemporaryDirectory(prefix="gcts-wide-port-graph-") as tmp:
        directory = Path(tmp)
        active, launched = [], 0
        while launched < len(payloads) or active:
            while launched < len(payloads) and len(active) < workers:
                source = directory / f"input-{launched}.pickle"
                target = directory / f"output-{launched}.pickle"
                source.write_bytes(pickle.dumps(payloads[launched]))
                process = subprocess.Popen(
                    [sys.executable, "-B", str(Path(__file__).resolve()),
                     "--group-pickle", str(source), str(target)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, env=environment)
                active.append((launched, process, target))
                launched += 1
            index, process, target = active.pop(0)
            _output, error = process.communicate()
            if process.returncode:
                raise RuntimeError(
                    f"wide port graph group {index} failed: {error.strip()}")
        return tuple(pickle.loads(
            (directory / f"output-{index}.pickle").read_bytes())
            for index in range(len(payloads)))


def build_dataset(*, workers=1):
    payloads, portfolio = _sanitized_payloads()
    geometry_groups = (tuple(_geometry_payload(row) for row in payloads)
                       if workers == 1 else _parallel_groups(
                           payloads, min(len(payloads), max(1, workers))))
    # Existing immutable labels enter only after every graph digest freezes.
    labels = load_label_dataset()
    label_rows = {(int(group["group"]), int(row["stable_index"])): row
                  for group in labels["groups"] for row in group["rows"]}
    groups = []
    for group in geometry_groups:
        rows = []
        for row in group["rows"]:
            label = label_rows[(group["group"], row["stable_index"])]
            candidate_id = _digest({
                "group": group["group"],
                "stable_index": row["stable_index"],
                "graph": row["port_incidence_graph"],
            })
            rows.append({**row, "candidate_id": candidate_id,
                         "exact": bool(label["exact"]),
                         "correct_sites": int(label["correct_sites"])})
        groups.append({**group, "rows": tuple(rows),
                       "labels_joined_after_graph_freeze": True})
    body = {
        "schema_version": SCHEMA_VERSION,
        "graph_schema_version": GRAPH_SCHEMA_VERSION,
        "source_exact_port_dataset_digest": labels["dataset_digest"],
        "source_wide_portfolio_audit_digest": portfolio["audit_digest"],
        "groups": tuple(groups),
        "group_count": len(groups),
        "candidate_count": sum(len(group["rows"]) for group in groups),
        "all_graphs_use_common_schema": True,
        "raw_occurrence_ids_serialized": False,
        "global_frame_semantic": False,
        "second_block_targets_or_labels_used_for_graph_generation": False,
        "labels_joined_after_all_graphs_freeze": True,
        "candidate_geometry_changed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "dataset_digest": _digest(body)}


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("wide port-incidence fixture byte drift")
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (_digest(body) != digest or body["schema_version"] != SCHEMA_VERSION
            or body["graph_schema_version"] != GRAPH_SCHEMA_VERSION
            or body["group_count"] != 10 or body["candidate_count"] != 120
            or not body["all_graphs_use_common_schema"]
            or body["raw_occurrence_ids_serialized"]
            or body["global_frame_semantic"]
            or body["second_block_targets_or_labels_used_for_graph_generation"]
            or not body["labels_joined_after_all_graphs_freeze"]
            or body["candidate_geometry_changed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("wide port-incidence dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("wide port-incidence dataset digest drift")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--group-pickle", nargs=2,
                        metavar=("INPUT", "OUTPUT"))
    args = parser.parse_args()
    if args.group_pickle:
        source, target = map(Path, args.group_pickle)
        target.write_bytes(pickle.dumps(
            _geometry_payload(pickle.loads(source.read_bytes()))))
        return
    row = build_dataset(workers=max(1, args.workers))
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
