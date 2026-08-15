#!/usr/bin/env python3
"""Safety/metamorphic audit for witnessed boundary-edge recursive mining.

This benchmark deliberately has no family-specific success expectation.  It
checks the finite, train-witnessed graph contract and reports metamorphic
failures as failures rather than weakening the fingerprint until it passes.
"""

from __future__ import annotations

import argparse
import math
from collections import Counter
from dataclasses import asdict, dataclass
import json

from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_iqc_recursive_action_submacro_benchmark import (
    evaluate as evaluate_six_patch_depth)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_recursive_port_hierarchy import (
    drive_recursive_port_hierarchy, real_first_level_callbacks)
from materials_gcts_sparse_occurrence_graph import reduce_occurrence_graph
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class BoundaryRecursiveSafetyCase:
    system: str
    atoms: int
    base_occurrences: int
    base_ports: int
    base_candidates: int
    base_macro_types: int
    promoted_occurrences: int
    promoted_boundary_ports: int
    promoted_boundary_relations: int
    boundary_relations_admitted_and_witnessed: bool
    boundary_sparse_edges: int
    zero_overlap_boundary_sparse_edges: int
    every_sparse_boundary_edge_train_witnessed: bool
    overlap_only_source_edges: int
    boundary_enabled_source_edges: int
    overlap_only_retained_edges: int
    boundary_enabled_retained_edges: int
    overlap_only_candidates: int
    boundary_enabled_candidates: int
    overlap_only_macro_types: int
    boundary_enabled_macro_types: int
    default_equals_explicit_overlap_only: bool
    finite_candidate_bound: int
    candidate_graphs_finite: bool
    hierarchy_admitted_types: tuple[int, ...]
    hierarchy_quotient_types: tuple[int, ...]
    hierarchy_stationary_witnesses: int
    input_permutation_preserves_result: bool
    proper_rigid_transform_preserves_result: bool


@dataclass(frozen=True)
class SixPatchDepthAudit:
    base_dense_occurrences: int
    base_dense_multiplicity_histogram: tuple[tuple[int, int], ...]
    boundary_admitted_types_by_level: tuple[int, ...]
    boundary_quotient_types_by_level: tuple[int, ...]
    artifact_occurrences_by_level: tuple[int, ...]
    admitted_multiplicities_by_level: tuple[tuple[int, ...], ...]
    quotient_promotion_multiplicities_by_level: tuple[tuple[int, ...], ...]
    terminal_promoted_occurrences: int
    minimum_occurrences_for_two_disjoint_binary_embeddings: int
    third_binary_promotion_mathematically_starved: bool
    boundary_recursion_terminated: bool
    stationary_claimed: bool
    target_used: bool


@dataclass(frozen=True)
class BoundaryRecursiveSafetyAudit:
    cases: tuple[BoundaryRecursiveSafetyCase, ...]
    six_patch_depth: SixPatchDepthAudit
    all_boundary_edges_train_witnessed: bool
    all_candidate_graphs_finite: bool
    all_default_paths_byte_semantics_preserved: bool
    all_input_permutations_invariant: bool
    all_proper_rigid_transforms_invariant: bool
    amorphous_stationary_recursion_rejected: bool
    larger_multi_nucleation_ablation_run: bool
    passed: bool


def _configuration_cases():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    nacl = AtomicConfiguration(nacl.name, nacl.positions, nacl.species)
    iqc, _ = oracle_patch(3, 9.)
    disorder = amorphous_hard_core_point_set(atom_count=216, seed=91)
    amorphous = AtomicConfiguration(
        disorder.name, disorder.positions, disorder.species)
    return nacl, iqc, amorphous


def _variant(configuration, kind):
    pairs = list(zip(configuration.species, configuration.positions))
    if kind == "permuted":
        pairs.reverse()
    elif kind == "rigid":
        # Generic determinant +1 Rodrigues rotation plus translation.  This is
        # deliberately not an axis permutation, so numeric frame leakage is
        # exercised too.
        inverse_norm = 1 / math.sqrt(14.)
        x, y, z = inverse_norm, 2 * inverse_norm, 3 * inverse_norm
        angle = .713
        cosine, sine = math.cos(angle), math.sin(angle)
        complement = 1 - cosine
        rotation = (
            (cosine + x*x*complement,
             x*y*complement - z*sine, x*z*complement + y*sine),
            (y*x*complement + z*sine, cosine + y*y*complement,
             y*z*complement - x*sine),
            (z*x*complement - y*sine, z*y*complement + x*sine,
             cosine + z*z*complement))
        shift = (3.1, -4.2, 7.3)
        pairs = [(species, tuple(
            sum(rotation[axis][source] * point[source]
                for source in range(3)) + shift[axis]
            for axis in range(3))) for species, point in pairs]
    return (tuple(item[0] for item in pairs),
            tuple(item[1] for item in pairs))


def _fingerprint(species, positions):
    program = compile_irregular_port_program(species, positions)
    mined = mine_port_graph_macros(program, maximum_nodes=3)
    macro_histogram = tuple(sorted(Counter((
        len(item.node_types), len(item.atom_union), len(item.occurrences),
        item.mdl_saving, len(item.boundary_slots))
        for item in mined.macro_types).items()))
    return (program.cover.complete, len(program.prototypes),
            len(program.occurrences), len(program.atlas.ports),
            mined.source_graph_vertices, mined.source_graph_edges,
            mined.graph_vertices, mined.graph_edges,
            mined.rooted_connected_candidates, mined.exact_geometry_classes,
            len(mined.macro_types), macro_histogram)


def _finite_bound(vertices, maximum_nodes=3):
    # Each candidate is a root plus at most maximum_nodes-1 other vertices.
    return vertices * sum(math.comb(max(0, vertices - 1), extra)
                          for extra in range(1, maximum_nodes))


def _boundary_witness_checks(promoted):
    admitted = {(item.parent_type, item.child_type,
                 item.symmetry_orbit_key)
                for item in promoted.boundary_ports}
    occurrences = {item.occurrence_id for item in promoted.occurrences}
    relations = {(min(item.parent_occurrence, item.child_occurrence),
                  max(item.parent_occurrence, item.child_occurrence),
                  item.parent_type, item.child_type,
                  item.symmetry_orbit_key)
                 for item in promoted.boundary_relation_classes}
    relation_ok = all(
        (item.parent_type, item.child_type, item.symmetry_orbit_key)
        in admitted and item.parent_occurrence in occurrences and
        item.child_occurrence in occurrences and item.child_port_witnesses > 0
        for item in promoted.boundary_relation_classes)
    sparse = reduce_occurrence_graph(
        promoted, include_boundary_relations=True)
    boundary_edges = tuple(item for item in sparse.retained_edges
                           if item.connection_kind == "boundary")
    edge_ok = all((item.left, item.right) + item.canonical_port_label in relations
                  for item in boundary_edges)
    return relation_ok, sparse, boundary_edges, edge_ok


def _case(configuration):
    program = compile_irregular_port_program(
        configuration.species, configuration.positions)
    base = mine_port_graph_macros(program, maximum_nodes=3)
    promoted = promote_macro_types(program, base.macro_types, level=1)
    implicit = mine_port_graph_macros(promoted, maximum_nodes=3)
    overlap = mine_port_graph_macros(
        promoted, maximum_nodes=3, include_boundary_relations=False)
    boundary = mine_port_graph_macros(
        promoted, maximum_nodes=3, include_boundary_relations=True)
    relation_ok, sparse, boundary_edges, edge_ok = (
        _boundary_witness_checks(promoted))
    hierarchy = drive_recursive_port_hierarchy(
        program, real_first_level_callbacks(maximum_nodes=3),
        maximum_levels=3)
    fingerprint = _fingerprint(
        configuration.species, configuration.positions)
    permuted = _fingerprint(*_variant(configuration, "permuted"))
    rigid = _fingerprint(*_variant(configuration, "rigid"))
    bound = _finite_bound(boundary.graph_vertices)
    default_parity = implicit == overlap
    return BoundaryRecursiveSafetyCase(
        configuration.name, len(configuration.positions),
        len(program.occurrences), len(program.atlas.ports),
        base.rooted_connected_candidates, len(base.macro_types),
        len(promoted.occurrences), len(promoted.boundary_ports),
        len(promoted.boundary_relation_classes), relation_ok,
        len(boundary_edges),
        sum(item.overlap_atoms == 0 for item in boundary_edges), edge_ok,
        overlap.source_graph_edges, boundary.source_graph_edges,
        overlap.graph_edges, boundary.graph_edges,
        overlap.rooted_connected_candidates,
        boundary.rooted_connected_candidates, len(overlap.macro_types),
        len(boundary.macro_types), default_parity, bound,
        boundary.rooted_connected_candidates <= bound,
        tuple(item.admitted_macro_types for item in hierarchy.levels),
        tuple(item.quotient_macro_types for item in hierarchy.levels),
        len(hierarchy.stationary_witnesses), fingerprint == permuted,
        fingerprint == rigid)


def _six_patch_depth():
    result = evaluate_six_patch_depth()
    terminal = (result.boundary_artifact_occurrences_by_level[-1]
                if result.boundary_artifact_occurrences_by_level else 0)
    # A binary type needs two atom-disjoint evidence embeddings: four child
    # occurrences is a necessary (not sufficient) counting condition.
    minimum = 4
    return SixPatchDepthAudit(
        result.promoted_dense_occurrences,
        result.base_dense_occurrence_multiplicity_histogram,
        result.boundary_admitted_types_by_level,
        result.boundary_quotient_types_by_level,
        result.boundary_artifact_occurrences_by_level,
        result.boundary_admitted_occurrence_multiplicities_by_level,
        result.boundary_quotient_promotion_multiplicities_by_level,
        terminal, minimum,
        bool(result.boundary_quotient_types_by_level and
             result.boundary_quotient_types_by_level[-2:-1] == (1,) and
             terminal < minimum), result.boundary_terminated,
        result.stationary, result.target_used)


def evaluate():
    cases = tuple(_case(item) for item in _configuration_cases())
    depth = _six_patch_depth()
    witnessed = all(item.boundary_relations_admitted_and_witnessed and
                    item.every_sparse_boundary_edge_train_witnessed
                    for item in cases)
    finite = all(item.candidate_graphs_finite for item in cases)
    default = all(item.default_equals_explicit_overlap_only for item in cases)
    permutation = all(item.input_permutation_preserves_result for item in cases)
    rigid = all(item.proper_rigid_transform_preserves_result for item in cases)
    amorphous = next(item for item in cases if "amorphous" in item.system)
    rejected = (amorphous.hierarchy_stationary_witnesses == 0 and
                amorphous.base_macro_types == 0)
    # The available target-free corpus has six namespaces.  Duplicating them
    # would inflate evidence without new raw occurrences, so this audit does
    # not pretend that namespace replication is a larger-data ablation.
    larger = False
    passed = (witnessed and finite and default and permutation and rigid and
              rejected and depth.boundary_recursion_terminated and
              not depth.stationary_claimed and not depth.target_used)
    return BoundaryRecursiveSafetyAudit(
        cases, depth, witnessed, finite, default, permutation, rigid,
        rejected, larger, passed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
