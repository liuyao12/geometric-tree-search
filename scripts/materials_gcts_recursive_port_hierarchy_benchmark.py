#!/usr/bin/env python3
"""Real first-level audit of the injectable recursive hierarchy driver."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_recursive_port_hierarchy import (
    drive_recursive_port_hierarchy, real_first_level_callbacks)


@dataclass(frozen=True)
class RecursiveHierarchyCase:
    system: str
    atoms: int
    realized_levels: int
    first_level_source_types: int
    first_level_macro_types: int
    first_level_atom_supports: tuple[int, ...]
    first_level_production_types: int
    first_level_total_mdl_saving: int
    level_source_type_counts: tuple[int, ...]
    level_positive_macro_counts: tuple[int, ...]
    level_atom_supports: tuple[tuple[int, ...], ...]
    level_production_type_counts: tuple[int, ...]
    level_total_mdl_savings: tuple[int, ...]
    stationary_witnesses: int
    real_stationary_semantics_certified: bool
    termination_reason: str
    converged_no_positive_mdl: bool
    actual_promotion_available: bool
    constants_and_labels_unused: bool


def _case(configuration: AtomicConfiguration) -> RecursiveHierarchyCase:
    program = compile_irregular_port_program(
        configuration.species, configuration.positions)
    hierarchy = drive_recursive_port_hierarchy(
        program, real_first_level_callbacks())
    first = hierarchy.levels[0]
    return RecursiveHierarchyCase(
        configuration.name, len(configuration.positions),
        len(hierarchy.levels), first.source_type_count,
        first.positive_macro_types, first.atom_supports,
        first.production_type_count, first.total_mdl_saving,
        tuple(level.source_type_count for level in hierarchy.levels),
        tuple(level.positive_macro_types for level in hierarchy.levels),
        tuple(level.atom_supports for level in hierarchy.levels),
        tuple(level.production_type_count for level in hierarchy.levels),
        tuple(level.total_mdl_saving for level in hierarchy.levels),
        len(hierarchy.stationary_witnesses),
        any(level.certified_stationarity_signatures
            for level in hierarchy.levels), hierarchy.termination_reason,
        hierarchy.converged_no_positive_mdl, hierarchy.promotion_available,
        hierarchy.material_family_cell_scale_constants_unused)


def evaluate() -> tuple[RecursiveHierarchyCase, ...]:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    nacl = AtomicConfiguration(nacl.name, nacl.positions, nacl.species)
    iqc, _ = oracle_patch(3, 9.0)
    cdyb = build_cdyb_split().training
    return tuple(_case(item) for item in (nacl, iqc, cdyb))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps([asdict(item) for item in result], indent=2,
                     sort_keys=True) if arguments.json else result)


if __name__ == "__main__":
    main()
