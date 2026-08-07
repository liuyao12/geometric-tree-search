#!/usr/bin/env python3
"""Blind material continuation with rigid clusters and learned GCTS sections.

The learner sees only a finite core.  It extracts recurring local cluster
templates and the finite set of species-labelled pair distances in a bounded
halo.  At the frontier, three matching atoms determine a rigid orientation of
a template.  The learned halo section then accepts or rejects all connections
from proposed atoms to the current configuration.

Hidden annulus atoms are used only after proposal generation for scoring.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import DefaultDict, Dict, Iterable, Optional, Sequence, Tuple

from materials_recursive_gcts import learn_recursive_hierarchy

Vector = Tuple[float, float, float]
SiteKey = Tuple[int, int, int]


@dataclass(frozen=True)
class AtomState:
    species: str
    cluster_type: int
    position: Vector


@dataclass(frozen=True)
class RigidTemplate:
    center_species: str
    center_cluster_type: int
    offsets: Tuple[Vector, ...]
    species: Tuple[str, ...]
    cluster_types: Tuple[int, ...]


@dataclass(frozen=True)
class LearnedGrammar:
    template_level: int
    nearest_neighbor_scale: float
    cluster_radius: float
    marking_radius: float
    templates: Tuple[RigidTemplate, ...]
    allowed_sections: frozenset[Tuple[str, str, int]]
    allowed_star_sections: Tuple[Tuple[str, Tuple[Tuple[str, int], ...]], ...]
    allowed_colored_star_sections: Tuple[
        Tuple[int, Tuple[Tuple[int, int], ...]], ...]
    training_cluster_types: Tuple[int, ...]


@dataclass(frozen=True)
class AblationResult:
    candidate_patches: int
    proposed_sites: int
    correct_sites: int
    precision: float
    hidden_recall: float


@dataclass(frozen=True)
class BlindContinuationResult:
    system: str
    training_atoms: int
    hidden_atoms: int
    learned_cluster_templates: int
    learned_section_entries: int
    unmarked: AblationResult
    marked: AblationResult
    marking_precision_gain: float
    marking_false_positive_reduction: float


@dataclass(frozen=True)
class GrowthWave:
    wave: int
    candidate_patches: int
    accepted_patches: int
    added_sites: int
    total_sites: int
    precision: float
    hidden_recall: float


@dataclass(frozen=True)
class IteratedContinuationResult:
    system: str
    training_atoms: int
    hidden_atoms: int
    waves: Tuple[GrowthWave, ...]
    final_precision: float
    final_hidden_recall: float


def _add(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def _subtract(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def _scale(factor: float, vector: Sequence[float]) -> Vector:
    return tuple(factor * value for value in vector)  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _frame(first: Vector, second: Vector) -> Optional[Tuple[Vector, Vector, Vector]]:
    length = _norm(first)
    if length < 1e-8:
        return None
    e1 = _scale(1.0 / length, first)
    remainder = _subtract(second, _scale(_dot(second, e1), e1))
    remainder_length = _norm(remainder)
    if remainder_length < 1e-8:
        return None
    e2 = _scale(1.0 / remainder_length, remainder)
    return e1, e2, _cross(e1, e2)


def _rotate_between(
    vector: Vector,
    source: Tuple[Vector, Vector, Vector],
    target: Tuple[Vector, Vector, Vector],
) -> Vector:
    coordinates = tuple(_dot(vector, axis) for axis in source)
    return tuple(sum(coordinates[index] * target[index][axis]
                     for index in range(3)) for axis in range(3))  # type: ignore[return-value]


def _site_key(point: Sequence[float], tolerance: float = 1e-5) -> SiteKey:
    return tuple(round(value / tolerance) for value in point)  # type: ignore[return-value]


def _distance_bin(distance: float, tolerance: float = 1e-4) -> int:
    return round(distance / tolerance)


def _cell_key(point: Sequence[float], cell_size: float) -> Tuple[int, int, int]:
    return tuple(math.floor(value / cell_size) for value in point)  # type: ignore[return-value]


def _spatial_index(
    atoms: Iterable[AtomState], cell_size: float,
) -> Dict[Tuple[int, int, int], Tuple[AtomState, ...]]:
    buckets: DefaultDict[Tuple[int, int, int], list[AtomState]] = defaultdict(list)
    for atom in atoms:
        buckets[_cell_key(atom.position, cell_size)].append(atom)
    return {key: tuple(values) for key, values in buckets.items()}


def _nearby(
    point: Vector,
    index: Dict[Tuple[int, int, int], Tuple[AtomState, ...]],
    cell_size: float,
    radius: float,
) -> Tuple[AtomState, ...]:
    center = _cell_key(point, cell_size)
    reach = math.ceil(radius / cell_size)
    result = []
    for dx in range(-reach, reach + 1):
        for dy in range(-reach, reach + 1):
            for dz in range(-reach, reach + 1):
                for atom in index.get((center[0] + dx, center[1] + dy,
                                       center[2] + dz), ()):
                    if _norm(_subtract(point, atom.position)) <= radius + 1e-6:
                        result.append(atom)
    return tuple(result)


def _pair_key(
    first_species: str,
    second_species: str,
    first: Vector,
    second: Vector,
    first_cluster_type: int = -1,
    second_cluster_type: int = -1,
    use_cluster_colors: bool = False,
) -> Tuple[object, ...]:
    colors = ((first_cluster_type, second_cluster_type)
              if use_cluster_colors else ())
    return (first_species, second_species, *colors,
            _distance_bin(_norm(first), 1e-5),
            _distance_bin(_norm(second), 1e-5),
            _distance_bin(_norm(_subtract(first, second)), 1e-5))


def learn_grammar(
    positions: Sequence[Vector], species: Sequence[str],
    marking_radius_scale: float = 2.25,
    template_level: int = 1,
) -> LearnedGrammar:
    hierarchy, dictionaries = learn_recursive_hierarchy(
        "blind-training-core", positions, species,
        maximum_levels=template_level)
    models = dictionaries[template_level - 1]
    color_models = dictionaries[max(0, template_level - 2)]
    labels = [-1] * len(positions)
    for model in color_models:
        for center in model.occurrence_centers:
            labels[center] = model.type_id
    templates = []
    for model in models:
        if len(model.occurrence_centers) < 2 or len(model.representative_support) < 3:
            continue
        center = model.occurrence_centers[0]
        members = model.representative_support
        templates.append(RigidTemplate(
            center_species=species[center],
            center_cluster_type=labels[center],
            offsets=tuple(_subtract(positions[index], positions[center])
                          for index in members),
            species=tuple(species[index] for index in members),
            cluster_types=tuple(labels[index] for index in members),
        ))
    marking_radius = marking_radius_scale * hierarchy.nearest_neighbor_scale
    allowed = set()
    stars = []
    colored_stars = []
    for left, left_point in enumerate(positions):
        star = []
        colored_star = []
        for right, right_point in enumerate(positions):
            if left == right:
                continue
            distance = _norm(_subtract(left_point, right_point))
            if distance <= marking_radius + 1e-6:
                allowed.add((species[left], species[right],
                             _distance_bin(distance)))
                star.append((species[right], _distance_bin(distance)))
                colored_star.append((labels[right], _distance_bin(distance)))
        stars.append((species[left], tuple(sorted(star))))
        colored_stars.append((labels[left], tuple(sorted(colored_star))))
    return LearnedGrammar(
        template_level,
        hierarchy.nearest_neighbor_scale,
        hierarchy.levels[template_level - 1].radius,
        marking_radius,
        tuple(templates),
        frozenset(allowed),
        tuple(sorted(set(stars))),
        tuple(sorted(set(colored_stars))),
        tuple(labels),
    )


def _section_is_learned(
    center_species: str,
    section: Sequence[Tuple[str, int]],
    grammar: LearnedGrammar,
) -> bool:
    observed: DefaultDict[Tuple[str, int], int] = defaultdict(int)
    for value in section:
        observed[value] += 1
    for chemical, learned in grammar.allowed_star_sections:
        if chemical != center_species:
            continue
        available: DefaultDict[Tuple[str, int], int] = defaultdict(int)
        for value in learned:
            available[value] += 1
        if all(available[value] >= count for value, count in observed.items()):
            return True
    return False


def _colored_section_is_learned(
    center_cluster_type: int,
    section: Sequence[Tuple[int, int]],
    grammar: LearnedGrammar,
) -> bool:
    observed: DefaultDict[Tuple[int, int], int] = defaultdict(int)
    for value in section:
        observed[value] += 1
    for cluster_type, learned in grammar.allowed_colored_star_sections:
        if cluster_type != center_cluster_type:
            continue
        available: DefaultDict[Tuple[int, int], int] = defaultdict(int)
        for value in learned:
            available[value] += 1
        if all(available[value] >= count for value, count in observed.items()):
            return True
    return False


def _template_pair_index(
    template: RigidTemplate,
    use_cluster_colors: bool,
) -> Dict[Tuple[object, ...], list[Tuple[int, int]]]:
    result: DefaultDict[Tuple[object, ...], list[Tuple[int, int]]] = defaultdict(list)
    for first, first_vector in enumerate(template.offsets):
        if _norm(first_vector) < 1e-8:
            continue
        for second, second_vector in enumerate(template.offsets):
            if first == second or _norm(second_vector) < 1e-8:
                continue
            result[_pair_key(template.species[first], template.species[second],
                             first_vector, second_vector,
                             template.cluster_types[first],
                             template.cluster_types[second],
                             use_cluster_colors)].append((first, second))
    # A large symmetric macro-cluster contains thousands of equivalent anchor
    # pairs.  Rare pair classes are the most informative orientation marks;
    # retaining a bounded atlas avoids re-deriving a continuum of rotations
    # from common shells.
    ordered = sorted(result.items(), key=lambda item: (len(item[1]), repr(item[0])))
    return dict(ordered[:64])


def propose_first_wave(
    positions: Sequence[Vector],
    species: Sequence[str],
    grammar: LearnedGrammar,
    confinement_center: Vector,
    confinement_radius: float,
    *,
    use_marking: bool,
    minimum_overlap: int = 3,
    anchor_keys: Optional[frozenset[SiteKey]] = None,
    cluster_types: Optional[Sequence[int]] = None,
    use_cluster_colors: Optional[bool] = None,
    enforce_overlap_colors: Optional[bool] = None,
) -> Tuple[Tuple[int, Tuple[Tuple[SiteKey, str, int, Vector], ...]], ...]:
    if use_cluster_colors is None:
        use_cluster_colors = grammar.template_level > 1
    if enforce_overlap_colors is None:
        enforce_overlap_colors = use_cluster_colors
    if cluster_types is None:
        cluster_types = (grammar.training_cluster_types
                         if len(positions) == len(grammar.training_cluster_types)
                         else (-1,) * len(positions))
    if len(cluster_types) != len(positions):
        raise ValueError("cluster_types must align with positions")
    state = {_site_key(point): AtomState(chemical, cluster_type, point)
             for point, chemical, cluster_type
             in zip(positions, species, cluster_types)}
    atoms = tuple(state.values())
    spatial = _spatial_index(atoms, grammar.marking_radius)
    template_indices = tuple((template, _template_pair_index(
        template, use_cluster_colors))
                             for template in grammar.templates)
    proposals: Dict[Tuple[SiteKey, ...], Tuple[int, Tuple[Tuple[SiteKey, str, int, Vector], ...]]] = {}
    anchors = tuple(atom for key, atom in state.items()
                    if anchor_keys is None or key in anchor_keys)
    for anchor in anchors:
        neighbors = tuple(atom for atom in _nearby(
            anchor.position, spatial, grammar.marking_radius,
            grammar.cluster_radius) if atom.position != anchor.position)
        for template, pair_index in template_indices:
            if template.center_species != anchor.species:
                continue
            seen_orientations = set()
            for first_index, first_atom in enumerate(neighbors):
                if len(seen_orientations) >= 120:
                    break
                first_vector = _subtract(first_atom.position, anchor.position)
                for second_index, second_atom in enumerate(neighbors):
                    if len(seen_orientations) >= 120:
                        break
                    if first_index == second_index:
                        continue
                    second_vector = _subtract(second_atom.position, anchor.position)
                    matches = pair_index.get(_pair_key(
                        first_atom.species, second_atom.species,
                        first_vector, second_vector,
                        first_atom.cluster_type, second_atom.cluster_type,
                        use_cluster_colors), ())
                    for template_first, template_second in matches:
                        if len(seen_orientations) >= 120:
                            break
                        source_frame = _frame(
                            template.offsets[template_first],
                            template.offsets[template_second])
                        target_frame = _frame(first_vector, second_vector)
                        if source_frame is None or target_frame is None:
                            continue
                        orientation_key = tuple(
                            round(value / 1e-5)
                            for basis in ((1.0, 0.0, 0.0),
                                          (0.0, 1.0, 0.0),
                                          (0.0, 0.0, 1.0))
                            for value in _rotate_between(
                                basis, source_frame, target_frame))
                        if orientation_key in seen_orientations:
                            continue
                        seen_orientations.add(orientation_key)
                        new_sites = []
                        overlap = 0
                        conflict = False
                        for offset, chemical, cluster_type in zip(
                                template.offsets, template.species,
                                template.cluster_types):
                            point = _add(anchor.position, _rotate_between(
                                offset, source_frame, target_frame))
                            if (_norm(_subtract(point, confinement_center)) >
                                    confinement_radius + 1e-5):
                                continue
                            key = _site_key(point)
                            if key in state:
                                if state[key].species != chemical:
                                    conflict = True
                                    break
                                if (enforce_overlap_colors and
                                        state[key].cluster_type >= 0 and
                                        state[key].cluster_type != cluster_type):
                                    conflict = True
                                    break
                                overlap += 1
                            else:
                                new_sites.append((key, chemical, cluster_type, point))
                        if conflict or overlap < minimum_overlap or not new_sites:
                            continue
                        if use_marking:
                            for _, chemical, _, point in new_sites:
                                section = []
                                for existing in _nearby(
                                        point, spatial, grammar.marking_radius,
                                        grammar.marking_radius):
                                    distance = _norm(_subtract(point, existing.position))
                                    if distance < 0.5 * grammar.nearest_neighbor_scale:
                                        conflict = True
                                        break
                                    if (distance <= grammar.marking_radius + 1e-6 and
                                            (chemical, existing.species,
                                             _distance_bin(distance))
                                            not in grammar.allowed_sections):
                                        conflict = True
                                        break
                                    if distance <= grammar.marking_radius + 1e-6:
                                        section.append((existing.species,
                                                        _distance_bin(distance)))
                                if conflict:
                                    break
                                for other_key, other_species, _, other_point in new_sites:
                                    if other_key == _site_key(point):
                                        continue
                                    distance = _norm(_subtract(point, other_point))
                                    if distance <= grammar.marking_radius + 1e-6:
                                        section.append((other_species,
                                                        _distance_bin(distance)))
                                if not _section_is_learned(
                                        chemical, section, grammar):
                                    conflict = True
                                    break
                                if conflict:
                                    break
                        if conflict:
                            continue
                        signature = tuple(sorted(site[0] for site in new_sites))
                        candidate = (overlap, tuple(new_sites))
                        if (signature not in proposals or
                                overlap > proposals[signature][0]):
                            proposals[signature] = candidate
    return tuple(proposals.values())


def _compatible_with_additions(
    point: Vector,
    chemical: str,
    additions: Dict[SiteKey, AtomState],
    grammar: LearnedGrammar,
) -> bool:
    for existing in additions.values():
        distance = _norm(_subtract(point, existing.position))
        if distance < 0.5 * grammar.nearest_neighbor_scale:
            return False
        if (distance <= grammar.marking_radius + 1e-6 and
                (chemical, existing.species, _distance_bin(distance))
                not in grammar.allowed_sections):
            return False
    return True


def accept_compatible_patches(
    proposals: Iterable[Tuple[int, Tuple[Tuple[SiteKey, str, int, Vector], ...]]],
    existing_keys: frozenset[SiteKey],
    grammar: LearnedGrammar,
) -> Tuple[int, Dict[SiteKey, AtomState]]:
    additions: Dict[SiteKey, AtomState] = {}
    accepted = 0
    ordered = sorted(proposals, key=lambda item: (-item[0], -len(item[1]),
                                                   tuple(site[0] for site in item[1])))
    for _, patch in ordered:
        conflict = False
        genuinely_new = []
        for key, chemical, cluster_type, point in patch:
            if key in existing_keys:
                continue
            if key in additions:
                if additions[key].species != chemical:
                    conflict = True
                    break
                continue
            if not _compatible_with_additions(point, chemical, additions, grammar):
                conflict = True
                break
            genuinely_new.append((key, AtomState(chemical, cluster_type, point)))
        if conflict or not genuinely_new:
            continue
        for key, atom in genuinely_new:
            additions[key] = atom
        accepted += 1
    return accepted, additions


def refine_proposed_sites(
    proposals: Iterable[Tuple[int, Tuple[Tuple[SiteKey, str, int, Vector], ...]]],
    state: Dict[SiteKey, AtomState],
    marking_grammar: LearnedGrammar,
    use_cluster_sections: bool = False,
) -> Dict[SiteKey, AtomState]:
    """Use a marking to improve cluster proposals site by site.

    A rejected site does not invalidate the useful part of its parent cluster.
    This is important for partial frontier matches, where a learned cluster can
    contain both a forced continuation and an unresolved alternative.
    """
    candidates: Dict[Tuple[SiteKey, str], AtomState] = {}
    for _, patch in proposals:
        for key, chemical, cluster_type, point in patch:
            if key in state:
                continue
            atom = AtomState(chemical, cluster_type, point)
            candidates[(key, chemical)] = atom
    spatial = _spatial_index(state.values(), marking_grammar.marking_radius)
    passing: DefaultDict[SiteKey, list[AtomState]] = defaultdict(list)
    for (key, _), atom in sorted(candidates.items()):
        section = []
        colored_section = []
        valid = True
        for existing in _nearby(
                atom.position, spatial, marking_grammar.marking_radius,
                marking_grammar.marking_radius):
            distance = _norm(_subtract(atom.position, existing.position))
            if distance < 0.5 * marking_grammar.nearest_neighbor_scale:
                valid = False
                break
            relation = (atom.species, existing.species,
                        _distance_bin(distance))
            if relation not in marking_grammar.allowed_sections:
                valid = False
                break
            section.append((existing.species, _distance_bin(distance)))
            if existing.cluster_type >= 0:
                colored_section.append((existing.cluster_type,
                                        _distance_bin(distance)))
        if (not valid or not _section_is_learned(
                atom.species, section, marking_grammar)):
            continue
        if (use_cluster_sections and atom.cluster_type >= 0 and
                not _colored_section_is_learned(
                    atom.cluster_type, colored_section, marking_grammar)):
            continue
        passing[key].append(atom)
    additions: Dict[SiteKey, AtomState] = {}
    for key, atoms in sorted(passing.items()):
        chemicals = {atom.species for atom in atoms}
        if len(chemicals) != 1:
            continue
        atom = atoms[0]
        if _compatible_with_additions(
                atom.position, atom.species, additions, marking_grammar):
            additions[key] = atom
    return additions


def iterate_refined_growth(
    training_positions: Sequence[Vector],
    training_species: Sequence[str],
    oracle_positions: Sequence[Vector],
    oracle_species: Sequence[str],
    proposal_grammar: LearnedGrammar,
    refinement_grammar: LearnedGrammar,
    confinement_center: Vector,
    confinement_radius: float,
    maximum_waves: int = 4,
) -> IteratedContinuationResult:
    state = {_site_key(point): AtomState(chemical, cluster_type, point)
             for point, chemical, cluster_type in zip(
                 training_positions, training_species,
                 proposal_grammar.training_cluster_types)}
    oracle = {_site_key(point): chemical
              for point, chemical in zip(oracle_positions, oracle_species)}
    hidden = len(oracle) - len(state)
    frontier: Optional[frozenset[SiteKey]] = None
    waves = []
    for wave in range(1, maximum_waves + 1):
        positions = tuple(atom.position for atom in state.values())
        species = tuple(atom.species for atom in state.values())
        cluster_types = tuple(atom.cluster_type for atom in state.values())
        proposals = propose_first_wave(
            positions, species, proposal_grammar, confinement_center,
            confinement_radius, use_marking=(wave == 1),
            anchor_keys=frontier, cluster_types=cluster_types,
            use_cluster_colors=False)
        if wave == 1:
            accepted, additions = accept_compatible_patches(
                proposals, frozenset(state), proposal_grammar)
        else:
            additions = refine_proposed_sites(
                proposals, state, refinement_grammar)
            accepted = len(proposals)
        if not additions:
            break
        state.update(additions)
        correct = sum(key in oracle and oracle[key] == atom.species
                      for key, atom in state.items())
        hidden_correct = correct - len(training_positions)
        waves.append(GrowthWave(
            wave, len(proposals), accepted, len(additions), len(state),
            correct / len(state), hidden_correct / hidden))
        frontier = frozenset(
            key for key, atom in state.items()
            if any(_norm(_subtract(atom.position, new_atom.position))
                   <= proposal_grammar.cluster_radius + 1e-6
                   for new_atom in additions.values()))
    final_correct = sum(key in oracle and oracle[key] == atom.species
                        for key, atom in state.items())
    return IteratedContinuationResult(
        system="blind-refined-continuation",
        training_atoms=len(training_positions),
        hidden_atoms=hidden,
        waves=tuple(waves),
        final_precision=final_correct / len(state),
        final_hidden_recall=(final_correct - len(training_positions)) / hidden,
    )


def iterate_hierarchical_growth(
    training_positions: Sequence[Vector],
    training_species: Sequence[str],
    oracle_positions: Sequence[Vector],
    oracle_species: Sequence[str],
    local_grammar: LearnedGrammar,
    macro_grammar: LearnedGrammar,
    refinement_grammar: LearnedGrammar,
    confinement_center: Vector,
    confinement_radius: float,
    maximum_waves: int = 5,
) -> IteratedContinuationResult:
    """Continue with local moves, then level-2 colored macro moves."""
    state = {_site_key(point): AtomState(chemical, cluster_type, point)
             for point, chemical, cluster_type in zip(
                 training_positions, training_species,
                 local_grammar.training_cluster_types)}
    oracle = {_site_key(point): chemical
              for point, chemical in zip(oracle_positions, oracle_species)}
    hidden = len(oracle) - len(state)
    frontier: Optional[frozenset[SiteKey]] = None
    waves = []
    for wave in range(1, maximum_waves + 1):
        proposal_grammar = local_grammar if wave <= 2 else macro_grammar
        positions = tuple(atom.position for atom in state.values())
        species = tuple(atom.species for atom in state.values())
        cluster_types = tuple(atom.cluster_type for atom in state.values())
        proposals = propose_first_wave(
            positions, species, proposal_grammar, confinement_center,
            confinement_radius, use_marking=(wave == 1),
            minimum_overlap=3 if wave <= 2 else 6,
            anchor_keys=frontier, cluster_types=cluster_types,
            use_cluster_colors=False)
        if wave == 1:
            accepted, additions = accept_compatible_patches(
                proposals, frozenset(state), local_grammar)
        else:
            additions = refine_proposed_sites(
                proposals, state, refinement_grammar,
                use_cluster_sections=wave >= 3)
            accepted = 0
        if not additions:
            break
        state.update(additions)
        correct = sum(key in oracle and oracle[key] == atom.species
                      for key, atom in state.items())
        hidden_correct = correct - len(training_positions)
        waves.append(GrowthWave(
            wave, len(proposals), accepted, len(additions), len(state),
            correct / len(state), hidden_correct / hidden))
        next_radius = (local_grammar.cluster_radius if wave < 2
                       else macro_grammar.cluster_radius)
        frontier = frozenset(
            key for key, atom in state.items()
            if any(_norm(_subtract(atom.position, new_atom.position))
                   <= next_radius + 1e-6
                   for new_atom in additions.values()))
    final_correct = sum(key in oracle and oracle[key] == atom.species
                        for key, atom in state.items())
    return IteratedContinuationResult(
        system="blind-hierarchical-continuation",
        training_atoms=len(training_positions),
        hidden_atoms=hidden,
        waves=tuple(waves),
        final_precision=final_correct / len(state),
        final_hidden_recall=(final_correct - len(training_positions)) / hidden,
    )


def iterate_marked_growth(
    training_positions: Sequence[Vector],
    training_species: Sequence[str],
    oracle_positions: Sequence[Vector],
    oracle_species: Sequence[str],
    grammar: LearnedGrammar,
    confinement_center: Vector,
    confinement_radius: float,
    maximum_waves: int = 4,
) -> IteratedContinuationResult:
    state = {_site_key(point): AtomState(chemical, cluster_type, point)
             for point, chemical, cluster_type in zip(
                 training_positions, training_species,
                 grammar.training_cluster_types)}
    oracle = {_site_key(point): chemical
              for point, chemical in zip(oracle_positions, oracle_species)}
    hidden = len(oracle) - len(state)
    frontier: Optional[frozenset[SiteKey]] = None
    waves = []
    for wave in range(1, maximum_waves + 1):
        positions = tuple(atom.position for atom in state.values())
        species = tuple(atom.species for atom in state.values())
        cluster_types = tuple(atom.cluster_type for atom in state.values())
        proposals = propose_first_wave(
            positions, species, grammar, confinement_center,
            confinement_radius, use_marking=True, anchor_keys=frontier,
            cluster_types=cluster_types)
        accepted, additions = accept_compatible_patches(
            proposals, frozenset(state), grammar)
        if not additions:
            break
        state.update(additions)
        correct = sum(key in oracle and oracle[key] == atom.species
                      for key, atom in state.items())
        hidden_correct = correct - len(training_positions)
        waves.append(GrowthWave(
            wave=wave,
            candidate_patches=len(proposals),
            accepted_patches=accepted,
            added_sites=len(additions),
            total_sites=len(state),
            precision=correct / len(state),
            hidden_recall=hidden_correct / hidden if hidden else 0.0,
        ))
        # Reconsider atoms near the newly added sites.  This includes new
        # anchors and older boundary anchors whose partial domains just gained
        # enough points to determine a rigid placement.
        frontier = frozenset(
            key for key, atom in state.items()
            if any(_norm(_subtract(atom.position, new_atom.position))
                   <= grammar.cluster_radius + 1e-6
                   for new_atom in additions.values()))
    final_correct = sum(key in oracle and oracle[key] == atom.species
                        for key, atom in state.items())
    return IteratedContinuationResult(
        system="blind-iterated-continuation",
        training_atoms=len(training_positions),
        hidden_atoms=hidden,
        waves=tuple(waves),
        final_precision=final_correct / len(state),
        final_hidden_recall=(final_correct - len(training_positions)) / hidden,
    )


def _score(
    proposals: Iterable[Tuple[int, Tuple[Tuple[SiteKey, str, int, Vector], ...]]],
    oracle_positions: Sequence[Vector], oracle_species: Sequence[str],
    training_count: int,
) -> AblationResult:
    sites: Dict[SiteKey, str] = {}
    proposal_list = tuple(proposals)
    for _, patch in proposal_list:
        for key, chemical, _, _ in patch:
            sites[key] = chemical
    oracle = {_site_key(point): chemical
              for point, chemical in zip(oracle_positions, oracle_species)}
    correct = sum(key in oracle and oracle[key] == chemical
                  for key, chemical in sites.items())
    hidden = len(oracle) - training_count
    return AblationResult(
        candidate_patches=len(proposal_list),
        proposed_sites=len(sites),
        correct_sites=correct,
        precision=correct / len(sites) if sites else 0.0,
        hidden_recall=correct / hidden if hidden else 0.0,
    )


def evaluate_icosahedral() -> BlindContinuationResult:
    from materials_gcts_icosahedral_modelset import oracle_patch
    training, _ = oracle_patch(3, 9.0)
    oracle, _ = oracle_patch(4, 15.0)
    grammar = learn_grammar(training.positions, training.species)
    unmarked_proposals = propose_first_wave(
        training.positions, training.species, grammar, (0.0, 0.0, 0.0),
        15.0, use_marking=False)
    marked_proposals = propose_first_wave(
        training.positions, training.species, grammar, (0.0, 0.0, 0.0),
        15.0, use_marking=True)
    unmarked = _score(unmarked_proposals, oracle.positions, oracle.species,
                      len(training.positions))
    marked = _score(marked_proposals, oracle.positions, oracle.species,
                    len(training.positions))
    unmarked_false = unmarked.proposed_sites - unmarked.correct_sites
    marked_false = marked.proposed_sites - marked.correct_sites
    return BlindContinuationResult(
        system=training.name,
        training_atoms=len(training.positions),
        hidden_atoms=len(oracle.positions) - len(training.positions),
        learned_cluster_templates=len(grammar.templates),
        learned_section_entries=len(grammar.allowed_sections),
        unmarked=unmarked,
        marked=marked,
        marking_precision_gain=(marked.precision / unmarked.precision
                                if unmarked.precision else math.inf),
        marking_false_positive_reduction=(
            1.0 - marked_false / unmarked_false if unmarked_false else 0.0),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate_icosahedral()
    print(json.dumps(asdict(result), indent=2) if arguments.json else result)


if __name__ == "__main__":
    main()
