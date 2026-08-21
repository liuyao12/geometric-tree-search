#!/usr/bin/env python3
"""Freeze exact finite-port-instance continuation certificates for wide IQC.

The earlier simultaneous audit quotiented an ordered occurrence pair down to
its cluster colors and separation bin.  Here each selected proposal keeps its
one exact ``parent -> source`` witness.  Successor actions are tested against
seven fixed equality/incidence relations on those occurrences.  Raw indices
are used transiently only to evaluate equality; serialized candidate identity
is a proper-motion-invariant colored metric signature.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gzip
import hashlib
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
from materials_gcts_iqc_extended_development_preregistration import (
    TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import (
    _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import SECOND_BLOCK_RADIUS
from materials_gcts_iqc_simultaneous_port_cover_dataset import (
    MAXIMUM_SEARCH_NODES, _minimum_distance)
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _payloads
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_recursive_connections import ProposalPairAction
from materials_gcts_simultaneous_port_cover import (
    FrozenPortCoverProblem, PortCoverAction, solve_simultaneous_port_cover)


RELATIONS = (
    "reverse", "forward", "backward", "same_parent", "same_source",
    "touch_parent", "touch_source",
)
FRONTIER_NORMALIZATION = 1024.
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_exact_port_instance_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "6078563db697459e2d9c7aea2820fe1f6e6914c1954ca7f27e4e0a1279abfd4c"
EXPECTED_DATASET_DIGEST = \
    "16c0067d58082e60beaaee584a06dfe8c13358b565060729323b9056bb9544ce"


def _relation_flags(selected: ProposalPairAction,
                    other: ProposalPairAction):
    parent, source = selected.parent_index, selected.source_index
    other_parent, other_source = other.parent_index, other.source_index
    return {
        "reverse": (other_parent == source and other_source == parent),
        "forward": other_parent == source,
        "backward": other_source == parent,
        "same_parent": other_parent == parent,
        "same_source": other_source == source,
        "touch_parent": parent in (other_parent, other_source),
        "touch_source": source in (other_parent, other_source),
    }


def _state_code(state):
    return (state.parent_type.color_key,
            tuple(state.parent_type.cumulative_neighbor_counts),
            state.source_type.color_key,
            tuple(state.source_type.cumulative_neighbor_counts),
            int(state.normalized_separation_bin))


def _distance_signature(selected, other, selected_target, candidate_target,
                        positions, minimum_distance):
    anchors = (
        positions[selected.parent_index], positions[selected.source_index],
        selected_target, positions[other.parent_index],
        positions[other.source_index], candidate_target)
    distances = tuple(round(math.dist(anchors[left], anchors[right]) /
                            minimum_distance, 6)
                      for left in range(len(anchors))
                      for right in range(left + 1, len(anchors)))
    return _state_code(other.state), distances


def _boundary_context(center, target, parent, source, radius,
                      minimum_distance, frontier_actions):
    radial = tuple(target[axis] - center[axis] for axis in range(3))
    port = tuple(source[axis] - parent[axis] for axis in range(3))
    radial_norm = math.sqrt(sum(value * value for value in radial))
    port_norm = math.sqrt(sum(value * value for value in port))
    outward_cosine = (sum(left * right for left, right in zip(radial, port)) /
                       (radial_norm * port_norm)
                       if radial_norm > 1e-12 and port_norm > 1e-12 else 0.)
    return {
        "target_margin_nn": round(
            (radius - math.dist(target, center)) / minimum_distance, 6),
        "parent_margin_nn": round(
            (radius - math.dist(parent, center)) / minimum_distance, 6),
        "source_margin_nn": round(
            (radius - math.dist(source, center)) / minimum_distance, 6),
        "ordered_port_length_nn": round(port_norm / minimum_distance, 6),
        "outward_cosine": round(outward_cosine, 6),
        "current_frontier_fraction": round(
            frontier_actions / FRONTIER_NORMALIZATION, 6),
    }


def _successor_relations(source, state, runtime, minimum_distance):
    if state.proposals.pair_actions is None:
        raise AssertionError("exact proposal pair provenance is unavailable")
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    point = min(state.proposals.votes, key=lambda candidate: (
        -score_pose_port_state(
            runtime["state_model"], descriptors[candidate]),
        -state.proposals.votes[candidate], candidate))
    selected_rows = tuple(state.proposals.pair_actions.get(point, ()))
    if len(selected_rows) != 1:
        raise AssertionError("wide selected action must have one pair witness")
    selected = selected_rows[0]
    parent = state.positions[selected.parent_index]
    selected_source = state.positions[selected.source_index]
    boundary_context = _boundary_context(
        source.group, point, parent, selected_source, SECOND_BLOCK_RADIUS,
        minimum_distance, len(state.proposals.votes))
    successor = _child(
        source, runtime["connection"], runtime["state_model"], state,
        point, descriptors[point], SECOND_BLOCK_RADIUS)
    if successor.proposals.pair_actions is None:
        raise AssertionError("successor pair provenance is unavailable")

    classes = {relation: set() for relation in RELATIONS}
    raw_counts = {relation: 0 for relation in RELATIONS}
    for candidate in sorted(successor.proposals.votes):
        color = str(_dominant_source_color(successor.proposals, candidate))
        for other in successor.proposals.pair_actions.get(candidate, ()):
            flags = _relation_flags(selected, other)
            signature = (color, _distance_signature(
                selected, other, point, candidate, successor.positions,
                minimum_distance))
            for relation in RELATIONS:
                if flags[relation]:
                    raw_counts[relation] += 1
                    classes[relation].add(signature)
    certificates = {}
    for relation in RELATIONS:
        actions = tuple(PortCoverAction(
            signature, (relation,), marking_score=0.)
            for signature in sorted(classes[relation], key=repr))
        certificates[relation] = asdict(solve_simultaneous_port_cover(
            FrozenPortCoverProblem((relation,), actions, True),
            maximum_actions=1, maximum_search_nodes=MAXIMUM_SEARCH_NODES))
    return {
        "selected_state": _state_code(selected.state),
        "selected_pair_witnesses": len(selected_rows),
        "complete_successor_frontier_actions": len(successor.proposals.votes),
        "boundary_context": boundary_context,
        "raw_matching_pair_actions": raw_counts,
        "invariant_candidate_classes": {
            relation: len(classes[relation]) for relation in RELATIONS},
        "certificates": certificates,
    }


def _evaluate_group(payload):
    (group_index, center, seed_positions, seed_species, first_truth, expected,
     retained_stable_indices, candidate_universe_digest) = payload
    runtime = load_default_runtime()
    first_source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    first_states, _counts = _complete_states_at_radius(
        first_source, runtime, TARGET_RADIUS)
    inherited = tuple(state for state in first_states if all(
        first_truth.get(tuple(round(value, 6) for value in point)) == color
        for point, color in state.actions) and hashlib.sha256(
            repr(action_key(state.actions)).encode()).hexdigest()
        == expected["inherited_action_digest"])
    if len(inherited) != 1:
        raise AssertionError(f"group {group_index} inherited-state drift")
    source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited[0].positions,
        seed_species=inherited[0].species)
    states, counts = _complete_states_at_radius(
        source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    if (tuple(counts) != tuple(expected["second_block_counts"])
            or len(states) != len(expected["rows"])):
        raise AssertionError(f"group {group_index} source candidate drift")
    minimum_distance = _minimum_distance(source.seed_positions)
    geometry_rows = []
    for stable_index in retained_stable_indices:
        state = states[int(stable_index)]
        geometry_rows.append({
            "stable_index": int(stable_index),
            "source_action_digest": hashlib.sha256(
                repr(action_key(state.actions)).encode()).hexdigest(),
            **_successor_relations(source, state, runtime, minimum_distance),
        })
    geometry_digest = hashlib.sha256(json.dumps(
        geometry_rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    rows = []
    for geometry in geometry_rows:
        label = expected["rows"][geometry["stable_index"]]
        rows.append({**geometry, "exact": bool(label["exact"]),
                     "correct_sites": int(label["correct_sites"])})
    return {
        "group": int(group_index), "center": tuple(center),
        "candidate_universe_digest": str(candidate_universe_digest),
        "minimum_distance": minimum_distance,
        "frozen_geometry_digest_before_label_join": geometry_digest,
        "rows": rows, "successor_enumeration_complete": True,
        "raw_occurrence_indices_serialized": False,
        "proper_motion_invariant_candidate_identity": True,
        "public_boundary_context_serialized": True,
        "target_used_for_candidates_or_certificates": False,
        "labels_joined_after_group_geometry_freeze": True,
    }


def _parallel_groups(payloads, workers):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    with tempfile.TemporaryDirectory(prefix="gcts-exact-port-") as tmp:
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
                    f"exact port-instance group {index} failed: "
                    f"{error.strip()}")
        return tuple(pickle.loads(
            (directory / f"output-{index}.pickle").read_bytes())
            for index in range(len(payloads)))


def build_dataset(*, workers=1):
    payloads, portfolio = _payloads()
    groups = (tuple(_evaluate_group(payload) for payload in payloads)
              if workers == 1 else _parallel_groups(
                  payloads, min(len(payloads), max(1, workers))))
    body = {
        "schema_version": 1,
        "source_wide_portfolio_audit_digest": portfolio["audit_digest"],
        "development_groups": len(groups),
        "retained_candidates": sum(len(group["rows"]) for group in groups),
        "relation_families": RELATIONS,
        "groups": groups,
        "complete_successor_frontier_enumerated": True,
        "ordered_pair_provenance_preserved": True,
        "raw_occurrence_indices_serialized": False,
        "proper_motion_invariant_candidate_identity": True,
        "public_boundary_context_serialized": True,
        "candidate_geometry_unchanged": True,
        "target_used_for_candidates_or_certificates": False,
        "labels_joined_after_geometry_freeze": True,
        "targets_consumed_development_only": True,
        "mandatory_physical_port_occupancy_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "dataset_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("exact port-instance fixture byte drift")
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != digest or body["schema_version"] != 1
            or body["retained_candidates"] != 120
            or tuple(body["relation_families"]) != RELATIONS
            or not body["complete_successor_frontier_enumerated"]
            or not body["ordered_pair_provenance_preserved"]
            or body["raw_occurrence_indices_serialized"]
            or not body["proper_motion_invariant_candidate_identity"]
            or not body["public_boundary_context_serialized"]
            or body["target_used_for_candidates_or_certificates"]
            or not body["labels_joined_after_geometry_freeze"]
            or body["mandatory_physical_port_occupancy_claimed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("exact port-instance dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("exact port-instance dataset digest drift")
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
            _evaluate_group(pickle.loads(source.read_bytes()))))
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
