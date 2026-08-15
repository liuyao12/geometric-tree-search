#!/usr/bin/env python3
"""Controls for exact alternatives beneath one semantic recursive type."""

from dataclasses import dataclass

from materials_gcts_oriented_overlap_ports import IDENTITY, make_prototype
from materials_gcts_semantic_production_grammar import (
    ExactChildPlacement, ExpansionRequest, IncomingPortTrace,
    compile_from_semantic_quotient, compile_semantic_port_grammar,
    constant_marking, enumerate_semantic_candidates,
    execute_semantic_requests, fit_incoming_port_marking,
    make_production_alternative)


def _control():
    prototypes = (
        make_prototype(0, (
            ("A", (0., 0., 0.)), ("A", (.2, 0., 0.)),
            ("A", (0., .2, 0.)))),
        make_prototype(1, (
            ("B", (0., 0., 0.)), ("B", (.2, 0., 0.)),
            ("B", (0., .2, 0.)))))
    good = make_production_alternative(
        "coarse-S", (ExactChildPlacement(
            0, IDENTITY, (0., 0., 0.)),), prototypes,
        outgoing_ports=("A-socket",))
    bad = make_production_alternative(
        "coarse-S", (ExactChildPlacement(
            1, IDENTITY, (2., 0., 0.)),), prototypes,
        outgoing_ports=("B-socket",))
    # The canonical digest order is deliberately adverse for the constant
    # policy; no mutable display/order label is used as an action identity.
    assert bad.exact_action_id < good.exact_action_id
    grammar = compile_semantic_port_grammar(
        prototypes, (good, bad), maximum_context_order=1,
        overlap_tolerance=1e-6, exclusion_distance=.15)
    requests = (
        ExpansionRequest(0, "coarse-S", IDENTITY, (0., 0., 0.),
                         ("red-in",)),
        ExpansionRequest(1, "coarse-S", IDENTITY, (2., 0., 0.),
                         ("blue-in",)))
    traces = tuple(
        IncomingPortTrace("coarse-S", (port,), good.exact_action_id)
        for port in ("red-in", "blue-in") for _ in range(3))
    shuffled = tuple(
        IncomingPortTrace("coarse-S", trace.incoming_ports,
                          bad.exact_action_id)
        for trace in traces)
    blocker = (("C", (4., 0., 0.)),)
    return (prototypes, good, bad, grammar, requests, traces, shuffled,
            blocker)


def test_marking_ranks_same_exact_actions_and_avoids_backtracking():
    _, good, _, grammar, requests, traces, shuffled, blocker = _control()
    learned = fit_incoming_port_marking(grammar, traces)
    shuffled_marking = fit_incoming_port_marking(grammar, shuffled)
    constant = constant_marking(grammar)
    candidate_ids = tuple(tuple(item.exact_action_id for item in
                                enumerate_semantic_candidates(grammar, request))
                          for request in requests)
    marked = execute_semantic_requests(
        grammar, learned, requests, explicit_occupied_sites=blocker)
    shuffled_result = execute_semantic_requests(
        grammar, shuffled_marking, requests,
        explicit_occupied_sites=blocker)
    constant_result = execute_semantic_requests(
        grammar, constant, requests, explicit_occupied_sites=blocker)
    assert marked.candidate_sets == shuffled_result.candidate_sets == (
        constant_result.candidate_sets) == candidate_ids
    assert tuple(item.exact_action_id for item in marked.accepted_actions) == (
        good.exact_action_id, good.exact_action_id)
    assert marked.total_backtracks == 0
    assert shuffled_result.total_backtracks == 4
    assert constant_result.total_backtracks == 4
    assert shuffled_result.downstream_choice_backtracks == 1
    assert constant_result.downstream_choice_backtracks == 1
    assert not marked.exhausted
    assert not marked.target_used and not learned.target_used
    assert len({item.replay_certificate_digest
                for item in marked.accepted_actions}) == 2


def test_same_coarse_type_retains_multiple_replay_exact_identities():
    _, good, bad, grammar, requests, _, _, _ = _control()
    alternatives = tuple(item for item in grammar.alternatives
                         if item.semantic_parent_type == "coarse-S")
    assert len(alternatives) == 2
    assert {item.exact_action_id for item in alternatives} == {
        good.exact_action_id, bad.exact_action_id}
    assert all(item.atom_union and item.inclusion_certificate_digest
               for item in alternatives)
    assert tuple(item.exact_action_id for item in
                 enumerate_semantic_candidates(grammar, requests[0])) == tuple(
        sorted((good.exact_action_id, bad.exact_action_id)))


@dataclass(frozen=True)
class _QuotientRecord:
    alternative: object


def test_semantic_quotient_adapter_does_not_reidentify_actions():
    prototypes, good, bad, _, _, _, _, _ = _control()
    records = (_QuotientRecord(good), _QuotientRecord(bad))
    adapted = compile_from_semantic_quotient(
        prototypes, records, lambda record, _: record.alternative,
        maximum_context_order=1, overlap_tolerance=1e-6,
        exclusion_distance=.15)
    assert tuple(item.exact_action_id for item in adapted.alternatives) == tuple(
        sorted((good.exact_action_id, bad.exact_action_id)))
    assert not adapted.target_artifacts_stored


if __name__ == "__main__":
    test_marking_ranks_same_exact_actions_and_avoids_backtracking()
    test_same_coarse_type_retains_multiple_replay_exact_identities()
    test_semantic_quotient_adapter_does_not_reidentify_actions()
    print("semantic production alternatives: all assertions passed")
