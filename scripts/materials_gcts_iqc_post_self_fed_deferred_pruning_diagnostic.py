#!/usr/bin/env python3
"""Consumed-target audit of deferred first-block pruning for IQC GCTS.

The complete 128-terminal first tree is scored with the already-frozen fusion
value before pruning.  Its top eight states are then self-fed independently
into the unchanged width-two second-block marking portfolio.  Every candidate
set is frozen without a target; the consumed confirmation target is constructed
only afterward to measure exact cross-block supply.
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

from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, select_equivariant_port_fusion)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    _local_section, _partial, action_key, branch_features,
    load_default_runtime)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _colored_digest, _second_block_candidates)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import OUTER_ORACLE_LIFT_BOUND
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


FIRST_BLOCK_WIDTH = 8
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_deferred_pruning_diagnostic_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "bdb1e0c1984b5c67d5435e6b3e53eae393132b85ab6b4c398887cbe3ba9c6779"
EXPECTED_RESULT_DIGEST = \
    "9e6fb8ba8aba1c3f4d736994b4e572ba3b5bed15a5d5595907d3469393c6c87c"


def _key(point):
    return tuple(round(value, 6) for value in point)


def _complete_first_block(seed):
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(seed.positions), seed_species=tuple(seed.species))
    states, counts = _complete_states_at_radius(
        source, runtime, TARGET_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    candidates = []
    for stable_index, state in enumerate(states):
        partial, graph = _partial(
            source, state, runtime["grouped_vocabulary"])
        features = tuple(branch_features(state)) + _local_section(state) + partial
        candidates.append(EquivariantPortFusionCandidate(
            features, tuple(color for _point, color in state.actions), graph,
            stable_index))
    selection = select_equivariant_port_fusion(
        runtime["fusion_model"], tuple(candidates))
    order = tuple(sorted(range(len(states)), key=lambda index: (
        -selection.fused_scores[index], index)))
    return source, states, tuple(counts), order, tuple(selection.fused_scores)


def _second_block_worker(payload):
    first_rank, first_stable_index, positions, species, actions = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=tuple(positions),
        seed_species=tuple(species))
    states, counts = _complete_states_at_radius(
        source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    rows, retained, candidate_digest, model_digests = \
        _second_block_candidates(source, states, runtime)
    return {
        "first_rank": first_rank,
        "first_stable_index": first_stable_index,
        "first_actions": action_key(actions),
        "second_candidate_counts": tuple(counts),
        "second_candidate_count": len(rows),
        "second_candidate_digest": candidate_digest,
        "second_actions": tuple(action_key(row["state"].actions)
                                for row in rows),
        "retained": tuple({
            "stable_index": row["stable_index"],
            "marking": row["marking"],
            "actions": action_key(row["state"].actions),
        } for row in retained),
        "model_digests": model_digests,
        "target_used": False,
    }


def evaluate(*, workers=1):
    # Seed construction is deliberately bounded below the confirmation target
    # radius.  No target crop exists while either tree is enumerated.
    seed_physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                              + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seed = _crop(seed_oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-deferred-pruning-consumed-seed")
    _source, first_states, first_counts, first_order, first_scores = \
        _complete_first_block(seed)
    retained_first = first_order[:FIRST_BLOCK_WIDTH]
    payloads = tuple((rank, stable, first_states[stable].positions,
                      first_states[stable].species,
                      first_states[stable].actions)
                     for rank, stable in enumerate(retained_first, 1))
    if workers == 1:
        second = tuple(_second_block_worker(payload) for payload in payloads)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            second = tuple(pool.map(_second_block_worker, payloads))
    receipt = {
        "schema_version": 1,
        "center": CONFIRMATION_CENTER,
        "seed_atoms": len(seed.positions),
        "seed_digest": _colored_digest(seed.positions, seed.species),
        "first_candidate_counts": first_counts,
        "first_candidate_count": len(first_states),
        "first_candidate_digest": hashlib.sha256(repr(tuple(
            (action_key(state.actions), first_scores[index])
            for index, state in enumerate(first_states))).encode()).hexdigest(),
        "first_retained_width": FIRST_BLOCK_WIDTH,
        "first_retained_stable_indices": retained_first,
        "second_sources": second,
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                         + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    target = _crop(oracle, CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS,
                   "IQC-deferred-pruning-consumed-target")
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    scored = []
    for source in second:
        first_correct = sum(truth.get(_key(point)) == color
                            for point, color in source["first_actions"])
        second_correct = tuple(sum(truth.get(_key(point)) == color
                                   for point, color in actions)
                               for actions in source["second_actions"])
        second_exact_indices = tuple(
            index for index, value in enumerate(second_correct)
            if value == 3)
        retained = tuple({
            **row,
            "correct_actions": sum(truth.get(_key(point)) == color
                                   for point, color in row["actions"]),
            "exact": all(truth.get(_key(point)) == color
                         for point, color in row["actions"]),
        } for row in source["retained"])
        scored.append({
            "first_rank": source["first_rank"],
            "first_stable_index": source["first_stable_index"],
            "first_correct_actions": first_correct,
            "first_exact": first_correct == 3,
            "second_exact_candidates": len(second_exact_indices),
            "second_exact_candidate_stable_indices": second_exact_indices,
            "second_best_correct_actions": max(second_correct, default=0),
            "portfolio_retained": retained,
            "portfolio_contains_exact": any(row["exact"] for row in retained),
            "end_to_end_candidate_exact_supply": (
                first_correct == 3 and bool(second_exact_indices)),
            "end_to_end_portfolio_exact_supply": (
                first_correct == 3 and any(row["exact"] for row in retained)),
        })
    first_exact_ranks = tuple(row["first_rank"] for row in scored
                              if row["first_exact"])
    candidate_exact_paths = tuple(
        (row["first_rank"], stable_index)
        for row in scored if row["first_exact"]
        for stable_index in row["second_exact_candidate_stable_indices"])
    portfolio_exact_paths = tuple(
        (row["first_rank"], retained["stable_index"])
        for row in scored if row["first_exact"]
        for retained in row["portfolio_retained"] if retained["exact"])
    body = {
        "schema_version": 1,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "target_open_count": 1,
        "target_atoms": len(target.positions),
        "target_digest": _colored_digest(target.positions, target.species),
        "scored_sources": tuple(scored),
        "first_exact_ranks_in_width": first_exact_ranks,
        "cross_block_candidate_exact_paths": candidate_exact_paths,
        "cross_block_portfolio_exact_paths": portfolio_exact_paths,
        "cross_block_candidate_exact_supply": bool(candidate_exact_paths),
        "cross_block_portfolio_exact_supply": bool(portfolio_exact_paths),
        "deferred_pruning_retains_exact_first_block": bool(first_exact_ranks),
        "candidate_geometry_unchanged": True,
        "target_used_for_candidate_or_portfolio_selection": False,
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
            or body["schema_version"] != 1
            or body["receipt"]["target_used"]
            or body["receipt"]["target_open_count_before_receipt"] != 0
            or hashlib.sha256(canonical_json(body["receipt"])).hexdigest()
            != body["receipt_digest"]
            or body["target_open_count"] != 1
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_candidate_or_portfolio_selection"]
            or not body["consumed_target_diagnostic_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("deferred-pruning diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("deferred-pruning result digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("deferred-pruning fixture byte drift")
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
