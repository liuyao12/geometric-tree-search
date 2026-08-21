#!/usr/bin/env python3
"""Consumed-target audit of a clusters² future-option IQC beam.

Eight first-block parents and each parent's complete second-block candidate
tree were frozen before the historical target was opened.  This diagnostic
replays those immutable trees and asks four train-frozen recurrent marking
heads (base, colored, ports, coupled) to value each parent by its best eight
children.  Only after the parent order and receipt are hashed is the already
consumed target reconstructed for scoring.

This is a bounded lookahead/supply audit, not a fresh confirmation and not a
stationary or exponential-growth claim.
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

from materials_gcts_clusters2_future_option import (
    ChildOption, FrozenFutureOptionSpec, ParentOption,
    select_future_options)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    BRANCH_VARIANTS, action_key, branch_features, load_default_runtime)
from materials_gcts_iqc_post_self_fed_deferred_pruning_diagnostic import (
    load_default_result as load_deferred_result)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _colored_digest, _replay_first_terminal)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS, SEED_RADIUS)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    OUTER_ORACLE_LIFT_BOUND)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_recurrent_branch_value import score_recurrent_branch


CHANNEL_NAMES = tuple(BRANCH_VARIANTS)
TOP_K_CHILDREN = 8
PARENT_BEAM_WIDTH = 4
SPEC = FrozenFutureOptionSpec(
    CHANNEL_NAMES, top_k=TOP_K_CHILDREN, beam_width=PARENT_BEAM_WIDTH)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_clusters2_future_option_diagnostic_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "1ccded34f7ff1aadab67e1d23075489367d1186206ac46f85674f4d66b2984ad"
EXPECTED_RESULT_DIGEST = \
    "939b0ec11af4cfe0320debc1122b8aae259545c87ad5bc90580dd542f6f0bb03"


def _key(point):
    return tuple(round(float(value), 6) for value in point)


def _seed():
    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    return _crop(oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-clusters2-option-consumed-seed")


def _target():
    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    return _crop(oracle, CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS,
                 "IQC-clusters2-option-consumed-target")


def _worker(payload):
    source_row, seed_positions, seed_species = payload
    runtime = load_default_runtime()
    seed_source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    parent_actions = tuple((tuple(point), str(color))
                           for point, color in source_row["first_actions"])
    first_state = _replay_first_terminal(
        seed_source, runtime, parent_actions)
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(first_state.positions),
        seed_species=tuple(first_state.species))
    states, counts = _complete_states_at_radius(
        source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    children = []
    action_rows = tuple(action_key(state.actions) for state in states)
    expected = tuple(tuple((tuple(point), str(color))
                           for point, color in actions)
                     for actions in source_row["second_actions"])
    if action_rows != expected:
        raise AssertionError("child terminal identity drift")
    for stable_index, state in enumerate(states):
        full = branch_features(state)
        scores = tuple(score_recurrent_branch(
            runtime["branch_models"][name][2],
            tuple(full[index] for index in BRANCH_VARIANTS[name]),
            tuple(color for _point, color in state.actions))
            for name in CHANNEL_NAMES)
        child_id = (int(source_row["first_rank"]), stable_index)
        children.append(ChildOption(child_id, scores))
    canonical = tuple((child.child_id, child.channel_scores)
                      for child in children)
    return {
        "parent_id": int(source_row["first_rank"]),
        "first_stable_index": int(source_row["first_stable_index"]),
        "parent_actions": action_key(parent_actions),
        "children": tuple(children),
        "child_actions": tuple(action_rows),
        "child_count": len(children),
        "candidate_counts_by_depth": tuple(counts),
        "child_score_digest": hashlib.sha256(
            repr(canonical).encode()).hexdigest(),
        "target_used": False,
    }


def _prepare_pool():
    import concurrent.futures.process as process
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def _rank(scored, channel=None):
    if channel is None:
        return tuple(row.parent_id for row in sorted(
            scored, key=lambda row: (-row.mean_value, repr(row.parent_id))))
    return tuple(row.parent_id for row in sorted(
        scored, key=lambda row: (
            -row.channel_values[channel], repr(row.parent_id))))


def evaluate(*, workers=4):
    deferred = load_deferred_result()
    source_rows = tuple(deferred["receipt"]["second_sources"])
    if len(source_rows) != 8:
        raise AssertionError("frozen parent beam width drift")
    seed = _seed()
    payloads = tuple((row, tuple(seed.positions), tuple(seed.species))
                     for row in source_rows)
    if workers == 1:
        branches = tuple(_worker(payload) for payload in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            branches = tuple(pool.map(_worker, payloads))
    branches = tuple(sorted(branches, key=lambda row: row["parent_id"]))
    parent_options = tuple(ParentOption(
        row["parent_id"], row["children"]) for row in branches)
    selection = select_future_options(parent_options, SPEC)
    scored_by_parent = {row.parent_id: row for row in selection.scored}
    parent_rows = tuple({
        "parent_id": row["parent_id"],
        "first_stable_index": row["first_stable_index"],
        "parent_actions": row["parent_actions"],
        "child_count": row["child_count"],
        "candidate_counts_by_depth": row["candidate_counts_by_depth"],
        "child_score_digest": row["child_score_digest"],
        "channel_values": scored_by_parent[row["parent_id"]].channel_values,
        "mean_value": scored_by_parent[row["parent_id"]].mean_value,
        "best_child_ids": scored_by_parent[row["parent_id"]].best_child_ids,
        "target_used": False,
    } for row in branches)
    receipt = {
        "schema_version": 1,
        "center": CONFIRMATION_CENTER,
        "seed_atoms": len(seed.positions),
        "seed_digest": _colored_digest(seed.positions, seed.species),
        "source_candidate_digest": deferred["receipt"][
            "first_candidate_digest"],
        "channel_names": CHANNEL_NAMES,
        "top_k_children": TOP_K_CHILDREN,
        "parent_beam_width": PARENT_BEAM_WIDTH,
        "parent_rows": parent_rows,
        "channel_parent_orders": tuple(
            _rank(selection.scored, channel)
            for channel in range(len(CHANNEL_NAMES))),
        "mean_parent_order": _rank(selection.scored),
        "selected_parent_ids": selection.selected_parent_ids,
        "selected_by_channels": selection.selected_by_channels,
        "selected_child_ids_by_parent":
            selection.selected_child_ids_by_parent,
        "candidate_digest": selection.candidate_digest,
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    # The historical target is reconstructed only after the option-value
    # receipt, candidate digest, and selected parent IDs are immutable.
    target = _target()
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    branch_lookup = {row["parent_id"]: row for row in branches}
    scored = []
    for row in parent_rows:
        parent_id = row["parent_id"]
        branch = branch_lookup[parent_id]
        parent_exact = all(truth.get(_key(point)) == color
                           for point, color in row["parent_actions"])
        exact_children = tuple(index for index, actions in enumerate(
            branch["child_actions"]) if all(
                truth.get(_key(point)) == color for point, color in actions))
        channel_top8_exact = []
        channel_best_exact = []
        for channel in range(len(CHANNEL_NAMES)):
            order = tuple(sorted(branch["children"], key=lambda child: (
                -child.channel_scores[channel], repr(child.child_id))))
            channel_best_exact.append(order[0].child_id[1]
                                      in exact_children)
            channel_top8_exact.append(sum(
                child.child_id[1] in exact_children
                for child in order[:TOP_K_CHILDREN]))
        scored.append({
            "parent_id": parent_id,
            "parent_exact": parent_exact,
            "exact_child_count": len(exact_children),
            "channel_best_child_exact": tuple(channel_best_exact),
            "channel_exact_children_in_top_k": tuple(channel_top8_exact),
            "end_to_end_exact_supply": parent_exact and bool(exact_children),
        })
    exact_parent_ids = tuple(row["parent_id"] for row in scored
                             if row["parent_exact"])
    exact_path_parent_ids = tuple(row["parent_id"] for row in scored
                                  if row["end_to_end_exact_supply"])
    retained_exact = tuple(parent_id for parent_id in
                           selection.selected_parent_ids
                           if parent_id in exact_path_parent_ids)
    child_portfolios = dict(selection.selected_child_ids_by_parent)
    retained_exact_paths = tuple(
        (row["parent_id"], child_id)
        for row in scored if row["parent_exact"]
        for child_id in child_portfolios.get(row["parent_id"], ())
        if child_id[1] in {
            index for index, actions in enumerate(
                branch_lookup[row["parent_id"]]["child_actions"])
            if all(truth.get(_key(point)) == color
                   for point, color in actions)})
    body = {
        "schema_version": 1,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "target_open_count": 1,
        "target_atoms": len(target.positions),
        "scored_parents": tuple(scored),
        "exact_parent_ids": exact_parent_ids,
        "exact_path_parent_ids": exact_path_parent_ids,
        "retained_exact_path_parent_ids": retained_exact,
        "future_option_retains_exact_path": bool(retained_exact),
        "retained_exact_parent_child_paths": retained_exact_paths,
        "future_option_child_portfolio_retains_exact_path":
            bool(retained_exact_paths),
        "mean_option_first_exact_rank": next((
            rank for rank, parent_id in enumerate(
                receipt["mean_parent_order"], 1)
            if parent_id in exact_path_parent_ids), None),
        "channel_first_exact_ranks": tuple(next((
            rank for rank, parent_id in enumerate(order, 1)
            if parent_id in exact_path_parent_ids), None)
            for order in receipt["channel_parent_orders"]),
        "candidate_geometry_unchanged": True,
        "target_used_for_tree_or_ranking": False,
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
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_tree_or_ranking"]
            or not body["consumed_target_diagnostic_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("clusters-squared future-option result drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("clusters-squared future-option digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("clusters-squared future-option fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = evaluate(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(text.encode(), mtime=0))
    print(text if args.json else row)


if __name__ == "__main__":
    main()
