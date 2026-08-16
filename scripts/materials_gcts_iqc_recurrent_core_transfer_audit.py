#!/usr/bin/env python3
"""Sealed first-level transfer audit for the train recurrent macro core."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_iqc_reclustered_transfer_audit import (
    HELDOUT_PATCH_IDS, TRAIN_PATCH_IDS, _frozen_heldout_program,
    _grow_patches, _pack)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_core_selector import select_recurrent_macro_core


@dataclass(frozen=True)
class IQCRecurrentCoreTransferAudit:
    training_patches: int
    heldout_patches: int
    strict_majority_threshold: int
    train_quotient_types: int
    selected_recurrent_types: int
    rejected_nonrecurrent_types: int
    selected_type_ids_preserved: bool
    patch2_only_train_type_ids: tuple[int, ...]
    patch2_only_types_rejected: bool
    rare_primitive49_type_ids: tuple[int, ...]
    rare_primitive49_types_rejected: bool
    train_atoms: int
    selected_train_covered_atoms: int
    exact_residual_atom_terminals: int
    residual_atom_indices: tuple[int, ...]
    train_representation_certificate_digest: str
    complete_train_representation: bool
    heldout_atoms: int
    selected_types_with_two_exact_heldout_occurrences: int
    selected_type_transfer_coverage: float
    heldout_exact_macro_occurrences: int
    heldout_atoms_covered_by_selected_types: int
    heldout_atom_coverage: float
    exact_proper_se3_replay: bool
    all_selected_types_transfer_with_two_occurrences: bool
    selector_read_heldout: bool
    target_family_phi_cell_labels_used: bool
    elapsed_seconds: float


def evaluate(maximum_nodes: int = 3) -> IQCRecurrentCoreTransferAudit:
    started = time.perf_counter()
    executions, _ = _grow_patches()
    train_species, train_positions, train_patch = _pack(
        executions, TRAIN_PATCH_IDS)

    # Everything through selection is fitted strictly before the heldout atom
    # union is even materialized in this function.
    training = compile_irregular_port_program(train_species, train_positions)
    mined = mine_port_graph_macros(
        training, maximum_nodes=maximum_nodes,
        include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    selection = select_recurrent_macro_core(
        quotient.quotient_macros, train_species, train_positions, train_patch,
        training_patch_ids=TRAIN_PATCH_IDS)
    evidence = {item.macro_id: item for item in selection.evidence}
    patch2_only = tuple(sorted(
        macro_id for macro_id, item in evidence.items()
        if item.patch_ids == (2,)))
    rare_primitive49 = tuple(sorted(
        macro.macro_id for macro in quotient.quotient_macros
        if 49 in macro.node_types))

    held_species, held_positions, _ = _pack(executions, HELDOUT_PATCH_IDS)
    held_enumeration = enumerate_frozen_port_occurrences(
        training, held_species, held_positions)
    held_program = _frozen_heldout_program(training, held_enumeration)
    replay = match_dense_macro_types(
        held_program, selection.selected_macros)
    counts = tuple(len(item.promotion_occurrences)
                   for item in replay.dense_macro_types)
    atoms = {index for macro in replay.dense_macro_types
             for occurrence in macro.promotion_occurrences
             for index in occurrence.atom_indices}
    transferred = sum(value >= 2 for value in counts)
    selected_ids = set(selection.selected_macro_ids)
    return IQCRecurrentCoreTransferAudit(
        len(TRAIN_PATCH_IDS), len(HELDOUT_PATCH_IDS),
        selection.strict_majority_threshold, len(quotient.quotient_macros),
        len(selection.selected_macro_ids), len(selection.rejected_macro_ids),
        selection.original_macro_ids_preserved, patch2_only,
        all(item not in selected_ids for item in patch2_only),
        rare_primitive49,
        all(item not in selected_ids for item in rare_primitive49),
        len(train_positions), len(selection.selected_covered_atom_indices),
        len(selection.residual_atom_terminals),
        tuple(item.atom_index for item in selection.residual_atom_terminals),
        selection.representation_certificate_digest,
        selection.complete_atom_representation, len(held_positions),
        transferred, transferred / max(1, len(selection.selected_macro_ids)),
        sum(counts), len(atoms), len(atoms) / max(1, len(held_positions)),
        replay.every_dense_match_proper,
        transferred == len(selection.selected_macro_ids), False, False,
        time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maximum-nodes", type=int, default=3,
                        choices=(3, 4, 5))
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.maximum_nodes)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
