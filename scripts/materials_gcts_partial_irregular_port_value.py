#!/usr/bin/env python3
"""Finite train-only value table for typed irregular-support port graphs."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_partial_irregular_port_graph import \
    PartialIrregularPortGraph


@dataclass(frozen=True)
class PartialPortGraphExample:
    group: Hashable
    graph: PartialIrregularPortGraph
    successful: bool


@dataclass(frozen=True)
class PartialPortGraphValueSpec:
    minimum_support: int = 2
    minimum_groups: int = 2
    beta_prior: float = .5


@dataclass(frozen=True)
class FrozenPartialPortGraphValue:
    spec: PartialPortGraphValueSpec
    exact_scores: tuple[tuple[Hashable, float], ...]
    node_scores: tuple[tuple[Hashable, float], ...]
    port_scores: tuple[tuple[Hashable, float], ...]
    global_score: float
    training_groups: int
    training_examples: int
    model_digest: str
    target_used: bool = False


@dataclass(frozen=True)
class PartialPortGraphScore:
    probability: float
    backoff_level: str
    train_supported: bool


def _exact_key(graph: PartialIrregularPortGraph):
    return (graph.nodes, graph.edges)


def _node_key(graph: PartialIrregularPortGraph):
    return graph.nodes


def _port_key(graph: PartialIrregularPortGraph):
    # Remove recurrent support IDs only at the last backoff. Chemistry,
    # distance profiles, proper chirality, and graph edge multiplicity remain.
    return tuple((edge.shared_species, edge.separation_bin,
                  edge.shared_distance_profiles, edge.chirality)
                 for edge in graph.edges)


def _fit_table(rows, key, spec):
    buckets = defaultdict(list)
    for row in rows:
        buckets[key(row.graph)].append(row)
    result = []
    for code, examples in buckets.items():
        if (len(examples) < spec.minimum_support
                or len({row.group for row in examples}) < spec.minimum_groups):
            continue
        positive = sum(row.successful for row in examples)
        probability = (positive + spec.beta_prior) / \
            (len(examples) + 2 * spec.beta_prior)
        result.append((code, probability))
    return tuple(sorted(result, key=lambda row: repr(row[0])))


def fit_partial_port_graph_value(
        examples: Sequence[PartialPortGraphExample],
        spec: PartialPortGraphValueSpec = PartialPortGraphValueSpec(),
        ) -> FrozenPartialPortGraphValue:
    rows = tuple(examples)
    groups = {row.group for row in rows}
    if (not rows or len(groups) < 2 or spec.minimum_support < 1
            or spec.minimum_groups < 1
            or spec.minimum_groups > len(groups) or spec.beta_prior <= 0
            or any(row.graph.target_used for row in rows)):
        raise ValueError("invalid partial port-graph training corpus")
    positive = sum(row.successful for row in rows)
    global_score = (positive + spec.beta_prior) / \
        (len(rows) + 2 * spec.beta_prior)
    exact = _fit_table(rows, _exact_key, spec)
    nodes = _fit_table(rows, _node_key, spec)
    ports = _fit_table(rows, _port_key, spec)
    payload = (spec, exact, nodes, ports, global_score,
               len(groups), len(rows))
    return FrozenPartialPortGraphValue(
        spec, exact, nodes, ports, global_score, len(groups), len(rows),
        hashlib.sha256(repr(payload).encode()).hexdigest())


def score_partial_port_graph(
        model: FrozenPartialPortGraphValue,
        graph: PartialIrregularPortGraph,
        ) -> PartialPortGraphScore:
    if graph.target_used:
        raise ValueError("target-tainted port graph cannot be ranked")
    for level, table, key in (
            ("exact", model.exact_scores, _exact_key),
            ("nodes", model.node_scores, _node_key),
            ("ports", model.port_scores, _port_key)):
        scores = dict(table)
        code = key(graph)
        if code in scores:
            return PartialPortGraphScore(scores[code], level, True)
    return PartialPortGraphScore(model.global_score, "global", False)

