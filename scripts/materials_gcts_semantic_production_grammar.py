#!/usr/bin/env python3
"""Exact execution beneath a coarse semantic recursive type.

A semantic type may own several finite child-cover alternatives.  Grouping is
only a policy abstraction: every alternative retains a canonical exact action
identity, proper-SE(3) child placements, and an exact colored-union inclusion
certificate.  A train-fitted bounded incoming-port marking ranks the fixed
candidate set.  It cannot add, remove, or geometrically modify candidates.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Hashable, Sequence

from materials_gcts_frozen_frontier_replay import (
    Site, _add, _classify_candidate, _site_key)
from materials_gcts_oriented_overlap_ports import (
    ClusterPrototype, IDENTITY, Matrix, Vector, is_proper_rotation,
    matmul, matvec)


@dataclass(frozen=True)
class ExactChildPlacement:
    child_type: int
    rotation: Matrix
    translation: Vector


@dataclass(frozen=True)
class ProductionAlternative:
    semantic_parent_type: Hashable
    exact_action_id: str
    children: tuple[ExactChildPlacement, ...]
    atom_union: tuple[Site, ...]
    outgoing_ports: tuple[Hashable, ...]
    inclusion_certificate_digest: str


@dataclass(frozen=True)
class IncomingPortTrace:
    semantic_parent_type: Hashable
    incoming_ports: tuple[Hashable, ...]
    exact_action_id: str
    learned_from_training_only: bool = True


@dataclass(frozen=True)
class PortMarking:
    maximum_context_order: int
    exact_scores: tuple[tuple[tuple[Hashable, tuple[Hashable, ...]],
                              tuple[tuple[str, int], ...]], ...]
    marginal_scores: tuple[tuple[Hashable, tuple[tuple[str, int], ...]], ...]
    training_samples: int
    target_used: bool


@dataclass(frozen=True)
class SemanticPortGrammar:
    prototypes: tuple[ClusterPrototype, ...]
    alternatives: tuple[ProductionAlternative, ...]
    maximum_context_order: int
    overlap_tolerance: float
    exclusion_distance: float
    target_artifacts_stored: bool


@dataclass(frozen=True)
class ExpansionRequest:
    request_id: int
    semantic_parent_type: Hashable
    rotation: Matrix
    translation: Vector
    incoming_ports: tuple[Hashable, ...]


@dataclass(frozen=True)
class SemanticCandidate:
    request_id: int
    semantic_parent_type: Hashable
    exact_action_id: str
    rotation: Matrix
    translation: Vector
    rendered_sites: tuple[Site, ...]
    alternative_inclusion_certificate_digest: str
    replay_certificate_digest: str


@dataclass(frozen=True)
class AcceptedSemanticAction:
    request_id: int
    exact_action_id: str
    novel_sites: tuple[Site, ...]
    replay_certificate_digest: str


@dataclass(frozen=True)
class SemanticExecutionResult:
    accepted_actions: tuple[AcceptedSemanticAction, ...]
    sites: tuple[Site, ...]
    candidate_sets: tuple[tuple[str, ...], ...]
    attempted_actions: int
    geometric_rejections: int
    downstream_choice_backtracks: int
    exhausted: bool
    target_used: bool

    @property
    def total_backtracks(self) -> int:
        return self.geometric_rejections + self.downstream_choice_backtracks


def _subtract(left: Vector, right: Vector) -> Vector:
    return tuple(left[index] - right[index]
                 for index in range(3))  # type: ignore[return-value]


def _render(prototype, rotation, translation):
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _canonical_union(children, prototypes, tolerance):
    prototype_by_id = {item.type_id: item for item in prototypes}
    unique = {}
    species_at = {}
    for child in children:
        if child.child_type not in prototype_by_id:
            raise ValueError("alternative references an unknown exact child")
        if not is_proper_rotation(child.rotation):
            raise ValueError("alternative child pose must be proper SE(3)")
        for species, point in _render(
                prototype_by_id[child.child_type], child.rotation,
                child.translation):
            coordinate = tuple(round(value / tolerance) for value in point)
            if coordinate in species_at and species_at[coordinate] != species:
                raise ValueError("alternative contains an unlike-colored overlap")
            species_at[coordinate] = species
            unique.setdefault(coordinate, (species, point))
    return tuple(unique[key] for key in sorted(unique))


def make_production_alternative(
        semantic_parent_type: Hashable,
        children: Sequence[ExactChildPlacement],
        prototypes: Sequence[ClusterPrototype], *,
        outgoing_ports: Sequence[Hashable] = (), tolerance: float = 1e-6,
) -> ProductionAlternative:
    """Compile one exact child cover and derive its immutable action ID."""
    if tolerance <= 0 or not children:
        raise ValueError("an alternative needs children and positive tolerance")
    children = tuple(children)
    union = _canonical_union(children, prototypes, tolerance)
    geometry = tuple((child.child_type,
                      tuple(round(value / tolerance)
                            for row in child.rotation for value in row),
                      tuple(round(value / tolerance)
                            for value in child.translation))
                     for child in children)
    union_key = tuple(sorted((_site_key(site, tolerance) for site in union)))
    payload = repr((geometry, union_key,
                    tuple(map(repr, outgoing_ports)))).encode()
    exact_id = hashlib.sha256(payload).hexdigest()
    certificate = hashlib.sha256(
        repr((exact_id, geometry, union_key)).encode()).hexdigest()
    return ProductionAlternative(
        semantic_parent_type, exact_id, children, union,
        tuple(outgoing_ports), certificate)


def compile_semantic_port_grammar(
        prototypes: Sequence[ClusterPrototype],
        alternatives: Sequence[ProductionAlternative], *,
        maximum_context_order: int = 2, overlap_tolerance: float = 1e-6,
        exclusion_distance: float = 1e-3,
) -> SemanticPortGrammar:
    if maximum_context_order < 0:
        raise ValueError("context order cannot be negative")
    if overlap_tolerance <= 0 or exclusion_distance < overlap_tolerance:
        raise ValueError("invalid geometric tolerances")
    alternatives = tuple(alternatives)
    ids = [item.exact_action_id for item in alternatives]
    if len(ids) != len(set(ids)):
        raise ValueError("exact alternative action IDs must be unique")
    for item in alternatives:
        expected = make_production_alternative(
            item.semantic_parent_type, item.children, prototypes,
            outgoing_ports=item.outgoing_ports,
            tolerance=overlap_tolerance)
        if (item.atom_union != expected.atom_union or
                item.exact_action_id != expected.exact_action_id or
                item.inclusion_certificate_digest !=
                expected.inclusion_certificate_digest):
            raise ValueError(
                "alternative identity or atom union is not replay-exact")
    return SemanticPortGrammar(
        tuple(prototypes), alternatives, maximum_context_order,
        overlap_tolerance, exclusion_distance, False)


def fit_incoming_port_marking(
        grammar: SemanticPortGrammar, traces: Sequence[IncomingPortTrace],
) -> PortMarking:
    alternatives = {item.exact_action_id: item for item in grammar.alternatives}
    exact = defaultdict(Counter)
    marginal = defaultdict(Counter)
    for trace in traces:
        if not trace.learned_from_training_only:
            raise ValueError("marking traces must be train-only")
        if len(trace.incoming_ports) > grammar.maximum_context_order:
            raise ValueError("trace exceeds the bounded marking domain")
        alternative = alternatives.get(trace.exact_action_id)
        if (alternative is None or alternative.semantic_parent_type !=
                trace.semantic_parent_type):
            raise ValueError("trace action is absent from its semantic type")
        context = tuple(sorted(trace.incoming_ports, key=repr))
        exact[trace.semantic_parent_type, context][trace.exact_action_id] += 1
        marginal[trace.semantic_parent_type][trace.exact_action_id] += 1
    return PortMarking(
        grammar.maximum_context_order,
        tuple(sorted(((key, tuple(sorted(value.items())))
                      for key, value in exact.items()), key=repr)),
        tuple(sorted(((key, tuple(sorted(value.items())))
                      for key, value in marginal.items()), key=repr)),
        len(traces), False)


def constant_marking(grammar: SemanticPortGrammar) -> PortMarking:
    return PortMarking(grammar.maximum_context_order, (), (), 0, False)


def enumerate_semantic_candidates(
        grammar: SemanticPortGrammar,
        request: ExpansionRequest,
) -> tuple[SemanticCandidate, ...]:
    """Enumerate the marking-independent exact action set."""
    if len(request.incoming_ports) > grammar.maximum_context_order:
        raise ValueError("request exceeds the bounded marking domain")
    if not is_proper_rotation(request.rotation):
        raise ValueError("semantic parent pose must be proper SE(3)")
    result = []
    for alternative in grammar.alternatives:
        if alternative.semantic_parent_type != request.semantic_parent_type:
            continue
        sites = tuple((species, _add(matvec(request.rotation, point),
                                     request.translation))
                      for species, point in alternative.atom_union)
        replay_digest = hashlib.sha256(repr((
            request.request_id, alternative.exact_action_id,
            tuple(sorted(_site_key(site, grammar.overlap_tolerance)
                         for site in sites)))).encode()).hexdigest()
        result.append(SemanticCandidate(
            request.request_id, request.semantic_parent_type,
            alternative.exact_action_id, request.rotation,
            request.translation, sites,
            alternative.inclusion_certificate_digest, replay_digest))
    return tuple(sorted(result, key=lambda item: item.exact_action_id))


def _ranking(marking, request, candidate):
    exact = dict(marking.exact_scores)
    marginal = dict(marking.marginal_scores)
    context = tuple(sorted(request.incoming_ports, key=repr))
    exact_count = dict(exact.get(
        (request.semantic_parent_type, context), ())).get(
            candidate.exact_action_id, 0)
    marginal_count = dict(marginal.get(
        request.semantic_parent_type, ())).get(candidate.exact_action_id, 0)
    return (-exact_count, -marginal_count, candidate.exact_action_id)


def execute_semantic_requests(
        grammar: SemanticPortGrammar, marking: PortMarking,
        requests: Sequence[ExpansionRequest], *,
        explicit_occupied_sites: Sequence[Site] = (),
) -> SemanticExecutionResult:
    """Depth-first exact replay; target data is not an input to this API."""
    if marking.maximum_context_order != grammar.maximum_context_order:
        raise ValueError("marking and grammar context domains differ")
    initial = tuple(explicit_occupied_sites)
    candidate_sets = tuple(tuple(item.exact_action_id for item in
                                 enumerate_semantic_candidates(grammar, request))
                           for request in requests)
    occupied = list(initial)
    accepted = []
    attempts = geometric = downstream = 0

    def search(index):
        nonlocal attempts, geometric, downstream
        if index == len(requests):
            return True
        request = requests[index]
        candidates = sorted(enumerate_semantic_candidates(grammar, request),
                            key=lambda item: _ranking(
                                marking, request, item))
        for candidate in candidates:
            attempts += 1
            _, novel, conflict = _classify_candidate(
                candidate.rendered_sites, occupied,
                grammar.overlap_tolerance, grammar.exclusion_distance)
            if conflict:
                geometric += 1
                continue
            occupied.extend(novel)
            accepted.append(AcceptedSemanticAction(
                request.request_id, candidate.exact_action_id, novel,
                candidate.replay_certificate_digest))
            if search(index + 1):
                return True
            downstream += 1
            accepted.pop()
            if novel:
                del occupied[-len(novel):]
        return False

    success = search(0)
    unique = {}
    for site in occupied:
        unique[_site_key(site, grammar.overlap_tolerance)] = site
    return SemanticExecutionResult(
        tuple(accepted), tuple(unique[key] for key in sorted(unique)),
        candidate_sets, attempts, geometric, downstream, not success, False)


def compile_from_semantic_quotient(
        prototypes: Sequence[ClusterPrototype], quotient_records: Sequence[Any],
        adapter: Callable[[Any, Sequence[ClusterPrototype]],
                          ProductionAlternative], *,
        maximum_context_order: int = 2, overlap_tolerance: float = 1e-6,
        exclusion_distance: float = 1e-3,
) -> SemanticPortGrammar:
    """Adapter hook for an external train-only semantic quotient corpus."""
    chosen = {}
    for record in quotient_records:
        alternative = adapter(record, prototypes)
        prior = chosen.get(alternative.exact_action_id)
        if prior is not None and prior != alternative:
            raise ValueError(
                "semantic quotient reused an exact ID for different geometry")
        chosen[alternative.exact_action_id] = alternative
    alternatives = tuple(chosen[key] for key in sorted(chosen))
    return compile_semantic_port_grammar(
        prototypes, alternatives,
        maximum_context_order=maximum_context_order,
        overlap_tolerance=overlap_tolerance,
        exclusion_distance=exclusion_distance)
