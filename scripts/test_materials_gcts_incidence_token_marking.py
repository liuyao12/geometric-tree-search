#!/usr/bin/env python3
"""Controls for finite joint port-incidence marking."""

from collections import Counter

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample,
    candidate_incidence_descriptors, fit_incidence_token_marking,
    score_incidence_descriptor)
from materials_gcts_recursive_connections import (
    LocalClusterType, MarkedProposalResult, RecursiveConnectionState)


def _proposals(reverse=False, transform=lambda point: point):
    left = RecursiveConnectionState(
        LocalClusterType("A", (1, 3)), LocalClusterType("B", (2, 4)), 2)
    right = RecursiveConnectionState(
        LocalClusterType("B", (2, 4)), LocalClusterType("A", (1, 3)), 3)
    canonical_points = tuple(transform(point) for point in (
        (0., 0., 0.), (1., 0., 0.), (0., 2., 0.)))
    points = tuple(reversed(canonical_points)) if reverse else canonical_points
    votes = Counter({point: index + 2
                     for index, point in enumerate(canonical_points)})
    states = {point: Counter({left: 2, right: 1}) for point in points}
    colors = {point: Counter({"A": 2}) for point in points}
    targets = {point: Counter({"B": 2}) for point in points}
    parents = {point: Counter({index: 2})
               for index, point in enumerate(points)}
    return MarkedProposalResult(
        votes, 0, None, colors, targets, states, parents)


def test_descriptor_is_permutation_translation_rotation_invariant():
    occupied = ((-.5, 0., 0.), (0., -.5, 0.))
    species = ("A", "B")
    first = candidate_incidence_descriptors(
        _proposals(), distance_scale=1., occupied_positions=occupied,
        occupied_species=species)
    # Proper quarter turn around z followed by a translation.
    second_raw = _proposals(
        True, lambda point: (7. - point[1], -3. + point[0], 11. + point[2]))
    second = candidate_incidence_descriptors(
        second_raw, distance_scale=1.,
        occupied_positions=tuple(
            (7. - point[1], -3. + point[0], 11. + point[2])
            for point in occupied), occupied_species=species)
    assert sorted((row.tokens for row in first.values()), key=repr) == \
        sorted((row.tokens for row in second.values()), key=repr)


def test_train_only_tokens_rank_supported_context():
    positive = CandidateIncidenceDescriptor((('role', 'good'),))
    negative = CandidateIncidenceDescriptor((('role', 'bad'),))
    examples = tuple(
        IncidenceTokenExample(group, positive, True)
        for group in ("a", "b", "c") for _ in range(3)) + tuple(
        IncidenceTokenExample(group, negative, False)
        for group in ("a", "b", "c") for _ in range(3))
    marker = fit_incidence_token_marking(
        examples, minimum_support=2, minimum_groups=2)
    assert score_incidence_descriptor(marker, positive) > \
        score_incidence_descriptor(marker, negative)
    assert all("coordinate" not in repr(token).lower() and
               "raw-id" not in repr(token).lower()
               for token in marker.token_weights)


def main():
    test_descriptor_is_permutation_translation_rotation_invariant()
    test_train_only_tokens_rank_supported_context()
    print("incidence token marking tests passed")


if __name__ == "__main__":
    main()
