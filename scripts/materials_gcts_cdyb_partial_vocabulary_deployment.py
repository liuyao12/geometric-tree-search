#!/usr/bin/env python3
"""Partial frozen-vocabulary deployment on reserved Cd--Yb windows.

All train-frozen symbols and ports remain available at every level.  A finite
heldout corpus may instantiate only a subset; absent symbols are dormant, not
renumbered or declared transferred.  Higher matching uses only exact active
child occurrences and immutable frozen relations.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    HELDOUT_CENTERS, _pack, _window_ids)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_frozen_hierarchy_transfer import (
    transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import (
    _frozen_heldout_program)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports


@dataclass(frozen=True)
class PartialVocabularyLevel:
    level: int
    frozen_types: int
    active_types: int
    dormant_types: int
    active_type_ids: tuple[int, ...]
    dormant_type_ids: tuple[int, ...]
    occurrences: int
    occurrence_multiplicity_histogram: tuple[tuple[int, int], ...]
    active_namespace_count_histogram: tuple[tuple[int, int], ...]
    minimum_active_namespaces: int
    minimum_active_atom_independent_occurrences: int
    covered_atoms: int
    residual_atoms: int
    atom_coverage: float
    exact_replay: bool
    complete_representation_certificate: bool
    frozen_type_ids_retained: bool
    frozen_overlap_ports_retained: bool
    frozen_boundary_ports_retained: bool
    admitted_relations_only: bool


@dataclass(frozen=True)
class CdYbPartialVocabularyDeployment:
    train_windows: int
    heldout_windows: int
    train_atoms: int
    heldout_atoms: int
    train_heldout_raw_id_intersection: int
    frozen_levels: int
    attempted_levels: int
    positive_active_depth: int
    levels: tuple[PartialVocabularyLevel, ...]
    active_types_by_level: tuple[int, ...]
    dormant_types_by_level: tuple[int, ...]
    occurrences_by_level: tuple[int, ...]
    atom_coverage_by_level: tuple[float, ...]
    residual_atoms_by_level: tuple[int, ...]
    stopped_reason: str
    dormant_types_claimed_transferred: bool
    vocabulary_refit_or_renumbered_on_heldout: bool
    heldout_reencoding_only: bool
    autonomous_growth_or_emission: bool
    all_exact_certificates: bool
    leakage_safe_partial_deployment: bool


def _active_evidence(program, atom_namespaces):
    occurrence = {item.occurrence_id: item for item in program.occurrences}
    by_type = {}
    for occurrence_id, support in program.occurrence_supports:
        by_type.setdefault(occurrence[occurrence_id].type_id, []).append(
            frozenset(support))
    namespace_counts = []
    independent_counts = []
    for supports in by_type.values():
        namespace_counts.append(len({atom_namespaces[next(iter(support))]
                                     for support in supports if support}))
        chosen = []
        for support in sorted(supports, key=lambda value:
                              (len(value), tuple(value))):
            if all(support.isdisjoint(prior) for prior in chosen):
                chosen.append(support)
        independent_counts.append(len(chosen))
    return (tuple(namespace_counts), tuple(independent_counts))


def evaluate(maximum_levels: int = 12):
    if maximum_levels < 1:
        raise ValueError("maximum_levels must be positive")
    atoms = generate_cdyb(5, (80.0,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    held_windows = _window_ids(atoms, HELDOUT_CENTERS)
    train_ids = set().union(*map(set, train_windows))
    held_ids = set().union(*map(set, held_windows))
    train_species, train_positions, _train_patch = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    held_species, held_positions, held_patch = _pack(
        atoms, HELDOUT_CENTERS, held_windows)
    raw_sites = tuple(zip(held_species, held_positions))
    train = compile_irregular_port_program(train_species, train_positions)
    frozen_levels = []
    train_artifact = train
    for level in range(maximum_levels):
        mined = mine_port_graph_macros(
            train_artifact, maximum_nodes=3,
            include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            train_artifact, quotient.quotient_macros, level=level + 1)
        frozen_levels.append((quotient, promoted))
        train_artifact = promoted

    enumeration = enumerate_frozen_port_occurrences(
        train, held_species, held_positions)
    held_artifact = _frozen_heldout_program(train, enumeration)
    reports = []
    stopped = "frozen training hierarchy exhausted"
    for quotient, frozen in frozen_levels:
        step = transfer_frozen_hierarchy_level(
            held_artifact, quotient, frozen, held_patch,
            raw_atom_sites=raw_sites)
        audit = step.audit
        active = {item.type_id for item in step.program.occurrences}
        frozen_ids = {item.type_id for item in frozen.prototypes}
        dormant = frozen_ids - active
        namespace_counts, independent_counts = _active_evidence(
            step.program, held_patch)
        reports.append(PartialVocabularyLevel(
            audit.level, len(frozen_ids), len(active), len(dormant),
            tuple(sorted(active)), tuple(sorted(dormant)), audit.occurrences,
            tuple(sorted(Counter(dict(
                audit.occurrence_multiplicity_by_type).values()).items())),
            tuple(sorted(Counter(namespace_counts).items())),
            min(namespace_counts, default=0),
            min(independent_counts, default=0), audit.covered_atoms,
            audit.explicit_residual_atoms, audit.coverage,
            audit.exact_replay, audit.complete_representation_certificate,
            step.program.prototype_macro_types ==
            frozen.prototype_macro_types,
            step.program.atlas.ports == frozen.atlas.ports,
            step.program.boundary_ports == frozen.boundary_ports,
            audit.admitted_overlap_semantics_only and
            audit.admitted_boundary_semantics_only))
        held_artifact = step.program
        if not step.program.occurrences:
            stopped = "no active exact occurrences can seed the next level"
            break

    positive_depth = sum(item.occurrences > 0 for item in reports)
    exact = all(
        item.exact_replay and item.complete_representation_certificate and
        item.frozen_type_ids_retained and
        item.frozen_overlap_ports_retained and
        item.frozen_boundary_ports_retained and item.admitted_relations_only
        for item in reports)
    return CdYbPartialVocabularyDeployment(
        len(TRAIN_CENTERS), len(HELDOUT_CENTERS), len(train_positions),
        len(held_positions), len(train_ids.intersection(held_ids)),
        len(frozen_levels), len(reports), positive_depth, tuple(reports),
        tuple(item.active_types for item in reports),
        tuple(item.dormant_types for item in reports),
        tuple(item.occurrences for item in reports),
        tuple(item.atom_coverage for item in reports),
        tuple(item.residual_atoms for item in reports), stopped,
        False, False, True, False, exact,
        exact and len(train_ids.intersection(held_ids)) == 0)


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
