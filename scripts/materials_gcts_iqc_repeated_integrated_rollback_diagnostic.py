#!/usr/bin/env python3
"""Consumed-target audit of one repeated integrated-rollback GCTS rule.

The complete first-block tree is enumerated without a target.  Every terminal
receives the same frozen target-free rollout used by the second-block audit,
and all predeclared metric/horizon orders are hashed.  The consumed first crop
is opened only afterward.  Together with the separately frozen second-block
rank audit, this tests whether integrated frontier vote mass at horizon twelve
is a coherent repeated block policy rather than a branch-specific exception.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_post_self_fed_deferred_pruning_diagnostic import (
    _complete_first_block, _key)
from materials_gcts_iqc_post_self_fed_deferred_pruning_rollout_rank import (
    _chunks, _rollout_chunk,
    load_default_result as load_second_block_result)
from materials_gcts_iqc_post_self_fed_port_discharge_value import (
    RULE_GRID, _score)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _colored_digest)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_self_fed_terminal_dataset import OUTER_ORACLE_LIFT_BOUND
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_repeated_integrated_rollback_diagnostic_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "70d659ccd80f716eb49029e37ade8d3e37e07ca7e0f02aeeb4b3bebc7966f298"
EXPECTED_RESULT_DIGEST = \
    "af11db827c6ee95246ff3979e6308e1c5e452bb34f89658bd5f7f9c16994c663"
REPEATED_RULE = ("integrated_frontier_vote_mass", 12)


def evaluate(*, workers=1):
    if workers > 1:
        import concurrent.futures.process as process
        try:
            process._check_system_limits()
        except PermissionError:
            # The managed macOS runner denies this advisory sysconf query.
            process._check_system_limits = lambda: None
    second_block = load_second_block_result()
    if (second_block["result_digest"] !=
            "a391cc21fc3060a02d546d4dfbb7f7b6f138d0b58d3a38083defdf3aad5980ea"
            or not second_block["integrated_vote_mass_h12_retains_exact"]):
        raise AssertionError("second-block integrated-rule evidence drift")
    seed_physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seed = _crop(seed_oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-repeated-rollback-consumed-seed")
    source, states, counts, _fusion_order, _fusion_scores = \
        _complete_first_block(seed)
    rows = tuple((stable_index, state)
                 for stable_index, state in enumerate(states))
    source_payload = {
        "group": source.group,
        "seed_positions": source.seed_positions,
        "seed_species": source.seed_species,
    }
    payloads = tuple((source_payload, chunk)
                     for chunk in _chunks(rows, workers))
    if workers == 1:
        parts = tuple(_rollout_chunk(payload) for payload in payloads)
    else:
        try:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                parts = tuple(pool.map(_rollout_chunk, payloads))
        except PermissionError:
            # Some managed macOS sandboxes deny only the advisory
            # SC_SEM_NSEMS_MAX query even though spawning and semaphores work.
            # Retry after bypassing that query; scientific inputs and worker
            # payloads remain byte-for-byte identical.
            import concurrent.futures.process as process
            original_check = process._check_system_limits
            process._check_system_limits = lambda: None
            try:
                with ProcessPoolExecutor(max_workers=workers) as pool:
                    parts = tuple(pool.map(_rollout_chunk, payloads))
            finally:
                process._check_system_limits = original_check
    traces = tuple(sorted(
        (row for part in parts for row in part),
        key=lambda row: row["stable_index"]))
    if len(traces) != len(states):
        raise AssertionError("incomplete first-block trace universe")
    rule_orders = {
        f"{metric}@{horizon}": tuple(row["stable_index"] for row in sorted(
            traces, key=lambda row: (
                -_score(row["trace"], (metric, horizon)),
                row["stable_index"])))
        for metric, horizon in RULE_GRID}
    repeated_key = f"{REPEATED_RULE[0]}@{REPEATED_RULE[1]}"
    selected_stable_index = rule_orders[repeated_key][0]
    receipt = {
        "schema_version": 1,
        "seed_atoms": len(seed.positions),
        "seed_digest": _colored_digest(seed.positions, seed.species),
        "first_candidate_counts": counts,
        "first_candidate_count": len(states),
        "rollout_rows": traces,
        "predeclared_rule_orders": rule_orders,
        "repeated_rule": REPEATED_RULE,
        "selected_stable_index": selected_stable_index,
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    target = _crop(oracle, CONFIRMATION_CENTER, TARGET_RADIUS,
                   "IQC-repeated-rollback-consumed-first-target")
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    exact_stable_indices = tuple(stable_index for stable_index, state in
                                 enumerate(states)
                                 if all(truth.get(_key(point)) == color
                                        for point, color in state.actions))
    exact_ranks_by_rule = {
        name: tuple(order.index(stable) + 1
                    for stable in exact_stable_indices)
        for name, order in rule_orders.items()}
    repeated_exact_ranks = exact_ranks_by_rule[repeated_key]
    body = {
        "schema_version": 1,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "target_open_count": 1,
        "target_atoms": len(target.positions),
        "exact_first_stable_indices": exact_stable_indices,
        "exact_ranks_by_predeclared_rule": exact_ranks_by_rule,
        "repeated_rule_exact_ranks": repeated_exact_ranks,
        "repeated_rule_selects_exact_first":
            selected_stable_index in exact_stable_indices,
        "second_block_same_rule_selects_exact":
            second_block["integrated_vote_mass_h12_retains_exact"],
        "second_block_evidence_digest": second_block["result_digest"],
        "consumed_two_block_rule_green": (
            selected_stable_index in exact_stable_indices
            and second_block["integrated_vote_mass_h12_retains_exact"]),
        "candidate_geometry_unchanged": True,
        "target_used_for_rollout_or_ordering": False,
        "development_rule_selected_after_consumed_scoring": True,
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
            or body["target_used_for_rollout_or_ordering"]
            or not body["development_rule_selected_after_consumed_scoring"]
            or not body["consumed_target_diagnostic_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("repeated integrated-rollback diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("repeated integrated-rollback result drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("repeated integrated-rollback fixture drift")
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
