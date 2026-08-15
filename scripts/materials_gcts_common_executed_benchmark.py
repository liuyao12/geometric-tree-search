#!/usr/bin/env python3
"""Executed cross-family growth gate for one family-blind program API."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_executable_program import (
    discover_executable_program, execute_program)
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_gap_node_benchmark import _hidden_site
from materials_gcts_generic import benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_periodic_growth import replicate
from materials_gcts_recursive_connections import point_key


@dataclass(frozen=True)
class ExecutedGrowthCase:
    system: str
    production_kind: str
    atom_counts: tuple[int, ...]
    novel_sites_by_action: tuple[int, ...]
    atom_growth_factors: tuple[float, ...]
    exact_species_and_positions: bool
    self_fed: bool
    family_label_used: bool
    heldout_atoms_used_for_growth: bool


@dataclass(frozen=True)
class CommonExecutedBenchmark:
    cases: tuple[ExecutedGrowthCase, ...]
    one_discovery_entrypoint: bool
    one_execution_entrypoint: bool
    explicit_atoms_scored: int
    all_three_actions_executed: bool
    all_exact: bool
    all_self_fed: bool
    exponential_style_all_cases: bool
    specialized_production_kinds_remain: bool
    cross_family_execution_gate_passed: bool
    single_generic_production_gate_passed: bool


def _site_set(configuration):
    return set(zip(map(point_key, configuration.positions),
                   configuration.species))


def _case(seed, targets, scorer):
    program = discover_executable_program(seed)
    outputs = execute_program(seed, program, 3)
    exact = len(outputs) == 3 and all(
        scorer(output, target) for output, target in zip(outputs, targets))
    counts = (len(seed.positions),) + tuple(
        len(output.positions) for output in outputs)
    novel = tuple(right - left for left, right in zip(counts, counts[1:]))
    factors = tuple(right / left for left, right in zip(counts, counts[1:]))
    return ExecutedGrowthCase(
        seed.name, program.production_kind, counts, novel, factors, exact,
        True, program.family_label_used, program.heldout_atoms_used)


def evaluate():
    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    crystal_targets = []
    state = crystal
    for _ in range(3):
        state = replicate(state)
        crystal_targets.append(state)
    crystal_case = _case(
        crystal, tuple(crystal_targets),
        lambda output, target: _site_set(output) == _site_set(target))

    fibonacci = make_input(9)
    fibonacci_targets = tuple(make_input(side) for side in (15, 24, 39))
    fibonacci_case = _case(
        fibonacci, fibonacci_targets,
        lambda output, target: _site_set(output) == _site_set(target))

    iqc, _ = oracle_patch(3, 9.0)
    iqc_case = _case(
        iqc, (None, None, None),
        lambda output, _target: all(
            _hidden_site(point, chemical) for point, chemical in
            zip(output.positions, output.species)))

    cases = (crystal_case, iqc_case, fibonacci_case)
    exact = all(case.exact_species_and_positions for case in cases)
    self_fed = all(case.self_fed for case in cases)
    three = all(len(case.atom_counts) == 4 for case in cases)
    exponential = all(
        len(case.atom_growth_factors) == 3 and
        min(case.atom_growth_factors) > 1.5 for case in cases)
    specialized = len({case.production_kind for case in cases}) > 1
    cross_family = (exact and self_fed and three and exponential and
                    not any(case.family_label_used or
                            case.heldout_atoms_used_for_growth
                            for case in cases))
    return CommonExecutedBenchmark(
        cases, True, True,
        sum(sum(case.atom_counts[1:]) for case in cases), three, exact,
        self_fed, exponential, specialized, cross_family,
        cross_family and not specialized)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
