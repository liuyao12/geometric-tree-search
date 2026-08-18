#!/usr/bin/env python3
"""Focused checks for finite pair-interaction incidence marking."""

from materials_gcts_incidence_pair_marking import (
    IncidencePairSpec, fit_incidence_pair_group_statistics,
    incidence_pair_group_statistics, incidence_pair_keys,
    incidence_pair_marking_digest, score_incidence_pair_marking)
from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)


def descriptor(role, graph, color):
    return CandidateIncidenceDescriptor(tuple(sorted((
        ("coarse-role", role),
        ("role-occupied-message-graph", graph),
        ("predicted-colors", (color,)),
    ), key=repr)))


def main():
    groups = tuple(tuple(IncidenceTokenExample(index, descriptor(*values), ok)
                         for values, ok in rows)
                   for index, rows in enumerate((
                       ((("a", "g", "red"), True),
                        (("a", "h", "blue"), False)),
                       ((("a", "g", "red"), True),
                        (("b", "g", "blue"), False)),
                       ((("a", "g", "red"), True),
                        (("b", "h", "blue"), False)),
                   )))
    pairs = (("coarse-role", "role-occupied-message-graph"),
             ("role-occupied-message-graph", "predicted-colors"))
    spec = IncidencePairSpec(pairs, 2, 2, 1., 1., 1.)
    stats = incidence_pair_group_statistics(groups, family_pairs=pairs)
    model = fit_incidence_pair_group_statistics(stats, (0, 1, 2), spec=spec)
    assert score_incidence_pair_marking(
        model, descriptor("a", "g", "red")) > \
        score_incidence_pair_marking(model, descriptor("b", "h", "blue"))
    assert incidence_pair_keys(descriptor("a", "g", "red"), pairs)
    assert incidence_pair_marking_digest(model) == \
        incidence_pair_marking_digest(model)
    try:
        fit_incidence_pair_group_statistics(stats, (), spec=spec)
    except ValueError:
        pass
    else:
        raise AssertionError("empty fit must fail closed")
    print("incidence-pair marking tests passed")


if __name__ == "__main__":
    main()
