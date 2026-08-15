#!/usr/bin/env python3
"""Deploy sparse-admitted macros across the full frozen training port graph.

The sparse reducer and atom-disjoint evidence decide whether a ``MacroType`` is
admitted.  They must not restrict where that admitted production can be used.
This module therefore matches each admitted rooted, directed, port-labelled
graph against every occurrence and admitted relation in the original training
program.  A graph embedding is retained only if its rendered colored atom
union is a proper rigid occurrence of the admitted macro prototype.

No type is fitted, admitted, rejected, or modified by dense support.  Dense
occurrences are deployment evidence only.  The returned ``MacroType`` records
retain their sparse ``occurrences`` as the MDL admission proof and place the
deployment matches in ``promotion_occurrences``, which the generic promoter
already consumes in preference to the sparse proof.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Sequence

from materials_gcts_irregular_port_atlas import IrregularPortProgram
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, ClusterPrototype, fit_occurrence_pose, make_prototype,
    matvec)
from materials_gcts_port_graph_macros import MacroOccurrence, MacroType


@dataclass(frozen=True)
class DenseMacroTypeAudit:
    macro_id: int
    nodes: int
    sparse_admission_occurrences: int
    graph_embeddings_considered: int
    proper_geometry_matches: int
    duplicate_atom_unions: int
    pose_fit_failures: int
    dense_occurrences: int
    admission_mdl_saving_unchanged: bool


@dataclass(frozen=True)
class DenseMacroMatchingResult:
    source_occurrences: int
    source_directed_relations: int
    admitted_macro_types: int
    dense_macro_types: tuple[MacroType, ...]
    audits: tuple[DenseMacroTypeAudit, ...]
    total_sparse_admission_occurrences: int
    total_dense_occurrences: int
    every_dense_match_proper: bool
    target_used: bool
    family_cell_scale_used: bool


def _add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def _render_union(
    node_ids: Sequence[int], occurrences: dict[int, ClusterOccurrence],
    prototypes: dict[int, ClusterPrototype], tolerance: float,
):
    species_at = {}
    position_at = {}
    for node in node_ids:
        occurrence = occurrences[node]
        prototype = prototypes[occurrence.type_id]
        for species, local in prototype.sites:
            point = _add(matvec(occurrence.rotation, local),
                         occurrence.translation)
            key = tuple(round(value / tolerance) for value in point)
            if key in species_at and species_at[key] != species:
                return None
            species_at[key] = species
            position_at.setdefault(key, point)
    return tuple((species_at[key], position_at[key])
                 for key in sorted(species_at))


def _admitted_graph(program: IrregularPortProgram):
    admitted = {(port.parent_type, port.child_type,
                 port.symmetry_orbit_key)
                for port in program.atlas.ports}
    occurrence_type = {item.occurrence_id: item.type_id
                       for item in program.occurrences}
    labels = defaultdict(set)
    outgoing = defaultdict(set)
    incoming = defaultdict(set)
    for parent, child, parent_type, child_type, key in (
            program.atlas.relation_classes):
        label = parent_type, child_type, key
        if label not in admitted:
            continue
        labels[(parent, child)].add(label)
        outgoing[(parent, label)].add(child)
        incoming[(child, label)].add(parent)
    return occurrence_type, labels, outgoing, incoming


def _pattern(macro: MacroType):
    labels = defaultdict(set)
    for edge in macro.edges:
        labels[(edge.source, edge.target)].add(edge.port)
    return labels


def _enumerate_graph_embeddings(
    macro: MacroType, occurrence_type, labels, outgoing, incoming,
):
    pattern = _pattern(macro)
    count = len(macro.node_types)
    by_type = defaultdict(set)
    for occurrence, type_id in occurrence_type.items():
        by_type[type_id].add(occurrence)
    seen = set()

    def search(mapping, unused_pattern):
        if not unused_pattern:
            embedding = tuple(mapping[index] for index in range(count))
            if embedding not in seen:
                seen.add(embedding)
                yield embedding
            return
        # Assign the node with the most constraints to the mapped subgraph.
        node = max(unused_pattern, key=lambda candidate: (
            sum((candidate, other) in pattern or (other, candidate) in pattern
                for other in mapping), -candidate))
        candidates = set(by_type[macro.node_types[node]])
        for other, actual in mapping.items():
            for label in pattern.get((other, node), ()):
                candidates.intersection_update(outgoing.get((actual, label), ()))
            for label in pattern.get((node, other), ()):
                candidates.intersection_update(incoming.get((actual, label), ()))
        candidates.difference_update(mapping.values())
        for actual in sorted(candidates):
            valid = True
            for other, other_actual in mapping.items():
                required_forward = pattern.get((node, other), set())
                required_reverse = pattern.get((other, node), set())
                if (not required_forward.issubset(
                        labels.get((actual, other_actual), set())) or
                    not required_reverse.issubset(
                        labels.get((other_actual, actual), set()))):
                    valid = False
                    break
            if valid:
                mapping[node] = actual
                yield from search(mapping, unused_pattern - {node})
                del mapping[node]

    # Rooted identity is retained: pattern node zero is always the root.
    for root in sorted(by_type[macro.node_types[0]]):
        yield from search({0: root}, set(range(1, count)))


def match_dense_macro_types(
    program: IrregularPortProgram, admitted_macros: Sequence[MacroType], *,
    pose_tolerance: float = .03,
) -> DenseMacroMatchingResult:
    """Match admitted macros densely without changing their admission proof."""
    if pose_tolerance <= 0 or not math.isfinite(pose_tolerance):
        raise ValueError("pose tolerance must be finite and positive")
    occurrence_type, labels, outgoing, incoming = _admitted_graph(program)
    occurrences = {item.occurrence_id: item for item in program.occurrences}
    prototypes = {item.type_id: item for item in program.prototypes}
    supports = dict(program.occurrence_supports)
    dense_types = []
    audits = []
    all_proper = True
    for macro in admitted_macros:
        try:
            prototype = make_prototype(
                macro.macro_id, macro.atom_union,
                tolerance=pose_tolerance)
        except ValueError:
            audits.append(DenseMacroTypeAudit(
                macro.macro_id, len(macro.node_types), len(macro.occurrences),
                0, 0, 0, 1, 0, True))
            all_proper = False
            continue
        considered = proper = duplicates = failures = 0
        dense = []
        atom_unions = set()
        for embedding in _enumerate_graph_embeddings(
                macro, occurrence_type, labels, outgoing, incoming):
            considered += 1
            observed = _render_union(
                embedding, occurrences, prototypes, pose_tolerance)
            if observed is None:
                failures += 1
                continue
            try:
                fit_occurrence_pose(
                    0, prototype, observed, tolerance=pose_tolerance)
            except ValueError:
                failures += 1
                continue
            proper += 1
            atoms = tuple(sorted({atom for node in embedding
                                  for atom in supports[node]}))
            if atoms in atom_unions:
                duplicates += 1
                continue
            atom_unions.add(atoms)
            dense.append(MacroOccurrence(
                embedding[0], embedding, atoms, 0.0))
        # Keep sparse/disjoint occurrences as the immutable admission proof.
        # Dense matches are deployment evidence only.
        dense_type = replace(macro, promotion_occurrences=tuple(dense))
        dense_types.append(dense_type)
        audits.append(DenseMacroTypeAudit(
            macro.macro_id, len(macro.node_types), len(macro.occurrences),
            considered, proper, duplicates, failures, len(dense),
            dense_type.mdl_saving == macro.mdl_saving))
        # Graph-only candidates can legitimately fail the final SE(3) check;
        # every *retained* occurrence has passed it.
    return DenseMacroMatchingResult(
        len(occurrence_type), sum(len(value) for value in labels.values()),
        len(admitted_macros),
        tuple(dense_types), tuple(audits),
        sum(len(macro.occurrences) for macro in admitted_macros),
        sum(len(macro.promotion_occurrences or macro.occurrences)
            for macro in dense_types),
        all_proper, False, False)
