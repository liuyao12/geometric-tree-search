#!/usr/bin/env python3
"""Geometry-first cluster-of-clusters decoration transfer benchmark."""

from __future__ import annotations

import argparse
import json
import math
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
    heldout_macro_child_train_seen_alternative_samples: int
    heldout_macro_child_train_seen_alternative_ceiling: float
    heldout_macro_role_context_coverage: float
    heldout_macro_role_decoration_accuracy: float
    heldout_primitive_modal_accuracy_on_same_samples: float
    macro_role_context_improves_primitive_modal: bool
    macro_role_shuffle_trials: int
    shuffled_macro_role_median_accuracy: float
    shuffled_macro_role_best_accuracy: float
    macro_role_empirical_p_value: float
    macro_role_beats_shuffled_controls: bool
    selected_macro_boundary_schema: str
    train_macro_boundary_states: int
    train_macro_boundary_lopo_accuracy: float
    heldout_macro_boundary_context_coverage: float
    heldout_macro_boundary_decoration_accuracy: float
    macro_boundary_improves_exact_role: bool
    shuffled_macro_boundary_median_accuracy: float
    shuffled_macro_boundary_best_accuracy: float
    macro_boundary_empirical_p_value: float
    macro_boundary_beats_shuffled_controls: bool
    heldout_macro_boundary_unique_children: int
    heldout_macro_boundary_unique_children_with_train_seen_alternative: int
    heldout_macro_boundary_unique_child_alternative_ceiling: float
    heldout_macro_boundary_consensus_accuracy: float
    heldout_primitive_modal_accuracy_on_unique_children: float
    shuffled_macro_boundary_consensus_median_accuracy: float
    shuffled_macro_boundary_consensus_best_accuracy: float
    macro_boundary_consensus_empirical_p_value: float
    macro_boundary_consensus_beats_shuffled_controls: bool
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


def _macro_role_key(macro, role, primitive_sizes, schema):
    """Proper-frame-free, ID-free macro-boundary descriptor.

    Primitive geometry type remains because its finite decoration alphabet is
    type-specific.  Macro identity, occurrence identity and world pose do not.
    """
    child_type = macro.node_types[role]
    neighbors = {
        edge.target if edge.source == role else edge.source
        for edge in macro.edges
        if edge.source == role or edge.target == role}
    slots = tuple(slot for slot in macro.boundary_slots if slot.node == role)
    incoming = sum(slot.direction == "incoming" for slot in slots)
    outgoing = sum(slot.direction == "outgoing" for slot in slots)
    base = (child_type, len(macro.node_types), len(neighbors),
            min(3, len(slots)))
    if schema == "topology":
        return base
    translations = tuple(item.translation for item in macro.child_placements)
    centroid = tuple(sum(point[axis] for point in translations) /
                     len(translations) for axis in range(3))
    distances = tuple(math.dist(point, centroid) for point in translations)
    scale = max(distances, default=0.) or 1.
    radial = distances[role] / scale
    child_size = primitive_sizes[child_type]
    union_ratio = len(macro.atom_union) / max(1, child_size)
    child_size_shape = tuple(sorted(primitive_sizes[item]
                                    for item in macro.node_types))
    if schema == "boundary_coarse":
        return base + (min(3, incoming), min(3, outgoing),
                       round(radial / .5), round(union_ratio / 1.),
                       child_size_shape)
    if schema == "boundary_fine":
        mean_frequency = (sum(slot.frequency for slot in slots) /
                          len(slots) if slots else 0.)
        return base + (min(3, incoming), min(3, outgoing),
                       round(radial / .25), round(union_ratio / .5),
                       round(mean_frequency / .25), child_size_shape)
    raise ValueError("unknown macro-boundary schema")


def _fit_role_table(samples, macro_by_id, primitive_sizes, schema,
                    excluded_patch=None, decorations=None):
    table = defaultdict(Counter)
    modal = defaultdict(Counter)
    for patch, macro_id, role, primitive_id, child_type, decoration in samples:
        if patch == excluded_patch:
            continue
        label = decorations.get(primitive_id, decoration) \
            if decorations is not None else decoration
        key = _macro_role_key(
            macro_by_id[macro_id], role, primitive_sizes, schema)
        table[key][label] += 1
        modal[child_type][label] += 1
    return table, modal


def _score_role_table(samples, macro_by_id, primitive_sizes, schema,
                      table, modal):
    correct = covered = 0
    for _patch, macro_id, role, _primitive_id, child_type, actual in samples:
        key = _macro_role_key(
            macro_by_id[macro_id], role, primitive_sizes, schema)
        counts = table.get(key)
        if counts:
            covered += 1
        else:
            counts = modal[child_type]
        predicted = max(counts.items(),
                        key=lambda item: (item[1], repr(item[0])))[0]
        correct += predicted == actual
    return correct, covered


def _score_role_consensus(samples, macro_by_id, primitive_sizes, schema,
                          table, modal):
    grouped = defaultdict(list)
    actual_by_child = {}
    type_by_child = {}
    for _patch, macro_id, role, primitive_id, child_type, actual in samples:
        key = _macro_role_key(
            macro_by_id[macro_id], role, primitive_sizes, schema)
        grouped[primitive_id].append(key)
        actual_by_child[primitive_id] = actual
        type_by_child[primitive_id] = child_type
    correct = modal_correct = 0
    for primitive_id, keys in grouped.items():
        votes = defaultdict(float)
        for key in set(keys):
            counts = table.get(key)
            if not counts:
                continue
            total = sum(counts.values())
            for decoration, count in counts.items():
                votes[decoration] += count / total
        child_type = type_by_child[primitive_id]
        if votes:
            predicted = max(votes.items(),
                            key=lambda item: (item[1], repr(item[0])))[0]
        else:
            predicted = max(modal[child_type].items(),
                            key=lambda item: (item[1], repr(item[0])))[0]
        baseline = max(modal[child_type].items(),
                       key=lambda item: (item[1], repr(item[0])))[0]
        actual = actual_by_child[primitive_id]
        correct += predicted == actual
        modal_correct += baseline == actual
    return correct, modal_correct, len(grouped)


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
    train_role_samples = []
    train_patch_ids = fixture.training_patch_ids
    for macro in dense.dense_macro_types:
        for deployment in macro.promotion_occurrences or macro.occurrences:
            patches = {train_patch_ids[atom] for atom in
                       deployment.atom_indices}
            if len(patches) != 1:
                raise AssertionError("train macro crosses patch namespaces")
            patch = next(iter(patches))
            for role, primitive_id in enumerate(deployment.node_occurrences):
                role_counts[(macro.macro_id, role)][
                    train_primitive_decorations[primitive_id]] += 1
                child_type = geometry.occurrences[primitive_id].type_id
                train_role_samples.append((
                    patch, macro.macro_id, role, primitive_id, child_type,
                    train_primitive_decorations[primitive_id]))
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
    held_role_samples = []
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
                held_role_samples.append((
                    -1, macro.macro_id, role, primitive_id,
                    held_occurrence_type[primitive_id], actual))
    train_type = {item.occurrence_id: item.type_id
                  for item in geometry.occurrences}
    primitive_alternatives = defaultdict(set)
    for occurrence_id, decoration in train_primitive_decorations.items():
        primitive_alternatives[train_type[occurrence_id]].add(decoration)
    train_seen_role_samples = sum(
        actual in primitive_alternatives[child_type]
        for _patch, _macro_id, _role, _primitive_id, child_type, actual
        in held_role_samples)
    held_unique_actual = {}
    held_unique_type = {}
    for (_patch, _macro_id, _role, primitive_id, child_type, actual) in \
            held_role_samples:
        held_unique_actual[primitive_id] = actual
        held_unique_type[primitive_id] = child_type
    train_seen_unique_children = sum(
        actual in primitive_alternatives[held_unique_type[primitive_id]]
        for primitive_id, actual in held_unique_actual.items())
    shuffled_accuracies = []
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

    macro_by_id = {item.macro_id: item
                   for item in quotient.quotient_macros}
    primitive_sizes = {item.type_id: len(item.sites)
                       for item in geometry.prototypes}
    schemas = ("topology", "boundary_coarse", "boundary_fine")
    patch_ids = tuple(sorted(set(item[0] for item in train_role_samples)))
    schema_scores = []
    for schema in schemas:
        correct = total = 0
        for patch in patch_ids:
            table, modal = _fit_role_table(
                train_role_samples, macro_by_id, primitive_sizes, schema,
                excluded_patch=patch)
            fold = tuple(item for item in train_role_samples
                         if item[0] == patch)
            fold_correct, _covered = _score_role_table(
                fold, macro_by_id, primitive_sizes, schema, table, modal)
            correct += fold_correct
            total += len(fold)
        full_table, _full_modal = _fit_role_table(
            train_role_samples, macro_by_id, primitive_sizes, schema)
        schema_scores.append((correct / max(1, total), -len(full_table),
                              schema))
    lopo_accuracy, _negative_states, selected_schema = max(schema_scores)
    boundary_table, boundary_modal = _fit_role_table(
        train_role_samples, macro_by_id, primitive_sizes, selected_schema)
    boundary_correct, boundary_covered = _score_role_table(
        held_role_samples, macro_by_id, primitive_sizes, selected_schema,
        boundary_table, boundary_modal)
    (boundary_consensus_correct, boundary_consensus_modal_correct,
     boundary_unique_children) = _score_role_consensus(
        held_role_samples, macro_by_id, primitive_sizes, selected_schema,
        boundary_table, boundary_modal)
    shuffled_boundary_accuracies = []
    shuffled_consensus_accuracies = []
    for trial in range(31):
        rng = random.Random(88091 + trial)
        shuffled_labels = {}
        by_type = defaultdict(list)
        for occurrence_id, decoration in train_primitive_decorations.items():
            by_type[train_type[occurrence_id]].append(
                (occurrence_id, decoration))
        for type_id, rows in sorted(by_type.items()):
            labels = [decoration for _occurrence, decoration in rows]
            rng.shuffle(labels)
            for (occurrence_id, _decoration), label in zip(rows, labels):
                shuffled_labels[occurrence_id] = label
        shuffled_table, shuffled_modal = _fit_role_table(
            train_role_samples, macro_by_id, primitive_sizes,
            selected_schema, decorations=shuffled_labels)
        correct, _covered = _score_role_table(
            held_role_samples, macro_by_id, primitive_sizes, selected_schema,
            shuffled_table, shuffled_modal)
        shuffled_boundary_accuracies.append(
            correct / max(1, len(held_role_samples)))
        consensus_correct, _modal_correct, unique_children = \
            _score_role_consensus(
                held_role_samples, macro_by_id, primitive_sizes,
                selected_schema, shuffled_table, shuffled_modal)
        if unique_children != boundary_unique_children:
            raise AssertionError("shuffle changed heldout child set")
        shuffled_consensus_accuracies.append(
            consensus_correct / max(1, unique_children))
    boundary_accuracy = boundary_correct / max(1, len(held_role_samples))
    boundary_p = (1 + sum(value >= boundary_accuracy
                          for value in shuffled_boundary_accuracies)) / 32
    boundary_consensus_accuracy = (
        boundary_consensus_correct / max(1, boundary_unique_children))
    boundary_consensus_p = (
        1 + sum(value >= boundary_consensus_accuracy
                for value in shuffled_consensus_accuracies)) / 32
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
        len(role_counts), role_samples, train_seen_role_samples,
        train_seen_role_samples / max(1, role_samples),
        covered_role_samples / max(1, role_samples),
        role_correct / max(1, covered_role_samples),
        modal_correct / max(1, covered_role_samples),
        role_correct > modal_correct,
        31, median(shuffled_accuracies), max(shuffled_accuracies), role_p,
        role_p <= .05,
        selected_schema, len(boundary_table), lopo_accuracy,
        boundary_covered / max(1, len(held_role_samples)),
        boundary_accuracy, boundary_accuracy > role_accuracy,
        median(shuffled_boundary_accuracies),
        max(shuffled_boundary_accuracies), boundary_p, boundary_p <= .05,
        boundary_unique_children, train_seen_unique_children,
        train_seen_unique_children / max(1, boundary_unique_children),
        boundary_consensus_accuracy,
        boundary_consensus_modal_correct / max(1, boundary_unique_children),
        median(shuffled_consensus_accuracies),
        max(shuffled_consensus_accuracies), boundary_consensus_p,
        boundary_consensus_p <= .05,
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
