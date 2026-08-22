#!/usr/bin/env python3
"""Finite recurrent state quotient for invariant GCTS pose-port evidence.

The exact candidate geometry remains outside this model.  The quotient pools
train-fitted token evidence into five fixed connection channels and quantizes
their normalized responses.  A recurrent state is therefore independent of
candidate IDs, absolute coordinates, the global frame, and raw orientation
orbit cardinality.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, FrozenIncidenceTokenMarking,
    IncidenceTokenExample, fit_incidence_token_marking)


DEFAULT_POSE_PORT_CHANNELS = (
    ("coarse-role", "role", "role-support", "same-site-role-pair"),
    ("parent-multiplicity", "port-axis-multiplicity", "vote"),
    ("occupied-count", "occupied-shell", "occupied-shell-colorless",
     "role-occupied-shell"),
    ("neighbor-colors", "neighbor-role", "occupied-metric-edge",
     "role-occupied-metric-edge"),
    ("port-axis-angle", "port-axis-handedness", "port-neighbor-angle",
     "role-port-neighbor-angle"),
)


@dataclass(frozen=True)
class PosePortStateEvidence:
    positive: int
    total: int
    independent_groups: int


@dataclass(frozen=True)
class FrozenPosePortStateMarking:
    token_marking: FrozenIncidenceTokenMarking
    channel_families: tuple[tuple[str, ...], ...]
    state_bin_width: float
    state_probabilities: Mapping[tuple[int, ...], float]
    state_evidence: Mapping[tuple[int, ...], PosePortStateEvidence]
    prior_probability: float
    minimum_state_support: int
    minimum_state_groups: int
    smoothing: float


def _family(token: Hashable) -> Hashable:
    return token[0] if isinstance(token, tuple) and token else token


def pose_port_state_code(
        token_marking: FrozenIncidenceTokenMarking,
        descriptor: CandidateIncidenceDescriptor, *,
        state_bin_width: float,
        channel_families: Sequence[Sequence[str]] =
        DEFAULT_POSE_PORT_CHANNELS) -> tuple[int, ...]:
    """Return the bounded channel-response state for one exact candidate."""
    if state_bin_width <= 0 or not channel_families or any(
            not channel for channel in channel_families):
        raise ValueError("invalid pose-port state schema")
    responses = pose_port_channel_responses(
        token_marking, descriptor, channel_families=channel_families)
    return tuple(round(response / state_bin_width)
                 for response in responses)


def pose_port_channel_responses(
        token_marking: FrozenIncidenceTokenMarking,
        descriptor: CandidateIncidenceDescriptor, *,
        channel_families: Sequence[Sequence[str]] =
        DEFAULT_POSE_PORT_CHANNELS) -> tuple[float, ...]:
    """Return the continuous, train-frozen response of every port channel.

    These values are an ID-free view of the same evidence used by
    :func:`pose_port_state_code`.  Exposing them lets a search allocate a
    fixed candidate budget across distinct connection channels without
    refitting the marking or changing exact candidate geometry.
    """
    if not channel_families or any(not channel for channel in channel_families):
        raise ValueError("invalid pose-port channel schema")
    result = []
    for channel in channel_families:
        admitted = frozenset(channel)
        values = tuple(token_marking.token_weights[token]
                       for token in descriptor.tokens
                       if token in token_marking.token_weights and
                       _family(token) in admitted)
        response = sum(values) / math.sqrt(len(values)) if values else 0.
        result.append(response)
    return tuple(result)


def fit_pose_port_state_marking(
        examples: Sequence[IncidenceTokenExample], *,
        minimum_token_support: int = 4,
        minimum_token_groups: int = 2,
        token_shrinkage: float = .5,
        state_bin_width: float = 1.,
        minimum_state_support: int = 8,
        minimum_state_groups: int = 2,
        smoothing: float = 1.,
        channel_families: Sequence[Sequence[str]] =
        DEFAULT_POSE_PORT_CHANNELS) -> FrozenPosePortStateMarking:
    """Fit token evidence and its finite recurrent state table on train only."""
    if (not examples or state_bin_width <= 0 or minimum_state_support < 1 or
            minimum_state_groups < 1 or smoothing <= 0):
        raise ValueError("invalid pose-port state fit")
    token_marking = fit_incidence_token_marking(
        examples, minimum_support=minimum_token_support,
        minimum_groups=minimum_token_groups, shrinkage=token_shrinkage,
        smoothing=smoothing)
    return fit_pose_port_states_from_token_marking(
        examples, token_marking, state_bin_width=state_bin_width,
        minimum_state_support=minimum_state_support,
        minimum_state_groups=minimum_state_groups, smoothing=smoothing,
        channel_families=channel_families)


def fit_pose_port_states_from_token_marking(
        examples: Sequence[IncidenceTokenExample],
        token_marking: FrozenIncidenceTokenMarking, *,
        state_bin_width: float = 1.,
        minimum_state_support: int = 8,
        minimum_state_groups: int = 2,
        smoothing: float = 1.,
        channel_families: Sequence[Sequence[str]] =
        DEFAULT_POSE_PORT_CHANNELS) -> FrozenPosePortStateMarking:
    """Fit only the recurrent table when token evidence is already frozen."""
    if (not examples or state_bin_width <= 0 or minimum_state_support < 1 or
            minimum_state_groups < 1 or smoothing <= 0):
        raise ValueError("invalid pose-port state fit")
    schema = tuple(tuple(sorted(set(channel)))
                   for channel in channel_families)
    counts = defaultdict(lambda: [0, 0, set()])
    positive = 0
    for row in examples:
        state = pose_port_state_code(
            token_marking, row.descriptor,
            state_bin_width=state_bin_width,
            channel_families=schema)
        counts[state][0] += int(row.successful)
        counts[state][1] += 1
        counts[state][2].add(row.group)
        positive += int(row.successful)
    prior = (positive + smoothing) / (len(examples) + 2 * smoothing)
    evidence = {
        state: PosePortStateEvidence(pos, total, len(groups))
        for state, (pos, total, groups) in counts.items()}
    probabilities = {
        state: (row.positive + smoothing) / (row.total + 2 * smoothing)
        for state, row in evidence.items()
        if row.total >= minimum_state_support and
        row.independent_groups >= minimum_state_groups}
    return FrozenPosePortStateMarking(
        token_marking, schema, state_bin_width, probabilities, evidence,
        prior, minimum_state_support, minimum_state_groups, smoothing)


def score_pose_port_state(
        marking: FrozenPosePortStateMarking,
        descriptor: CandidateIncidenceDescriptor) -> float:
    state = pose_port_state_code(
        marking.token_marking, descriptor,
        state_bin_width=marking.state_bin_width,
        channel_families=marking.channel_families)
    return marking.state_probabilities.get(state, marking.prior_probability)


def select_pose_port_channel_diverse(
        marking: FrozenPosePortStateMarking,
        descriptors: Mapping[Hashable, CandidateIncidenceDescriptor], *,
        budget: int, baseline_slots: int,
        votes: Mapping[Hashable, int] | None = None,
        tie_keys: Mapping[Hashable, object] | None = None,
        ) -> tuple[Hashable, ...]:
    """Allocate one fixed action budget across learned connection channels.

    The exact candidate keys and geometry remain outside the marking.  The
    selector first keeps ``baseline_slots`` leaders under the frozen recurrent
    state probability, then one previously unseen leader from every continuous
    port-channel response, and finally fills any unspent slots from the same
    baseline order.  It therefore changes representation of a fixed budget,
    not the number or geometry of candidates rendered by the caller.
    """
    rows = tuple(descriptors)
    if (not rows or budget < 1 or baseline_slots < 0 or
            baseline_slots > budget or budget > len(rows)):
        raise ValueError("invalid channel-diverse candidate budget")
    votes = {} if votes is None else votes
    if tie_keys is not None and any(key not in tie_keys for key in rows):
        raise ValueError("tie-key mapping must cover every candidate")
    tie = ((lambda key: repr(key)) if tie_keys is None else
           (lambda key: tie_keys[key]))
    scores = {key: score_pose_port_state(marking, descriptors[key])
              for key in rows}
    baseline = tuple(sorted(rows, key=lambda key: (
        -scores[key], -int(votes.get(key, 0)), tie(key))))
    responses = {key: pose_port_channel_responses(
        marking.token_marking, descriptors[key],
        channel_families=marking.channel_families) for key in rows}
    selected = list(baseline[:baseline_slots])
    seen = set(selected)
    for channel in range(len(marking.channel_families)):
        order = sorted(rows, key=lambda key: (
            -responses[key][channel], -scores[key],
            -int(votes.get(key, 0)), tie(key)))
        winner = next((key for key in order if key not in seen), None)
        if winner is not None and len(selected) < budget:
            selected.append(winner)
            seen.add(winner)
    for key in baseline:
        if len(selected) >= budget:
            break
        if key not in seen:
            selected.append(key)
            seen.add(key)
    if len(selected) != budget:
        raise AssertionError("channel-diverse selector underfilled its budget")
    return tuple(selected)


def pose_port_state_marking_digest(
        marking: FrozenPosePortStateMarking) -> str:
    token_rows = tuple(sorted(
        marking.token_marking.token_weights.items(), key=lambda row: repr(row[0])))
    state_rows = tuple(sorted(marking.state_probabilities.items()))
    evidence_rows = tuple(sorted(
        (state, row.positive, row.total, row.independent_groups)
        for state, row in marking.state_evidence.items()))
    payload = (
        marking.channel_families, marking.state_bin_width,
        marking.prior_probability, marking.minimum_state_support,
        marking.minimum_state_groups, marking.smoothing,
        marking.token_marking.minimum_support,
        marking.token_marking.minimum_groups,
        marking.token_marking.shrinkage,
        token_rows, state_rows, evidence_rows)
    return hashlib.sha256(repr(payload).encode()).hexdigest()
