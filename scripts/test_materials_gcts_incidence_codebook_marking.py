#!/usr/bin/env python3
"""Controls for the finite GCTS incidence prototype codebook."""

from materials_gcts_incidence_codebook_marking import (
    IncidenceCodebookSpec, fit_incidence_codebook,
    incidence_codebook_digest, score_incidence_codebook)
from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)


def _descriptor(role, node, irrelevant):
    return CandidateIncidenceDescriptor((
        ("coarse-role", role),
        ("role-occupied-message-node", node),
        ("raw-irrelevant-family", irrelevant)))


def test_codebook_is_finite_id_free_and_ranks_recurring_positive():
    spec = IncidenceCodebookSpec((
        "coarse-role", "role-occupied-message-node"))
    examples = (
        IncidenceTokenExample("a", _descriptor("p", "n", 1), True),
        IncidenceTokenExample("b", _descriptor("p", "n", 2), True),
        IncidenceTokenExample("a", _descriptor("q", "x", 3), False),
        IncidenceTokenExample("b", _descriptor("q", "x", 4), False),
    )
    model = fit_incidence_codebook(examples, spec=spec)
    assert len(model.prototypes) == 1
    assert score_incidence_codebook(model, _descriptor("p", "n", 99)) > \
        score_incidence_codebook(model, _descriptor("q", "x", 99))
    assert "raw-irrelevant-family" not in repr(model)


def test_codebook_digest_is_example_order_invariant():
    spec = IncidenceCodebookSpec(("coarse-role",), 2)
    examples = (
        IncidenceTokenExample("a", _descriptor("p", "n", 1), True),
        IncidenceTokenExample("b", _descriptor("q", "x", 2), True),
        IncidenceTokenExample("a", _descriptor("r", "y", 3), False),
    )
    assert incidence_codebook_digest(
        fit_incidence_codebook(examples, spec=spec)) == \
        incidence_codebook_digest(
            fit_incidence_codebook(tuple(reversed(examples)), spec=spec))


def test_codebook_requires_independent_group_recurrence():
    examples = (
        IncidenceTokenExample("a", _descriptor("p", "n", 1), True),
        IncidenceTokenExample("a", _descriptor("p", "n", 2), True),
        IncidenceTokenExample("b", _descriptor("q", "x", 3), True),
        IncidenceTokenExample("c", _descriptor("q", "x", 4), True),
    )
    model = fit_incidence_codebook(examples, spec=IncidenceCodebookSpec(
        ("coarse-role", "role-occupied-message-node"), 1, 2))
    assert len(model.prototypes) == 1
    assert "'q'" in repr(model.prototypes[0])


def main():
    test_codebook_is_finite_id_free_and_ranks_recurring_positive()
    test_codebook_digest_is_example_order_invariant()
    test_codebook_requires_independent_group_recurrence()
    print("incidence codebook marking tests passed")


if __name__ == "__main__":
    main()
