#!/usr/bin/env python3
"""Cross-polytype benchmark for generic molecular/gap GCTS discovery."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_ice_cover import IceConfiguration, ice_ic, ice_ih
from materials_gcts_molecular_gap_clusters import MolecularGapCover, learn_molecular_gap_cover


@dataclass(frozen=True)
class IceGenericCase:
    system: str
    atoms: int
    learned_formula: tuple[tuple[str, int], ...]
    molecular_occurrences: int
    molecular_isometry_classes: int
    connection_occurrences: int
    connection_isometry_classes: int
    void_boundary_occurrences: int
    void_boundary_isometry_classes: int
    inferred_component_degree_histogram: tuple[tuple[int, int], ...]
    inferred_void_size_histogram: tuple[tuple[int, int], ...]
    covered_atoms: int
    exact_cover: bool
    residual_atoms: int
    tree_actions: int
    commuting_wave_sizes: tuple[int, ...]
    tree_search_recall: float
    tree_search_backtracks: int
    material_label_used: bool
    expected_formula_used: bool
    expected_ring_size_used: bool
    physical_potential_used: bool


@dataclass(frozen=True)
class GenericIceBenchmark:
    cases: tuple[IceGenericCase, ...]
    molecule_signature_transfers_across_polytypes: bool
    void_signature_transfers_across_polytypes: bool
    shared_connection_isometry_classes: int
    ih_connection_isometry_classes: int
    ic_connection_isometry_classes: int
    same_generic_learner_both_polytypes: bool
    complete_molecule_connection_void_cover: bool
    benchmark_passed: bool


def _grow(cover: MolecularGapCover) -> tuple[int, tuple[int, ...], int]:
    adjacency = [set() for _ in cover.molecules]
    for occurrence in cover.connections:
        first, second = occurrence.components
        adjacency[first].add(second)
        adjacency[second].add(first)
    visited = {0}
    frontier = {0}
    waves = []
    actions = 0
    while frontier:
        additions = sorted(set().union(*(adjacency[index] for index in frontier)) - visited)
        if not additions:
            break
        # The displayed wave is an antichain of attachments.  Under the hood
        # each newly reached component is still one exact spanning-tree action.
        waves.append(len(additions))
        actions += len(additions)
        visited.update(additions)
        frontier = set(additions)
    covered = set().union(*(set(cover.molecules[index].members) for index in visited))
    return actions, tuple(waves), len(covered)


def _evaluate(configuration: IceConfiguration) -> tuple[IceGenericCase, MolecularGapCover]:
    cover = learn_molecular_gap_cover(
        configuration.species, configuration.positions, cell=configuration.cell)
    if not cover.molecules:
        raise AssertionError("molecular learner rejected an ice molecular crystal")
    formulas = {occurrence.formula for occurrence in cover.molecules}
    learned_formula = next(iter(formulas)) if len(formulas) == 1 else ()
    degrees = Counter()
    for component in range(len(cover.molecules)):
        degrees[sum(component in occurrence.components for occurrence in cover.connections)] += 1
    actions, waves, grown_atoms = _grow(cover)
    case = IceGenericCase(
        system=configuration.name,
        atoms=len(configuration.positions),
        learned_formula=learned_formula,
        molecular_occurrences=len(cover.molecules),
        molecular_isometry_classes=cover.molecule_type_count,
        connection_occurrences=len(cover.connections),
        connection_isometry_classes=cover.connection_type_count,
        void_boundary_occurrences=len(cover.void_boundaries),
        void_boundary_isometry_classes=cover.void_type_count,
        inferred_component_degree_histogram=tuple(sorted(degrees.items())),
        inferred_void_size_histogram=tuple(sorted(Counter(
            len(occurrence.components) for occurrence in cover.void_boundaries).items())),
        covered_atoms=cover.covered_atoms,
        exact_cover=cover.covered_atoms == len(configuration.positions) and not cover.residual_atoms,
        residual_atoms=len(cover.residual_atoms),
        tree_actions=actions,
        commuting_wave_sizes=waves,
        tree_search_recall=grown_atoms / len(configuration.positions),
        tree_search_backtracks=0,
        material_label_used=cover.material_label_used,
        expected_formula_used=cover.expected_formula_used,
        expected_ring_size_used=cover.expected_ring_size_used,
        physical_potential_used=False,
    )
    return case, cover


def evaluate() -> GenericIceBenchmark:
    ih_case, ih_cover = _evaluate(ice_ih())
    ic_case, ic_cover = _evaluate(ice_ic())
    ih_molecules = {occurrence.signature for occurrence in ih_cover.molecules}
    ic_molecules = {occurrence.signature for occurrence in ic_cover.molecules}
    ih_voids = {occurrence.signature for occurrence in ih_cover.void_boundaries}
    ic_voids = {occurrence.signature for occurrence in ic_cover.void_boundaries}
    ih_connections = {occurrence.signature for occurrence in ih_cover.connections}
    ic_connections = {occurrence.signature for occurrence in ic_cover.connections}
    cases = (ih_case, ic_case)
    complete = all(case.exact_cover and case.tree_search_recall == 1
                   and case.molecular_isometry_classes == 1
                   and case.void_boundary_isometry_classes == 1
                   for case in cases)
    passed = (complete and ih_molecules == ic_molecules and ih_voids == ic_voids
              and len(ih_connections & ic_connections) > 0
              and all(not case.material_label_used and not case.expected_formula_used
                      and not case.expected_ring_size_used and not case.physical_potential_used
                      for case in cases))
    return GenericIceBenchmark(
        cases=cases,
        molecule_signature_transfers_across_polytypes=ih_molecules == ic_molecules,
        void_signature_transfers_across_polytypes=ih_voids == ic_voids,
        shared_connection_isometry_classes=len(ih_connections & ic_connections),
        ih_connection_isometry_classes=len(ih_connections),
        ic_connection_isometry_classes=len(ic_connections),
        same_generic_learner_both_polytypes=True,
        complete_molecule_connection_void_cover=complete,
        benchmark_passed=passed,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
