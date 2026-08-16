#!/usr/bin/env python3
"""Train-evidence diagnosis for missing first-level Cd--Yb macro types."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from statistics import mean, median

from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    HELDOUT_CENTERS, _pack, _window_ids)
from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
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
from materials_gcts_recurrent_core_selector import (
    filter_quotient_by_recurrent_core, select_recurrent_macro_core)


@dataclass(frozen=True)
class TypeGroupSummary:
    types: int
    type_ids: tuple[int, ...]
    train_patch_prevalence_histogram: tuple[tuple[int, int], ...]
    train_occurrences: int
    support_size_min_median_max: tuple[float, float, float]
    mean_cd_atoms: float
    mean_yb_atoms: float
    mean_boundary_slots: float
    mean_boundary_slot_frequency: float
    mean_atom_coverage_redundancy: float
    mean_atom_fraction_covered_by_other_types: float


@dataclass(frozen=True)
class CdYbMissingTypeDiagnostic:
    frozen_types: int
    heldout_transferred_types: int
    missing_types: int
    transferred: TypeGroupSummary
    missing: TypeGroupSummary
    missing_train_atoms_not_covered_by_transferred_types: int
    missing_train_atom_fraction_not_covered_by_transferred_types: float
    missing_types_with_zero_unique_train_atoms: int
    strict_majority_threshold: int
    strict_majority_selected_types: int
    strict_majority_selected_ids: tuple[int, ...]
    strict_majority_train_covered_atoms: int
    strict_majority_train_residual_atoms: int
    strict_majority_heldout_transferred_types: int
    strict_majority_heldout_occurrences: int
    strict_majority_heldout_coverage: float
    strict_majority_heldout_residual_atoms: int
    strict_majority_every_type_transferred: bool
    strict_majority_minimum_namespaces: int
    strict_majority_minimum_independent_occurrences: int
    leakage_safe_rule_succeeds: bool
    conclusion: str


def _occurrences(macro):
    return macro.promotion_occurrences or macro.occurrences


def _atom_indices(macro):
    return {index for item in _occurrences(macro)
            for index in item.atom_indices}


def _summary(macros, train_patch, all_macros):
    if not macros:
        return TypeGroupSummary(0, (), (), 0, (0., 0., 0.), 0., 0.,
                                0., 0., 0., 0.)
    prevalence = []
    sizes = []
    cd = []
    yb = []
    slots = []
    frequencies = []
    redundancies = []
    cross_type_redundancies = []
    occurrences = 0
    for macro in macros:
        values = _occurrences(macro)
        occurrences += len(values)
        prevalence.append(len({train_patch[index]
                               for item in values
                               for index in item.atom_indices}))
        sizes.append(len(macro.atom_union))
        chemistry = Counter(species for species, _point in macro.atom_union)
        cd.append(chemistry.get("Cd", 0))
        yb.append(chemistry.get("Yb", 0))
        slots.append(len(macro.boundary_slots))
        frequencies.extend(item.frequency for item in macro.boundary_slots)
        total = sum(len(item.atom_indices) for item in values)
        unique = len(_atom_indices(macro))
        redundancies.append(total / max(1, unique))
        other_atoms = set().union(*(
            _atom_indices(other) for other in all_macros
            if other.macro_id != macro.macro_id))
        cross_type_redundancies.append(
            len(_atom_indices(macro).intersection(other_atoms)) /
            max(1, unique))
    return TypeGroupSummary(
        len(macros), tuple(sorted(item.macro_id for item in macros)),
        tuple(sorted(Counter(prevalence).items())), occurrences,
        (float(min(sizes)), float(median(sizes)), float(max(sizes))),
        mean(cd), mean(yb), mean(slots),
        mean(frequencies) if frequencies else 0., mean(redundancies),
        mean(cross_type_redundancies))


def evaluate():
    atoms = generate_cdyb(5, (80.0,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    held_windows = _window_ids(atoms, HELDOUT_CENTERS)
    train_species, train_positions, train_patch = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    held_species, held_positions, held_patch = _pack(
        atoms, HELDOUT_CENTERS, held_windows)
    train = compile_irregular_port_program(train_species, train_positions)
    mined = mine_port_graph_macros(
        train, maximum_nodes=3, include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    promoted = promote_macro_types(train, quotient.quotient_macros, level=1)
    enumeration = enumerate_frozen_port_occurrences(
        train, held_species, held_positions)
    held = _frozen_heldout_program(train, enumeration)
    full = transfer_frozen_hierarchy_level(
        held, quotient, promoted, held_patch,
        raw_atom_sites=tuple(zip(held_species, held_positions))).audit
    multiplicity = dict(full.occurrence_multiplicity_by_type)
    present_ids = {key for key, count in multiplicity.items() if count > 0}
    by_id = {item.macro_id: item for item in quotient.quotient_macros}
    present = tuple(by_id[key] for key in sorted(present_ids))
    missing = tuple(by_id[key] for key in sorted(set(by_id) - present_ids))
    present_atoms = set().union(*(_atom_indices(item) for item in present))
    missing_atoms = set().union(*(_atom_indices(item) for item in missing))
    additional = missing_atoms - present_atoms
    zero_unique = sum(not (_atom_indices(item) - present_atoms)
                      for item in missing)

    selection = select_recurrent_macro_core(
        quotient.quotient_macros, train_species, train_positions,
        train_patch, training_patch_ids=tuple(range(len(TRAIN_CENTERS))))
    selected_quotient = filter_quotient_by_recurrent_core(
        quotient, selection)
    selected_promoted = promote_macro_types(
        train, selected_quotient.quotient_macros, level=1)
    selected_transfer = transfer_frozen_hierarchy_level(
        held, selected_quotient, selected_promoted, held_patch,
        raw_atom_sites=tuple(zip(held_species, held_positions))).audit
    succeeds = (selected_transfer.every_frozen_type_transferred and
                selection.complete_atom_representation)
    return CdYbMissingTypeDiagnostic(
        len(by_id), len(present), len(missing),
        _summary(present, train_patch, quotient.quotient_macros),
        _summary(missing, train_patch, quotient.quotient_macros),
        len(additional), len(additional) / len(train_positions), zero_unique,
        selection.strict_majority_threshold,
        len(selection.selected_macro_ids), selection.selected_macro_ids,
        len(selection.selected_covered_atom_indices),
        len(selection.residual_atom_terminals),
        selected_transfer.transferred_types, selected_transfer.occurrences,
        selected_transfer.coverage, selected_transfer.explicit_residual_atoms,
        selected_transfer.every_frozen_type_transferred,
        selected_transfer.minimum_distinct_namespaces_per_frozen_type,
        selected_transfer.minimum_independent_occurrences_per_frozen_type,
        succeeds,
        "The strict-majority rule is fixed from five train namespaces only. "
        + ("It yields a completely represented, transferable recurrent core."
           if succeeds else
           "It still lacks two-window heldout support for at least one type; "
           "do not relax the transfer gate using heldout prevalence."))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
