#!/usr/bin/env python3
"""Check that recursive crystal growth expands consensus motifs, not defects."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import FrozenSet, Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_parametric_recursive import apply_rule, discover_rule
from materials_gcts_periodic_growth import replicate

Site = Tuple[Tuple[int, int, int], str]


@dataclass(frozen=True)
class DefectCase:
    defect: str
    observed_atoms: int
    grown_atoms: int
    expected_atoms: int
    discovered_family: str
    consensus_motif_atoms: int
    exact_position_species_set: bool
    defect_copies: int


@dataclass(frozen=True)
class DefectLocalityBenchmark:
    cases: Tuple[DefectCase, ...]
    passed: int
    total: int


def _sites(configuration: AtomicConfiguration) -> FrozenSet[Site]:
    return frozenset((blind._site_key(point), chemical)
                     for point, chemical in zip(configuration.positions,
                                                configuration.species))


def _finite(configuration: AtomicConfiguration, positions=None, species=None):
    return AtomicConfiguration(
        configuration.name,
        tuple(configuration.positions if positions is None else positions),
        tuple(configuration.species if species is None else species),
        None, False, configuration.provenance)


def _evaluate(defect, observed, expected, diagnostic_species) -> DefectCase:
    rule = discover_rule(observed)
    grown = apply_rule(observed, rule)
    actual = _sites(grown)
    return DefectCase(
        defect, len(observed.positions), len(grown.positions), len(expected),
        rule.family, len(rule.translation_motif), actual == expected,
        sum(chemical == diagnostic_species for _, chemical in actual))


def evaluate() -> DefectLocalityBenchmark:
    periodic = next(configuration for configuration in benchmark_systems()
                    if configuration.name == "NaCl-rocksalt")
    clean = _finite(periodic)
    expected_clean = replicate(periodic)
    clean_sites = set(_sites(expected_clean))
    index = len(clean.positions) // 2
    position = clean.positions[index]
    chemical = clean.species[index]
    site = blind._site_key(position)

    vacancy_positions = list(clean.positions)
    vacancy_species = list(clean.species)
    vacancy_positions.pop(index)
    vacancy_species.pop(index)
    vacancy_expected = clean_sites - {(site, chemical)}
    vacancy = _evaluate(
        "vacancy", _finite(clean, vacancy_positions, vacancy_species),
        frozenset(vacancy_expected), "__absent__")

    substitution_species = list(clean.species)
    substitution_species[index] = "K"
    substitution_expected = clean_sites - {(site, chemical)} | {(site, "K")}
    substitution = _evaluate(
        "substitution", _finite(clean, species=substitution_species),
        frozenset(substitution_expected), "K")

    interstitial_position = (1.11, 1.23, 1.37)
    interstitial = _finite(
        clean, clean.positions + (interstitial_position,),
        clean.species + ("Xe",))
    interstitial_expected = clean_sites | {
        (blind._site_key(interstitial_position), "Xe")}
    interstitial_result = _evaluate(
        "interstitial", interstitial, frozenset(interstitial_expected), "Xe")

    cases = (vacancy, substitution, interstitial_result)
    passed = sum(case.discovered_family == "translation_quotient" and
                 case.exact_position_species_set and case.defect_copies <= 1
                 for case in cases)
    return DefectLocalityBenchmark(cases, passed, len(cases))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
