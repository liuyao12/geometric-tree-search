#!/usr/bin/env python3
"""Complete the bounded IQC nine-action lineage receipts target-blind.

The four consumed development receipts predate the bounded joint prefix
schedule.  They already contain many, but not all, scheduled parent/child
prefixes.  This module expands only the missing frozen prefixes, using the
same exact geometry memoization as the one-shot confirmation, and serializes
their complete third-block lineages.  No oracle target or correctness label is
an input to this completion step.

The resulting fixture is deliberately geometry-only.  A later dataset builder
may join it to the original receipts and only then open consumed targets for
labels.  This separation makes the target-order boundary mechanical rather
than narrative.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_iqc_three_block_lazy_joint_execution import (
    _lazy_third_parent_worker)
from materials_gcts_iqc_three_block_portfolio_execution import _prepare_pool
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_bounded_lineage_completion_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "f69c38b7b868fd1072c5ee7a0df0123329b7c6c60f0a4377205d00b624cc9bcf")
EXPECTED_RESULT_DIGEST = (
    "b1b0a8a59f4cd36af227c39a294217553466b9278ee991c8ca58e3efc5a50b8b")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _load_case(name, relative, center):
    source_raw = (ROOT / relative).read_bytes()
    source = json.loads(gzip.decompress(source_raw))
    receipt = source["receipt"]
    branches = tuple(SimpleNamespace(**row)
                     for row in receipt["second_branches"])
    seed, _ = oracle_crop_fast(center, 9.)
    schedule, schedule_artifact = load_default_schedule()
    scheduled = schedule_prefixes(
        schedule=schedule, seed_positions=seed.positions,
        seed_species=seed.species, branches=branches)
    selected = tuple(sorted((int(row[0]), int(row[1]))
                            for row in scheduled["selected_rows"]))
    existing = {(int(row["parent_id"]),
                 int(row["child_stable_index"]))
                for row in receipt["lineages"]}
    missing = tuple(pair for pair in selected if pair not in existing)
    branch_by_parent = {int(row.first_rank): row for row in branches}
    tasks = []
    task_meta = []
    for parent in sorted({pair[0] for pair in missing}):
        branch = branch_by_parent[parent]
        children = tuple(child for candidate_parent, child in missing
                         if candidate_parent == parent)
        tasks.append((
            tuple(map(float, center)), tuple(seed.positions),
            tuple(seed.species), branch.first_actions,
            tuple((child, branch.second_actions[child])
                  for child in children), parent,
            *tuple(map(float, receipt["radii"]))))
        task_meta.append((parent, children))
    return {
        "name": name,
        "relative": relative,
        "center": tuple(map(float, center)),
        "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
        "source_candidate_digest": receipt["candidate_digest"],
        "radii": tuple(map(float, receipt["radii"])),
        "seed_atoms": len(seed.positions),
        "schedule_artifact_digest": schedule.artifact_digest,
        "complete_queue_digest": scheduled["complete_queue_digest"],
        "selected_prefix_digest": scheduled["selected_prefix_digest"],
        "selected_pairs": selected,
        "existing_pairs": tuple(sorted(set(selected) & existing)),
        "missing_pairs": missing,
        "tasks": tuple(tasks),
        "task_meta": tuple(task_meta),
        "schedule_target_used": bool(schedule.target_used_for_execution or
                                     scheduled["model"].target_used_for_scoring),
        "schedule_payload": schedule_artifact["schedule"],
    }


def evaluate(workers=4):
    if workers < 1:
        raise ValueError("workers must be positive")
    cases = tuple(_load_case(*case) for case in CASES)
    tasks = tuple(task for case in cases for task in case["tasks"])
    if workers == 1:
        results = tuple(_lazy_third_parent_worker(task) for task in tasks)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(_lazy_third_parent_worker, tasks))
    cursor = 0
    output_cases = []
    total_missing = total_lineages = 0
    naive = unique = hits = saved = 0
    for case in cases:
        generated = []
        for parent, children in case["task_meta"]:
            worker_results, telemetry_items = results[cursor]
            cursor += 1
            if len(worker_results) != len(children):
                raise AssertionError("missing-prefix worker lost a child")
            for child, (counts, lineages) in zip(children, worker_results):
                if any(lineage.parent_id != parent or
                       lineage.child_stable_index != child
                       for lineage in lineages):
                    raise AssertionError("completed lineage identity drift")
                generated.append({
                    "parent_id": parent,
                    "child_stable_index": child,
                    "third_candidate_counts": counts,
                    "lineages": tuple(asdict(lineage)
                                      for lineage in lineages),
                })
                total_lineages += len(lineages)
            telemetry = dict(telemetry_items)
            naive += telemetry["naive_geometry_expansions"]
            unique += telemetry["unique_geometry_expansions"]
            saved += telemetry["saved_geometry_expansions"]
            hits += telemetry["geometry_cache_hits"]
        generated = tuple(sorted(generated, key=lambda row: (
            row["parent_id"], row["child_stable_index"])))
        generated_pairs = tuple((row["parent_id"],
                                 row["child_stable_index"])
                                for row in generated)
        if generated_pairs != case["missing_pairs"]:
            raise AssertionError("bounded lineage completion is incomplete")
        target_used = case["schedule_target_used"]
        output_cases.append({
            key: case[key] for key in (
                "name", "relative", "center", "source_fixture_sha256",
                "source_candidate_digest", "radii", "seed_atoms",
                "schedule_artifact_digest", "complete_queue_digest",
                "selected_prefix_digest", "selected_pairs",
                "existing_pairs", "missing_pairs", "schedule_payload")
        } | {
            "generated": generated,
            "generated_lineage_digest": hashlib.sha256(repr(tuple(
                lineage["all_actions"] for row in generated
                for lineage in row["lineages"])).encode()).hexdigest(),
            "target_used": target_used,
        })
        total_missing += len(generated)
    if cursor != len(results):
        raise AssertionError("orphan bounded lineage completion result")
    schedule_digests = {case["schedule_artifact_digest"] for case in cases}
    body = {
        "schema_version": 1,
        "cases": tuple(output_cases),
        "schedule_artifact_digest": next(iter(schedule_digests)),
        "missing_prefixes_completed": total_missing,
        "generated_lineages": total_lineages,
        "naive_geometry_expansions": naive,
        "unique_geometry_expansions": unique,
        "saved_geometry_expansions": saved,
        "geometry_cache_hits": hits,
        "all_selected_prefixes_complete": all(
            len(case["selected_pairs"]) ==
            len(case["existing_pairs"]) + len(case["missing_pairs"])
            for case in output_cases),
        "target_used_for_completion": any(
            case["target_used"] for case in output_cases),
        "correctness_labels_present": False,
        "winner_selected": False,
        "stationary_or_exponential_claimed": False,
    }
    if len(schedule_digests) != 1:
        raise AssertionError("schedule artifact drift across cases")
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            not body["all_selected_prefixes_complete"] or
            body["target_used_for_completion"] or
            body["correctness_labels_present"] or
            body["winner_selected"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("bounded lineage completion drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("bounded lineage completion result digest drift")
    for case in body["cases"]:
        selected = {tuple(row) for row in case["selected_pairs"]}
        existing = {tuple(row) for row in case["existing_pairs"]}
        missing = {tuple(row) for row in case["missing_pairs"]}
        generated = {(row["parent_id"], row["child_stable_index"])
                     for row in case["generated"]}
        if existing & missing or selected != existing | missing or \
                generated != missing or case["target_used"]:
            raise AssertionError("bounded lineage case partition drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("bounded lineage completion fixture drift")
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
    print(json.dumps({key: row[key] for key in (
        "missing_prefixes_completed", "generated_lineages",
        "naive_geometry_expansions", "unique_geometry_expansions",
        "saved_geometry_expansions", "all_selected_prefixes_complete",
        "target_used_for_completion", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
