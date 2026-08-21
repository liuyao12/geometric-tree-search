#!/usr/bin/env python3
"""Posthoc proposal-reach audit on the consumed site-section nucleus."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _subset_proposals, _without_known_sites)
from materials_gcts_iqc_frozen_fusion_runtime import (
    FrozenFusionTerminal, FusionSearchState, _child, _local_section, _partial,
    _scalar_only_model, action_key, branch_features, load_default_runtime)
from materials_gcts_iqc_obligation_expanded_dataset import _digest, _site_key
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_site_resolved_confirmation_preregistration import (
    CONFIRMATION_CENTER, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_crop_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_recursive_connections import (
    local_cluster_types, propose_with_recursive_marking)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES
from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, select_equivariant_port_fusion)


SCHEDULES = (
    (8, 8, 8),
    (12, 4, 8),
    (12, 8, 8),
    (16, 4, 8),
    (16, 8, 8),
    (24, 4, 8),
)
EXPECTED_RESULT_DIGEST = \
    "d4536b62e1e309ceb4ec49cde089ca41abb45b5538c09f0486785dfa3efbd03d"


def _frontier(runtime, source):
    connection = runtime["connection"]
    proposals = propose_with_recursive_marking(
        connection, source.seed_positions, local_cluster_types(
            source.seed_positions, source.seed_species, CLUSTER_EDGES),
        HIDDEN_UNIT)
    proposals = _without_known_sites(proposals, source.seed_positions)
    return _subset_proposals(proposals, (
        point for point in proposals.votes
        if math.dist(point, source.group) <= TARGET_RADIUS + 1e-8))


def _enumerate_schedule(runtime, source, schedule, *, include_ranking=False):
    connection, state_model = runtime["connection"], runtime["state_model"]
    frontier = _frontier(runtime, source)
    states = (FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ()),)
    counts, attempts = [], 0
    for reach in schedule:
        children = {}
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(state_model, descriptors[point]),
                -state.proposals.votes[point], point)))[:reach]
            attempts += len(ordered)
            for point in ordered:
                candidate = _child(
                    source, connection, state_model, state, point,
                    descriptors[point], TARGET_RADIUS)
                key = action_key(candidate.actions)
                prior = children.get(key)
                if prior is None or (candidate.cumulative, candidate.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = candidate
        states = tuple(sorted(children.values(),
                              key=lambda row: action_key(row.actions)))
        counts.append(len(states))
    if not include_ranking:
        actions = tuple(action_key(state.actions) for state in states)
        return {
            "schedule": tuple(schedule),
            "candidate_counts_by_depth": tuple(counts),
            "proposal_checks": attempts, "terminal_actions": actions,
            "scalar_order": None, "fusion_order": None,
            "terminal_digest": hashlib.sha256(
                repr(actions).encode()).hexdigest(),
            "target_used": False,
        }

    terminals = []
    for state in states:
        partial, graph = _partial(
            source, state, runtime["grouped_vocabulary"])
        terminals.append(FrozenFusionTerminal(
            action_key(state.actions),
            tuple(branch_features(state)) + _local_section(state) + partial,
            tuple(color for _point, color in state.actions), graph,
            action_key(state.actions)))
    terminals = tuple(sorted(terminals, key=lambda row: repr(row.tie_key)))
    candidates = tuple(EquivariantPortFusionCandidate(
        row.scalar_features, row.action_colors, row.graph, row.tie_key)
        for row in terminals)
    fusion = select_equivariant_port_fusion(
        runtime["fusion_model"], candidates)
    scalar = select_equivariant_port_fusion(
        _scalar_only_model(runtime["fusion_model"]), candidates)
    scalar_order = tuple(sorted(range(len(terminals)), key=lambda index: (
        -scalar.fused_scores[index], repr(terminals[index].tie_key))))
    fusion_order = tuple(sorted(range(len(terminals)), key=lambda index: (
        -fusion.fused_scores[index], repr(terminals[index].tie_key))))
    actions = tuple(row.actions for row in terminals)
    return {
        "schedule": tuple(schedule), "candidate_counts_by_depth": tuple(counts),
        "proposal_checks": attempts, "terminal_actions": actions,
        "scalar_order": scalar_order, "fusion_order": fusion_order,
        "terminal_digest": hashlib.sha256(repr(actions).encode()).hexdigest(),
        "target_used": False,
    }


def evaluate():
    runtime = load_default_runtime()
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    source = SimpleNamespace(
        group=tuple(CONFIRMATION_CENTER),
        seed_positions=tuple(seed.positions), seed_species=tuple(seed.species))
    frozen = tuple(_enumerate_schedule(
                       runtime, source, schedule,
                       include_ranking=schedule == (12, 4, 8))
                   for schedule in SCHEDULES)
    geometry_digest = _digest(frozen)

    target, _ = oracle_crop_fast(CONFIRMATION_CENTER, TARGET_RADIUS)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    results = []
    for row in frozen:
        correctness = tuple(tuple(
            truth.get(_site_key(point)) == str(color)
            for point, color in actions) for actions in row["terminal_actions"])
        histogram = tuple(sorted((correct, sum(
            sum(flags) == correct for flags in correctness))
            for correct in range(4)))
        exact_indices = tuple(index for index, flags in enumerate(correctness)
                              if all(flags))
        ranked = row["scalar_order"] is not None
        scalar_rank = ({index: rank + 1 for rank, index in enumerate(
            row["scalar_order"])} if ranked else {})
        fusion_rank = ({index: rank + 1 for rank, index in enumerate(
            row["fusion_order"])} if ranked else {})
        minimum_budget = (next((budget for budget in range(
            1, len(row["terminal_actions"]) + 1) if any(
                scalar_rank[index] <= budget or fusion_rank[index] <= budget
                for index in exact_indices)), None) if ranked else None)
        results.append({
            "schedule": row["schedule"],
            "candidate_counts_by_depth": row["candidate_counts_by_depth"],
            "proposal_checks": row["proposal_checks"],
            "terminal_count": len(row["terminal_actions"]),
            "correct_site_histogram": histogram,
            "exact_terminal_count": sum(all(flags) for flags in correctness),
            "ranking_evaluated": ranked,
            "exact_terminal_ranks": tuple({
                "terminal_index": index,
                "scalar_rank": scalar_rank[index],
                "fusion_rank": fusion_rank[index],
            } for index in exact_indices) if ranked else (),
            "minimum_dual_rank_budget_for_exact_supply": minimum_budget,
            "maximum_correct_sites": max(map(sum, correctness), default=0),
            "terminal_digest": row["terminal_digest"],
        })
    body = {
        "schema_version": 1,
        "consumed_confirmation_diagnostic": True,
        "fresh_confirmation_claimed": False,
        "center": tuple(CONFIRMATION_CENTER),
        "seed_atoms": len(seed.positions), "target_atoms": len(target.positions),
        "geometry_digest_before_target": geometry_digest,
        "target_opened_after_all_schedule_geometry": True,
        "target_used_for_proposal_generation": False,
        "schedule_results": tuple(results),
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
        raise AssertionError("consumed confirmation reach audit drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          "consumed confirmation proposal-reach audit: complete")


if __name__ == "__main__":
    main()
