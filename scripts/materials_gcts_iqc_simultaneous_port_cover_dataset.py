#!/usr/bin/env python3
"""Freeze exhaustive one-frontier IQC semantic port-cover certificates.

For every state in the already frozen width-16 rollback portfolio, this
builder executes the unchanged first rollout action without target access.  A
persisting selected semantic port identity becomes a carried duty.  Every
collision-free action in the complete successor frontier that can consume at
least one such identity is retained; pair conflicts are computed from exact
Cartesian separation.  The simultaneous-cover solver then returns SAT, UNSAT,
or UNKNOWN.  Labels from the consumed development fixture are joined only
after all candidate sets and certificates in a group are frozen.

The identities are connection-section roles, not physical valence rules.
Consequently this is a bounded GCTS consistency certificate, not a claim that
every observed port must be occupied in a material.
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
from materials_gcts_iqc_typed_port_discharge_dataset import (
    _selected_role_counts, typed_transition)
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _payloads
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_simultaneous_port_cover import (
    FrozenPortCoverProblem, PortCoverAction, solve_simultaneous_port_cover)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_simultaneous_port_cover_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "22fa9491319ce117129beade99a282f74780ad10d371c8a83c57bc4f998ae2dd"
EXPECTED_DATASET_DIGEST = \
    "d19463a11a0f7db1512c59b18ef155ff3db144c8639901e0746b999473c41681"
MAXIMUM_SEARCH_NODES = 1_000_000


def _freeze(value):
    return tuple(_freeze(item) for item in value) \
        if isinstance(value, (list, tuple)) else value


def _minimum_distance(points):
    minimum = math.inf
    rows = tuple(points)
    for left, first in enumerate(rows):
        for second in rows[left + 1:]:
            distance = math.dist(first, second)
            if 1e-8 < distance < minimum:
                minimum = distance
    if not math.isfinite(minimum):
        raise ValueError("cannot infer a finite minimum distance")
    return minimum


def _successor_certificate(source, state, runtime, minimum_distance):
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    point = min(state.proposals.votes, key=lambda candidate: (
        -score_pose_port_state(
            runtime["state_model"], descriptors[candidate]),
        -state.proposals.votes[candidate], candidate))
    before = state.proposals
    successor = _child(
        source, runtime["connection"], runtime["state_model"], state,
        point, descriptors[point], SECOND_BLOCK_RADIUS)
    transition = typed_transition(before, point, successor.proposals)
    obligations = tuple(sorted({
        _freeze(row["role"])
        for row in transition["selected_role_transitions"]
        if int(row["persisted"]) > 0
    }, key=repr))
    if not obligations:
        problem = FrozenPortCoverProblem((), (), True)
        certificate = solve_simultaneous_port_cover(
            problem, maximum_actions=0,
            maximum_search_nodes=MAXIMUM_SEARCH_NODES)
        return certificate, 0, 0, len(successor.proposals.votes), transition

    successor_descriptors = _descriptors(
        successor.positions, successor.species, successor.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    rows = []
    obligation_set = set(obligations)
    for candidate in sorted(successor.proposals.votes):
        roles = tuple(sorted({
            _freeze(role) for role, _count in
            _selected_role_counts(successor.proposals, candidate)
            if _freeze(role) in obligation_set
        }, key=repr))
        if roles:
            rows.append((candidate, roles, score_pose_port_state(
                runtime["state_model"], successor_descriptors[candidate])))
    conflict_sets = [set() for _row in rows]
    conflicts = 0
    for left, (first, _roles, _score) in enumerate(rows):
        for right in range(left + 1, len(rows)):
            if math.dist(first, rows[right][0]) < minimum_distance - 1e-8:
                conflict_sets[left].add(right)
                conflict_sets[right].add(left)
                conflicts += 1
    actions = tuple(PortCoverAction(
        index, roles, frozenset(conflict_sets[index]), float(score))
        for index, (_point, roles, score) in enumerate(rows))
    certificate = solve_simultaneous_port_cover(
        FrozenPortCoverProblem(obligations, actions, True),
        maximum_actions=len(obligations),
        maximum_search_nodes=MAXIMUM_SEARCH_NODES)
    return (certificate, len(rows), conflicts,
            len(successor.proposals.votes), transition)


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
        certificate, candidate_count, conflict_count, frontier_count, \
            transition = _successor_certificate(
                source, state, runtime, minimum_distance)
        geometry_rows.append({
            "stable_index": int(stable_index),
            "source_action_digest": hashlib.sha256(
                repr(action_key(state.actions)).encode()).hexdigest(),
            "persisting_selected_role_identities": len(
                certificate.covered_obligations) +
                len(certificate.uncovered_obligations),
            "complete_successor_frontier_actions": int(frontier_count),
            "role_relevant_successor_actions": int(candidate_count),
            "pair_conflicts": int(conflict_count),
            "certificate": asdict(certificate),
            "first_transition_digest": hashlib.sha256(json.dumps(
                transition, sort_keys=True,
                separators=(",", ":")).encode()).hexdigest(),
        })
    geometry_digest = hashlib.sha256(json.dumps(
        geometry_rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    rows = []
    for geometry in geometry_rows:
        label = expected["rows"][geometry["stable_index"]]
        rows.append({
            **geometry,
            "exact": bool(label["exact"]),
            "correct_sites": int(label["correct_sites"]),
        })
    return {
        "group": int(group_index),
        "center": tuple(center),
        "candidate_universe_digest": str(candidate_universe_digest),
        "minimum_distance": minimum_distance,
        "frozen_geometry_digest_before_label_join": geometry_digest,
        "rows": rows,
        "successor_enumeration_complete": True,
        "target_used_for_candidates_or_certificates": False,
        "labels_joined_after_group_geometry_freeze": True,
    }


def _parallel_groups(payloads, workers):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    with tempfile.TemporaryDirectory(prefix="gcts-simultaneous-port-") as tmp:
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
                    f"simultaneous port group {index} failed: {error.strip()}")
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
        "maximum_search_nodes": MAXIMUM_SEARCH_NODES,
        "groups": groups,
        "semantic_role_identity_not_vote_multiplicity": True,
        "complete_successor_frontier_enumerated": True,
        "exact_pair_collision_constraints": True,
        "candidate_geometry_unchanged": True,
        "target_used_for_candidates_or_certificates": False,
        "labels_joined_after_geometry_freeze": True,
        "targets_consumed_development_only": True,
        "physical_valence_or_mandatory_occupancy_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "dataset_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("simultaneous port-cover fixture byte drift")
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != digest or body["schema_version"] != 1
            or body["retained_candidates"] != 120
            or not body["complete_successor_frontier_enumerated"]
            or body["target_used_for_candidates_or_certificates"]
            or not body["labels_joined_after_geometry_freeze"]
            or body["physical_valence_or_mandatory_occupancy_claimed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("simultaneous port-cover dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("simultaneous port-cover dataset digest drift")
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
