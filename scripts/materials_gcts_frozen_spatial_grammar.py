#!/usr/bin/env python3
"""Fit and replay a frozen cluster-of-clusters grammar across spatial domains."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence, Tuple

from materials_gcts_spatial_support_hierarchy import (
    Signature, SpatialSupportHierarchy, learn_spatial_support_hierarchy)


@dataclass(frozen=True)
class FrozenSpatialProduction:
    level: int
    parent_type: Signature
    child_alternatives: Tuple[Tuple[Signature, ...], ...]
    training_occurrences: int
    training_domains: int


@dataclass(frozen=True)
class FrozenSpatialGrammar:
    length_unit: float
    radius_scales: Tuple[float, ...]
    type_vocabularies: Tuple[Tuple[Signature, ...], ...]
    productions: Tuple[FrozenSpatialProduction, ...]
    training_domains: int
    heldout_geometry_used: bool


@dataclass(frozen=True)
class FrozenReplayLevel:
    level: int
    heldout_occurrences: int
    known_type_occurrences: int
    known_type_atoms: int
    heldout_atoms: int
    known_type_occurrence_fraction: float
    known_type_atom_fraction: float
    production_checked_occurrences: int
    production_agreement_fraction: float
    unseen_types: int
    unseen_productions: int


@dataclass(frozen=True)
class FrozenSpatialReplay:
    levels: Tuple[FrozenReplayLevel, ...]
    all_types_known: bool
    all_productions_transfer: bool
    all_atoms_covered_by_known_types: bool
    heldout_geometry_used_for_fitting: bool


def fit_frozen_spatial_grammar(
    positions: Sequence[Sequence[float]],
    species: Sequence[Hashable],
    training_domains: Mapping[Hashable, Sequence[int]],
    *,
    radius_scales: Sequence[float] = (1.08, 2.0, 3.7),
) -> Tuple[FrozenSpatialGrammar, SpatialSupportHierarchy]:
    hierarchy = learn_spatial_support_hierarchy(
        positions, species, training_domains, radius_scales=radius_scales)
    vocabularies = []
    grouped = defaultdict(list)
    domain_support = defaultdict(set)
    for level in hierarchy.levels:
        vocabulary = tuple(sorted(
            {item.geometry_type for item in level.occurrences}, key=repr))
        vocabularies.append(vocabulary)
        for occurrence in level.occurrences:
            key = (level.level, occurrence.geometry_type)
            grouped[key].append(occurrence.child_types)
            domain_support[key].add(occurrence.domain)
    productions = tuple(FrozenSpatialProduction(
        level, parent,
        tuple(sorted(set(alternatives), key=repr)), len(alternatives),
        len(domain_support[(level, parent)]))
        for (level, parent), alternatives in sorted(
            grouped.items(), key=lambda item: repr(item[0])))
    return FrozenSpatialGrammar(
        hierarchy.nearest_neighbor_scale, tuple(radius_scales),
        tuple(vocabularies), productions, len(training_domains), False), hierarchy


def replay_frozen_spatial_grammar(
    grammar: FrozenSpatialGrammar,
    positions: Sequence[Sequence[float]],
    species: Sequence[Hashable],
    heldout_domains: Mapping[Hashable, Sequence[int]],
) -> Tuple[FrozenSpatialReplay, SpatialSupportHierarchy]:
    hierarchy = learn_spatial_support_hierarchy(
        positions, species, heldout_domains,
        radius_scales=grammar.radius_scales,
        frozen_length_unit=grammar.length_unit)
    rules = {(item.level, item.parent_type): set(item.child_alternatives)
             for item in grammar.productions}
    reports = []
    for level, vocabulary in zip(hierarchy.levels,
                                 grammar.type_vocabularies):
        known = set(vocabulary)
        known_occurrences = [item for item in level.occurrences
                             if item.geometry_type in known]
        all_atoms = {atom for item in level.occurrences for atom in item.support}
        known_atoms = {atom for item in known_occurrences
                       for atom in item.support}
        checked = 0
        matched = 0
        unseen_productions = 0
        for occurrence in known_occurrences:
            checked += 1
            alternatives = rules.get((level.level, occurrence.geometry_type))
            if alternatives is not None and occurrence.child_types in alternatives:
                matched += 1
            else:
                unseen_productions += 1
        reports.append(FrozenReplayLevel(
            level.level, len(level.occurrences), len(known_occurrences),
            len(known_atoms), len(all_atoms),
            len(known_occurrences) / max(1, len(level.occurrences)),
            len(known_atoms) / max(1, len(all_atoms)), checked,
            matched / max(1, checked),
            len({item.geometry_type for item in level.occurrences} - known),
            unseen_productions))
    all_types = all(item.unseen_types == 0 for item in reports)
    productions = all(item.unseen_productions == 0 and
                      item.production_agreement_fraction == 1.0
                      for item in reports)
    atoms = all(item.known_type_atom_fraction == 1.0 for item in reports)
    return FrozenSpatialReplay(
        tuple(reports), all_types, productions, atoms,
        grammar.heldout_geometry_used), hierarchy
