#!/usr/bin/env python3
"""Posthoc full-tree supply audit for the consumed site-section confirmation.

The confirmation target is already consumed and its one-shot result is never
recomputed or reinterpreted here.  This diagnostic freezes all complete-tree
geometry, target-free rollouts, and site-section scores first; it then uses an
exact local model-set crop only to locate the previously omitted exact actions
and measure fixed portfolio-width requirements.
"""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)
from materials_gcts_iqc_frozen_fusion_runtime import action_key, load_default_runtime
from materials_gcts_iqc_obligation_expanded_dataset import _digest, _site_key
from materials_gcts_iqc_obligation_site_resolved_audit import (
    score_site_resolved_model)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius, _freeze_at_radius)
from materials_gcts_iqc_site_resolved_confirmation_benchmark import (
    _training_model)
from materials_gcts_iqc_site_resolved_confirmation_preregistration import (
    CONFIRMATION_CENTER, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout
from materials_gcts_icosahedral_modelset import oracle_crop_fast


EXPECTED_RESULT_DIGEST = \
    "1b3091f26963a9e5a174b553d9effcdbdcdd8c955ae276f31c7bc5eef4d68f5f"
PORTFOLIO_BUDGETS = (4, 8, 12, 16, 24, 32, 48, 64)


def _rank_map(order):
    return {int(index): rank + 1 for rank, index in enumerate(order)}


def evaluate():
    model = _training_model()
    runtime = load_default_runtime()
    seed, _seed_lifts = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    source = SimpleNamespace(
        group=tuple(CONFIRMATION_CENTER),
        seed_positions=tuple(seed.positions), seed_species=tuple(seed.species))
    nucleus = _freeze_at_radius(
        runtime, CONFIRMATION_CENTER, seed, TARGET_RADIUS)
    states, counts = _complete_states_at_radius(source, runtime, TARGET_RADIUS)
    states_by_action = {action_key(state.actions): state for state in states}
    if tuple(counts) != tuple(nucleus.candidate_counts_by_depth) or \
            len(states_by_action) != len(nucleus.terminals):
        raise AssertionError("consumed confirmation candidate accounting drift")

    rows = []
    for index, terminal in enumerate(nucleus.terminals):
        actions = tuple(terminal.actions)
        trace, transitions = _rollout(
            source, states_by_action[actions], runtime, relational=True)
        if trace["target_used"]:
            raise AssertionError("target-tainted supply diagnostic rollout")
        candidate = {
            "group": -1, "candidate_index": index,
            "action_key": actions, "transitions": tuple(transitions),
            "trace": trace,
        }
        site_scores, score = score_site_resolved_model(model, candidate)
        rows.append({
            "candidate_index": index, "action_key": actions,
            "site_scores": tuple(site_scores), "site_score": float(score),
            "transition_digest": _digest(tuple(transitions)),
        })
    geometry_body = {
        "center": tuple(CONFIRMATION_CENTER), "seed_atoms": len(seed.positions),
        "candidate_counts_by_depth": tuple(counts),
        "candidate_digest": nucleus.candidate_digest,
        "rows": tuple(rows), "target_used": False,
    }
    geometry_digest = _digest(geometry_body)

    # This crop is opened only after the full candidate geometry and every
    # marking score above is immutable.  The target is already consumed by the
    # published one-shot result, so this is explicitly diagnostic evidence.
    target, _target_lifts = oracle_crop_fast(
        CONFIRMATION_CENTER, TARGET_RADIUS)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    labelled = []
    for row in rows:
        site_correct = tuple(
            truth.get(_site_key(point)) == str(color)
            for point, color in row["action_key"])
        labelled.append({
            **row, "site_correct": site_correct,
            "correct_sites": sum(site_correct), "exact": all(site_correct),
        })
    exact_indices = tuple(
        row["candidate_index"] for row in labelled if row["exact"])
    scalar_rank, fusion_rank = (
        _rank_map(nucleus.scalar_order), _rank_map(nucleus.fusion_order))
    site_order = tuple(sorted(range(len(labelled)), key=lambda index: (
        -labelled[index]["site_score"], repr(labelled[index]["action_key"]))))
    site_rank = _rank_map(site_order)

    candidate_ids = tuple(row.actions for row in nucleus.terminals)
    portfolios = []
    for budget in PORTFOLIO_BUDGETS:
        selected = select_dual_rank_terminal_portfolio(
            candidate_ids, nucleus.scalar_order, nucleus.fusion_order,
            per_channel_budget=budget)
        exact = sum(index in exact_indices for index in selected.selected_indices)
        portfolios.append({
            "per_channel_budget": budget,
            "retained_candidates": len(selected.selected_indices),
            "exact_candidates": exact,
            "selection_digest": selected.selection_digest,
        })
    minimum_union_budget = next((budget for budget in range(1, len(labelled) + 1)
                                 if any(scalar_rank[index] <= budget or
                                        fusion_rank[index] <= budget
                                        for index in exact_indices)), None)
    body = {
        "schema_version": 1,
        "consumed_confirmation_diagnostic": True,
        "fresh_confirmation_claimed": False,
        "center": tuple(CONFIRMATION_CENTER),
        "seed_atoms": len(seed.positions), "target_atoms": len(target.positions),
        "candidate_counts_by_depth": tuple(counts),
        "complete_terminal_count": len(labelled),
        "geometry_digest_before_target": geometry_digest,
        "target_opened_after_all_geometry_and_scores": True,
        "target_used_for_candidate_rollout_or_ranking": False,
        "exact_candidate_count": len(exact_indices),
        "exact_candidate_indices": exact_indices,
        "exact_candidate_ranks": tuple({
            "candidate_index": index,
            "scalar_rank": scalar_rank[index],
            "fusion_rank": fusion_rank[index],
            "site_section_rank": site_rank[index],
        } for index in exact_indices),
        "minimum_dual_rank_budget_for_exact_supply": minimum_union_budget,
        "portfolio_width_audit": tuple(portfolios),
        "site_section_top_candidate_exact": labelled[site_order[0]]["exact"],
        "site_section_top_candidate_correct_sites":
            labelled[site_order[0]]["correct_sites"],
        "candidate_geometry_changed": False,
        "policy_integrated": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    if EXPECTED_RESULT_DIGEST and row["result_digest"] != EXPECTED_RESULT_DIGEST:
        raise AssertionError("consumed confirmation supply audit drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          "consumed confirmation full-tree supply audit: complete")


if __name__ == "__main__":
    main()
