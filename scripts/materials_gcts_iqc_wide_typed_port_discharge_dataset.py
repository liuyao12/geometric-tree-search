#!/usr/bin/env python3
"""Freeze typed port-discharge rollouts for the wide IQC portfolio.

The portfolio is fixed before this builder runs: eight candidates from each of
two target-free marking orders, deduplicated to at most sixteen states per
nucleus.  Every retained state is replayed for the same 16 child placements.
Labels from the already-consumed development fixture are joined only after all
geometry and semantic obligation histories in one nucleus are frozen.
"""

from __future__ import annotations

import argparse
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
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_frontier_attachment_benchmark import _dominant_source_color
from materials_gcts_iqc_frozen_fusion_runtime import (
    _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
    ROLLOUT_HORIZON, ROLLOUT_RADIUS, TRACE_STEP_FIELDS, _frontier_summary)
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as TERMINAL_FIXTURE,
    EXPECTED_DATASET_DIGEST as TERMINAL_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as TERMINAL_FIXTURE_SHA256,
    OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS,
    load_fixture_json as load_terminal_fixture,
    validate_dataset as validate_terminal_dataset)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_iqc_typed_port_discharge_dataset import (
    MAXIMUM_SELECTED_ROLES, MAXIMUM_TRANSITION_ROLES, typed_transition)
from materials_gcts_iqc_wide_rollback_portfolio import (
    EXPECTED_AUDIT_DIGEST as WIDE_PORTFOLIO_DIGEST,
    load_default_result as load_wide_portfolio)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_wide_typed_port_discharge_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "f548d50fe95ca42a95764146dc9bdd02df4ff4687ca09c2ef5693a0948233417"
EXPECTED_DATASET_DIGEST = \
    "1f0d54243d79f56cbe7bef2c0a578d0f79dc5373be56a8bcac9c501f01c1facb"


def _annotate_reappearance(transitions):
    for index, transition in enumerate(transitions):
        future = {}
        for later_index in range(index + 1, len(transitions)):
            for item in transitions[later_index]["selected_role_transitions"]:
                future.setdefault(tuple(item["role"]), later_index - index)
        for item in transition["selected_role_transitions"]:
            wait = future.get(tuple(item["role"]))
            item["selected_again_within_horizon"] = wait is not None
            item["steps_until_selected_again"] = wait or 0


def _rollout(source, state, runtime):
    steps, transitions = [], []
    for _depth in range(ROLLOUT_HORIZON):
        before_summary = _frontier_summary(state.proposals)
        if before_summary[0] == 0:
            break
        descriptors = _descriptors(
            state.positions, state.species, state.proposals,
            UPSTREAM_ANGULAR_BIN_WIDTH)
        point = min(state.proposals.votes, key=lambda candidate: (
            -score_pose_port_state(
                runtime["state_model"], descriptors[candidate]),
            -state.proposals.votes[candidate], candidate))
        probability = score_pose_port_state(
            runtime["state_model"], descriptors[point])
        votes = int(state.proposals.votes[point])
        color = str(_dominant_source_color(state.proposals, point))
        before = state.proposals
        state = _child(
            source, runtime["connection"], runtime["state_model"], state,
            point, descriptors[point], ROLLOUT_RADIUS)
        after_summary = _frontier_summary(state.proposals)
        steps.append({
            "frontier_count_before": before_summary[0],
            "frontier_vote_mass_before": before_summary[1],
            "frontier_max_vote_before": before_summary[2],
            "selected_probability": probability,
            "selected_votes": votes,
            "selected_color": color,
            "frontier_count_after": after_summary[0],
            "frontier_vote_mass_after": after_summary[1],
            "frontier_max_vote_after": after_summary[2],
        })
        transitions.append(typed_transition(before, point, state.proposals))
    _annotate_reappearance(transitions)
    final = _frontier_summary(state.proposals)
    return ({
        "steps": steps,
        "accepted_children": len(steps),
        "fixed_point_reached": len(steps) < ROLLOUT_HORIZON,
        "final_frontier_count": final[0],
        "final_frontier_vote_mass": final[1],
        "final_frontier_max_vote": final[2],
        "cumulative_selected_votes": sum(
            step["selected_votes"] for step in steps),
        "cumulative_log_probability": sum(math.log(max(
            float(step["selected_probability"]), 1e-15)) for step in steps),
        "target_used": False,
    }, transitions)


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

    geometry_rows = []
    for stable_index in retained_stable_indices:
        state = states[int(stable_index)]
        expected_row = expected["rows"][int(stable_index)]
        if (int(expected_row["stable_index"]) != int(stable_index)
                or tuple(expected_row["action_colors"]) != tuple(
                    color for _point, color in state.actions)):
            raise AssertionError(f"group {group_index} terminal drift")
        trace, transitions = _rollout(source, state, runtime)
        geometry_rows.append({
            "stable_index": int(stable_index),
            "source_action_digest": hashlib.sha256(
                repr(action_key(state.actions)).encode()).hexdigest(),
            "trace": trace,
            "typed_transitions": transitions,
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
        "group": group_index,
        "center": tuple(center),
        "retained_stable_indices": tuple(map(int, retained_stable_indices)),
        "candidate_universe_digest": str(candidate_universe_digest),
        "source_inherited_action_digest": expected["inherited_action_digest"],
        "source_candidate_counts": tuple(counts),
        "frozen_geometry_digest_before_label_join": geometry_digest,
        "rows": rows,
        "target_used_for_rollouts": False,
        "labels_joined_after_all_group_traces_frozen": True,
    }


def _payloads():
    terminal_raw, terminal_payload = load_terminal_fixture(TERMINAL_FIXTURE)
    if hashlib.sha256(terminal_raw).hexdigest() != TERMINAL_FIXTURE_SHA256:
        raise AssertionError("terminal fixture byte drift")
    terminal = validate_terminal_dataset(terminal_payload)
    if terminal["dataset_digest"] != TERMINAL_DATASET_DIGEST:
        raise AssertionError("terminal dataset drift")
    portfolio = load_wide_portfolio()
    if portfolio["audit_digest"] != WIDE_PORTFOLIO_DIGEST:
        raise AssertionError("wide portfolio drift")
    folds = {int(row["heldout_group"]): row
             for row in portfolio["selected_folds"]}
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "wide-typed-discharge-seed")
                  for center in DEVELOPMENT_CENTERS)
    first_targets = tuple(_crop(
        oracle, center, TARGET_RADIUS,
        "wide-typed-discharge-consumed-first")
        for center in DEVELOPMENT_CENTERS)
    result = []
    for index, (center, seed, first, expected) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, first_targets, terminal["groups"])):
        fold = folds[index]
        truth = {tuple(round(value, 6) for value in point): str(color)
                 for point, color in zip(first.positions, first.species)}
        result.append((
            index, center, tuple(seed.positions), tuple(seed.species), truth,
            expected, tuple(fold["retained_stable_indices"]),
            next(row for row in portfolio["ranked_fold_digests"]
                 if int(row[0]) == index)[1]))
    return tuple(result), portfolio


def _parallel_groups(payloads, workers):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    with tempfile.TemporaryDirectory(prefix="gcts-wide-discharge-") as tmp:
        directory = Path(tmp)
        active, launched = [], 0
        while launched < len(payloads) or active:
            while launched < len(payloads) and len(active) < workers:
                input_path = directory / f"input-{launched}.pickle"
                output_path = directory / f"output-{launched}.pickle"
                input_path.write_bytes(pickle.dumps(payloads[launched]))
                process = subprocess.Popen(
                    [sys.executable, "-B", str(Path(__file__).resolve()),
                     "--group-pickle", str(input_path), str(output_path)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, env=environment)
                active.append((launched, process, output_path))
                launched += 1
            index, process, output_path = active.pop(0)
            output, error = process.communicate()
            if process.returncode:
                raise RuntimeError(
                    f"wide typed group {index} failed: {error.strip()}")
        return tuple(pickle.loads(
            (directory / f"output-{index}.pickle").read_bytes())
            for index in range(len(payloads)))


def build_dataset(*, workers=1):
    payloads, portfolio = _payloads()
    groups = (tuple(_evaluate_group(payload) for payload in payloads)
              if workers == 1 else _parallel_groups(payloads, workers))
    body = {
        "schema_version": 1,
        "source_terminal_dataset_digest": TERMINAL_DATASET_DIGEST,
        "source_wide_portfolio_audit_digest": portfolio["audit_digest"],
        "development_groups": len(groups),
        "retained_candidates": sum(len(group["rows"]) for group in groups),
        "maximum_retained_candidates": max(
            len(group["rows"]) for group in groups),
        "rollout_horizon": ROLLOUT_HORIZON,
        "rollout_radius": ROLLOUT_RADIUS,
        "trace_step_fields": TRACE_STEP_FIELDS,
        "maximum_transition_roles": MAXIMUM_TRANSITION_ROLES,
        "maximum_selected_roles": MAXIMUM_SELECTED_ROLES,
        "groups": groups,
        "semantic_selected_role_cohort_untruncated": True,
        "candidate_geometry_unchanged": True,
        "target_used_for_rollouts": False,
        "rollout_target_crop_constructed": False,
        "labels_joined_after_geometry_freeze": True,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
    }
    return {**body, "dataset_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("wide typed fixture byte drift")
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != digest or body["source_terminal_dataset_digest"] !=
            TERMINAL_DATASET_DIGEST or body["source_wide_portfolio_audit_digest"]
            != WIDE_PORTFOLIO_DIGEST or body["retained_candidates"] != 120
            or body["maximum_retained_candidates"] > 16
            or body["target_used_for_rollouts"]
            or body["rollout_target_crop_constructed"]
            or not body["labels_joined_after_geometry_freeze"]):
        raise AssertionError("wide typed discharge dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("wide typed discharge digest drift")
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
