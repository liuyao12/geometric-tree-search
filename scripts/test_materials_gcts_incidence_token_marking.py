#!/usr/bin/env python3
"""Controls for finite joint port-incidence marking."""

from collections import Counter

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample,
    candidate_incidence_descriptors, fit_incidence_token_marking,
    incidence_marking_digest,
    score_incidence_descriptor, score_incidence_descriptor_by_channel)
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
    parents = {point: Counter({canonical_points.index(point): 2})
               for point in points}
    return MarkedProposalResult(
        votes, 0, None, colors, targets, states, parents)


def test_descriptor_is_permutation_translation_rotation_invariant():
    occupied = ((-.5, 0., 0.), (0., -.5, 0.), (.5, .5, 0.))
    species = ("A", "B", "A")
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

    first_joint = candidate_incidence_descriptors(
        _proposals(), distance_scale=1., occupied_positions=occupied,
        occupied_species=species, joint_role_geometry=True)
    second_joint = candidate_incidence_descriptors(
        second_raw, distance_scale=1.,
        occupied_positions=tuple(
            (7. - point[1], -3. + point[0], 11. + point[2])
            for point in occupied), occupied_species=species,
        joint_role_geometry=True)
    assert sorted((row.tokens for row in first_joint.values()), key=repr) == \
        sorted((row.tokens for row in second_joint.values()), key=repr)
    assert any(token[0] == "role-occupied-shell"
               for row in first_joint.values() for token in row.tokens)


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


def test_channel_projection_counts_each_family_once():
    positive = CandidateIncidenceDescriptor((('role', 'good'),))
    negative = CandidateIncidenceDescriptor((('role', 'bad'),))
    examples = tuple(
        IncidenceTokenExample(group, positive, True)
        for group in ("a", "b", "c") for _ in range(3)) + tuple(
        IncidenceTokenExample(group, negative, False)
        for group in ("a", "b", "c") for _ in range(3))
    marker = fit_incidence_token_marking(
        examples, minimum_support=2, minimum_groups=2)
    repeated_family = CandidateIncidenceDescriptor((
        ('role', 'good'), ('role', 'bad')))
    mean_weight = .5 * (
        marker.token_weights[('role', 'good')] +
        marker.token_weights[('role', 'bad')])
    expected = 1 / (1 + __import__('math').exp(-(
        marker.intercept + mean_weight)))
    assert abs(score_incidence_descriptor_by_channel(
        marker, repeated_family) - expected) < 1e-12


def test_marking_digest_is_mapping_order_invariant():
    examples = tuple(IncidenceTokenExample(
        group, CandidateIncidenceDescriptor((("role", role),)), successful)
        for group, role, successful in (
            ("a", "left", True), ("b", "left", True),
            ("a", "right", False), ("b", "right", False)))
    marker = fit_incidence_token_marking(
        examples, minimum_support=2, minimum_groups=2)
    reversed_marker = type(marker)(
        marker.intercept, dict(reversed(tuple(marker.token_weights.items()))),
        dict(reversed(tuple(marker.token_evidence.items()))),
        marker.minimum_support, marker.minimum_groups, marker.shrinkage)
    assert incidence_marking_digest(marker) == \
        incidence_marking_digest(reversed_marker)


def main():
    test_descriptor_is_permutation_translation_rotation_invariant()
    test_train_only_tokens_rank_supported_context()
    test_channel_projection_counts_each_family_once()
    test_marking_digest_is_mapping_order_invariant()
    print("incidence token marking tests passed")


if __name__ == "__main__":
    main()
