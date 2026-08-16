#!/usr/bin/env python3
"""Target-free causal GCTS ranking for frozen partial macro completions."""

from __future__ import annotations

import hashlib
import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence


PortSemantic = tuple[str, tuple[str, ...], int, int]


@dataclass(frozen=True)
class CompletionMarkDescriptor:
    anchor_incoming_ports: tuple[PortSemantic, ...]
    alternative_boundary_slots: tuple[
        tuple[str, PortSemantic, int, int], ...]
    matched_witnesses: int
    training_port_evidence: int
    live_overlap_support: int
    live_collision_support: int


@dataclass(frozen=True)
class FrozenCompletionCandidate:
    candidate_id: str
    macro_id: int
    frozen_parent_type: int | None
    descriptor: CompletionMarkDescriptor
    stable_key: tuple


@dataclass(frozen=True)
class CompletionMarkTrace:
    descriptor: CompletionMarkDescriptor
    successful: bool
    learned_from_training_only: bool = True
    shuffle_stratum: Hashable = None


@dataclass(frozen=True)
class FrozenCompletionMarking:
    scores: tuple[tuple[CompletionMarkDescriptor, float], ...]
    marginal_score: float
    training_samples: int
    target_used: bool


@dataclass(frozen=True)
class RankedCompletion:
    candidate: FrozenCompletionCandidate
    marking_score: float
    rank: int


@dataclass(frozen=True)
class CompletionRanking:
    candidate_digest: str
    ranked: tuple[RankedCompletion, ...]
    candidates_unchanged: bool
    target_used: bool


def _rotation_angle(rotation):
    cosine = max(-1., min(1., (sum(rotation[i][i] for i in range(3)) - 1.) / 2.))
    return math.acos(cosine) / math.pi


def _port_lookup(program, length_scale, pose_bin):
    result = {}
    for kind, ports in (("overlap", getattr(program.atlas, "ports", ())),
                        ("boundary", getattr(program, "boundary_ports", ()))):
        for port in ports:
            semantic = (
                kind,
                tuple(sorted(map(repr, getattr(port, "overlap_species", ())))),
                round(math.sqrt(sum(value * value for value in
                                    port.relative_translation)) /
                      length_scale / pose_bin),
                round(_rotation_angle(port.relative_rotation) / pose_bin))
            result[(port.parent_type, port.child_type,
                    port.symmetry_orbit_key)] = (
                        semantic,
                        getattr(port, "observations",
                                getattr(port, "occurrence_observations", 0)))
    return result


def _candidate_id(completion, tolerance):
    missing = tuple(sorted((child.type_id, tuple(sorted(
        (repr(species),) + tuple(round(value / tolerance) for value in point)
        for species, point in child.sites)))
                           for child in completion.missing_children))
    pose = (tuple(round(value / tolerance)
                  for row in completion.macro_rotation for value in row),
            tuple(round(value / tolerance)
                  for value in completion.macro_translation))
    return hashlib.sha256(repr((completion.macro_id,
                                completion.frozen_parent_type,
                                pose, missing)).encode()).hexdigest()


def freeze_completion_candidate(
    lower_program, macro, completion, *,
    live_overlap_support: int = 0, live_collision_support: int = 0,
    maximum_anchor_ports: int = 2, pose_bin: float = .2,
    pose_tolerance: float = .03,
) -> FrozenCompletionCandidate:
    """Compile an immutable local descriptor without target/future atoms."""
    if (getattr(lower_program, "target_used", False) or
            getattr(completion, "target_used", False)):
        raise ValueError("completion marking requires target-free inputs")
    if (maximum_anchor_ports < 0 or maximum_anchor_ports > 2 or
            pose_bin <= 0 or pose_tolerance <= 0 or
            min(live_overlap_support, live_collision_support) < 0):
        raise ValueError("invalid completion descriptor controls")
    scale = getattr(lower_program, "minimum_distance", 0.)
    if scale <= 0 or not math.isfinite(scale):
        raise ValueError("lower program needs a positive frozen length scale")
    lookup = _port_lookup(lower_program, scale, pose_bin)
    matched = frozenset(completion.matched_occurrence_ids)
    incoming = []
    evidence = 0
    atlas_relations = tuple(getattr(
        getattr(lower_program, "atlas", None), "relation_classes", ()))
    boundary_relations = tuple((
        item.parent_occurrence, item.child_occurrence,
        item.parent_type, item.child_type, item.symmetry_orbit_key)
        for item in getattr(lower_program, "boundary_relation_classes", ()))
    for parent, child, parent_type, child_type, key in (
            atlas_relations + boundary_relations):
        if child in matched and parent not in matched:
            resolved = lookup.get((parent_type, child_type, key))
            if resolved is not None:
                incoming.append(resolved[0])
                evidence += resolved[1]
    incoming = tuple(sorted(set(incoming), key=repr))[:maximum_anchor_ports]
    slots = []
    for slot in getattr(macro, "boundary_slots", ()):
        resolved = lookup.get(tuple(slot.port))
        if resolved is None:
            continue
        semantic, observations = resolved
        evidence += observations + slot.occurrence_support
        slots.append((slot.direction, semantic,
                      round(slot.frequency * 10), slot.occurrence_support))
    slots = tuple(sorted(slots, key=repr))
    descriptor = CompletionMarkDescriptor(
        incoming, slots, len(matched), evidence,
        live_overlap_support, live_collision_support)
    candidate_id = _candidate_id(completion, pose_tolerance)
    stable = (live_collision_support, -live_overlap_support,
              -len(matched), completion.macro_id, candidate_id)
    return FrozenCompletionCandidate(
        candidate_id, completion.macro_id, completion.frozen_parent_type,
        descriptor, stable)


def fit_completion_marking(
    traces: Sequence[CompletionMarkTrace],
) -> FrozenCompletionMarking:
    if not traces or any(not item.learned_from_training_only for item in traces):
        raise ValueError("completion marking requires train-only samples")
    counts = {}
    total = Counter()
    for trace in traces:
        counts.setdefault(trace.descriptor, Counter())[trace.successful] += 1
        total[trace.successful] += 1
    # Beta(1,1) posterior mean; deterministic, bounded, and finite.
    scores = tuple(sorted((
        (descriptor, (values[True] + 1) / (sum(values.values()) + 2))
        for descriptor, values in counts.items()), key=repr))
    marginal = (total[True] + 1) / (sum(total.values()) + 2)
    return FrozenCompletionMarking(scores, marginal, len(traces), False)


def shuffle_completion_marking(
    marking: FrozenCompletionMarking, seed: int,
) -> FrozenCompletionMarking:
    values = [score for _descriptor, score in marking.scores]
    random.Random(seed).shuffle(values)
    return FrozenCompletionMarking(
        tuple((item[0], value)
              for item, value in zip(marking.scores, values)),
        marking.marginal_score, marking.training_samples, False)


def shuffle_completion_traces_within_strata(
    traces: Sequence[CompletionMarkTrace], seed: int,
) -> tuple[CompletionMarkTrace, ...]:
    """Permute labels within predeclared parent/context strata only."""
    traces = tuple(traces)
    groups = {}
    for index, trace in enumerate(traces):
        if not trace.learned_from_training_only:
            raise ValueError("cannot shuffle a target-tainted trace")
        groups.setdefault(trace.shuffle_stratum, []).append(index)
    labels = [item.successful for item in traces]
    generator = random.Random(seed)
    for indices in groups.values():
        shuffled = [labels[index] for index in indices]
        generator.shuffle(shuffled)
        for index, label in zip(indices, shuffled):
            labels[index] = label
    return tuple(CompletionMarkTrace(
        trace.descriptor, labels[index], True, trace.shuffle_stratum)
                 for index, trace in enumerate(traces))


def rank_completion_candidates(
    candidates: Sequence[FrozenCompletionCandidate],
    marking: FrozenCompletionMarking | None,
) -> CompletionRanking:
    candidates = tuple(candidates)
    if len({item.candidate_id for item in candidates}) != len(candidates):
        raise ValueError("frozen completion candidate IDs must be unique")
    if marking is not None and marking.target_used:
        raise ValueError("target-tainted completion marking is forbidden")
    digest = hashlib.sha256(repr(tuple(sorted(
        item.candidate_id for item in candidates))).encode()).hexdigest()
    score_by_descriptor = {} if marking is None else dict(marking.scores)
    marginal = 0. if marking is None else marking.marginal_score
    ordered = sorted(candidates, key=lambda item: (
        -score_by_descriptor.get(item.descriptor, marginal), item.stable_key))
    ranked = tuple(RankedCompletion(
        item, score_by_descriptor.get(item.descriptor, marginal), index + 1)
                   for index, item in enumerate(ordered))
    return CompletionRanking(
        digest, ranked,
        {item.candidate_id for item in candidates} ==
        {item.candidate.candidate_id for item in ranked}, False)
