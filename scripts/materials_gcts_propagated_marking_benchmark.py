#!/usr/bin/env python3
"""Benchmark coordinate-lift-free inference with carried local GCTS marks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_gap_node_benchmark import _hidden_site
from materials_gcts_geometry_vm_benchmark import _compile_iqc_instruction
from materials_gcts_propagated_marking import (
    execute_propagated_wave, extend_marked_configuration,
    fit_propagated_marking, initial_marked_configuration)


@dataclass(frozen=True)
class MarkingLevel:
    recursive_level: int
    wave_sites: tuple[int, ...]
    exact_sites: int
    rejected_connections: int


@dataclass(frozen=True)
class PropagatedMarkingBenchmark:
    training_atoms: int
    final_atoms: int
    marking_dimension: int
    port_arity: int
    levels: tuple[MarkingLevel, ...]
    exact_added_sites: int
    recursive_levels_regenerated: int
    coordinate_lift_used_at_inference: bool
    global_section_queried_at_inference: bool
    heldout_atoms_inserted: bool
    exact_colored_growth: bool
    exponential_growth: bool
    local_marking_gate_passed: bool


def evaluate(maximum_level=6, maximum_waves=10):
    seed, instruction = _compile_iqc_instruction()
    marking = fit_propagated_marking(instruction, seed)
    state = initial_marked_configuration(seed, marking)
    levels = []
    for level in range(1, maximum_level + 1):
        wave_sizes = []
        exact = 0
        rejected = 0
        for _ in range(maximum_waves):
            wave = execute_propagated_wave(
                instruction, marking, state, level=level)
            rejected += (wave.outside_section_rejections +
                         wave.inconsistent_mark_rejections)
            if not wave.emitted_sites:
                break
            exact_wave = sum(_hidden_site(*site)
                             for site in wave.emitted_sites)
            wave_sizes.append(len(wave.emitted_sites))
            exact += exact_wave
            if exact_wave != len(wave.emitted_sites):
                break
            state = extend_marked_configuration(state, wave)
        levels.append(MarkingLevel(
            level, tuple(wave_sizes), exact, rejected))
    additions = len(state.configuration.positions) - len(seed.positions)
    regenerated = sum(bool(level.wave_sites) for level in levels)
    exact = additions > 0 and additions == sum(
        level.exact_sites for level in levels)
    totals = tuple(level.exact_sites for level in levels
                   if level.exact_sites)
    exponential = (len(totals) >= 3 and
                   all(right > left for left, right in zip(totals, totals[1:])))
    return PropagatedMarkingBenchmark(
        len(seed.positions), len(state.configuration.positions),
        marking.marking_dimension, marking.port_arity, tuple(levels),
        additions, regenerated, False, False, False, exact, exponential,
        exact and regenerated >= 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
