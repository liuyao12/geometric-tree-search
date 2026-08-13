#!/usr/bin/env python3
"""Causal multiscale IQC growth from a self-fed recursive cover graph."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace

from materials_gcts_generic import AtomicConfiguration
from materials_gcts_geometry_vm import GeometryInstruction
from materials_gcts_geometry_vm_benchmark import _iqc
from materials_gcts_icosahedral_modelset import (
    HIDDEN_UNIT, oracle_patch, oracle_patch_fast)
from materials_gcts_port_cover_graph import compile_instruction, execute_graph
from materials_gcts_recursive_connections import point_key


@dataclass(frozen=True)
class SelfFedWave:
    recursive_level: int
    wave: int
    atoms_before: int
    emitted_sites: int
    true_sites: int
    precision: float


@dataclass(frozen=True)
class SelfFedGraphBenchmark:
    training_atoms: int
    initial_atoms: int
    final_atoms: int
    waves: tuple[SelfFedWave, ...]
    sites_by_recursive_level: tuple[int, ...]
    exact_added_sites: int
    exact_nonempty_waves: int
    recursive_levels_regenerated: int
    heldout_atoms_inserted: bool
    oracle_colors_used_for_insertion: bool
    self_fed_multiscale_growth: bool
    exponential_growth: bool
    benchmark_passed: bool


def _configuration(sites):
    ordered = sorted(sites)
    return AtomicConfiguration(
        "self-fed-IQC", tuple(point for point, _ in ordered),
        tuple(color for _, color in ordered), None, False,
        "Only the initial state and recursive graph emissions.")


def evaluate(maximum_waves_per_level=8):
    seed, _ = oracle_patch(3, 9.0)
    initial, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    # Independent, converged hidden oracle is scoring-only. Bounds 16--20
    # all give 155,097 sites at this physical radius.
    target, _ = oracle_patch_fast(16, 9.0 * HIDDEN_UNIT ** 4)
    target_sites = set(zip(map(point_key, target.positions), target.species))
    _, conservative = _iqc(True)
    # Pair membership itself is the seed-learned consensus. Disable the extra
    # scale-normalized vote cutoff used by the sparse amplifying-batch audit.
    regenerative = GeometryInstruction(
        conservative.opcode,
        replace(conservative.payload, seed_minimum_votes=1),
        conservative.learned_from_seed_only,
        conservative.family_label_used,
        conservative.physical_potential_used)
    graph = compile_instruction(regenerative)
    known = set(zip(map(point_key, initial.positions), initial.species))
    state = initial
    waves = []
    by_level = []
    for level in (1, 2, 3):
        level_sites = 0
        for wave in range(1, maximum_waves_per_level + 1):
            emitted = execute_graph(graph, state, level=level).emitted_sites - known
            true = emitted & target_sites
            waves.append(SelfFedWave(
                level, wave, len(known), len(emitted), len(true),
                len(true) / max(1, len(emitted))))
            if not emitted:
                break
            # This assertion is scoring, not oracle insertion. The emitted
            # species-labelled sites themselves become the only next state.
            if emitted != true:
                break
            known.update(emitted)
            state = _configuration(known)
            level_sites += len(emitted)
        by_level.append(level_sites)
    nonempty = tuple(wave for wave in waves if wave.emitted_sites)
    exact = all(wave.precision == 1.0 for wave in nonempty)
    regenerated = sum(total > 0 for total in by_level)
    multiscale = exact and regenerated == 3 and len(nonempty) >= 3
    exponential = (multiscale and len(by_level) >= 3 and
                   all(right > left for left, right in
                       zip(by_level, by_level[1:])))
    return SelfFedGraphBenchmark(
        len(seed.positions), len(initial.positions), len(known), tuple(waves),
        tuple(by_level), len(known) - len(initial.positions), len(nonempty),
        regenerated, False, False, multiscale, exponential, multiscale)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
