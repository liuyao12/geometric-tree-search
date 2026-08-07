#!/usr/bin/env python3
"""Frontier-defect benchmark for hierarchical residual GCTS growth."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_hierarchical_residual import (
    _hidden_configuration, apply_defect_aware_rule, learn_defect_aware_rule)


@dataclass(frozen=True)
class FrontierDefectCase:
    defect: str
    input_atoms: int
    output_atoms: int
    missing_residuals: int
    added_residuals: int
    defect_instances_after_growth: int
    naive_parent_copy_instances: int
    exact_position_species_set: bool


@dataclass(frozen=True)
class FrontierDefectBenchmark:
    cases: Tuple[FrontierDefectCase, ...]
    output_parent_atoms: int
    recursive_actions: int
    passed: int
    total: int


def _sites(configuration):
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def _replace(configuration, positions, species):
    return AtomicConfiguration(
        configuration.name, tuple(positions), tuple(species), None, False,
        configuration.provenance)


def _cell_atom_index(side, cell, motif_index=0):
    i, j, k = cell
    return ((i * side + j) * side + k) * 2 + motif_index


def _evaluate_case(name, observed, expected, diagnostic_species,
                   expected_instances):
    rule = learn_defect_aware_rule(observed)
    grown = apply_defect_aware_rule(rule, 2)
    instances = sum(chemical == diagnostic_species
                    for chemical in grown.species)
    if diagnostic_species == "__vacancy__":
        instances = len(rule.missing_sites)
    return FrontierDefectCase(
        name, len(observed.positions), len(grown.positions),
        len(rule.missing_sites), len(rule.added_atoms), instances, 64,
        _sites(grown) == _sites(expected) and instances == expected_instances)


def evaluate() -> FrontierDefectBenchmark:
    training = _hidden_configuration(8)
    target = _hidden_configuration(32)

    vacancy_index = _cell_atom_index(8, (7, 7, 6), 0)
    vacancy_position = training.positions[vacancy_index]
    vacancy_species = training.species[vacancy_index]
    positions = list(training.positions)
    species = list(training.species)
    positions.pop(vacancy_index)
    species.pop(vacancy_index)
    vacancy_observed = _replace(training, positions, species)
    target_positions = list(target.positions)
    target_species = list(target.species)
    target_index = next(index for index, (point, chemical) in enumerate(zip(
        target_positions, target_species))
                        if blind._site_key(point) == blind._site_key(vacancy_position)
                        and chemical == vacancy_species)
    target_positions.pop(target_index)
    target_species.pop(target_index)
    vacancy_expected = _replace(target, target_positions, target_species)

    substitution_index = _cell_atom_index(8, (7, 0, 7), 0)
    substitution_position = training.positions[substitution_index]
    substitution_species = list(training.species)
    substitution_species[substitution_index] = "K"
    substitution_observed = _replace(
        training, training.positions, substitution_species)
    target_species = list(target.species)
    target_index = next(index for index, point in enumerate(target.positions)
                        if blind._site_key(point) ==
                        blind._site_key(substitution_position) and
                        target.species[index] == "Ni")
    target_species[target_index] = "K"
    substitution_expected = _replace(target, target.positions, target_species)

    anchor = training.positions[_cell_atom_index(8, (7, 4, 4), 1)]
    interstitial_position = (anchor[0] + 0.31, anchor[1] - 0.17,
                             anchor[2] + 0.23)
    interstitial_observed = _replace(
        training, training.positions + (interstitial_position,),
        training.species + ("Xe",))
    interstitial_expected = _replace(
        target, target.positions + (interstitial_position,),
        target.species + ("Xe",))

    cases = (
        _evaluate_case("frontier-vacancy", vacancy_observed,
                       vacancy_expected, "__vacancy__", 1),
        _evaluate_case("frontier-substitution", substitution_observed,
                       substitution_expected, "K", 1),
        _evaluate_case("frontier-interstitial", interstitial_observed,
                       interstitial_expected, "Xe", 1),
    )
    passed = sum(case.exact_position_species_set for case in cases)
    return FrontierDefectBenchmark(cases, len(target.positions), 2,
                                   passed, len(cases))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
