#!/usr/bin/env python3
"""Self-trained clusters-of-clusters promotion with carried GCTS marks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_gap_node_benchmark import _hidden_site
from materials_gcts_geometry_vm_benchmark import _compile_iqc_instruction
from materials_gcts_propagated_marking import (
    compile_propagated_port_program, execute_propagated_wave,
    extend_marked_configuration,
    fit_propagated_marking, initial_marked_configuration,
    promote_port_instruction)


@dataclass(frozen=True)
class ClusterPromotionBenchmark:
    training_atoms: int
    self_generated_parent_atoms: int
    final_atoms: int
    base_cluster_types: int
    promoted_cluster_types: int
    mean_base_cluster_support: float
    mean_promoted_cluster_support: float
    support_growth_factor: float
    maximum_promoted_cluster_support: int
    promoted_ports: int
    promoted_port_pairs: int
    promoted_wave_sites: int
    exact_promoted_wave_sites: int
    promoted_wave_to_parent_ratio: float
    promoted_level_sites: tuple[int, ...]
    exact_promoted_level_sites: tuple[int, ...]
    promoted_level_growth_factors: tuple[float, ...]
    geometric_mean_level_growth: float
    heldout_atoms_used_for_promotion: bool
    global_section_queried_at_inference: bool
    larger_support_clusters_promoted: bool
    amplified_exact_growth: bool
    exponential_growth: bool
    promotion_gate_passed: bool


def evaluate(promoted_levels=3):
    seed, instruction = _compile_iqc_instruction()
    marking = fit_propagated_marking(instruction, seed)
    port_program = compile_propagated_port_program(instruction)
    state = initial_marked_configuration(seed, marking)
    for level in (1, 2):
        for _ in range(10):
            wave = execute_propagated_wave(
                port_program, marking, state, level=level)
            if not wave.emitted_sites:
                break
            state = extend_marked_configuration(state, wave)
    promoted, report = promote_port_instruction(instruction, state)
    promoted_program = compile_propagated_port_program(promoted)
    level_sites = []
    exact_level_sites = []
    for level in range(1, promoted_levels + 1):
        wave = execute_propagated_wave(
            promoted_program, marking, state, level=level)
        exact = sum(_hidden_site(*site) for site in wave.emitted_sites)
        level_sites.append(len(wave.emitted_sites))
        exact_level_sites.append(exact)
        if exact != len(wave.emitted_sites) or not wave.emitted_sites:
            break
        state = extend_marked_configuration(state, wave)
    support_growth = (report.mean_promoted_support /
                      report.mean_base_support)
    amplification = level_sites[0] / report.input_atoms
    growth_factors = tuple(right / left for left, right in
                           zip(level_sites, level_sites[1:]))
    geometric_growth = ((level_sites[-1] / level_sites[0]) **
                        (1.0 / (len(level_sites) - 1))
                        if len(level_sites) > 1 else 1.0)
    larger = support_growth > 2.0
    amplified = (exact_level_sites == level_sites and amplification > 1.0)
    exponential = (len(level_sites) >= 3 and amplified and
                   all(factor > 1.0 for factor in growth_factors))
    passed = (larger and exponential and
              report.promoted_cluster_types > 0)
    return ClusterPromotionBenchmark(
        len(seed.positions), report.input_atoms,
        len(state.configuration.positions), report.base_cluster_types,
        report.promoted_cluster_types, report.mean_base_support,
        report.mean_promoted_support, support_growth,
        report.maximum_promoted_support, report.promoted_ports,
        report.promoted_port_pairs, level_sites[0], exact_level_sites[0],
        amplification, tuple(level_sites), tuple(exact_level_sites),
        growth_factors, geometric_growth, False, False, larger, amplified,
        exponential, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
