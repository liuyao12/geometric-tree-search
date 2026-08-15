#!/usr/bin/env python3
"""Cross-family reduction audit for sparse occurrence graphs."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_sparse_occurrence_graph import reduce_occurrence_graph


@dataclass(frozen=True)
class SparseOccurrenceCase:
    system: str
    atoms: int
    source_nodes: int
    cover_nodes: int
    connector_nodes: int
    retained_nodes: int
    node_reduction: float
    source_edges: int
    spanning_edges: int
    canonical_cycle_edges: int
    retained_edges: int
    edge_reduction: float
    source_components: int
    cover_components_before_connectors: int
    retained_components: int
    complete_repeated_support_cover: bool
    connected_when_source_connected: bool
    generic_inputs_only: bool


def _case(configuration: AtomicConfiguration) -> SparseOccurrenceCase:
    program = compile_irregular_port_program(
        configuration.species, configuration.positions)
    graph = reduce_occurrence_graph(program)
    return SparseOccurrenceCase(
        configuration.name, len(configuration.positions), graph.source_nodes,
        len(graph.cover_nodes), len(graph.connector_nodes),
        len(graph.retained_nodes), graph.node_reduction,
        graph.source_edges, len(graph.spanning_edges), len(graph.cycle_edges),
        len(graph.retained_edges), graph.edge_reduction,
        graph.source_components, graph.cover_components_before_connectors,
        graph.retained_components, graph.complete_repeated_support_cover,
        graph.connected_when_source_connected, True)


def evaluate() -> tuple[SparseOccurrenceCase, ...]:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    nacl = AtomicConfiguration(nacl.name, nacl.positions, nacl.species)
    iqc, _ = oracle_patch(3, 9.0)
    cdyb = build_cdyb_split().training
    return tuple(_case(item) for item in (nacl, iqc, cdyb))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps([asdict(item) for item in result], indent=2,
                     sort_keys=True) if arguments.json else result)


if __name__ == "__main__":
    main()
