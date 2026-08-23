#!/usr/bin/env python3
"""Sealed IQC fourth-block extension with the frozen development marking.

The marking was fit only on consumed nuclei 0 and 1.  This worker applies it
to an untouched beam at the original reach-eight action budget.  It loads no
target, truth, scorer, or correctness label and changes no candidate geometry.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import canonical_json
from materials_gcts_iqc_fourth_block_action_marking import (
    DEVELOPMENT_GROUPS, load_default_artifact,
    load_fourth_block_runtime)
from materials_gcts_iqc_fourth_block_extension import evaluate_group


ROOT = Path(__file__).resolve().parent
ACTION_BUDGET = 8
EXPECTED_FIXTURE_SHA256 = {
    2: "27d7d9cf5f0a63ee8d8a742dd2dfc06b606487f720475830b61b675242794c8f",
    3: "f2a8ee8a1daddf4e36a271f167418ae0e835d1629e9e25fe5ae6f44f118ea119",
    4: "c713bc4e311707fb83a1c898cae8a8436e726d17068635b44af2584e1996e529",
}
EXPECTED_RESULT_DIGEST = {
    2: "c83f64066c32a9bd8963d701e4f99e0b96f0ca65e6cdf1656f66c951b6aa3732",
    3: "9fa4dc292477ecb98cc9072debcde9ea00394caf1ae9b24564536ad9a20497a1",
    4: "69021b44a1ae38168c0a3b5a0e5ae81893d402d4519b50107395d14b4ef80998",
}


def fixture_path(group):
    return ROOT / "fixtures" / \
        f"iqc_fourth_block_marked_group{int(group)}_v1.json.gz"


def evaluate_group_marked(group: int, workers=4):
    if group in DEVELOPMENT_GROUPS:
        raise ValueError("development nuclei are not marking confirmation")
    marking = load_default_artifact()
    source = evaluate_group(
        group, workers,
        task_overrides={"runtime_loader": load_fourth_block_runtime})
    body = dict(source)
    body.pop("result_digest")
    body.update({
        "schema_version": 3,
        "action_budget": ACTION_BUDGET,
        "marking_model_digest": marking.model_digest,
        "marking_development_groups": marking.development_groups,
        "development_targets_used_for_marking_fit": True,
        "development_targets_reused": False,
        "confirmation_target_opened": False,
        "confirmation_target_used_for_marking_fit": False,
        "target_used_for_extension": False,
        "candidate_geometry_changed": False,
        "winner_selected": False,
    })
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    group = int(body["group"])
    marking = load_default_artifact()
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 3
            or group in DEVELOPMENT_GROUPS or group not in range(5)
            or body["action_budget"] != ACTION_BUDGET
            or body["marking_model_digest"] != marking.model_digest
            or tuple(body["marking_development_groups"]) !=
            DEVELOPMENT_GROUPS
            or not body["development_targets_used_for_marking_fit"]
            or body["development_targets_reused"]
            or body["confirmation_target_opened"]
            or body["confirmation_target_used_for_marking_fit"]
            or body["target_used_for_extension"]
            or body["candidate_geometry_changed"]
            or body["winner_selected"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("marked fourth-block extension drift")
    if EXPECTED_RESULT_DIGEST.get(group) and \
            digest != EXPECTED_RESULT_DIGEST[group]:
        raise AssertionError("marked fourth-block result digest drift")
    return row


def load_group(group, path=None):
    path = fixture_path(group) if path is None else Path(path)
    raw = path.read_bytes()
    if EXPECTED_FIXTURE_SHA256.get(group) and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256[group]:
        raise AssertionError("marked fourth-block fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate_group_marked(
            args.group, args.workers))
        path = fixture_path(args.group)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_group(args.group)
    print(json.dumps({key: row[key] for key in (
        "group", "action_budget", "marking_model_digest",
        "lineages_extended", "lineages_replay_rejected",
        "lineages_continued", "lineages_with_successors", "successors",
        "naive_geometry_expansions", "unique_geometry_expansions",
        "saved_geometry_expansions", "confirmation_target_opened",
        "target_used_for_extension", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
