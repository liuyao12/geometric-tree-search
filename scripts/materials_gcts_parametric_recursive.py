#!/usr/bin/env python3
"""Generic discovery shell for parametric recursive GCTS nodes.

The dispatcher receives only a colored point configuration.  It does not take
a crystal/quasicrystal label.  Evidence gates one of three outcomes:

* a translation-quotient node for a periodic crystal;
* an internal-section inflation node for a low-residual quadratic model set;
* no deterministic recursive node for a disordered control.

The rule implementations remain family-specific, but their contract and
benchmark accounting are shared.  This is the bridge from special controls to
a generic GCTS rule-learning interface, not a claim that all quasicrystals use
the quadratic module below.
"""

from __future__ import annotations

import argparse
import collections
import itertools
import json
import math
from dataclasses import asdict, dataclass
from typing import Optional, Tuple

import materials_gcts_transform_dag as dag
import materials_gcts_blind_continuation as blind
from materials_gcts_generic import (
    AtomicConfiguration, benchmark_systems, fractional_to_cartesian,
    inverse3, matvec)
from materials_gcts_fibonacci_3d import (
    Substitution, apply_substitution, coordinates_from_gaps, gap_word,
    generate, infer_axes, infer_substitution, make_input, species_at)
from materials_gcts_icosahedral_modelset import (
    infer_model, infer_quadratic_unit, lift_point, oracle_patch)
from materials_gcts_latent_macro_growth import _latent_patch
from materials_gcts_periodic_growth import replicate
from materials_pointset_benchmarks import amorphous_hard_core_point_set
from materials_recursive_gcts import learn_recursive_hierarchy
from materials_structure_classifier import evaluate_structure


@dataclass(frozen=True)
class ParametricRecursiveRule:
    family: str
    transform: str
    marking: str
    scale: float
    residual: Optional[float]
    deterministic: bool
    reason: str
    origin: Optional[Tuple[float, float, float]] = None
    to_canonical: Optional[Tuple[Tuple[float, float, float], ...]] = None
    input_radius: Optional[float] = None
    translation_basis: Optional[Tuple[Tuple[float, float, float], ...]] = None
    hierarchy_supports: Tuple[int, ...] = ()
    hierarchy_marking_confidence: float = 0.0
    canonical_minimum: Optional[Tuple[float, float, float]] = None
    substitution_images: Optional[Tuple[Tuple[str, ...],
                                        Tuple[str, ...], str]] = None
    input_side: Optional[int] = None
    substitution_decoration: Tuple[Tuple[str, str, str, str], ...] = ()
    substitution_gap_lengths: Optional[Tuple[float, float]] = None
    translation_motif: Tuple[Tuple[str, float, float, float], ...] = ()
    translation_index_minimum: Optional[Tuple[int, int, int]] = None
    translation_index_maximum: Optional[Tuple[int, int, int]] = None
    translation_occupied_cells: Tuple[Tuple[int, int, int], ...] = ()
    section_window_radius: Optional[float] = None
    section_threshold_fractions: Tuple[float, ...] = ()


@dataclass(frozen=True)
class RuleCandidate:
    rule: ParametricRecursiveRule
    normalized_residual: float
    description_entries: int
    seed_replay_exact: bool
    seed_mismatch_fraction: float
    recurring_levels: int
    selection_score: float


def _translation_seed_mismatch(
    configuration: AtomicConfiguration,
    basis: Tuple[Tuple[float, float, float], ...],
    motif: Tuple[Tuple[str, float, float, float], ...],
    minimum: Tuple[int, int, int], maximum: Tuple[int, int, int],
) -> float:
    predicted = set()
    for cell in itertools.product(*(range(minimum[axis], maximum[axis] + 1)
                                    for axis in range(3))):
        for chemical, fx, fy, fz in motif:
            fractional = tuple(cell[axis] + (fx, fy, fz)[axis]
                               for axis in range(3))
            point = fractional_to_cartesian(basis, fractional)  # type: ignore[arg-type]
            predicted.add((blind._site_key(point), chemical))
    observed = {(blind._site_key(point), chemical)
                for point, chemical in zip(configuration.positions,
                                           configuration.species)}
    return len(predicted ^ observed) / max(1, len(predicted | observed))


@dataclass(frozen=True)
class FamilyBenchmark:
    system: str
    discovered_family: str
    deterministic: bool
    input_atoms: int
    verified_output_atoms: int
    verified_actions: int
    verified_growth: float
    generated_new_atoms: int
    atomwise_action_compression: float
    exact_reconstruction: bool
    projected_actions_to_million: Optional[int]
    projected_atoms: Optional[int]
    rule_residual: Optional[float]
    marking: str
    hierarchy_supports: Tuple[int, ...]
    hierarchy_marking_confidence: float
    note: str


@dataclass(frozen=True)
class GenericParametricBenchmark:
    crystal: FamilyBenchmark
    quasicrystal: FamilyBenchmark
    substitution_quasicrystal: FamilyBenchmark
    amorphous: FamilyBenchmark


def _shortest_bond_axes(configuration: AtomicConfiguration):
    points = configuration.positions
    minimum = min(
        math.dist(left, right)
        for index, left in enumerate(points)
        for right in points[index + 1:]
        if math.dist(left, right) > 1e-8)
    candidates = []
    for index, left in enumerate(points):
        for right in points[index + 1:]:
            vector = tuple(right[axis] - left[axis] for axis in range(3))
            length = math.sqrt(sum(value * value for value in vector))
            if length > minimum * 1.03 + 1e-6:
                continue
            axis = tuple(value / length for value in vector)
            candidates.append(axis)
    clusters = []
    cosine_tolerance = math.cos(0.04)
    for axis in candidates:
        for cluster in clusters:
            representative = cluster[0]
            cosine = sum(a * b for a, b in zip(axis, representative))
            if abs(cosine) >= cosine_tolerance:
                aligned = axis if cosine >= 0 else tuple(-value for value in axis)
                cluster[1].append(aligned)
                mean = tuple(sum(item[k] for item in cluster[1]) /
                             len(cluster[1]) for k in range(3))
                length = math.sqrt(sum(value * value for value in mean))
                cluster[0] = tuple(value / length for value in mean)
                break
        else:
            clusters.append([axis, [axis]])
    return tuple(cluster[0] for cluster in clusters)


def _icosahedral_reference_axes():
    unit = (1.0 + math.sqrt(5.0)) / 2.0
    raw = [(1.0, y, z) for y in (-1.0, 1.0) for z in (-1.0, 1.0)]
    raw += [(1.0 / unit, 0.0, sign * unit) for sign in (-1.0, 1.0)]
    raw += [(unit, sign / unit, 0.0) for sign in (-1.0, 1.0)]
    raw += [(0.0, unit, sign / unit) for sign in (-1.0, 1.0)]
    return tuple(tuple(value / math.sqrt(sum(item * item for item in axis))
                       for value in axis) for axis in raw)


def _robust_inversion_center(configuration: AtomicConfiguration) -> Tuple[float, float, float]:
    """Estimate the centre from repeated antipodal-pair midpoints.

    A finite spherical model-set patch contains many ``p, -p`` witnesses.
    Missing atoms bias the ordinary centroid, while their surviving pair
    midpoints still vote for the same centre. The bin width is tied to the
    nearest-neighbour scale and remains far below an atomic separation.
    """
    points = configuration.positions
    centroid = tuple(sum(point[axis] for point in points) / len(points)
                     for axis in range(3))
    nearest = min(math.dist(left, right)
                  for index, left in enumerate(points)
                  for right in points[index + 1:]
                  if math.dist(left, right) > 1e-8)
    width = max(1e-5, nearest * .04)
    maximum_offset = nearest * .35
    bins = collections.defaultdict(list)
    for left_index, left in enumerate(points):
        for right in points[left_index:]:
            midpoint = tuple((left[axis] + right[axis]) * .5
                             for axis in range(3))
            if math.dist(midpoint, centroid) > maximum_offset:
                continue
            key = tuple(round(value / width) for value in midpoint)
            bins[key].append(midpoint)
    if not bins:
        return centroid
    winning = max(bins.values(), key=lambda values: (len(values),
                                                      -math.dist(values[0], centroid)))
    return tuple(sum(point[axis] for point in winning) / len(winning)
                 for axis in range(3))


def _register_axis_sets_approximately(source, target):
    best = None
    for first in range(len(source)):
        for second in range(first + 1, len(source)):
            source_frame = dag._frame(source[first], source[second])
            if source_frame is None:
                continue
            source_dot = sum(source[first][k] * source[second][k]
                             for k in range(3))
            for target_first in range(len(target)):
                for target_second in range(len(target)):
                    if target_first == target_second:
                        continue
                    for sign in (-1.0, 1.0):
                        signed_second = tuple(sign * value
                                              for value in target[target_second])
                        target_dot = sum(target[target_first][k] *
                                         signed_second[k] for k in range(3))
                        if abs(source_dot - target_dot) > 0.04:
                            continue
                        target_frame = dag._frame(
                            target[target_first], signed_second)
                        if target_frame is None:
                            continue
                        rotation = dag._rotation(source_frame, target_frame)
                        mismatches = []
                        for axis in source:
                            moved = dag._matvec(rotation, axis)
                            agreement = max(abs(sum(moved[k] * reference[k]
                                                    for k in range(3)))
                                            for reference in target)
                            mismatches.append(1.0 - agreement)
                        candidate = (max(mismatches), sum(mismatches), rotation)
                        if best is None or candidate[:2] < best[:2]:
                            best = candidate
    if best is None or best[0] > 0.01:
        raise ValueError("axis set has no sufficiently accurate registration")
    return best[2], best[0]


def _normalize_icosahedral(configuration: AtomicConfiguration):
    """Infer translation and SO(3) frame from the colored point cloud."""
    axes = _shortest_bond_axes(configuration)
    if len(axes) != 10:
        raise ValueError(f"expected ten shortest-bond axes, found {len(axes)}")
    reference = _icosahedral_reference_axes()
    rotation, axis_residual = _register_axis_sets_approximately(axes, reference)
    origin = _robust_inversion_center(configuration)
    positions = tuple(dag._matvec(rotation, tuple(
        point[axis] - origin[axis] for axis in range(3)))
        for point in configuration.positions)
    normalized = AtomicConfiguration(
        configuration.name + "-canonical", positions,
        configuration.species, None, False, configuration.provenance)
    return normalized, origin, rotation, axis_residual


def _discover_product_substitution(configuration: AtomicConfiguration):
    axes = _shortest_bond_axes(configuration)
    if len(axes) != 3:
        raise ValueError("product substitution requires three shortest axes")
    if any(abs(sum(axes[left][k] * axes[right][k] for k in range(3))) > 0.05
           for left in range(3) for right in range(left + 1, 3)):
        raise ValueError("shortest axes are not an orthogonal product frame")
    origin = tuple(sum(point[axis] for point in configuration.positions) /
                   len(configuration.positions) for axis in range(3))
    first = axes[0]
    projection = sum(axes[1][k] * first[k] for k in range(3))
    second_raw = tuple(axes[1][k] - projection * first[k]
                       for k in range(3))
    second_length = math.sqrt(sum(value * value for value in second_raw))
    second = tuple(value / second_length for value in second_raw)
    third = (first[1] * second[2] - first[2] * second[1],
             first[2] * second[0] - first[0] * second[2],
             first[0] * second[1] - first[1] * second[0])
    if sum(third[k] * axes[2][k] for k in range(3)) < 0:
        third = tuple(-value for value in third)
    base = (first, second, third)
    for signs in itertools.product((-1.0, 1.0), repeat=3):
        rotation = tuple(tuple(signs[row] * base[row][column]
                               for column in range(3))
                         for row in range(3))
        positions = tuple(dag._matvec(rotation, tuple(
            point[axis] - origin[axis] for axis in range(3)))
            for point in configuration.positions)
        canonical = AtomicConfiguration(
            configuration.name + "-product-canonical", positions,
            configuration.species, None, False, configuration.provenance)
        coordinate_axes = []
        for axis in range(3):
            values = sorted(point[axis] for point in canonical.positions)
            groups = []
            for value in values:
                if not groups or value - groups[-1][-1] > 0.15:
                    groups.append([value])
                else:
                    groups[-1].append(value)
            coordinate_axes.append(tuple(
                sum(group) / len(group) for group in groups))
        coordinate_axes = tuple(coordinate_axes)
        side = len(coordinate_axes[0])
        if side ** 3 != len(configuration.positions) or any(
                len(axis) != side for axis in coordinate_axes):
            continue
        learned = []
        for axis in coordinate_axes:
            gaps = [axis[index + 1] - axis[index]
                    for index in range(len(axis) - 1)]
            ordered = sorted(gaps)
            split = max(range(1, len(ordered)),
                        key=lambda index: ordered[index] - ordered[index - 1])
            short = sum(ordered[:split]) / split
            long = sum(ordered[split:]) / (len(ordered) - split)
            word = tuple("A" if abs(gap - long) < abs(gap - short) else "B"
                         for gap in gaps)
            learned.append(((short, long), word))
        if not all(item[1] == learned[0][1] for item in learned):
            continue
        try:
            substitution, _ = infer_substitution(learned[0][1])
        except ValueError:
            continue
        minima = tuple(axis[0] for axis in coordinate_axes)
        gaps = tuple(item[0] for item in learned)
        residual = max(abs(gaps[axis][kind] - gaps[0][kind])
                       for axis in range(3) for kind in range(2))
        point_word = generate(substitution, side)
        decoration = {}
        consistent = True
        for point, chemical in zip(canonical.positions, canonical.species):
            indices = tuple(min(range(len(coordinate_axes[axis])), key=lambda i:
                                abs(coordinate_axes[axis][i] - point[axis]))
                            for axis in range(3))
            key = tuple(point_word[index] for index in indices)  # type: ignore[index]
            if key in decoration and decoration[key] != chemical:
                consistent = False
                break
            decoration[key] = chemical
        if not consistent:
            continue
        return (canonical, origin, rotation, minima, side,
                substitution, residual, learned[0][0], tuple(sorted(
                    key + (chemical,) for key, chemical in decoration.items())))
    raise ValueError("no common bounded substitution explains the product axes")


def _independent_translation_basis(structure):
    strong = [item.vector for item in structure.translations
              if item.match_fraction >= 0.72]
    chosen = []
    for vector in strong:
        length = math.sqrt(sum(value * value for value in vector))
        if not chosen:
            chosen.append(vector)
        elif len(chosen) == 1:
            cross = (chosen[0][1] * vector[2] - chosen[0][2] * vector[1],
                     chosen[0][2] * vector[0] - chosen[0][0] * vector[2],
                     chosen[0][0] * vector[1] - chosen[0][1] * vector[0])
            sine = math.sqrt(sum(value * value for value in cross)) / (
                math.sqrt(sum(value * value for value in chosen[0])) * length)
            if sine > 0.18:
                chosen.append(vector)
        else:
            cross = (chosen[0][1] * chosen[1][2] -
                     chosen[0][2] * chosen[1][1],
                     chosen[0][2] * chosen[1][0] -
                     chosen[0][0] * chosen[1][2],
                     chosen[0][0] * chosen[1][1] -
                     chosen[0][1] * chosen[1][0])
            volume = abs(sum(cross[axis] * vector[axis]
                             for axis in range(3)))
            normalized = volume / (
                math.sqrt(sum(value * value for value in cross)) * length)
            if normalized > 0.08:
                chosen.append(vector)
        if len(chosen) == 3:
            return tuple(chosen)
    return None


def _learn_translation_motif(
    configuration: AtomicConfiguration,
    basis: Tuple[Tuple[float, float, float], ...],
):
    inverse = inverse3(basis)  # type: ignore[arg-type]
    grouped = {}
    all_indices = []
    # This is a quotient-residue clustering tolerance, not a positional snap.
    # A bounded smooth displacement field can move equivalent residues by a
    # few percent of the parent translation.  Keeping the old 1% bins split a
    # single motif into boundary-specific pseudo-types before a residual
    # marking had a chance to model that variation.
    residue_tolerance = 0.05
    boundary_tolerance = 0.01
    for point, chemical in zip(configuration.positions,
                               configuration.species):
        coordinate = matvec(inverse, point)
        cell_index = []
        residue = []
        for value in coordinate:
            nearest = round(value)
            if abs(value - nearest) <= boundary_tolerance:
                cell_index.append(nearest)
                residue.append(0.0)
            else:
                integer = math.floor(value)
                cell_index.append(integer)
                residue.append(value - integer)
        index_tuple = tuple(cell_index)
        all_indices.append(index_tuple)
        key = (chemical,) + tuple(round(value / residue_tolerance)
                                  for value in residue)
        entry = grouped.setdefault(key, {"residues": [], "cells": set()})
        entry["residues"].append(tuple(residue))
        entry["cells"].add(index_tuple)
    minimum = tuple(min(index[axis] for index in all_indices)
                    for axis in range(3))
    maximum = tuple(max(index[axis] for index in all_indices)
                    for axis in range(3))
    cell_count = math.prod(maximum[axis] - minimum[axis] + 1
                           for axis in range(3))
    required = max(2, math.ceil(0.5 * cell_count))
    motif = []
    for key, entry in grouped.items():
        if len(entry["cells"]) < required:
            continue
        representative = tuple(
            sum(value[axis] for value in entry["residues"]) /
            len(entry["residues"]) for axis in range(3))
        motif.append((key[0],) + representative)
    if not motif:
        raise ValueError("no recurring quotient motif survived consensus")
    return tuple(sorted(motif)), minimum, maximum, tuple(sorted(set(all_indices)))


def _best_translation_model(configuration, structure):
    candidates = [item for item in structure.translations
                  if item.match_fraction >= 0.72][:12]
    best = None
    for first, second, third in itertools.combinations(candidates, 3):
        basis = (first.vector, second.vector, third.vector)
        determinant = abs(sum(
            basis[0][axis] * (
                basis[1][(axis + 1) % 3] * basis[2][(axis + 2) % 3] -
                basis[1][(axis + 2) % 3] * basis[2][(axis + 1) % 3])
            for axis in range(3)))
        lengths = [math.sqrt(sum(value * value for value in vector))
                   for vector in basis]
        normalized_volume = determinant / math.prod(lengths)
        if normalized_volume <= 0.08:
            continue
        try:
            motif, minimum, maximum, occupied = _learn_translation_motif(
                configuration, basis)
        except ValueError:
            continue
        cell_count = math.prod(maximum[axis] - minimum[axis] + 1
                               for axis in range(3))
        predicted = len(motif) * cell_count
        mismatch = abs(predicted - len(configuration.positions)) / max(
            1, len(configuration.positions))
        support_penalty = 0.05 * (1.0 - min(
            first.match_fraction, second.match_fraction,
            third.match_fraction))
        # Equivalent supercells can replay the finite seed exactly. Prefer the
        # shortest quotient description instead of the largest determinant;
        # otherwise a larger observation window can spuriously promote a 2x
        # supercell into a new cluster type.
        description_penalty = len(motif) / max(1, len(configuration.positions))
        score = (mismatch + support_penalty + description_penalty,
                 mismatch, len(motif), determinant)
        if best is None or score < best[0]:
            best = (score, basis, motif, minimum, maximum, occupied)
    if best is None:
        return None
    return best[1:]


def _apply_translation_quotient(
    configuration: AtomicConfiguration,
    basis: Tuple[Tuple[float, float, float], ...],
    motif: Tuple[Tuple[str, float, float, float], ...] = (),
    index_minimum: Optional[Tuple[int, int, int]] = None,
    index_maximum: Optional[Tuple[int, int, int]] = None,
    occupied_cells: Tuple[Tuple[int, int, int], ...] = (),
) -> AtomicConfiguration:
    if motif and index_minimum is not None and index_maximum is not None:
        # Re-measure the current parent from atoms explained by the learned
        # motif.  Fixed discovery-time bounds would make the rewrite idempotent
        # after its first application; including unexplained residual atoms
        # would let a remote defect spuriously enlarge the recursive parent.
        inverse = inverse3(basis)  # type: ignore[arg-type]
        motif_by_species = {}
        for chemical, fx, fy, fz in motif:
            motif_by_species.setdefault(chemical, []).append((fx, fy, fz))
        explained_cells = []
        tolerance = 0.02
        for point, chemical in zip(configuration.positions,
                                   configuration.species):
            if chemical not in motif_by_species:
                continue
            coordinate = matvec(inverse, point)
            cell_index = []
            residue = []
            for value in coordinate:
                nearest = round(value)
                if abs(value - nearest) <= tolerance:
                    cell_index.append(nearest)
                    residue.append(0.0)
                else:
                    integer = math.floor(value)
                    cell_index.append(integer)
                    residue.append(value - integer)
            if any(max(abs(residue[axis] - candidate[axis])
                           for axis in range(3)) <= tolerance
                   for candidate in motif_by_species[chemical]):
                explained_cells.append(tuple(cell_index))
        if explained_cells:
            index_minimum = tuple(min(cell[axis] for cell in explained_cells)
                                  for axis in range(3))
            index_maximum = tuple(max(cell[axis] for cell in explained_cells)
                                  for axis in range(3))
        extents = tuple(index_maximum[axis] - index_minimum[axis] + 1
                        for axis in range(3))
        atoms = {(blind._site_key(point), chemical): point
                 for point, chemical in zip(configuration.positions,
                                            configuration.species)}
        for image in itertools.product((0, 1), repeat=3):
            if image == (0, 0, 0):
                continue
            offset = tuple(image[axis] * extents[axis] for axis in range(3))
            cells = occupied_cells or tuple(itertools.product(*(
                range(index_minimum[axis], index_maximum[axis] + 1)
                for axis in range(3))))
            for cell_index in cells:
                shifted_index = tuple(cell_index[axis] + offset[axis]
                                      for axis in range(3))
                for chemical, fx, fy, fz in motif:
                    fractional = tuple(shifted_index[axis] +
                                       (fx, fy, fz)[axis]
                                       for axis in range(3))
                    point = fractional_to_cartesian(
                        basis, fractional)  # type: ignore[arg-type]
                    atoms[(blind._site_key(point), chemical)] = point
        ordered = sorted(atoms.items())
        return AtomicConfiguration(
            configuration.name + "-grown",
            tuple(point for _, point in ordered),
            tuple(site[1] for site, _ in ordered), None, False,
            "One consensus translation-quotient rewrite")
    inverse = inverse3(basis)  # type: ignore[arg-type]
    fractional = tuple(matvec(inverse, point)
                       for point in configuration.positions)
    extents = tuple(
        math.floor(max(point[axis] for point in fractional) -
                   min(point[axis] for point in fractional) + 1e-6) + 1
        for axis in range(3))
    atoms = {}
    for image in itertools.product((0, 1), repeat=3):
        shift = tuple(sum(image[axis] * extents[axis] * basis[axis][coordinate]
                          for axis in range(3)) for coordinate in range(3))
        for point, chemical in zip(configuration.positions,
                                   configuration.species):
            grown = tuple(point[axis] + shift[axis] for axis in range(3))
            atoms[(blind._site_key(grown), chemical)] = grown
    ordered = sorted(atoms.items())
    return AtomicConfiguration(
        configuration.name + "-grown",
        tuple(point for _, point in ordered),
        tuple(site[1] for site, _ in ordered), None, False,
        "One learned translation-quotient rewrite")


def apply_rule(
    configuration: AtomicConfiguration,
    rule: ParametricRecursiveRule,
) -> AtomicConfiguration:
    """Apply one discovered recursive rewrite in the input coordinate frame."""
    if not rule.deterministic:
        raise ValueError("cannot apply a rejected recursive rule")
    if rule.family == "translation_quotient":
        if rule.translation_basis is None:
            raise ValueError("translation rule is missing its learned basis")
        return _apply_translation_quotient(
            configuration, rule.translation_basis, rule.translation_motif,
            rule.translation_index_minimum,
            rule.translation_index_maximum,
            rule.translation_occupied_cells)  # type: ignore[arg-type]
    if rule.family == "substitution_product":
        if (rule.origin is None or rule.to_canonical is None or
                rule.canonical_minimum is None or
                rule.substitution_images is None or rule.input_side is None or
                not rule.substitution_decoration or
                rule.substitution_gap_lengths is None):
            raise ValueError("substitution rule is missing its learned frame")
        image_a, image_b, seed = rule.substitution_images
        substitution = Substitution(image_a, image_b, seed)
        decoration = {item[:3]: item[3]
                      for item in rule.substitution_decoration}
        current_word = generate(substitution, rule.input_side)
        grown_word = apply_substitution(current_word, substitution)
        short, long = rule.substitution_gap_lengths
        coordinates = [0.0]
        for symbol in grown_word[:-1]:
            coordinates.append(coordinates[-1] +
                               (long if symbol == "A" else short))
        minimum = rule.canonical_minimum
        coordinates_by_axis = tuple(tuple(value + minimum[axis]
                                          for value in coordinates)
                                    for axis in range(3))
        inverse = tuple(tuple(rule.to_canonical[column][row]
                              for column in range(3)) for row in range(3))
        positions = []
        species = []
        for i, j, k in itertools.product(range(len(grown_word)), repeat=3):
            canonical = (coordinates_by_axis[0][i],
                         coordinates_by_axis[1][j],
                         coordinates_by_axis[2][k])
            moved = dag._matvec(inverse, canonical)
            positions.append(tuple(moved[axis] + rule.origin[axis]
                                   for axis in range(3)))
            species.append(decoration[(grown_word[i], grown_word[j],
                                       grown_word[k])])
        return AtomicConfiguration(
            configuration.name + "-grown", tuple(positions), tuple(species),
            None, False, "One learned product-substitution rewrite")
    if rule.family != "internal_section_inflation":
        raise ValueError(f"unsupported recursive family {rule.family}")
    if (rule.origin is None or rule.to_canonical is None or
            rule.input_radius is None):
        raise ValueError("module rule is missing its learned coordinate frame")
    centered = tuple(dag._matvec(rule.to_canonical, tuple(
        point[axis] - rule.origin[axis] for axis in range(3)))
        for point in configuration.positions)
    canonical = AtomicConfiguration(
        configuration.name + "-canonical", centered,
        configuration.species, None, False, configuration.provenance)
    grown = _latent_patch(
        canonical, rule.input_radius * rule.scale,
        maximum_residual=max(1e-5, (rule.residual or 0.0) * 1.01))
    inverse = tuple(tuple(rule.to_canonical[column][row]
                          for column in range(3)) for row in range(3))
    positions = tuple(tuple(value + rule.origin[axis]
                            for axis, value in enumerate(
                                dag._matvec(inverse, point)))
                      for point in grown.positions)
    return AtomicConfiguration(
        configuration.name + "-grown", positions, grown.species,
        None, False, "One learned recursive internal-section rewrite")


def apply_rule_actions(
    configuration: AtomicConfiguration,
    rule: ParametricRecursiveRule,
    actions: int,
) -> AtomicConfiguration:
    """Materialize ``actions`` levels of one learned recursive node.

    The base configuration remains the training witness for the marking.  This
    is important for nonperiodic rules: the requested parent envelope is state,
    while the internal section or substitution grammar is reused unchanged.
    Repeatedly calling the old one-step materializer lost that envelope and
    therefore regenerated the first child instead of a child-of-a-child.
    """
    if actions < 0:
        raise ValueError("recursive action count must be nonnegative")
    if actions == 0:
        return configuration
    if not rule.deterministic:
        raise ValueError("cannot apply a rejected recursive rule")
    if rule.family == "translation_quotient":
        grown = configuration
        for _ in range(actions):
            grown = apply_rule(grown, rule)
        return grown
    if rule.family == "substitution_product":
        if (rule.origin is None or rule.to_canonical is None or
                rule.canonical_minimum is None or
                rule.substitution_images is None or rule.input_side is None or
                not rule.substitution_decoration or
                rule.substitution_gap_lengths is None):
            raise ValueError("substitution rule is missing its learned frame")
        image_a, image_b, seed = rule.substitution_images
        substitution = Substitution(image_a, image_b, seed)
        word = generate(substitution, rule.input_side)
        for _ in range(actions):
            word = apply_substitution(word, substitution)
        short, long = rule.substitution_gap_lengths
        coordinates = [0.0]
        for symbol in word[:-1]:
            coordinates.append(coordinates[-1] +
                               (long if symbol == "A" else short))
        decoration = {item[:3]: item[3]
                      for item in rule.substitution_decoration}
        inverse = tuple(tuple(rule.to_canonical[column][row]
                              for column in range(3)) for row in range(3))
        positions = []
        species = []
        minimum = rule.canonical_minimum
        for i, j, k in itertools.product(range(len(word)), repeat=3):
            canonical = (coordinates[i] + minimum[0],
                         coordinates[j] + minimum[1],
                         coordinates[k] + minimum[2])
            moved = dag._matvec(inverse, canonical)
            positions.append(tuple(moved[axis] + rule.origin[axis]
                                   for axis in range(3)))
            species.append(decoration[(word[i], word[j], word[k])])
        return AtomicConfiguration(
            configuration.name + f"-grown-{actions}", tuple(positions),
            tuple(species), None, False,
            f"{actions} learned product-substitution rewrites")
    if rule.family != "internal_section_inflation":
        raise ValueError(f"unsupported recursive family {rule.family}")
    if (rule.origin is None or rule.to_canonical is None or
            rule.input_radius is None):
        raise ValueError("module rule is missing its learned coordinate frame")
    centered = tuple(dag._matvec(rule.to_canonical, tuple(
        point[axis] - rule.origin[axis] for axis in range(3)))
        for point in configuration.positions)
    canonical = AtomicConfiguration(
        configuration.name + "-canonical", centered,
        configuration.species, None, False, configuration.provenance)
    grown = _latent_patch(
        canonical, rule.input_radius * rule.scale ** actions,
        maximum_residual=max(1e-5, (rule.residual or 0.0) * 1.01))
    inverse = tuple(tuple(rule.to_canonical[column][row]
                          for column in range(3)) for row in range(3))
    positions = tuple(tuple(value + rule.origin[axis]
                            for axis, value in enumerate(
                                dag._matvec(inverse, point)))
                      for point in grown.positions)
    return AtomicConfiguration(
        configuration.name + f"-grown-{actions}", positions, grown.species,
        None, False,
        f"{actions} learned recursive internal-section rewrites")


def discover_rule_candidates(
    configuration: AtomicConfiguration,
) -> Tuple[RuleCandidate, ...]:
    """Propose every supported rule and score it through one evidence gate.

    Candidate extractors may use different geometry, but none is guarded by a
    crystal/quasicrystal category and no first-success dispatch is performed.
    """
    structure = evaluate_structure(
        configuration.positions, configuration.species,
        cell=configuration.cell)
    hierarchy, _ = learn_recursive_hierarchy(
        configuration.name, configuration.positions, configuration.species,
        maximum_levels=3,
        first_descriptor_bin_scale=0.02,
        first_angle_bin=0.03,
        macro_distance_bin_scale=0.20,
        macro_angle_bin=0.08)
    supports = tuple(level.largest_recurring_support
                     for level in hierarchy.levels)
    recurring_levels = [level for level in hierarchy.levels
                        if level.recurring_types]
    marking_confidence = (min(level.marking_confidence
                              for level in recurring_levels)
                          if recurring_levels else 0.0)

    hierarchy_complete = (len(recurring_levels) == 3 and
                          all(support > 0 for support in supports))
    hierarchy_growing = (hierarchy_complete and
                         supports[0] < supports[1] < supports[2])
    candidates = []

    # The finite colored cloud—not the optional cell or a phase label—must
    # supply three strong, composable translations.
    translation_model = _best_translation_model(configuration, structure)
    if (translation_model is not None and len(recurring_levels) == 3 and
            all(support > 0 for support in supports)):
        (basis, motif, index_minimum, index_maximum,
         occupied_cells) = translation_model
        residual = (1.0 - structure.translation_periodicity
                    if structure.translation_periodicity >= 0.98 else
                    1.0 - min(structure.translation_periodicity,
                              structure.translation_closure))
        rule = ParametricRecursiveRule(
            "translation_quotient", "2x2x2 quotient rewrite",
            "species-preserving translation orbit", 2.0, residual, True,
            "three translations and their doubles match the finite cloud",
            translation_basis=basis, hierarchy_supports=supports,
            hierarchy_marking_confidence=marking_confidence,
            translation_motif=motif,
            translation_index_minimum=index_minimum,
            translation_index_maximum=index_maximum,
            # The selected model explicitly minimizes motif × box mismatch;
            # the complete box is therefore the continuation domain.  The
            # occupied-cell set remains diagnostic for future irregular masks.
            translation_occupied_cells=())
        complexity = len(motif) + 3
        normalized = residual / max(structure.nearest_neighbor_scale, 1e-12)
        mismatch = _translation_seed_mismatch(
            configuration, basis, motif, index_minimum, index_maximum)
        candidates.append(RuleCandidate(
            rule, normalized, complexity, mismatch == 0.0, mismatch,
            len(recurring_levels), normalized + mismatch +
            complexity / len(configuration.positions)))

    # Recurrent hierarchy evidence is a shared guard against accidental
    # expressive fits to disorder. The geometric extractors themselves are
    # nevertheless all attempted.
    try:
        (_, product_origin, product_rotation, minima, side,
         substitution, product_residual, product_gaps,
         product_decoration) = _discover_product_substitution(configuration)
    except (ValueError, RuntimeError):
        product_residual = math.inf
    if (product_residual <= 0.02 * structure.nearest_neighbor_scale and
            hierarchy_growing):
        rule = ParametricRecursiveRule(
                "substitution_product", "word -> substitute(word) on 3 axes",
                "learned gap clusters + substitution images + decoration",
                (1.0 + math.sqrt(5.0)) / 2.0, product_residual, True,
                "three product axes share a minimum-description substitution",
                origin=product_origin, to_canonical=product_rotation,
                hierarchy_supports=supports,
                hierarchy_marking_confidence=marking_confidence,
                canonical_minimum=tuple(minima),
                substitution_images=(substitution.image_a,
                                     substitution.image_b,
                                     substitution.seed),
                input_side=side,
                substitution_decoration=product_decoration,
                substitution_gap_lengths=product_gaps)
        complexity = (len(substitution.image_a) +
                      len(substitution.image_b) +
                      len(product_decoration) + 3)
        normalized_residual = product_residual / max(
            structure.nearest_neighbor_scale, 1e-12)
        candidates.append(RuleCandidate(
            rule, normalized_residual, complexity,
            product_residual <= 1e-8, 0.0,
            len(recurring_levels), normalized_residual +
            complexity / len(configuration.positions)))
    try:
        normalized_cloud, origin, rotation, axis_residual = (
            _normalize_icosahedral(configuration))
        probe_unit, _ = infer_quadratic_unit(
            normalized_cloud, coefficient_bound=8,
            complexity_penalty=1e-3)
        probe_lifts = tuple(lift_point(
            point, probe_unit, coefficient_bound=8,
            complexity_penalty=1e-3)[0]
            for point in normalized_cloud.positions)
        if max(abs(value) for lift in probe_lifts for value in lift) > 5:
            raise ValueError("module lift exceeds the bounded candidate box")
        unit, _, window, thresholds, residual = infer_model(
            normalized_cloud, coefficient_bound=8,
            complexity_penalty=1e-3)
        residual = max(residual, axis_residual)
    except (ValueError, RuntimeError, ZeroDivisionError, OverflowError):
        residual = math.inf
        unit = math.nan
        thresholds = ()
    if (residual <= 0.02 * structure.nearest_neighbor_scale and
            unit > 1.0 and hierarchy_growing):
        rule = ParametricRecursiveRule(
                "internal_section_inflation", "patch(R) -> patch(unit R)",
                "learned integer lift + bounded internal acceptance section",
                unit, residual, True,
                "recurrent nonperiodic order has a zero-residual module lift",
                origin, rotation,
                float(math.ceil(max(math.dist(point, origin)
                                    for point in configuration.positions) -
                                1e-9)), None, supports, marking_confidence,
                section_window_radius=window,
                section_threshold_fractions=tuple(
                    threshold / window for threshold in thresholds))
        complexity = 6 + len(thresholds) + 1
        normalized_residual = residual / max(
            structure.nearest_neighbor_scale, 1e-12)
        candidates.append(RuleCandidate(
            rule, normalized_residual, complexity,
            residual <= 1e-8, 0.0,
            len(recurring_levels), normalized_residual +
            complexity / len(configuration.positions)))

    return tuple(sorted(candidates, key=lambda candidate: (
        candidate.selection_score, candidate.description_entries,
        candidate.rule.transform)))


def discover_rule(configuration: AtomicConfiguration) -> ParametricRecursiveRule:
    """Select the minimum-score accepted proposal without a phase label."""
    candidates = discover_rule_candidates(configuration)
    if candidates:
        return candidates[0].rule
    structure = evaluate_structure(
        configuration.positions, configuration.species,
        cell=configuration.cell)
    hierarchy, _ = learn_recursive_hierarchy(
        configuration.name, configuration.positions, configuration.species,
        maximum_levels=3, first_descriptor_bin_scale=0.02,
        first_angle_bin=0.03, macro_distance_bin_scale=0.20,
        macro_angle_bin=0.08)
    supports = tuple(level.largest_recurring_support
                     for level in hierarchy.levels)
    recurring_levels = [level for level in hierarchy.levels
                        if level.recurring_types]
    marking_confidence = (min(level.marking_confidence
                              for level in recurring_levels)
                          if recurring_levels else 0.0)

    return ParametricRecursiveRule(
        "none", "none", "none", 1.0, None, False,
        f"{structure.category}: deterministic recursive evidence did not pass",
        hierarchy_supports=supports,
        hierarchy_marking_confidence=marking_confidence)


def _actions_to_million(atoms: int, growth: float) -> int:
    if atoms >= 1_000_000:
        return 0
    return math.ceil(math.log(1_000_000 / atoms, growth))


def _crystal_benchmark() -> FamilyBenchmark:
    configuration = next(item for item in benchmark_systems()
                         if item.name == "NaCl-rocksalt")
    rule = discover_rule(configuration)
    if rule.family != "translation_quotient":
        raise RuntimeError(f"crystal rule discovery failed: {rule}")
    expected_first = replicate(configuration)
    grown = configuration
    for _ in range(3):
        grown = apply_rule(grown, rule)
    actions = 3
    projected_actions = _actions_to_million(len(configuration.positions), 8.0)
    projected_atoms = len(configuration.positions) * 8 ** projected_actions
    first = apply_rule(configuration, rule)
    exact = ({(blind._site_key(point), chemical)
              for point, chemical in zip(first.positions, first.species)} ==
             {(blind._site_key(point), chemical)
              for point, chemical in zip(expected_first.positions,
                                         expected_first.species)})
    return FamilyBenchmark(
        configuration.name, rule.family, True, len(configuration.positions),
        len(grown.positions), actions,
        len(grown.positions) / len(configuration.positions),
        len(grown.positions) - len(configuration.positions),
        (len(grown.positions) - len(configuration.positions)) / actions,
        exact, projected_actions, projected_atoms, rule.residual, rule.marking,
        rule.hierarchy_supports, rule.hierarchy_marking_confidence,
        "Three explicit recursive rewrites are verified; the million-atom "
        "count is the same implicit quotient recurrence.")


def _quasicrystal_benchmark() -> FamilyBenchmark:
    configuration, _ = oracle_patch(3, 9.0)
    rule = discover_rule(configuration)
    if rule.family != "internal_section_inflation":
        raise RuntimeError(f"IQC rule discovery failed: {rule}")
    assert rule.input_radius is not None
    output_radius = rule.input_radius * rule.scale
    grown = apply_rule(configuration, rule)
    oracle, _ = oracle_patch(4, output_radius)
    predicted = {(blind._site_key(point), chemical)
                 for point, chemical in zip(grown.positions, grown.species)}
    expected = {(blind._site_key(point), chemical)
                for point, chemical in zip(oracle.positions, oracle.species)}
    exact = predicted == expected
    growth = len(grown.positions) / len(configuration.positions)
    projected_actions = _actions_to_million(len(configuration.positions), growth)
    projected_atoms = round(len(configuration.positions) *
                            growth ** projected_actions)
    generated = len(grown.positions) - len(configuration.positions)
    return FamilyBenchmark(
        configuration.name, rule.family, True, len(configuration.positions),
        len(grown.positions), 1, growth, generated, float(generated), exact,
        projected_actions, projected_atoms, rule.residual, rule.marking,
        rule.hierarchy_supports, rule.hierarchy_marking_confidence,
        "One inflation is explicitly oracle-verified. Million-atom growth is "
        "an implicit recurrence projection until a scalable enumerator exists.")


def _substitution_benchmark() -> FamilyBenchmark:
    configuration = make_input(9)
    rule = discover_rule(configuration)
    if rule.family != "substitution_product":
        raise RuntimeError(f"substitution rule discovery failed: {rule}")
    grown = apply_rule(configuration, rule)
    expected_side = round(len(grown.positions) ** (1.0 / 3.0))
    expected = make_input(expected_side)
    predicted_sites = {(blind._site_key(point), chemical)
                       for point, chemical in zip(grown.positions, grown.species)}
    expected_sites = {(blind._site_key(point), chemical)
                      for point, chemical in zip(expected.positions,
                                                 expected.species)}
    generated = len(grown.positions) - len(configuration.positions)
    growth = len(grown.positions) / len(configuration.positions)
    projected_actions = _actions_to_million(
        len(configuration.positions), growth)
    projected_atoms = round(len(configuration.positions) *
                            growth ** projected_actions)
    return FamilyBenchmark(
        configuration.name, rule.family, True, len(configuration.positions),
        len(grown.positions), 1, growth, generated, float(generated),
        predicted_sites == expected_sites, projected_actions, projected_atoms,
        rule.residual, rule.marking, rule.hierarchy_supports,
        rule.hierarchy_marking_confidence,
        "A second, non-icosahedral quasiperiodic family learns substitution "
        "images rather than an internal-space window.")


def _amorphous_benchmark() -> FamilyBenchmark:
    sample = amorphous_hard_core_point_set(atom_count=507)
    configuration = AtomicConfiguration(
        sample.name, sample.positions, sample.species, None, False,
        "Synthetic hard-core amorphous negative control")
    rule = discover_rule(configuration)
    return FamilyBenchmark(
        configuration.name, rule.family, rule.deterministic,
        len(configuration.positions), len(configuration.positions), 0, 1.0,
        0, 0.0, not rule.deterministic, None, None, rule.residual,
        rule.marking, rule.hierarchy_supports,
        rule.hierarchy_marking_confidence,
        "Passing means declining an unsupported deterministic continuation.")


def evaluate() -> GenericParametricBenchmark:
    return GenericParametricBenchmark(
        _crystal_benchmark(), _quasicrystal_benchmark(),
        _substitution_benchmark(),
        _amorphous_benchmark())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, allow_nan=False)
          if arguments.json else result)


if __name__ == "__main__":
    main()
