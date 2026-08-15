#!/usr/bin/env python3
"""Cell-free discovery of repeated irregular supports in colored point sets.

The public entry point accepts *only* chemical labels and Cartesian positions.
It does not accept a cell, phase label, lattice coordinate, source-site label,
or oracle metadata.  Adaptive atomic neighborhoods are merely seeds.  The
actual cluster candidates are unions of touching seeds and are canonicalized
as colored finite metric graphs, so a learned support need not be a ball, have
a fixed size, or have a distinguished central atom.

This is deliberately a support learner rather than a growth oracle.  It gives
the downstream GCTS layer a finite, completely covering vocabulary.  Repeated
supports are marked ``repeated``; sites that cannot yet be explained by one
are retained as explicit species-labelled ``gap`` singleton isometry classes.
No atom disappears from the accounting.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Hashable, Sequence

Point = tuple[float, float, float]
SpeciesKey = tuple[str, str]
MetricSignature = tuple[tuple[object, ...], ...]


@dataclass(frozen=True)
class SupportOccurrence:
    """One occurrence is an unordered set of input point indices."""

    member_indices: tuple[int, ...]


@dataclass(frozen=True)
class IrregularSupportType:
    """One finite colored-metric isometry class."""

    type_id: int
    kind: str
    hierarchy_level: int
    representative_members: tuple[int, ...]
    signature: MetricSignature
    occurrences: tuple[SupportOccurrence, ...]

    @property
    def support_size(self) -> int:
        return len(self.representative_members)


@dataclass(frozen=True)
class IrregularCover:
    point_count: int
    minimum_distance: float
    support_types: tuple[IrregularSupportType, ...]
    repeated_type_count: int
    repeated_occurrence_count: int
    gap_type_count: int
    covered_indices: tuple[int, ...]
    repeated_covered_indices: tuple[int, ...]

    @property
    def complete(self) -> bool:
        return len(self.covered_indices) == self.point_count

    @property
    def repeated_coverage(self) -> float:
        return len(self.repeated_covered_indices) / self.point_count


@dataclass(frozen=True)
class FrozenSupportPrototype:
    """A train-learned type with no references to training point indices."""

    type_id: int
    hierarchy_level: int
    species: tuple[SpeciesKey, ...]
    quantized_distances: tuple[tuple[int, ...], ...]
    signature: MetricSignature


@dataclass(frozen=True)
class FrozenSupportVocabulary:
    """The complete information allowed to cross the train/test boundary."""

    prototypes: tuple[FrozenSupportPrototype, ...]
    distance_tolerance: float
    minimum_neighbors: int
    maximum_neighbors: int
    shell_gap: float
    maximum_merged_size: int


@dataclass(frozen=True)
class FrozenEnumeration:
    point_count: int
    occurrences_by_type: tuple[tuple[SupportOccurrence, ...], ...]
    covered_indices: tuple[int, ...]

    @property
    def coverage(self) -> float:
        return len(self.covered_indices) / self.point_count

    def coverage_of(self, indices: Sequence[int]) -> float:
        requested = tuple(indices)
        if any(index < 0 or index >= self.point_count for index in requested):
            raise ValueError("coverage indices are outside the target cloud")
        if not requested:
            return 1.0
        covered = set(self.covered_indices)
        return sum(index in covered for index in requested) / len(requested)


def _point(value: Sequence[float]) -> Point:
    if len(value) != 3:
        raise ValueError("every point must have exactly three coordinates")
    result = tuple(float(coordinate) for coordinate in value)
    if not all(math.isfinite(coordinate) for coordinate in result):
        raise ValueError("point coordinates must be finite")
    return result  # type: ignore[return-value]


def _species_key(value: Hashable) -> SpeciesKey:
    try:
        hash(value)
    except TypeError as error:
        raise ValueError("species labels must be hashable") from error
    return (f"{type(value).__module__}.{type(value).__qualname__}", repr(value))


def _distance_table(points: Sequence[Point]) -> tuple[tuple[float, ...], ...]:
    result = [[0.0] * len(points) for _ in points]
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            distance = math.dist(points[left], points[right])
            result[left][right] = distance
            result[right][left] = distance
    return tuple(tuple(row) for row in result)


def _quantize(value: float, tolerance: float) -> int:
    return int(round(value / tolerance))


def _metric_signature(
    members: Sequence[int],
    species: Sequence[SpeciesKey],
    distances: Sequence[Sequence[float]],
    tolerance: float,
) -> MetricSignature:
    """A permutation/rotation/translation invariant colored metric signature.

    Per-vertex distance profiles retain substantially more incidence
    information than a bare distance multiset.  For atomic supports in these
    benchmarks this is a compact deterministic canonicalizer.  A later exact
    matcher may split the (rare) homometric collision without changing the
    discovery API.
    """
    profiles = []
    for member in members:
        incident = tuple(sorted(
            (species[other], _quantize(distances[member][other], tolerance))
            for other in members if other != member))
        profiles.append((species[member], incident))
    return tuple(sorted(profiles))


def _metric_isomorphic(
    left: Sequence[int],
    right: Sequence[int],
    species: Sequence[SpeciesKey],
    distances: Sequence[Sequence[float]],
    tolerance: float,
) -> bool:
    """Decide colored isometry of two supports at the declared resolution.

    The signature is only a fast bucket key.  This finite backtracking check
    proves that a species-preserving bijection also preserves every quantized
    pair distance, preventing homometric fingerprint collisions from merging
    cluster types.
    """
    if len(left) != len(right):
        return False

    def profile(member: int, support: Sequence[int]) -> tuple[object, ...]:
        return (species[member], tuple(sorted(
            (species[other], _quantize(distances[member][other], tolerance))
            for other in support if other != member)))

    left_profiles = tuple(profile(member, left) for member in left)
    right_profiles = tuple(profile(member, right) for member in right)
    candidates = tuple(tuple(index for index, candidate in enumerate(right_profiles)
                             if candidate == left_profiles[left_index])
                       for left_index in range(len(left)))
    if any(not choices for choices in candidates):
        return False
    order = tuple(sorted(range(len(left)), key=lambda index: (len(candidates[index]), index)))
    mapping = [-1] * len(left)
    used: set[int] = set()

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        source_index = order[depth]
        source = left[source_index]
        for target_index in candidates[source_index]:
            if target_index in used:
                continue
            target = right[target_index]
            if any(
                _quantize(distances[source][left[other_source]], tolerance) !=
                _quantize(distances[target][right[other_target]], tolerance)
                for other_source, other_target in enumerate(mapping)
                if other_target >= 0
            ):
                continue
            mapping[source_index] = target_index
            used.add(target_index)
            if search(depth + 1):
                return True
            used.remove(target_index)
            mapping[source_index] = -1
        return False

    return search(0)


def _adaptive_seed(
    center: int,
    distances: Sequence[Sequence[float]],
    *,
    minimum_neighbors: int,
    maximum_neighbors: int,
    shell_gap: float,
    tolerance: float,
) -> tuple[int, ...]:
    ranked = sorted((distances[center][other], other)
                    for other in range(len(distances)) if other != center)
    if not ranked:
        return (center,)
    upper = min(maximum_neighbors, len(ranked) - 1)
    lower = min(minimum_neighbors, len(ranked))
    cutoff_index = lower - 1
    best = (-1.0, cutoff_index)
    scale = max(ranked[0][0], tolerance)
    # Choose a conspicuous local shell boundary, rather than prescribing a
    # radius or a common neighbor count.  The small penalty favors the first
    # equally clear boundary and keeps supports finite in dense clouds.
    for index in range(lower - 1, upper):
        gap = (ranked[index + 1][0] - ranked[index][0]) / scale
        score = gap - 1e-6 * index
        if gap >= shell_gap and score > best[0]:
            best = (score, index)
    if best[0] >= 0:
        cutoff_index = best[1]
    cutoff = ranked[cutoff_index][0]
    neighbors = tuple(other for distance, other in ranked
                      if distance <= cutoff + tolerance)
    return tuple(sorted((center,) + neighbors))


def _group_supports(
    supports: Sequence[tuple[int, ...]],
    species: Sequence[SpeciesKey],
    distances: Sequence[Sequence[float]],
    tolerance: float,
    minimum_occurrences: int,
) -> tuple[tuple[MetricSignature, tuple[tuple[int, ...], ...]], ...]:
    groups: DefaultDict[MetricSignature, set[tuple[int, ...]]] = defaultdict(set)
    for support in supports:
        groups[_metric_signature(support, species, distances, tolerance)].add(support)
    retained = []
    for signature, occurrences in groups.items():
        # Split each cheap signature bucket by proven colored metric-graph
        # isometry.  Usually this loop has one class; correctness does not rely
        # on that empirical fact.
        classes: list[list[tuple[int, ...]]] = []
        for occurrence in sorted(occurrences):
            for equivalence_class in classes:
                if _metric_isomorphic(
                        equivalence_class[0], occurrence, species, distances,
                        tolerance):
                    equivalence_class.append(occurrence)
                    break
            else:
                classes.append([occurrence])
        retained.extend((signature, tuple(equivalence_class))
                        for equivalence_class in classes
                        if len(equivalence_class) >= minimum_occurrences)
    retained.sort(key=lambda item: (-len(item[1][0]), -len(item[1]), item[0]))
    return tuple(retained)


def _merged_supports(
    seeds: Sequence[tuple[int, ...]], maximum_merged_size: int,
) -> tuple[tuple[int, ...], ...]:
    """Union touching seed pairs without an all-pairs seed scan."""
    containing: DefaultDict[int, list[int]] = defaultdict(list)
    for seed_index, seed in enumerate(seeds):
        for member in seed:
            containing[member].append(seed_index)
    touching_pairs: set[tuple[int, int]] = set()
    for seed_indices in containing.values():
        for offset, left in enumerate(seed_indices):
            for right in seed_indices[offset + 1:]:
                touching_pairs.add((min(left, right), max(left, right)))
    seed_sets = tuple(frozenset(seed) for seed in seeds)
    merged = set()
    for left, right in sorted(touching_pairs):
        union = tuple(sorted(seed_sets[left] | seed_sets[right]))
        if (len(union) <= maximum_merged_size and
                union != seeds[left] and union != seeds[right]):
            merged.add(union)
    return tuple(sorted(merged))


def learn_irregular_cover(
    species: Sequence[Hashable],
    positions: Sequence[Sequence[float]],
    *,
    distance_tolerance: float = 0.02,
    minimum_occurrences: int = 2,
    minimum_neighbors: int = 3,
    maximum_neighbors: int = 14,
    shell_gap: float = 0.10,
    maximum_merged_size: int = 40,
) -> IrregularCover:
    """Learn repeated irregular supports and an exact finite cover.

    Candidate construction has two levels.  Level zero groups adaptive local
    shell seeds.  Level one unions every touching pair of seeds and groups the
    resulting, generally irregular, colored metric graphs.  A deterministic
    greedy dictionary selection prefers candidates with the greatest new-site
    coverage per stored representative atom.  Finally, uncovered sites become
    explicit singleton gap classes, one per chemical-species isometry class.
    """
    if len(species) != len(positions):
        raise ValueError("species and positions must have equal length")
    if not positions:
        raise ValueError("at least one point is required")
    if distance_tolerance <= 0 or not math.isfinite(distance_tolerance):
        raise ValueError("distance_tolerance must be finite and positive")
    if minimum_occurrences < 2:
        raise ValueError("minimum_occurrences must be at least two")
    if not 1 <= minimum_neighbors <= maximum_neighbors:
        raise ValueError("invalid adaptive-neighborhood bounds")
    if shell_gap < 0 or not math.isfinite(shell_gap):
        raise ValueError("shell_gap must be finite and nonnegative")
    if maximum_merged_size < minimum_neighbors + 2:
        raise ValueError("maximum_merged_size is too small")

    points = tuple(_point(point) for point in positions)
    labels = tuple(_species_key(label) for label in species)
    distances = _distance_table(points)
    pair_distances = [distances[i][j] for i in range(len(points))
                      for j in range(i + 1, len(points))]
    minimum_distance = min(pair_distances, default=math.inf)
    if minimum_distance <= 0:
        raise ValueError("points must be distinct with positive separation")

    seeds = tuple(_adaptive_seed(
        center, distances, minimum_neighbors=minimum_neighbors,
        maximum_neighbors=maximum_neighbors, shell_gap=shell_gap,
        tolerance=distance_tolerance) for center in range(len(points)))
    level_zero = _group_supports(
        seeds, labels, distances, distance_tolerance, minimum_occurrences)

    # Touching is learned from the adaptive supports themselves.  It neither
    # assumes a bond cutoff nor imports a lattice adjacency graph.
    merged = _merged_supports(seeds, maximum_merged_size)
    level_one = _group_supports(
        merged, labels, distances, distance_tolerance,
        minimum_occurrences)

    candidates = []
    for level, groups in ((1, level_one), (0, level_zero)):
        for signature, occurrences in groups:
            union = frozenset(index for occurrence in occurrences for index in occurrence)
            # Dictionary utility rewards reusable coverage and mildly favors
            # merged supports over atom-centred seeds when both explain it.
            utility = len(union) * len(occurrences) / len(occurrences[0])
            candidates.append((-utility, -level, -len(occurrences[0]),
                               signature, occurrences, level))
    candidates.sort()

    covered: set[int] = set()
    selected = []
    for _, _, _, signature, occurrences, level in candidates:
        occurrence_union = {index for occurrence in occurrences for index in occurrence}
        if not occurrence_union - covered:
            continue
        selected.append((signature, occurrences, level))
        covered.update(occurrence_union)

    support_types = []
    for type_id, (signature, occurrences, level) in enumerate(selected):
        support_types.append(IrregularSupportType(
            type_id, "repeated", level, occurrences[0], signature,
            tuple(SupportOccurrence(occurrence) for occurrence in occurrences)))
    repeated_covered = tuple(sorted(covered))

    gap_groups: DefaultDict[SpeciesKey, list[int]] = defaultdict(list)
    for index in range(len(points)):
        if index not in covered:
            gap_groups[labels[index]].append(index)
    for label, indices in sorted(gap_groups.items()):
        type_id = len(support_types)
        signature: MetricSignature = ((label, ()),)
        support_types.append(IrregularSupportType(
            type_id, "gap", 0, (indices[0],), signature,
            tuple(SupportOccurrence((index,)) for index in indices)))
        covered.update(indices)

    return IrregularCover(
        len(points), minimum_distance, tuple(support_types), len(selected),
        sum(len(occurrences) for _, occurrences, _ in selected),
        len(gap_groups), tuple(sorted(covered)), repeated_covered)


def fit_frozen_vocabulary(
    species: Sequence[Hashable],
    positions: Sequence[Sequence[float]],
    *,
    distance_tolerance: float = 0.02,
    minimum_occurrences: int = 2,
    minimum_neighbors: int = 3,
    maximum_neighbors: int = 14,
    shell_gap: float = 0.10,
    maximum_merged_size: int = 40,
) -> tuple[FrozenSupportVocabulary, IrregularCover]:
    """Fit a cover and detach its repeated prototypes from training storage."""
    cover = learn_irregular_cover(
        species, positions, distance_tolerance=distance_tolerance,
        minimum_occurrences=minimum_occurrences,
        minimum_neighbors=minimum_neighbors,
        maximum_neighbors=maximum_neighbors, shell_gap=shell_gap,
        maximum_merged_size=maximum_merged_size)
    points = tuple(_point(point) for point in positions)
    labels = tuple(_species_key(label) for label in species)
    distances = _distance_table(points)
    prototypes = []
    for support_type in cover.support_types:
        if support_type.kind != "repeated":
            continue
        members = support_type.representative_members
        prototypes.append(FrozenSupportPrototype(
            support_type.type_id, support_type.hierarchy_level,
            tuple(labels[index] for index in members),
            tuple(tuple(_quantize(distances[left][right], distance_tolerance)
                        for right in members) for left in members),
            support_type.signature))
    vocabulary = FrozenSupportVocabulary(
        tuple(prototypes), distance_tolerance, minimum_neighbors,
        maximum_neighbors, shell_gap, maximum_merged_size)
    return vocabulary, cover


def _matches_prototype(
    prototype: FrozenSupportPrototype,
    support: Sequence[int],
    target_species: Sequence[SpeciesKey],
    target_distances: Sequence[Sequence[float]],
    tolerance: float,
) -> bool:
    if len(prototype.species) != len(support):
        return False
    target_profiles = tuple(
        (target_species[member], tuple(sorted(
            (target_species[other],
             _quantize(target_distances[member][other], tolerance))
            for other in support if other != member)))
        for member in support)
    prototype_profiles = tuple(
        (prototype.species[index], tuple(sorted(
            (prototype.species[other], prototype.quantized_distances[index][other])
            for other in range(len(prototype.species)) if other != index)))
        for index in range(len(prototype.species)))
    candidates = tuple(tuple(index for index, value in enumerate(target_profiles)
                             if value == prototype_profiles[source])
                       for source in range(len(prototype.species)))
    if any(not values for values in candidates):
        return False
    order = tuple(sorted(range(len(candidates)),
                         key=lambda index: (len(candidates[index]), index)))
    mapping = [-1] * len(candidates)
    used: set[int] = set()

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        source = order[depth]
        for target in candidates[source]:
            if target in used:
                continue
            if any(
                prototype.quantized_distances[source][other_source] !=
                _quantize(target_distances[support[target]][support[other_target]],
                          tolerance)
                for other_source, other_target in enumerate(mapping)
                if other_target >= 0
            ):
                continue
            mapping[source] = target
            used.add(target)
            if search(depth + 1):
                return True
            used.remove(target)
            mapping[source] = -1
        return False

    return search(0)


def _enumerate_prototype_subgraphs(
    prototype: FrozenSupportPrototype,
    target_species: Sequence[SpeciesKey],
    target_distances: Sequence[Sequence[float]],
    tolerance: float,
) -> tuple[tuple[int, ...], ...]:
    """Enumerate a prototype as a non-induced target metric subgraph.

    Extra target atoms impose no condition.  This is essential at a crop
    boundary: a support learned when outer atoms were unseen remains a valid
    subset after those atoms appear.  Species and the distance from a chosen
    anchor construct finite candidate shells; all remaining pair distances are
    checked during backtracking.
    """
    size = len(prototype.species)
    species_population = {
        label: sum(candidate == label for candidate in target_species)
        for label in set(prototype.species)}
    anchor = min(range(size), key=lambda index: (
        species_population.get(prototype.species[index], 0), index))
    anchor_targets = tuple(index for index, label in enumerate(target_species)
                           if label == prototype.species[anchor])
    supports: set[tuple[int, ...]] = set()
    for target_anchor in anchor_targets:
        candidates = []
        impossible = False
        for source in range(size):
            if source == anchor:
                choices = (target_anchor,)
            else:
                expected = prototype.quantized_distances[anchor][source]
                choices = tuple(target for target, label in enumerate(target_species)
                                if target != target_anchor and
                                label == prototype.species[source] and
                                _quantize(target_distances[target_anchor][target],
                                          tolerance) == expected)
            if not choices:
                impossible = True
                break
            candidates.append(choices)
        if impossible:
            continue
        order = tuple(index for index in sorted(
            range(size), key=lambda index: (len(candidates[index]), index))
            if index != anchor)
        mapping = [-1] * size
        mapping[anchor] = target_anchor
        used = {target_anchor}

        def search(depth: int) -> None:
            if depth == len(order):
                supports.add(tuple(sorted(mapping)))
                return
            source = order[depth]
            for target in candidates[source]:
                if target in used:
                    continue
                if any(
                    prototype.quantized_distances[source][other_source] !=
                    _quantize(target_distances[target][other_target], tolerance)
                    for other_source, other_target in enumerate(mapping)
                    if other_target >= 0
                ):
                    continue
                mapping[source] = target
                used.add(target)
                search(depth + 1)
                used.remove(target)
                mapping[source] = -1

        search(0)
    return tuple(sorted(supports))


def enumerate_frozen_vocabulary(
    vocabulary: FrozenSupportVocabulary,
    species: Sequence[Hashable],
    positions: Sequence[Sequence[float]],
) -> FrozenEnumeration:
    """Enumerate train-frozen types in a target cloud without fitting types."""
    if len(species) != len(positions):
        raise ValueError("species and positions must have equal length")
    if not positions:
        raise ValueError("at least one point is required")
    points = tuple(_point(point) for point in positions)
    labels = tuple(_species_key(label) for label in species)
    distances = _distance_table(points)
    ordered = tuple(tuple(SupportOccurrence(support) for support in
                          _enumerate_prototype_subgraphs(
                              prototype, labels, distances,
                              vocabulary.distance_tolerance))
                    for prototype in vocabulary.prototypes)
    covered = tuple(sorted({index for group in ordered
                            for occurrence in group
                            for index in occurrence.member_indices}))
    return FrozenEnumeration(len(points), ordered, covered)
