#!/usr/bin/env python3
"""Bounded causal incoming-port marking for dense macro growth.

Contexts contain at most two already placed incoming frozen production ports.
They are local proper-pose orbit classes: no world coordinate, direction,
radius, target, cell, or material label is represented.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import random
from typing import Mapping, Sequence

from materials_gcts_macro_derivation import _compile_productions


@dataclass(frozen=True)
class ConnectionTrace:
    center_occurrence: int
    parent_type: int
    incoming_ports: tuple[int, ...]
    chosen_outgoing_port: int
    occurrence_domain: tuple[int, ...]


@dataclass(frozen=True)
class CausalConnectionMarking:
    exact: Mapping[tuple[int, tuple[int, ...]], Counter[int]]
    order_one: Mapping[tuple[int, int], Counter[int]]
    marginal: Mapping[int, Counter[int]]
    maximum_interaction_order: int
    training_traces: int
    guarded_validation_traces: int
    guarded_domains_disjoint: bool


def connection_traces(program, *, maximum_interaction_order: int = 2):
    if maximum_interaction_order not in (1, 2):
        raise ValueError("interaction order must be one or two")
    productions = _compile_productions(program)
    production_by_key = {
        (item.parent_type, item.child_type, item.symmetry_orbit_key):
        item.production_id for item in productions}
    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    for parent, child, parent_type, child_type, key in (
            program.atlas.relation_classes):
        production = production_by_key[(parent_type, child_type, key)]
        incoming[child].append((production, parent))
        outgoing[parent].append((production, child))
    occurrence_type = {item.occurrence_id: item.type_id
                       for item in program.occurrences}
    traces = []
    for center in sorted(outgoing):
        selected = tuple(sorted(incoming.get(center, ()))
                         [:maximum_interaction_order])
        context = tuple(item[0] for item in selected)
        incoming_nodes = tuple(item[1] for item in selected)
        for action, child in sorted(outgoing[center]):
            traces.append(ConnectionTrace(
                center, occurrence_type[center], context, action,
                tuple(sorted({center, child, *incoming_nodes}))))
    return tuple(traces)


def guarded_trace_split(traces: Sequence[ConnectionTrace], *,
                        validation_traces: int = 31):
    """Choose validation traces, then exclude their occurrence domains.

    This is stronger than an occurrence-id modulo split: no occurrence used by
    a held-out center/incoming/outgoing trace can occur in a fitted trace.
    """
    if validation_traces < 1:
        raise ValueError("validation_traces must be positive")
    stride = max(1, len(traces) // validation_traces)
    validation = tuple(traces[index] for index in
                       range(stride // 2, len(traces), stride)
                       )[:validation_traces]
    forbidden = {occurrence for trace in validation
                 for occurrence in trace.occurrence_domain}
    training = tuple(trace for trace in traces
                     if forbidden.isdisjoint(trace.occurrence_domain))
    if not training or not validation:
        raise ValueError("guarded split starved a trace partition")
    train_domain = {occurrence for trace in training
                    for occurrence in trace.occurrence_domain}
    assert train_domain.isdisjoint(forbidden)
    return training, validation


def shuffle_trace_labels(traces: Sequence[ConnectionTrace], *, seed: int):
    grouped = defaultdict(list)
    for index, trace in enumerate(traces):
        grouped[trace.parent_type].append(index)
    result = list(traces)
    rng = random.Random(seed)
    for indices in grouped.values():
        labels = [traces[index].chosen_outgoing_port for index in indices]
        rng.shuffle(labels)
        for index, label in zip(indices, labels):
            trace = traces[index]
            result[index] = ConnectionTrace(
                trace.center_occurrence, trace.parent_type,
                trace.incoming_ports, label, trace.occurrence_domain)
    return tuple(result)


def fit_causal_connection_marking(
        training: Sequence[ConnectionTrace], *, validation_count: int = 0,
        guarded_domains_disjoint: bool = False,
) -> CausalConnectionMarking:
    exact = defaultdict(Counter)
    order_one = defaultdict(Counter)
    marginal = defaultdict(Counter)
    maximum_order = 0
    for trace in training:
        maximum_order = max(maximum_order, len(trace.incoming_ports))
        exact[(trace.parent_type, trace.incoming_ports)][
            trace.chosen_outgoing_port] += 1
        for incoming in trace.incoming_ports:
            order_one[(trace.parent_type, incoming)][
                trace.chosen_outgoing_port] += 1
        marginal[trace.parent_type][trace.chosen_outgoing_port] += 1
    return CausalConnectionMarking(
        dict(exact), dict(order_one), dict(marginal), maximum_order,
        len(training), validation_count, guarded_domains_disjoint)


def rank_key(marking: CausalConnectionMarking, parent_type: int,
             incoming_ports: tuple[int, ...], action: int,
             overlap: int, emitted: int, parent_node: int):
    exact = marking.exact.get((parent_type, incoming_ports), Counter())[action]
    backoff = sum(marking.order_one.get(
        (parent_type, incoming), Counter())[action]
                  for incoming in incoming_ports)
    marginal = marking.marginal.get(parent_type, Counter())[action]
    return (-exact, -backoff, -marginal, -overlap, -emitted,
            action, parent_node)
