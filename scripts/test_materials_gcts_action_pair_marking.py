#!/usr/bin/env python3
"""Focused tests for compatible two-action GCTS marking."""

from dataclasses import dataclass

from materials_gcts_action_pair_marking import (
    ActionPairExample, action_pair_adjustment, action_pair_descriptor,
    action_pair_marking_digest, fit_action_pair_marking)
from materials_gcts_incidence_token_marking import CandidateIncidenceDescriptor


@dataclass(frozen=True)
class Row:
    group: int
    point: tuple[float, float, float]
    color: str
    minimum_distance: float
    descriptor: CandidateIncidenceDescriptor


def row(group, x, role, color):
    return Row(group, (x, 0., 0.), color, 1., CandidateIncidenceDescriptor((
        ("coarse-role", role), ("predicted-colors", (color,)),
        ("occupied-count", 2),
        ("role-occupied-message-graph", role, 3))))


def main():
    examples = []
    for group in range(3):
        examples.append(ActionPairExample(group, action_pair_descriptor(
            row(group, 0., "a", "Cd"), row(group, 2., "b", "Yb")), True))
        examples.append(ActionPairExample(group, action_pair_descriptor(
            row(group, 0., "a", "Cd"), row(group, 5., "b", "Yb")), False))
    model = fit_action_pair_marking(examples, minimum_support=2,
                                    minimum_groups=2, shrinkage=1.)
    good = action_pair_descriptor(row(9, 0., "a", "Cd"),
                                  row(9, 2., "b", "Yb"))
    bad = action_pair_descriptor(row(9, 0., "a", "Cd"),
                                 row(9, 5., "b", "Yb"))
    assert action_pair_adjustment(model, good) > \
        action_pair_adjustment(model, bad)
    assert action_pair_marking_digest(model) == action_pair_marking_digest(model)
    assert action_pair_descriptor(row(9, 2., "b", "Yb"),
                                  row(9, 0., "a", "Cd")) == good
    print("action-pair marking tests passed")


if __name__ == "__main__":
    main()
