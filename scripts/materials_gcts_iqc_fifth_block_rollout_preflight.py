#!/usr/bin/env python3
"""Freeze one target-blind fifth-block rollout for shortlisted IQC lineages."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_bounded_lineage_value import canonical_json
from materials_gcts_iqc_fourth_block_action_marking import \
    load_fourth_block_runtime
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_iqc_fourth_block_winner_preflight import (
    CONFIRMATION_GROUP, DEVELOPMENT_GROUPS, SHORTLIST, _fit, _order, _rows,
    load_default_result as load_winner_preflight)
from materials_gcts_iqc_three_block_channel_execution import _channel_tree
from materials_gcts_iqc_three_block_portfolio_execution import _prepare_pool
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fifth_block_rollout_preflight_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "1352362617a400b9943c5d4b1a7b59c247b39a0c4b0b992103b16c1af6ae6285"
EXPECTED_RESULT_DIGEST = \
    "d5fb35b3ceaeb3682aa40180b53f90487c8cf222c9fccd63585c4421c6f7b68b"
ROLLOUT_FEATURE_NAMES = (
    "depth1-states", "depth2-states", "depth3-states",
    "naive-expansions", "unique-expansions", "saved-expansions",
    "terminal-cumulative-maximum", "terminal-cumulative-mean",
    "terminal-vote-sum-maximum", "terminal-vote-sum-mean")


def _shortlists():
    by_group, _receipt, _beams = _rows()
    rows = []
    for heldout in DEVELOPMENT_GROUPS:
        training = tuple(row for group in DEVELOPMENT_GROUPS
                         if group != heldout for row in by_group[group])
        order, scores = _order(_fit(training), by_group[heldout])
        rows.append((heldout, tuple({
            "rank": rank,
            "parent_index": by_group[heldout][index].parent_index,
            "stable_index": by_group[heldout][index].stable_index,
            "linear_score": scores[index],
            "actions": by_group[heldout][index].actions,
        } for rank, index in enumerate(order[:SHORTLIST], 1))))
    confirmation = load_winner_preflight()
    rows.append((CONFIRMATION_GROUP, tuple({
        "rank": int(row["rank"]),
        "parent_index": int(row["parent_index"]),
        "stable_index": int(row["stable_index"]),
        "linear_score": float(row["score"]),
        "actions": tuple((tuple(map(float, point)), str(color))
                         for point, color in row["actions"]),
    } for row in confirmation["shortlist"])))
    return tuple(rows), confirmation


@lru_cache(maxsize=None)
def _context(group):
    beam = load_beams()["beams"][group]
    seed, _ = oracle_crop_fast(beam["center"], beam["seed_radius"])
    increment = float(beam["next_radius"] - beam["replay_radii"][-1])
    if increment <= 0 or not math.isfinite(increment):
        raise AssertionError("invalid public radius increment")
    return beam, seed, load_fourth_block_runtime(), \
        float(beam["next_radius"] + increment)


def _worker(task):
    group, rank, parent_index, stable_index, linear_score, actions = task
    beam, seed, runtime, radius = _context(int(group))
    actions = tuple((tuple(map(float, point)), str(color))
                    for point, color in actions)
    source = SimpleNamespace(
        group=tuple(map(float, beam["center"])),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed.positions) +
                       tuple(point for point, _color in actions),
        seed_species=tuple(map(str, seed.species)) +
                     tuple(color for _point, color in actions))
    telemetry = {}
    states, counts = _channel_tree(
        source, runtime, radius, telemetry=telemetry,
        action_budget=8, baseline_slots=3)
    cumulative = tuple(float(state.cumulative) for state in states)
    vote_sums = tuple(float(sum(state.votes)) for state in states)
    features = (
        *(float(value) for value in counts),
        float(telemetry["naive_geometry_expansions"]),
        float(telemetry["unique_geometry_expansions"]),
        float(telemetry["saved_geometry_expansions"]),
        max(cumulative, default=-1e6),
        sum(cumulative) / len(cumulative) if cumulative else -1e6,
        max(vote_sums, default=0.),
        sum(vote_sums) / len(vote_sums) if vote_sums else 0.,
    )
    if len(features) != len(ROLLOUT_FEATURE_NAMES) or any(
            not math.isfinite(value) for value in features):
        raise AssertionError("fifth-block rollout feature drift")
    return {
        "group": int(group), "rank": int(rank),
        "parent_index": int(parent_index),
        "stable_index": int(stable_index),
        "linear_score": float(linear_score),
        "actions": actions, "fifth_radius": radius,
        "features": features,
        "fifth_block_candidate_digest": hashlib.sha256(repr(tuple(
            state.actions for state in states)).encode()).hexdigest(),
        "target_used": False,
    }


def evaluate(workers=4):
    if workers < 1:
        raise ValueError("workers must be positive")
    shortlists, winner = _shortlists()
    tasks = tuple((group, row["rank"], row["parent_index"],
                   row["stable_index"], row["linear_score"], row["actions"])
                  for group, rows in shortlists for row in rows)
    if workers == 1:
        result = tuple(map(_worker, tasks))
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            result = tuple(pool.map(_worker, tasks))
    if len(result) != len(tasks) or any(row["target_used"] for row in result):
        raise AssertionError("fifth-block rollout task accounting drift")
    groups = tuple({
        "group": group,
        "rows": tuple(row for row in result if row["group"] == group),
    } for group, _rows_group in shortlists)
    if any(len(row["rows"]) != SHORTLIST for row in groups):
        raise AssertionError("fifth-block shortlist width drift")
    body = {
        "schema_version": 1,
        "source_winner_preflight_result_digest": winner["result_digest"],
        "groups": tuple(group for group, _rows_group in shortlists),
        "shortlist_size_each": SHORTLIST,
        "rollout_feature_names": ROLLOUT_FEATURE_NAMES,
        "group_rows": groups,
        "candidate_receipts_frozen_before_rollout": True,
        "targets_opened": False,
        "target_or_correctness_used": False,
        "candidate_geometry_changed": False,
        "winner_selected": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or tuple(body["groups"]) != DEVELOPMENT_GROUPS +
            (CONFIRMATION_GROUP,)
            or body["shortlist_size_each"] != SHORTLIST
            or tuple(body["rollout_feature_names"]) != ROLLOUT_FEATURE_NAMES
            or not body["candidate_receipts_frozen_before_rollout"]
            or body["targets_opened"] or body["target_or_correctness_used"]
            or body["candidate_geometry_changed"] or body["winner_selected"]):
        raise AssertionError("fifth-block rollout preflight drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("fifth-block rollout result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("fifth-block rollout fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate(args.workers))
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({
        "groups": row["groups"],
        "shortlist_size_each": row["shortlist_size_each"],
        "targets_opened": row["targets_opened"],
        "result_digest": row["result_digest"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
