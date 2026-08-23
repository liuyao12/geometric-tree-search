#!/usr/bin/env python3
"""Target-blind fourth-block confirmation at development-frozen reach nine.

The consumed group-0 reach diagnostic found that the unchanged frozen IQC
geometry contains an exact fourth block only when each action step can inspect
at least nine channel-diverse proposals.  This module freezes that one-unit
search-width change and applies it only to other, still-sealed nuclei.  It has
no target, scorer, truth, or correctness-label API.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import canonical_json
from materials_gcts_iqc_fourth_block_extension import evaluate_group
from materials_gcts_iqc_three_block_channel_execution import _channel_tree


ROOT = Path(__file__).resolve().parent
ACTION_BUDGET = 9
BASELINE_SLOTS = 3
DEVELOPMENT_GROUP = 0
EXPECTED_FIXTURE_SHA256 = {
    1: "7608c3a80b8bdec776049b42a83a697c6bae11164b0563c7ccd73104e34f0a44",
}
EXPECTED_RESULT_DIGEST = {
    1: "1e0a4786387700160a21ac98d958f45625b19b8e515df5efb134881784401e78",
}


def _reach9_tree(source, runtime, radius, telemetry=None,
                 use_geometry_cache=True):
    return _channel_tree(
        source, runtime, radius, telemetry=telemetry,
        use_geometry_cache=use_geometry_cache,
        action_budget=ACTION_BUDGET, baseline_slots=BASELINE_SLOTS)


def fixture_path(group):
    return ROOT / "fixtures" / \
        f"iqc_fourth_block_reach9_group{int(group)}_v1.json.gz"


def evaluate_group_reach9(group: int, workers=4):
    if group == DEVELOPMENT_GROUP:
        raise ValueError("consumed development nucleus is not confirmation")
    source = evaluate_group(
        group, workers, task_overrides={"tree": _reach9_tree})
    body = dict(source)
    body.pop("result_digest")
    body.update({
        "schema_version": 2,
        "action_budget": ACTION_BUDGET,
        "baseline_slots": BASELINE_SLOTS,
        "development_group": DEVELOPMENT_GROUP,
        "development_target_reused": False,
        "confirmation_target_opened": False,
        "target_used_for_budget_selection": False,
        "target_used_for_extension": False,
        "winner_selected": False,
    })
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    group = int(body["group"])
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 2
            or group not in range(1, 5)
            or body["action_budget"] != ACTION_BUDGET
            or body["baseline_slots"] != BASELINE_SLOTS
            or body["development_group"] != DEVELOPMENT_GROUP
            or body["development_target_reused"]
            or body["confirmation_target_opened"]
            or body["target_used_for_budget_selection"]
            or body["target_used_for_extension"]
            or body["winner_selected"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("reach-nine fourth-block confirmation drift")
    if EXPECTED_RESULT_DIGEST.get(group) and \
            digest != EXPECTED_RESULT_DIGEST[group]:
        raise AssertionError("reach-nine result digest drift")
    return row


def load_group(group, path=None):
    path = fixture_path(group) if path is None else Path(path)
    raw = path.read_bytes()
    if EXPECTED_FIXTURE_SHA256.get(group) and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256[group]:
        raise AssertionError("reach-nine fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate_group_reach9(
            args.group, args.workers))
        path = fixture_path(args.group)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_group(args.group)
    print(json.dumps({key: row[key] for key in (
        "group", "action_budget", "lineages_extended",
        "lineages_replay_rejected", "lineages_continued",
        "lineages_with_successors", "successors",
        "naive_geometry_expansions", "unique_geometry_expansions",
        "saved_geometry_expansions", "confirmation_target_opened",
        "target_used_for_extension", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
