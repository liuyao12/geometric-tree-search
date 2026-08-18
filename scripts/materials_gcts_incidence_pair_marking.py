#!/usr/bin/env python3
"""Finite train-only pair interactions for local GCTS incidence markings."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)


@dataclass(frozen=True)
class IncidencePairSpec:
    family_pairs: tuple[tuple[str, str], ...]
    minimum_support: int
    minimum_groups: int
    shrinkage: float = .5
    smoothing: float = 1.
    additive_mix: float = .5


@dataclass(frozen=True)
class PairEvidence:
    positive: int
    total: int
    independent_groups: int


@dataclass(frozen=True)
class FrozenIncidencePairMarking:
    spec: IncidencePairSpec
    intercept: float
    weights: Mapping[Hashable, float]
    evidence: Mapping[Hashable, PairEvidence]


def _family(token):
    return token[0] if isinstance(token, tuple) and token else token


def incidence_pair_keys(descriptor: CandidateIncidenceDescriptor,
                        family_pairs: tuple[tuple[str, str], ...]):
    """Return finite unordered token interactions from declared families."""
    by_family = defaultdict(list)
    for token in set(descriptor.tokens):
        by_family[_family(token)].append(token)
    result = []
    for left_family, right_family in family_pairs:
        left = sorted(by_family.get(left_family, ()), key=repr)
        right = sorted(by_family.get(right_family, ()), key=repr)
        if left_family == right_family:
            result.extend((left_family, right_family, left[index], left[other])
                          for index in range(len(left))
                          for other in range(index + 1, len(left)))
        else:
            result.extend((left_family, right_family, one, two)
                          for one in left for two in right)
    return tuple(result)


def incidence_pair_group_statistics(
        groups: Sequence[Sequence[IncidenceTokenExample]], *,
        family_pairs: tuple[tuple[str, str], ...]):
    if not groups or any(not group for group in groups):
        raise ValueError("incidence-pair groups must be nonempty")
    labels = tuple((sum(row.successful for row in group), len(group))
                   for group in groups)
    by_group = []
    for group in groups:
        counts = defaultdict(lambda: [0, 0])
        for row in group:
            for key in incidence_pair_keys(row.descriptor, family_pairs):
                counts[key][0] += int(row.successful)
                counts[key][1] += 1
        by_group.append(dict(counts))
    return labels, tuple(by_group)


def fit_incidence_pair_group_statistics(
        statistics, included_groups: Sequence[int], *,
        spec: IncidencePairSpec) -> FrozenIncidencePairMarking:
    labels, by_group = statistics
    included = tuple(included_groups)
    positive = sum(labels[index][0] for index in included)
    total = sum(labels[index][1] for index in included)
    if (not spec.family_pairs or spec.minimum_support < 1 or
            spec.minimum_groups < 1 or spec.shrinkage <= 0 or
            spec.smoothing <= 0 or not 0 <= spec.additive_mix <= 1 or
            not 0 < positive < total):
        raise ValueError("invalid incidence-pair training data")
    prior = (positive + spec.smoothing) / (total + 2 * spec.smoothing)
    intercept = math.log(prior / (1. - prior))
    aggregate = defaultdict(lambda: [0, 0, 0])
    for index in included:
        for key, (key_positive, key_total) in by_group[index].items():
            aggregate[key][0] += key_positive
            aggregate[key][1] += key_total
            aggregate[key][2] += 1
    evidence = {key: PairEvidence(*row) for key, row in aggregate.items()}
    weights = {}
    for key, row in evidence.items():
        if (row.total < spec.minimum_support or
                row.independent_groups < spec.minimum_groups):
            continue
        probability = (row.positive + spec.smoothing) / (
            row.total + 2 * spec.smoothing)
        logit = math.log(probability / (1. - probability))
        weights[key] = max(-4., min(4., spec.shrinkage *
                                    (logit - intercept)))
    return FrozenIncidencePairMarking(spec, intercept, weights, evidence)


def score_incidence_pair_marking(
        marking: FrozenIncidencePairMarking,
        descriptor: CandidateIncidenceDescriptor) -> float:
    """Score pair interactions with one normalized vote per family pair."""
    by_pair = defaultdict(list)
    for key in incidence_pair_keys(descriptor, marking.spec.family_pairs):
        if key in marking.weights:
            by_pair[key[:2]].append(marking.weights[key])
    channels = tuple(sum(values) / len(values)
                     for values in by_pair.values() if values)
    interaction = sum(channels) / math.sqrt(len(channels)) if channels else 0.
    value = marking.intercept + marking.spec.additive_mix * interaction
    if value >= 0:
        inverse = math.exp(-min(value, 50.))
        return 1. / (1. + inverse)
    exponential = math.exp(max(value, -50.))
    return exponential / (1. + exponential)


def incidence_pair_adjustment(
        marking: FrozenIncidencePairMarking,
        descriptor: CandidateIncidenceDescriptor) -> float:
    """Return the centered pair term for combination with another marking."""
    by_pair = defaultdict(list)
    for key in incidence_pair_keys(descriptor, marking.spec.family_pairs):
        if key in marking.weights:
            by_pair[key[:2]].append(marking.weights[key])
    channels = tuple(sum(values) / len(values)
                     for values in by_pair.values() if values)
    return (marking.spec.additive_mix * sum(channels) /
            math.sqrt(len(channels))) if channels else 0.


def incidence_pair_marking_digest(marking: FrozenIncidencePairMarking):
    canonical = tuple(sorted(((key, row.positive, row.total,
                               row.independent_groups,
                               marking.weights.get(key))
                              for key, row in marking.evidence.items()),
                             key=lambda item: repr(item[0])))
    return hashlib.sha256(repr((marking.spec, marking.intercept,
                                canonical)).encode()).hexdigest()
