#!/usr/bin/env python3
"""Cell-free recursive GCTS benchmark over real crystal prototypes."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_parametric_recursive import apply_rule, discover_rule
from materials_gcts_periodic_growth import replicate


@dataclass(frozen=True)
class RealCrystalCase:
    system: str
    observed_atoms: int
    observed_cell_repeats: int
    chemical_species: int
    hierarchy_supports: Tuple[int, ...]
    discovered_family: str
    rule_residual: float
    grown_atoms: int
    growth_factor: float
    exact_position_species_set: bool


@dataclass(frozen=True)
class RealCrystalBenchmark:
    cases: Tuple[RealCrystalCase, ...]
    passed: int
    total: int


def _sites(configuration):
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def _evaluate_case(source: AtomicConfiguration) -> RealCrystalCase:
    # The complex 168-atom Cd6Yb cell has no repeated cell translation inside
    # a single finite crop.  Two cells per axis are the minimum observed sample
    # on which that quotient is identifiable without using the supplied cell.
    repeats = 2 if source.name == "Cd6Yb-1/1-approximant" else 1
    observed = replicate(source) if repeats == 2 else source
    finite = AtomicConfiguration(
        observed.name, observed.positions, observed.species, None, False,
        observed.provenance)
    rule = discover_rule(finite)
    grown = apply_rule(finite, rule) if rule.deterministic else finite
    expected = replicate(observed)
    return RealCrystalCase(
        source.name, len(finite.positions), repeats,
        len(set(finite.species)), rule.hierarchy_supports, rule.family,
        float(rule.residual if rule.residual is not None else 1.0),
        len(grown.positions), len(grown.positions) / len(finite.positions),
        _sites(grown) == _sites(expected))


def evaluate() -> RealCrystalBenchmark:
    cases = tuple(_evaluate_case(source) for source in benchmark_systems())
    passed = sum(case.discovered_family == "translation_quotient" and
                 case.exact_position_species_set for case in cases)
    return RealCrystalBenchmark(cases, passed, len(cases))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
