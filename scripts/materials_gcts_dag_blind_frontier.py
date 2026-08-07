#!/usr/bin/env python3
"""Blind level-3 parent proposals from oriented level-2 child clusters."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Dict, Hashable, Optional, Sequence, Tuple

import materials_gcts_blind_continuation as blind
import materials_gcts_transform_dag as dag
from materials_pointset_clusters import learn_cluster_candidates

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class OrientedOccurrence:
    type_id: int
    center: Vector
    rotation: Matrix
    child_matches: int = 0


@dataclass(frozen=True)
class FrontierCandidate:
    child_matches: int
    parent_type: int
    rotation: Matrix
    translation: Vector
    exterior_score: float = 0.0
    lookahead_score: float = 0.0
    depth2_score: int = 0
    long_range_score: float = 0.0


@dataclass(frozen=True)
class ExteriorPort:
    child_type: int
    translation: Vector
    rotation: Matrix
    frequency: float


@dataclass(frozen=True)
class ModuleMarking:
    unit: float
    window: float
    thresholds: Tuple[float, ...]
    ordered_species: Tuple[str, ...]
    residual: float


@dataclass(frozen=True)
class ScoreStratum:
    child_matches: int
    candidates: int
    best_precision: float
    mean_precision: float
    maximum_correct_new_atoms: int


@dataclass(frozen=True)
class DagBlindFrontierResult:
    training_atoms: int
    state_atoms: int
    hidden_atoms: int
    mapped_level1_centers: int
    mapped_level2_centers: int
    partial_level1_hypotheses: int
    retained_level1_hypotheses: int
    level2_hypotheses: int
    generated_parent_candidates: int
    parent_candidates: int
    frontier_candidates: int
    best_closed_parent_score: int
    best_frontier_score: int
    best_exterior_score: float
    top_marked_candidates: int
    best_lookahead_score: float
    top_lookahead_candidates: int
    best_depth2_score: int
    top_depth2_candidates: int
    best_long_range_score: float
    top_long_range_candidates: int
    policy_new_atoms: int
    policy_correct_atoms: int
    policy_precision: float
    policy_hidden_recall_gain: float
    latent_marking_active: bool
    latent_marking_residual: float
    latent_new_atoms: int
    latent_correct_atoms: int
    latent_precision: float
    latent_hidden_recall_gain: float
    batch_actions: int
    batch_new_atoms: int
    batch_correct_atoms: int
    batch_precision: float
    batch_hidden_recall_gain: float
    latent_batch_actions: int
    latent_batch_new_atoms: int
    latent_batch_correct_atoms: int
    latent_batch_precision: float
    latent_batch_hidden_recall_gain: float
    strata: Tuple[ScoreStratum, ...]


def _transpose(matrix: Matrix) -> Matrix:
    return tuple(tuple(matrix[column][row] for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _matmul(left: Matrix, right: Matrix) -> Matrix:
    return tuple(tuple(sum(left[row][index] * right[index][column]
                           for index in range(3))
                       for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _matrix_key(matrix: Matrix, translation: Vector) -> Tuple[int, ...]:
    return (tuple(round(value / 1e-5)
                  for row in matrix for value in row) +
            tuple(round(value / 1e-5) for value in translation))


def _rotation_key(matrix: Matrix) -> Tuple[int, ...]:
    return tuple(round(value / 1e-5) for row in matrix for value in row)


def _three_wave_state(training, oracle):
    local = blind.learn_grammar(
        training.positions, training.species, marking_radius_scale=2.25)
    macro = blind.learn_grammar(
        training.positions, training.species, template_level=2)
    refinement = blind.learn_grammar(
        training.positions, training.species, marking_radius_scale=3.0)
    state = {blind._site_key(point): blind.AtomState(
        chemical, local.training_cluster_types[index], point)
        for index, (point, chemical) in enumerate(
            zip(training.positions, training.species))}
    frontier = None
    for wave in (1, 2, 3):
        grammar = local if wave <= 2 else macro
        positions = tuple(atom.position for atom in state.values())
        species = tuple(atom.species for atom in state.values())
        cluster_types = tuple(atom.cluster_type for atom in state.values())
        proposals = blind.propose_first_wave(
            positions, species, grammar, (0.0, 0.0, 0.0), 15.0,
            use_marking=wave == 1,
            minimum_overlap=3 if wave <= 2 else 6,
            anchor_keys=frontier, cluster_types=cluster_types,
            use_cluster_colors=False)
        if wave == 1:
            additions = blind.accept_compatible_patches(
                proposals, frozenset(state), local)[1]
        else:
            additions = blind.refine_proposed_sites(
                proposals, state, refinement,
                use_cluster_sections=wave >= 3)
        state.update(additions)
        frontier = frozenset(
            key for key, atom in state.items()
            if any(blind._norm(blind._subtract(
                atom.position, new_atom.position))
                <= macro.cluster_radius + 1e-6
                for new_atom in additions.values()))
    return state, refinement


def _mark_new_sites(
    sites: Dict[Tuple[Tuple[int, int, int], str], Vector],
    state: Dict[Tuple[int, int, int], blind.AtomState],
    grammar: blind.LearnedGrammar,
    minimum_section_support: int = 3,
) -> frozenset[Tuple[Tuple[int, int, int], str]]:
    """Apply the learned bounded section marking to a macro proposal."""
    spatial = blind._spatial_index(state.values(), grammar.marking_radius)
    additions: Dict[Tuple[int, int, int], blind.AtomState] = {}
    accepted = set()
    for (key, chemical), point in sorted(sites.items()):
        section = []
        valid = True
        for existing in blind._nearby(
                point, spatial, grammar.marking_radius,
                grammar.marking_radius):
            distance = dag._norm(dag._subtract(point, existing.position))
            if distance < 0.5 * grammar.nearest_neighbor_scale:
                valid = False
                break
            relation = (chemical, existing.species,
                        blind._distance_bin(distance))
            if relation not in grammar.allowed_sections:
                valid = False
                break
            section.append((existing.species,
                            blind._distance_bin(distance)))
        if (not valid or len(section) < minimum_section_support or
                not blind._section_is_learned(
                chemical, section, grammar)):
            continue
        if not blind._compatible_with_additions(
                point, chemical, additions, grammar):
            continue
        additions[key] = blind.AtomState(chemical, -1, point)
        accepted.add((key, chemical))
    return frozenset(accepted)


def _learn_pair_marking(
    positions: Sequence[Vector], species: Sequence[str], radius: float,
) -> Counter[Tuple[str, str, int]]:
    marking: Counter[Tuple[str, str, int]] = Counter()
    for first in range(len(positions)):
        for second in range(first + 1, len(positions)):
            distance = dag._norm(dag._subtract(
                positions[first], positions[second]))
            if distance > radius + 1e-6:
                continue
            pair = tuple(sorted((species[first], species[second])))
            marking[(pair[0], pair[1],
                     blind._distance_bin(distance, 1e-3))] += 1
    return marking


def _pair_marking_score(
    marked: frozenset[Tuple[Tuple[int, int, int], str]],
    state: Dict[Tuple[int, int, int], blind.AtomState],
    marking: Counter[Tuple[str, str, int]],
    radius: float,
) -> Tuple[
        float,
        frozenset[Tuple[Tuple[int, int, int], str]]]:
    proposed = [
        blind.AtomState(
            chemical, -1, tuple(value * 1e-5 for value in key))
        for key, chemical in marked]
    existing = tuple(state.values())
    matched = 0
    total = 0
    log_support = 0.0
    fully_supported = set()
    for index, atom in enumerate(proposed):
        atom_matched = 0
        atom_total = 0
        others = existing + tuple(
            other for other_index, other in enumerate(proposed)
            if other_index != index)
        for other in others:
            distance = dag._norm(dag._subtract(
                atom.position, other.position))
            if distance > radius + 1e-6:
                continue
            pair = tuple(sorted((atom.species, other.species)))
            count = marking.get((
                pair[0], pair[1],
                blind._distance_bin(distance, 1e-3)), 0)
            total += 1
            atom_total += 1
            if count:
                matched += 1
                atom_matched += 1
                log_support += math.log1p(count)
        if atom_total and atom_matched == atom_total:
            fully_supported.add((
                blind._site_key(atom.position), atom.species))
    if not total:
        return 0.0, frozenset()
    # Exact support fraction dominates; frequency resolves equal-support ties.
    return (matched / total + 1e-6 * log_support / total,
            frozenset(fully_supported))


def _learn_module_marking(configuration) -> ModuleMarking:
    from materials_gcts_icosahedral_modelset import (
        infer_model, project, star_vectors, vector_norm)
    unit, lifted, window, thresholds, residual = infer_model(configuration)
    internal_vectors = star_vectors(-1.0 / unit)
    radii_by_species: Dict[str, list[float]] = {}
    for lift, chemical in lifted.items():
        radii_by_species.setdefault(chemical, []).append(
            vector_norm(project(lift, internal_vectors)))
    ordered = tuple(sorted(
        radii_by_species,
        key=lambda chemical: (
            sum(radii_by_species[chemical]) /
            len(radii_by_species[chemical]))))
    return ModuleMarking(
        unit, window, tuple(thresholds), ordered, residual)


def _apply_module_marking(
    marked: frozenset[Tuple[Tuple[int, int, int], str]],
    marking: ModuleMarking,
    maximum_residual: float = 1e-5,
) -> frozenset[Tuple[Tuple[int, int, int], str]]:
    from materials_gcts_icosahedral_modelset import (
        learned_species, lift_point, project, star_vectors, vector_norm)
    if marking.residual > maximum_residual:
        return frozenset()
    internal_vectors = star_vectors(-1.0 / marking.unit)
    physical_vectors = star_vectors(marking.unit)
    accepted = set()
    for key, chemical in marked:
        point = tuple(value * 1e-5 for value in key)
        lift, residual = lift_point(point, marking.unit)
        if residual > maximum_residual:
            continue
        internal_radius = vector_norm(project(lift, internal_vectors))
        if internal_radius > marking.window + 1e-8:
            continue
        if learned_species(
                internal_radius, marking.ordered_species,
                marking.thresholds) != chemical:
            continue
        canonical_point = project(lift, physical_vectors)
        accepted.add((blind._site_key(canonical_point), chemical))
    return frozenset(accepted)


def _match_state_levels(
    training_positions: Sequence[Vector],
    training_species: Sequence[str],
    training_model,
    state_positions: Sequence[Vector],
    state_species: Sequence[str],
    maximum_levels: int = 2,
) -> Tuple[
        Tuple[int, ...],
        Tuple[Tuple[OrientedOccurrence, ...], ...],
        Tuple[int, ...]]:
    radii, training_levels, training_labels = training_model
    labels: Sequence[Hashable] = state_species
    mapped_counts = []
    oriented = ()
    oriented_levels = []
    mapped = ()
    for level in range(maximum_levels):
        provisional = learn_cluster_candidates(
            labels, state_positions, neighbor_count=None, radius=radii[level],
            descriptor_tolerance=1e-5, minimum_occurrences=1)
        learned = dag._split_by_exact_congruence(
            provisional, labels, state_positions)
        mapped_list = [-1] * len(state_positions)
        occurrences = []
        training_input: Sequence[Hashable] = (
            training_species if level == 0 else training_labels[level - 1])
        for state_type in learned.cluster_types:
            state_members = state_type.representative_members
            state_center = state_members[0]
            state_offsets = tuple(dag._subtract(
                state_positions[index], state_positions[state_center])
                for index in state_members)
            state_labels = tuple(labels[index] for index in state_members)
            match = None
            for training_type in training_levels[level].cluster_types:
                if (len(training_type.representative_members) !=
                        len(state_members)):
                    continue
                members = training_type.representative_members
                center = members[0]
                offsets = tuple(dag._subtract(
                    training_positions[index], training_positions[center])
                    for index in members)
                colors = tuple(training_input[index] for index in members)
                if dag._register_colored_supports(
                        offsets, colors, state_offsets, state_labels,
                        allow_reflection=False) is not None:
                    match = (training_type, offsets, colors)
                    break
            if match is None:
                continue
            training_type, offsets, colors = match
            for occurrence in state_type.occurrences:
                mapped_list[occurrence.center_index] = training_type.type_id
                center = occurrence.center_index
                target_offsets = tuple(dag._subtract(
                    state_positions[index], state_positions[center])
                    for index in occurrence.member_indices)
                target_colors = tuple(labels[index]
                                      for index in occurrence.member_indices)
                rotation = dag._register_colored_supports(
                    offsets, colors, target_offsets, target_colors,
                    allow_reflection=False)
                if rotation is not None:
                    occurrences.append(OrientedOccurrence(
                        training_type.type_id,
                        state_positions[center], rotation))
        mapped = tuple(mapped_list)
        mapped_counts.append(sum(value >= 0 for value in mapped))
        labels = mapped
        oriented = tuple(occurrences)
        oriented_levels.append(oriented)
    return mapped, tuple(oriented_levels), tuple(mapped_counts)


def _parent_candidates(
    nodes: Sequence[dag.DagNode],
    oriented: Sequence[OrientedOccurrence],
    anchors: Optional[Sequence[OrientedOccurrence]] = None,
) -> Tuple[FrontierCandidate, ...]:
    child_set = {(item.type_id, blind._site_key(item.center),
                  _rotation_key(item.rotation))
                 for item in oriented}
    candidates = {}
    by_type: Dict[int, list[OrientedOccurrence]] = {}
    for item in (oriented if anchors is None else anchors):
        by_type.setdefault(item.type_id, []).append(item)
    for parent in nodes:
        for child in parent.children:
            for occurrence in by_type.get(child.child_type, ()):
                rotation = _matmul(
                    _transpose(child.rotation), occurrence.rotation)
                translation = dag._subtract(
                    occurrence.center,
                    dag._matvec(rotation, child.translation))
                key = (parent.type_id, _matrix_key(rotation, translation))
                if key in candidates:
                    continue
                score = sum(
                    (other.child_type, blind._site_key(dag._add(
                        translation,
                        dag._matvec(rotation, other.translation))),
                     _rotation_key(_matmul(other.rotation, rotation)))
                    in child_set for other in parent.children)
                candidates[key] = FrontierCandidate(
                    score, parent.type_id, rotation, translation)
    return tuple(candidates.values())


def _overlap_marking_nodes(
    positions: Sequence[Vector], training_model,
    child_rotations: Optional[Dict[Tuple[int, int], Matrix]] = None,
) -> Tuple[dag.DagNode, ...]:
    """Compile full overlapping child-port sections for every level-3 type.

    The transform DAG stores a sparse nonoverlapping child cover for compact
    expansion.  A GCTS marking has a different job and retains every learned
    level-2 occurrence centered in the parent support, including overlaps.
    """
    _, learned_levels, labels_by_level = training_model
    child_level = learned_levels[1]
    parent_level = learned_levels[2]
    rotations = child_rotations or dag._occurrence_rotations(
        2, child_level, labels_by_level[0], positions)
    occurrences = {}
    for child_type in child_level.cluster_types:
        for occurrence in child_type.occurrences:
            occurrences[occurrence.center_index] = (
                child_type.type_id, occurrence)
    nodes = []
    for parent_type in parent_level.cluster_types:
        parent_center = parent_type.representative_center
        ports = []
        for center in parent_type.representative_members:
            child = occurrences.get(center)
            if child is None:
                continue
            child_type, _ = child
            ports.append(dag.ChildTransform(
                child_type,
                dag._subtract(positions[center], positions[parent_center]),
                rotations[(child_type, center)], 1))
        nodes.append(dag.DagNode(
            3, parent_type.type_id,
            len(parent_type.representative_members), tuple(ports), ()))
    return tuple(nodes)


def _rescore_with_overlap_marking(
    candidates: Sequence[FrontierCandidate],
    marking_nodes: Sequence[dag.DagNode],
    oriented: Sequence[OrientedOccurrence],
) -> Tuple[FrontierCandidate, ...]:
    candidate_by_key = {
        (candidate.parent_type,
         _matrix_key(candidate.rotation, candidate.translation)): candidate
        for candidate in candidates}
    scores: Counter[Tuple[int, Tuple[int, ...]]] = Counter()
    observed_by_type: Dict[int, list[OrientedOccurrence]] = {}
    seen_observed = set()
    for occurrence in oriented:
        observed_key = (occurrence.type_id,
                        blind._site_key(occurrence.center),
                        _rotation_key(occurrence.rotation))
        if observed_key in seen_observed:
            continue
        seen_observed.add(observed_key)
        observed_by_type.setdefault(
            occurrence.type_id, []).append(occurrence)
    for node in marking_nodes:
        for port in node.children:
            inverse_port = _transpose(port.rotation)
            for occurrence in observed_by_type.get(port.child_type, ()):
                rotation = _matmul(inverse_port, occurrence.rotation)
                translation = dag._subtract(
                    occurrence.center,
                    dag._matvec(rotation, port.translation))
                key = (node.type_id, _matrix_key(rotation, translation))
                if key in candidate_by_key:
                    scores[key] += 1
    return tuple(FrontierCandidate(
        scores[(candidate.parent_type,
                _matrix_key(candidate.rotation, candidate.translation))],
        candidate.parent_type, candidate.rotation, candidate.translation)
        for candidate in candidates)


def _exterior_marking_ports(
    positions: Sequence[Vector], training_model,
    minimum_frequency: float = 0.25,
    child_rotations: Optional[Dict[Tuple[int, int], Matrix]] = None,
    parent_rotations: Optional[Dict[Tuple[int, int], Matrix]] = None,
) -> Tuple[Tuple[ExteriorPort, ...], ...]:
    """Learn rotation-canonical ports in a bounded halo outside each parent.

    A port must recur for the same parent type in at least two occurrences and
    in ``minimum_frequency`` of those occurrences.  This rejects accidental
    relations to the finite training boundary while retaining contextual marks
    that are not already encoded by the parent's internal support.
    """
    radii, learned_levels, labels_by_level = training_model
    child_level = learned_levels[1]
    parent_level = learned_levels[2]
    child_rotations = child_rotations or dag._occurrence_rotations(
        2, child_level, labels_by_level[0], positions)
    parent_rotations = parent_rotations or dag._occurrence_rotations(
        3, parent_level, labels_by_level[1], positions)
    child_at_center = {}
    for child_type in child_level.cluster_types:
        for occurrence in child_type.occurrences:
            child_at_center[occurrence.center_index] = child_type.type_id
    halo_radius = radii[2] + radii[0]
    all_ports = []
    for parent_type in parent_level.cluster_types:
        counts: Counter[Tuple[int, Tuple[int, ...]]] = Counter()
        examples = {}
        occurrence_count = len(parent_type.occurrences)
        for occurrence in parent_type.occurrences:
            parent_center = occurrence.center_index
            parent_rotation = parent_rotations[
                (parent_type.type_id, parent_center)]
            inverse_parent = _transpose(parent_rotation)
            internal = frozenset(occurrence.member_indices)
            seen = set()
            for child_center, child_type in child_at_center.items():
                if child_center in internal:
                    continue
                delta = dag._subtract(
                    positions[child_center], positions[parent_center])
                distance = dag._norm(delta)
                if distance > halo_radius + 1e-6:
                    continue
                relative_translation = dag._matvec(inverse_parent, delta)
                relative_rotation = _matmul(
                    child_rotations[(child_type, child_center)],
                    inverse_parent)
                key = (child_type,
                       _matrix_key(relative_rotation, relative_translation))
                if key in seen:
                    continue
                seen.add(key)
                counts[key] += 1
                examples[key] = ExteriorPort(
                    child_type, relative_translation,
                    relative_rotation, 0.0)
        ports = []
        for key, count in counts.items():
            frequency = count / max(1, occurrence_count)
            if count < 2 or frequency < minimum_frequency:
                continue
            example = examples[key]
            ports.append(ExteriorPort(
                example.child_type, example.translation,
                example.rotation, frequency))
        all_ports.append(tuple(sorted(
            ports, key=lambda port: (
                -port.frequency, port.child_type,
                _matrix_key(port.rotation, port.translation)))))
    return tuple(all_ports)


def _rescore_with_exterior_marking(
    candidates: Sequence[FrontierCandidate],
    exterior_ports: Sequence[Sequence[ExteriorPort]],
    oriented: Sequence[OrientedOccurrence],
) -> Tuple[FrontierCandidate, ...]:
    candidate_by_key = {
        (candidate.parent_type,
         _matrix_key(candidate.rotation, candidate.translation)): candidate
        for candidate in candidates}
    scores: Dict[Tuple[int, Tuple[int, ...]], float] = {}
    observed_by_type: Dict[int, list[OrientedOccurrence]] = {}
    seen_observed = set()
    for occurrence in oriented:
        observed_key = (occurrence.type_id,
                        blind._site_key(occurrence.center),
                        _rotation_key(occurrence.rotation))
        if observed_key in seen_observed:
            continue
        seen_observed.add(observed_key)
        observed_by_type.setdefault(
            occurrence.type_id, []).append(occurrence)
    for parent_type, ports in enumerate(exterior_ports):
        for port in ports:
            inverse_port = _transpose(port.rotation)
            for occurrence in observed_by_type.get(port.child_type, ()):
                rotation = _matmul(inverse_port, occurrence.rotation)
                translation = dag._subtract(
                    occurrence.center,
                    dag._matvec(rotation, port.translation))
                key = (parent_type, _matrix_key(rotation, translation))
                if key in candidate_by_key:
                    scores[key] = scores.get(key, 0.0) + port.frequency
    return tuple(FrontierCandidate(
        candidate.child_matches, candidate.parent_type,
        candidate.rotation, candidate.translation,
        scores.get((candidate.parent_type,
                    _matrix_key(candidate.rotation,
                                candidate.translation)), 0.0))
        for candidate in candidates)


def _exterior_lookahead_score(
    candidate: FrontierCandidate,
    ports: Sequence[ExteriorPort],
    levels: Sequence[Sequence[dag.DagNode]],
    current: frozenset[Tuple[Tuple[int, int, int], str]],
    marked: frozenset[Tuple[Tuple[int, int, int], str]],
    confinement_radius: float,
    expansion_cache: Dict[int, Tuple[Tuple[str, Vector], ...]],
    minimum_site_port_support: int = 1,
) -> Tuple[
        float,
        frozenset[Tuple[Tuple[int, int, int], str]],
        Tuple[OrientedOccurrence, ...]]:
    """Score exterior child clusters made visible by a proposed parent."""
    available = current | marked
    occupied = {key: chemical for key, chemical in available}
    score = 0.0
    supported_sites: Counter[Tuple[Tuple[int, int, int], str]] = Counter()
    supported_occurrences = {}
    for port in ports:
        leaves = expansion_cache.setdefault(
            port.child_type, dag.expand_node(levels, 2, port.child_type))
        combined_rotation = _matmul(port.rotation, candidate.rotation)
        child_center = dag._add(
            candidate.translation,
            dag._matvec(candidate.rotation, port.translation))
        overlap = 0
        new_overlap = 0
        visible = 0
        conflict = False
        port_new_sites = set()
        for chemical, offset in leaves:
            point = dag._add(
                child_center, dag._matvec(combined_rotation, offset))
            if dag._norm(point) > confinement_radius + 1e-5:
                continue
            visible += 1
            key = blind._site_key(point)
            if key in occupied and occupied[key] != chemical:
                conflict = True
                break
            site = (key, chemical)
            if site in available:
                overlap += 1
            if site in marked:
                new_overlap += 1
                port_new_sites.add(site)
        if (not conflict and visible >= 3 and overlap >= 3 and
                new_overlap >= 1):
            score += port.frequency * overlap / visible
            supported_sites.update(port_new_sites)
            occurrence = OrientedOccurrence(
                port.child_type, child_center,
                combined_rotation, overlap)
            supported_occurrences[
                (port.child_type, blind._site_key(child_center),
                 _rotation_key(combined_rotation))] = occurrence
    return (score, frozenset(
        site for site, count in supported_sites.items()
        if count >= minimum_site_port_support),
        tuple(supported_occurrences.values()))


def _depth2_branch_score(
    first: FrontierCandidate,
    new_occurrences: Sequence[OrientedOccurrence],
    existing_occurrences: Sequence[OrientedOccurrence],
    marking_nodes: Sequence[dag.DagNode],
    levels: Sequence[Sequence[dag.DagNode]],
    level3_expansions: Dict[int, Tuple[Tuple[str, Vector], ...]],
    occupied: frozenset[Tuple[Tuple[int, int, int], str]],
    confinement_radius: float,
) -> int:
    if not new_occurrences:
        return 0
    augmented = tuple(existing_occurrences) + tuple(new_occurrences)
    second = _parent_candidates(
        levels[2], augmented, anchors=new_occurrences)
    second = _rescore_with_overlap_marking(
        second, marking_nodes, augmented)
    first_key = (first.parent_type,
                 _matrix_key(first.rotation, first.translation))
    best = 0
    for candidate in second:
        key = (candidate.parent_type,
               _matrix_key(candidate.rotation, candidate.translation))
        if key == first_key:
            continue
        adds_site = False
        for chemical, offset in level3_expansions[candidate.parent_type]:
            point = dag._add(
                candidate.translation,
                dag._matvec(candidate.rotation, offset))
            if dag._norm(point) > confinement_radius + 1e-5:
                continue
            if (blind._site_key(point), chemical) not in occupied:
                adds_site = True
                break
        if adds_site:
            best = max(best, candidate.child_matches)
    return best


def _lift_hypotheses(
    nodes: Sequence[dag.DagNode],
    children: Sequence[OrientedOccurrence],
    minimum_matches: int,
) -> Tuple[OrientedOccurrence, ...]:
    return tuple(OrientedOccurrence(
        candidate.parent_type, candidate.translation,
        candidate.rotation, candidate.child_matches)
        for candidate in _parent_candidates(nodes, children)
        if candidate.child_matches >= minimum_matches)


def _partial_level1_hypotheses(
    nodes: Sequence[dag.DagNode],
    positions: Sequence[Vector],
    species: Sequence[str],
    radius: float,
) -> Tuple[OrientedOccurrence, ...]:
    state = {blind._site_key(point): chemical
             for point, chemical in zip(positions, species)}
    atoms = tuple(blind.AtomState(chemical, -1, point)
                  for point, chemical in zip(positions, species))
    spatial = blind._spatial_index(atoms, radius)
    # Compile every learned cluster's rotation-defining connector pairs into a
    # shared marking atlas.  The earlier implementation rescanned every atom
    # neighborhood once per cluster type; this index scans it once and lets a
    # connector key name the few compatible cluster frames directly.
    templates = {}
    pair_atlas: Dict[
        str, Dict[Tuple[object, ...], list[Tuple[int, int, int]]]] = {}
    for node in nodes:
        entries = node.residual_offsets
        center_species = next(
            chemical for chemical, offset in entries
            if dag._norm(offset) < 1e-6)
        template = blind.RigidTemplate(
            center_species, node.type_id,
            tuple(offset for _, offset in entries),
            tuple(chemical for chemical, _ in entries),
            (-1,) * len(entries))
        pair_index = blind._template_pair_index(
            template, use_cluster_colors=False)
        templates[node.type_id] = (entries, template)
        atlas = pair_atlas.setdefault(center_species, {})
        for key, pairs in tuple(pair_index.items())[:8]:
            # Pairs in one key have identical species and Gram data.  They are
            # symmetry-equivalent pose marks for this cluster, so one canonical
            # representative is sufficient; keeping every equivalent pair
            # recreates the combinatorial explosion the marking should remove.
            atlas.setdefault(key, []).extend(
                (node.type_id, source_first, source_second)
                for source_first, source_second in pairs[:1])

    hypotheses = {}
    for anchor in atoms:
        atlas = pair_atlas.get(anchor.species)
        if not atlas:
            continue
        neighbors = tuple(item for item in blind._nearby(
            anchor.position, spatial, radius, radius)
            if item.position != anchor.position)
        seen = set()
        for first_index, first_atom in enumerate(neighbors):
            first_vector = dag._subtract(
                first_atom.position, anchor.position)
            for second_index, second_atom in enumerate(neighbors):
                if first_index == second_index:
                    continue
                second_vector = dag._subtract(
                    second_atom.position, anchor.position)
                matches = atlas.get(blind._pair_key(
                    first_atom.species, second_atom.species,
                    first_vector, second_vector), ())
                for node_type, source_first, source_second in matches:
                    entries, template = templates[node_type]
                    source_frame = blind._frame(
                        template.offsets[source_first],
                        template.offsets[source_second])
                    target_frame = blind._frame(
                        first_vector, second_vector)
                    if source_frame is None or target_frame is None:
                        continue
                    rotation: Matrix = tuple(tuple(
                        blind._rotate_between(
                            basis, source_frame, target_frame)[column]
                        for column in range(3))
                        for basis in ((1.0, 0.0, 0.0),
                                      (0.0, 1.0, 0.0),
                                      (0.0, 0.0, 1.0)))  # type: ignore[assignment]
                    key = (node_type,
                           _matrix_key(rotation, anchor.position))
                    if key in seen:
                        continue
                    seen.add(key)
                    overlap = 0
                    conflict = False
                    for chemical, offset in entries:
                        point = dag._add(
                            anchor.position,
                            dag._matvec(rotation, offset))
                        site = blind._site_key(point)
                        if site in state:
                            if state[site] != chemical:
                                conflict = True
                                break
                            overlap += 1
                    if not conflict and overlap >= 3:
                        hypotheses[key] = OrientedOccurrence(
                            node_type, anchor.position,
                            rotation, overlap)
    return tuple(hypotheses.values())


def _beam_hypotheses(
    hypotheses: Sequence[OrientedOccurrence],
    *,
    maximum_per_center: int,
    maximum_total: int,
    frontier_first: bool = False,
) -> Tuple[OrientedOccurrence, ...]:
    grouped: Dict[Tuple[int, Tuple[int, int, int]], list[OrientedOccurrence]] = {}
    for hypothesis in hypotheses:
        grouped.setdefault(
            (hypothesis.type_id, blind._site_key(hypothesis.center)),
            []).append(hypothesis)
    retained = []
    for values in grouped.values():
        retained.extend(sorted(
            values, key=lambda item: item.child_matches, reverse=True)
            [:maximum_per_center])
    def rank(item: OrientedOccurrence) -> Tuple[float, float]:
        if frontier_first:
            return dag._norm(item.center), float(item.child_matches)
        return float(item.child_matches), dag._norm(item.center)
    return tuple(sorted(retained, key=rank, reverse=True)[:maximum_total])


def evaluate() -> DagBlindFrontierResult:
    from materials_gcts_icosahedral_modelset import oracle_patch
    training, _ = oracle_patch(3, 9.0)
    oracle, _ = oracle_patch(4, 15.0)
    state, refinement = _three_wave_state(training, oracle)
    state_positions = tuple(atom.position for atom in state.values())
    state_species = tuple(atom.species for atom in state.values())
    training_model = dag._learn_levels(
        training.positions, training.species, 3, 2.2)
    module_marking = _learn_module_marking(training)
    dag_result, levels = dag.build_transform_dag(
        training.name, training.positions, training.species,
        prelearned=training_model)
    _, oriented_levels, mapped_counts = _match_state_levels(
        training.positions, training.species, training_model,
        state_positions, state_species)
    partial_level1 = _partial_level1_hypotheses(
        levels[0], state_positions, state_species,
        training_model[0][0])
    level1_hypotheses = _beam_hypotheses(
        tuple(oriented_levels[0]) + partial_level1,
        maximum_per_center=4, maximum_total=500, frontier_first=True)
    level2_hypotheses = _beam_hypotheses(
        _lift_hypotheses(
            levels[1], level1_hypotheses, minimum_matches=1),
        maximum_per_center=4, maximum_total=500, frontier_first=True)
    candidates = _parent_candidates(levels[2], level2_hypotheses)
    generated_parent_candidates = len(candidates)
    learned_levels = training_model[1]
    labels_by_level = training_model[2]
    child_rotations = dag._occurrence_rotations(
        2, learned_levels[1], labels_by_level[0], training.positions)
    parent_rotations = dag._occurrence_rotations(
        3, learned_levels[2], labels_by_level[1], training.positions)
    marking_nodes = _overlap_marking_nodes(
        training.positions, training_model, child_rotations)
    candidates = _rescore_with_overlap_marking(
        candidates, marking_nodes, level2_hypotheses)
    exterior_ports = _exterior_marking_ports(
        training.positions, training_model,
        child_rotations=child_rotations,
        parent_rotations=parent_rotations)
    candidates = _rescore_with_exterior_marking(
        candidates, exterior_ports, level2_hypotheses)
    current = frozenset((key, atom.species) for key, atom in state.items())
    long_range_radius = training_model[0][2]
    pair_marking = _learn_pair_marking(
        training.positions, training.species, long_range_radius)
    oracle_set = {(blind._site_key(point), chemical)
                  for point, chemical in zip(oracle.positions, oracle.species)}
    frontier = []
    closed_best = 0
    level3_expansions = {
        node.type_id: dag.expand_node(levels, 3, node.type_id)
        for node in levels[2]}
    for candidate in candidates:
        leaves = level3_expansions[candidate.parent_type]
        transformed = {
            (blind._site_key(point), chemical): point
            for chemical, offset in leaves
            for point in (dag._add(candidate.translation,
                                   dag._matvec(candidate.rotation, offset)),)
            if dag._norm(point) <= 15.0 + 1e-5}
        new = {site: point for site, point in transformed.items()
               if site not in current}
        if not new:
            closed_best = max(closed_best, candidate.child_matches)
            continue
        frontier.append((candidate, new))
    best_frontier_score = max(
        (item[0].child_matches for item in frontier), default=0)
    best_exterior_score = max(
        (item[0].exterior_score for item in frontier
         if item[0].child_matches == best_frontier_score),
        default=0.0)
    top_marked_candidates = sum(
        candidate.child_matches == best_frontier_score and
        abs(candidate.exterior_score - best_exterior_score) < 1e-9
        for candidate, _ in frontier)
    evaluated = []
    expansion_cache: Dict[int, Tuple[Tuple[str, Vector], ...]] = {}
    for candidate, new in frontier:
        if (candidate.child_matches != best_frontier_score or
                abs(candidate.exterior_score - best_exterior_score) >= 1e-9):
            continue
        marked = _mark_new_sites(new, state, refinement)
        if not marked:
            continue
        (lookahead_score, lookahead_supported,
         future_occurrences) = _exterior_lookahead_score(
            candidate, exterior_ports[candidate.parent_type], levels,
            current, marked, 15.0, expansion_cache)
        if lookahead_score > 0.0:
            if not lookahead_supported:
                continue
            marked = lookahead_supported
        candidate = FrontierCandidate(
            candidate.child_matches, candidate.parent_type,
            candidate.rotation, candidate.translation,
            candidate.exterior_score, lookahead_score)
        correct = len(marked & oracle_set)
        evaluated.append((candidate, len(new), len(marked), correct,
                          marked, future_occurrences))
    best_lookahead_score = max(
        (item[0].lookahead_score for item in evaluated), default=0.0)
    top_lookahead_candidates = sum(
        abs(item[0].lookahead_score - best_lookahead_score) < 1e-9
        for item in evaluated)
    lookahead_pool = [
        item for item in evaluated
        if abs(item[0].lookahead_score - best_lookahead_score) < 1e-9]
    depth2_evaluated = []
    for candidate, raw_size, size, correct, marked, future in lookahead_pool:
        depth2_score = _depth2_branch_score(
            candidate, future, level2_hypotheses, marking_nodes,
            levels, level3_expansions, current | marked, 15.0)
        candidate = FrontierCandidate(
            candidate.child_matches, candidate.parent_type,
            candidate.rotation, candidate.translation,
            candidate.exterior_score, candidate.lookahead_score,
            depth2_score)
        depth2_evaluated.append((
            candidate, raw_size, size, correct, marked, future))
    best_depth2_score = max(
        (item[0].depth2_score for item in depth2_evaluated), default=0)
    top_depth2_candidates = sum(
        item[0].depth2_score == best_depth2_score
        for item in depth2_evaluated)
    depth2_pool = [
        item for item in depth2_evaluated
        if item[0].depth2_score == best_depth2_score]
    long_range_evaluated = []
    for candidate, raw_size, size, correct, marked, future in depth2_pool:
        long_range_score, _ = _pair_marking_score(
            marked, state, pair_marking, long_range_radius)
        candidate = FrontierCandidate(
            candidate.child_matches, candidate.parent_type,
            candidate.rotation, candidate.translation,
            candidate.exterior_score, candidate.lookahead_score,
            candidate.depth2_score, long_range_score)
        long_range_evaluated.append((
            candidate, raw_size, size, correct, marked, future))
    best_long_range_score = max(
        (item[0].long_range_score for item in long_range_evaluated),
        default=0.0)
    top_long_range_candidates = sum(
        abs(item[0].long_range_score - best_long_range_score) < 1e-12
        for item in long_range_evaluated)
    policy_pool = [
        item for item in long_range_evaluated
        if abs(item[0].long_range_score - best_long_range_score) < 1e-12]
    strata = []
    for score in sorted({item[0].child_matches for item in policy_pool},
                        reverse=True):
        group = [item for item in policy_pool
                 if item[0].child_matches == score]
        precisions = [correct / size for _, _, size, correct, _, _ in group]
        strata.append(ScoreStratum(
            score, len(group), max(precisions),
            sum(precisions) / len(precisions),
            max(correct for _, _, _, correct, _, _ in group)))
    if not evaluated:
        return DagBlindFrontierResult(
            training_atoms=len(training.positions), state_atoms=len(state),
            hidden_atoms=len(oracle.positions) - len(training.positions),
            mapped_level1_centers=mapped_counts[0],
            mapped_level2_centers=mapped_counts[1],
            partial_level1_hypotheses=len(partial_level1),
            retained_level1_hypotheses=len(level1_hypotheses),
            level2_hypotheses=len(level2_hypotheses),
            generated_parent_candidates=generated_parent_candidates,
            parent_candidates=len(candidates),
            frontier_candidates=len(frontier),
            best_closed_parent_score=closed_best,
            best_frontier_score=best_frontier_score,
            best_exterior_score=best_exterior_score,
            top_marked_candidates=top_marked_candidates,
            best_lookahead_score=best_lookahead_score,
            top_lookahead_candidates=top_lookahead_candidates,
            best_depth2_score=best_depth2_score,
            top_depth2_candidates=top_depth2_candidates,
            best_long_range_score=best_long_range_score,
            top_long_range_candidates=top_long_range_candidates,
            policy_new_atoms=0, policy_correct_atoms=0,
            policy_precision=0.0, policy_hidden_recall_gain=0.0,
            latent_marking_active=module_marking.residual <= 1e-5,
            latent_marking_residual=module_marking.residual,
            latent_new_atoms=0, latent_correct_atoms=0,
            latent_precision=0.0, latent_hidden_recall_gain=0.0,
            batch_actions=0, batch_new_atoms=0, batch_correct_atoms=0,
            batch_precision=0.0, batch_hidden_recall_gain=0.0,
            latent_batch_actions=0, latent_batch_new_atoms=0,
            latent_batch_correct_atoms=0, latent_batch_precision=0.0,
            latent_batch_hidden_recall_gain=0.0,
            strata=())
    selected = max(
        policy_pool,
        key=lambda item: (item[0].child_matches,
                          item[0].exterior_score,
                          item[0].lookahead_score,
                          item[0].depth2_score,
                          item[0].long_range_score,
                          item[2] / item[1], item[2]))
    _, _, size, correct, selected_marked, _ = selected
    latent_marked = _apply_module_marking(
        selected_marked, module_marking)
    latent_marked = frozenset(
        site for site in latent_marked if site not in current)
    latent_size = len(latent_marked)
    latent_correct = len(latent_marked & oracle_set)
    batch_additions: Dict[Tuple[int, int, int], blind.AtomState] = {}
    batch_actions = 0
    ordered_actions = sorted(
        policy_pool,
        key=lambda item: (item[0].lookahead_score,
                          item[2] / item[1], item[2]),
        reverse=True)
    for _, _, _, _, marked, _ in ordered_actions:
        proposed = []
        conflict = False
        for key, chemical in marked:
            if key in batch_additions:
                if batch_additions[key].species != chemical:
                    conflict = True
                    break
                continue
            point = tuple(value * 1e-5 for value in key)
            if not blind._compatible_with_additions(
                    point, chemical, batch_additions, refinement):
                conflict = True
                break
            proposed.append((key, blind.AtomState(chemical, -1, point)))
        if conflict or not proposed:
            continue
        batch_additions.update(proposed)
        batch_actions += 1
    batch_set = frozenset(
        (key, atom.species) for key, atom in batch_additions.items())
    batch_correct = len(batch_set & oracle_set)
    batch_size = len(batch_set)
    latent_batch_additions: Dict[
        Tuple[int, int, int], blind.AtomState] = {}
    latent_batch_actions = 0
    for _, _, _, _, marked, _ in ordered_actions:
        marked = _apply_module_marking(marked, module_marking)
        marked = frozenset(site for site in marked if site not in current)
        proposed = []
        conflict = False
        for key, chemical in marked:
            if key in latent_batch_additions:
                if latent_batch_additions[key].species != chemical:
                    conflict = True
                    break
                continue
            point = tuple(value * 1e-5 for value in key)
            if not blind._compatible_with_additions(
                    point, chemical, latent_batch_additions, refinement):
                conflict = True
                break
            proposed.append((key, blind.AtomState(chemical, -1, point)))
        if conflict or not proposed:
            continue
        latent_batch_additions.update(proposed)
        latent_batch_actions += 1
    latent_batch_set = frozenset(
        (key, atom.species)
        for key, atom in latent_batch_additions.items())
    latent_batch_correct = len(latent_batch_set & oracle_set)
    latent_batch_size = len(latent_batch_set)
    return DagBlindFrontierResult(
        training_atoms=len(training.positions), state_atoms=len(state),
        hidden_atoms=len(oracle.positions) - len(training.positions),
        mapped_level1_centers=mapped_counts[0],
        mapped_level2_centers=mapped_counts[1],
        partial_level1_hypotheses=len(partial_level1),
        retained_level1_hypotheses=len(level1_hypotheses),
        level2_hypotheses=len(level2_hypotheses),
        generated_parent_candidates=generated_parent_candidates,
        parent_candidates=len(candidates),
        frontier_candidates=len(frontier),
        best_closed_parent_score=closed_best,
        best_frontier_score=best_frontier_score,
        best_exterior_score=best_exterior_score,
        top_marked_candidates=top_marked_candidates,
        best_lookahead_score=best_lookahead_score,
        top_lookahead_candidates=top_lookahead_candidates,
        best_depth2_score=best_depth2_score,
        top_depth2_candidates=top_depth2_candidates,
        best_long_range_score=best_long_range_score,
        top_long_range_candidates=top_long_range_candidates,
        policy_new_atoms=size, policy_correct_atoms=correct,
        policy_precision=correct / size,
        policy_hidden_recall_gain=(
            correct / (len(oracle.positions) - len(training.positions))),
        latent_marking_active=module_marking.residual <= 1e-5,
        latent_marking_residual=module_marking.residual,
        latent_new_atoms=latent_size,
        latent_correct_atoms=latent_correct,
        latent_precision=latent_correct / max(1, latent_size),
        latent_hidden_recall_gain=(
            latent_correct /
            (len(oracle.positions) - len(training.positions))),
        batch_actions=batch_actions,
        batch_new_atoms=batch_size,
        batch_correct_atoms=batch_correct,
        batch_precision=batch_correct / max(1, batch_size),
        batch_hidden_recall_gain=(
            batch_correct /
            (len(oracle.positions) - len(training.positions))),
        latent_batch_actions=latent_batch_actions,
        latent_batch_new_atoms=latent_batch_size,
        latent_batch_correct_atoms=latent_batch_correct,
        latent_batch_precision=(
            latent_batch_correct / max(1, latent_batch_size)),
        latent_batch_hidden_recall_gain=(
            latent_batch_correct /
            (len(oracle.positions) - len(training.positions))),
        strata=tuple(strata))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
