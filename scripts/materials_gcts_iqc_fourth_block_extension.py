#!/usr/bin/env python3
"""Execute one sealed IQC fourth-block beam shard without target labels."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import canonical_json
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_iqc_three_block_portfolio_execution import _prepare_pool
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_lineage_continuation import (
    FrozenLineageContinuation, FrozenLineageContinuationFailure,
    lineage_continuation_attempt_worker)


ROOT = Path(__file__).resolve().parent
EXPECTED_FIXTURE_SHA256 = {
    0: "29248866eeb44261d6005102f8ec2cb66b9d79f1de725923d964ef4a7fa9c811",
}
EXPECTED_RESULT_DIGEST = {
    0: "cbf7e8ff353b035f65dfacb9be5e644d8eed52339e3c4017b3ef1019ff7f4ad9",
}


def fixture_path(group):
    return ROOT / "fixtures" / \
        f"iqc_fourth_block_extension_group{int(group)}_v1.json.gz"


def evaluate_group(group: int, workers=4):
    if group not in range(5) or workers < 1:
        raise ValueError("invalid fourth-block shard request")
    source = load_beams()
    beam = source["beams"][group]
    if beam["heldout_group"] != group or beam["heldout_target_opened"] or \
            beam["target_used_for_ranking"]:
        raise AssertionError("beam target-order contract drift")
    seed, _ = oracle_crop_fast(beam["center"], beam["seed_radius"])
    tasks = tuple({
        "lineage_id": (group, row["stable_index"]),
        "center": tuple(beam["center"]),
        "seed_positions": tuple(seed.positions),
        "seed_species": tuple(seed.species),
        "prior_actions": tuple((tuple(point), color)
                               for point, color in row["actions"]),
        "replay_radii": tuple(beam["replay_radii"]),
        "next_radius": float(beam["next_radius"]),
    } for row in beam["candidates"])
    task_digest = hashlib.sha256(repr(tuple(
        (task["lineage_id"], task["prior_actions"], task["replay_radii"],
         task["next_radius"]) for task in tasks)).encode()).hexdigest()
    if workers == 1:
        results = tuple(map(lineage_continuation_attempt_worker, tasks))
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(
                lineage_continuation_attempt_worker, tasks))
    if (len(results) != len(tasks) or any(row.target_used for row in results)
            or tuple(row.lineage_id for row in results) !=
            tuple(task["lineage_id"] for task in tasks)):
        raise AssertionError("fourth-block shard execution drift")
    continued = tuple(row for row in results
                      if isinstance(row, FrozenLineageContinuation))
    rejected = tuple(row for row in results
                     if isinstance(row, FrozenLineageContinuationFailure))
    if len(continued) + len(rejected) != len(results):
        raise AssertionError("unknown fourth-block attempt result")
    result_rows = tuple(({"status": "continued", **asdict(row)}
                         if isinstance(row, FrozenLineageContinuation) else
                         {"status": "rejected", **asdict(row)})
                        for row in results)
    body = {
        "schema_version": 1,
        "group": group,
        "nucleus": beam["nucleus"],
        "center": beam["center"],
        "seed_radius": beam["seed_radius"],
        "replay_radii": beam["replay_radii"],
        "next_radius": beam["next_radius"],
        "source_beam_result_digest": source["result_digest"],
        "source_retained_digest": beam["retained_digest"],
        "task_digest": task_digest,
        "lineages_extended": len(results),
        "lineages_replay_rejected": len(rejected),
        "lineages_continued": len(continued),
        "lineages_with_successors": sum(bool(row.successors)
                                        for row in continued),
        "lineages_at_fixed_point": sum(not row.successors
                                       for row in continued),
        "successors": sum(len(row.successors) for row in continued),
        "naive_geometry_expansions": sum(
            row.naive_geometry_expansions for row in continued),
        "unique_geometry_expansions": sum(
            row.unique_geometry_expansions for row in continued),
        "saved_geometry_expansions": sum(
            row.saved_geometry_expansions for row in continued),
        "geometry_cache_hits": sum(row.geometry_cache_hits
                                   for row in continued),
        "results": result_rows,
        "heldout_target_opened": False,
        "target_used_for_extension": False,
        "correctness_labels_present": False,
        "candidate_geometry_changed": False,
        "winner_selected": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    group = int(body["group"])
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1 or group not in range(5)
            or body["lineages_extended"] != 64
            or body["heldout_target_opened"]
            or body["target_used_for_extension"]
            or body["correctness_labels_present"]
            or body["candidate_geometry_changed"]
            or body["winner_selected"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("fourth-block extension shard drift")
    if EXPECTED_RESULT_DIGEST.get(group) and \
            digest != EXPECTED_RESULT_DIGEST[group]:
        raise AssertionError("fourth-block shard result digest drift")
    return row


def load_group(group, path=None):
    path = fixture_path(group) if path is None else Path(path)
    raw = path.read_bytes()
    if EXPECTED_FIXTURE_SHA256.get(group) and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256[group]:
        raise AssertionError("fourth-block shard fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate_group(args.group, args.workers))
        path = fixture_path(args.group)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_group(args.group)
    print(json.dumps({key: row[key] for key in (
        "group", "lineages_extended", "lineages_replay_rejected",
        "lineages_continued", "lineages_with_successors",
        "lineages_at_fixed_point", "successors",
        "naive_geometry_expansions", "unique_geometry_expansions",
        "saved_geometry_expansions", "heldout_target_opened",
        "target_used_for_extension", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
