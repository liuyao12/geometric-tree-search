#!/usr/bin/env python3
"""Controls for finite conditional GCTS incidence states."""

from materials_gcts_incidence_state_marking import (
    IncidenceStateSpec, fit_incidence_state_group_statistics,
    fit_incidence_state_marking, incidence_state_group_statistics,
    incidence_state_marking_digest, score_incidence_state_marking)
from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)


def _descriptor(graph, role):
    return CandidateIncidenceDescriptor((
        ("role-occupied-message-graph", graph),
        ("coarse-role", role)))


def test_state_marking_uses_supported_exact_state_then_backoff():
    spec = IncidenceStateSpec((
        ("role-occupied-message-graph", "coarse-role"),
        ("coarse-role",)), 2, 2)
    examples = tuple(
        IncidenceTokenExample(group, _descriptor("good", "p"), True)
        for group in ("a", "b") for _ in range(2)) + tuple(
        IncidenceTokenExample(group, _descriptor("bad", "q"), False)
        for group in ("a", "b") for _ in range(2))
    model = fit_incidence_state_marking(examples, spec=spec)
    assert score_incidence_state_marking(
        model, _descriptor("good", "p")) > \
        score_incidence_state_marking(model, _descriptor("bad", "q"))
    # The unseen full graph backs off to the supported coarse role.
    assert score_incidence_state_marking(
        model, _descriptor("unseen", "p")) > model.prior


def test_state_digest_is_example_order_invariant():
    spec = IncidenceStateSpec((("coarse-role",),), 1, 1)
    examples = (
        IncidenceTokenExample("a", _descriptor("g", "p"), True),
        IncidenceTokenExample("b", _descriptor("b", "q"), False),
    )
    assert incidence_state_marking_digest(
        fit_incidence_state_marking(examples, spec=spec)) == \
        incidence_state_marking_digest(fit_incidence_state_marking(
            tuple(reversed(examples)), spec=spec))


def test_group_statistics_reproduce_direct_fit():
    spec = IncidenceStateSpec((("coarse-role",),), 1, 1)
    groups = (
        (IncidenceTokenExample("a", _descriptor("g", "p"), True),
         IncidenceTokenExample("a", _descriptor("b", "q"), False)),
        (IncidenceTokenExample("b", _descriptor("g", "p"), True),
         IncidenceTokenExample("b", _descriptor("b", "q"), False)),
    )
    direct = fit_incidence_state_marking(
        tuple(row for group in groups for row in group), spec=spec)
    grouped = fit_incidence_state_group_statistics(
        incidence_state_group_statistics(
            groups, signature_levels=spec.signature_levels),
        (0, 1), spec=spec)
    assert incidence_state_marking_digest(direct) == \
        incidence_state_marking_digest(grouped)


def main():
    test_state_marking_uses_supported_exact_state_then_backoff()
    test_state_digest_is_example_order_invariant()
    test_group_statistics_reproduce_direct_fit()
    print("incidence-state marking tests passed")


if __name__ == "__main__":
    main()
