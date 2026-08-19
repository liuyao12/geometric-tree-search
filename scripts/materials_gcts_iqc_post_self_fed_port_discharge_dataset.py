#!/usr/bin/env python3
"""Freeze target-free port-discharge rollouts for the bounded IQC portfolio.

The two marking heads retain at most two exact-geometry terminals per consumed
development nucleus.  This builder reconstructs only those retained states,
then advances each for a fixed 16-action horizon with the already-frozen
pose/port marking.  The rollout radius is one additional public seed-radius
shell.  No second-block target, scorer, correctness label, or oracle site is
available while a trace is generated.  Labels are copied from the consumed
terminal fixture only after every retained trace in a nucleus is frozen.
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
    _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_post_self_fed_marking_portfolio import (
    EXPECTED_AUDIT_DIGEST as PORTFOLIO_AUDIT_DIGEST,
    load_default_result as load_portfolio_result)
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
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state


ROLLOUT_HORIZON = 16
ROLLOUT_RADIUS = SECOND_BLOCK_RADIUS + SEED_RADIUS
TRACE_STEP_FIELDS = (
    "frontier_count_before", "frontier_vote_mass_before",
    "frontier_max_vote_before", "selected_probability", "selected_votes",
    "selected_color", "frontier_count_after", "frontier_vote_mass_after",
    "frontier_max_vote_after",
)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_port_discharge_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "16c0eebe9e22b7b07d1989613f94c380a0939813ae4daab5ce5e80c0b7aa00c4"
EXPECTED_DATASET_DIGEST = \
    "0f3805854fa6f41a3fbe019f6d1506afe4a90b8b4094f38ea21e3957666cda0c"


def _frontier_summary(frontier):
    votes = tuple(map(int, frontier.votes.values()))
    return len(votes), sum(votes), max(votes, default=0)


def _rollout(source, state, runtime):
    steps = []
    for _depth in range(ROLLOUT_HORIZON):
        before = _frontier_summary(state.proposals)
        if before[0] == 0:
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
        state = _child(
            source, runtime["connection"], runtime["state_model"], state,
            point, descriptors[point], ROLLOUT_RADIUS)
        after = _frontier_summary(state.proposals)
        steps.append({
            "frontier_count_before": before[0],
            "frontier_vote_mass_before": before[1],
            "frontier_max_vote_before": before[2],
            "selected_probability": probability,
            "selected_votes": votes,
            "selected_color": str(state.actions[-1][1]),
            "frontier_count_after": after[0],
            "frontier_vote_mass_after": after[1],
            "frontier_max_vote_after": after[2],
        })
    return {
        "steps": steps,
        "accepted_children": len(steps),
        "fixed_point_reached": len(steps) < ROLLOUT_HORIZON,
        "final_frontier_count": _frontier_summary(state.proposals)[0],
        "final_frontier_vote_mass": _frontier_summary(state.proposals)[1],
        "final_frontier_max_vote": _frontier_summary(state.proposals)[2],
        "cumulative_selected_votes": sum(
            step["selected_votes"] for step in steps),
        "cumulative_log_probability": sum(math.log(max(
            float(step["selected_probability"]), 1e-15)) for step in steps),
        "target_used": False,
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
    inherited = inherited[0]
    second_source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited.positions,
        seed_species=inherited.species)
    states, counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    if (tuple(counts) != tuple(expected["second_block_counts"])
            or len(states) != len(expected["rows"])):
        raise AssertionError(f"group {group_index} source candidate drift")

    # Freeze every target-free trace first.  The following label join is a
    # deliberately separate pass so correctness cannot influence a rollout.
    geometry_rows = []
    for stable_index in retained_stable_indices:
        state = states[int(stable_index)]
        expected_row = expected["rows"][int(stable_index)]
        if (int(expected_row["stable_index"]) != int(stable_index)
                or tuple(expected_row["action_colors"]) != tuple(
                    color for _point, color in state.actions)):
            raise AssertionError(f"group {group_index} terminal drift")
        geometry_rows.append({
            "stable_index": int(stable_index),
            "source_action_digest": hashlib.sha256(
                repr(action_key(state.actions)).encode()).hexdigest(),
            "trace": _rollout(second_source, state, runtime),
        })
    frozen_geometry_digest = hashlib.sha256(json.dumps(
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
        "source_feature_digest": expected["feature_digest"],
        "source_inherited_action_digest": expected["inherited_action_digest"],
        "source_candidate_counts": tuple(counts),
        "frozen_geometry_digest_before_label_join": frozen_geometry_digest,
        "rows": rows,
        "target_used_for_rollouts": False,
        "labels_joined_after_all_group_traces_frozen": True,
    }


def build_dataset(*, workers=1):
    source_raw, source_payload = load_fixture_json(SOURCE_FIXTURE)
    if hashlib.sha256(source_raw).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise AssertionError("source terminal fixture byte drift")
    source = validate_source_dataset(source_payload)
    if source["dataset_digest"] != SOURCE_DATASET_DIGEST:
        raise AssertionError("source terminal dataset drift")
    portfolio = load_portfolio_result()
    if portfolio["audit_digest"] != PORTFOLIO_AUDIT_DIGEST:
        raise AssertionError("source portfolio drift")
    portfolio_folds = {int(row["heldout_group"]): row
                       for row in portfolio["folds"]}

    # The oracle supplies only the original seed and already-consumed first
    # block needed to identify the inherited state.  No rollout target crop is
    # constructed at any radius.
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "IQC-port-discharge-seed")
                  for center in DEVELOPMENT_CENTERS)
    first_targets = tuple(_crop(
        oracle, center, TARGET_RADIUS,
        "IQC-port-discharge-consumed-first-target")
        for center in DEVELOPMENT_CENTERS)
    payloads = []
    for index, (center, seed, first, expected) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, first_targets, source["groups"])):
        fold = portfolio_folds[index]
        truth = {tuple(round(value, 6) for value in point): str(color)
                 for point, color in zip(first.positions, first.species)}
        payloads.append((
            index, center, tuple(seed.positions), tuple(seed.species), truth,
            expected, tuple(fold["retained_stable_indices"]),
            fold["candidate_universe_digest"]))
    if workers == 1:
        groups = tuple(_evaluate_group(payload) for payload in payloads)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_evaluate_group, payloads))
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "source_portfolio_audit_digest": portfolio["audit_digest"],
        "development_groups": len(groups),
        "rollout_horizon": ROLLOUT_HORIZON,
        "rollout_radius": ROLLOUT_RADIUS,
        "trace_step_fields": TRACE_STEP_FIELDS,
        "groups": groups,
        "target_used_for_rollouts": False,
        "rollout_target_crop_constructed": False,
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
            or body["source_portfolio_audit_digest"] != PORTFOLIO_AUDIT_DIGEST
            or body["development_groups"] != len(DEVELOPMENT_CENTERS)
            or body["rollout_horizon"] != ROLLOUT_HORIZON
            or abs(body["rollout_radius"] - ROLLOUT_RADIUS) > 1e-12
            or tuple(body["trace_step_fields"]) != TRACE_STEP_FIELDS
            or body["target_used_for_rollouts"]
            or body["rollout_target_crop_constructed"]
            or not body["labels_copied_from_consumed_development_fixture"]
            or body["fresh_confirmation_claimed"]):
        raise AssertionError("post-self-fed port-discharge dataset drift")
    rows = [row for group in body["groups"] for row in group["rows"]]
    if (len(rows) != 19 or any(
            row["trace"]["target_used"]
            or len(row["trace"]["steps"]) > ROLLOUT_HORIZON
            or any(set(step) != set(TRACE_STEP_FIELDS)
                   for step in row["trace"]["steps"])
            for row in rows) or any(
                group["target_used_for_rollouts"]
                or not group["labels_joined_after_all_group_traces_frozen"]
                for group in body["groups"])):
        raise AssertionError("invalid port-discharge trace corpus")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("post-self-fed port-discharge digest drift")
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
