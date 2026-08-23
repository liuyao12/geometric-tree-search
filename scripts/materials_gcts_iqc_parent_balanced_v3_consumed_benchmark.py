#!/usr/bin/env python3
"""Consumed-nucleus audit of the fully serialized v3 parent hierarchy."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_fresh_parent_balanced_execution_v3 import \
    freeze_fresh_parent_balanced_execution_v3
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import (
    FIRST_RADIUS, FOURTH_RADIUS, SECOND_RADIUS, SEED_RADIUS, THIRD_RADIUS,
    canonical_json)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_parent_balanced_v3_consumed_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "711e80f19030c4afd828dd6c8b78eed752830f664cb7cf623a51ef8b58f010ed"
EXPECTED_RESULT_DIGEST = \
    "3016a6327d88ed43b94005258b9af21e482e1c8b74fc77f1e3028864edc7178f"
CONSUMED_CENTER = (-70., 10., 70.)
WORKERS = 4
POSITION_TOLERANCE = 1e-5
RUNTIME_LIMIT_SECONDS = 600.


def evaluate():
    seed, _seed_lifts = oracle_crop_fast(CONSUMED_CENTER, SEED_RADIUS)
    execution = freeze_fresh_parent_balanced_execution_v3(
        center=CONSUMED_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, third_radius=THIRD_RADIUS,
        fourth_radius=FOURTH_RADIUS, workers=WORKERS)
    receipt = asdict(execution)
    frozen_bytes = canonical_json(receipt)
    frozen_digest = hashlib.sha256(frozen_bytes).hexdigest()
    # The serialized-receipt digest includes diagnostic wall timings, whereas
    # the executor's deterministic digest intentionally excludes them.  They
    # are two different audit objects and must not be compared for equality.
    if (execution.target_used or len(frozen_digest) != 64 or
            len(execution.deterministic_receipt_digest) != 64):
        raise AssertionError("v3 consumed receipt failed to freeze")

    # This development target has been consumed by earlier audits. It is
    # constructed only after the v3 receipt and every raw parent are frozen.
    target, _target_lifts = oracle_crop_fast(CONSUMED_CENTER, FOURTH_RADIUS)
    truth = colored_position_index(
        target.positions, target.species, tolerance=POSITION_TOLERANCE)
    raw_labels = tuple(colored_action_labels(
        lineage.all_actions, truth, tolerance=POSITION_TOLERANCE)
        for lineage in execution.raw_nine_action_lineages)
    selected_labels = tuple(
        raw_labels[index]
        for index in execution.selected_nine_action_lineage_indices)
    final_labels = tuple(colored_action_labels(
        candidate.all_actions, truth, tolerance=POSITION_TOLERANCE)
        for candidate in execution.candidates)
    terminal_labels = tuple(colored_action_labels(
        candidate.actions, truth, tolerance=POSITION_TOLERANCE)
        for candidate in execution.candidates)
    raw_exact = tuple(index for index, labels in enumerate(raw_labels)
                      if all(labels))
    selected_exact = tuple(index for index, labels in enumerate(
        selected_labels) if all(labels))
    final_exact = tuple(index for index, labels in enumerate(final_labels)
                        if all(labels))
    raw_exact_parents = {execution.raw_nine_action_lineages[index].parent_id
                         for index in raw_exact}
    selected_exact_parents = {
        execution.raw_nine_action_lineages[
            execution.selected_nine_action_lineage_indices[index]].parent_id
        for index in selected_exact}
    total_seconds = sum(seconds for _name, seconds in execution.stage_seconds)
    receipt_unchanged = canonical_json(asdict(execution)) == frozen_bytes
    body = {
        "schema_version": 1,
        "center": CONSUMED_CENTER,
        "radii": (SEED_RADIUS, FIRST_RADIUS, SECOND_RADIUS, THIRD_RADIUS,
                  FOURTH_RADIUS),
        "seed_atoms": len(seed.positions),
        "target_atoms": len(target.positions),
        "workers": WORKERS,
        "position_tolerance": POSITION_TOLERANCE,
        "runtime_limit_seconds": RUNTIME_LIMIT_SECONDS,
        "receipt": receipt,
        "serialized_receipt_digest": frozen_digest,
        "deterministic_receipt_digest":
            execution.deterministic_receipt_digest,
        "receipt_serialized_before_consumed_target": True,
        "receipt_unchanged_after_scoring": receipt_unchanged,
        "raw_nine_action_lineages": len(raw_labels),
        "raw_nine_action_lineage_digest":
            execution.raw_nine_action_lineage_digest,
        "raw_exact_nine_action_lineages": len(raw_exact),
        "raw_exact_parent_count": len(raw_exact_parents),
        "selected_nine_action_lineages": len(selected_labels),
        "selected_exact_nine_action_lineages": len(selected_exact),
        "selected_exact_parent_count": len(selected_exact_parents),
        "all_raw_exact_parents_retained":
            selected_exact_parents == raw_exact_parents,
        "fourth_candidates": len(final_labels),
        "exact_fourth_candidates": len(final_exact),
        "exact_terminal_blocks": sum(all(labels)
                                     for labels in terminal_labels),
        "best_complete_correct_actions": max(
            map(sum, final_labels), default=0),
        "stage_seconds": execution.stage_seconds,
        "total_execution_seconds": total_seconds,
        "runtime_gate_passed": total_seconds <= RUNTIME_LIMIT_SECONDS,
        "full_raw_parent_antichain_serialized":
            len(execution.raw_nine_action_lineages) == len(raw_labels),
        "target_used_for_generation_fit_or_ranking": False,
        "consumed_development_target_used_only_for_posthoc_scoring": True,
        "fresh_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            not body["receipt_serialized_before_consumed_target"] or
            not body["receipt_unchanged_after_scoring"] or
            not body["full_raw_parent_antichain_serialized"] or
            body["target_used_for_generation_fit_or_ranking"] or
            not body["consumed_development_target_used_only_for_posthoc_scoring"] or
            body["fresh_confirmation_claimed"] or
            body["autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("v3 consumed benchmark drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("v3 consumed result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("v3 consumed fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate())
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    keys = ("raw_nine_action_lineages", "raw_exact_nine_action_lineages",
            "raw_exact_parent_count", "selected_nine_action_lineages",
            "selected_exact_nine_action_lineages",
            "selected_exact_parent_count", "all_raw_exact_parents_retained",
            "fourth_candidates", "exact_fourth_candidates",
            "exact_terminal_blocks", "best_complete_correct_actions",
            "stage_seconds", "total_execution_seconds",
            "runtime_gate_passed", "result_digest")
    print(json.dumps(row if args.json else {key: row[key] for key in keys},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
