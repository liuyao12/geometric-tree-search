#!/usr/bin/env python3
"""One-shot fresh full-width confirmation of the two-fallback IQC policy."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_fresh_parent_balanced_execution_v4 import \
    freeze_fresh_parent_balanced_execution_v4
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, EXECUTION_WORKERS, EXPECTED_MANIFEST_DIGEST,
    FIRST_RADIUS, FOURTH_RADIUS, MAXIMUM_FALLBACKS,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard, PARENT_WIDTH,
    POSITION_TOLERANCE, PRIOR_CENTERS, RUNTIME_LIMIT_SECONDS, SECOND_RADIUS,
    SEED_RADIUS, THIRD_RADIUS, canonical_json, validate_preregistration)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_hybrid_confirmation_v4.json.gz"
ATTEMPT_MARKER = ROOT / \
    "fixtures/iqc_hybrid_confirmation_attempt_v4.json"
EXPECTED_FIXTURE_SHA256 = \
    "2dac238f2d581d83f9b79f3e6836ce3f3fe3e7df792952785319b8a9346a2b8d"
EXPECTED_RESULT_DIGEST = \
    "11fc67ff7db4e9e3c8edae83403e14e29c74f0da668633c649c4455cb96bd1d5"


def _serialize_receipt(execution):
    receipt = asdict(execution)
    payload = canonical_json(receipt)
    return receipt, payload, hashlib.sha256(payload).hexdigest()


def _labels(actions, truth):
    return tuple(tuple(colored_action_labels(
        row, truth, tolerance=POSITION_TOLERANCE)) for row in actions)


def _prefix(execution, raw_index):
    row = execution.raw_nine_action_lineages[raw_index]
    return int(row.parent_id), int(row.child_stable_index)


def _execute_and_score_once():
    guard = OneShotOrderGuard()
    guard.protocol_verified()
    guard.seed_opened()
    seed, seed_lifts = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    execution = freeze_fresh_parent_balanced_execution_v4(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, third_radius=THIRD_RADIUS,
        fourth_radius=FOURTH_RADIUS, workers=EXECUTION_WORKERS,
        maximum_fallbacks=MAXIMUM_FALLBACKS)
    receipt, receipt_bytes, receipt_digest = _serialize_receipt(execution)
    stage_total = sum(seconds for _name, seconds in execution.stage_seconds)
    if (execution.target_used or execution.parent_width != PARENT_WIDTH or
            execution.maximum_diverse_fallbacks != MAXIMUM_FALLBACKS or
            execution.selected_prefixes > 8 + MAXIMUM_FALLBACKS or
            execution.selected_prefixes < 8 or
            len(execution.raw_nine_action_lineages) < 1 or
            len(execution.selected_nine_action_lineage_indices) !=
            8 * PARENT_WIDTH or len(execution.candidates) !=
            8 * PARENT_WIDTH * PARENT_WIDTH or any(
                len(row.all_actions) != 12 for row in execution.candidates)):
        raise AssertionError("V4 hybrid fresh receipt invariant drift")
    guard.receipt_frozen(receipt_digest)
    frozen_receipt = bytes(receipt_bytes)

    guard.target_opened()
    target, target_lifts = oracle_crop_fast(
        CONFIRMATION_CENTER, FOURTH_RADIUS)
    truth = colored_position_index(
        target.positions, target.species, tolerance=POSITION_TOLERANCE)
    raw_labels = _labels(
        (row.all_actions for row in execution.raw_nine_action_lineages), truth)
    candidate_labels = _labels(
        (row.all_actions for row in execution.candidates), truth)
    terminal_labels = _labels(
        (row.all_actions[-3:] for row in execution.candidates), truth)
    raw_exact = tuple(index for index, row in enumerate(raw_labels)
                      if all(row))
    selected_indices = tuple(execution.selected_nine_action_lineage_indices)
    selected_set = frozenset(selected_indices)
    selected_exact = tuple(index for index in raw_exact
                           if index in selected_set)
    selected_exact_offsets = tuple(
        offset for offset, raw_index in enumerate(selected_indices)
        if raw_index in set(selected_exact))
    complete_exact = tuple(index for index, row in enumerate(candidate_labels)
                           if all(row))
    terminal_exact = tuple(index for index, row in enumerate(terminal_labels)
                           if all(row))
    raw_exact_prefixes = tuple(sorted({_prefix(execution, index)
                                       for index in raw_exact}))
    selected_exact_prefixes = tuple(sorted({_prefix(execution, index)
                                            for index in selected_exact}))
    complete_exact_prefixes = tuple(sorted({
        _prefix(execution, selected_indices[
            execution.candidates[index].parent_lineage_index])
        for index in complete_exact}))
    best = max((sum(row) for row in candidate_labels), default=0)
    target_sites = tuple((tuple(map(float, point)), str(color))
                         for point, color in zip(
                             target.positions, target.species))
    target_site_digest = hashlib.sha256(
        canonical_json(target_sites)).hexdigest()
    post_receipt, post_bytes, post_digest = _serialize_receipt(execution)
    receipt_unchanged = (post_receipt == receipt and
                         post_bytes == frozen_receipt and
                         post_digest == receipt_digest)
    guard.scored(post_digest)
    nearest_prior = min(math.dist(CONFIRMATION_CENTER, prior)
                        for prior in PRIOR_CENTERS)
    seed_is_target_subset = set(seed_lifts).issubset(target_lifts)
    every_raw_exact_prefix_retained = (
        set(raw_exact_prefixes) <= set(selected_exact_prefixes))
    success = bool(
        raw_exact and selected_exact and complete_exact and
        every_raw_exact_prefix_retained and receipt_unchanged and
        seed_is_target_subset and not execution.target_used and
        guard.target_open_count == 1 and
        nearest_prior > MINIMUM_REQUIRED_DOMAIN_SEPARATION and
        stage_total <= RUNTIME_LIMIT_SECONDS)
    body = {
        "schema_version": 4,
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "center": CONFIRMATION_CENTER,
        "radii": (SEED_RADIUS, FIRST_RADIUS, SECOND_RADIUS, THIRD_RADIUS,
                  FOURTH_RADIUS),
        "workers": EXECUTION_WORKERS,
        "parent_width": PARENT_WIDTH,
        "maximum_action_marginal_fallbacks": MAXIMUM_FALLBACKS,
        "position_tolerance": POSITION_TOLERANCE,
        "seed_atoms": len(seed.positions),
        "target_atoms": len(target.positions),
        "novel_target_atoms": len(set(target_lifts) - set(seed_lifts)),
        "seed_is_target_subset": seed_is_target_subset,
        "nearest_prior_center_separation": nearest_prior,
        "required_domain_separation": MINIMUM_REQUIRED_DOMAIN_SEPARATION,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "receipt_serialized_before_target": True,
        "receipt_unchanged_after_target": receipt_unchanged,
        "raw_nine_action_lineages": len(raw_labels),
        "raw_exact_nine_action_lineages": len(raw_exact),
        "raw_exact_nine_action_indices": raw_exact,
        "raw_exact_prefixes": raw_exact_prefixes,
        "selected_nine_action_lineages": len(selected_set),
        "selected_exact_nine_action_lineages": len(selected_exact),
        "selected_exact_nine_action_indices": selected_exact,
        "selected_exact_offsets": selected_exact_offsets,
        "selected_exact_prefixes": selected_exact_prefixes,
        "every_raw_exact_prefix_represented_after_selection":
            every_raw_exact_prefix_retained,
        "fourth_candidates": len(execution.candidates),
        "exact_complete_twelve_action_paths": len(complete_exact),
        "exact_complete_candidate_indices": complete_exact,
        "exact_complete_prefixes": complete_exact_prefixes,
        "exact_terminal_fourth_blocks": len(terminal_exact),
        "best_complete_correct_actions": best,
        "raw_nine_action_labels": raw_labels,
        "candidate_action_labels": candidate_labels,
        "candidate_terminal_labels": terminal_labels,
        "target_sites": target_sites,
        "target_site_digest": target_site_digest,
        "stage_seconds": execution.stage_seconds,
        "total_execution_seconds": stage_total,
        "runtime_limit_seconds": RUNTIME_LIMIT_SECONDS,
        "runtime_gate_passed": stage_total <= RUNTIME_LIMIT_SECONDS,
        "target_order_audit": guard.audit(),
        "target_used_for_generation_fit_or_ranking": False,
        "fresh_exact_twelve_action_supply_confirmed": success,
        "autonomous_sustained_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "rerun_or_fallback_allowed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    audit = body["target_order_audit"]
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 4 or
            body["protocol_digest"] != EXPECTED_MANIFEST_DIGEST or
            body["position_tolerance"] != POSITION_TOLERANCE or
            body["maximum_action_marginal_fallbacks"] !=
            MAXIMUM_FALLBACKS or body["receipt"]["target_used"] or
            body["receipt"]["maximum_diverse_fallbacks"] !=
            MAXIMUM_FALLBACKS or body["parent_width"] != PARENT_WIDTH or
            body["selected_nine_action_lineages"] != 8 * PARENT_WIDTH or
            body["fourth_candidates"] != 8 * PARENT_WIDTH * PARENT_WIDTH or
            len(body["raw_nine_action_labels"]) !=
            body["raw_nine_action_lineages"] or
            len(body["candidate_action_labels"]) !=
            body["fourth_candidates"] or
            hashlib.sha256(canonical_json(body["target_sites"])).hexdigest()
            != body["target_site_digest"] or
            not body["receipt_serialized_before_target"] or
            not body["receipt_unchanged_after_target"] or
            body["target_used_for_generation_fit_or_ranking"] or
            audit["state"] != "scored" or audit["seed_open_count"] != 1 or
            audit["target_open_count"] != 1 or audit["score_count"] != 1 or
            audit["receipt_digest"] != body["receipt_digest"] or
            body["autonomous_sustained_growth_claimed"] or
            body["stationary_or_exponential_claimed"] or
            body["rerun_or_fallback_allowed"]):
        raise AssertionError("V4 hybrid fresh confirmation drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("V4 hybrid fresh result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("V4 hybrid fresh fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def _attempt_marker_bytes():
    return canonical_json({
        "schema_version": 4,
        "protocol_digest": EXPECTED_MANIFEST_DIGEST,
        "one_shot_invocation": 1,
        "confirmation_center": CONFIRMATION_CENTER,
    }) + b"\n"


def _summary(row):
    return {key: row[key] for key in (
        "fresh_exact_twelve_action_supply_confirmed", "center",
        "seed_atoms", "target_atoms", "raw_nine_action_lineages",
        "raw_exact_nine_action_lineages", "raw_exact_prefixes",
        "selected_nine_action_lineages",
        "selected_exact_nine_action_lineages", "selected_exact_prefixes",
        "fourth_candidates", "exact_complete_twelve_action_paths",
        "exact_complete_prefixes", "exact_terminal_fourth_blocks",
        "best_complete_correct_actions", "total_execution_seconds",
        "runtime_gate_passed", "receipt_digest", "result_digest")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.write:
        validate_preregistration()
        if DEFAULT_FIXTURE.exists() or ATTEMPT_MARKER.exists():
            raise RuntimeError("V4 hybrid fresh one-shot already consumed")
        ATTEMPT_MARKER.parent.mkdir(parents=True, exist_ok=True)
        with ATTEMPT_MARKER.open("xb") as stream:
            stream.write(_attempt_marker_bytes())
        row = validate_result(_execute_and_score_once())
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps(row if args.json else _summary(row),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
