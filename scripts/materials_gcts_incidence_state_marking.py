#!/usr/bin/env python3
"""Finite train-only conditional states for local GCTS incidence graphs."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)


@dataclass(frozen=True)
class IncidenceStateSpec:
    signature_levels: tuple[tuple[str, ...], ...]
    minimum_support: int
    minimum_groups: int
    smoothing: float = 1.


@dataclass(frozen=True)
class IncidenceStateEvidence:
    positive: int
    total: int
    independent_groups: int


@dataclass(frozen=True)
class FrozenIncidenceStateMarking:
    spec: IncidenceStateSpec
    prior: float
    evidence_by_level: tuple[Mapping[Hashable, IncidenceStateEvidence], ...]


def incidence_state_key(descriptor: CandidateIncidenceDescriptor,
                        families: tuple[str, ...]):
    allowed = set(families)
    return tuple(sorted((token for token in descriptor.tokens
                         if isinstance(token, tuple) and token and
                         token[0] in allowed), key=repr))


def fit_incidence_state_marking(
        examples: Sequence[IncidenceTokenExample], *,
        spec: IncidenceStateSpec) -> FrozenIncidenceStateMarking:
    if (not examples or not spec.signature_levels or
            any(not level for level in spec.signature_levels) or
            spec.minimum_support < 1 or spec.minimum_groups < 1 or
            spec.smoothing <= 0 or not any(row.successful for row in examples)
            or all(row.successful for row in examples)):
        raise ValueError("invalid finite incidence-state training data")
    positive = sum(row.successful for row in examples)
    prior = (positive + spec.smoothing) / (
        len(examples) + 2 * spec.smoothing)
    levels = []
    for families in spec.signature_levels:
        counts = defaultdict(lambda: [0, 0, set()])
        for row in examples:
            key = incidence_state_key(row.descriptor, families)
            counts[key][0] += int(row.successful)
            counts[key][1] += 1
            counts[key][2].add(row.group)
        levels.append({key: IncidenceStateEvidence(
            row[0], row[1], len(row[2])) for key, row in counts.items()})
    return FrozenIncidenceStateMarking(spec, prior, tuple(levels))


def incidence_state_group_statistics(
        groups: Sequence[Sequence[IncidenceTokenExample]], *,
        signature_levels: tuple[tuple[str, ...], ...]):
    if not groups or any(not group for group in groups):
        raise ValueError("incidence-state groups must be nonempty")
    labels = tuple((sum(row.successful for row in group), len(group))
                   for group in groups)
    levels = []
    for families in signature_levels:
        by_group = []
        for group in groups:
            counts = defaultdict(lambda: [0, 0])
            for row in group:
                key = incidence_state_key(row.descriptor, families)
                counts[key][0] += int(row.successful)
                counts[key][1] += 1
            by_group.append(dict(counts))
        levels.append(tuple(by_group))
    return labels, tuple(levels)


def fit_incidence_state_group_statistics(
        statistics, included_groups: Sequence[int], *,
        spec: IncidenceStateSpec) -> FrozenIncidenceStateMarking:
    labels, levels = statistics
    included = tuple(included_groups)
    positive = sum(labels[index][0] for index in included)
    total = sum(labels[index][1] for index in included)
    if not 0 < positive < total:
        raise ValueError("incidence-state folds need both labels")
    prior = (positive + spec.smoothing) / (total + 2 * spec.smoothing)
    evidence_levels = []
    for by_group in levels:
        aggregate = defaultdict(lambda: [0, 0, 0])
        for index in included:
            for key, (key_positive, key_total) in by_group[index].items():
                aggregate[key][0] += key_positive
                aggregate[key][1] += key_total
                aggregate[key][2] += 1
        evidence_levels.append({key: IncidenceStateEvidence(*row)
                                for key, row in aggregate.items()})
    return FrozenIncidenceStateMarking(
        spec, prior, tuple(evidence_levels))


def score_incidence_state_marking(
        marking: FrozenIncidenceStateMarking,
        descriptor: CandidateIncidenceDescriptor) -> float:
    for families, evidence in zip(
            marking.spec.signature_levels, marking.evidence_by_level):
        row = evidence.get(incidence_state_key(descriptor, families))
        if (row is None or row.total < marking.spec.minimum_support or
                row.independent_groups < marking.spec.minimum_groups):
            continue
        return (row.positive + marking.spec.smoothing) / (
            row.total + 2 * marking.spec.smoothing)
    return marking.prior


def incidence_state_marking_digest(
        marking: FrozenIncidenceStateMarking) -> str:
    canonical = tuple(tuple(sorted((
        (key, row.positive, row.total, row.independent_groups)
        for key, row in level.items()), key=lambda item: repr(item[0])))
        for level in marking.evidence_by_level)
    return hashlib.sha256(repr((
        marking.spec, marking.prior, canonical)).encode()).hexdigest()
