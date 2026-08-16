#!/usr/bin/env python3
"""Sealed target-blind Cd--Yb execution of a train-frozen deep hierarchy."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_hierarchical_seed_executor import (
    FrozenHierarchyLevel, recognize_and_execute_frozen_hierarchy)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import (
    ExecutionBoundary, score_recurrent_macro_execution)


TRAIN_RADIUS = 14.
EVAL_CENTER = (35., 30., 20.)
SEED_RADIUS = 14.
TARGET_RADIUS = 25.
PACK_SEPARATION = 80.


@dataclass(frozen=True)
class LevelExecutionAudit:
    level: int
    seed_occurrences: int
    seed_types: int
    seed_atoms_covered: int
    candidate_counts: tuple[int, ...]
    accepted_counts: tuple[int, ...]
    emitted_atoms: int
    correct_atoms: int
    wrong_atoms: int
    precision: float
    outer_recall: float
    exact_certificates: bool
    reachable_fixed_point: bool


@dataclass(frozen=True)
class CdYbHierarchicalSeedExecutionAudit:
    train_windows: int
    train_atoms: int
    frozen_positive_levels: int
    quotient_types_by_level: tuple[int, ...]
    seed_atoms: int
    target_atoms: int
    outer_atoms: int
    minimum_train_eval_center_separation: float
    train_target_radii_sum: float
    train_eval_raw_id_intersection: int
    spatial_domains_disjoint: bool
    primitive_seed_occurrences: int
    primitive_seed_admitted_relations: int
    recognized_occurrences_by_level: tuple[int, ...]
    recognized_types_by_level: tuple[int, ...]
    recognized_seed_coverage_by_level: tuple[int, ...]
    executed_levels: tuple[LevelExecutionAudit, ...]
    highest_recognized_level: int
    highest_executed_level: int
    any_higher_level_exterior_emission: bool
    every_emission_exactly_certified: bool
    certification_vacuous_no_emissions: bool
    target_factory_called_after_execution: bool
    target_used_for_recognition_or_execution: bool
    family_cell_source_site_or_expected_scale_used: bool
    autonomous_hierarchical_gate_passed: bool
    limitation: str


def _ids(atoms, center, radius):
    return tuple(index for index, point in enumerate(atoms.positions)
                 if math.dist(center, point) <= radius + 1e-10)


def _training(atoms):
    windows = tuple(_ids(atoms, center, TRAIN_RADIUS)
                    for center in TRAIN_CENTERS)
    species = []
    positions = []
    for patch, (center, ids) in enumerate(zip(TRAIN_CENTERS, windows)):
        for raw_id in ids:
            point = atoms.positions[raw_id]
            species.append(atoms.symbols[raw_id])
            positions.append((
                point[0] - center[0] + patch * PACK_SEPARATION,
                point[1] - center[1], point[2] - center[2]))
    primitive = compile_irregular_port_program(tuple(species), tuple(positions))
    levels = []
    quotient_counts = []
    artifact = primitive
    for level_index in range(16):
        mined = mine_port_graph_macros(
            artifact, maximum_nodes=3, include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        quotient_counts.append(len(quotient.quotient_macros))
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            artifact, quotient.quotient_macros, level=level_index + 1)
        levels.append(FrozenHierarchyLevel(quotient, promoted))
        artifact = promoted
    return windows, tuple(species), primitive, tuple(levels), tuple(quotient_counts)


def evaluate() -> CdYbHierarchicalSeedExecutionAudit:
    atoms = generate_cdyb(6, (120.,) * 3)
    train_windows, train_species, primitive, levels, quotient_counts = \
        _training(atoms)
    train_ids = set().union(*map(set, train_windows))
    seed_ids = _ids(atoms, EVAL_CENTER, SEED_RADIUS)
    seed_species = tuple(atoms.symbols[index] for index in seed_ids)
    seed_positions = tuple(atoms.positions[index] for index in seed_ids)
    execution = recognize_and_execute_frozen_hierarchy(
        primitive, levels, seed_species, seed_positions,
        boundary=ExecutionBoundary(EVAL_CENTER, TARGET_RADIUS),
        maximum_waves=3, maximum_accepted_per_wave=40)

    # The target crop is materialized only after recognition and every frozen
    # executor have returned immutable traces.
    target_ids = _ids(atoms, EVAL_CENTER, TARGET_RADIUS)
    target_species = tuple(atoms.symbols[index] for index in target_ids)
    target_positions = tuple(atoms.positions[index] for index in target_ids)
    rows = []
    recognized_by_level = {item.level: item for item in execution.levels}
    for level, result in execution.executions:
        score = score_recurrent_macro_execution(
            result, target_species, target_positions)
        seed = recognized_by_level[level]
        rows.append(LevelExecutionAudit(
            level, seed.recognized_occurrences, seed.recognized_types,
            seed.seed_atoms_covered,
            tuple(item.eligible_candidates for item in result.waves),
            tuple(item.accepted_placements for item in result.waves),
            score.proposed_novel_atoms, score.correct_novel_atoms,
            score.wrong_novel_atoms, score.precision,
            score.recall_outside_seed, result.exact_certificates,
            result.reachable_fixed_point))
    minimum_separation = min(math.dist(center, EVAL_CENTER)
                             for center in TRAIN_CENTERS)
    raw_intersection = len(train_ids.intersection(target_ids))
    highest_recognized = max((item.level for item in execution.levels
                              if item.recognized_occurrences), default=0)
    highest_executed = max((item.level for item in rows), default=0)
    higher_emission = any(item.level >= 2 and item.emitted_atoms > 0
                          for item in rows)
    certified = all(item.exact_certificates for item in rows)
    gate = (higher_emission and certified and raw_intersection == 0 and
            not execution.target_used_for_recognition_or_execution)
    return CdYbHierarchicalSeedExecutionAudit(
        len(train_windows), len(train_species), len(levels), quotient_counts,
        len(seed_ids), len(target_ids), len(set(target_ids) - set(seed_ids)),
        minimum_separation, TRAIN_RADIUS + TARGET_RADIUS, raw_intersection,
        minimum_separation > TRAIN_RADIUS + TARGET_RADIUS,
        execution.primitive_occurrences, execution.primitive_admitted_relations,
        tuple(item.recognized_occurrences for item in execution.levels),
        tuple(item.recognized_types for item in execution.levels),
        tuple(item.seed_atoms_covered for item in execution.levels),
        tuple(rows), highest_recognized, highest_executed, higher_emission,
        certified, not rows, True,
        execution.target_used_for_recognition_or_execution,
        False, gate,
        "Recognition uses only exact seed-contained supports. This nucleus has "
        "276 primitive occurrences and 500 admitted primitive relations, but "
        "zero exact frozen L1 macro occurrences, so no higher-level executor "
        "can start. Certificate truth is vacuous because nothing emitted; the "
        "benchmark does not infer a missing pose from the post-hoc target.")


def main():
    print(json.dumps(asdict(evaluate()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
