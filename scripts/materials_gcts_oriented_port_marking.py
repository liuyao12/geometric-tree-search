#!/usr/bin/env python3
"""Bounded causal GCTS marking over incoming oriented overlap ports."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence

from materials_gcts_irregular_port_atlas import IrregularPortProgram
from materials_gcts_oriented_overlap_ports import PortAtlas

PortKey = tuple[int, int, tuple[int, ...]]
ContextKey = tuple[int, PortKey]


@dataclass(frozen=True)
class PortChoiceSample:
    context: ContextKey
    parent_type: int
    correct_port: PortKey


@dataclass(frozen=True)
class IncomingPortMarking:
    global_counts: Mapping[int, Counter[PortKey]]
    conditional_counts: Mapping[ContextKey, Counter[PortKey]]
    training_samples: int
    admitted_contexts: int
    minimum_context_support: int
    maximum_incoming_per_node: int
    maximum_outgoing_per_node: int


@dataclass(frozen=True)
class MarkingWork:
    scored_choices: int
    contexts_seen: int
    proposal_checks: int
    failed_checks: int


def _port_key(relation) -> PortKey:
    return relation[2], relation[3], relation[4]


def choice_samples(
    atlas: PortAtlas, occurrence_types: Mapping[int, int], *,
    admitted_ports: frozenset[PortKey] | None = None,
    maximum_incoming_per_node: int = 4,
    maximum_outgoing_per_node: int = 16,
) -> tuple[PortChoiceSample, ...]:
    """Extract causal length-two paths: placed incoming edge -> next edge."""
    if maximum_incoming_per_node < 1 or maximum_outgoing_per_node < 1:
        raise ValueError("bounded node degrees must be positive")
    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    for relation in atlas.relation_classes:
        parent, child = relation[:2]
        key = _port_key(relation)
        if admitted_ports is not None and key not in admitted_ports:
            continue
        outgoing[parent].append((child, key))
        incoming[child].append((parent, key))
    samples = []
    for middle in sorted(set(incoming).intersection(outgoing)):
        if middle not in occurrence_types:
            continue
        left_edges = sorted(set(incoming[middle]), key=repr)[
            :maximum_incoming_per_node]
        right_edges = sorted(set(outgoing[middle]), key=repr)[
            :maximum_outgoing_per_node]
        for prior, incoming_key in left_edges:
            context = (occurrence_types[middle], incoming_key)
            for following, outgoing_key in right_edges:
                if following == prior:
                    continue
                samples.append(PortChoiceSample(
                    context, occurrence_types[middle], outgoing_key))
    return tuple(samples)


def fit_incoming_port_marking(
    program: IrregularPortProgram, *, minimum_context_support: int = 3,
    maximum_incoming_per_node: int = 4,
    maximum_outgoing_per_node: int = 16,
) -> IncomingPortMarking:
    if minimum_context_support < 1:
        raise ValueError("minimum_context_support must be positive")
    admitted = frozenset((port.parent_type, port.child_type,
                          port.symmetry_orbit_key)
                         for port in program.atlas.ports)
    occurrence_types = {occurrence.occurrence_id: occurrence.type_id
                        for occurrence in program.occurrences}
    samples = choice_samples(
        program.atlas, occurrence_types, admitted_ports=admitted,
        maximum_incoming_per_node=maximum_incoming_per_node,
        maximum_outgoing_per_node=maximum_outgoing_per_node)
    global_counts: dict[int, Counter[PortKey]] = defaultdict(Counter)
    raw_conditional: dict[ContextKey, Counter[PortKey]] = defaultdict(Counter)
    context_support = Counter(sample.context for sample in samples)
    for sample in samples:
        global_counts[sample.parent_type][sample.correct_port] += 1
        raw_conditional[sample.context][sample.correct_port] += 1
    conditional = {
        context: counts for context, counts in raw_conditional.items()
        if context_support[context] >= minimum_context_support}
    return IncomingPortMarking(
        dict(global_counts), conditional, len(samples), len(conditional),
        minimum_context_support, maximum_incoming_per_node,
        maximum_outgoing_per_node)


def _rank(correct: PortKey, candidates: Sequence[PortKey],
          primary: Counter[PortKey], fallback: Counter[PortKey]) -> int:
    ordered = sorted(candidates, key=lambda key: (
        -primary[key], -fallback[key], repr(key)))
    try:
        return ordered.index(correct) + 1
    except ValueError:
        return 0


def score_marking(
    marking: IncomingPortMarking, samples: Sequence[PortChoiceSample], *,
    use_context: bool,
) -> MarkingWork:
    checks = failures = scored = seen = 0
    candidates_by_type = {
        parent_type: tuple(counts)
        for parent_type, counts in marking.global_counts.items()}
    for sample in samples:
        candidates = candidates_by_type.get(sample.parent_type, ())
        if sample.correct_port not in candidates:
            continue
        conditional = (marking.conditional_counts.get(sample.context, Counter())
                       if use_context else Counter())
        rank = _rank(sample.correct_port, candidates, conditional,
                     marking.global_counts[sample.parent_type])
        if not rank:
            continue
        scored += 1
        seen += sample.context in marking.conditional_counts
        checks += rank
        failures += rank - 1
    return MarkingWork(scored, seen, checks, failures)


def shuffled_markings(
    marking: IncomingPortMarking,
    training_samples: Sequence[PortChoiceSample], count: int = 20,
    seed: int = 20260815,
) -> tuple[IncomingPortMarking, ...]:
    """Refit after within-parent label shuffles, preserving class marginals."""
    results = []
    by_type = defaultdict(list)
    for sample in training_samples:
        by_type[sample.parent_type].append(sample)
    for shuffle_index in range(count):
        rng = random.Random(seed + shuffle_index)
        shuffled = []
        for parent_type in sorted(by_type):
            group = by_type[parent_type]
            labels = [sample.correct_port for sample in group]
            rng.shuffle(labels)
            shuffled.extend(PortChoiceSample(
                sample.context, sample.parent_type, label)
                for sample, label in zip(group, labels))
        raw = defaultdict(Counter)
        support = Counter(sample.context for sample in shuffled)
        for sample in shuffled:
            raw[sample.context][sample.correct_port] += 1
        conditional = {context: counts for context, counts in raw.items()
                       if support[context] >= marking.minimum_context_support}
        results.append(IncomingPortMarking(
            marking.global_counts, conditional, len(shuffled),
            len(conditional), marking.minimum_context_support,
            marking.maximum_incoming_per_node,
            marking.maximum_outgoing_per_node))
    return tuple(results)
