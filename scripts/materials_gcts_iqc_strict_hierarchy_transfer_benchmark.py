#!/usr/bin/env python3
"""Sealed IQC benchmark for strict frozen recursive hierarchy transfer."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass

from materials_gcts_frozen_hierarchy_transfer import (
    FrozenTransferLevel, transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import (
    HELDOUT_PATCH_IDS, TRAIN_PATCH_IDS, _frozen_heldout_program, _grow_patches,
    _pack)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_core_selector import (
    filter_quotient_by_recurrent_core, select_recurrent_macro_core)


@dataclass(frozen=True)
class StrictHierarchyTransferBenchmark:
    train_patch_ids: tuple[int, ...]
    heldout_patch_ids: tuple[int, ...]
    train_atoms: int
    heldout_atoms: int
    frozen_positive_levels: int
    train_raw_types_by_level: tuple[int, ...]
    train_recurrent_types_by_level: tuple[int, ...]
    train_majority_domain_thresholds_by_level: tuple[int, ...]
    train_residual_atoms_by_level: tuple[int, ...]
    train_complete_representation_by_level: tuple[bool, ...]
    attempted_levels: int
    transferred_levels: tuple[FrozenTransferLevel, ...]
    transferred_types_by_level: tuple[int, ...]
    transferred_occurrences_by_level: tuple[int, ...]
    atom_coverage_by_level: tuple[float, ...]
    gap_atoms_by_level: tuple[int, ...]
    exact_replay_by_level: tuple[bool, ...]
    patch_namespaces_preserved: bool
    all_type_maps_frozen: bool
    all_relations_train_admitted: bool
    stopped_reason: str
    heldout_reencoding: bool
    autonomous_growth: bool
    heldout_used_for_fit_admission_or_branch_selection: bool
    target_labels_used: bool
    family_phi_cell_used: bool
    elapsed_seconds: float


def evaluate(maximum_nodes: int = 5, maximum_levels: int = 8):
    if not 2 <= maximum_nodes <= 5 or maximum_levels < 1:
        raise ValueError("invalid hierarchy bounds")
    started = time.perf_counter()
    executions, _raw_domains = _grow_patches()
    train_species, train_positions, train_patch = _pack(
        executions, TRAIN_PATCH_IDS)
    held_species, held_positions, held_patch = _pack(
        executions, HELDOUT_PATCH_IDS)

    train = compile_irregular_port_program(train_species, train_positions)
    held_enumeration = enumerate_frozen_port_occurrences(
        train, held_species, held_positions)
    held = _frozen_heldout_program(train, held_enumeration)

    frozen_levels = []
    selections = []
    train_artifact = train
    for level in range(maximum_levels):
        mined = mine_port_graph_macros(
            train_artifact, maximum_nodes=maximum_nodes,
            include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        if not quotient.quotient_macros:
            break
        selection = select_recurrent_macro_core(
            quotient.quotient_macros, train_species, train_positions,
            train_patch, training_patch_ids=TRAIN_PATCH_IDS)
        quotient = filter_quotient_by_recurrent_core(quotient, selection)
        selections.append(selection)
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            train_artifact, quotient.quotient_macros, level=level + 1)
        frozen_levels.append((quotient, promoted))
        train_artifact = promoted

    audits = []
    held_sites = tuple(zip(held_species, held_positions))
    held_artifact = held
    stopped = "frozen training hierarchy exhausted"
    for quotient, frozen_promoted in frozen_levels:
        step = transfer_frozen_hierarchy_level(
            held_artifact, quotient, frozen_promoted, held_patch,
            raw_atom_sites=held_sites)
        audits.append(step.audit)
        held_artifact = step.program
        if not step.audit.every_frozen_type_transferred:
            stopped = ("fail-closed: a selected frozen type lacks two "
                       "atom-independent occurrences or two heldout "
                       "namespaces")
            break

    namespace_ok = all(
        len({held_patch[atom] for atom in support}) == 1
        for _occurrence, support in held_artifact.occurrence_supports)
    return StrictHierarchyTransferBenchmark(
        TRAIN_PATCH_IDS, HELDOUT_PATCH_IDS, len(train_positions),
        len(held_positions), len(frozen_levels),
        tuple(len(item.input_macro_ids) for item in selections),
        tuple(len(item.selected_macro_ids) for item in selections),
        tuple(item.strict_majority_threshold for item in selections),
        tuple(len(item.residual_atom_terminals) for item in selections),
        tuple(item.complete_atom_representation for item in selections),
        len(audits), tuple(audits),
        tuple(item.transferred_types for item in audits),
        tuple(item.occurrences for item in audits),
        tuple(item.coverage for item in audits),
        tuple(item.gap_atoms for item in audits),
        tuple(item.exact_replay for item in audits), namespace_ok,
        all(item.frozen_type_ids_preserved for item in audits),
        all(item.admitted_overlap_semantics_only and
            item.admitted_boundary_semantics_only for item in audits),
        stopped, True, False, False, False, False,
        time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maximum-nodes", type=int, default=5)
    parser.add_argument("--maximum-levels", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.maximum_nodes, arguments.maximum_levels)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
