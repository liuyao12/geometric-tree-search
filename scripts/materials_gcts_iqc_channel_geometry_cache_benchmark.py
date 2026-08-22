#!/usr/bin/env python3
"""Consumed-prefix parity and cost audit for third-tree geometry memoization."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_iqc_three_block_channel_execution import (
    _channel_tree, _replay_action_set)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_channel_geometry_cache_benchmark_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "5041b2f7d29b549992ef2733b8beff6c6e099e2ec3be2675b66a73b7aebf020e")
EXPECTED_RESULT_DIGEST = (
    "0875d226c9f24ba302be58f50ba2e636ab013b677201d8c084d92b61f1b3c03f")
SOURCE_FIXTURE = ROOT / \
    "fixtures/iqc_three_block_portfolio_rehearsal_v1.json.gz"
CENTER = (-70., 10., 70.)
PARENT_ID = 8
CHILD_ID = 123


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _state_signature(states):
    payload = tuple((
        action_key(state.actions),
        tuple(sorted((str(color), tuple(map(float, point)))
                     for point, color in zip(
                         state.positions, state.species))),
        tuple(map(float, state.probabilities)), float(state.cumulative),
    ) for state in states)
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def evaluate():
    receipt = json.loads(gzip.decompress(
        SOURCE_FIXTURE.read_bytes()))["receipt"]
    branch = next(row for row in receipt["second_branches"]
                  if row["first_rank"] == PARENT_ID)
    seed, _ = oracle_crop_fast(CENTER, 9.)
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=CENTER, seed_positions=seed.positions,
        seed_species=seed.species)
    first, _ = _replay_action_set(
        source, runtime, branch["first_actions"], receipt["radii"][0])
    second_source = SimpleNamespace(
        group=CENTER, seed_positions=first.positions,
        seed_species=first.species)
    second, _ = _replay_action_set(
        second_source, runtime, branch["second_actions"][CHILD_ID],
        receipt["radii"][1])
    third_source = SimpleNamespace(
        group=CENTER, seed_positions=second.positions,
        seed_species=second.species)
    rows = []
    for cached in (False, True):
        telemetry = {}
        started = time.perf_counter()
        states, counts = _channel_tree(
            third_source, runtime, receipt["radii"][2],
            telemetry=telemetry, use_geometry_cache=cached)
        elapsed = time.perf_counter() - started
        rows.append({
            "geometry_cache_enabled": cached,
            "elapsed_seconds": elapsed,
            "candidate_counts": counts,
            "terminal_states": len(states),
            "state_signature": _state_signature(states),
            "telemetry": telemetry,
        })
    uncached, cached = rows
    body = {
        "schema_version": 1,
        "source_fixture_sha256": hashlib.sha256(
            SOURCE_FIXTURE.read_bytes()).hexdigest(),
        "consumed_prefix": {"center": CENTER, "parent": PARENT_ID,
                            "child": CHILD_ID},
        "uncached": uncached,
        "cached": cached,
        "exact_state_parity": bool(
            uncached["candidate_counts"] == cached["candidate_counts"] and
            uncached["terminal_states"] == cached["terminal_states"] and
            uncached["state_signature"] == cached["state_signature"]),
        "geometry_expansion_reduction":
            uncached["telemetry"]["unique_geometry_expansions"] -
            cached["telemetry"]["unique_geometry_expansions"],
        "measured_speedup": uncached["elapsed_seconds"] /
            cached["elapsed_seconds"],
        "target_used": False,
        "consumed_development_prefix_only": True,
        "fresh_confirmation_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or not body["exact_state_parity"] or
            body["geometry_expansion_reduction"] <= 0 or
            body["target_used"] or
            not body["consumed_development_prefix_only"] or
            body["fresh_confirmation_claimed"]):
        raise AssertionError("IQC channel geometry cache result drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("IQC channel geometry cache digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("IQC channel geometry cache fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate())
        text = json.dumps(row, indent=2, sort_keys=True) + "\n"
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({key: row[key] for key in (
        "exact_state_parity", "geometry_expansion_reduction",
        "measured_speedup", "result_digest")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
