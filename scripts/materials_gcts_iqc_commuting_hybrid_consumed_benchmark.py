#!/usr/bin/env python3
"""Consumed V4 end-to-end diagnostic for commuting-closure first parents."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_commuting_closure_model_artifact import \
    load_default_marking
from materials_gcts_iqc_commuting_hybrid_execution import \
    freeze_commuting_hybrid_execution
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, FIRST_RADIUS, FOURTH_RADIUS, MAXIMUM_FALLBACKS,
    POSITION_TOLERANCE, SECOND_RADIUS, SEED_RADIUS, THIRD_RADIUS,
    canonical_json)
from materials_gcts_iqc_hybrid_confirmation_v4 import \
    load_default_result as load_v4_result
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_hybrid_consumed_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "4de531b7d40b80c9304af37c3ca0d69a22d0b49108a42e32a699334f0dab1b0f"
EXPECTED_RESULT_DIGEST = \
    "bd3e8a61ca74967fb3a9549b292ea7fd487b18c18b72e7e2ffd1a525d210b19c"


def _exact(actions, truth):
    return tuple(all(colored_action_labels(
        row, truth, tolerance=POSITION_TOLERANCE)) for row in actions)


def _action_labels(actions, truth):
    return tuple(tuple(colored_action_labels(
        row, truth, tolerance=POSITION_TOLERANCE)) for row in actions)


def _prefix_counts(labels):
    if not labels:
        return (), ()
    blocks = len(labels[0]) // 3
    return (
        tuple(sum(all(row[:3 * (block + 1)]) for row in labels)
              for block in range(blocks)),
        tuple(max((sum(row[3 * block:3 * (block + 1)])
                       for row in labels), default=0)
              for block in range(blocks)))


def evaluate(*, workers=4):
    started = time.perf_counter()
    model, artifact = load_default_marking()
    model_seconds = time.perf_counter() - started
    if model.target_used or not artifact["development_gate_passed"]:
        raise AssertionError("commuting model did not reproduce development")
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    started = time.perf_counter()
    execution = freeze_commuting_hybrid_execution(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, third_radius=THIRD_RADIUS,
        fourth_radius=FOURTH_RADIUS, marking_model=model, workers=workers,
        maximum_fallbacks=MAXIMUM_FALLBACKS)
    execution_seconds = time.perf_counter() - started
    receipt = asdict(execution)
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()
    frozen_receipt = canonical_json(receipt)
    if execution.target_used or execution.downstream.target_used:
        raise AssertionError("target-tainted commuting execution")

    # The already-consumed V4 target first enters after the complete receipt.
    target = load_v4_result()
    sites = tuple((tuple(point), str(species))
                  for point, species in target["target_sites"])
    truth = colored_position_index(
        tuple(point for point, _species in sites),
        tuple(species for _point, species in sites),
        tolerance=POSITION_TOLERANCE)
    first_labels = _exact(
        execution.first_frontier.selected_first_actions, truth)
    raw = execution.downstream.raw_nine_action_lineages
    raw_action_labels = _action_labels(
        tuple(row.all_actions for row in raw), truth)
    raw_labels = tuple(all(row) for row in raw_action_labels)
    raw_prefix_exact, raw_block_best = _prefix_counts(raw_action_labels)
    candidates = execution.downstream.candidates
    complete_action_labels = _action_labels(
        tuple(row.all_actions for row in candidates), truth)
    complete_labels = tuple(all(row) for row in complete_action_labels)
    complete_prefix_exact, complete_block_best = _prefix_counts(
        complete_action_labels)
    terminal_labels = _exact(
        tuple(row.all_actions[-3:] for row in candidates), truth)
    receipt_unchanged = (
        canonical_json(asdict(execution)) == frozen_receipt)
    body = {
        "schema_version": 1,
        "development_model_digest": model.model_digest,
        "development_source_fixture_sha256":
            artifact["development_source_fixture_sha256"],
        "selected_representation": model.scalar.representation.name,
        "selected_neighbors": model.scalar.value.neighbors,
        "selected_graph_rank_weight": 0.0,
        "model_fit_seconds": model_seconds,
        "execution_seconds": execution_seconds,
        "first_candidate_digest":
            execution.first_frontier.closure_candidate_digest,
        "selected_first_parents": len(first_labels),
        "exact_selected_first_parents": sum(first_labels),
        "raw_nine_action_lineages": len(raw_labels),
        "exact_raw_nine_action_lineages": sum(raw_labels),
        "raw_prefix_exact_counts_at_3_6_9": raw_prefix_exact,
        "raw_best_correct_actions_by_block": raw_block_best,
        "fourth_candidates": len(complete_labels),
        "exact_complete_twelve_action_paths": sum(complete_labels),
        "complete_prefix_exact_counts_at_3_6_9_12":
            complete_prefix_exact,
        "complete_best_correct_actions_by_block": complete_block_best,
        "exact_terminal_fourth_blocks": sum(terminal_labels),
        "best_complete_correct_actions": max((sum(
            colored_action_labels(row.all_actions, truth,
                                  tolerance=POSITION_TOLERANCE))
            for row in candidates), default=0),
        "receipt_digest": receipt_digest,
        "receipt_unchanged_after_scoring": receipt_unchanged,
        "candidate_geometry_unchanged":
            execution.candidate_geometry_unchanged,
        "target_used_for_model_fit_generation_or_ranking": False,
        "consumed_v4_target_opened_only_after_receipt": True,
        "consumed_diagnostic_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row, *, pin=True):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            row["selected_first_parents"] != 8 or
            row["exact_selected_first_parents"] < 1 or
            row["target_used_for_model_fit_generation_or_ranking"] or
            not row["consumed_v4_target_opened_only_after_receipt"] or
            not row["receipt_unchanged_after_scoring"] or
            not row["candidate_geometry_unchanged"] or
            not row["consumed_diagnostic_only"] or
            row["fresh_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"]):
        raise AssertionError("commuting hybrid consumed audit drift")
    if pin and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("commuting hybrid consumed result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("commuting hybrid consumed fixture drift")
    return validate_result(json.loads(raw))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    row = validate_result(evaluate(workers=args.workers), pin=False) \
        if args.live else load_default_result()
    print(json.dumps(row,
                     indent=2, sort_keys=True))
