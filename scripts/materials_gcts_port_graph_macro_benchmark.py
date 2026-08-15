#!/usr/bin/env python3
"""Cross-family audit of first-level recurring port-graph macros."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_port_graph_macros import mine_port_graph_macros


@dataclass(frozen=True)
class PortGraphMacroCase:
    system: str
    atoms: int
    source_nodes: int
    sparse_nodes: int
    source_edges: int
    sparse_undirected_edges: int
    sparse_directed_edges: int
    node_reduction: float
    edge_reduction: float
    positive_mdl_macro_types: int
    maximum_macro_nodes: int
    maximum_macro_atoms: int
    maximum_mdl_saving: int
    minimum_independent_occurrences: int
    maximum_cycle_residual: float
    exact_graph_and_se3_verified: bool
    family_label_cell_potential_target_unused: bool


def _case(configuration: AtomicConfiguration) -> PortGraphMacroCase:
    program = compile_irregular_port_program(
        configuration.species, configuration.positions)
    result = mine_port_graph_macros(program, maximum_nodes=2)
    macros = result.macro_types
    return PortGraphMacroCase(
        configuration.name, len(configuration.positions),
        result.source_graph_vertices, result.graph_vertices,
        result.source_graph_edges, result.sparse_undirected_edges,
        result.graph_edges, result.sparse_node_reduction,
        result.sparse_edge_reduction, len(macros),
        result.maximum_macro_nodes, result.maximum_macro_atoms,
        max((macro.mdl_saving for macro in macros), default=0),
        min((len(macro.occurrences) for macro in macros), default=0),
        max((occurrence.maximum_cycle_residual for macro in macros
             for occurrence in macro.occurrences), default=0.0),
        all(macro.exact_graph_isomorphism_verified and
            macro.se3_cycle_consistent for macro in macros), True)


def evaluate() -> tuple[PortGraphMacroCase, ...]:
    nacl_source = next(item for item in benchmark_systems()
                       if item.name == "NaCl-rocksalt")
    nacl = AtomicConfiguration(
        nacl_source.name, nacl_source.positions, nacl_source.species)
    iqc, _ = oracle_patch(3, 9.0)
    cdyb = build_cdyb_split().training
    return tuple(_case(configuration) for configuration in (nacl, iqc, cdyb))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps([asdict(case) for case in result], indent=2,
                     sort_keys=True) if arguments.json else result)


if __name__ == "__main__":
    main()
