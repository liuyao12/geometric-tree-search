#!/usr/bin/env python3
"""Bounded, local GCTS markings over finite oriented overlap ports.

This layer never proposes an attachment.  It receives a frozen candidate list
from the oriented-port atlas and only changes its order.  Consequently marked,
unmarked, and shuffled-control searches perform work over byte-for-byte equal
actions.  Marking inputs are bounded multisets of incoming *local* port
geometry: overlap cardinality, relative translation length normalized by the
parent support size, and proper-rotation angle.  Material names, global axes,
absolute positions, and target outcomes are absent.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from typing import Hashable, Mapping, Sequence

from materials_gcts_irregular_port_atlas import (
    FrozenPortEnumeration, IrregularPortProgram)
from materials_gcts_oriented_overlap_ports import (
    canonical_relative_pose, matmul, matvec, transpose)

SpeciesHistogram = tuple[tuple[str, int], ...]
PrototypeToken = tuple[int, SpeciesHistogram]
GeometryToken = tuple[PrototypeToken, SpeciesHistogram, int, int, int]
ContextKey = tuple[PrototypeToken, tuple[GeometryToken, ...]]
StaticActionToken = tuple[PrototypeToken, SpeciesHistogram, int, int, int]
ActionFeature = tuple[StaticActionToken, tuple[int, ...]]


@dataclass(frozen=True)
class PortDecision:
    occurrence_id: int
    center_type: int
    center_prototype: PrototypeToken
    context: tuple[GeometryToken, ...]
    candidates: tuple[int, ...]
    candidate_features: tuple[ActionFeature, ...]
    chosen_action: int


@dataclass(frozen=True)
class BoundedPortMarking:
    exact_counts: Mapping[ContextKey, Counter[ActionFeature]]
    backoff_counts: Mapping[
        tuple[PrototypeToken, GeometryToken], Counter[ActionFeature]]
    marginal_counts: Mapping[PrototypeToken, Counter[StaticActionToken]]
    maximum_incoming_ports: int
    maximum_exact_states: int
    maximum_backoff_states: int
    minimum_state_support: int
    training_examples: int
    raw_contexts: int


@dataclass(frozen=True)
class RankingWork:
    examples: int
    candidate_actions: int
    mean_checks: float
    median_checks: float
    top_one_accuracy: float
    exact_context_coverage: float
    backoff_context_coverage: float
    candidate_digest: str


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _rotation_angle(rotation: Sequence[Sequence[float]]) -> float:
    cosine = max(-1.0, min(1.0, (
        rotation[0][0] + rotation[1][1] + rotation[2][2] - 1.0) / 2.0))
    return math.acos(cosine)


def _prototype_scale(program: IrregularPortProgram, type_id: int) -> float:
    prototype = next(item for item in program.prototypes
                     if item.type_id == type_id)
    squared = [sum(value * value for value in point)
               for _, point in prototype.sites]
    return max(math.sqrt(sum(squared) / len(squared)), 1e-12)


def _histogram(values: Sequence[Hashable]) -> SpeciesHistogram:
    counts = Counter(repr(value) for value in values)
    return tuple(sorted(counts.items()))


def _prototype_token(
    program: IrregularPortProgram, type_id: int,
) -> PrototypeToken:
    prototype = next(item for item in program.prototypes
                     if item.type_id == type_id)
    return len(prototype.sites), _histogram(
        tuple(species for species, _ in prototype.sites))


def _geometry_token(program: IrregularPortProgram, port_index: int) -> GeometryToken:
    port = program.atlas.ports[port_index]
    normalized_distance = (_norm(port.relative_translation) /
                           _prototype_scale(program, port.parent_type))
    return (
        _prototype_token(program, port.parent_type),
        _histogram(port.overlap_species),
        min(len(port.overlap), 7),
        min(int(normalized_distance / .25), 15),
        min(int(_rotation_angle(port.relative_rotation) / (math.pi / 12)), 11),
    )


def _static_action_token(
    program: IrregularPortProgram, port_index: int,
) -> StaticActionToken:
    port = program.atlas.ports[port_index]
    geometry = _geometry_token(program, port_index)
    return (_prototype_token(program, port.child_type),) + geometry[1:]


def _unit(vector: Sequence[float]) -> tuple[float, float, float] | None:
    length = _norm(vector)
    if length <= 1e-12:
        return None
    return tuple(value / length for value in vector)  # type: ignore[return-value]


def _angular_relation_bin(
    program: IrregularPortProgram, incoming_port: int, outgoing_port: int,
) -> int:
    """Angle in the shared center-cluster canonical frame, with no world axis."""
    incoming = program.atlas.ports[incoming_port]
    outgoing = program.atlas.ports[outgoing_port]
    inverse = transpose(incoming.relative_rotation)
    inward = _unit(tuple(-value for value in matvec(
        inverse, incoming.relative_translation)))
    outward = _unit(outgoing.relative_translation)
    if inward is None or outward is None:
        return 6
    cosine = sum(a*b for a, b in zip(inward, outward))
    angle = math.acos(max(-1.0, min(1.0, cosine)))
    return min(int(angle / (math.pi / 12)), 6)


def build_port_decisions(
    program: IrregularPortProgram, *, maximum_incoming_ports: int = 2,
) -> tuple[PortDecision, ...]:
    """Convert witnessed relations to local-context ranking examples."""
    if maximum_incoming_ports < 1:
        raise ValueError("maximum_incoming_ports must be positive")
    port_by_key = {
        (port.parent_type, port.child_type, port.symmetry_orbit_key): index
        for index, port in enumerate(program.atlas.ports)}
    incoming: dict[int, list[int]] = defaultdict(list)
    outgoing: dict[int, list[int]] = defaultdict(list)
    occurrence_type = {item.occurrence_id: item.type_id
                       for item in program.occurrences}
    for parent, child, parent_type, child_type, pose_key in (
            program.atlas.relation_classes):
        port_index = port_by_key.get((parent_type, child_type, pose_key))
        if port_index is None:
            continue
        incoming[child].append(port_index)
        outgoing[parent].append(port_index)
    candidates_by_type: dict[int, tuple[int, ...]] = {}
    for index, port in enumerate(program.atlas.ports):
        candidates_by_type.setdefault(port.parent_type, tuple())
        candidates_by_type[port.parent_type] += (index,)
    static_tokens = tuple(_static_action_token(program, index)
                          for index in range(len(program.atlas.ports)))
    angle_cache: dict[tuple[int, int], int] = {}
    decisions = []
    for occurrence_id in sorted(outgoing):
        center_type = occurrence_type[occurrence_id]
        selected_incoming = tuple(sorted(
            ((_geometry_token(program, port_index), port_index)
             for port_index in incoming.get(occurrence_id, ())))[
                 :maximum_incoming_ports])
        context = tuple(item[0] for item in selected_incoming)
        candidates = candidates_by_type[center_type]
        features = []
        for candidate in candidates:
            angles = []
            for _, incoming_port in selected_incoming:
                pair = incoming_port, candidate
                if pair not in angle_cache:
                    angle_cache[pair] = _angular_relation_bin(
                        program, incoming_port, candidate)
                angles.append(angle_cache[pair])
            features.append((static_tokens[candidate], tuple(angles)))
        for chosen in sorted(outgoing[occurrence_id]):
            decisions.append(PortDecision(
                occurrence_id, center_type,
                _prototype_token(program, center_type), context, candidates,
                tuple(features), chosen))
    return tuple(decisions)


def build_frozen_target_decisions(
    program: IrregularPortProgram, enumeration: FrozenPortEnumeration,
    *, maximum_incoming_ports: int = 2, pose_tolerance: float = .03,
) -> tuple[PortDecision, ...]:
    """Match target occurrence relations to train-frozen port keys only.

    No target port is learned. Candidate pairs arise solely from witnessed
    shared target atoms, and a pair becomes a relation only when its canonical
    relative pose is already present in the training atlas.
    """
    occurrence_by_id = {item.occurrence_id: item
                        for item in enumeration.occurrences}
    prototype_by_type = {item.type_id: item for item in program.prototypes}
    support_by_id = dict(enumeration.occurrence_supports)
    containing: dict[int, list[int]] = defaultdict(list)
    for occurrence_id, support in support_by_id.items():
        for atom in support:
            containing[atom].append(occurrence_id)
    shared: Counter[tuple[int, int]] = Counter()
    for occurrence_ids in containing.values():
        for left in occurrence_ids:
            for right in occurrence_ids:
                if left != right:
                    shared[(left, right)] += 1
    frozen_keys = {
        (port.parent_type, port.child_type, port.symmetry_orbit_key)
        for port in program.atlas.ports}
    relations = []
    for (parent_id, child_id), overlap in sorted(shared.items()):
        if overlap < program.minimum_shared_atoms:
            continue
        parent = occurrence_by_id[parent_id]
        child = occurrence_by_id[child_id]
        inverse = transpose(parent.rotation)
        relative_rotation = matmul(inverse, child.rotation)
        delta = tuple(child.translation[axis] - parent.translation[axis]
                      for axis in range(3))
        relative_translation = matvec(inverse, delta)
        try:
            _, _, pose_key = canonical_relative_pose(
                prototype_by_type[parent.type_id],
                prototype_by_type[child.type_id], relative_rotation,
                relative_translation, pose_tolerance)
        except ValueError:
            continue
        key = parent.type_id, child.type_id, pose_key
        if key in frozen_keys:
            relations.append((parent_id, child_id, parent.type_id,
                              child.type_id, pose_key))
    frozen_atlas = replace(
        program.atlas, relation_classes=tuple(relations),
        witnessed_relations=len(relations))
    target_program = replace(
        program, atlas=frozen_atlas,
        occurrences=enumeration.occurrences,
        occurrence_supports=enumeration.occurrence_supports)
    return build_port_decisions(
        target_program, maximum_incoming_ports=maximum_incoming_ports)


def split_decisions(
    decisions: Sequence[PortDecision], *, heldout_modulus: int = 5,
) -> tuple[tuple[PortDecision, ...], tuple[PortDecision, ...]]:
    """Modulo diagnostic only; scientific evaluation uses frozen targets."""
    if heldout_modulus < 2:
        raise ValueError("heldout_modulus must be at least two")
    training = tuple(item for item in decisions
                     if item.occurrence_id % heldout_modulus != 0)
    heldout = tuple(item for item in decisions
                    if item.occurrence_id % heldout_modulus == 0)
    return training, heldout


def shuffle_training_contexts(
    decisions: Sequence[PortDecision], *, seed: int = 1729,
) -> tuple[PortDecision, ...]:
    """Shuffle labels within identical action sets, preserving every input."""
    # A proper prototype type fixes its exact candidate tuple.  Grouping by
    # the small type id preserves that tuple without repeatedly hashing the
    # thousands-long candidate list (11k+ ports in the Cd--Yb seed).
    grouped: dict[int, list[int]] = defaultdict(list)
    for index, decision in enumerate(decisions):
        grouped[decision.center_type].append(index)
    result = list(decisions)
    rng = random.Random(seed)
    for indices in grouped.values():
        labels = [decisions[index].chosen_action for index in indices]
        rng.shuffle(labels)
        if len(labels) > 1 and all(
                label == decisions[index].chosen_action
                for index, label in zip(indices, labels)):
            labels = labels[1:] + labels[:1]
        for index, label in zip(indices, labels):
            decision = decisions[index]
            result[index] = PortDecision(
                decision.occurrence_id, decision.center_type,
                decision.center_prototype, decision.context,
                decision.candidates, decision.candidate_features, label)
    return tuple(result)


def fit_bounded_port_marking(
    decisions: Sequence[PortDecision], *,
    maximum_incoming_ports: int = 2, maximum_exact_states: int = 32,
    maximum_backoff_states: int = 64, minimum_state_support: int = 32,
) -> BoundedPortMarking:
    """Fit finite exact-context and one-port backoff tables on training only."""
    if maximum_exact_states < 0 or maximum_backoff_states < 0:
        raise ValueError("state bounds must be nonnegative")
    if minimum_state_support < 1:
        raise ValueError("minimum_state_support must be positive")
    exact_all: dict[ContextKey, Counter[ActionFeature]] = defaultdict(Counter)
    backoff_all: dict[
        tuple[PrototypeToken, GeometryToken], Counter[ActionFeature]
    ] = defaultdict(Counter)
    marginal: dict[PrototypeToken, Counter[StaticActionToken]] = defaultdict(Counter)
    candidate_indices: dict[int, dict[int, int]] = {}
    for decision in decisions:
        if len(decision.context) > maximum_incoming_ports:
            raise ValueError("decision exceeds the marking domain bound")
        if decision.center_type not in candidate_indices:
            candidate_indices[decision.center_type] = {
                action: index for index, action in enumerate(
                    decision.candidates)}
        chosen_index = candidate_indices[decision.center_type][
            decision.chosen_action]
        action = decision.candidate_features[chosen_index]
        key = (decision.center_prototype, decision.context)
        exact_all[key][action] += 1
        marginal[decision.center_prototype][action[0]] += 1
        for token in set(decision.context):
            backoff_all[(decision.center_prototype, token)][action] += 1
    exact_keys = sorted(
        (key for key, counts in exact_all.items()
         if sum(counts.values()) >= minimum_state_support),
        key=lambda key: (-sum(exact_all[key].values()), key))[:maximum_exact_states]
    backoff_keys = sorted(
        (key for key, counts in backoff_all.items()
         if sum(counts.values()) >= minimum_state_support),
        key=lambda key: (-sum(backoff_all[key].values()), key))[:maximum_backoff_states]
    return BoundedPortMarking(
        {key: exact_all[key] for key in exact_keys},
        {key: backoff_all[key] for key in backoff_keys}, dict(marginal),
        maximum_incoming_ports, maximum_exact_states,
        maximum_backoff_states, minimum_state_support,
        len(decisions), len(exact_all))


def _scores(
    marking: BoundedPortMarking, decision: PortDecision, arm: str,
) -> dict[int, int]:
    if arm not in {"marked", "unmarked"}:
        raise ValueError("arm must be marked or unmarked")
    counts: Counter
    use_static = arm == "unmarked"
    if arm == "unmarked":
        counts = marking.marginal_counts.get(decision.center_prototype, Counter())
    else:
        exact = marking.exact_counts.get(
            (decision.center_prototype, decision.context))
        if exact is not None:
            counts = exact
        else:
            counts = Counter()
            for token in set(decision.context):
                counts.update(marking.backoff_counts.get(
                    (decision.center_prototype, token), Counter()))
            if not counts:
                counts = marking.marginal_counts.get(
                    decision.center_prototype, Counter())
                use_static = True
    if use_static:
        return {candidate: counts[feature[0]] for candidate, feature in zip(
            decision.candidates, decision.candidate_features)}
    return {candidate: counts[feature] for candidate, feature in zip(
        decision.candidates, decision.candidate_features)}


def evaluate_ranking_work(
    marking: BoundedPortMarking, decisions: Sequence[PortDecision], *,
    arm: str,
) -> RankingWork:
    """Count candidate checks until the witnessed action is reached."""
    ranks = []
    exact_seen = backoff_seen = 0
    digest = hashlib.sha256()
    digested_types = set()
    for decision in decisions:
        digest.update(f"{decision.center_type};".encode())
        if decision.center_type not in digested_types:
            digest.update(repr(decision.candidates).encode())
            digested_types.add(decision.center_type)
        # Count the rank directly instead of sorting a potentially 11k-action
        # Cd--Yb list. Candidate features depend on the concrete incoming
        # orientation, so caching only by abstract context would be invalid.
        scores = _scores(marking, decision, arm)
        chosen_score = scores[decision.chosen_action]
        ranks.append(1 + sum(
            score > chosen_score or
            (score == chosen_score and candidate < decision.chosen_action)
            for candidate, score in scores.items()))
        exact = ((decision.center_prototype, decision.context) in
                 marking.exact_counts)
        exact_seen += exact
        backoff_seen += exact or any(
            (decision.center_prototype, token) in marking.backoff_counts
            for token in decision.context)
    ordered_ranks = sorted(ranks)
    count = len(ranks)
    median = (ordered_ranks[count // 2] if count % 2 else
              (ordered_ranks[count // 2 - 1] + ordered_ranks[count // 2]) / 2)
    return RankingWork(
        count, sum(len(item.candidates) for item in decisions),
        sum(ranks) / count, median, sum(rank == 1 for rank in ranks) / count,
        exact_seen / count, backoff_seen / count, digest.hexdigest())
