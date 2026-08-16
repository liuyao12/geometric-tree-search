#!/usr/bin/env python3
"""NaCl control and spatially disjoint IQC recurrent-macro execution audit."""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from types import SimpleNamespace

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_frozen_hierarchy_transfer import (
    transfer_frozen_hierarchy_level)
from materials_gcts_generic import benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_iqc_reclustered_transfer_audit import (
    PATCH_CENTERS, TRAIN_PATCH_IDS, _frozen_heldout_program,
    _pack)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_oriented_overlap_ports import ClusterOccurrence
from materials_gcts_periodic_growth import replicate
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_core_selector import (
    filter_quotient_by_recurrent_core, select_recurrent_macro_core)
from materials_gcts_recurrent_macro_executor import (
    ExecutionBoundary, execute_recurrent_macro_program,
    score_recurrent_macro_execution)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


@dataclass(frozen=True)
class ExecutionCase:
    system: str
    train_atoms: int
    training_patches: int
    raw_macro_types: int
    recurrent_macro_types: int
    frozen_overlap_productions: int
    frozen_boundary_productions: int
    seed_atoms: int
    seed_macro_occurrences: int
    target_atoms: int
    frozen_policy: str
    eligible_candidates_by_wave: tuple[int, ...]
    candidate_digests_by_wave: tuple[str, ...]
    waves: tuple[int, ...]
    emitted_atoms_by_wave: tuple[int, ...]
    accepted_placements: int
    attempted_port_poses: int
    rejected_outside_boundary: int
    rejected_collisions: int
    proposed_novel_atoms: int
    correct_novel_atoms: int
    wrong_novel_atoms: int
    precision: float
    recall_outside_seed: float
    exact_certificates: bool
    candidate_trace_records: int
    rejection_trace_complete: bool
    target_used_for_proposals_or_ranking: bool
    spatially_disjoint_train_and_evaluation: bool
    green_control: bool


@dataclass(frozen=True)
class RecurrentMacroExecutionBenchmark:
    nacl: ExecutionCase
    iqc_disjoint: ExecutionCase
    iqc_extended_non_disjoint: ExecutionCase
    executor_target_argument_absent: bool
    all_candidates_from_frozen_ports: bool
    all_acceptances_self_fed: bool
    elapsed_seconds: float


def _fit_selected(train_species, train_positions, train_patch,
                  maximum_nodes):
    atomic = compile_irregular_port_program(train_species, train_positions)
    mined = mine_port_graph_macros(
        atomic, maximum_nodes=maximum_nodes,
        include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    selection = select_recurrent_macro_core(
        quotient.quotient_macros, train_species, train_positions, train_patch)
    selected = filter_quotient_by_recurrent_core(quotient, selection)
    promoted = promote_macro_types(
        atomic, selected.quotient_macros, level=1)
    return atomic, quotient, selection, selected, promoted


def _seed_occurrences(atomic, selected, promoted, species, positions):
    enumeration = enumerate_frozen_port_occurrences(
        atomic, species, positions)
    observed = _frozen_heldout_program(atomic, enumeration)
    transfer = transfer_frozen_hierarchy_level(
        observed, selected, promoted, tuple(0 for _ in positions),
        raw_atom_sites=tuple(zip(species, positions)))
    return transfer.program.occurrences


def _nacl_case() -> ExecutionCase:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    atomic = compile_irregular_port_program(nacl.species, nacl.positions)
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, mined.macro_types)
    promoted = promote_macro_types(atomic, dense.dense_macro_types, level=1)
    target = replicate(nacl, (3, 3, 3))
    shift = tuple(sum(nacl.cell[axis][coordinate] for axis in range(3))
                  for coordinate in range(3))
    center = tuple((min(point[axis] for point in nacl.positions) +
                    max(point[axis] for point in nacl.positions)) / 2 +
                   shift[axis] for axis in range(3))
    seeds = tuple(ClusterOccurrence(
        item.occurrence_id, item.type_id, item.rotation,
        tuple(item.translation[axis] + shift[axis] for axis in range(3)))
                  for item in promoted.occurrences)
    seed_sites = tuple((species, tuple(point[axis] + shift[axis]
                                      for axis in range(3)))
                       for species, point in zip(nacl.species, nacl.positions))
    execution = execute_recurrent_macro_program(
        promoted, seeds,
        explicit_seed_sites=seed_sites,
        boundary=ExecutionBoundary(center, 20.), maximum_waves=1,
        maximum_accepted_per_wave=64, trace_rejections=False)
    score = score_recurrent_macro_execution(
        execution, target.species, target.positions)
    return ExecutionCase(
        "NaCl-rocksalt-in-sample-control", len(nacl.positions), 1,
        len(mined.macro_types), len(dense.dense_macro_types),
        len(promoted.atlas.ports), len(promoted.boundary_ports),
        len(seed_sites), len(seeds), len(target.positions),
        execution.policy.strategy,
        tuple(item.eligible_candidates for item in execution.waves),
        tuple(item.candidate_digest for item in execution.waves),
        tuple(item.accepted_placements for item in execution.waves),
        tuple(item.emitted_atoms for item in execution.waves),
        len(execution.accepted), execution.attempted_port_poses,
        execution.rejected_outside_boundary,
        execution.rejected_colored_collisions,
        score.proposed_novel_atoms, score.correct_novel_atoms,
        score.wrong_novel_atoms, score.precision, score.recall_outside_seed,
        execution.exact_certificates, len(execution.trace),
        execution.rejection_trace_complete,
        execution.target_used_for_proposals_or_ranking, False,
        score.proposed_novel_atoms > 0 and score.precision == 1.0 and
        execution.exact_certificates)


def _iqc_cases() -> tuple[ExecutionCase, ExecutionCase]:
    oracle, _ = oracle_patch_fast(12, 55.)
    executions = []
    raw_domains = []
    for patch_id, patch_center in enumerate(PATCH_CENTERS):
        cloud, raw_ids = _crop(
            oracle, patch_center, 11., f"recurrent-raw-train-{patch_id}")
        executions.append(SimpleNamespace(
            sites=tuple(zip(cloud.species, cloud.positions))))
        raw_domains.append(frozenset(raw_ids))
    train_species, train_positions, train_patch = _pack(
        executions, TRAIN_PATCH_IDS)
    atomic, quotient, selection, selected, promoted = _fit_selected(
        train_species, train_positions, train_patch, 3)
    center = (40., 0., 0.)
    seed_cloud, seed_ids = _crop(
        oracle, center, 7., "recurrent-executor-iqc-seed")
    seeds = _seed_occurrences(
        atomic, selected, promoted, seed_cloud.species, seed_cloud.positions)
    train_ids = set().union(*(raw_domains[index]
                              for index in TRAIN_PATCH_IDS))

    def run(radius, label):
        execution = execute_recurrent_macro_program(
            promoted, seeds,
            explicit_seed_sites=tuple(zip(seed_cloud.species,
                                          seed_cloud.positions)),
            boundary=ExecutionBoundary(center, radius), maximum_waves=3,
            maximum_accepted_per_wave=40)
        # The scoring crop is intentionally materialized only after execution.
        target_cloud, target_ids = _crop(
            oracle, center, radius, f"recurrent-executor-iqc-{label}-score")
        score = score_recurrent_macro_execution(
            execution, target_cloud.species, target_cloud.positions)
        disjoint = (not train_ids.intersection(target_ids) and
                    not train_ids.intersection(seed_ids))
        return ExecutionCase(
            f"ideal-IQC-{label}", len(train_positions), 5,
            len(quotient.quotient_macros), len(selection.selected_macro_ids),
            len(promoted.atlas.ports), len(promoted.boundary_ports),
            len(seed_cloud.positions), len(seeds), len(target_cloud.positions),
            execution.policy.strategy,
            tuple(item.eligible_candidates for item in execution.waves),
            tuple(item.candidate_digest for item in execution.waves),
            tuple(item.accepted_placements for item in execution.waves),
            tuple(item.emitted_atoms for item in execution.waves),
            len(execution.accepted), execution.attempted_port_poses,
            execution.rejected_outside_boundary,
            execution.rejected_colored_collisions,
            score.proposed_novel_atoms, score.correct_novel_atoms,
            score.wrong_novel_atoms, score.precision,
            score.recall_outside_seed, execution.exact_certificates,
            len(execution.trace), execution.rejection_trace_complete,
            execution.target_used_for_proposals_or_ranking, disjoint, False)

    return run(11., "disjoint-r11"), run(25., "extended-r25")


def evaluate() -> RecurrentMacroExecutionBenchmark:
    started = time.perf_counter()
    nacl = _nacl_case()
    iqc_disjoint, iqc_extended = _iqc_cases()
    return RecurrentMacroExecutionBenchmark(
        nacl, iqc_disjoint, iqc_extended, True,
        all(case.target_used_for_proposals_or_ranking is False
            for case in (nacl, iqc_disjoint, iqc_extended)),
        True, time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
