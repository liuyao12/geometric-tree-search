#!/usr/bin/env python3
"""Leakage-controlled crystal-side stationary-production benchmark.

The learner receives Cartesian positions, species, and the irregular-support
occurrence graph learned from those same data.  It is not told a cell, lattice,
space group, material/family label, target size, or preferred axes.

This is deliberately a *crystal-side* positive gate, not a classifier.  Three
linearly independent translations must be witnessed both as recurring edges
between equal learned cluster types and as high-support, species-preserving
translations of the atomic point set. Candidate integer subdivision ratios and
their child offsets are then inferred from recurrent complete-cell extents and
positive MDL, rather than supplied. The resulting rule is accepted only if two
independent training samples explicitly contain three nested productions. The
common strong stationary-production contract checks geometry, chemistry,
exact population substitution, scale, and MDL evidence before symbolic
self-feeding is allowed.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import reduce
from math import gcd
from typing import Hashable, Sequence

from materials_gcts_generic import AtomicConfiguration
from materials_gcts_irregular_port_atlas import (
    IrregularPortProgram, compile_irregular_port_program)
from materials_gcts_oriented_overlap_ports import IDENTITY, Vector
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionChild, ProductionPort,
    PromotionObservation, StationaryProductionEvidence,
    stationary_evidence)


@dataclass(frozen=True)
class TranslationGenerator:
    vector: Vector
    graph_witnesses: int
    atomic_overlap_fraction: float


@dataclass(frozen=True)
class TranslationLearningResult:
    accepted: bool
    generators: tuple[TranslationGenerator, ...]
    candidate_classes: int
    reason: str


@dataclass(frozen=True)
class LearnedGridProduction:
    radix: int
    child_offsets: tuple[tuple[int, int, int], ...]
    observed_side_lengths: tuple[int, ...]
    mdl_saving: int


@dataclass(frozen=True)
class ExplicitScaleCheck:
    side_in_base_cells: int
    samples_with_occurrence: int
    independent_occurrences: int
    exact: bool
    materialized_sites: int = 0
    one_to_one_colored_match: bool = False


@dataclass(frozen=True)
class CrystalStationaryCase:
    system: str
    accepted_generators: bool
    learned_generators: tuple[Vector, ...]
    generator_graph_witnesses: tuple[int, ...]
    generator_atomic_overlaps: tuple[float, ...]
    explicit_train_scales: tuple[ExplicitScaleCheck, ...]
    heldout_first_two_levels_exact: bool
    stationary: bool
    learned_similarity_scale: float | None
    substitution_matrix: tuple[tuple[int, ...], ...]
    base_sites: int
    symbolic_actions: int
    represented_sites: int
    million_sites_within_seven_actions: bool
    positions_species_and_learned_graph_only: bool
    reason: str
    heldout_explicit_scales: tuple[ExplicitScaleCheck, ...] = ()
    production_children: int = 0
    learned_radix: int = 0
    learned_child_offsets: tuple[tuple[int, int, int], ...] = ()
    discovery_atoms: int = 0
    training_sample_atoms: tuple[int, ...] = ()
    learning_atom_presentations: int = 0
    unique_learning_atoms: int = 0
    discovery_is_subset_of_first_training_sample: bool = False


def _sub(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(left[i] - right[i] for i in range(3))  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(left[i] * right[i] for i in range(3))


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _canonical_sign(vector: Vector, tolerance: float) -> Vector:
    first = next((value for value in vector if abs(value) > tolerance), 0.0)
    return tuple(-value for value in vector) if first < 0 else vector  # type: ignore[return-value]


def _quantize(vector: Sequence[float], tolerance: float) -> tuple[int, ...]:
    return tuple(round(value / tolerance) for value in vector)


def _atomic_overlap(
    positions: Sequence[Sequence[float]], species: Sequence[Hashable],
    translation: Vector, tolerance: float,
) -> float:
    sites = {(str(label),) + _quantize(point, tolerance)
             for label, point in zip(species, positions)}
    return sum(
        (str(label),) + _quantize(
            tuple(point[axis] + translation[axis] for axis in range(3)),
            tolerance) in sites
        for label, point in zip(species, positions)) / len(positions)


def learn_translation_generators(
    program: IrregularPortProgram,
    positions: Sequence[Sequence[float]], species: Sequence[Hashable], *,
    tolerance: float | None = None, minimum_atomic_overlap: float = .45,
    minimum_graph_witnesses: int = 4,
) -> TranslationLearningResult:
    """Infer three independent translations from admitted occurrence edges."""
    if len(positions) != len(species) or not positions:
        raise ValueError("positions/species must be nonempty and aligned")
    tolerance = tolerance or max(.01, program.cover.minimum_distance * .01)
    occurrence = {item.occurrence_id: item for item in program.occurrences}
    admitted = {(port.parent_type, port.child_type,
                 port.symmetry_orbit_key) for port in program.atlas.ports}
    buckets: dict[tuple[int, ...], list[Vector]] = defaultdict(list)
    # relation_classes are the witnessed edges of the learned occurrence graph;
    # arbitrary all-pairs point displacements are intentionally not candidates.
    for left_id, right_id, left_type, right_type, pose_key in (
            program.atlas.relation_classes):
        if (left_type, right_type, pose_key) not in admitted:
            continue
        left, right = occurrence[left_id], occurrence[right_id]
        if left.type_id != right.type_id:
            continue
        displacement = _canonical_sign(
            _sub(right.translation, left.translation), tolerance)
        buckets[_quantize(displacement, tolerance)].append(displacement)
    candidates = []
    for key, observations in buckets.items():
        if len(observations) < minimum_graph_witnesses:
            continue
        vector = tuple(sum(value[axis] for value in observations) /
                       len(observations) for axis in range(3))
        overlap = _atomic_overlap(positions, species, vector, tolerance)
        if overlap >= minimum_atomic_overlap:
            candidates.append(TranslationGenerator(
                vector, len(observations), overlap))
    # Recurrence support is primary; length only breaks evidence ties.  This
    # rejects seductive short centre-to-centre offsets that are not symmetries
    # of the colored atomic set.
    candidates.sort(key=lambda item: (
        -item.graph_witnesses * item.atomic_overlap_fraction,
        _norm(item.vector), tuple(round(value, 9) for value in item.vector)))
    chosen: list[TranslationGenerator] = []
    for candidate in candidates:
        if not chosen:
            chosen.append(candidate)
        elif len(chosen) == 1:
            area = _norm(_cross(chosen[0].vector, candidate.vector))
            if area > tolerance * _norm(chosen[0].vector) * _norm(candidate.vector):
                chosen.append(candidate)
        else:
            volume = abs(_dot(chosen[0].vector,
                              _cross(chosen[1].vector, candidate.vector)))
            scale = reduce(lambda a, b: a * b,
                           (_norm(item.vector) for item in
                            (chosen[0], chosen[1], candidate)))
            if volume > tolerance * scale:
                chosen.append(candidate)
        if len(chosen) == 3:
            break
    accepted = len(chosen) == 3
    return TranslationLearningResult(
        accepted, tuple(chosen), len(buckets),
        "" if accepted else
        "fewer than three independent recurring colored translations")


def _coordinates(point: Sequence[float], origin: Sequence[float],
                 generators: Sequence[Vector]) -> Vector:
    value = _sub(point, origin)
    denominator = _dot(generators[0], _cross(generators[1], generators[2]))
    if abs(denominator) <= 1e-12:
        raise ValueError("translation generators are not independent")
    return (
        _dot(value, _cross(generators[1], generators[2])) / denominator,
        _dot(generators[0], _cross(value, generators[2])) / denominator,
        _dot(generators[0], _cross(generators[1], value)) / denominator,
    )


def _cell_decomposition(
    positions: Sequence[Sequence[float]], species: Sequence[Hashable],
    generators: Sequence[Vector], *, tolerance: float = 2e-4,
) -> tuple[
    set[tuple[int, int, int]], tuple[tuple[str, int], ...],
    dict[tuple[str, tuple[int, int, int]],
         dict[tuple[int, int, int], Vector]],
]:
    origin = min(tuple(tuple(float(value) for value in point)
                       for point in positions))
    roles: dict[tuple[str, tuple[int, int, int]],
                dict[tuple[int, int, int], Vector]] = defaultdict(dict)
    for point, label in zip(positions, species):
        coordinate = _coordinates(point, origin, generators)
        cell = []
        fraction = []
        for value in coordinate:
            integer = math.floor(value + tolerance)
            residual = value - integer
            if residual > 1.0 - tolerance:
                integer += 1
                residual = 0.0
            cell.append(integer)
            fraction.append(round(residual / tolerance))
        roles[(str(label), tuple(fraction))][tuple(cell)] = tuple(
            float(value) for value in point)
    if not roles:
        return set(), (), {}
    # Fractional motif roles have independent integer representatives: adding
    # an integer generator to one role leaves the physical decorated lattice
    # unchanged. Remove that harmless gauge before asking which base cells are
    # chemically complete.
    normalized_roles = {}
    for role, values in roles.items():
        offset = tuple(min(value[axis] for value in values)
                       for axis in range(3))
        normalized_roles[role] = {
            tuple(value[axis] - offset[axis] for axis in range(3)): point
            for value, point in values.items()}
    complete = set.intersection(*(
        set(values) for values in normalized_roles.values()))
    population = Counter(role[0] for role in roles)
    return complete, tuple(sorted(population.items())), normalized_roles


def _complete_cells(
    positions: Sequence[Sequence[float]], species: Sequence[Hashable],
    generators: Sequence[Vector], *, tolerance: float = 2e-4,
) -> tuple[set[tuple[int, int, int]], tuple[tuple[str, int], ...]]:
    cells, population, _ = _cell_decomposition(
        positions, species, generators, tolerance=tolerance)
    return cells, population


def _recursive_offsets(
    learned: LearnedGridProduction, actions: int,
) -> tuple[tuple[int, int, int], ...]:
    offsets = ((0, 0, 0),)
    for _ in range(actions):
        offsets = tuple(sorted({
            tuple(learned.radix * parent[axis] + child[axis]
                  for axis in range(3))
            for parent in offsets for child in learned.child_offsets}))
    return offsets


def _materialize_heldout_level(
    positions: Sequence[Sequence[float]], species: Sequence[Hashable],
    generators: Sequence[Vector], learned: LearnedGridProduction,
    actions: int, *, tolerance: float = 2e-4,
) -> ExplicitScaleCheck:
    """Execute a frozen rule from one heldout motif and compare colored sites."""
    cells, _, role_maps = _cell_decomposition(
        positions, species, generators, tolerance=tolerance)
    offsets = _recursive_offsets(learned, actions)
    side = learned.radix ** actions
    anchor = _find_cube_anchor(cells, side)
    if anchor is None or not role_maps:
        return ExplicitScaleCheck(side, 0, 0, False, 0, False)
    predicted = []
    observed = []
    for role, cell_map in sorted(role_maps.items()):
        label = role[0]
        seed = cell_map.get(anchor)
        if seed is None:
            return ExplicitScaleCheck(side, 1, 1, False, 0, False)
        for offset in offsets:
            target_cell = tuple(anchor[axis] + offset[axis]
                                for axis in range(3))
            target = cell_map.get(target_cell)
            if target is None:
                return ExplicitScaleCheck(side, 1, 1, False,
                                          len(predicted), False)
            predicted_point = tuple(seed[coordinate] + sum(
                offset[axis] * generators[axis][coordinate]
                for axis in range(3)) for coordinate in range(3))
            predicted.append((label, _quantize(predicted_point, tolerance)))
            observed.append((label, _quantize(target, tolerance)))
    exact = (len(predicted) == len(role_maps) * len(offsets) and
             Counter(predicted) == Counter(observed))
    return ExplicitScaleCheck(
        side, 1, 1, exact, len(predicted), exact)


def _find_cube_anchor(
    cells: set[tuple[int, int, int]], side: int,
) -> tuple[int, int, int] | None:
    for anchor in sorted(cells):
        if all((anchor[0] + i, anchor[1] + j, anchor[2] + k) in cells
               for i in range(side) for j in range(side)
               for k in range(side)):
            return anchor
    return None


def _contains_cube(cells: set[tuple[int, int, int]], side: int) -> bool:
    return _find_cube_anchor(cells, side) is not None


def _maximum_complete_cube_side(
        cells: set[tuple[int, int, int]]) -> int:
    if not cells:
        return 0
    upper = min(max(point[axis] for point in cells) -
                min(point[axis] for point in cells) + 1
                for axis in range(3))
    for side in range(upper, 0, -1):
        if _contains_cube(cells, side):
            return side
    return 0


def learn_stationary_grid_production(
    training_cells: Sequence[set[tuple[int, int, int]]], *,
    observed_levels: int,
) -> LearnedGridProduction | None:
    """Infer an integer self-similar subdivision from train recurrence.

    Candidate radices are generated from the observed complete-cell extent;
    neither a desired scale nor child count is supplied. A candidate must have
    every nested power explicitly present in every independent train sample.
    The score is the recurrent terminal volume minus the literal offset table
    and level-description costs, a simple positive two-part MDL criterion.
    """
    if observed_levels < 3 or len(training_cells) < 2:
        raise ValueError("stationarity needs three levels and two train samples")
    maximum_side = min((_maximum_complete_cube_side(cells)
                        for cells in training_cells), default=0)
    candidates = []
    for radix in range(1, maximum_side + 1):
        if radix <= 1:
            continue
        sides = tuple(radix ** exponent
                      for exponent in range(1, observed_levels + 1))
        if sides[-1] > maximum_side or not all(
                _contains_cube(cells, side)
                for cells in training_cells for side in sides):
            continue
        # Read the child offsets back from each witnessed smallest parent.
        # They are not synthesized from a desired branching factor.
        observed_offsets = []
        for cells in training_cells:
            anchor = _find_cube_anchor(cells, sides[0])
            if anchor is None:
                break
            observed_offsets.append(tuple(sorted(
                tuple(point[axis] - anchor[axis] for axis in range(3))
                for point in cells
                if all(anchor[axis] <= point[axis] <
                       anchor[axis] + sides[0] for axis in range(3)))))
        if (len(observed_offsets) != len(training_cells) or
                len(set(observed_offsets)) != 1):
            continue
        offsets = observed_offsets[0]
        description_cost = len(offsets) * 3 + observed_levels
        represented_terminals = sides[-1] ** 3
        mdl_saving = represented_terminals - description_cost
        if mdl_saving > 0:
            candidates.append(LearnedGridProduction(
                radix, offsets, sides, mdl_saving))
    if not candidates:
        return None
    # Prefer the production explaining the largest explicitly observed parent,
    # then its actual MDL saving. This makes a ternary hierarchy distinguishable
    # from a smaller binary subpatch without prescribing either radix.
    return max(candidates, key=lambda item: (
        item.observed_side_lengths[-1], item.mdl_saving,
        -len(item.child_offsets), -item.radix))


def _reduced_chemistry(population: Sequence[tuple[str, int]]) -> tuple[str, ...]:
    divisor = reduce(gcd, (count for _, count in population))
    return tuple(f"{label}:{count // divisor}" for label, count in population)


def grid_production(
    generators: Sequence[Vector], population: Sequence[tuple[str, int]],
    learned: LearnedGridProduction, level: int,
) -> PortGraphProduction:
    """Construct a train-inferred grid production at an observed scale."""
    factor = learned.radix ** level
    child_count = len(learned.child_offsets)
    scaled_population = tuple((label, count * child_count ** level)
                              for label, count in population)
    chemistry = _reduced_chemistry(population)
    children = tuple(ProductionChild(
        chemistry, "achiral", IDENTITY,
        tuple(factor * sum(offset[axis] * generators[axis][coordinate]
                           for axis in range(3)) for coordinate in range(3)),
        (IDENTITY,), scaled_population)
        for offset in learned.child_offsets)
    ports = []
    for left, source in enumerate(learned.child_offsets):
        for right, target in enumerate(learned.child_offsets):
            if sum(a != b for a, b in zip(source, target)) != 1:
                continue
            if sum(abs(a - b) for a, b in zip(source, target)) != 1:
                continue
            ports.append(ProductionPort(
                left, right, ("recurring-translation-port",), chemistry))
    return PortGraphProduction(children, tuple(ports))


def certify_crystal_stationarity(
    name: str, discovery: AtomicConfiguration,
    training_samples: Sequence[AtomicConfiguration],
    heldout: AtomicConfiguration,
) -> CrystalStationaryCase:
    if not training_samples:
        raise ValueError("at least one training sample is required")
    discovery_atoms = len(discovery.positions)
    training_atom_counts = tuple(len(sample.positions)
                                 for sample in training_samples)
    learning_presentations = discovery_atoms + sum(training_atom_counts)
    quantization = 1e-7
    first_sites = {(str(label),) + _quantize(point, quantization)
                   for label, point in zip(training_samples[0].species,
                                           training_samples[0].positions)}
    discovery_sites = {(str(label),) + _quantize(point, quantization)
                       for label, point in zip(discovery.species,
                                               discovery.positions)}
    discovery_subset = discovery_sites.issubset(first_sites)
    all_learning_sites = set(discovery_sites)
    for sample in training_samples:
        all_learning_sites.update(
            (str(label),) + _quantize(point, quantization)
            for label, point in zip(sample.species, sample.positions))
    learning_metadata = dict(
        discovery_atoms=discovery_atoms,
        training_sample_atoms=training_atom_counts,
        learning_atom_presentations=learning_presentations,
        unique_learning_atoms=len(all_learning_sites),
        discovery_is_subset_of_first_training_sample=discovery_subset)
    program = compile_irregular_port_program(
        discovery.species, discovery.positions)
    # The expensive support/port vocabulary is learned on the bounded
    # discovery crop. Candidate translations are then scored on the larger
    # training window, still using positions/species only. This reduces crop
    # ambiguity between symmetry-equivalent primitive bases.
    learned = learn_translation_generators(
        program, training_samples[0].positions, training_samples[0].species)
    if not learned.accepted:
        return CrystalStationaryCase(
            name, False, tuple(item.vector for item in learned.generators),
            tuple(item.graph_witnesses for item in learned.generators),
            tuple(item.atomic_overlap_fraction for item in learned.generators),
            (), False, False, None, (), 0, 0, 0, False, True,
            learned.reason, **learning_metadata)
    vectors = tuple(item.vector for item in learned.generators)
    train_cells = []
    populations = []
    for sample in training_samples:
        cells, population = _complete_cells(
            sample.positions, sample.species, vectors)
        train_cells.append(cells)
        populations.append(population)
    if len(set(populations)) != 1 or not populations[0]:
        reason = "training samples disagree on the inferred chemical motif"
        return CrystalStationaryCase(
            name, True, vectors,
            tuple(item.graph_witnesses for item in learned.generators),
            tuple(item.atomic_overlap_fraction for item in learned.generators),
            (), False, False, None, (), 0, 0, 0, False, True, reason,
            **learning_metadata)
    population = populations[0]
    required_adjacent_comparisons = 2
    observed_levels = required_adjacent_comparisons + 1
    learned_production = learn_stationary_grid_production(
        train_cells, observed_levels=observed_levels)
    if learned_production is None:
        reason = "no positive-MDL stationary grid production was inferred"
        return CrystalStationaryCase(
            name, True, vectors,
            tuple(item.graph_witnesses for item in learned.generators),
            tuple(item.atomic_overlap_fraction for item in learned.generators),
            (), False, False, None, (), sum(count for _, count in population),
            0, sum(count for _, count in population), False, True, reason,
            **learning_metadata)
    checks = tuple(ExplicitScaleCheck(
        side, sum(_contains_cube(cells, side) for cells in train_cells),
        sum(_contains_cube(cells, side) for cells in train_cells),
        all(_contains_cube(cells, side) for cells in train_cells))
        for side in learned_production.observed_side_lengths)
    observations = tuple(PromotionObservation(
        level, grid_production(
            vectors, population, learned_production, level),
        checks[level].independent_occurrences, 0.0,
        learned_production.mdl_saving, True)
        for level in range(observed_levels))
    evidence: StationaryProductionEvidence = stationary_evidence(observations)
    _, heldout_population = _complete_cells(
        heldout.positions, heldout.species, vectors)
    materialized = tuple(_materialize_heldout_level(
        heldout.positions, heldout.species, vectors, learned_production,
        actions) for actions in range(1, required_adjacent_comparisons + 1))
    heldout_checks = tuple(
        item if heldout_population == population else ExplicitScaleCheck(
            item.side_in_base_cells, item.samples_with_occurrence,
            item.independent_occurrences, False, item.materialized_sites, False)
        for item in materialized)
    heldout_exact = all(item.exact for item in heldout_checks)
    base_sites = sum(count for _, count in population)
    represented, actions = base_sites, 0
    symbolic_multiplier = len(learned_production.child_offsets)
    if evidence.stationary and heldout_exact:
        while represented < 1_000_000 and actions < 7:
            represented *= symbolic_multiplier
            actions += 1
    matrix = ()
    if evidence.stationary:
        audit = evidence.adjacent_comparisons[0].chemical_population_audit
        matrix = () if audit is None else audit.substitution_matrix
    passed = evidence.stationary and heldout_exact and represented >= 1_000_000
    reason = evidence.reason or ("" if heldout_exact else
                                 "heldout explicit replay failed")
    return CrystalStationaryCase(
        name, True, vectors,
        tuple(item.graph_witnesses for item in learned.generators),
        tuple(item.atomic_overlap_fraction for item in learned.generators),
        checks, heldout_exact, evidence.stationary,
        evidence.learned_similarity_scale, matrix, base_sites, actions,
        represented, passed and actions <= 7, True, reason,
        heldout_checks, symbolic_multiplier, learned_production.radix,
        learned_production.child_offsets, **learning_metadata)


def _nacl_primitive_cube(name: str, side: int, shift: Vector) -> AtomicConfiguration:
    """Fixture generator; only its returned positions/species reach learning."""
    half = 2.82
    # A primitive fcc basis in the deterministic canonical orientation chosen
    # by the evidence-tied generator learner.  This is fixture construction
    # metadata only; neither these vectors nor ``side`` enter certification.
    generators = ((half, -half, 0.0), (half, 0.0, -half),
                  (half, 0.0, half))
    motif = (((0.0, 0.0, 0.0), "Na"), ((0.0, half, 0.0), "Cl"))
    sites = []
    for cell in itertools.product(range(side), repeat=3):
        offset = tuple(shift[coordinate] + sum(
            cell[axis] * generators[axis][coordinate] for axis in range(3))
                       for coordinate in range(3))
        for point, label in motif:
            sites.append((tuple(point[axis] + offset[axis]
                                for axis in range(3)), label))
    sites.sort(key=repr)
    return AtomicConfiguration(name, tuple(point for point, _ in sites),
                               tuple(label for _, label in sites))


def _central_subset(configuration: AtomicConfiguration,
                    count: int) -> AtomicConfiguration:
    center = tuple(sum(point[axis] for point in configuration.positions) /
                   len(configuration.positions) for axis in range(3))
    indices = sorted(range(len(configuration.positions)), key=lambda index: (
        math.dist(configuration.positions[index], center),
        configuration.species[index], configuration.positions[index]))[:count]
    return AtomicConfiguration(
        configuration.name + "-discovery",
        tuple(configuration.positions[index] for index in indices),
        tuple(configuration.species[index] for index in indices))


def evaluate() -> tuple[CrystalStationaryCase, ...]:
    from materials_gcts_icosahedral_modelset import oracle_patch
    from materials_pointset_benchmarks import amorphous_hard_core_point_set

    first = _nacl_primitive_cube("NaCl-train-A", 8, (0.0, 0.0, 0.0))
    second = _nacl_primitive_cube("NaCl-train-B", 8, (41.3, -17.1, 8.7))
    heldout = _nacl_primitive_cube("NaCl-heldout", 4, (-31.7, 23.4, 5.1))
    positive = certify_crystal_stationarity(
        "NaCl heldout", _central_subset(first, 216),
        (first, second), heldout)

    iqc, _ = oracle_patch(3, 9.0)
    iqc_discovery = _central_subset(iqc, min(216, len(iqc.positions)))
    iqc_case = certify_crystal_stationarity(
        "ideal IQC negative control", iqc_discovery,
        (iqc, iqc), iqc)

    amorphous = amorphous_hard_core_point_set(atom_count=216, seed=91)
    amorphous_configuration = AtomicConfiguration(
        amorphous.name, amorphous.positions, amorphous.species)
    amorphous_case = certify_crystal_stationarity(
        "amorphous negative control", amorphous_configuration,
        (amorphous_configuration, amorphous_configuration),
        amorphous_configuration)
    return positive, iqc_case, amorphous_case


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps([asdict(item) for item in result], indent=2,
                     sort_keys=True) if arguments.json else result)


if __name__ == "__main__":
    main()
