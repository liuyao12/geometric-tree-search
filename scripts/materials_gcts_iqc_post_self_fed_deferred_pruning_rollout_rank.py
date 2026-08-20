#!/usr/bin/env python3
"""Consumed-target rank audit of frozen rollback on the exact IQC branch.

The exact first-block state and its complete 127-state second frontier are
already established by the deferred-pruning diagnostics.  Here every second
state receives the same frozen 16-step target-free continuation trace, and is
ordered by the preregistered frontier-vote-mass value at horizon twelve.  The
consumed target is reconstructed only after all traces and their ordering are
hashed, solely to measure whether rollback supplies a bounded exact action.
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
from materials_gcts_iqc_post_self_fed_deferred_pruning_diagnostic import _key
from materials_gcts_iqc_post_self_fed_deferred_pruning_portfolio_rank import (
    build_exact_second_frontier)
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import _rollout
from materials_gcts_iqc_post_self_fed_port_discharge_value import (
    RULE_GRID, _score)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _colored_digest, _trace_score)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, ROLLBACK_HORIZON, ROLLBACK_METRIC,
    SECOND_BLOCK_RADIUS)
from materials_gcts_iqc_self_fed_terminal_dataset import OUTER_ORACLE_LIFT_BOUND
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_deferred_pruning_rollout_rank_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "398be53195bd4eae9dbc0856945c7c9cb3ae906ecdaa62e609660d5925c63acd"
EXPECTED_RESULT_DIGEST = \
    "a391cc21fc3060a02d546d4dfbb7f7b6f138d0b58d3a38083defdf3aad5980ea"


def _rollout_chunk(payload):
    source_payload, rows = payload
    from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(source_payload["group"]),
        seed_positions=tuple(source_payload["seed_positions"]),
        seed_species=tuple(source_payload["seed_species"]))
    result = []
    for stable_index, state in rows:
        trace = _rollout(source, state, runtime)
        result.append({
            "stable_index": stable_index,
            "rollback_score": _trace_score(trace),
            "trace": trace,
        })
    return tuple(result)


def _chunks(rows, count):
    count = max(1, min(count, len(rows)))
    return tuple(tuple(rows[index::count]) for index in range(count))


def evaluate(*, workers=1):
    rebuilt = build_exact_second_frontier()
    second_source = rebuilt["second_source"]
    rows = tuple((row["stable_index"], row["state"])
                 for row in rebuilt["rows"])
    source_payload = {
        "group": second_source.group,
        "seed_positions": second_source.seed_positions,
        "seed_species": second_source.seed_species,
    }
    payloads = tuple((source_payload, chunk)
                     for chunk in _chunks(rows, workers))
    if workers == 1:
        parts = tuple(_rollout_chunk(payload) for payload in payloads)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = tuple(pool.map(_rollout_chunk, payloads))
    traces = tuple(sorted(
        (row for part in parts for row in part),
        key=lambda row: row["stable_index"]))
    if len(traces) != len(rows):
        raise AssertionError("incomplete rollback trace universe")
    order = tuple(row["stable_index"] for row in sorted(
        traces, key=lambda row: (-row["rollback_score"],
                                row["stable_index"])))
    rule_orders = {
        f"{metric}@{horizon}": tuple(row["stable_index"] for row in sorted(
            traces, key=lambda row: (
                -_score(row["trace"], (metric, horizon)),
                row["stable_index"])))
        for metric, horizon in RULE_GRID}
    receipt = {
        "schema_version": 1,
        "consumed_first_rank": rebuilt["exact_source"]["first_rank"],
        "consumed_first_stable_index":
            rebuilt["exact_source"]["first_stable_index"],
        "second_candidate_counts": rebuilt["counts"],
        "second_candidate_count": len(rows),
        "second_candidate_digest": rebuilt["candidate_digest"],
        "rollback_metric": ROLLBACK_METRIC,
        "rollback_horizon": ROLLBACK_HORIZON,
        "rollout_rows": traces,
        "rollout_order": order,
        "predeclared_rule_orders": rule_orders,
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    target = _crop(oracle, CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS,
                   "IQC-deferred-rollout-rank-consumed-target")
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    exact_stable_indices = tuple(row["stable_index"]
                                 for row in rebuilt["rows"]
                                 if all(truth.get(_key(point)) == color
                                        for point, color in
                                        row["state"].actions))
    exact_ranks = tuple(order.index(stable) + 1
                        for stable in exact_stable_indices)
    exact_ranks_by_rule = {
        name: tuple(order.index(stable) + 1
                    for stable in exact_stable_indices)
        for name, order in rule_orders.items()}
    best_exact_rank = min(exact_ranks)
    body = {
        "schema_version": 1,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "target_open_count": 1,
        "target_atoms": len(target.positions),
        "target_digest": _colored_digest(target.positions, target.species),
        "exact_second_stable_indices": exact_stable_indices,
        "exact_rollback_ranks": exact_ranks,
        "exact_ranks_by_predeclared_rule": exact_ranks_by_rule,
        "best_exact_rollback_rank": best_exact_rank,
        "top_one_rollback_retains_exact": best_exact_rank <= 1,
        "top_eight_rollback_retains_exact": best_exact_rank <= 8,
        "top_sixteen_rollback_retains_exact": best_exact_rank <= 16,
        "integrated_vote_mass_h12_retains_exact":
            min(exact_ranks_by_rule[
                "integrated_frontier_vote_mass@12"]) == 1,
        "development_rule_selected_after_consumed_scoring": True,
        "candidate_geometry_unchanged": True,
        "target_used_for_rollout_or_ordering": False,
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
            or not body["consumed_target_diagnostic_only"]
            or not body["development_rule_selected_after_consumed_scoring"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("deferred rollback-rank diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("deferred rollback-rank result digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("deferred rollback-rank fixture byte drift")
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
