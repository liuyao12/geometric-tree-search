#!/usr/bin/env python3
"""Full-width consumed-target gate for the bounded hybrid IQC executor."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_fresh_parent_balanced_execution_v4 import \
    freeze_fresh_parent_balanced_execution_v4
from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import \
    FOURTH_RADIUS, canonical_json
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_hybrid_fullwidth_consumed_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "827d9a3f78ad6f4b1377dcbdc6003e9eee306bcad5990a6910151bfa588e29fc"
EXPECTED_RESULT_DIGEST = \
    "cf841cb8ec00f9e0246f47d250ca3da7b9488f440ed4a23fdb7c920d6f05ed30"
RUNTIME_LIMIT_SECONDS = 600.


def _labels(actions, truth):
    return tuple(tuple(colored_action_labels(row, truth, tolerance=1e-5))
                 for row in actions)


def evaluate(workers=4, maximum_fallbacks=4):
    name, relative, center = CASES[0]
    source_raw = (ROOT / relative).read_bytes()
    receipt = json.loads(gzip.decompress(source_raw))["receipt"]
    seed, _ = oracle_crop_fast(center, 9.)
    execution = freeze_fresh_parent_balanced_execution_v4(
        center=center, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=receipt["radii"][0],
        second_radius=receipt["radii"][1],
        third_radius=receipt["radii"][2],
        fourth_radius=FOURTH_RADIUS, workers=workers,
        maximum_fallbacks=maximum_fallbacks)
    frozen_payload = canonical_json(asdict(execution))
    frozen_digest = hashlib.sha256(frozen_payload).hexdigest()
    # This target is already consumed development data, but it remains closed
    # until every lineage, selection and fourth candidate is serialized.
    target, _ = oracle_crop_fast(center, FOURTH_RADIUS)
    truth = colored_position_index(
        target.positions, target.species, tolerance=1e-5)
    raw_labels = _labels(
        (row.all_actions for row in execution.raw_nine_action_lineages), truth)
    selected_indices = tuple(execution.selected_nine_action_lineage_indices)
    selected_labels = tuple(raw_labels[index] for index in selected_indices)
    candidate_labels = _labels(
        (row.all_actions for row in execution.candidates), truth)
    terminal_labels = _labels(
        (row.all_actions[-3:] for row in execution.candidates), truth)
    raw_exact = tuple(index for index, row in enumerate(raw_labels)
                      if all(row))
    selected_exact_offsets = tuple(
        offset for offset, row in enumerate(selected_labels) if all(row))
    complete_exact = tuple(index for index, row in enumerate(candidate_labels)
                           if all(row))
    terminal_exact = tuple(index for index, row in enumerate(terminal_labels)
                           if all(row))
    joint_pairs = {(int(row[0]), int(row[1])) for row in
                   execution.action_marginal_prefix_rows
                   if "joint" in row[2]}
    fallback_pairs = {(int(row[0]), int(row[1])) for row in
                      execution.action_marginal_prefix_rows
                      if "joint" not in row[2]}
    raw_exact_pairs = tuple(sorted({(
        int(execution.raw_nine_action_lineages[index].parent_id),
        int(execution.raw_nine_action_lineages[index].child_stable_index))
        for index in raw_exact}))
    selected_exact_pairs = tuple(sorted({(
        int(execution.raw_nine_action_lineages[selected_indices[offset]].parent_id),
        int(execution.raw_nine_action_lineages[selected_indices[offset]].child_stable_index))
        for offset in selected_exact_offsets}))
    stage_total = sum(seconds for _name, seconds in execution.stage_seconds)
    post_digest = hashlib.sha256(canonical_json(asdict(execution))).hexdigest()
    body = {
        "schema_version": 1,
        "case": name,
        "center": center,
        "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
        "workers": workers,
        "seed_atoms": len(seed.positions),
        "target_atoms": len(target.positions),
        "selected_prefixes": execution.selected_prefixes,
        "joint_prefixes": execution.joint_prefixes,
        "fallback_prefixes": execution.diverse_fallback_prefixes,
        "maximum_fallbacks": execution.maximum_diverse_fallbacks,
        "raw_nine_action_lineages": len(raw_labels),
        "raw_exact_nine_action_lineages": len(raw_exact),
        "raw_exact_prefixes": raw_exact_pairs,
        "raw_joint_exact_lineages": sum(
            (execution.raw_nine_action_lineages[index].parent_id,
             execution.raw_nine_action_lineages[index].child_stable_index)
            in joint_pairs for index in raw_exact),
        "raw_fallback_exact_lineages": sum(
            (execution.raw_nine_action_lineages[index].parent_id,
             execution.raw_nine_action_lineages[index].child_stable_index)
            in fallback_pairs for index in raw_exact),
        "selected_nine_action_lineages": len(selected_indices),
        "selected_exact_nine_action_lineages": len(selected_exact_offsets),
        "selected_exact_prefixes": selected_exact_pairs,
        "fourth_candidates": len(candidate_labels),
        "exact_terminal_fourth_blocks": len(terminal_exact),
        "exact_complete_twelve_action_paths": len(complete_exact),
        "best_complete_correct_actions": max(
            map(sum, candidate_labels), default=0),
        "stage_seconds": execution.stage_seconds,
        "total_execution_seconds": stage_total,
        "runtime_limit_seconds": RUNTIME_LIMIT_SECONDS,
        "runtime_gate_passed": stage_total <= RUNTIME_LIMIT_SECONDS,
        "receipt_digest": frozen_digest,
        "receipt_unchanged_after_target": post_digest == frozen_digest,
        "target_opened_after_complete_receipt_freeze": True,
        "candidate_selection_target_used": execution.target_used,
        "consumed_development_audit_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row, *, pin=True):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            row["candidate_selection_target_used"] or
            not row["target_opened_after_complete_receipt_freeze"] or
            not row["receipt_unchanged_after_target"] or
            not row["consumed_development_audit_only"] or
            row["fresh_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"] or
            row["selected_prefixes"] != 12 or
            row["joint_prefixes"] != 8 or
            row["fallback_prefixes"] != 4 or
            row["raw_joint_exact_lineages"] < 1 or
            row["raw_fallback_exact_lineages"] < 1 or
            row["selected_exact_nine_action_lineages"] < 1 or
            row["exact_terminal_fourth_blocks"] < 1 or
            row["exact_complete_twelve_action_paths"] < 1 or
            row["best_complete_correct_actions"] != 12 or
            not row["runtime_gate_passed"]):
        raise AssertionError("bounded hybrid full-width gate drift")
    if pin and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("bounded hybrid full-width result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("bounded hybrid full-width fixture drift")
    return validate_result(json.loads(raw))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--fallbacks", type=int, default=4)
    args = parser.parse_args()
    # A live development gate is printed even when it is scientifically red;
    # validation is reserved for the immutable pinned fixture.
    row = evaluate(maximum_fallbacks=args.fallbacks) if args.live \
        else load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))
