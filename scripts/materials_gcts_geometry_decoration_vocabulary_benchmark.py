#!/usr/bin/env python3
"""Frozen geometry-first support vocabulary with decoration alternatives."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_irregular_port_atlas import (
    IrregularPortProgram, compile_irregular_port_program,
    enumerate_frozen_port_occurrences)
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, learn_overlap_ports, make_prototype, matmul, matvec,
    transpose)
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)


POSE_TOLERANCE = .03


@dataclass(frozen=True)
class GeometryDecorationVocabularyAudit:
    training_atoms: int
    heldout_atoms: int
    geometry_types: int
    train_geometry_occurrences: int
    geometry_types_with_multiple_decorations: int
    train_decoration_alternatives: int
    maximum_decorations_per_geometry: int
    executable_decorated_prototypes: int
    executable_decorated_occurrences: int
    executable_decorated_port_classes: int
    executable_decorated_port_relations: int
    factored_geometry_port_classes: int
    factored_geometry_port_relations: int
    colored_port_expansion_factor: float
    train_decoration_transition_states: int
    ambiguous_decoration_transition_states: int
    frozen_vocabulary_digest: str
    heldout_geometry_occurrences: int
    heldout_geometry_types_seen: int
    heldout_geometry_type_coverage: float
    heldout_atoms_geometry_covered: int
    heldout_geometry_atom_coverage: float
    heldout_decorated_occurrences_seen: int
    heldout_decoration_occurrence_coverage: float
    heldout_atoms_known_decoration_covered: int
    heldout_known_decoration_atom_coverage: float
    heldout_unseen_decoration_patterns: int
    heldout_known_decoration_relations: int
    exact_transition_context_coverage: float
    decoration_marking_accuracy: float
    modal_child_geometry_accuracy: float
    decoration_marking_improves_modal: bool
    train_order_two_contexts: int
    heldout_causal_decoration_samples: int
    heldout_order_two_exact_context_coverage: float
    single_incoming_port_accuracy_on_causal_samples: float
    order_two_decoration_accuracy: float
    order_two_modal_accuracy: float
    order_two_improves_single_port: bool
    shuffle_trials: int
    shuffled_order_two_median_accuracy: float
    shuffled_order_two_best_accuracy: float
    order_two_empirical_p_value: float
    order_two_beats_shuffled_controls: bool
    geometry_fit_before_target_opened: bool
    heldout_used_for_geometry_or_decoration_fit: bool
    family_phi_cell_or_potential_used: bool
    representation_gate_passed: bool
    limitation: str


def _add(left, right):
    return tuple(left[index] + right[index]
                 for index in range(3))


def _site_permutation(points, rotation, tolerance):
    result = []
    for point in points:
        transformed = matvec(rotation, point)
        choices = tuple((math.dist(transformed, other), index)
                        for index, other in enumerate(points))
        distance, index = min(choices)
        if distance > tolerance:
            raise AssertionError("proper symmetry did not permute the sites")
        result.append(index)
    if len(set(result)) != len(points):
        raise AssertionError("symmetry site permutation is not bijective")
    return tuple(result)


def _canonical_decoration(prototype, occurrence, support, species, positions,
                          tolerance):
    available = set(support)
    labels = []
    for _dummy, local in prototype.sites:
        world = _add(matvec(occurrence.rotation, local),
                     occurrence.translation)
        distance, atom = min((math.dist(world, positions[index]), index)
                             for index in available)
        if distance > tolerance:
            raise AssertionError("occurrence support does not render exactly")
        available.remove(atom)
        labels.append(repr(species[atom]))
    if available:
        raise AssertionError("support contains unmapped geometry sites")
    points = tuple(point for _dummy, point in prototype.sites)
    alternatives = []
    for symmetry in prototype.proper_symmetries:
        permutation = _site_permutation(points, symmetry, tolerance)
        decorated = [None] * len(labels)
        for source, target in enumerate(permutation):
            decorated[target] = labels[source]
        alternatives.append(tuple(decorated))
    return min(alternatives)


def _canonical_decoration_pose(prototype, occurrence, support, species,
                               positions, tolerance):
    available = set(support)
    labels = []
    for _dummy, local in prototype.sites:
        world = _add(matvec(occurrence.rotation, local),
                     occurrence.translation)
        distance, atom = min((math.dist(world, positions[index]), index)
                             for index in available)
        if distance > tolerance:
            raise AssertionError("occurrence support does not render exactly")
        available.remove(atom)
        labels.append(species[atom])
    points = tuple(point for _dummy, point in prototype.sites)
    alternatives = []
    for symmetry in prototype.proper_symmetries:
        permutation = _site_permutation(points, symmetry, tolerance)
        decorated = [None] * len(labels)
        for source, target in enumerate(permutation):
            decorated[target] = labels[source]
        alternatives.append((tuple(map(repr, decorated)), tuple(decorated),
                             symmetry))
    _key, decoration, symmetry = min(alternatives, key=lambda item: item[0])
    rotation = matmul(occurrence.rotation, transpose(symmetry))
    return decoration, rotation, occurrence.translation


def compile_geometry_decoration_program(geometry, species, positions):
    """Attach exact train decorations to frozen uncolored support geometry."""
    geometry_prototypes = {item.type_id: item for item in geometry.prototypes}
    supports = dict(geometry.occurrence_supports)
    observed = []
    keys = set()
    for occurrence in geometry.occurrences:
        decoration, rotation, translation = _canonical_decoration_pose(
            geometry_prototypes[occurrence.type_id], occurrence,
            supports[occurrence.occurrence_id], species, positions,
            POSE_TOLERANCE)
        key = (occurrence.type_id, tuple(map(repr, decoration)))
        keys.add(key)
        observed.append((key, decoration, rotation, translation,
                         supports[occurrence.occurrence_id]))
    type_id = {key: index for index, key in enumerate(sorted(keys))}
    prototypes = []
    geometry_by_decorated = {}
    for key in sorted(keys):
        geometry_type, _decoration_key = key
        decoration = next(item[1] for item in observed if item[0] == key)
        prototype = geometry_prototypes[geometry_type]
        decorated_id = type_id[key]
        prototypes.append(make_prototype(
            decorated_id,
            tuple(zip(decoration, (point for _dummy, point in
                                   prototype.sites))),
            tolerance=POSE_TOLERANCE))
        geometry_by_decorated[decorated_id] = geometry_type
    occurrences = []
    occurrence_supports = []
    for occurrence_id, (key, _decoration, rotation, translation,
                        support) in enumerate(observed):
        occurrences.append(ClusterOccurrence(
            occurrence_id, type_id[key], rotation, translation))
        occurrence_supports.append((occurrence_id, support))
    membership = defaultdict(list)
    for occurrence_id, support in occurrence_supports:
        for atom in support:
            membership[atom].append(occurrence_id)
    shared = Counter()
    for values in membership.values():
        ids = tuple(sorted(set(values)))
        for left in ids:
            for right in ids:
                if left != right:
                    shared[left, right] += 1
    allowed = frozenset(pair for pair, count in shared.items()
                        if count >= geometry.minimum_shared_atoms)
    atlas = learn_overlap_ports(
        tuple(prototypes), tuple(occurrences),
        minimum_overlap=geometry.minimum_shared_atoms,
        minimum_observations=2, overlap_tolerance=POSE_TOLERANCE,
        exclusion_distance=max(
            POSE_TOLERANCE, geometry.cover.minimum_distance * .45),
        allowed_occurrence_pairs=allowed)
    support_type = dict(geometry.prototype_support_types)
    program = IrregularPortProgram(
        geometry.cover, geometry.vocabulary, tuple(prototypes),
        tuple((item.type_id, support_type[geometry_by_decorated[item.type_id]])
              for item in prototypes), tuple(occurrences),
        tuple(occurrence_supports), atlas, 0, len(allowed),
        geometry.minimum_shared_atoms, False, False, False)
    return program


def _target_geometry_atlas(program, enumeration):
    supports = dict(enumeration.occurrence_supports)
    membership = defaultdict(list)
    for occurrence_id, support in enumeration.occurrence_supports:
        for atom in support:
            membership[atom].append(occurrence_id)
    shared = Counter()
    for values in membership.values():
        ids = tuple(sorted(set(values)))
        for left in ids:
            for right in ids:
                if left != right:
                    shared[left, right] += 1
    allowed = frozenset(pair for pair, count in shared.items()
                        if count >= program.minimum_shared_atoms)
    return learn_overlap_ports(
        program.prototypes, enumeration.occurrences,
        minimum_overlap=program.minimum_shared_atoms,
        minimum_observations=1, overlap_tolerance=POSE_TOLERANCE,
        exclusion_distance=max(
            POSE_TOLERANCE, program.cover.minimum_distance * .45),
        allowed_occurrence_pairs=allowed)


def _radial_context_table(relations, occurrences, occurrence_decorations,
                          origins, patch_by_occurrence):
    occurrence_by_id = {item.occurrence_id: item for item in occurrences}
    incoming = defaultdict(list)
    for parent_id, child_id, parent_type, child_type, orbit_key in relations:
        if (parent_id not in occurrence_decorations or
                child_id not in occurrence_decorations or
                patch_by_occurrence[parent_id] != patch_by_occurrence[child_id]):
            continue
        patch = patch_by_occurrence[child_id]
        origin = origins[patch]
        parent = occurrence_by_id[parent_id]
        child = occurrence_by_id[child_id]
        if math.dist(parent.translation, origin) + 1e-8 >= \
                math.dist(child.translation, origin):
            continue
        token = (occurrence_decorations[parent_id], parent_type, child_type,
                 orbit_key)
        incoming[child_id].append(token)
    contexts = {}
    for child_id, values in incoming.items():
        contexts[child_id] = tuple(sorted(set(values), key=repr))[:2]
    return contexts


def _transition_tables(relations, occurrence_decorations):
    exact = defaultdict(Counter)
    port = defaultdict(Counter)
    child = defaultdict(Counter)
    for parent_id, child_id, parent_type, child_type, orbit_key in relations:
        parent_decoration = occurrence_decorations[parent_id]
        child_decoration = occurrence_decorations[child_id]
        exact[(parent_decoration, parent_type, child_type,
               orbit_key)][child_decoration] += 1
        port[(parent_type, child_type, orbit_key)][child_decoration] += 1
        child[child_type][child_decoration] += 1
    return exact, port, child


def _score_context_consensus(contexts, occurrence_by_id,
                             actual_decorations, exact_transition,
                             port_transition, child_geometry_counts):
    correct = scored = 0
    for occurrence_id, context in contexts.items():
        if not context or occurrence_id not in actual_decorations:
            continue
        child_type = occurrence_by_id[occurrence_id].type_id
        aggregate = defaultdict(float)
        for token in context:
            counts = exact_transition.get(
                (token[0], token[1], token[2], token[3]))
            if not counts:
                counts = port_transition.get(
                    (token[1], token[2], token[3]),
                    child_geometry_counts[child_type])
            total = sum(counts.values())
            for decoration, count in counts.items():
                aggregate[decoration] += count / total
        predicted = max(aggregate.items(),
                        key=lambda item: (item[1], -item[0]))[0]
        correct += predicted == actual_decorations[occurrence_id]
        scored += 1
    return correct / max(1, scored)


def _decorations(program, species, positions, occurrences, supports):
    prototypes = {item.type_id: item for item in program.prototypes}
    support_by_id = dict(supports)
    result = []
    for occurrence in occurrences:
        result.append((occurrence.type_id, _canonical_decoration(
            prototypes[occurrence.type_id], occurrence,
            support_by_id[occurrence.occurrence_id], species, positions,
            POSE_TOLERANCE)))
    return tuple(result)


def evaluate():
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    train_species = tuple(species for species, _point in fixture.training_sites)
    train_positions = tuple(point for _species, point in fixture.training_sites)
    dummy = tuple("*" for _ in train_positions)
    geometry = compile_irregular_port_program(dummy, train_positions)
    train_decorations = _decorations(
        geometry, train_species, train_positions, geometry.occurrences,
        geometry.occurrence_supports)
    alternatives = defaultdict(set)
    for type_id, decoration in train_decorations:
        alternatives[type_id].add(decoration)
    frozen_payload = tuple(sorted(
        (type_id, tuple(sorted(values)))
        for type_id, values in alternatives.items()))
    digest = hashlib.sha256(repr(frozen_payload).encode()).hexdigest()
    decoration_ids = {
        (type_id, decoration): index
        for index, (type_id, decoration) in enumerate(
            (item for type_id, values in frozen_payload
             for item in ((type_id, decoration)
                          for decoration in values)))}
    train_occurrence_decoration = {
        occurrence.occurrence_id: decoration_ids[type_id, decoration]
        for occurrence, (type_id, decoration) in zip(
            geometry.occurrences, train_decorations)}
    exact_transition, port_transition, child_geometry_counts = \
        _transition_tables(
            geometry.atlas.relation_classes, train_occurrence_decoration)
    decorated_program = compile_geometry_decoration_program(
        geometry, train_species, train_positions)
    train_supports = dict(geometry.occurrence_supports)
    train_patch_by_occurrence = {
        occurrence.occurrence_id:
        fixture.training_patch_ids[train_supports[occurrence.occurrence_id][0]]
        for occurrence in geometry.occurrences}
    train_origins = {item.patch_id: item.boundary.origin
                     for item in fixture.training_frontiers}
    train_contexts = _radial_context_table(
        geometry.atlas.relation_classes, geometry.occurrences,
        train_occurrence_decoration, train_origins,
        train_patch_by_occurrence)
    order_two_counts = defaultdict(Counter)
    geometry_occurrence_by_id = {
        item.occurrence_id: item for item in geometry.occurrences}
    for occurrence_id, context in train_contexts.items():
        if not context:
            continue
        child_type = geometry_occurrence_by_id[occurrence_id].type_id
        order_two_counts[(child_type, context)][
            train_occurrence_decoration[occurrence_id]] += 1

    # The heldout structure is not constructed until both geometry and every
    # admitted decoration alternative are frozen above.
    target = open_target()
    heldout_dummy = tuple("*" for _ in target.positions)
    enumeration = enumerate_frozen_port_occurrences(
        geometry, heldout_dummy, target.positions)
    heldout_decorations = _decorations(
        geometry, target.species, target.positions,
        enumeration.occurrences, enumeration.occurrence_supports)
    supports = dict(enumeration.occurrence_supports)
    geometry_atoms = set()
    decorated_atoms = set()
    seen_types = set()
    decorated_occurrences = 0
    unseen = set()
    heldout_occurrence_decoration = {}
    for occurrence, (type_id, decoration) in zip(
            enumeration.occurrences, heldout_decorations):
        atom_ids = set(supports[occurrence.occurrence_id])
        geometry_atoms.update(atom_ids)
        seen_types.add(type_id)
        if decoration in alternatives.get(type_id, ()):
            decorated_occurrences += 1
            decorated_atoms.update(atom_ids)
            heldout_occurrence_decoration[occurrence.occurrence_id] = \
                decoration_ids[type_id, decoration]
        else:
            unseen.add((type_id, decoration))
    target_atlas = _target_geometry_atlas(geometry, enumeration)
    scored = exact_seen = correct = modal_correct = 0
    for parent_id, child_id, parent_type, child_type, orbit_key in \
            target_atlas.relation_classes:
        if (parent_id not in heldout_occurrence_decoration or
                child_id not in heldout_occurrence_decoration):
            continue
        parent_decoration = heldout_occurrence_decoration[parent_id]
        child_decoration = heldout_occurrence_decoration[child_id]
        exact_key = (parent_decoration, parent_type, child_type, orbit_key)
        port_key = (parent_type, child_type, orbit_key)
        counts = exact_transition.get(exact_key)
        if counts:
            exact_seen += 1
        else:
            counts = port_transition.get(port_key,
                                         child_geometry_counts[child_type])
        predicted = max(counts.items(), key=lambda item: (item[1], -item[0]))[0]
        modal = max(child_geometry_counts[child_type].items(),
                    key=lambda item: (item[1], -item[0]))[0]
        correct += predicted == child_decoration
        modal_correct += modal == child_decoration
        scored += 1
    heldout_patch = {item.occurrence_id: 0
                     for item in enumeration.occurrences}
    heldout_contexts = _radial_context_table(
        target_atlas.relation_classes, enumeration.occurrences,
        heldout_occurrence_decoration, {0: fixture.boundary.origin},
        heldout_patch)
    heldout_occurrence_by_id = {
        item.occurrence_id: item for item in enumeration.occurrences}
    order_two_scored = order_two_exact = order_two_correct = \
        order_two_modal_correct = single_causal_correct = 0
    for occurrence_id, context in heldout_contexts.items():
        if (not context or
                occurrence_id not in heldout_occurrence_decoration):
            continue
        child_type = heldout_occurrence_by_id[occurrence_id].type_id
        actual = heldout_occurrence_decoration[occurrence_id]
        exact_pair = order_two_counts.get((child_type, context))
        if exact_pair:
            order_two_exact += 1
        # Compose bounded single-port sections instead of requiring the exact
        # pair to recur. Each incoming port contributes a normalized local
        # distribution, preventing a high-support relation from swamping the
        # second independent connection merely because it is common.
        aggregate = defaultdict(float)
        for token in context:
            counts = exact_transition.get(
                (token[0], token[1], token[2], token[3]))
            if not counts:
                counts = port_transition.get(
                    (token[1], token[2], token[3]),
                    child_geometry_counts[child_type])
            total = sum(counts.values())
            for decoration, count in counts.items():
                aggregate[decoration] += count / total
        predicted = max(aggregate.items(),
                        key=lambda item: (item[1], -item[0]))[0]
        first = context[0]
        single_counts = exact_transition.get(
            (first[0], first[1], first[2], first[3]))
        if not single_counts:
            single_counts = port_transition.get(
                (first[1], first[2], first[3]),
                child_geometry_counts[child_type])
        single_predicted = max(
            single_counts.items(), key=lambda item: (item[1], -item[0]))[0]
        modal = max(child_geometry_counts[child_type].items(),
                    key=lambda item: (item[1], -item[0]))[0]
        order_two_correct += predicted == actual
        single_causal_correct += single_predicted == actual
        order_two_modal_correct += modal == actual
        order_two_scored += 1
    geometry_types = len(geometry.prototypes)
    marking_accuracy = correct / max(1, scored)
    modal_accuracy = modal_correct / max(1, scored)
    marking_improves = marking_accuracy > modal_accuracy
    order_two_accuracy = order_two_correct / max(1, order_two_scored)
    single_causal_accuracy = single_causal_correct / max(1, order_two_scored)
    order_two_modal = order_two_modal_correct / max(1, order_two_scored)
    order_two_improves = order_two_accuracy > single_causal_accuracy
    shuffle_trials = 31
    occurrence_ids_by_geometry = defaultdict(list)
    for occurrence in geometry.occurrences:
        occurrence_ids_by_geometry[occurrence.type_id].append(
            occurrence.occurrence_id)
    shuffled_accuracies = []
    for index in range(shuffle_trials):
        rng = random.Random(104729 + 7919 * index)
        shuffled_decorations = dict(train_occurrence_decoration)
        for occurrence_ids in occurrence_ids_by_geometry.values():
            labels = [train_occurrence_decoration[value]
                      for value in occurrence_ids]
            rng.shuffle(labels)
            for occurrence_id, label in zip(occurrence_ids, labels):
                shuffled_decorations[occurrence_id] = label
        shuffled_exact, shuffled_port, shuffled_child = _transition_tables(
            geometry.atlas.relation_classes, shuffled_decorations)
        shuffled_accuracies.append(_score_context_consensus(
            heldout_contexts, heldout_occurrence_by_id,
            heldout_occurrence_decoration, shuffled_exact, shuffled_port,
            shuffled_child))
    shuffle_successes = sum(value >= order_two_accuracy
                            for value in shuffled_accuracies)
    shuffle_p = (1 + shuffle_successes) / (shuffle_trials + 1)
    beats_shuffles = shuffle_p <= .05
    gate = (
        len(geometry_atoms) == len(target.positions) and
        len(decorated_atoms) / len(target.positions) >= .95 and
        decorated_occurrences / max(1, len(heldout_decorations)) >= .9 and
        any(len(value) > 1 for value in alternatives.values()) and
        marking_improves and order_two_improves and beats_shuffles)
    return GeometryDecorationVocabularyAudit(
        len(train_positions), len(target.positions), geometry_types,
        len(geometry.occurrences),
        sum(len(value) > 1 for value in alternatives.values()),
        sum(map(len, alternatives.values())),
        max(map(len, alternatives.values()), default=0),
        len(decorated_program.prototypes),
        len(decorated_program.occurrences),
        len(decorated_program.atlas.ports),
        decorated_program.atlas.witnessed_relations,
        len(geometry.atlas.ports), geometry.atlas.witnessed_relations,
        len(decorated_program.atlas.ports) / max(1, len(geometry.atlas.ports)),
        len(exact_transition),
        sum(len(value) > 1 for value in exact_transition.values()), digest,
        len(enumeration.occurrences), len(seen_types),
        len(seen_types) / max(1, geometry_types), len(geometry_atoms),
        len(geometry_atoms) / len(target.positions), decorated_occurrences,
        decorated_occurrences / max(1, len(heldout_decorations)),
        len(decorated_atoms), len(decorated_atoms) / len(target.positions),
        len(unseen), scored, exact_seen / max(1, scored), marking_accuracy,
        modal_accuracy, marking_improves, len(order_two_counts),
        order_two_scored, order_two_exact / max(1, order_two_scored),
        single_causal_accuracy, order_two_accuracy, order_two_modal,
        order_two_improves, shuffle_trials, median(shuffled_accuracies),
        max(shuffled_accuracies), shuffle_p, beats_shuffles,
        True, False, False, gate,
        "Geometry is learned with all species hidden, then exact actual "
        "decorations are attached to train occurrences modulo each support's "
        "proper symmetry. The decorated prototypes and their witnessed "
        "overlap ports are executable, but this audit measures frozen "
        "representation transfer only; decorated macro mining and autonomous "
        "growth are separate gates.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
