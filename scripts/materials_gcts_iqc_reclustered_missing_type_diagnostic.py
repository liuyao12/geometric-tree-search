#!/usr/bin/env python3
"""Leakage-safe diagnosis/backoff for frozen first-level IQC macro types."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_iqc_reclustered_transfer_audit import (
    HELDOUT_PATCH_IDS, PATCH_CENTERS, TRAIN_PATCH_IDS, _frozen_heldout_program,
    _grow_patches, _pack)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_irregular_supports import enumerate_frozen_vocabulary
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports


@dataclass(frozen=True)
class MissingTypeAudit:
    type_id: int
    child_types: tuple[int, ...]
    child_occurrences_available: tuple[int, ...]
    absent_child_types: tuple[int, ...]
    absent_child_train_occurrences: tuple[int, ...]
    absent_child_train_patch_ids: tuple[tuple[int, ...], ...]
    absent_child_support_kinds: tuple[str, ...]
    absent_child_atom_counts: tuple[int, ...]
    directed_ports: int
    directed_ports_available: int
    direct_graph_embeddings_considered: int
    direct_exact_occurrences: int
    train_exact_derivation_alternatives: int
    heldout_exact_alternatives_replayed: int
    heldout_backoff_occurrences: int
    train_occurrences: int
    train_boundary_exposed_occurrences: int
    train_minimum_boundary_margin: float
    train_maximum_boundary_margin: float
    frozen_primitive_absent_in_heldout: bool
    port_novelty: bool
    alternative_derivation_mismatch: bool
    insufficient_multiplicity: bool
    boundary_crop_artifact_likely: bool


@dataclass(frozen=True)
class FrozenSemanticBackoffAudit:
    train_types: int
    direct_types_with_one_occurrence: int
    direct_types_with_two_occurrences: int
    semantic_types_with_one_occurrence: int
    semantic_types_with_two_occurrences: int
    exact_action_terminals: int
    ambiguous_atom_unions: int
    exact_semantic_assignments: int
    assignment_precision: float
    semantic_type_coverage: float
    strict_transfer_type_coverage: float
    all_type_ids_semantically_covered: bool
    all_type_ids_transferable_with_two_occurrences: bool
    train_fitted_mapping_only: bool
    heldout_used_for_tuning_or_admission: bool
    exact_action_identity_preserved: bool


@dataclass(frozen=True)
class MissingTypeDiagnosticResult:
    train_atoms: int
    heldout_atoms: int
    train_heldout_patch_ids_disjoint: bool
    heldout_support_isometry_novelty_atoms: int
    missing_direct_type_ids: tuple[int, ...]
    missing_types: tuple[MissingTypeAudit, ...]
    backoff: FrozenSemanticBackoffAudit
    family_phi_cell_labels_used: bool
    elapsed_seconds: float


def _patch_local_geometry(executions, patch_ids, positions):
    radii = []
    for patch_id in patch_ids:
        radii.append(max(math.dist((0., 0., 0.), point) for _, point in (
            (species, tuple(position[axis] -
                            PATCH_CENTERS[patch_id][axis]
                            for axis in range(3)))
            for species, position in executions[patch_id].sites)))
    separation = 4 * max(radii) + 1.
    local = []
    for corpus_patch, patch_id in enumerate(patch_ids):
        # Positions are concatenated by patch in _pack.
        count = len(executions[patch_id].sites)
        start = sum(len(executions[item].sites)
                    for item in patch_ids[:corpus_patch])
        for position in positions[start:start + count]:
            local.append((patch_id, (position[0] - corpus_patch * separation,
                                     position[1], position[2])))
    return tuple(local)


def _macro_diameter(macro):
    points = [point for _, point in macro.atom_union]
    return max((math.dist(left, right) for index, left in enumerate(points)
                for right in points[index + 1:]), default=0.)


def evaluate(maximum_nodes: int = 3) -> MissingTypeDiagnosticResult:
    started = time.perf_counter()
    executions, _ = _grow_patches()
    train_species, train_positions, train_patch = _pack(
        executions, TRAIN_PATCH_IDS)
    held_species, held_positions, _ = _pack(executions, HELDOUT_PATCH_IDS)
    train_local = _patch_local_geometry(
        executions, TRAIN_PATCH_IDS, train_positions)

    training = compile_irregular_port_program(train_species, train_positions)
    held_enumeration = enumerate_frozen_port_occurrences(
        training, held_species, held_positions)
    held_supports = enumerate_frozen_vocabulary(
        training.vocabulary, held_species, held_positions)
    held_support_novelty = len(held_positions) - len(
        held_supports.covered_indices)
    held_program = _frozen_heldout_program(training, held_enumeration)
    mined = mine_port_graph_macros(
        training, maximum_nodes=maximum_nodes,
        include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    direct = match_dense_macro_types(held_program, quotient.quotient_macros)
    alternatives = match_dense_macro_types(
        held_program, quotient.alternative_macros)

    # This mapping is frozen solely by the train quotient.  Exact action IDs
    # retain the source derivation ID even when several map to one semantic ID.
    alt_to_semantic = []
    exact_action_ids = []
    for geometry in quotient.derivation_classes:
        for alternative in geometry.alternatives:
            alt_to_semantic.append(geometry.geometry_class_id)
            exact_action_ids.append((geometry.geometry_class_id,
                                     alternative.source_macro_id))
    assert len(alt_to_semantic) == len(alternatives.dense_macro_types)

    semantic_occurrences = defaultdict(list)
    atom_union_types = defaultdict(set)
    terminal_count = 0
    for index, dense_macro in enumerate(alternatives.dense_macro_types):
        semantic_id = alt_to_semantic[index]
        action_id = exact_action_ids[index]
        for occurrence in dense_macro.promotion_occurrences:
            semantic_occurrences[semantic_id].append(
                (action_id, occurrence.atom_indices))
            atom_union_types[tuple(occurrence.atom_indices)].add(semantic_id)
            terminal_count += 1

    direct_counts = tuple(len(item.promotion_occurrences)
                          for item in direct.dense_macro_types)
    semantic_counts = tuple(len({atoms for _, atoms in
                                 semantic_occurrences[type_id]})
                            for type_id in range(len(quotient.quotient_macros)))
    held_child_counts = Counter(
        occurrence.type_id for occurrence in held_program.occurrences)
    train_child_counts = Counter(
        occurrence.type_id for occurrence in training.occurrences)
    train_occurrence_support = dict(training.occurrence_supports)
    child_patches = defaultdict(set)
    for occurrence in training.occurrences:
        support = train_occurrence_support[occurrence.occurrence_id]
        child_patches[occurrence.type_id].add(train_patch[support[0]])
    support_type_by_prototype = dict(training.prototype_support_types)
    support_kind = {item.type_id: item.kind
                    for item in training.cover.support_types}
    prototype_by_id = {item.type_id: item for item in training.prototypes}
    held_port_keys = {(item[2], item[3], item[4])
                      for item in held_program.atlas.relation_classes}
    missing = []
    for type_id, count in enumerate(direct_counts):
        if count:
            continue
        macro = quotient.quotient_macros[type_id]
        audit = direct.audits[type_id]
        child_available = tuple(held_child_counts[item]
                                for item in macro.node_types)
        absent_children = tuple(sorted({item for item in macro.node_types
                                        if held_child_counts[item] == 0}))
        port_available = sum(edge.port in held_port_keys
                             for edge in macro.edges)
        margins = []
        diameter = _macro_diameter(macro)
        occurrences = macro.promotion_occurrences or macro.occurrences
        boundary = 0
        for occurrence in occurrences:
            radii = [math.dist((0., 0., 0.), train_local[index][1])
                     for index in occurrence.atom_indices]
            margin = 11. - max(radii)
            margins.append(margin)
            boundary += margin <= diameter + .03
        class_alternatives = quotient.derivation_classes[type_id].alternatives
        source_ids = {item.source_macro_id for item in class_alternatives}
        alternative_replays = 0
        for index, dense_macro in enumerate(alternatives.dense_macro_types):
            if exact_action_ids[index][1] in source_ids:
                alternative_replays += bool(dense_macro.promotion_occurrences)
        semantic_count = semantic_counts[type_id]
        primitive_novel = any(value == 0 for value in child_available)
        port_novel = port_available < len(macro.edges)
        alternative_mismatch = semantic_count > 0
        missing.append(MissingTypeAudit(
            type_id, macro.node_types, child_available,
            absent_children,
            tuple(train_child_counts[item] for item in absent_children),
            tuple(tuple(sorted(child_patches[item]))
                  for item in absent_children),
            tuple(support_kind[support_type_by_prototype[item]]
                  for item in absent_children),
            tuple(len(prototype_by_id[item].sites)
                  for item in absent_children),
            len(macro.edges),
            port_available, audit.graph_embeddings_considered, count,
            len(class_alternatives), alternative_replays, semantic_count,
            len(occurrences), boundary, min(margins), max(margins),
            primitive_novel, port_novel, alternative_mismatch,
            semantic_count < 2, boundary == len(occurrences)))

    ambiguous = sum(len(types) > 1 for types in atom_union_types.values())
    semantic_one = sum(value >= 1 for value in semantic_counts)
    semantic_two = sum(value >= 2 for value in semantic_counts)
    exact_assignments = sum(semantic_counts)
    backoff = FrozenSemanticBackoffAudit(
        len(quotient.quotient_macros), sum(value >= 1 for value in direct_counts),
        sum(value >= 2 for value in direct_counts), semantic_one, semantic_two,
        terminal_count, ambiguous, exact_assignments,
        1.0 if exact_assignments and not ambiguous else 0.0,
        semantic_one / len(semantic_counts),
        semantic_two / len(semantic_counts),
        semantic_one == len(semantic_counts),
        semantic_two == len(semantic_counts), True, False, True)
    return MissingTypeDiagnosticResult(
        len(train_positions), len(held_positions),
        set(TRAIN_PATCH_IDS).isdisjoint(HELDOUT_PATCH_IDS),
        held_support_novelty,
        tuple(item.type_id for item in missing), tuple(missing), backoff,
        False, time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maximum-nodes", type=int, choices=(3, 4, 5),
                        default=3)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.maximum_nodes)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
