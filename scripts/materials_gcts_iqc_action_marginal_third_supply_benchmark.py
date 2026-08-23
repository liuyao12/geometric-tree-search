#!/usr/bin/env python3
"""Consumed-target third-lineage supply from joint plus diverse prefixes."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_fresh_parent_balanced_execution_v4 import \
    _complete_action_marginal_lineages
from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_action_marginal_third_supply_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "606d31dc4045e99d7397ca963dd053254af335720a2974afce1744bcd6d5b20e"
EXPECTED_RESULT_DIGEST = \
    "ca314c5410bef0790652a82dd4b61f6d3ec6998a56815a8fce7218e765dcd075"


def evaluate(workers=4):
    name, relative, center = CASES[0]
    source_raw = (ROOT / relative).read_bytes()
    receipt = json.loads(gzip.decompress(source_raw))["receipt"]
    branches = tuple(SimpleNamespace(**row)
                     for row in receipt["second_branches"])
    seed, _ = oracle_crop_fast(center, 9.)
    started = time.perf_counter()
    lineages, scheduled, marginal = _complete_action_marginal_lineages(
        center=center, seed_positions=seed.positions,
        seed_species=seed.species, radii=tuple(receipt["radii"][:3]),
        raw=SimpleNamespace(second_branches=branches), workers=workers)
    elapsed = time.perf_counter() - started
    lineage_digest = hashlib.sha256(repr(tuple(
        row.all_actions for row in lineages)).encode()).hexdigest()
    joint_pairs = {(int(row[0]), int(row[1]))
                   for row in marginal["joint_rows"]}
    fallback_pairs = {(int(row[0]), int(row[1]))
                      for row in marginal["diverse_fallback_rows"]}
    # Freeze every target-free lineage identity before opening this already-
    # consumed development target.
    target, _ = oracle_crop_fast(center, receipt["radii"][2])
    truth = colored_position_index(
        target.positions, target.species, tolerance=1e-5)
    labels = tuple(tuple(colored_action_labels(
        row.all_actions, truth, tolerance=1e-5)) for row in lineages)
    exact = tuple(index for index, values in enumerate(labels)
                  if all(values))
    joint_exact = tuple(index for index in exact if (
        lineages[index].parent_id,
        lineages[index].child_stable_index) in joint_pairs)
    fallback_exact = tuple(index for index in exact if (
        lineages[index].parent_id,
        lineages[index].child_stable_index) in fallback_pairs)
    body = {
        "schema_version": 1,
        "case": name,
        "center": center,
        "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
        "workers": workers,
        "joint_prefixes": len(joint_pairs),
        "diverse_fallback_prefixes": len(fallback_pairs),
        "selected_prefixes": len(marginal["selected_rows"]),
        "complete_queue_digest": scheduled["complete_queue_digest"],
        "action_marginal_prefix_digest":
            marginal["selected_prefix_digest"],
        "raw_nine_action_lineages": len(lineages),
        "raw_lineage_digest": lineage_digest,
        "exact_nine_action_lineages": len(exact),
        "joint_exact_lineages": len(joint_exact),
        "fallback_exact_lineages": len(fallback_exact),
        "best_correct_actions": max(map(sum, labels), default=0),
        "third_frontier_seconds": elapsed,
        "candidate_selection_target_used": False,
        "target_opened_after_lineage_receipt_freeze": True,
        "consumed_development_audit_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode()).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    computed = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode()).hexdigest()
    if (computed != digest or row["candidate_selection_target_used"] or
            not row["target_opened_after_lineage_receipt_freeze"] or
            not row["consumed_development_audit_only"] or
            row["fresh_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"] or
            row["selected_prefixes"] != row["joint_prefixes"] +
            row["diverse_fallback_prefixes"] or
            row["exact_nine_action_lineages"] < 1 or
            row["best_correct_actions"] != 9):
        raise AssertionError("action-marginal third-supply drift")
    if digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("action-marginal third-supply result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("action-marginal third-supply fixture drift")
    return validate_result(json.loads(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    row = validate_result(evaluate()) if args.live else load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
