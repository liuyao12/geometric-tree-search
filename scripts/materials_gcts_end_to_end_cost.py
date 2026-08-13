#!/usr/bin/env python3
"""Measured learning, representation, counting, and emission costs for GCTS."""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from typing import Callable, Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_2d_generic_atlas import _score, layered_hexagonal_configuration
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_periodic_growth import replicate
from materials_gcts_recursive_program import (
    discover_recursive_program, explicit_apply, fast_actions_to_at_least,
    symbolic_count)


@dataclass(frozen=True)
class EndToEndCostCase:
    system: str
    observed_atoms: int
    selected_program: str
    learning_seconds: float
    explicit_two_level_atoms: int
    explicit_two_level_seconds: float
    explicit_two_level_exact: bool
    million_action: int
    fast_represented_atoms: int
    fast_count_exact: bool
    fast_count_seconds: float
    exact_audit_atoms: int
    exact_audit_seconds: float
    fast_count_relative_error: float
    primitive_cluster_atoms: int
    flat_primitive_actions: int
    recursive_actions: int
    action_compression: float
    explicit_output_is_linear: bool


@dataclass(frozen=True)
class EndToEndCostBenchmark:
    cases: Tuple[EndToEndCostCase, ...]
    all_two_level_outputs_exact: bool
    all_reach_million_with_six_actions: bool
    all_action_compressions_above_ten_thousand: bool
    finite_graph_counts_exact: bool
    iqc_fast_count_is_estimate: bool
    iqc_fast_count_error_below_one_percent: bool
    exact_iqc_counting_is_linear_enumeration: bool
    no_md_speed_claim: bool
    benchmark_passed: bool


def _sites(configuration: AtomicConfiguration) -> set[tuple]:
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def _case(configuration: AtomicConfiguration,
          references: Callable[[object], Tuple[AtomicConfiguration, ...]],
          planar: bool = False) -> EndToEndCostCase:
    started = time.perf_counter()
    program = discover_recursive_program(configuration)
    learning_seconds = time.perf_counter() - started

    started = time.perf_counter()
    explicit = tuple(explicit_apply(configuration, program, action)
                     for action in (1, 2))
    explicit_seconds = time.perf_counter() - started
    expected = references(program)
    exact = (all(_score(actual, target) == (1.0, 1.0, 1.0)
                 for actual, target in zip(explicit, expected)) if planar else
             all(_sites(actual) == _sites(target)
                 for actual, target in zip(explicit, expected)))

    started = time.perf_counter()
    action, fast = fast_actions_to_at_least(configuration, program)
    fast_seconds = time.perf_counter() - started
    started = time.perf_counter()
    audited = symbolic_count(configuration, program, action)
    audit_seconds = time.perf_counter() - started
    error = abs(fast.atoms - audited) / audited
    flat = math.ceil(max(0, audited - len(configuration.positions)) /
                     program.primitive_cluster_atoms)
    return EndToEndCostCase(
        configuration.name, len(configuration.positions), program.family,
        learning_seconds, len(explicit[-1].positions), explicit_seconds,
        exact, action, fast.atoms, fast.exact, fast_seconds, audited,
        audit_seconds, error, program.primitive_cluster_atoms, flat, action,
        flat / action, True)


def evaluate() -> EndToEndCostBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    iqc, _ = oracle_patch(3, 9.0)
    fibonacci = make_input(9)
    basis = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    angles = (0.0, math.pi / 6)
    planar = layered_hexagonal_configuration(
        "cost-30deg-hBN", 18.0, basis, angles, global_rotation=True)

    def nacl_refs(_):
        first = replicate(nacl)
        return first, replicate(first)

    def iqc_refs(program):
        scale = program._payload.scale
        return (oracle_patch(4, 9.0 * scale)[0],
                oracle_patch(6, 9.0 * scale ** 2)[0])

    def fib_refs(_):
        return make_input(15), make_input(24)

    def planar_refs(program):
        return tuple(layered_hexagonal_configuration(
            f"cost-hBN-target-{action}",
            program.observation_radius * 2 ** action,
            basis, angles, global_rotation=True) for action in (1, 2))

    cases = (_case(nacl, nacl_refs), _case(iqc, iqc_refs),
             _case(fibonacci, fib_refs),
             _case(planar, planar_refs, True))
    exact = all(case.explicit_two_level_exact for case in cases)
    actions = all(case.million_action <= 6 for case in cases)
    compressed = all(case.action_compression > 10_000 for case in cases)
    finite_exact = all(case.fast_count_exact for case in
                       (cases[0], cases[2], cases[3]))
    iqc_estimate = not cases[1].fast_count_exact
    iqc_accurate = cases[1].fast_count_relative_error < .01
    return EndToEndCostBenchmark(
        cases, exact, actions, compressed, finite_exact, iqc_estimate,
        iqc_accurate, True, True,
        exact and actions and compressed and finite_exact and iqc_estimate and
        iqc_accurate)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
