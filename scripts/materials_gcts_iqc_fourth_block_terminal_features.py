#!/usr/bin/env python3
"""Freeze target-blind causal terminal features for fourth-block IQC beams.

The marked extension receipts contain exact candidate geometry but deliberately
omit correctness and rank features.  This module reconstructs each already
frozen parent tree with the same runtime and stores only local GCTS state:
branch marking probabilities, votes, pose/port channels, and immediate future
frontier support.  It never imports a target or scorer.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_bounded_lineage_value import canonical_json
from materials_gcts_iqc_fourth_block_action_marking import (
    load_default_artifact, load_fourth_block_runtime)
from materials_gcts_iqc_fourth_block_beam_fixture import (
    load_default_result as load_beams)
from materials_gcts_iqc_fourth_block_marked_extension import load_group
from materials_gcts_iqc_frozen_fusion_runtime import (
    BRANCH_NAMES, action_key, branch_features)
from materials_gcts_iqc_three_block_channel_execution import _channel_tree
from materials_gcts_iqc_three_block_portfolio_execution import _prepare_pool
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_terminal_features_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "e01b5a7255cdeeab8d6ae28d7c6fdf1fd23c16f91cb91f8f37d7ee869e556632"
EXPECTED_RESULT_DIGEST = \
    "3e01b1cfc37a957165763b23a97f51bc37345530fd38ac2886d80309a052efe4"
GROUPS = (2, 3, 4)
FEATURE_NAMES = BRANCH_NAMES + (
    "future:candidate-count", "future:vote-sum", "future:vote-maximum",
    "future:vote-mean")


@lru_cache(maxsize=None)
def _context(group: int):
    beams = load_beams()
    beam = beams["beams"][group]
    receipt = load_group(group)
    if (beam["heldout_target_opened"] or beam["target_used_for_ranking"]
            or receipt["confirmation_target_opened"]
            or receipt["target_used_for_extension"]):
        raise AssertionError("terminal feature source was not target sealed")
    seed, _ = oracle_crop_fast(beam["center"], beam["seed_radius"])
    return beam, receipt, seed, load_fourth_block_runtime()


def _parent_worker(task):
    group, parent_index = map(int, task)
    beam, receipt, seed, runtime = _context(group)
    parent = receipt["results"][parent_index]
    if parent["status"] != "continued":
        return {
            "group": group, "parent_index": parent_index,
            "lineage_id": parent["lineage_id"], "status": "rejected",
            "rows": (), "target_used": False,
        }
    prior = tuple((tuple(map(float, point)), str(color))
                  for point, color in parent["prior_actions"])
    # The replayed state is the exact colored union of the public seed and
    # the nine frozen actions.  Reconstructing this union directly avoids a
    # factorial permutation replay while preserving the identical frontier.
    source = SimpleNamespace(
        group=tuple(map(float, beam["center"])),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed.positions) +
                       tuple(point for point, _color in prior),
        seed_species=tuple(map(str, seed.species)) +
                     tuple(color for _point, color in prior))
    states, counts = _channel_tree(
        source, runtime, float(beam["next_radius"]),
        action_budget=8, baseline_slots=3)
    by_actions = {action_key(state.actions): state for state in states}
    rows = []
    for successor in parent["successors"]:
        actions = action_key(tuple((tuple(map(float, point)), str(color))
                                   for point, color in successor["actions"]))
        state = by_actions.get(actions)
        if state is None:
            raise AssertionError("frozen successor missing from rebuilt tree")
        votes = tuple(map(int, state.proposals.votes.values()))
        future = (
            float(len(votes)), float(sum(votes)),
            float(max(votes, default=0)),
            float(sum(votes) / len(votes) if votes else 0.))
        features = tuple(map(float, branch_features(state))) + future
        rows.append({
            "stable_index": int(successor["stable_index"]),
            "actions": successor["all_actions"],
            "features": features,
        })
    if (len(rows) != len(parent["successors"])
            or len(by_actions) != len(rows)
            or any(len(row["features"]) != len(FEATURE_NAMES)
                   for row in rows)):
        raise AssertionError("terminal feature candidate accounting drift")
    return {
        "group": group, "parent_index": parent_index,
        "lineage_id": parent["lineage_id"], "status": "continued",
        "candidate_counts_by_depth": counts, "rows": tuple(rows),
        "target_used": False,
    }


def evaluate(workers=4):
    if workers < 1:
        raise ValueError("workers must be positive")
    beams = load_beams()
    marking = load_default_artifact()
    tasks = tuple((group, parent_index) for group in GROUPS
                  for parent_index in range(64))
    if workers == 1:
        parents = tuple(map(_parent_worker, tasks))
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parents = tuple(pool.map(_parent_worker, tasks))
    parents = tuple(sorted(parents,
                           key=lambda row: (row["group"], row["parent_index"])))
    if (tuple((row["group"], row["parent_index"]) for row in parents) != tasks
            or any(row["target_used"] for row in parents)):
        raise AssertionError("terminal feature task ordering drift")
    group_rows = []
    for group in GROUPS:
        receipt = load_group(group)
        selected = tuple(row for row in parents if row["group"] == group)
        flat = tuple(candidate for parent in selected
                     for candidate in parent["rows"])
        if (len(selected) != 64 or len(flat) != receipt["successors"]
                or sum(parent["status"] == "continued"
                       for parent in selected) != receipt["lineages_continued"]):
            raise AssertionError("terminal feature group accounting drift")
        group_rows.append({
            "group": group,
            "source_marked_result_digest": receipt["result_digest"],
            "parents": selected,
            "candidates": len(flat),
            "candidate_digest": hashlib.sha256(repr(tuple(
                (parent["lineage_id"], row["stable_index"], row["actions"])
                for parent in selected for row in parent["rows"]
            )).encode()).hexdigest(),
        })
    body = {
        "schema_version": 1,
        "source_beam_result_digest": beams["result_digest"],
        "marking_model_digest": marking.model_digest,
        "groups": GROUPS,
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "group_rows": tuple(group_rows),
        "total_candidates": sum(row["candidates"] for row in group_rows),
        "targets_opened": False,
        "target_or_correctness_used": False,
        "absolute_frame_or_raw_ids_in_features": False,
        "candidate_geometry_changed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    marking = load_default_artifact()
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or tuple(body["groups"]) != GROUPS
            or tuple(body["feature_names"]) != FEATURE_NAMES
            or body["feature_count"] != len(FEATURE_NAMES)
            or body["marking_model_digest"] != marking.model_digest
            or body["targets_opened"] or body["target_or_correctness_used"]
            or body["absolute_frame_or_raw_ids_in_features"]
            or body["candidate_geometry_changed"]):
        raise AssertionError("fourth-block terminal feature receipt drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("terminal feature result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("terminal feature fixture byte drift")
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
        "group_candidates": tuple(group["candidates"]
                                  for group in row["group_rows"]),
        "total_candidates": row["total_candidates"],
        "feature_count": row["feature_count"],
        "targets_opened": row["targets_opened"],
        "result_digest": row["result_digest"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
