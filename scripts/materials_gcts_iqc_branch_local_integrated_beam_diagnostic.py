#!/usr/bin/env python3
"""Consumed-target audit of a branch-local two-block IQC GCTS beam.

The complete first tree is fused target-free and its top eight parents are
retained.  Each parent independently builds its complete second tree; every
second terminal is rolled out for twelve target-free steps and ranked by
integrated frontier vote mass.  One child is retained per parent.  The eight
branch receipts and a global score order are hashed before the already-
consumed target is reconstructed.  This tests a real tree beam, not a greedy
scalar shared across unrelated parent contexts.
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

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_post_self_fed_deferred_pruning_diagnostic import (
    _key, load_default_result as load_deferred_result)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _colored_digest, _replay_first_terminal)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS, SEED_RADIUS)
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import OUTER_ORACLE_LIFT_BOUND
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_branch_local_integrated_beam_diagnostic_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "93cc05605e016196952194cf042268d44a9029957635c899e8b9aaed73dfb824"
EXPECTED_RESULT_DIGEST = \
    "db07213949d1bd1dd89ff73f63d14d6c6a664026948b0e6390860a23a2cf351b"
FIRST_BEAM_WIDTH = 8
ROLLOUT_HORIZON = 12
ROLLBACK_METRIC = "integrated_frontier_vote_mass"


def _frontier_mass(frontier):
    return sum(map(int, frontier.votes.values()))


def _integrated_rollout(source, state, runtime):
    masses = [_frontier_mass(state.proposals)]
    selected = []
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
        selected.append((tuple(point), int(state.proposals.votes[point])))
        state = _child(
            source, runtime["connection"], runtime["state_model"], state,
            point, descriptors[point], SECOND_BLOCK_RADIUS + SEED_RADIUS)
        masses.append(_frontier_mass(state.proposals))
    return {
        "integrated_frontier_vote_mass": float(sum(masses)),
        "frontier_vote_masses": tuple(masses),
        "accepted_children": len(selected),
        "selected_points_and_votes": tuple(selected),
        "fixed_point_reached": len(selected) < ROLLOUT_HORIZON,
        "target_used": False,
    }


def _worker(payload):
    (first_rank, expected_stable, first_actions, seed_positions, seed_species,
     expected_second_actions) = payload
    runtime = load_default_runtime()
    seed_source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    typed_first_actions = tuple((tuple(point), str(color))
                                for point, color in first_actions)
    first_state = _replay_first_terminal(
        seed_source, runtime, typed_first_actions)
    second_source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(first_state.positions),
        seed_species=tuple(first_state.species))
    states, counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    actual_actions = tuple(action_key(state.actions) for state in states)
    expected_actions = tuple(tuple((tuple(point), str(color))
                                   for point, color in actions)
                             for actions in expected_second_actions)
    if actual_actions != expected_actions:
        raise AssertionError("branch-local second candidate universe drift")
    traces = tuple({
        "stable_index": stable_index,
        "actions": action_key(state.actions),
        "trace": _integrated_rollout(second_source, state, runtime),
    } for stable_index, state in enumerate(states))
    order = tuple(row["stable_index"] for row in sorted(
        traces, key=lambda row: (
            -row["trace"]["integrated_frontier_vote_mass"],
            row["stable_index"])))
    selected = traces[order[0]]
    body = {
        "first_rank": first_rank,
        "first_stable_index": expected_stable,
        "first_actions": action_key(typed_first_actions),
        "second_candidate_counts": tuple(counts),
        "second_candidate_count": len(states),
        "second_candidate_digest": hashlib.sha256(
            repr(actual_actions).encode()).hexdigest(),
        "rollout_order": order,
        "selected_second_stable_index": selected["stable_index"],
        "selected_second_actions": selected["actions"],
        "selected_integrated_score":
            selected["trace"]["integrated_frontier_vote_mass"],
        "selected_trace": selected["trace"],
        "all_trace_digest": hashlib.sha256(
            canonical_json(traces)).hexdigest(),
        "target_used": False,
    }
    return {**body, "branch_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def _prepare_pool():
    import concurrent.futures.process as process
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def evaluate(*, workers=1):
    deferred = load_deferred_result()
    source_rows = deferred["receipt"]["second_sources"]
    if len(source_rows) != FIRST_BEAM_WIDTH:
        raise AssertionError("first beam width drift")
    seed_physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seed = _crop(seed_oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-branch-local-beam-consumed-seed")
    payloads = tuple((
        int(row["first_rank"]), int(row["first_stable_index"]),
        row["first_actions"], tuple(seed.positions), tuple(seed.species),
        row["second_actions"])
        for row in source_rows)
    if workers == 1:
        branches = tuple(_worker(payload) for payload in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            branches = tuple(pool.map(_worker, payloads))
    branches = tuple(sorted(branches, key=lambda row: row["first_rank"]))
    global_order = tuple(row["first_rank"] for row in sorted(
        branches, key=lambda row: (
            -row["selected_integrated_score"], row["first_rank"],
            row["selected_second_stable_index"])))
    receipt = {
        "schema_version": 1,
        "center": CONFIRMATION_CENTER,
        "seed_atoms": len(seed.positions),
        "seed_digest": _colored_digest(seed.positions, seed.species),
        "first_beam_width": FIRST_BEAM_WIDTH,
        "rollback_metric": ROLLBACK_METRIC,
        "rollout_horizon": ROLLOUT_HORIZON,
        "branches": branches,
        "global_parent_order": global_order,
        "globally_selected_first_rank": global_order[0],
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    target = _crop(oracle, CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS,
                   "IQC-branch-local-beam-consumed-target")
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    scored = tuple({
        "first_rank": branch["first_rank"],
        "first_correct_actions": sum(
            truth.get(_key(point)) == color
            for point, color in branch["first_actions"]),
        "first_exact": all(truth.get(_key(point)) == color
                           for point, color in branch["first_actions"]),
        "second_correct_actions": sum(
            truth.get(_key(point)) == color
            for point, color in branch["selected_second_actions"]),
        "second_exact": all(truth.get(_key(point)) == color
                            for point, color in
                            branch["selected_second_actions"]),
    } for branch in branches)
    exact_paths = tuple(row["first_rank"] for row in scored
                        if row["first_exact"] and row["second_exact"])
    selected = scored[global_order[0] - 1]
    body = {
        "schema_version": 1,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "target_open_count": 1,
        "target_atoms": len(target.positions),
        "scored_branches": scored,
        "exact_end_to_end_branch_ranks": exact_paths,
        "branch_local_beam_contains_exact_path": bool(exact_paths),
        "globally_selected_first_rank": global_order[0],
        "globally_selected_first_exact": selected["first_exact"],
        "globally_selected_second_exact": selected["second_exact"],
        "globally_selected_end_to_end_exact":
            selected["first_exact"] and selected["second_exact"],
        "target_used_for_candidate_rollout_or_ordering": False,
        "consumed_target_diagnostic_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["receipt"]["target_used"]
            or body["receipt"]["target_open_count_before_receipt"] != 0
            or hashlib.sha256(canonical_json(body["receipt"])).hexdigest()
            != body["receipt_digest"]
            or body["target_open_count"] != 1
            or body["target_used_for_candidate_rollout_or_ordering"]
            or not body["consumed_target_diagnostic_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("branch-local integrated beam drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("branch-local integrated beam result drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("branch-local integrated beam fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.workers <= 0:
        raise SystemExit("--workers must be positive")
    row = evaluate(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
