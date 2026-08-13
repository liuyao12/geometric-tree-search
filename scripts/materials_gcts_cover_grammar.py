#!/usr/bin/env python3
"""Compile learned overlapping clusters into an explicit cover grammar.

``materials_recursive_gcts`` discovers recurrent cluster colors at increasing
bounded radii.  This module supplies the missing compositional contract: every
supercluster occurrence is covered by occurrences from the preceding level,
with uncovered atoms promoted to typed gap terminals.  Child clusters may
overlap; exactness is judged by the union of their atomic supports.

The grammar is learned only from a finite colored point set.  It is not by
itself a continuation oracle: extrapolation still needs a learned placement
rule or section marking.  Its purpose is to make clusters-of-clusters real and
auditable rather than treating increasing support sizes as a recursive rule.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, replace
from typing import Hashable, Sequence, Tuple

from materials_recursive_gcts import (
    HierarchyResult, RecursiveClusterType, learn_recursive_hierarchy)


Point = Tuple[float, float, float]
Matrix = Tuple[Tuple[float, float, float], ...]


@dataclass(frozen=True)
class ChildPlacement:
    child_type: int
    translation: Point
    rotation: Matrix
    shared_parent_atoms: Tuple[int, ...]


@dataclass(frozen=True)
class GapTerminal:
    species: str
    position: Point


@dataclass(frozen=True)
class CoverProduction:
    parent_level: int
    parent_type: int
    observed_occurrences: int
    child_level: int
    child_type_counts: Tuple[Tuple[int, int], ...]
    gap_species_counts: Tuple[Tuple[str, int], ...]
    child_placements: Tuple[ChildPlacement, ...]
    gap_terminals_data: Tuple[GapTerminal, ...]
    prototype_positions: Tuple[Point, ...]
    prototype_species: Tuple[str, ...]
    child_references: int
    gap_terminals: int
    parent_atoms: int
    overlap_atoms: int
    child_covered_fraction: float
    exact_union_cover: bool
    exact_geometric_replay: bool
    production_agreement: float


@dataclass(frozen=True)
class CoverGrammar:
    system: str
    atoms: int
    levels: int
    productions: Tuple[CoverProduction, ...]
    recurring_productions: int
    exact_productions: int
    exact_geometric_productions: int
    minimum_child_covered_fraction: float
    minimum_production_agreement: float
    largest_macro_atoms: int
    maximum_macro_reference_compression: float
    overlapping_productions: int
    gap_cluster_types: int


def _species_key(value: Hashable) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def _dot(left, right):
    return sum(left[index] * right[index] for index in range(3))


def _cross(left, right):
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _normalize(vector):
    length = math.sqrt(_dot(vector, vector))
    if length < 1e-10:
        raise ValueError("degenerate frame vector")
    return tuple(value / length for value in vector)


def _frame(first, second) -> Matrix:
    x = _normalize(first)
    residual = tuple(second[index] - _dot(second, x) * x[index]
                     for index in range(3))
    y = _normalize(residual)
    z = _cross(x, y)
    return tuple((x[row], y[row], z[row]) for row in range(3))


def _matvec(matrix: Matrix, vector) -> Point:
    return tuple(sum(matrix[row][column] * vector[column]
                     for column in range(3)) for row in range(3))


def _frame_map(source: Matrix, target: Matrix) -> Matrix:
    return tuple(tuple(sum(target[row][axis] * source[column][axis]
                           for axis in range(3))
                       for column in range(3)) for row in range(3))


def _rigid_pose(source_positions, source_species, target_positions,
                target_species, tolerance) -> tuple[Point, Matrix]:
    """Find a proper rigid pose by trying chemically/radially compatible anchors."""
    source_center, target_center = source_positions[0], target_positions[0]
    source_vectors = [_subtract(point, source_center)
                      for point in source_positions]
    target_vectors = [_subtract(point, target_center)
                      for point in target_positions]
    source_radii = [math.sqrt(_dot(vector, vector)) for vector in source_vectors]
    target_radii = [math.sqrt(_dot(vector, vector)) for vector in target_vectors]
    source_anchors = sorted(
        (index for index in range(1, len(source_positions))
         if source_radii[index] > tolerance),
        key=lambda index: (source_radii[index], source_species[index], index))[:16]
    for first in source_anchors:
        for second in source_anchors:
            if second == first or math.sqrt(_dot(
                    _cross(source_vectors[first], source_vectors[second]),
                    _cross(source_vectors[first], source_vectors[second]))) < tolerance:
                continue
            candidates_first = [index for index in range(1, len(target_positions))
                if target_species[index] == source_species[first] and
                abs(target_radii[index] - source_radii[first]) <= tolerance]
            candidates_second = [index for index in range(1, len(target_positions))
                if target_species[index] == source_species[second] and
                abs(target_radii[index] - source_radii[second]) <= tolerance]
            source_distance = math.dist(source_positions[first],
                                        source_positions[second])
            for target_first in candidates_first:
                for target_second in candidates_second:
                    if target_first == target_second or abs(math.dist(
                            target_positions[target_first],
                            target_positions[target_second]) -
                            source_distance) > tolerance:
                        continue
                    rotation = _frame_map(
                        _frame(source_vectors[first], source_vectors[second]),
                        _frame(target_vectors[target_first],
                               target_vectors[target_second]))
                    transformed = [_matvec(rotation, vector)
                                   for vector in source_vectors]
                    bins = {}
                    width = tolerance
                    for index, (chemical, point) in enumerate(
                            zip(target_species, target_vectors)):
                        key = (chemical,) + tuple(round(value / width)
                                                  for value in point)
                        bins.setdefault(key, []).append(index)
                    unmatched = set(range(len(target_positions)))
                    valid = True
                    for chemical, point in zip(source_species, transformed):
                        key = tuple(round(value / width) for value in point)
                        options = []
                        for dx in (-1, 0, 1):
                            for dy in (-1, 0, 1):
                                for dz in (-1, 0, 1):
                                    options.extend(index for index in bins.get(
                                        (chemical, key[0] + dx, key[1] + dy,
                                         key[2] + dz), ()) if index in unmatched)
                        if not options:
                            valid = False
                            break
                        match = min(options, key=lambda index:
                                    math.dist(point, target_vectors[index]))
                        if math.dist(point, target_vectors[match]) > tolerance:
                            valid = False
                            break
                        unmatched.remove(match)
                    if valid and not unmatched:
                        return target_center, rotation
    if len(source_positions) == 1 and source_species == target_species:
        return target_center, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                               (0.0, 0.0, 1.0))
    raise ValueError("cluster occurrence has no rigid prototype pose")


def _is_recurring(model: RecursiveClusterType,
                  minimum_occurrences: int,
                  minimum_cluster_size: int) -> bool:
    return (len(model.occurrence_centers) >= minimum_occurrences and
            len(model.representative_support) >= minimum_cluster_size)


def _cover_signature(
    parent_support: Sequence[int],
    child_models: Sequence[RecursiveClusterType],
    species: Sequence[Hashable],
) -> tuple[tuple, int, int, int, tuple]:
    """Greedily cover one parent and return an isometry-free production.

    Only child occurrences wholly contained in the parent are references.
    Children may overlap one another, but a boundary-truncated child is not
    silently changed into another cluster.  Atoms left near that boundary are
    explicit typed gap terminals, making the union exact without pretending
    the recurrent dictionary covered them.
    """
    parent = frozenset(parent_support)
    candidates = []
    for model in child_models:
        for center, support in zip(model.occurrence_centers,
                                   model.occurrence_supports):
            child = frozenset(support)
            if center in parent and child.issubset(parent):
                candidates.append((model.type_id, center, child))
    remaining = set(parent)
    selected = []
    while remaining:
        viable = [(len(support.intersection(remaining)), type_id, center, support)
                  for type_id, center, support in candidates]
        gain, type_id, center, support = max(
            viable, default=(0, -1, -1, frozenset()),
            key=lambda item: (item[0], -item[1], -item[2]))
        if gain == 0:
            break
        selected.append((type_id, center, support))
        remaining.difference_update(support)
        candidates = [candidate for candidate in candidates
                      if candidate[1] != center or candidate[0] != type_id]

    child_counts = tuple(sorted(Counter(item[0] for item in selected).items()))
    gap_counts = tuple(sorted(Counter(_species_key(species[index])
                                      for index in remaining).items()))
    covered = len(parent) - len(remaining)
    overlap = sum(len(item[2]) for item in selected) - covered
    signature = (child_counts, gap_counts, len(parent), overlap)
    return signature, len(selected), len(remaining), covered, tuple(selected)


def _local_prototype(support, center, positions, species):
    ordered = (center,) + tuple(index for index in sorted(support)
                                if index != center)
    origin = positions[center]
    return (ordered,
            tuple(_subtract(positions[index], origin) for index in ordered),
            tuple(_species_key(species[index]) for index in ordered))


def _merge_site(sites, point, chemical, tolerance):
    for existing_point, existing_chemical in sites:
        if math.dist(point, existing_point) <= tolerance:
            if chemical != existing_chemical:
                raise ValueError("overlap joins unlike species")
            return
    sites.append((point, chemical))


def _same_sites(actual, expected, tolerance):
    if len(actual) != len(expected):
        return False
    unmatched = set(range(len(expected)))
    for point, chemical in actual:
        options = [index for index in unmatched
                   if expected[index][1] == chemical]
        if not options:
            return False
        match = min(options, key=lambda index:
                    math.dist(point, expected[index][0]))
        if math.dist(point, expected[match][0]) > tolerance:
            return False
        unmatched.remove(match)
    return not unmatched


def materialize_production(grammar: "CoverGrammar", level: int,
                           type_id: int, *, tolerance: float = 1e-6,
                           _cache=None):
    """Recursively expand one learned prototype and merge geometric overlaps."""
    if _cache is None:
        _cache = {}
    key = (level, type_id)
    if key in _cache:
        return _cache[key]
    lookup = {(item.parent_level, item.parent_type): item
              for item in grammar.productions}
    production = lookup[(level, type_id)]
    sites = []
    for child in production.child_placements:
        for point, chemical in materialize_production(
                grammar, level - 1, child.child_type, tolerance=tolerance,
                _cache=_cache):
            moved = tuple(_matvec(child.rotation, point)[axis] +
                          child.translation[axis] for axis in range(3))
            _merge_site(sites, moved, chemical, tolerance)
    for terminal in production.gap_terminals_data:
        _merge_site(sites, terminal.position, terminal.species, tolerance)
    result = tuple(sorted(sites, key=repr))
    _cache[key] = result
    return result


def compile_cover_grammar(
    system: str,
    positions: Sequence[Sequence[float]],
    species: Sequence[Hashable],
    *,
    maximum_levels: int = 4,
    minimum_occurrences: int = 2,
    minimum_cluster_size: int = 3,
    **hierarchy_options,
) -> tuple[HierarchyResult, CoverGrammar]:
    hierarchy, dictionaries = learn_recursive_hierarchy(
        system, positions, species, maximum_levels=maximum_levels,
        minimum_occurrences=minimum_occurrences,
        minimum_cluster_size=minimum_cluster_size, **hierarchy_options)
    points = tuple(tuple(float(value) for value in point)
                   for point in positions)
    tolerance = max(1e-7, hierarchy.nearest_neighbor_scale * 1e-4)
    productions = []
    production_lookup = {}
    pose_cache = {}

    # Level-one clusters expand directly to coordinate-bearing atom terminals.
    for model in dictionaries[0]:
        if not _is_recurring(model, minimum_occurrences,
                             minimum_cluster_size):
            continue
        ordered, prototype, chemicals = _local_prototype(
            model.representative_support, model.occurrence_centers[0],
            points, species)
        fitting = 0
        for center, support in zip(model.occurrence_centers,
                                   model.occurrence_supports):
            _, target, target_chemicals = _local_prototype(
                support, center, points, species)
            target_global = tuple(tuple(value + points[center][axis]
                                        for axis, value in enumerate(point))
                                  for point in target)
            try:
                pose_cache[(1, model.type_id, center)] = _rigid_pose(
                    prototype, chemicals, target_global,
                    target_chemicals, tolerance)
                fitting += 1
            except ValueError:
                pass
        terminals = tuple(GapTerminal(chemical, point)
                          for chemical, point in zip(chemicals, prototype))
        counts = tuple(sorted(Counter(chemicals).items()))
        production = CoverProduction(
            1, model.type_id, len(model.occurrence_supports), 0, (), counts,
            (), terminals, prototype, chemicals, 0, len(terminals),
            len(terminals), 0, 0.0, True, True,
            fitting / len(model.occurrence_supports))
        productions.append(production)
        production_lookup[(1, model.type_id)] = production

    for level_index in range(1, len(dictionaries)):
        children = tuple(model for model in dictionaries[level_index - 1]
                         if _is_recurring(model, minimum_occurrences,
                                          minimum_cluster_size))
        parents = tuple(model for model in dictionaries[level_index]
                        if _is_recurring(model, minimum_occurrences,
                                         minimum_cluster_size))
        for parent in parents:
            variants = []
            details = []
            for support in parent.occurrence_supports:
                signature, references, gaps, covered, selected = _cover_signature(
                    support, children, species)
                variants.append(signature)
                details.append((references, gaps, covered, selected))
            modal, agreement_count = Counter(variants).most_common(1)[0]
            representative = variants.index(modal)
            references, gaps, covered, selected = details[representative]
            child_counts, gap_counts, parent_atoms, overlap = modal
            parent_center = parent.occurrence_centers[representative]
            parent_support = parent.occurrence_supports[representative]
            parent_order, prototype, parent_chemicals = _local_prototype(
                parent_support, parent_center, points, species)
            parent_local = {atom: index for index, atom in enumerate(parent_order)}
            placements = []
            child_support_union = set()
            placed_supports = []
            for child_type, child_center, child_support in selected:
                child_production = production_lookup[
                    (parent.level - 1, child_type)]
                _, _, target_chemicals = _local_prototype(
                    child_support, child_center, points, species)
                target_order = ((child_center,) + tuple(
                    atom for atom in sorted(child_support)
                    if atom != child_center))
                target_positions = tuple(points[atom] for atom in target_order)
                try:
                    pose_key = (parent.level - 1, child_type, child_center)
                    if pose_key not in pose_cache:
                        pose_cache[pose_key] = _rigid_pose(
                            child_production.prototype_positions,
                            child_production.prototype_species,
                            target_positions, target_chemicals, tolerance)
                    translation, rotation = pose_cache[pose_key]
                except ValueError as error:
                    # A coarse higher-level color can contain occurrences that
                    # are not rigid copies.  Such an occurrence is not a valid
                    # reusable child reference; its sites remain explicit gap
                    # terminals instead of being forced into the grammar.
                    continue
                relative_translation = _subtract(
                    translation, points[parent_center])
                placements.append(ChildPlacement(
                    child_type, relative_translation, rotation, ()))
                child_support_union.update(child_support)
                placed_supports.append(child_support)
            support_multiplicity = Counter(
                atom for support in placed_supports for atom in support)
            placements = [replace(
                placement,
                shared_parent_atoms=tuple(sorted(
                    parent_local[atom] for atom in support
                    if support_multiplicity[atom] > 1)))
                for placement, support in zip(placements, placed_supports)]
            gap_atoms = tuple(atom for atom in parent_order
                              if atom not in child_support_union)
            gap_data = tuple(GapTerminal(
                _species_key(species[atom]),
                _subtract(points[atom], points[parent_center]))
                for atom in gap_atoms)
            child_counts = tuple(sorted(Counter(
                placement.child_type for placement in placements).items()))
            gap_counts = tuple(sorted(Counter(
                terminal.species for terminal in gap_data).items()))
            references = len(placements)
            gaps = len(gap_data)
            covered = len(parent_support) - gaps
            overlap = sum(len(support) for support in placed_supports) - covered
            production = CoverProduction(
                parent.level, parent.type_id,
                len(parent.occurrence_supports), parent.level - 1,
                child_counts, gap_counts, tuple(placements), gap_data,
                prototype, parent_chemicals, references, gaps, parent_atoms,
                overlap, covered / parent_atoms, covered + gaps == parent_atoms,
                False, agreement_count / len(variants))
            productions.append(production)
            production_lookup[(parent.level, parent.type_id)] = production

    exact = [production for production in productions
             if production.exact_union_cover]
    provisional = CoverGrammar(
        system, len(positions), len(dictionaries), tuple(productions),
        len(productions), len(exact), 0, 0.0, 0.0, 0, 0.0, 0, 0)
    replayed = []
    replay_cache = {}
    for production in productions:
        actual = materialize_production(
            provisional, production.parent_level, production.parent_type,
            tolerance=tolerance, _cache=replay_cache)
        expected = tuple(zip(production.prototype_positions,
                             production.prototype_species))
        exact_geometry = _same_sites(actual, expected, tolerance)
        replayed.append(replace(
            production, exact_geometric_replay=exact_geometry))
    productions = replayed
    exact_geometry = [production for production in productions
                      if production.exact_geometric_replay]
    recursive = [production for production in productions
                 if production.parent_level > 1]
    compressions = [production.parent_atoms /
                    max(1, production.child_references +
                        production.gap_terminals)
                    for production in recursive]
    gap_types = {chemical for production in productions
                 for chemical, _ in production.gap_species_counts}
    grammar = CoverGrammar(
        system, len(positions), len(dictionaries), tuple(productions),
        len(productions), len(exact), len(exact_geometry),
        min((item.child_covered_fraction for item in recursive), default=0.0),
        min((item.production_agreement for item in productions), default=0.0),
        max((item.parent_atoms for item in productions), default=0),
        max(compressions, default=0.0),
        sum(item.overlap_atoms > 0 for item in recursive), len(gap_types))
    return hierarchy, grammar


def main() -> None:
    from materials_gcts_icosahedral_modelset import oracle_patch

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    sample, _ = oracle_patch(3, 9.0)
    _, grammar = compile_cover_grammar(
        sample.name, sample.positions, sample.species, maximum_levels=3,
        first_descriptor_bin_scale=.02, first_angle_bin=.03,
        macro_distance_bin_scale=.20, macro_angle_bin=.08)
    print(json.dumps(asdict(grammar), indent=2)
          if arguments.json else grammar)


if __name__ == "__main__":
    main()
