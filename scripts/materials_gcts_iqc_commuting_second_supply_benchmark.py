#!/usr/bin/env python3
"""Consumed V4 audit of complete second-frontier supply after closure L1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from materials_gcts_action_marginal_prefix_schedule import \
    select_action_marginal_prefixes
from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_commuting_closure_model_artifact import \
    load_default_marking
from materials_gcts_iqc_commuting_parent_execution import \
    freeze_commuting_second_frontier
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, FIRST_RADIUS, MAXIMUM_FALLBACKS,
    POSITION_TOLERANCE, SECOND_RADIUS, SEED_RADIUS, canonical_json)
from materials_gcts_iqc_hybrid_confirmation_v4 import \
    load_default_result as load_v4_result
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_second_supply_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "15492e55d3a10f57b5ba36b24ebc42cb8f18a0d30f4bb2057a08164a56f441aa"
EXPECTED_RESULT_DIGEST = \
    "ae1efbeae10b7f1ecb04dc5ee135aeabe01bb85976d8ce10e76bc5405ebe22a5"


def _exact(actions, truth):
    return all(colored_action_labels(
        actions, truth, tolerance=POSITION_TOLERANCE))


def evaluate(*, workers=4):
    model, artifact = load_default_marking()
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    execution = freeze_commuting_second_frontier(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, marking_model=model, workers=workers)
    schedule, _schedule_artifact = load_default_schedule()
    scheduled = schedule_prefixes(
        schedule=schedule, seed_positions=seed.positions,
        seed_species=seed.species, branches=execution.second_branches)
    marginal = select_action_marginal_prefixes(
        scheduled=scheduled, branches=execution.second_branches,
        maximum_fallbacks=MAXIMUM_FALLBACKS,
        require_universal_avoidance=True,
        base_tail_when_unsaturated=True)
    selected_pairs = frozenset((int(row[0]), int(row[1]))
                               for row in marginal["selected_rows"])
    receipt = {
        "execution": asdict(execution),
        "scheduled_complete_queue_digest":
            scheduled["complete_queue_digest"],
        "marginal_selected_prefix_digest":
            marginal["selected_prefix_digest"],
        "selected_pairs": tuple(sorted(selected_pairs)),
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    target = load_v4_result()
    sites = tuple((tuple(point), str(species))
                  for point, species in target["target_sites"])
    truth = colored_position_index(
        tuple(point for point, _species in sites),
        tuple(species for _point, species in sites),
        tolerance=POSITION_TOLERANCE)
    rows_by_pair = {(int(row[0]), int(row[1])): row for row in
                    tuple(scheduled["selected_rows"]) +
                    tuple(scheduled["deferred_rows"])}
    first_exact = {}
    exact_second = []
    exact_prefix = []
    selected_exact_prefix = []
    exact_ranks = []
    best_second = 0
    for branch in execution.second_branches:
        parent = int(branch.first_rank)
        first_exact[parent] = _exact(branch.first_actions, truth)
        for child, actions in enumerate(branch.second_actions):
            labels = colored_action_labels(
                actions, truth, tolerance=POSITION_TOLERANCE)
            best_second = max(best_second, sum(labels))
            if all(labels):
                exact_second.append((parent, child))
            if first_exact[parent] and all(labels):
                pair = (parent, child)
                exact_prefix.append(pair)
                row = rows_by_pair[pair]
                exact_ranks.append((parent, child, int(row[3]), int(row[5])))
                if pair in selected_pairs:
                    selected_exact_prefix.append(pair)
    body = {
        "schema_version": 1,
        "development_model_digest": model.model_digest,
        "development_artifact_digest": artifact["artifact_digest"],
        "selected_first_parents": len(first_exact),
        "exact_first_parents": sum(first_exact.values()),
        "second_candidates": sum(len(row.second_actions)
                                 for row in execution.second_branches),
        "best_second_correct_actions": best_second,
        "exact_second_blocks": len(exact_second),
        "exact_six_action_prefixes": len(exact_prefix),
        "exact_six_action_pairs": tuple(exact_prefix),
        "exact_six_action_joint_and_base_ranks": tuple(exact_ranks),
        "scheduled_selected_pairs": len(selected_pairs),
        "selected_exact_six_action_prefixes":
            len(selected_exact_prefix),
        "selected_exact_six_action_pairs": tuple(selected_exact_prefix),
        "receipt_digest": receipt_digest,
        "receipt_unchanged_after_scoring":
            hashlib.sha256(canonical_json(receipt)).hexdigest() ==
            receipt_digest,
        "target_used_for_generation_fit_or_ranking": False,
        "consumed_v4_target_opened_only_after_receipt": True,
        "consumed_diagnostic_only": True,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row, *, pin=True):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            row["selected_first_parents"] != 8 or
            row["exact_first_parents"] < 1 or
            row["target_used_for_generation_fit_or_ranking"] or
            not row["consumed_v4_target_opened_only_after_receipt"] or
            not row["receipt_unchanged_after_scoring"] or
            not row["consumed_diagnostic_only"] or
            row["autonomous_or_exponential_growth_claimed"]):
        raise AssertionError("commuting second-supply audit drift")
    if pin and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("commuting second-supply result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("commuting second-supply fixture drift")
    return validate_result(json.loads(raw))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    row = validate_result(evaluate(), pin=False) if args.live \
        else load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))
