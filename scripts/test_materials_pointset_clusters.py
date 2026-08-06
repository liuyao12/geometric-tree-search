#!/usr/bin/env python3

import math
import random

from materials_pointset_clusters import (
    enumerate_type_occurrences,
    learn_cluster_candidates,
    occurrence_type_labels,
)


def random_rotation(seed: int):
    """Shoemake's uniform unit-quaternion construction."""
    rng = random.Random(seed)
    u1, u2, u3 = rng.random(), rng.random(), rng.random()
    x = math.sqrt(1.0 - u1) * math.sin(2.0 * math.pi * u2)
    y = math.sqrt(1.0 - u1) * math.cos(2.0 * math.pi * u2)
    z = math.sqrt(u1) * math.sin(2.0 * math.pi * u3)
    w = math.sqrt(u1) * math.cos(2.0 * math.pi * u3)
    return (
        (1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w),
        (2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w),
        (2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y),
    )


def transform(points, rotation, translation):
    return tuple(
        tuple(sum(rotation[row][column] * point[column]
                  for column in range(3)) + translation[row]
              for row in range(3))
        for point in points
    )


def repeated_irregular_motifs():
    # Four species in a scalene, non-coplanar motif: there is neither a lattice
    # nor a preferred orientation.  The second copy is independently rotated.
    motif = ((0.0, 0.0, 0.0), (1.13, 0.12, -0.08),
             (-0.31, 1.37, 0.24), (0.19, -0.42, 1.61))
    second = transform(motif, random_rotation(17), (6.2, -3.7, 4.1))
    return ("Si", "O", "Al", "Na") * 2, motif + second


def test_invariant_under_arbitrary_rigid_motion():
    species, points = repeated_irregular_motifs()
    learned = learn_cluster_candidates(
        species, points, neighbor_count=3, minimum_occurrences=2)
    moved = learn_cluster_candidates(
        species,
        transform(points, random_rotation(2026), (11.7, -8.2, 0.314)),
        neighbor_count=3,
        minimum_occurrences=2,
    )
    assert tuple(cluster.signature for cluster in learned.cluster_types) == tuple(
        cluster.signature for cluster in moved.cluster_types)
    assert occurrence_type_labels(learned) == occurrence_type_labels(moved)
    assert tuple(tuple(item.member_indices for item in cluster.occurrences)
                 for cluster in learned.cluster_types) == tuple(
        tuple(item.member_indices for item in cluster.occurrences)
        for cluster in moved.cluster_types)
    assert math.isclose(learned.minimum_distance, moved.minimum_distance,
                        rel_tol=0.0, abs_tol=1e-12)


def test_non_lattice_point_set_yields_recurring_overlapping_clusters():
    species, points = repeated_irregular_motifs()
    learned = learn_cluster_candidates(
        species, points, neighbor_count=2, minimum_occurrences=2)
    assert learned.minimum_distance > 1.0
    assert len(learned.cluster_types) == 4
    assert all(len(cluster.occurrences) == 2
               for cluster in learned.cluster_types)
    assert all(len(occurrence.member_indices) == 3
               for occurrence in learned.occurrences)

    supports = [set(occurrence.member_indices)
                for occurrence in learned.occurrences]
    assert any(left != right and left & right
               for index, left in enumerate(supports)
               for right in supports[index + 1:])


def test_radius_neighborhood_and_minimum_separation_validation():
    species, points = repeated_irregular_motifs()
    learned = learn_cluster_candidates(
        species, points, neighbor_count=None, radius=2.5)
    assert len(learned.occurrences) == len(points)
    tiny = learn_cluster_candidates(
        ("A", "B"), ((0, 0, 0), (1e-9, 0, 0)), neighbor_count=1)
    assert tiny.minimum_distance > 0.0

    try:
        learn_cluster_candidates(("A", "B"), ((0, 0, 0), (0, 0, 0)),
                                 neighbor_count=1)
    except ValueError as error:
        assert "positive separation" in str(error)
    else:
        raise AssertionError("coincident points should be rejected")


def test_distance_graph_embedding_ignores_closer_distractors():
    # Learn one colored tetrahedral environment without any lattice metadata.
    motif = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0),
             (1.0, -1.0, -1.0), (-1.0, 1.0, -1.0),
             (-1.0, -1.0, 1.0))
    motif_species = ("Si", "O", "O", "O", "O")
    learned = learn_cluster_candidates(
        motif_species, motif, neighbor_count=4)
    silicon_type = next(cluster for cluster in learned.cluster_types
                        if cluster.center_species == "Si")

    # Two independently oriented copies are embedded in a larger point set.
    # In each copy an extra O is substantially closer to Si than every true O,
    # so taking the four nearest atoms cannot recover the planted SiO4 support.
    # The four O vertices are symmetry-equivalent, exercising repeated-species
    # mappings and the support deduplication of their 4! graph automorphisms.
    second = transform(motif, random_rotation(73), (8.1, -5.4, 3.3))
    target_points = motif + ((0.23, 0.04, -0.02),) + second + (
        transform(((0.19, -0.03, 0.06),), random_rotation(73),
                  (8.1, -5.4, 3.3))[0],)
    target_species = motif_species + ("O",) + motif_species + ("O",)
    occurrences = enumerate_type_occurrences(
        silicon_type, target_species, target_points,
        distance_tolerance=1e-8)

    supports = {frozenset(item.member_indices) for item in occurrences}
    assert frozenset(range(5)) in supports
    assert frozenset(range(6, 11)) in supports
    assert len(supports) == len(occurrences) == 2
    assert all(5 not in support and 11 not in support for support in supports)


def main():
    test_invariant_under_arbitrary_rigid_motion()
    test_non_lattice_point_set_yields_recurring_overlapping_clusters()
    test_radius_neighborhood_and_minimum_separation_validation()
    test_distance_graph_embedding_ignores_closer_distractors()
    print("point-set cluster learner: all assertions passed")


if __name__ == "__main__":
    main()
