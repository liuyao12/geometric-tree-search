#!/usr/bin/env python3
"""Finite invariant marking for a compatible unordered pair of GCTS actions."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence


@dataclass(frozen=True)
class ActionPairDescriptor:
    tokens: tuple[Hashable, ...]


@dataclass(frozen=True)
class ActionPairExample:
    group: Hashable
    descriptor: ActionPairDescriptor
    successful: bool


@dataclass(frozen=True)
class ActionPairEvidence:
    positive: int
    total: int
    independent_groups: int


@dataclass(frozen=True)
class FrozenActionPairMarking:
    minimum_support: int
    minimum_groups: int
    shrinkage: float
    smoothing: float
    intercept: float
    weights: Mapping[Hashable, float]
    evidence: Mapping[Hashable, ActionPairEvidence]


SUMMARY_FAMILIES = frozenset((
    "coarse-role", "predicted-colors", "occupied-count",
    "role-occupied-message-graph"))


def _summary(row):
    return tuple(token for token in row.descriptor.tokens
                 if isinstance(token, tuple) and token and
                 token[0] in SUMMARY_FAMILIES)


def action_pair_descriptor(left, right, *, distance_bin_width=.25):
    """Encode an unordered action pair without a global position or frame."""
    if distance_bin_width <= 0 or left.group != right.group:
        raise ValueError("action pair must share a group and valid scale")
    scale = (left.minimum_distance + right.minimum_distance) / 2.
    distance_bin = round(math.dist(left.point, right.point) /
                         (scale * distance_bin_width))
    summaries = tuple(sorted((_summary(left), _summary(right)), key=repr))
    colors = tuple(sorted((str(left.color), str(right.color))))
    tokens = {
        ("pair-distance", distance_bin),
        ("pair-colors", colors),
        ("pair-color-distance", colors, distance_bin),
        ("pair-summary", summaries),
    }
    for family in SUMMARY_FAMILIES:
        values = tuple(tuple(token for token in summary if token[0] == family)
                       for summary in summaries)
        tokens.add(("paired-family", family, values))
        tokens.add(("paired-family-distance", family, values, distance_bin))
    return ActionPairDescriptor(tuple(sorted(tokens, key=repr)))


def fit_action_pair_marking(
        examples: Sequence[ActionPairExample], *, minimum_support=4,
        minimum_groups=2, shrinkage=.5,
        smoothing=1.) -> FrozenActionPairMarking:
    if (not examples or minimum_support < 1 or minimum_groups < 1 or
            shrinkage <= 0 or smoothing <= 0 or
            not any(row.successful for row in examples) or
            all(row.successful for row in examples)):
        raise ValueError("action-pair marking needs both labels")
    positive = sum(row.successful for row in examples)
    prior = (positive + smoothing) / (len(examples) + 2 * smoothing)
    intercept = math.log(prior / (1. - prior))
    counts = defaultdict(lambda: [0, 0, set()])
    for row in examples:
        for token in set(row.descriptor.tokens):
            counts[token][0] += int(row.successful)
            counts[token][1] += 1
            counts[token][2].add(row.group)
    evidence = {key: ActionPairEvidence(pos, total, len(groups))
                for key, (pos, total, groups) in counts.items()}
    weights = {}
    for key, row in evidence.items():
        if row.total < minimum_support or \
                row.independent_groups < minimum_groups:
            continue
        probability = (row.positive + smoothing) / (row.total + 2 * smoothing)
        logit = math.log(probability / (1. - probability))
        weights[key] = max(-4., min(4., shrinkage * (logit - intercept)))
    return FrozenActionPairMarking(
        minimum_support, minimum_groups, shrinkage, smoothing, intercept,
        weights, evidence)


def action_pair_adjustment(marking: FrozenActionPairMarking,
                           descriptor: ActionPairDescriptor):
    families = defaultdict(list)
    for token in descriptor.tokens:
        if token in marking.weights:
            families[token[0]].append(marking.weights[token])
    channels = tuple(sum(values) / len(values)
                     for values in families.values() if values)
    return sum(channels) / math.sqrt(len(channels)) if channels else 0.


def action_pair_marking_digest(marking: FrozenActionPairMarking):
    rows = tuple(sorted(((key, row.positive, row.total,
                          row.independent_groups, marking.weights.get(key))
                         for key, row in marking.evidence.items()),
                        key=lambda item: repr(item[0])))
    return hashlib.sha256(repr((
        marking.minimum_support, marking.minimum_groups, marking.shrinkage,
        marking.smoothing, marking.intercept, rows)).encode()).hexdigest()
