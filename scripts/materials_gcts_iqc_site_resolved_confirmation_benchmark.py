#!/usr/bin/env python3
"""One-shot self-fed confirmation of the frozen site-resolved IQC marking."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_iqc_obligation_expanded_dataset import (
    _digest, _site_key, load_default_dataset as load_training_geometry)
from materials_gcts_iqc_obligation_expanded_site_labels import (
    load_default_dataset as load_training_labels)
from materials_gcts_iqc_obligation_site_resolved_audit import (
    SiteResolvedSpec, fit_site_resolved_model, score_site_resolved_model)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius, _freeze_at_radius)
from materials_gcts_iqc_site_resolved_confirmation_preregistration import (
    CANDIDATES_PER_BASE_RANKER, CONFIRMATION_CENTER,
    EXPECTED_MANIFEST_DIGEST, FROZEN_MODEL_DIGEST,
    MAXIMUM_FROZEN_CANDIDATES, ORACLE_LIFT_BOUND, REQUIRED_EXACT_SITES,
    SEED_RADIUS, SELECTED_SPEC, SELF_FED_WAVES, SOURCE_FILE_SHA256S,
    TARGET_RADIUS, audit as preregistration_audit)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
EXPECTED_RESULT_DIGEST = \
    "51bb326bb7a1e3c80493239f4e814a95a6c383b333369e4b22ba50e3d11d6dd8"


def _training_model():
    geometry_source = load_training_geometry()
    label_source = load_training_labels()
    if label_source["source_dataset_digest"] != \
            geometry_source["dataset_digest"]:
        raise AssertionError("confirmation training fixtures disagree")
    geometry = tuple({
        "group": int(group["group"]), "candidate_index": index,
        "action_key": row["action_key"], "transitions": row["transitions"],
        "trace": row["trace"],
    } for group in geometry_source["groups"]
      for index, row in enumerate(group["rows"]))
    labels = {
        f"{int(group['group'])}:{int(item['candidate_index'])}:{site}":
        bool(value)
        for group in label_source["groups"] for item in group["rows"]
        for site, value in enumerate(item["site_correct"])}
    spec = SiteResolvedSpec(**dict(SELECTED_SPEC))
    model = fit_site_resolved_model(geometry, labels, spec)
    if model.model_digest != FROZEN_MODEL_DIGEST:
        raise AssertionError("frozen site model drift")
    return model


def _verify_sources():
    for name, expected in SOURCE_FILE_SHA256S:
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"confirmation source drift: {name}")


def _freeze_wave(runtime, model, wave, positions, species):
    source = SimpleNamespace(
        group=tuple(CONFIRMATION_CENTER), seed_positions=tuple(positions),
        seed_species=tuple(species))
    seed = SimpleNamespace(positions=source.seed_positions,
                           species=source.seed_species)
    nucleus = _freeze_at_radius(
        runtime, CONFIRMATION_CENTER, seed, TARGET_RADIUS)
    states, counts = _complete_states_at_radius(
        source, runtime, TARGET_RADIUS)
    states_by_action = {action_key(state.actions): state for state in states}
    if tuple(counts) != tuple(nucleus.candidate_counts_by_depth) or \
            len(states_by_action) != len(nucleus.terminals):
        raise AssertionError(f"confirmation wave {wave} accounting drift")
    candidate_ids = tuple(row.actions for row in nucleus.terminals)
    portfolio = select_dual_rank_terminal_portfolio(
        candidate_ids, nucleus.scalar_order, nucleus.fusion_order,
        per_channel_budget=CANDIDATES_PER_BASE_RANKER)
    if len(portfolio.selected_candidate_ids) > MAXIMUM_FROZEN_CANDIDATES:
        raise AssertionError("confirmation candidate portfolio exceeds bound")
    rows = []
    for actions in portfolio.selected_candidate_ids:
        state = states_by_action[tuple(actions)]
        trace, transitions = _rollout(
            source, state, runtime, relational=True)
        if trace["target_used"]:
            raise AssertionError("target-tainted confirmation rollout")
        candidate = {
            "group": -1, "candidate_index": len(rows),
            "action_key": tuple(actions), "transitions": tuple(transitions),
            "trace": trace,
        }
        site_scores, score = score_site_resolved_model(model, candidate)
        rows.append({
            "candidate_index": len(rows), "action_key": tuple(actions),
            "site_scores": site_scores, "score": score,
            "trace": trace, "transition_digest": _digest(transitions),
        })
    rows = tuple(rows)
    ranked = tuple(sorted(rows, key=lambda row: (
        -float(row["score"]), repr(row["action_key"]))))
    selected = ranked[0]
    selected_state = states_by_action[tuple(selected["action_key"])]
    body = {
        "wave": int(wave), "source_atoms": len(positions),
        "candidate_counts_by_depth": tuple(counts),
        "complete_terminal_count": len(states),
        "retained_candidates": len(rows),
        "candidate_digest": nucleus.candidate_digest,
        "portfolio_digest": portfolio.selection_digest,
        "ranked_candidates": ranked,
        "selected_action_key": selected["action_key"],
        "selected_score": selected["score"],
        "selected_site_scores": selected["site_scores"],
        "target_used": False,
    }
    return ({**body, "wave_digest_before_target": _digest(body)},
            tuple(selected_state.positions), tuple(selected_state.species))


def evaluate():
    protocol = preregistration_audit()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("confirmation preregistration drift")
    _verify_sources()
    model = _training_model()
    runtime = load_default_runtime()

    seed_physical_radius = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        ORACLE_LIFT_BOUND, seed_physical_radius)
    seed = _crop(seed_oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "site-resolved-confirmation-seed")
    if not seed.positions:
        raise AssertionError("empty confirmation seed")

    waves = []
    positions, species = tuple(seed.positions), tuple(seed.species)
    for wave in range(SELF_FED_WAVES):
        record, positions, species = _freeze_wave(
            runtime, model, wave + 1, positions, species)
        waves.append(record)
    execution_body = {
        "protocol_digest": protocol.manifest_digest,
        "model_digest": model.model_digest,
        "seed_atoms": len(seed.positions), "waves": tuple(waves),
        "final_atoms_before_target": len(positions),
        "target_used": False,
    }
    execution_digest = _digest(execution_body)

    # The only outer-target construction occurs after every wave, score, and
    # selected action above has become immutable.
    target_physical_radius = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(
        ORACLE_LIFT_BOUND, target_physical_radius)
    check, _ = oracle_patch_fast(
        ORACLE_LIFT_BOUND + 1, target_physical_radius)
    target = _crop(oracle, CONFIRMATION_CENTER, TARGET_RADIUS,
                   "site-resolved-confirmation-target")
    target_check = _crop(check, CONFIRMATION_CENTER, TARGET_RADIUS,
                         "site-resolved-confirmation-target-check")
    seed_check = _crop(check, CONFIRMATION_CENTER, SEED_RADIUS,
                       "site-resolved-confirmation-seed-check")
    stable = ((tuple(target.positions), tuple(target.species)) ==
              (tuple(target_check.positions), tuple(target_check.species)) and
              (tuple(seed.positions), tuple(seed.species)) ==
              (tuple(seed_check.positions), tuple(seed_check.species)))
    if not stable:
        raise AssertionError("confirmation crop changes at bound + 1")
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    scored_waves = []
    for wave in waves:
        scored_candidates = []
        for row in wave["ranked_candidates"]:
            site_correct = tuple(
                truth.get(_site_key(point)) == str(color)
                for point, color in row["action_key"])
            scored_candidates.append({
                "candidate_index": row["candidate_index"],
                "site_correct": site_correct,
                "exact": all(site_correct),
                "correct_sites": sum(site_correct),
            })
        selected = scored_candidates[0]
        scored_waves.append({
            "wave": wave["wave"],
            "exact_candidate_supply": sum(
                int(row["exact"]) for row in scored_candidates),
            "selected_exact": selected["exact"],
            "selected_correct_sites": selected["correct_sites"],
            "selected_site_correct": selected["site_correct"],
        })
    exact_sites = sum(row["selected_correct_sites"] for row in scored_waves)
    body = {
        "schema_version": 1,
        "protocol_digest": protocol.manifest_digest,
        "model_digest": model.model_digest,
        "confirmation_center": CONFIRMATION_CENTER,
        "minimum_consumed_center_separation":
            protocol.minimum_consumed_center_separation,
        "seed_atoms": len(seed.positions), "target_atoms": len(target.positions),
        "execution_digest_before_target": execution_digest,
        "wave_candidate_digests": tuple(
            row["candidate_digest"] for row in waves),
        "wave_portfolio_digests": tuple(
            row["portfolio_digest"] for row in waves),
        "wave_frozen_receipts": tuple(waves),
        "posthoc_wave_scores": tuple(scored_waves),
        "selected_exact_sites": exact_sites,
        "required_exact_sites": REQUIRED_EXACT_SITES,
        "self_fed_depth": len(waves),
        "target_factory_calls": 1,
        "target_opened_after_all_wave_rankings": True,
        "oracle_bound_plus_one_stable": stable,
        "target_used_for_fit_candidates_ranking_or_execution": False,
        "candidate_geometry_changed": False,
        "branches_spliced_or_sites_moved": False,
        "fresh_confirmation_consumed": True,
        "autonomous_finite_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["confirmation_gate_passed"] = bool(
        all(row["exact_candidate_supply"] > 0 and row["selected_exact"]
            and row["selected_correct_sites"] == 3 for row in scored_waves) and
        exact_sites == REQUIRED_EXACT_SITES and stable and
        body["target_factory_calls"] == 1 and
        body["target_opened_after_all_wave_rankings"] and
        not body["target_used_for_fit_candidates_ranking_or_execution"])
    return {**body, "result_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    if EXPECTED_RESULT_DIGEST and row["result_digest"] != \
            EXPECTED_RESULT_DIGEST:
        raise AssertionError("site-resolved confirmation result drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          ("site-resolved confirmation passes" if
           row["confirmation_gate_passed"] else
           "site-resolved confirmation remains red"))


if __name__ == "__main__":
    main()
