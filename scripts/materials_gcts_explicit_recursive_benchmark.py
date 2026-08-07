#!/usr/bin/env python3
"""Materialized multi-action benchmark for learned recursive GCTS nodes."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import benchmark_systems
from materials_gcts_icosahedral_modelset import (
    HIDDEN_UNIT, HIDDEN_WINDOW, hidden_species, lift_point, oracle_patch,
    project, star_vectors, vector_norm)
from materials_gcts_parametric_recursive import (
    apply_rule_actions, discover_rule)
from materials_gcts_periodic_growth import replicate


@dataclass(frozen=True)
class ExplicitRecursiveCase:
    system: str
    family: str
    action_counts: Tuple[int, ...]
    atom_counts: Tuple[int, ...]
    exact_each_action: bool
    learned_rule_objects: int
    macro_actions: int
    atomwise_new_atom_actions: int
    action_compression: float


@dataclass(frozen=True)
class ExplicitRecursiveBenchmark:
    crystal: ExplicitRecursiveCase
    quasicrystal: ExplicitRecursiveCase
    substitution_quasicrystal: ExplicitRecursiveCase
    passed: int
    total: int


def _sites(configuration):
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def _case(configuration, expected, family, rule_objects):
    rule = discover_rule(configuration)
    grown = tuple(apply_rule_actions(configuration, rule, action)
                  for action in (0, 1, 2))
    exact = all(_sites(item) == _sites(reference)
                for item, reference in zip(grown, expected))
    generated = len(grown[-1].positions) - len(configuration.positions)
    return ExplicitRecursiveCase(
        configuration.name, rule.family, (0, 1, 2),
        tuple(len(item.positions) for item in grown), exact, rule_objects, 2,
        generated, generated / 2.0)


def _crystal_case():
    source = next(item for item in benchmark_systems()
                  if item.name == "NaCl-rocksalt")
    return _case(source, (source, replicate(source), replicate(replicate(source))),
                 "translation_quotient", 1)


def _iqc_case():
    source, _ = oracle_patch(3, 9.0)
    first, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    # A coefficient-box oracle would be expensive at this radius.  Certify the
    # independently generated second parent by lifting every atom back to the
    # hidden integer module and checking its learned internal-section marking.
    rule = discover_rule(source)
    grown = tuple(apply_rule_actions(source, rule, action)
                  for action in (0, 1, 2))
    internal_vectors = star_vectors(-1.0 / HIDDEN_UNIT)
    second_valid = True
    lifts = set()
    for point, chemical in zip(grown[2].positions, grown[2].species):
        lift, residual = lift_point(point, HIDDEN_UNIT)
        radius = vector_norm(project(lift, internal_vectors))
        second_valid &= (residual < 1e-5 and
                         radius <= HIDDEN_WINDOW + 1e-10 and
                         chemical == hidden_species(radius))
        lifts.add(lift)
    exact = (_sites(grown[0]) == _sites(source) and
             _sites(grown[1]) == _sites(first) and second_valid and
             len(lifts) == len(grown[2].positions) == 8603)
    generated = len(grown[2].positions) - len(source.positions)
    return ExplicitRecursiveCase(
        source.name, rule.family, (0, 1, 2),
        tuple(len(item.positions) for item in grown), exact, 1, 2, generated,
        generated / 2.0)


def _substitution_case():
    source = make_input(9)
    return _case(source, (source, make_input(15), make_input(24)),
                 "substitution_product", 2)


def evaluate() -> ExplicitRecursiveBenchmark:
    cases = (_crystal_case(), _iqc_case(), _substitution_case())
    passed = sum(case.family == expected and case.exact_each_action
                 for case, expected in zip(cases, (
                     "translation_quotient", "internal_section_inflation",
                     "substitution_product")))
    return ExplicitRecursiveBenchmark(*cases, passed, len(cases))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
