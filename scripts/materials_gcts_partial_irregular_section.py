#!/usr/bin/env python3
"""Partial local sections over a frozen irregular-support vocabulary.

A frontier atom need not complete an entire stored cluster.  This module asks
how large a species-preserving metric subgraph containing that atom is already
witnessed by occupied sites.  It never invents missing sites and cannot admit
an action; its only output is a bounded marking feature for ranking exact
candidate geometry supplied elsewhere.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_supports import (
    FrozenSupportPrototype, FrozenSupportVocabulary, _quantize, _species_key)


Point = tuple[float, float, float]


@dataclass(frozen=True)
class PartialSupportMatch:
    action_index: int
    prototype_type_id: int
    matched_atoms: int
    prototype_atoms: int
    matched_fraction: float
    training_group_support: int
    search_nodes: int
    matched_target_indices: tuple[int, ...]


@dataclass(frozen=True)
class PartialIrregularSection:
    action_matches: tuple[PartialSupportMatch, ...]
    minimum_matched_fraction: float
    mean_matched_fraction: float
    minimum_matched_atoms: int
    pair_shared_occupied_atoms: tuple[int, ...]
    minimum_pair_shared_occupied: int
    mean_pair_shared_occupied: float
    maximum_pair_shared_occupied: int
    connected_action_pairs: int
    all_searches_exact: bool
    lattice_coordinates_used: bool = False
    target_used: bool = False


class PartialSupportSearchLimit(RuntimeError):
    pass


def _points(rows: Sequence[Sequence[float]]) -> tuple[Point, ...]:
    result = tuple(tuple(map(float, row)) for row in rows)
    if any(len(point) != 3 or not all(map(math.isfinite, point))
           for point in result):
        raise ValueError("partial-support points must be finite 3D vectors")
    return result  # type: ignore[return-value]


def _maximum_anchored_match(
        prototype: FrozenSupportPrototype,
        positions: tuple[Point, ...], labels, anchor_target: int,
        tolerance: float, maximum_search_nodes: int,
        ) -> tuple[int, int, tuple[int, ...]]:
    best = 1
    best_targets = (anchor_target,)
    visited = 0
    for anchor_source, species in enumerate(prototype.species):
        if species != labels[anchor_target]:
            continue
        candidates = {}
        for source in range(len(prototype.species)):
            if source == anchor_source:
                continue
            expected = prototype.quantized_distances[anchor_source][source]
            choices = tuple(
                target for target, label in enumerate(labels)
                if target != anchor_target and label == prototype.species[source]
                and _quantize(math.dist(
                    positions[anchor_target], positions[target]), tolerance)
                    == expected)
            if choices:
                candidates[source] = choices
        order = tuple(sorted(candidates,
                             key=lambda source: (len(candidates[source]),
                                                 source)))
        mapping = {anchor_source: anchor_target}
        used = {anchor_target}

        def search(depth: int) -> None:
            nonlocal best, best_targets, visited
            visited += 1
            if visited > maximum_search_nodes:
                raise PartialSupportSearchLimit(
                    "partial irregular-support search exceeded its bound")
            targets = tuple(sorted(mapping.values()))
            if len(mapping) > best or (len(mapping) == best
                                       and targets < best_targets):
                best = len(mapping)
                best_targets = targets
            if depth == len(order) or \
                    len(mapping) + len(order) - depth <= best:
                return
            source = order[depth]
            for target in candidates[source]:
                if target in used:
                    continue
                if any(
                    prototype.quantized_distances[source][other_source] !=
                    _quantize(math.dist(
                        positions[target], positions[other_target]), tolerance)
                    for other_source, other_target in mapping.items()
                ):
                    continue
                mapping[source] = target
                used.add(target)
                search(depth + 1)
                used.remove(target)
                del mapping[source]
            # A partial section may omit any not-yet-grown prototype vertex.
            search(depth + 1)

        search(0)
    return best, visited, best_targets


def partial_irregular_section(
        vocabulary: FrozenSupportVocabulary,
        training_group_support: Sequence[int],
        occupied_positions: Sequence[Sequence[float]],
        occupied_species: Sequence[Hashable],
        action_positions: Sequence[Sequence[float]],
        action_species: Sequence[Hashable],
        *, maximum_search_nodes: int = 20_000,
        ) -> PartialIrregularSection:
    """Score every action as an anchor of a recurrent partial support."""
    occupied = _points(occupied_positions)
    actions = _points(action_positions)
    occupied_species = tuple(occupied_species)
    action_species = tuple(action_species)
    prototypes = tuple(vocabulary.prototypes)
    support = tuple(map(int, training_group_support))
    if (not prototypes or len(support) != len(prototypes)
            or any(value < 1 for value in support)
            or len(occupied) != len(occupied_species) or not actions
            or len(actions) != len(action_species)
            or len(set(occupied + actions)) != len(occupied) + len(actions)
            or maximum_search_nodes < 1):
        raise ValueError("invalid partial irregular-section inputs")
    positions = occupied + actions
    labels = tuple(_species_key(item)
                   for item in occupied_species + action_species)
    matches = []
    for offset, _action in enumerate(actions):
        anchor = len(occupied) + offset
        rows = []
        for prototype, groups in zip(prototypes, support):
            if labels[anchor] not in prototype.species:
                continue
            matched, visited, targets = _maximum_anchored_match(
                prototype, positions, labels, anchor,
                vocabulary.distance_tolerance, maximum_search_nodes)
            rows.append((matched / len(prototype.species), matched, groups,
                         -len(prototype.species), -prototype.type_id,
                         prototype, visited, targets))
        if not rows:
            raise ValueError("no frozen support prototype has the action species")
        fraction, matched, groups, _size, _type, prototype, visited, targets = \
            max(rows)
        matches.append(PartialSupportMatch(
            offset, prototype.type_id, matched, len(prototype.species),
            fraction, groups, visited, targets))
    fractions = tuple(row.matched_fraction for row in matches)
    occupied_limit = len(occupied)
    occupied_matches = tuple({index for index in row.matched_target_indices
                              if index < occupied_limit} for row in matches)
    pair_shared = tuple(len(left & right)
                        for offset, left in enumerate(occupied_matches)
                        for right in occupied_matches[offset + 1:])
    return PartialIrregularSection(
        tuple(matches), min(fractions), sum(fractions) / len(fractions),
        min(row.matched_atoms for row in matches), pair_shared,
        min(pair_shared, default=0),
        sum(pair_shared) / len(pair_shared) if pair_shared else 0.,
        max(pair_shared, default=0), sum(value > 0 for value in pair_shared),
        True)
