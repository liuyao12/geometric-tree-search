#!/usr/bin/env python3
"""Consumed IQC supply gate for the closure-conditioned child marking."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_commuting_child_action_marking_fit import \
    load_default_marking as load_child_marking
from materials_gcts_iqc_commuting_closure_model_artifact import \
    load_default_marking as load_parent_marking
from materials_gcts_iqc_commuting_parent_execution import \
    freeze_commuting_second_frontier
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, FIRST_RADIUS, POSITION_TOLERANCE, SECOND_RADIUS,
    SEED_RADIUS, canonical_json)
from materials_gcts_iqc_hybrid_confirmation_v4 import \
    load_default_result as load_v4_result
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_child_action_marking import rank_joint_children


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_child_supply_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "0d48e0b695c8791879f282808798b92d8cb000d50ca6431109e1249bba3662e1"
EXPECTED_RESULT_DIGEST = \
    "cae8ce06001f74bbfe1239ddd40cc2f95983340f4abe11e499d702887d9e59fa"


def _exact(actions, truth):
    return all(colored_action_labels(
        actions, truth, tolerance=POSITION_TOLERANCE))


def evaluate(*, workers=4):
    parent_model, parent_artifact = load_parent_marking()
    child_model, child_artifact = load_child_marking()
    if (child_artifact["upstream_model_digest"] !=
            parent_model.model_digest or child_model.target_used_for_scoring):
        raise AssertionError("child model is not bound to the parent model")
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    execution = freeze_commuting_second_frontier(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, marking_model=parent_model,
        workers=workers)
    ranked = []
    selected_pairs = []
    for branch in execution.second_branches:
        rows = rank_joint_children(
            model=child_model, seed_positions=seed.positions,
            seed_species=seed.species, branch=branch)
        ranked.append((int(branch.first_rank), rows))
        selected_pairs.extend((int(branch.first_rank), int(child))
                              for child, _score in
                              rows[:child_model.child_top_k])
    receipt = {
        "execution": asdict(execution),
        "parent_model_digest": parent_model.model_digest,
        "parent_artifact_digest": parent_artifact["artifact_digest"],
        "child_model_digest": child_model.model_digest,
        "child_artifact_digest": child_artifact["artifact_digest"],
        "ranked_children": ranked,
        "selected_pairs": tuple(selected_pairs),
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()
    frozen_receipt = canonical_json(receipt)

    # This target is already consumed and first appears after the complete
    # geometry, model, scores, ordering, and selected prefix set are frozen.
    target = load_v4_result()
    sites = tuple((tuple(point), str(species))
                  for point, species in target["target_sites"])
    truth = colored_position_index(
        tuple(point for point, _species in sites),
        tuple(species for _point, species in sites),
        tolerance=POSITION_TOLERANCE)
    branch_by_parent = {int(row.first_rank): row
                        for row in execution.second_branches}
    exact_pairs = []
    exact_ranks = []
    selected_exact = []
    selected_set = set(selected_pairs)
    for parent, rows in ranked:
        branch = branch_by_parent[parent]
        first_exact = _exact(branch.first_actions, truth)
        order = tuple(child for child, _score in rows)
        for child, actions in enumerate(branch.second_actions):
            if first_exact and _exact(actions, truth):
                pair = (parent, child)
                exact_pairs.append(pair)
                exact_ranks.append((parent, child,
                                    order.index(child) + 1))
                if pair in selected_set:
                    selected_exact.append(pair)
    body = {
        "schema_version": 1,
        "parent_model_digest": parent_model.model_digest,
        "child_model_digest": child_model.model_digest,
        "selected_first_parents": len(execution.second_branches),
        "second_candidates": sum(len(row.second_actions)
                                  for row in execution.second_branches),
        "selected_child_width_per_parent": child_model.child_top_k,
        "selected_six_action_prefixes": len(selected_pairs),
        "exact_six_action_prefixes": len(exact_pairs),
        "exact_six_action_pairs": exact_pairs,
        "exact_six_action_child_ranks": exact_ranks,
        "selected_exact_six_action_prefixes": len(selected_exact),
        "selected_exact_six_action_pairs": selected_exact,
        "receipt_digest": receipt_digest,
        "receipt_unchanged_after_scoring":
            canonical_json(receipt) == frozen_receipt,
        "target_used_for_generation_fit_or_ranking": False,
        "consumed_v4_target_opened_only_after_receipt": True,
        "conditional_child_model_diagnostic_only": True,
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
            row["exact_six_action_prefixes"] < 1 or
            row["target_used_for_generation_fit_or_ranking"] or
            not row["receipt_unchanged_after_scoring"] or
            not row["consumed_v4_target_opened_only_after_receipt"] or
            not row["conditional_child_model_diagnostic_only"] or
            row["fresh_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"]):
        raise AssertionError("commuting child-supply audit drift")
    if pin and EXPECTED_RESULT_DIGEST != "PENDING" and \
            digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("commuting child-supply result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 != "PENDING" and \
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("commuting child-supply fixture drift")
    return validate_result(json.loads(raw))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.live or args.write:
        row = validate_result(evaluate(workers=args.workers), pin=False)
        if args.write:
            if DEFAULT_FIXTURE.exists():
                raise RuntimeError("commuting child-supply fixture exists")
            DEFAULT_FIXTURE.write_text(
                json.dumps(row, indent=2, sort_keys=True) + "\n")
    else:
        row = load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))
