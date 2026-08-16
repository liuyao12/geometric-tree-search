#!/usr/bin/env python3
"""Train-only recurrent-core hierarchy and sealed Cd--Yb re-encoding."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import RADIUS, TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import HELDOUT_CENTERS
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_frozen_hierarchy_transfer import (
    FrozenTransferLevel, transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import _frozen_heldout_program
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_core_selector import (
    filter_quotient_by_recurrent_core, select_recurrent_macro_core)


@dataclass(frozen=True)
class CdYbRecurrentCoreTransferAudit:
    training_patch_ids: tuple[int, ...]
    heldout_patch_ids: tuple[int, ...]
    training_atoms: int
    heldout_atoms: int
    raw_domains_pairwise_disjoint: bool
    frozen_support_types: int
    heldout_recognized_support_occurrences: int
    frozen_positive_levels: int
    raw_types_by_level: tuple[int, ...]
    selected_types_by_level: tuple[int, ...]
    majority_thresholds_by_level: tuple[int, ...]
    training_residual_atoms_by_level: tuple[int, ...]
    training_complete_representation_by_level: tuple[bool, ...]
    attempted_transfer_levels: int
    certified_recursive_transfer_depth: int
    transferred_levels: tuple[FrozenTransferLevel, ...]
    selected_equals_transferred_by_level: tuple[bool, ...]
    minimum_independent_occurrences_by_level: tuple[int, ...]
    minimum_distinct_namespaces_by_level: tuple[int, ...]
    transferred_occurrences_by_level: tuple[int, ...]
    atom_coverage_by_level: tuple[float, ...]
    residual_atoms_by_level: tuple[int, ...]
    complete_representation_by_level: tuple[bool, ...]
    exact_replay_by_level: tuple[bool, ...]
    frozen_ids_and_ports_preserved: bool
    stopped_reason: str
    heldout_reencoding: bool
    autonomous_growth: bool
    heldout_used_for_selection_or_refit: bool


def _windows(atoms, centers):
    return tuple(tuple(index for index, point in enumerate(atoms.positions)
                       if math.dist(center, point) <= RADIUS + 1e-10)
                 for center in centers)


def _pack(atoms, centers, windows, namespace_offset=0):
    species = []
    positions = []
    namespaces = []
    separation = 80.0
    for patch, (center, indices) in enumerate(zip(centers, windows)):
        for index in indices:
            point = atoms.positions[index]
            species.append(atoms.symbols[index])
            positions.append((point[0] - center[0] + patch * separation,
                              point[1] - center[1], point[2] - center[2]))
            namespaces.append(namespace_offset + patch)
    return tuple(species), tuple(positions), tuple(namespaces)


def evaluate(maximum_nodes=3, maximum_levels=12):
    if not 2 <= maximum_nodes <= 5 or maximum_levels < 1:
        raise ValueError("invalid hierarchy bounds")
    atoms = generate_cdyb(5, (80.0,) * 3)
    train_windows = _windows(atoms, TRAIN_CENTERS)
    held_windows = _windows(atoms, HELDOUT_CENTERS)
    all_windows = train_windows + held_windows
    raw_disjoint = all(set(left).isdisjoint(right)
                       for index, left in enumerate(all_windows)
                       for right in all_windows[index + 1:])
    train_ids = tuple(range(len(TRAIN_CENTERS)))
    held_ids = tuple(range(len(TRAIN_CENTERS),
                           len(TRAIN_CENTERS) + len(HELDOUT_CENTERS)))
    train_species, train_positions, train_patch = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    held_species, held_positions, held_patch = _pack(
        atoms, HELDOUT_CENTERS, held_windows, len(TRAIN_CENTERS))

    train = compile_irregular_port_program(train_species, train_positions)
    held_enumeration = enumerate_frozen_port_occurrences(
        train, held_species, held_positions)
    held = _frozen_heldout_program(train, held_enumeration)

    frozen_levels = []
    selections = []
    artifact = train
    for level in range(maximum_levels):
        mined = mine_port_graph_macros(
            artifact, maximum_nodes=maximum_nodes,
            include_boundary_relations=True)
        raw_quotient = quotient_macro_supports(mined.macro_types)
        if not raw_quotient.quotient_macros:
            break
        selection = select_recurrent_macro_core(
            raw_quotient.quotient_macros, train_species, train_positions,
            train_patch, training_patch_ids=train_ids)
        quotient = filter_quotient_by_recurrent_core(raw_quotient, selection)
        selections.append(selection)
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            artifact, quotient.quotient_macros, level=level + 1)
        frozen_levels.append((quotient, promoted))
        artifact = promoted

    audits = []
    held_sites = tuple(zip(held_species, held_positions))
    held_artifact = held
    stopped = "frozen training hierarchy exhausted"
    for quotient, promoted in frozen_levels:
        step = transfer_frozen_hierarchy_level(
            held_artifact, quotient, promoted, held_patch,
            raw_atom_sites=held_sites)
        audits.append(step.audit)
        held_artifact = step.program
        if not step.audit.every_frozen_type_transferred:
            stopped = ("fail-closed: not every frozen type has two disjoint "
                       "occurrences in two heldout namespaces")
            break

    return CdYbRecurrentCoreTransferAudit(
        train_ids, held_ids, len(train_species), len(held_species),
        raw_disjoint, len(train.vocabulary.prototypes),
        held_enumeration.recognized_support_occurrences,
        len(frozen_levels),
        tuple(len(item.input_macro_ids) for item in selections),
        tuple(len(item.selected_macro_ids) for item in selections),
        tuple(item.strict_majority_threshold for item in selections),
        tuple(len(item.residual_atom_terminals) for item in selections),
        tuple(item.complete_atom_representation for item in selections),
        len(audits), sum(item.every_frozen_type_transferred for item in audits),
        tuple(audits),
        tuple(item.frozen_types == item.transferred_types for item in audits),
        tuple(item.minimum_independent_occurrences_per_frozen_type
              for item in audits),
        tuple(item.minimum_distinct_namespaces_per_frozen_type
              for item in audits),
        tuple(item.occurrences for item in audits),
        tuple(item.coverage for item in audits),
        tuple(item.explicit_residual_atoms for item in audits),
        tuple(item.complete_representation_certificate for item in audits),
        tuple(item.exact_replay for item in audits),
        all(item.frozen_type_ids_preserved and
            item.admitted_overlap_semantics_only and
            item.admitted_boundary_semantics_only for item in audits),
        stopped, True, False, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maximum-nodes", type=int, default=3)
    parser.add_argument("--maximum-levels", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.maximum_nodes, arguments.maximum_levels)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
