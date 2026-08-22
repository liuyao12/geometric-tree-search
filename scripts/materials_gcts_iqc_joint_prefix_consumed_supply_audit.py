#!/usr/bin/env python3
"""Consumed-target audit of the bounded joint IQC prefix schedule.

Selections and queue digests are frozen before each already-consumed target is
reopened.  The target is used only to identify which selected prefixes are
exact and to verify that at least one of their third-frontier subtrees contains
an exact nine-action lineage.  This is development evidence, never a fresh
confirmation or winner claim.
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

from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_iqc_three_block_marking_library_execution import (
    select_marking_library_children)
from materials_gcts_iqc_three_block_portfolio_execution import (
    _prepare_pool, _third_parent_worker)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_joint_prefix_consumed_supply_audit_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "ca0711bf1dc571168de0e29fcbceb069beff5c844c457882a535f5b2e4716e38")
EXPECTED_RESULT_DIGEST = (
    "3548377de5a2fd697f9bfd44cc465fc21529205b7742d0aece588abf31e819a8")
POSITION_TOLERANCE = 1e-5


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _correct(action, by_species):
    point, color = action
    return min(math.dist(point, candidate)
               for candidate in by_species[color]) <= POSITION_TOLERANCE


def evaluate(workers=4):
    schedule, schedule_artifact = load_default_schedule()
    case_rows = []
    total_groups = supplied_groups = third_supplied_groups = 0
    total_selected = total_eager = total_complete = 0
    for name, relative, center in CASES:
        source_raw = (ROOT / relative).read_bytes()
        receipt = json.loads(gzip.decompress(source_raw))["receipt"]
        branches = tuple(SimpleNamespace(**row)
                         for row in receipt["second_branches"])
        seed, _ = oracle_crop_fast(center, 9.)

        scheduled = schedule_prefixes(
            schedule=schedule, seed_positions=seed.positions,
            seed_species=seed.species, branches=branches)
        selected = {(row[0], row[1]) for row
                    in scheduled["selected_rows"]}
        eager = select_marking_library_children(
            branches=branches, seed_positions=seed.positions,
            seed_species=seed.species)
        selected_count = len(selected)
        eager_count = sum(len(children) for _parent, children
                          in eager["union_rows"])
        complete_count = sum(len(branch.second_actions)
                             for branch in branches)
        total_selected += selected_count
        total_eager += eager_count
        total_complete += complete_count

        # All candidate identities and schedule digests above are frozen before
        # this already-consumed target is opened.
        target, _ = oracle_crop_fast(center, receipt["radii"][2])
        by_species = {color: tuple(point for point, species in zip(
            target.positions, target.species) if species == color)
                      for color in set(target.species)}
        groups = []
        payloads = []
        payload_group = []
        for branch in branches:
            if not all(_correct(action, by_species)
                       for action in branch.first_actions):
                continue
            exact = tuple(child for child, actions in enumerate(
                branch.second_actions) if all(
                    _correct(action, by_species) for action in actions))
            if not exact:
                continue
            total_groups += 1
            selected_exact = tuple(child for child in exact
                                   if (branch.first_rank, child) in selected)
            supplied_groups += bool(selected_exact)
            group_index = len(groups)
            groups.append({
                "parent": branch.first_rank,
                "exact_children": exact,
                "selected_exact_children": selected_exact,
                "third_rows": [],
            })
            for child in selected_exact:
                payloads.append((
                    center, seed.positions, seed.species,
                    branch.first_actions,
                    ((child, branch.second_actions[child]),),
                    branch.first_rank, *receipt["radii"]))
                payload_group.append((group_index, child))
        if workers == 1:
            results = tuple(_third_parent_worker(payload)
                            for payload in payloads)
        else:
            _prepare_pool()
            with ProcessPoolExecutor(max_workers=workers) as pool:
                results = tuple(pool.map(_third_parent_worker, payloads))
        for (group_index, child), result in zip(payload_group, results):
            counts, lineages = result[0]
            scores = tuple(sum(_correct(action, by_species)
                               for action in lineage.all_actions)
                           for lineage in lineages)
            groups[group_index]["third_rows"].append({
                "child": child,
                "candidate_counts": counts,
                "lineages": len(lineages),
                "best_correct_actions": max(scores, default=0),
                "exact_nine_action_lineages": sum(score == 9
                                                   for score in scores),
            })
        for group in groups:
            has_third = any(row["exact_nine_action_lineages"] > 0
                            for row in group["third_rows"])
            group["exact_third_supply"] = has_third
            third_supplied_groups += has_third
        case_rows.append({
            "name": name,
            "center": center,
            "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
            "complete_prefixes": complete_count,
            "eager_marking_library_prefixes": eager_count,
            "bounded_joint_prefixes": selected_count,
            "saved_vs_eager": eager_count - selected_count,
            "complete_queue_digest_frozen_before_target":
                scheduled["complete_queue_digest"],
            "selected_prefix_digest_frozen_before_target":
                scheduled["selected_prefix_digest"],
            "exact_groups": groups,
        })
    body = {
        "schema_version": 1,
        "schedule_artifact_digest": schedule.artifact_digest,
        "schedule": schedule_artifact["schedule"],
        "cases": case_rows,
        "exact_child_groups": total_groups,
        "selected_exact_child_groups": supplied_groups,
        "exact_third_supplied_groups": third_supplied_groups,
        "selected_prefixes_across_cases": total_selected,
        "eager_prefixes_across_cases": total_eager,
        "complete_prefixes_across_cases": total_complete,
        "prefix_reduction_vs_eager": total_eager - total_selected,
        "all_consumed_groups_supply_exact_nine_action_lineage": bool(
            total_groups and total_groups == supplied_groups ==
            third_supplied_groups),
        "candidate_selection_target_used": False,
        "consumed_targets_opened_after_schedule_freeze": True,
        "consumed_target_development_audit_only": True,
        "fresh_confirmation_claimed": False,
        "winner_or_autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            body["candidate_selection_target_used"] or
            not body["consumed_targets_opened_after_schedule_freeze"] or
            not body["consumed_target_development_audit_only"] or
            body["fresh_confirmation_claimed"] or
            body["winner_or_autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("joint prefix consumed audit drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("joint prefix consumed result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("joint prefix consumed fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate(args.workers))
        text = json.dumps(row, indent=2, sort_keys=True) + "\n"
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({key: row[key] for key in (
        "all_consumed_groups_supply_exact_nine_action_lineage",
        "exact_child_groups", "selected_exact_child_groups",
        "exact_third_supplied_groups", "selected_prefixes_across_cases",
        "eager_prefixes_across_cases", "prefix_reduction_vs_eager",
        "result_digest")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
