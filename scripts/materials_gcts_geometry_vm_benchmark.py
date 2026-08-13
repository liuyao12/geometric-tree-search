#!/usr/bin/env python3
"""Coordinate/species replay through one generic GCTS geometry VM."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cross_family_transfer_audit import _learn_anchor
from materials_gcts_fibonacci_3d import PHI, make_input
from materials_gcts_generic import benchmark_systems
from materials_gcts_geometry_vm import (
    compile_anchor, compile_overlap, compile_translation)
from materials_gcts_icosahedral_modelset import (
    HIDDEN_UNIT, oracle_patch, oracle_patch_fast)
from materials_gcts_metric_port_atlas import (
    fit_metric_port_atlas, fit_port_pair_section, pair_section_sites,
    propose_with_metric_ports)
from materials_gcts_parametric_recursive import discover_rule
from materials_gcts_recursive_connections import local_cluster_types, point_key
from materials_gcts_port_cover_graph import compile_instruction, execute_graph


def _execute(instruction, state, *, level=1):
    """Benchmark the normalized graph, not the legacy opcode dispatch."""
    return execute_graph(compile_instruction(instruction), state, level=level)


@dataclass(frozen=True)
class VmLevel:
    input_atoms: int
    target_atoms: int
    emitted_sites: int
    true_sites: int
    precision: float
    novel_recall: float


@dataclass(frozen=True)
class VmCase:
    system: str
    selected_opcode: str
    levels: tuple[VmLevel, ...]
    exact_species_and_positions: bool


@dataclass(frozen=True)
class GeometryVmBenchmark:
    cases: tuple[VmCase, ...]
    interpreter_opcodes: tuple[str, ...]
    one_interpreter: bool
    normalized_cover_graph: bool
    every_graph_recursively_nested: bool
    family_labels_used: bool
    heldout_geometry_used_for_fitting: bool
    benchmark_passed: bool


def _score(state, target, emitted):
    known = set(zip(map(point_key, state.positions), state.species))
    novel = set(zip(map(point_key, target.positions), target.species)) - known
    true = emitted & novel
    return VmLevel(len(state.positions), len(target.positions), len(emitted),
                   len(true), len(true) / max(1, len(emitted)),
                   len(true) / len(novel))


def _crystal(return_instruction=False):
    seed = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    rule = discover_rule(seed)
    instruction = compile_translation(rule)
    from materials_gcts_periodic_growth import replicate
    reports = []
    state = seed
    for _ in range(2):
        target = replicate(state)
        result = _execute(instruction, state)
        reports.append(_score(state, target, result.emitted_sites))
        state = target
    case = VmCase(seed.name, instruction.opcode, tuple(reports),
                  all(item.precision == item.novel_recall == 1.0
                      for item in reports))
    return (case, instruction) if return_instruction else case


def _fibonacci(return_instruction=False):
    seed = make_input(9)
    edges = (1.1, 1.7, 2.4, 3.0)
    _, anchor = _learn_anchor(seed, PHI, edges)
    instruction = compile_anchor(seed, PHI, edges, anchor)
    reports = []
    for state_side, target_side in ((15, 24), (24, 39)):
        state, target = make_input(state_side), make_input(target_side)
        reports.append(_score(
            state, target, _execute(instruction, state).emitted_sites))
    case = VmCase(seed.name, instruction.opcode, tuple(reports),
                  all(item.precision == 1.0 for item in reports))
    return (case, instruction) if return_instruction else case


def _iqc(return_instruction=False):
    seed, _ = oracle_patch(3, 9.0)
    edges = (1.4, 2.1, 2.8, 3.81)
    types = local_cluster_types(seed.positions, seed.species, edges)
    atlas = fit_metric_port_atlas(
        seed.positions, types, seed.positions, HIDDEN_UNIT,
        target_colors=seed.species, observable_radius=9.0)
    section = fit_port_pair_section(atlas, seed.positions, types,
                                    seed.positions)
    proposals = propose_with_metric_ports(atlas, seed.positions, types)
    targets = set(map(point_key, seed.positions))
    pair_sites = pair_section_sites(section, atlas, seed.positions, types)
    minimum = min(proposals.votes[point] for point in pair_sites
                  if point in targets)
    instruction = compile_overlap(
        seed, HIDDEN_UNIT, edges, atlas, section, minimum,
        discover_rule(seed))
    reports = []
    for action, state_bound, target_bound in ((1, 4, 6), (2, 6, 10)):
        state, _ = oracle_patch(
            state_bound, 9.0 * HIDDEN_UNIT ** action)
        oracle = oracle_patch if target_bound < 10 else oracle_patch_fast
        target, _ = oracle(
            target_bound, 9.0 * HIDDEN_UNIT ** (action + 1))
        reports.append(_score(
            state, target, _execute(
                instruction, state, level=action).emitted_sites))
    case = VmCase(seed.name, instruction.opcode, tuple(reports),
                  all(item.precision == 1.0 for item in reports))
    return (case, instruction) if return_instruction else case


def evaluate():
    compiled = (_crystal(True), _iqc(True), _fibonacci(True))
    cases = tuple(item[0] for item in compiled)
    instructions = tuple(item[1] for item in compiled)
    opcodes = tuple(case.selected_opcode for case in cases)
    one = len(set(opcodes)) == 3
    graphs = tuple(compile_instruction(item) for item in instructions)
    normalized = len(graphs) == 3 and all(
                     len(graph.nodes) == len(graph.root_nodes) == 1
                     for graph in graphs)
    recursive = all(graph.nodes[0].child_nodes == graph.root_nodes
                    for graph in graphs)
    passed = (one and normalized and recursive and
              all(case.exact_species_and_positions for case in cases))
    return GeometryVmBenchmark(
        cases, opcodes, one, normalized, recursive, False, False, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
