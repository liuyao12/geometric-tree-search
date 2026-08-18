#!/usr/bin/env python3
"""Fit a recurrent irregular-support vocabulary across independent clouds.

Each cloud is fitted independently.  A support class earns one vote per cloud,
regardless of how many occurrences or duplicate prototypes that cloud contains.
Cheap metric signatures are only buckets: an exact colored, quantized complete-
graph isomorphism check splits homometric collisions before recurrence is
counted.  The result is detached from all source coordinates and atom IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_supports import (
    FrozenSupportPrototype, FrozenSupportVocabulary, IrregularCover,
    fit_frozen_vocabulary)


@dataclass(frozen=True)
class GroupedIrregularVocabulary:
    vocabulary: FrozenSupportVocabulary
    training_group_support: tuple[int, ...]
    fitted_group_count: int
    input_prototype_count: int
    recurrent_prototype_count: int
    repeated_coverage_by_group: tuple[float, ...]
    lattice_coordinates_used: bool = False
    target_used: bool = False


def _prototype_isomorphic(
        left: FrozenSupportPrototype,
        right: FrozenSupportPrototype,
        ) -> bool:
    if (len(left.species) != len(right.species)
            or left.signature != right.signature):
        return False
    candidates = tuple(tuple(
        target for target, species in enumerate(right.species)
        if species == left.species[source]
        and tuple(sorted(
            (right.species[other], right.quantized_distances[target][other])
            for other in range(len(right.species)) if other != target))
        == tuple(sorted(
            (left.species[other], left.quantized_distances[source][other])
            for other in range(len(left.species)) if other != source))
    ) for source in range(len(left.species)))
    if any(not row for row in candidates):
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
                left.quantized_distances[source][other_source] !=
                right.quantized_distances[target][other_target]
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


def merge_grouped_vocabulary(
        vocabularies: Sequence[FrozenSupportVocabulary],
        repeated_coverage_by_group: Sequence[float],
        *, minimum_group_support: int,
        ) -> GroupedIrregularVocabulary:
    """Merge already-fitted vocabularies without seeing source coordinates."""
    vocabularies = tuple(vocabularies)
    coverage = tuple(map(float, repeated_coverage_by_group))
    if (not vocabularies or len(coverage) != len(vocabularies)
            or not 1 <= minimum_group_support <= len(vocabularies)
            or any(not 0. <= value <= 1. for value in coverage)):
        raise ValueError("invalid grouped-vocabulary inputs")
    schema = vocabularies[0]
    schema_fields = ("distance_tolerance", "minimum_neighbors",
                     "maximum_neighbors", "shell_gap",
                     "maximum_merged_size")
    if any(any(getattr(row, field) != getattr(schema, field)
               for field in schema_fields) for row in vocabularies[1:]):
        raise ValueError("all grouped vocabularies must share one frozen schema")

    classes: list[dict[str, object]] = []
    input_count = 0
    for group_index, vocabulary in enumerate(vocabularies):
        seen_in_group: set[int] = set()
        for prototype in vocabulary.prototypes:
            input_count += 1
            matched = next((index for index, row in enumerate(classes)
                            if row["signature"] == prototype.signature
                            and _prototype_isomorphic(
                                row["prototype"], prototype)), None)  # type: ignore[arg-type]
            if matched is None:
                matched = len(classes)
                classes.append({"signature": prototype.signature,
                                "prototype": prototype, "groups": set()})
            # Duplicate isometry classes in one cloud never add recurrence.
            if matched not in seen_in_group:
                classes[matched]["groups"].add(group_index)  # type: ignore[union-attr]
                seen_in_group.add(matched)

    retained = [row for row in classes
                if len(row["groups"]) >= minimum_group_support]  # type: ignore[arg-type]
    retained.sort(key=lambda row: (
        -len(row["groups"]),  # type: ignore[arg-type]
        -len(row["prototype"].species),  # type: ignore[union-attr]
        row["prototype"].hierarchy_level,  # type: ignore[union-attr]
        row["signature"]))
    prototypes = tuple(FrozenSupportPrototype(
        type_id, row["prototype"].hierarchy_level,  # type: ignore[union-attr]
        row["prototype"].species,  # type: ignore[union-attr]
        row["prototype"].quantized_distances,  # type: ignore[union-attr]
        row["prototype"].signature,  # type: ignore[union-attr]
    ) for type_id, row in enumerate(retained))
    merged = FrozenSupportVocabulary(
        prototypes, schema.distance_tolerance, schema.minimum_neighbors,
        schema.maximum_neighbors, schema.shell_gap, schema.maximum_merged_size)
    return GroupedIrregularVocabulary(
        merged, tuple(len(row["groups"]) for row in retained),  # type: ignore[arg-type]
        len(vocabularies), input_count, len(prototypes), coverage)


def fit_grouped_irregular_vocabulary(
        groups: Sequence[tuple[Sequence[Hashable],
                               Sequence[Sequence[float]]]],
        *, minimum_group_support: int = 3,
        distance_tolerance: float = 0.02,
        minimum_occurrences: int = 2,
        minimum_neighbors: int = 3,
        maximum_neighbors: int = 14,
        shell_gap: float = 0.10,
        maximum_merged_size: int = 40,
        ) -> tuple[GroupedIrregularVocabulary, tuple[IrregularCover, ...]]:
    """Fit each independent cloud, then retain cross-cloud recurrence."""
    if not groups:
        raise ValueError("at least one independent training group is required")
    fitted = tuple(fit_frozen_vocabulary(
        species, positions, distance_tolerance=distance_tolerance,
        minimum_occurrences=minimum_occurrences,
        minimum_neighbors=minimum_neighbors,
        maximum_neighbors=maximum_neighbors, shell_gap=shell_gap,
        maximum_merged_size=maximum_merged_size) for species, positions in groups)
    vocabularies = tuple(row[0] for row in fitted)
    covers = tuple(row[1] for row in fitted)
    grouped = merge_grouped_vocabulary(
        vocabularies, tuple(row.repeated_coverage for row in covers),
        minimum_group_support=minimum_group_support)
    return grouped, covers

