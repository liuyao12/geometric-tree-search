#!/usr/bin/env python3
"""Self-fed IQC gap production using ports plus a bounded GCTS section."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_generic import AtomicConfiguration
from materials_gcts_geometry_vm_benchmark import _compile_iqc_instruction
from materials_gcts_icosahedral_modelset import (
    HIDDEN_CONJUGATE, HIDDEN_UNIT, HIDDEN_WINDOW, hidden_species, lift_point,
    oracle_patch, project, star_vectors, vector_norm)
from materials_gcts_port_cover_graph import (
    compile_gap_instruction, execute_graph)
from materials_gcts_recursive_connections import point_key


@dataclass(frozen=True)
class GapWave:
    recursive_level: int
    wave: int
    atoms_before: int
    candidate_sites: int
    section_rejections: int
    emitted_sites: int
    exact_sites: int
    precision: float


@dataclass(frozen=True)
class GapNodeBenchmark:
    training_atoms: int
    initial_atoms: int
    final_atoms: int
    waves: tuple[GapWave, ...]
    sites_by_recursive_level: tuple[int, ...]
    exact_added_sites: int
    section_rejections: int
    recursive_levels_regenerated: int
    heldout_atoms_inserted: bool
    hidden_model_used_for_fitting: bool
    exact_self_fed_growth: bool
    exponential_growth: bool
    benchmark_passed: bool


def _hidden_site(point, chemical):
    coefficient_bound = max(16, __import__("math").ceil(
        max(map(abs, point))) + 8)
    lift, residual = lift_point(
        point, HIDDEN_UNIT, coefficient_bound=coefficient_bound)
    if residual > 1e-5:
        return False
    radius = vector_norm(project(lift, star_vectors(HIDDEN_CONJUGATE)))
    return (radius <= HIDDEN_WINDOW + 1e-9 and
            chemical == hidden_species(radius))


def _configuration(sites):
    ordered = sorted(sites)
    return AtomicConfiguration(
        "gap-node-self-fed-IQC", tuple(point for point, _ in ordered),
        tuple(color for _, color in ordered), None, False,
        "Initial state plus bounded-section gap-node emissions only.")


def evaluate(maximum_waves_per_level=12, maximum_recursive_level=6):
    seed, instruction = _compile_iqc_instruction()
    graph = compile_gap_instruction(instruction)
    initial, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    known = set(zip(map(point_key, initial.positions), initial.species))
    state = initial
    waves = []
    by_level = []
    for level in range(1, maximum_recursive_level + 1):
        total = 0
        for wave in range(1, maximum_waves_per_level + 1):
            result = execute_graph(graph, state, level=level)
            emitted = result.emitted_sites - known
            exact = frozenset(site for site in emitted if _hidden_site(*site))
            waves.append(GapWave(
                level, wave, len(known), result.novel_candidate_groups,
                result.rejected_candidate_groups, len(emitted), len(exact),
                len(exact) / max(1, len(emitted))))
            if not emitted:
                break
            if len(exact) != len(emitted):
                break
            known.update(emitted)
            state = _configuration(known)
            total += len(emitted)
        by_level.append(total)
    nonempty = tuple(wave for wave in waves if wave.emitted_sites)
    exact_growth = (len(nonempty) > 1 and
                    all(wave.precision == 1.0 for wave in nonempty))
    regenerated = sum(total > 0 for total in by_level)
    exponential = exact_growth and all(
        right > left for left, right in zip(by_level, by_level[1:]))
    return GapNodeBenchmark(
        len(seed.positions), len(initial.positions), len(known), tuple(waves),
        tuple(by_level), len(known) - len(initial.positions),
        sum(wave.section_rejections for wave in waves), regenerated,
        False, False, exact_growth, exponential,
        exact_growth and regenerated == maximum_recursive_level)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
