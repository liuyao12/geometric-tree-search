#!/usr/bin/env python3
"""Consumed-target supply audit for the bounded hybrid prefix schedule."""

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
    "fixtures/iqc_hybrid_prefix_third_supply_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "f741604a2c6c9f6462ceb188a71453600d7a77a6d8c4db8e94f8afae8ae9a177"
EXPECTED_RESULT_DIGEST = \
    "87c6d76fefd692e344181d588852d06b61598f96de019184a5cacd4b9ec0d36a"


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
        raw=SimpleNamespace(second_branches=branches), workers=workers,
        maximum_fallbacks=4, require_universal_avoidance=True,
        base_tail_when_unsaturated=True)
    elapsed = time.perf_counter() - started
    lineage_digest = hashlib.sha256(repr(tuple(
        row.all_actions for row in lineages)).encode()).hexdigest()
    joint_pairs = {(int(row[0]), int(row[1]))
                   for row in marginal["joint_rows"]}
    fallback_pairs = {(int(row[0]), int(row[1]))
                      for row in marginal["diverse_fallback_rows"]}
    # Freeze every target-free lineage identity before reopening this already-
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
    exact_prefixes = sorted({(
        int(lineages[index].parent_id),
        int(lineages[index].child_stable_index)) for index in exact})
    fallback_prefixes = sorted(fallback_pairs)
    body = {
        "schema_version": 1,
        "case": name,
        "center": center,
        "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
        "workers": workers,
        "joint_prefixes": len(joint_pairs),
        "diverse_fallback_prefixes": len(fallback_pairs),
        "selected_prefixes": len(marginal["selected_rows"]),
        "fallback_prefixes": fallback_prefixes,
        "exact_prefixes": exact_prefixes,
        "complete_queue_digest": scheduled["complete_queue_digest"],
        "hybrid_prefix_digest": marginal["selected_prefix_digest"],
        "raw_nine_action_lineages": len(lineages),
        "raw_lineage_digest": lineage_digest,
        "exact_nine_action_lineages": len(exact),
        "joint_exact_lineages": len(joint_exact),
        "fallback_exact_lineages": len(fallback_exact),
        "best_correct_actions": max(map(sum, labels), default=0),
        "third_frontier_seconds": elapsed,
        "maximum_fallbacks": marginal["maximum_fallbacks"],
        "universal_avoidance_required":
            marginal["universal_avoidance_required"],
        "base_tail_when_unsaturated":
            marginal["base_tail_when_unsaturated"],
        "candidate_selection_target_used": False,
        "target_opened_after_lineage_receipt_freeze": True,
        "consumed_development_audit_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode()).hexdigest()}


def validate_result(row, *, pin=True):
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
            row["selected_prefixes"] != 12 or
            row["joint_prefixes"] != 8 or
            row["diverse_fallback_prefixes"] != 4 or
            row["maximum_fallbacks"] != 4 or
            not row["universal_avoidance_required"] or
            not row["base_tail_when_unsaturated"] or
            row["exact_nine_action_lineages"] < 1 or
            row["joint_exact_lineages"] < 1 or
            row["fallback_exact_lineages"] < 1 or
            row["best_correct_actions"] != 9):
        raise AssertionError("bounded hybrid third-supply drift")
    if pin and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("bounded hybrid result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("bounded hybrid fixture drift")
    return validate_result(json.loads(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    row = validate_result(evaluate(), pin=False) if args.live \
        else load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
