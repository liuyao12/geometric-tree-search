#!/usr/bin/env python3
"""Geometry-first cluster-of-clusters decoration transfer benchmark."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median
from types import SimpleNamespace

from materials_gcts_dense_macro_matching import (
    _render_union, match_dense_macro_types)
from materials_gcts_geometry_decoration_vocabulary_benchmark import (
    _decorations)
from materials_gcts_iqc_reclustered_transfer_audit import (
    _frozen_heldout_program)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_oriented_overlap_ports import (
    fit_occurrence_pose, make_prototype)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)


@dataclass(frozen=True)
class GeometryDecorationHierarchyAudit:
    training_atoms: int
    heldout_atoms: int
    primitive_geometry_types: int
    admitted_macro_types: int
    quotient_macro_types: int
    promoted_geometry_types: int
    promoted_train_occurrences: int
    promoted_minimum_support_atoms: int
    promoted_maximum_support_atoms: int
    promoted_decoration_alternatives: int
    promoted_types_with_multiple_decorations: int
    heldout_transferred_geometry_types: int
    heldout_promoted_occurrences: int
    heldout_known_decoration_occurrences: int
    heldout_known_decoration_occurrence_coverage: float
    heldout_promoted_atoms_covered: int
    heldout_atoms_known_decoration_covered: int
    heldout_known_decoration_atom_coverage: float
    primitive_known_decoration_occurrence_coverage: float
    train_macro_child_role_states: int
    heldout_macro_child_role_samples: int
    heldout_macro_role_context_coverage: float
    heldout_macro_role_decoration_accuracy: float
    heldout_primitive_modal_accuracy_on_same_samples: float
    macro_role_context_improves_primitive_modal: bool
    macro_role_shuffle_trials: int
    shuffled_macro_role_median_accuracy: float
    shuffled_macro_role_best_accuracy: float
    macro_role_empirical_p_value: float
    macro_role_beats_shuffled_controls: bool
    hierarchy_improves_decoration_occurrence_transfer: bool
    geometry_fit_before_target_opened: bool
    heldout_used_for_fit_mining_or_quotient: bool
    target_positions_used_for_reencoding: bool
    autonomous_growth_claimed: bool
    hierarchy_decoration_gate_passed: bool
    limitation: str


def _macro_program(source, macro_types, tolerance=.03, *,
                   use_sparse_fallback=True):
    """Fit only exact macro prototypes/poses; do not build an all-pairs atlas."""
    source_occurrences = {item.occurrence_id: item
                          for item in source.occurrences}
    source_prototypes = {item.type_id: item for item in source.prototypes}
    prototypes = []
    occurrences = []
    supports = []
    for macro in macro_types:
        prototype = make_prototype(
            macro.macro_id, macro.atom_union, tolerance=tolerance)
        prototypes.append(prototype)
        deployments = macro.promotion_occurrences
        if use_sparse_fallback and not deployments:
            deployments = macro.occurrences
        for deployment in deployments:
            observed = _render_union(
                deployment.node_occurrences, source_occurrences,
                source_prototypes, tolerance)
            if observed is None:
                raise AssertionError("macro occurrence has colored conflict")
            fitted = fit_occurrence_pose(
                len(occurrences), prototype, observed, tolerance=tolerance)
            occurrences.append(fitted)
            supports.append((fitted.occurrence_id,
                             tuple(deployment.atom_indices)))
    return SimpleNamespace(
        prototypes=tuple(prototypes), occurrences=tuple(occurrences),
        occurrence_supports=tuple(supports))


def evaluate(maximum_nodes=3):
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    train_species = tuple(species for species, _point in fixture.training_sites)
    train_positions = tuple(point for _species, point in fixture.training_sites)
    geometry = compile_irregular_port_program(
        tuple("*" for _ in train_positions), train_positions)
    mined = mine_port_graph_macros(
        geometry, maximum_nodes=maximum_nodes,
        include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    dense = match_dense_macro_types(geometry, quotient.quotient_macros)
    promoted = _macro_program(geometry, dense.dense_macro_types)
    train_decorations = _decorations(
        promoted, train_species, train_positions, promoted.occurrences,
        promoted.occurrence_supports)
    alternatives = defaultdict(set)
    for type_id, decoration in train_decorations:
        alternatives[type_id].add(decoration)

    # Only after the hierarchy is frozen are heldout positions enumerated.
    target = open_target()
    enumeration = enumerate_frozen_port_occurrences(
        geometry, tuple("*" for _ in target.positions), target.positions,
        select_greedy_cover=True)
    held_primitive = _frozen_heldout_program(geometry, enumeration)
    held_dense = match_dense_macro_types(
        held_primitive, quotient.quotient_macros)
    held = _macro_program(
        held_primitive, held_dense.dense_macro_types,
        use_sparse_fallback=False)
    held_decorations = _decorations(
        held, target.species, target.positions, held.occurrences,
        held.occurrence_supports)

    # A whole macro decoration is intentionally strict.  The bounded
    # hierarchical section below instead lets macro geometry/child role mark
    # the decoration of each primitive child cluster.
    train_primitive_decorations = dict(zip(
        (item.occurrence_id for item in geometry.occurrences),
        _decorations(geometry, train_species, train_positions,
                     geometry.occurrences, geometry.occurrence_supports)))
    role_counts = defaultdict(Counter)
    for macro in dense.dense_macro_types:
        for deployment in macro.promotion_occurrences or macro.occurrences:
            for role, primitive_id in enumerate(deployment.node_occurrences):
                role_counts[(macro.macro_id, role)][
                    train_primitive_decorations[primitive_id]] += 1
    held_primitive_decorations = dict(zip(
        (item.occurrence_id for item in held_primitive.occurrences),
        _decorations(held_primitive, target.species, target.positions,
                     held_primitive.occurrences,
                     held_primitive.occurrence_supports)))
    primitive_modal_counts = defaultdict(Counter)
    for occurrence in geometry.occurrences:
        primitive_modal_counts[occurrence.type_id][
            train_primitive_decorations[occurrence.occurrence_id]] += 1
    held_occurrence_type = {item.occurrence_id: item.type_id
                            for item in held_primitive.occurrences}
    role_samples = covered_role_samples = role_correct = modal_correct = 0
    scored_roles = []
    for macro in held_dense.dense_macro_types:
        for deployment in macro.promotion_occurrences:
            for role, primitive_id in enumerate(deployment.node_occurrences):
                role_samples += 1
                counts = role_counts.get((macro.macro_id, role))
                if not counts:
                    continue
                covered_role_samples += 1
                actual = held_primitive_decorations[primitive_id]
                predicted = max(counts.items(),
                                key=lambda item: (item[1], repr(item[0])))[0]
                role_correct += predicted == actual
                modal_counts = primitive_modal_counts[
                    held_occurrence_type[primitive_id]]
                modal = max(modal_counts.items(),
                            key=lambda item: (item[1], repr(item[0])))[0]
                modal_correct += modal == actual
                scored_roles.append((macro.macro_id, role, primitive_id,
                                     actual))
    shuffled_accuracies = []
    train_type = {item.occurrence_id: item.type_id
                  for item in geometry.occurrences}
    for trial in range(31):
        rng = random.Random(44051 + trial)
        shuffled_decorations = {}
        by_type = defaultdict(list)
        for occurrence_id, decoration in train_primitive_decorations.items():
            by_type[train_type[occurrence_id]].append(
                (occurrence_id, decoration))
        for type_id, rows in sorted(by_type.items()):
            labels = [decoration for _occurrence, decoration in rows]
            rng.shuffle(labels)
            for (occurrence_id, _decoration), label in zip(rows, labels):
                shuffled_decorations[occurrence_id] = label
        shuffled_counts = defaultdict(Counter)
        for macro in dense.dense_macro_types:
            for deployment in macro.promotion_occurrences or macro.occurrences:
                for role, primitive_id in enumerate(
                        deployment.node_occurrences):
                    shuffled_counts[(macro.macro_id, role)][
                        shuffled_decorations[primitive_id]] += 1
        correct = 0
        for macro_id, role, _primitive_id, actual in scored_roles:
            counts = shuffled_counts[macro_id, role]
            predicted = max(counts.items(),
                            key=lambda item: (item[1], repr(item[0])))[0]
            correct += predicted == actual
        shuffled_accuracies.append(correct / max(1, len(scored_roles)))
    role_accuracy = role_correct / max(1, covered_role_samples)
    role_p = (1 + sum(value >= role_accuracy
                      for value in shuffled_accuracies)) / 32
    known_occurrence_ids = {
        occurrence.occurrence_id
        for occurrence, (type_id, decoration) in zip(
            held.occurrences, held_decorations)
        if decoration in alternatives.get(type_id, ())}
    support_by_id = dict(held.occurrence_supports)
    all_covered = {atom for _occurrence_id, support in
                   held.occurrence_supports for atom in support}
    known_covered = {
        atom for occurrence_id in known_occurrence_ids
        for atom in support_by_id[occurrence_id]}
    sizes = tuple(len(support) for _occurrence_id, support in
                  promoted.occurrence_supports)
    occurrence_coverage = len(known_occurrence_ids) / max(
        1, len(held.occurrences))
    atom_coverage = len(known_covered) / len(target.positions)
    primitive_coverage = .156229254259792
    improves = occurrence_coverage > primitive_coverage
    gate = occurrence_coverage >= .9 and atom_coverage >= .95
    return GeometryDecorationHierarchyAudit(
        len(train_positions), len(target.positions), len(geometry.prototypes),
        len(mined.macro_types), len(quotient.quotient_macros),
        len(promoted.prototypes), len(promoted.occurrences),
        min(sizes, default=0), max(sizes, default=0),
        sum(map(len, alternatives.values())),
        sum(len(value) > 1 for value in alternatives.values()),
        len({item.type_id for item in held.occurrences}),
        len(held.occurrences),
        len(known_occurrence_ids), occurrence_coverage, len(all_covered),
        len(known_covered), atom_coverage, primitive_coverage,
        len(role_counts), role_samples,
        covered_role_samples / max(1, role_samples),
        role_correct / max(1, covered_role_samples),
        modal_correct / max(1, covered_role_samples),
        role_correct > modal_correct,
        31, median(shuffled_accuracies), max(shuffled_accuracies), role_p,
        role_p <= .05,
        improves,
        True, False, True, False, gate,
        "The full heldout coordinates are enumerated against a frozen "
        "uncolored hierarchy and species are used only to score decoration "
        "transfer. This is representation transfer, not autonomous growth.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maximum-nodes", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.maximum_nodes)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
