#!/usr/bin/env python3
"""Self-trained clusters-of-clusters promotion with carried GCTS marks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_gap_node_benchmark import _hidden_site
from materials_gcts_geometry_vm_benchmark import _compile_iqc_instruction
from materials_gcts_propagated_marking import (
    execute_propagated_wave, extend_marked_configuration,
    fit_propagated_marking, initial_marked_configuration,
    promote_port_instruction)


@dataclass(frozen=True)
class ClusterPromotionBenchmark:
    training_atoms: int
    self_generated_parent_atoms: int
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
    heldout_atoms_used_for_promotion: bool
    global_section_queried_at_inference: bool
    larger_support_clusters_promoted: bool
    amplified_exact_growth: bool
    exponential_growth: bool
    promotion_gate_passed: bool


def evaluate():
    seed, instruction = _compile_iqc_instruction()
    marking = fit_propagated_marking(instruction, seed)
    state = initial_marked_configuration(seed, marking)
    for level in (1, 2):
        for _ in range(10):
            wave = execute_propagated_wave(
                instruction, marking, state, level=level)
            if not wave.emitted_sites:
                break
            state = extend_marked_configuration(state, wave)
    promoted, report = promote_port_instruction(instruction, state)
    wave = execute_propagated_wave(
        promoted, marking, state, level=1)
    exact = sum(_hidden_site(*site) for site in wave.emitted_sites)
    support_growth = (report.mean_promoted_support /
                      report.mean_base_support)
    amplification = len(wave.emitted_sites) / report.input_atoms
    larger = support_growth > 2.0
    amplified = exact == len(wave.emitted_sites) and amplification > 1.0
    passed = larger and amplified and report.promoted_cluster_types > 0
    return ClusterPromotionBenchmark(
        len(seed.positions), report.input_atoms, report.base_cluster_types,
        report.promoted_cluster_types, report.mean_base_support,
        report.mean_promoted_support, support_growth,
        report.maximum_promoted_support, report.promoted_ports,
        report.promoted_port_pairs, len(wave.emitted_sites), exact,
        amplification, False, False, larger, amplified, False, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
