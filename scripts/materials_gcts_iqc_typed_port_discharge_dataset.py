#!/usr/bin/env python3
"""Freeze identity-preserving target-free IQC port-discharge rollouts.

The earlier discharge corpus retained only scalar frontier mass.  This corpus
replays the identical retained exact-geometry states and the identical greedy
16-action continuation, but also records which finite semantic GCTS port roles
persist, disappear, and appear at each transition.  Roles contain only colored
local cluster types and a normalized separation bin; atom IDs, candidate IDs,
absolute coordinates, lattice axes, and target atoms are absent.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import pickle
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
    DEFAULT_FIXTURE as SCALAR_FIXTURE,
    EXPECTED_DATASET_DIGEST as SCALAR_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as SCALAR_FIXTURE_SHA256,
    ROLLOUT_HORIZON, load_fixture_json,
    validate_dataset as validate_scalar_dataset)
from materials_gcts_port_incidence_search import semantic_port_role


MAXIMUM_TRANSITION_ROLES = 16
MAXIMUM_SELECTED_ROLES = 4
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_typed_port_discharge_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "a7e094b01d40e6165e258ac5553ed8db8918edc143564464ebe9df7c3b324800"
EXPECTED_DATASET_DIGEST = \
    "e15abead974143b705a18583d3c2a051ef2dc5180d27e12c227105dcbb6e4729"


def _role_key(role):
    return (
        role.parent_color, tuple(role.parent_neighbors),
        role.source_color, tuple(role.source_neighbors),
        int(role.separation_bin),
    )


def _role_counts(frontier):
    counts = Counter()
    for point in frontier.votes:
        for state, count in frontier.state_votes.get(point, {}).items():
            counts[_role_key(semantic_port_role(state))] += int(count)
    return counts


def _selected_role_counts(frontier, point):
    rows = Counter()
    for state, count in frontier.state_votes.get(point, {}).items():
        rows[_role_key(semantic_port_role(state))] += int(count)
    return tuple((role, count) for role, count in sorted(
        rows.items(), key=lambda row: (-row[1], row[0]))[
            :MAXIMUM_SELECTED_ROLES])


def typed_transition(before_frontier, selected_point, after_frontier):
    """Return one bounded, ID-free typed-obligation transition."""
    before = _role_counts(before_frontier)
    after = _role_counts(after_frontier)
    roles = sorted(set(before) | set(after), key=lambda role: (
        -max(before[role], after[role]), role))
    explicit = roles[:MAXIMUM_TRANSITION_ROLES]
    overflow = roles[MAXIMUM_TRANSITION_ROLES:]
    rows = []
    for role in explicit:
        left, right = before[role], after[role]
        rows.append({
            "role": role,
            "before": left,
            "after": right,
            "discharged": max(0, left - right),
            "persisted": min(left, right),
            "produced": max(0, right - left),
        })
    selected = _selected_role_counts(before_frontier, selected_point)
    selected_rows = []
    for role, selected_count in selected:
        left, right = before[role], after[role]
        selected_rows.append({
            "role": role,
            "selected_votes": selected_count,
            "before": left,
            "after": right,
            "discharged": max(0, left - right),
            "persisted": min(left, right),
            "produced": max(0, right - left),
        })
    return {
        # This causal cohort is exact and never truncated: the upstream
        # proposal descriptor itself is bounded to MAXIMUM_SELECTED_ROLES.
        "selected_role_transitions": selected_rows,
        "roles": rows,
        "explicit_role_count": len(explicit),
        "overflow_role_count": len(overflow),
        "overflow_before_mass": sum(before[role] for role in overflow),
        "overflow_after_mass": sum(after[role] for role in overflow),
        "discharged_mass": sum(max(0, before[role] - after[role])
                               for role in roles),
        "persisted_mass": sum(min(before[role], after[role])
                              for role in roles),
        "produced_mass": sum(max(0, after[role] - before[role])
                             for role in roles),
    }


def _augment_group(payload):
    """Replay one source group and attach typed transitions.

    The scalar evaluator remains the authority for reconstruction and labels.
    A local import avoids changing the already frozen scalar fixture API.
    """
    from materials_gcts_iqc_frozen_fusion_runtime import (
        _child, load_default_runtime)
    from materials_gcts_iqc_pose_port_state_audit import _descriptors
    from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
        UPSTREAM_ANGULAR_BIN_WIDTH)
    from materials_gcts_iqc_self_fed_complete_frontier_execution import (
        _complete_states_at_radius)
    from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
        ROLLOUT_RADIUS)
    from materials_gcts_pose_port_state_marking import score_pose_port_state
    from types import SimpleNamespace

    (group_index, center, seed_positions, seed_species, first_truth, expected,
     retained_stable_indices, _candidate_digest, scalar_group) = payload
    runtime = load_default_runtime()
    first_source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    first_states, _ = _complete_states_at_radius(
        first_source, runtime, __import__(
            "materials_gcts_iqc_extended_development_preregistration",
            fromlist=["TARGET_RADIUS"]).TARGET_RADIUS)
    inherited = tuple(state for state in first_states if all(
        first_truth.get(tuple(round(value, 6) for value in point)) == color
        for point, color in state.actions))
    expected_digest = expected["inherited_action_digest"]
    from materials_gcts_iqc_frozen_fusion_runtime import action_key
    inherited = tuple(state for state in inherited if hashlib.sha256(
        repr(action_key(state.actions)).encode()).hexdigest() == expected_digest)
    if len(inherited) != 1:
        raise AssertionError(f"group {group_index} inherited-state drift")
    source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited[0].positions,
        seed_species=inherited[0].species)
    states, _ = _complete_states_at_radius(source, runtime, __import__(
        "materials_gcts_iqc_self_fed_terminal_dataset",
        fromlist=["SECOND_BLOCK_RADIUS"]).SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))

    typed_by_index = {}
    for stable_index in retained_stable_indices:
        state = states[int(stable_index)]
        transitions = []
        for _depth in range(ROLLOUT_HORIZON):
            if not state.proposals.votes:
                break
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            point = min(state.proposals.votes, key=lambda candidate: (
                -score_pose_port_state(
                    runtime["state_model"], descriptors[candidate]),
                -state.proposals.votes[candidate], candidate))
            before = state.proposals
            state = _child(source, runtime["connection"],
                           runtime["state_model"], state, point,
                           descriptors[point], ROLLOUT_RADIUS)
            transitions.append(typed_transition(before, point,
                                                state.proposals))
        # Preserve whether a selected semantic obligation is selected again
        # later in the same target-free trajectory.  This is identity history,
        # not a coordinate-bearing action identifier.
        for index, transition in enumerate(transitions):
            future = {}
            for later_index in range(index + 1, len(transitions)):
                for item in transitions[later_index][
                        "selected_role_transitions"]:
                    future.setdefault(tuple(item["role"]), later_index - index)
            for item in transition["selected_role_transitions"]:
                wait = future.get(tuple(item["role"]))
                item["selected_again_within_horizon"] = wait is not None
                item["steps_until_selected_again"] = wait or 0
        typed_by_index[int(stable_index)] = transitions

    rows = []
    for row in scalar_group["rows"]:
        transitions = typed_by_index[int(row["stable_index"])]
        if len(transitions) != len(row["trace"]["steps"]):
            raise AssertionError("typed/scalar rollout length drift")
        rows.append({**row, "typed_transitions": transitions})
    body = {**scalar_group, "rows": rows}
    body["frozen_typed_geometry_digest_before_label_join"] = hashlib.sha256(
        json.dumps([{k: v for k, v in row.items()
                     if k not in ("exact", "correct_sites")}
                    for row in rows], sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()
    return body


def _source_payloads():
    """Reconstruct the scalar builder payloads without opening a new target."""
    # Reuse the frozen scalar artifact as the exact source of group metadata;
    # rebuilding it supplies only already-consumed seed/first-block geometry.
    # This function is deliberately imported lazily because it is expensive.
    from materials_gcts_iqc_extended_development_preregistration import (
        DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
    from materials_gcts_iqc_post_self_fed_marking_portfolio import (
        load_default_result as load_portfolio_result)
    from materials_gcts_iqc_self_fed_terminal_dataset import (
        OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS)
    from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
    from materials_gcts_icosahedral_modelset import oracle_patch_fast
    import math

    raw, scalar_payload = load_fixture_json(SCALAR_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != SCALAR_FIXTURE_SHA256:
        raise AssertionError("scalar fixture byte drift")
    scalar = validate_scalar_dataset(scalar_payload)
    portfolio = load_portfolio_result()
    folds = {int(row["heldout_group"]): row for row in portfolio["folds"]}
    # Terminal labels/actions come from the already-consumed terminal source
    # embedded in the scalar builder's upstream fixture.
    from materials_gcts_iqc_self_fed_terminal_dataset import (
        DEFAULT_FIXTURE as terminal_path, load_fixture_json as load_terminal,
        validate_dataset as validate_terminal)
    _terminal_raw, terminal_payload = load_terminal(terminal_path)
    terminal = validate_terminal(terminal_payload)
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS, "typed-discharge-seed")
                  for center in DEVELOPMENT_CENTERS)
    first = tuple(_crop(oracle, center, TARGET_RADIUS,
                        "typed-discharge-consumed-first")
                  for center in DEVELOPMENT_CENTERS)
    payloads = []
    for index, (center, seed, target, expected) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, first, terminal["groups"])):
        truth = {tuple(round(value, 6) for value in point): str(color)
                 for point, color in zip(target.positions, target.species)}
        fold = folds[index]
        payloads.append((
            index, center, tuple(seed.positions), tuple(seed.species), truth,
            expected, tuple(fold["retained_stable_indices"]),
            fold["candidate_universe_digest"], scalar["groups"][index]))
    if scalar["development_groups"] != len(payloads):
        raise AssertionError("scalar group count drift")
    return tuple(payloads)


def build_dataset(*, workers=1):
    payloads = _source_payloads()
    if workers == 1:
        groups = tuple(_augment_group(payload) for payload in payloads)
    else:
        # ProcessPoolExecutor probes POSIX semaphore limits, which is denied in
        # the managed macOS sandbox.  Plain child processes need no semaphore.
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
            "PYTHONPATH", "")
        with tempfile.TemporaryDirectory(prefix="gcts-typed-discharge-") as tmp:
            directory = Path(tmp)
            pending = []
            for index, payload in enumerate(payloads):
                input_path = directory / f"input-{index}.pickle"
                output_path = directory / f"output-{index}.pickle"
                input_path.write_bytes(pickle.dumps(payload))
                process = subprocess.Popen(
                    [sys.executable, "-B", str(Path(__file__).resolve()),
                     "--group-pickle", str(input_path), str(output_path)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env=environment, text=True)
                pending.append((index, process, output_path))
                if len(pending) >= workers:
                    first = pending.pop(0)
                    output, error = first[1].communicate()
                    if first[1].returncode:
                        raise RuntimeError(
                            f"typed group {first[0]} failed: {error.strip()}")
            for index, process, _path in pending:
                output, error = process.communicate()
                if process.returncode:
                    raise RuntimeError(
                        f"typed group {index} failed: {error.strip()}")
            groups = tuple(pickle.loads(
                (directory / f"output-{index}.pickle").read_bytes())
                for index in range(len(payloads)))
    body = {
        "schema_version": 1,
        "source_scalar_dataset_digest": SCALAR_DATASET_DIGEST,
        "development_groups": len(groups),
        "retained_candidates": sum(len(group["rows"]) for group in groups),
        "rollout_horizon": ROLLOUT_HORIZON,
        "maximum_transition_roles": MAXIMUM_TRANSITION_ROLES,
        "maximum_selected_roles": MAXIMUM_SELECTED_ROLES,
        "groups": groups,
        "semantic_roles_are_id_free": True,
        "proper_rotation_quotiented_upstream": True,
        "candidate_geometry_unchanged": True,
        "target_used_for_rollouts": False,
        "rollout_target_crop_constructed": False,
        "labels_joined_after_geometry_freeze": True,
        "fresh_confirmation_claimed": False,
    }
    return {**body, "dataset_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("typed fixture byte drift")
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != digest or body["source_scalar_dataset_digest"] !=
            SCALAR_DATASET_DIGEST or body["retained_candidates"] != 19
            or body["target_used_for_rollouts"]
            or body["rollout_target_crop_constructed"]
            or not body["labels_joined_after_geometry_freeze"]):
        raise AssertionError("typed discharge dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("typed discharge digest drift")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--group-pickle", nargs=2, metavar=("INPUT", "OUTPUT"))
    args = parser.parse_args()
    if args.group_pickle:
        source, destination = map(Path, args.group_pickle)
        destination.write_bytes(pickle.dumps(
            _augment_group(pickle.loads(source.read_bytes()))))
        return
    row = build_dataset(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
