#!/usr/bin/env python3
"""Diagnose IQC supply after removing only the final beam truncation.

The first two search depths and all candidate geometry remain exactly those of
the published frozen fusion runtime.  At depth three, every already-enumerated
child is retained for terminal scoring instead of reducing 22--29 branches to
eight.  The consumed extended-development targets are unavailable until all
terminal geometry, features, graphs, and policy orders are immutable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from types import SimpleNamespace

from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, select_equivariant_port_fusion)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import (
    BEAM_SPECS, SCHEDULE, FusionSearchState, FrozenFusionTerminal,
    _child, _local_section, _partial, _portfolio_select, _scalar_only_model,
    action_key, branch_features, load_default_runtime)
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, _crop)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_recursive_connections import local_cluster_types


@dataclass(frozen=True)
class CompleteTerminalNucleus:
    center: tuple[float, float, float]
    seed_atoms: int
    candidate_counts_by_depth: tuple[int, ...]
    retained_counts_by_depth: tuple[int, ...]
    terminals: tuple[FrozenFusionTerminal, ...]
    scalar_order: tuple[int, ...]
    fusion_order: tuple[int, ...]
    candidate_digest: str
    target_used: bool = False


@dataclass(frozen=True)
class IQCCompleteTerminalFrontierAudit:
    nuclei: int
    baseline_terminal_budget: int
    complete_terminal_counts: tuple[int, ...]
    candidate_counts_by_depth: tuple[tuple[int, ...], ...]
    retained_counts_by_depth: tuple[tuple[int, ...], ...]
    scalar_terminal_supply_by_center: tuple[bool, ...]
    scalar_selected_exact_by_center: tuple[bool, ...]
    scalar_selected_correct_by_center: tuple[int, ...]
    scalar_first_exact_rank_by_center: tuple[int | None, ...]
    fusion_terminal_supply_by_center: tuple[bool, ...]
    fusion_selected_exact_by_center: tuple[bool, ...]
    fusion_selected_correct_by_center: tuple[int, ...]
    fusion_first_exact_rank_by_center: tuple[int | None, ...]
    scalar_terminal_supply: int
    scalar_selected_exact: int
    scalar_selected_correct: int
    fusion_terminal_supply: int
    fusion_selected_exact: int
    fusion_selected_correct: int
    newly_supplied_nuclei: int
    supply_gate_passed: bool
    incremental_fusion_advantage: bool
    candidates_frozen_before_targets: bool
    target_used_for_candidate_or_ranking: bool
    consumed_development_only: bool
    fresh_confirmation_claimed: bool
    stationary_or_exponential_claimed: bool
    receipt_digest: str
    honest_status: str


def _crop_all(radius, bound):
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS) + radius)
    oracle, _ = oracle_patch_fast(bound, physical)
    return tuple(_crop(oracle, center, radius,
                       "IQC-complete-terminal-development")
                 for center in DEVELOPMENT_CENTERS)


def _complete_states(source, runtime, *, unpruned_from_depth=2,
                     schedule=SCHEDULE):
    schedule = tuple(map(int, schedule))
    if len(schedule) != len(SCHEDULE) or any(reach <= 0 for reach in schedule):
        raise ValueError("schedule must contain one positive reach per depth")
    if unpruned_from_depth not in range(len(schedule)):
        raise ValueError("unpruned_from_depth must name a search depth")
    connection = runtime["connection"]
    state_model = runtime["state_model"]
    frontier = _bounded(connection, source, local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES))
    states = (FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ()),)
    counts, retained = [], []
    for depth, (reach, spec) in enumerate(zip(schedule, BEAM_SPECS)):
        children = {}
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(state_model, descriptors[point]),
                -state.proposals.votes[point], point)))[:reach]
            for point in ordered:
                candidate = _child(
                    source, connection, state_model, state, point,
                    descriptors[point], TARGET_RADIUS)
                key = action_key(candidate.actions)
                prior = children.get(key)
                if prior is None or (candidate.cumulative, candidate.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = candidate
        stage = tuple(sorted(children.values(),
                             key=lambda row: action_key(row.actions)))
        counts.append(len(stage))
        states = stage if depth >= unpruned_from_depth else _portfolio_select(
            runtime["branch_models"], depth, stage, spec)
        retained.append(len(states))
    return states, tuple(counts), tuple(retained)


def _freeze_nucleus(runtime, center, seed, *, unpruned_from_depth=2,
                    schedule=SCHEDULE):
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    states, counts, retained = _complete_states(
        source, runtime, unpruned_from_depth=unpruned_from_depth,
        schedule=schedule)
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
    digest = hashlib.sha256(repr(tuple(
        (row.actions, row.scalar_features, row.action_colors,
         row.graph.canonical_digest) for row in terminals)).encode()).hexdigest()
    return CompleteTerminalNucleus(
        tuple(center), len(seed.positions), counts, retained, terminals,
        scalar_order, fusion_order, digest)


def _score(nucleus, order, truth):
    exact = tuple(all(truth.get(_key(point)) == color
                      for point, color in terminal.actions)
                  for terminal in nucleus.terminals)
    selected = order[0]
    correct = sum(truth.get(_key(point)) == color
                  for point, color in nucleus.terminals[selected].actions)
    rank = next((rank for rank, index in enumerate(order, 1)
                 if exact[index]), None)
    return any(exact), exact[selected], correct, rank


def evaluate():
    runtime = load_default_runtime()
    seeds = _crop_all(SEED_RADIUS, ORACLE_LIFT_BOUND)
    nuclei = tuple(_freeze_nucleus(runtime, center, seed)
                   for center, seed in zip(DEVELOPMENT_CENTERS, seeds))
    receipt = tuple((
        row.center, row.seed_atoms, row.candidate_counts_by_depth,
        row.retained_counts_by_depth, row.candidate_digest,
        tuple(terminal.actions for terminal in row.terminals),
        row.scalar_order, row.fusion_order) for row in nuclei)
    receipt_digest = hashlib.sha256(repr(receipt).encode()).hexdigest()
    immutable = repr(receipt)
    targets = _crop_all(TARGET_RADIUS, ORACLE_LIFT_BOUND)
    scalar, fusion = [], []
    for nucleus, target in zip(nuclei, targets):
        truth = {_key(point): str(color) for point, color in
                 zip(target.positions, target.species)}
        scalar.append(_score(nucleus, nucleus.scalar_order, truth))
        fusion.append(_score(nucleus, nucleus.fusion_order, truth))
    if immutable != repr(receipt):
        raise AssertionError("complete terminal receipt changed after scoring")
    scalar_supply, scalar_exact, scalar_correct = (
        sum(row[index] for row in scalar) for index in range(3))
    fusion_supply, fusion_exact, fusion_correct = (
        sum(row[index] for row in fusion) for index in range(3))
    supply_passed = fusion_supply == len(nuclei)
    incremental = fusion_exact > scalar_exact or \
        fusion_correct > scalar_correct
    return IQCCompleteTerminalFrontierAudit(
        len(nuclei), 8, tuple(len(row.terminals) for row in nuclei),
        tuple(row.candidate_counts_by_depth for row in nuclei),
        tuple(row.retained_counts_by_depth for row in nuclei),
        tuple(row[0] for row in scalar), tuple(row[1] for row in scalar),
        tuple(row[2] for row in scalar), tuple(row[3] for row in scalar),
        tuple(row[0] for row in fusion), tuple(row[1] for row in fusion),
        tuple(row[2] for row in fusion), tuple(row[3] for row in fusion),
        scalar_supply, scalar_exact, scalar_correct,
        fusion_supply, fusion_exact, fusion_correct,
        fusion_supply - 6, supply_passed, incremental, True, False, True,
        False, False, receipt_digest,
        ("final beam truncation caused missing terminal supply"
         if supply_passed else
         "complete final frontier still lacks exact terminal supply"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
