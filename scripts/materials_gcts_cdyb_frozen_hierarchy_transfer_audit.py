#!/usr/bin/env python3
"""Exact frozen-hierarchy re-encoding on two reserved Cd--Yb windows.

The five training windows alone define every primitive type, port, macro,
quotient, and promoted prototype.  Both heldout radius-14 atom clouds are
fully observed before matching, so this audit is transfer/re-encoding only;
it is not autonomous emission or material growth.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import (
    RADIUS, TRAIN_CENTERS)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_frozen_hierarchy_transfer import (
    FrozenTransferLevel, transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import (
    _frozen_heldout_program)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports


HELDOUT_CENTERS = ((5.0, 15.0, 5.0), (20.0, 15.0, -20.0))
PACK_SEPARATION = 80.0


@dataclass(frozen=True)
class CdYbFrozenHierarchyTransferAudit:
    train_windows: int
    heldout_windows: int
    train_atoms: int
    heldout_atoms: int
    heldout_atoms_by_window: tuple[int, ...]
    train_heldout_raw_id_intersection: int
    heldout_raw_domains_disjoint: bool
    spatial_domains_disjoint: bool
    frozen_positive_levels: int
    selected_types_by_level: tuple[int, ...]
    attempted_levels: int
    transferred_levels: tuple[FrozenTransferLevel, ...]
    transferred_types_by_level: tuple[int, ...]
    occurrences_by_level: tuple[int, ...]
    covered_atoms_by_level: tuple[int, ...]
    atom_coverage_by_level: tuple[float, ...]
    residual_atoms_by_level: tuple[int, ...]
    minimum_namespaces_by_level: tuple[int, ...]
    minimum_independent_occurrences_by_level: tuple[int, ...]
    exact_replay_by_level: tuple[bool, ...]
    complete_representation_by_level: tuple[bool, ...]
    namespaces_preserved: bool
    stopped_reason: str
    heldout_reencoding_only: bool
    autonomous_growth_or_emission: bool
    heldout_used_for_fit_admission_or_branch_selection: bool
    source_sites_family_cell_or_expected_scale_used: bool
    elapsed_seconds: float


def _window_ids(atoms, centers):
    return tuple(tuple(index for index, point in enumerate(atoms.positions)
                       if math.dist(center, point) <= RADIUS + 1e-10)
                 for center in centers)


def _pack(atoms, centers, windows):
    species = []
    positions = []
    namespaces = []
    for namespace, (center, raw_ids) in enumerate(zip(centers, windows)):
        for raw_id in raw_ids:
            point = atoms.positions[raw_id]
            species.append(atoms.symbols[raw_id])
            positions.append((
                point[0] - center[0] + namespace * PACK_SEPARATION,
                point[1] - center[1], point[2] - center[2]))
            namespaces.append(namespace)
    return tuple(species), tuple(positions), tuple(namespaces)


def evaluate(maximum_levels: int = 12):
    if maximum_levels < 1:
        raise ValueError("maximum_levels must be positive")
    started = time.perf_counter()
    atoms = generate_cdyb(5, (80.0,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    held_windows = _window_ids(atoms, HELDOUT_CENTERS)
    train_ids = set().union(*map(set, train_windows))
    held_ids = set().union(*map(set, held_windows))
    train_species, train_positions, _train_namespaces = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    held_species, held_positions, held_namespaces = _pack(
        atoms, HELDOUT_CENTERS, held_windows)

    train = compile_irregular_port_program(train_species, train_positions)
    frozen_levels = []
    artifact = train
    for level in range(maximum_levels):
        mined = mine_port_graph_macros(
            artifact, maximum_nodes=3, include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            artifact, quotient.quotient_macros, level=level + 1)
        frozen_levels.append((quotient, promoted))
        artifact = promoted

    enumeration = enumerate_frozen_port_occurrences(
        train, held_species, held_positions)
    held_artifact = _frozen_heldout_program(train, enumeration)
    raw_sites = tuple(zip(held_species, held_positions))
    audits = []
    stopped = "frozen training hierarchy exhausted"
    for quotient, promoted in frozen_levels:
        step = transfer_frozen_hierarchy_level(
            held_artifact, quotient, promoted, held_namespaces,
            raw_atom_sites=raw_sites)
        audits.append(step.audit)
        held_artifact = step.program
        if not step.audit.every_frozen_type_transferred:
            stopped = (
                "fail-closed: at least one train-selected frozen type lacks "
                "two atom-independent occurrences in two heldout namespaces")
            break

    namespace_ok = all(
        len({held_namespaces[index] for index in support}) == 1
        for _occurrence, support in held_artifact.occurrence_supports)
    all_centers = TRAIN_CENTERS + HELDOUT_CENTERS
    spatial_disjoint = all(
        math.dist(left, right) > 2 * RADIUS
        for index, left in enumerate(all_centers)
        for right in all_centers[index + 1:])
    return CdYbFrozenHierarchyTransferAudit(
        len(TRAIN_CENTERS), len(HELDOUT_CENTERS), len(train_positions),
        len(held_positions), tuple(map(len, held_windows)),
        len(train_ids.intersection(held_ids)),
        set(held_windows[0]).isdisjoint(held_windows[1]), spatial_disjoint,
        len(frozen_levels),
        tuple(len(quotient.quotient_macros)
              for quotient, _promoted in frozen_levels),
        len(audits), tuple(audits),
        tuple(item.transferred_types for item in audits),
        tuple(item.occurrences for item in audits),
        tuple(item.covered_atoms for item in audits),
        tuple(item.coverage for item in audits),
        tuple(item.explicit_residual_atoms for item in audits),
        tuple(item.minimum_distinct_namespaces_per_frozen_type
              for item in audits),
        tuple(item.minimum_independent_occurrences_per_frozen_type
              for item in audits),
        tuple(item.exact_replay for item in audits),
        tuple(item.complete_representation_certificate for item in audits),
        namespace_ok, stopped, True, False, False, False,
        time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maximum-levels", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.maximum_levels)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
