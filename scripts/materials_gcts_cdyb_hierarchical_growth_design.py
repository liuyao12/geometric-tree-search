#!/usr/bin/env python3
"""Sealed primitive-versus-hierarchical Cd--Yb autonomous-growth design."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_batch_frontier_search import run_batch_frontier_search
from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    _pack, _window_ids)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, _site_key, fit_frozen_frontier_program)
from materials_gcts_frozen_hierarchy_transfer import (
    transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import (
    _frozen_heldout_program)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import (
    ExecutionBoundary, execute_recurrent_macro_program,
    score_recurrent_macro_execution)


EVAL_CENTER = (35.0, 30.0, 20.0)
TRAIN_RADIUS = 14.0
SEED_RADIUS = 14.0
TARGET_RADIUS = 25.0
MAXIMUM_WAVES = 3
MAXIMUM_ACCEPTED_PER_WAVE = 40
PRIMITIVE_THRESHOLD = 0.7


@dataclass(frozen=True)
class MatchedWork:
    matched_correct_atoms: int
    proposal_checks: int
    geometric_or_oracle_backtracks: int


@dataclass(frozen=True)
class GrowthArm:
    arm: str
    hierarchy_level: int
    executable: bool
    seed_occurrences: int
    frozen_candidate_digest: str
    candidates: int
    accepted_actions: int
    proposed_novel_atoms: int
    correct_novel_atoms: int
    wrong_novel_atoms: int
    precision: float
    outer_recall: float
    matched_work: MatchedWork | None
    target_used_during_compile_or_execution: bool
    blocked_reason: str


@dataclass(frozen=True)
class CdYbHierarchicalGrowthDesign:
    train_centers: tuple[tuple[float, float, float], ...]
    eval_center: tuple[float, float, float]
    train_radius: float
    seed_radius: float
    target_radius: float
    train_atoms: int
    seed_atoms: int
    target_atoms: int
    train_target_raw_id_intersection: int
    minimum_train_eval_center_separation: float
    spatial_domains_disjoint: bool
    oracle_target_ball_unclipped: bool
    frozen_hierarchy_levels: int
    seed_active_types_by_level: tuple[int, ...]
    seed_occurrences_by_level: tuple[int, ...]
    executable_hierarchy_levels: tuple[int, ...]
    arms: tuple[GrowthArm, ...]
    common_matched_correct_atom_budget: int
    target_factory_called_after_all_candidate_traces_frozen: bool
    candidate_sets_target_blind_and_digest_frozen: bool
    same_train_seed_boundary_for_all_arms: bool
    heldout_target_used_for_fit_ranking_or_branch_selection: bool
    exact_blocker: str
    benchmark_is_design_not_growth_claim: bool


def _ids(atoms, center, radius):
    return tuple(index for index, point in enumerate(atoms.positions)
                 if math.dist(point, center) <= radius + 1e-10)


def _primitive_seed(program, species, positions):
    enumeration = enumerate_frozen_port_occurrences(
        program, species, positions, select_greedy_cover=True)
    covered = {index for _occurrence, support in
               enumeration.occurrence_supports for index in support}
    gaps = tuple((species[index], positions[index])
                 for index in range(len(positions)) if index not in covered)
    return enumeration, FrontierSeed(enumeration.occurrences, gaps)


def _digest_primitive(result):
    payload = tuple(tuple(item.candidate_id for item in wave.candidates)
                    for wave in result.waves)
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def _primitive_exact_union(result, target_keys):
    return {site for wave in result.waves for item in wave.candidates
            if item.accepted and item.emitted_site_keys and
            set(item.emitted_site_keys).issubset(target_keys)
            for site in item.emitted_site_keys}


def _macro_exact_union(result, target_keys):
    return {site for item in result.accepted
            if item.certificate.emitted_sites and
            set(item.certificate.emitted_sites).issubset(target_keys)
            for site in item.certificate.emitted_sites}


def _primitive_work(result, target_keys, budget):
    recovered = set()
    checks = backtracks = 0
    for wave in result.waves:
        for item in wave.candidates:
            checks += 1
            exact = (item.accepted and item.emitted_site_keys and
                     set(item.emitted_site_keys).issubset(target_keys))
            if exact:
                recovered.update(item.emitted_site_keys)
            elif item.accepted or item.rejection in {
                    "pair-conflict", "redundant-after-batch"}:
                backtracks += 1
            if len(recovered) >= budget:
                return MatchedWork(budget, checks, backtracks)
    return MatchedWork(len(recovered), checks, backtracks)


def _macro_work(result, target_keys, budget):
    accepted = {item.candidate_id: item for item in result.accepted}
    recovered = set()
    checks = backtracks = 0
    for event in result.trace:
        if event.phase != "commit":
            continue
        checks += 1
        placement = accepted.get(event.candidate_id)
        exact = (placement is not None and
                 placement.certificate.emitted_sites and
                 set(placement.certificate.emitted_sites).issubset(
                     target_keys))
        if exact:
            recovered.update(placement.certificate.emitted_sites)
        elif placement is not None or event.decision == "commit-conflict":
            backtracks += 1
        if len(recovered) >= budget:
            return MatchedWork(budget, checks, backtracks)
    return MatchedWork(len(recovered), checks, backtracks)


def evaluate():
    atoms = generate_cdyb(6, (120.0,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    train_ids = set().union(*map(set, train_windows))
    train_species, train_positions, _train_patch = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    train = compile_irregular_port_program(train_species, train_positions)
    frozen_primitive = fit_frozen_frontier_program(train)
    frozen_levels = []
    artifact = train
    for level in range(4):
        quotient = quotient_macro_supports(mine_port_graph_macros(
            artifact, maximum_nodes=3,
            include_boundary_relations=True).macro_types)
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            artifact, quotient.quotient_macros, level=level + 1)
        frozen_levels.append((quotient, promoted))
        artifact = promoted

    seed_ids = _ids(atoms, EVAL_CENTER, SEED_RADIUS)
    seed_species = tuple(atoms.symbols[index] for index in seed_ids)
    seed_positions = tuple(atoms.positions[index] for index in seed_ids)
    seed_sites = tuple(zip(seed_species, seed_positions))
    primitive_enumeration, primitive_seed = _primitive_seed(
        train, seed_species, seed_positions)
    primitive_execution = run_batch_frontier_search(
        frozen_primitive, primitive_seed,
        threshold_ratio=PRIMITIVE_THRESHOLD,
        maximum_waves=MAXIMUM_WAVES,
        maximum_accepted_per_wave=MAXIMUM_ACCEPTED_PER_WAVE,
        boundary=RadialBoundary(EVAL_CENTER, TARGET_RADIUS))

    seed_artifact = _frozen_heldout_program(train, primitive_enumeration)
    seed_active = []
    seed_occurrences = []
    macro_executions = []
    for quotient, promoted in frozen_levels:
        step = transfer_frozen_hierarchy_level(
            seed_artifact, quotient, promoted, (0,) * len(seed_ids),
            raw_atom_sites=seed_sites)
        seed_artifact = step.program
        seed_active.append(step.audit.transferred_types)
        seed_occurrences.append(step.audit.occurrences)
        if step.program.occurrences:
            execution = execute_recurrent_macro_program(
                promoted, step.program.occurrences,
                explicit_seed_sites=seed_sites,
                boundary=ExecutionBoundary(EVAL_CENTER, TARGET_RADIUS),
                maximum_waves=MAXIMUM_WAVES,
                maximum_accepted_per_wave=MAXIMUM_ACCEPTED_PER_WAVE)
            macro_executions.append((promoted.level, execution))

    # Sole scoring boundary: no target crop exists before all traces above.
    target_ids = _ids(atoms, EVAL_CENTER, TARGET_RADIUS)
    target_species = tuple(atoms.symbols[index] for index in target_ids)
    target_positions = tuple(atoms.positions[index] for index in target_ids)
    target_keys = {_site_key(site, .03)
                   for site in zip(target_species, target_positions)}
    seed_keys = {_site_key(site, .03) for site in seed_sites}
    primitive_final = {_site_key(site, .03)
                       for site in primitive_execution.sites}
    primitive_proposed = primitive_final - seed_keys
    primitive_correct = primitive_proposed.intersection(target_keys)
    macro_scores = {level: score_recurrent_macro_execution(
        execution, target_species, target_positions)
                    for level, execution in macro_executions}
    exact_unions = [_primitive_exact_union(
        primitive_execution, target_keys)] + [
            _macro_exact_union(execution, target_keys)
            for _level, execution in macro_executions]
    # Matched-work comparisons exist only when at least one hierarchical arm
    # can actually run.  A primitive-only result must not manufacture a
    # comparison budget from its own exact actions.
    common = min(map(len, exact_unions)) if macro_executions else 0
    primitive_arm = GrowthArm(
        "primitive-port", 0, True, len(primitive_enumeration.occurrences),
        _digest_primitive(primitive_execution),
        sum(len(wave.candidates) for wave in primitive_execution.waves),
        len(primitive_execution.accepted_candidate_ids),
        len(primitive_proposed), len(primitive_correct),
        len(primitive_proposed - target_keys),
        len(primitive_correct) / max(1, len(primitive_proposed)),
        len(primitive_correct) / max(1, len(target_keys - seed_keys)),
        _primitive_work(primitive_execution, target_keys, common)
        if common else None, primitive_execution.target_used, "")
    arms = [primitive_arm]
    for level, execution in macro_executions:
        score = macro_scores[level]
        arms.append(GrowthArm(
            f"macro-L{level}", level, True,
            next(seed_occurrences[index] for index in range(
                len(seed_occurrences)) if index + 1 == level),
            hashlib.sha256(repr(tuple(
                item.candidate_digest for item in execution.waves)
            ).encode()).hexdigest(), len(execution.eligible_candidates),
            len(execution.accepted), score.proposed_novel_atoms,
            score.correct_novel_atoms, score.wrong_novel_atoms,
            score.precision, score.recall_outside_seed,
            _macro_work(execution, target_keys, common) if common else None,
            execution.target_used_for_proposals_or_ranking, ""))
    executable = {level for level, _execution in macro_executions}
    for level in range(1, 5):
        if level not in executable:
            count = seed_occurrences[level - 1] \
                if level <= len(seed_occurrences) else 0
            arms.append(GrowthArm(
                f"macro-L{level}", level, False, count, "", 0, 0,
                0, 0, 0, 0., 0., None, False,
                "seed-only frozen matching produced no exact macro "
                "occurrence at this level"))
    minimum_separation = min(math.dist(EVAL_CENTER, center)
                             for center in TRAIN_CENTERS)
    missing = tuple(level for level in range(1, 5)
                    if level not in executable)
    blocker = ("none: L1-L4 have exact seed-only occurrences and target-blind "
               "executor APIs" if not missing else
               "seed recognition blocker at levels " +
               ",".join(map(str, missing)) +
               ": the four-level full-target re-encoding cannot supply an "
               "autonomous seed because those level occurrences require "
               "atoms outside the observed radius-14 nucleus")
    unclipped = all(abs(EVAL_CENTER[axis]) + TARGET_RADIUS <= 60.
                    for axis in range(3))
    return CdYbHierarchicalGrowthDesign(
        TRAIN_CENTERS, EVAL_CENTER, TRAIN_RADIUS, SEED_RADIUS, TARGET_RADIUS,
        len(train_positions), len(seed_ids), len(target_ids),
        len(train_ids.intersection(target_ids)), minimum_separation,
        minimum_separation > TRAIN_RADIUS + TARGET_RADIUS, unclipped,
        len(frozen_levels), tuple(seed_active), tuple(seed_occurrences),
        tuple(sorted(executable)), tuple(sorted(
            arms, key=lambda item: item.hierarchy_level)), common, True,
        all(len(item.frozen_candidate_digest) == 64
            for item in arms if item.executable), True,
        any(item.target_used_during_compile_or_execution for item in arms),
        blocker, True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
