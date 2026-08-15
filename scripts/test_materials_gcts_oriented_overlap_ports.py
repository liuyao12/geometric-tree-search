#!/usr/bin/env python3

import math

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, determinant, expand_port_orbit,
    fit_occurrence_pose, learn_overlap_ports,
    make_prototype, matmul, matvec, place_child)


def _axis_angle(axis, angle):
    length = math.sqrt(sum(value * value for value in axis))
    x, y, z = (value / length for value in axis)
    c, s, d = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
    return ((c + x*x*d, x*y*d - z*s, x*z*d + y*s),
            (y*x*d + z*s, c + y*y*d, y*z*d - x*s),
            (z*x*d - y*s, z*y*d + x*s, c + z*z*d))


def _octahedron(center, neighbor):
    return make_prototype(0 if center == "Na" else 1, (
        (center, (0.0, 0.0, 0.0)),
        (neighbor, (1.0, 0.0, 0.0)),
        (neighbor, (-1.0, 0.0, 0.0)),
        (neighbor, (0.0, 1.0, 0.0)),
        (neighbor, (0.0, -1.0, 0.0)),
        (neighbor, (0.0, 0.0, 1.0)),
        (neighbor, (0.0, 0.0, -1.0))))


def test_nacl_six_directions_are_one_symmetry_quotiented_port():
    sodium = _octahedron("Na", "Cl")
    chloride = _octahedron("Cl", "Na")
    assert len(sodium.proper_symmetries) == 24
    assert len(chloride.proper_symmetries) == 24
    directions = ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
                  (0.0, 1.0, 0.0), (0.0, -1.0, 0.0),
                  (0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
    occurrences = [ClusterOccurrence(0, 0, IDENTITY, (0.0, 0.0, 0.0))]
    occurrences.extend(ClusterOccurrence(index + 1, 1, IDENTITY, direction)
                       for index, direction in enumerate(directions))
    atlas = learn_overlap_ports(
        (sodium, chloride), occurrences, minimum_overlap=2,
        allowed_type_pairs=frozenset({(0, 1)}))
    assert atlas.witnessed_relations == 6
    assert len(atlas.ports) == 1
    assert atlas.symmetry_orbit_collapses == 5
    assert atlas.ports[0].observations == 6
    assert len(atlas.ports[0].overlap) == 2
    assert atlas.ports[0].overlap_species == ("Na", "Cl")
    orbit = expand_port_orbit(sodium, chloride, atlas.ports[0])
    assert len(orbit) == 6
    assert {tuple(round(value) for value in translation)
            for _, translation in orbit} == set(directions)


def test_irregular_port_is_invariant_to_arbitrary_global_rotation():
    parent = make_prototype(4, (
        ("A", (-0.2, -0.3, -0.4)), ("B", (1.1, -0.1, 0.2)),
        ("C", (-0.4, 1.3, 0.1)), ("A", (-0.5, -0.2, 1.4))))
    # The two clusters deliberately have unrelated, irregular shapes.  The
    # translation is chosen so the first child site coincides with parent site 1.
    child = make_prototype(7, (
        ("B", (0.3, -0.4, 0.1)), ("D", (1.5, 0.2, -0.3)),
        ("A", (-0.7, 0.6, 0.4)), ("C", (0.1, -0.2, 1.6))))
    relative = _axis_angle((0.3, 0.7, -0.2), 0.731)
    translation = tuple(parent.sites[1][1][axis] -
                        matvec(relative, child.sites[0][1])[axis]
                        for axis in range(3))
    base = learn_overlap_ports((parent, child), (
        ClusterOccurrence(1, 4, IDENTITY, (0.0, 0.0, 0.0)),
        ClusterOccurrence(2, 7, relative, translation)),
        allowed_type_pairs=frozenset({(4, 7)}))
    global_rotation = _axis_angle((1.0, -2.0, 0.5), 1.117)
    shift = (5.2, -3.4, 9.1)
    rotated = learn_overlap_ports((parent, child), (
        ClusterOccurrence(1, 4, global_rotation, shift),
        ClusterOccurrence(2, 7, matmul(global_rotation, relative),
                          tuple(shift[axis] + matvec(
                              global_rotation, translation)[axis]
                                for axis in range(3)))),
        allowed_type_pairs=frozenset({(4, 7)}))
    assert len(base.ports) == len(rotated.ports) == 1
    assert (base.ports[0].symmetry_orbit_key ==
            rotated.ports[0].symmetry_orbit_key)
    assert base.ports[0].overlap == rotated.ports[0].overlap
    placed_rotation, placed_translation = place_child(
        global_rotation, shift, base.ports[0])
    assert determinant(placed_rotation) > 0.999999
    assert math.dist(placed_translation, tuple(
        shift[axis] + matvec(global_rotation,
                             base.ports[0].relative_translation)[axis]
        for axis in range(3))) < 1e-9


def test_reflected_occurrence_is_rejected_not_folded_into_rotation_port():
    prototype = make_prototype(9, (
        ("A", (0.0, 0.0, 0.0)), ("B", (1.0, 0.0, 0.0)),
        ("C", (0.0, 2.0, 0.0)), ("D", (0.0, 0.0, 3.0))))
    reflection = ((-1.0, 0.0, 0.0),
                  (0.0, 1.0, 0.0),
                  (0.0, 0.0, 1.0))
    atlas = learn_overlap_ports((prototype,), (
        ClusterOccurrence(1, 9, IDENTITY, (0.0, 0.0, 0.0)),
        ClusterOccurrence(2, 9, reflection, (1.0, 0.0, 0.0))))
    assert atlas.rejected_improper_occurrences == 1
    assert atlas.witnessed_relations == 0
    assert atlas.ports == ()


def test_unlike_species_coincidence_is_a_connection_conflict():
    first = make_prototype(11, (
        ("A", (0.0, 0.0, 0.0)), ("B", (1.0, 0.0, 0.0)),
        ("C", (0.0, 2.0, 0.0)), ("D", (0.0, 0.0, 3.0))))
    second = make_prototype(12, (
        ("X", (0.0, 0.0, 0.0)), ("Y", (1.0, 0.0, 0.0)),
        ("Z", (0.0, 2.0, 0.0)), ("W", (0.0, 0.0, 3.0))))
    atlas = learn_overlap_ports((first, second), (
        ClusterOccurrence(1, 11, IDENTITY, (0.0, 0.0, 0.0)),
        ClusterOccurrence(2, 12, IDENTITY, (0.0, 0.0, 0.0))),
        allowed_type_pairs=frozenset({(11, 12)}))
    assert atlas.rejected_conflicting_relations == 1
    assert atlas.ports == ()


def test_unordered_occurrence_pose_is_fitted_without_a_central_atom():
    prototype = make_prototype(21, (
        ("A", (0.1, 0.2, -0.4)), ("B", (1.4, -0.3, 0.2)),
        ("C", (-0.2, 1.7, 0.5)), ("A", (0.3, 0.1, 2.2))))
    rotation = _axis_angle((.2, -.7, 1.1), .83)
    shift = (4.2, -3.1, .7)
    observed = tuple(reversed(tuple(
        (species, tuple(shift[axis] + matvec(rotation, point)[axis]
                        for axis in range(3)))
        for species, point in prototype.sites)))
    fitted = fit_occurrence_pose(31, prototype, observed)
    assert determinant(fitted.rotation) > .999999
    assert math.dist(fitted.translation, shift) < 1e-8
    moved = tuple((species, tuple(
        fitted.translation[axis] + matvec(fitted.rotation, point)[axis]
        for axis in range(3))) for species, point in prototype.sites)
    assert all(any(species == target_species and math.dist(point, target) < 1e-8
                   for target_species, target in observed)
               for species, point in moved)


def test_occurrence_pair_filter_limits_the_witnessed_relation_graph():
    sodium = _octahedron("Na", "Cl")
    chloride = _octahedron("Cl", "Na")
    occurrences = (
        ClusterOccurrence(1, 0, IDENTITY, (0., 0., 0.)),
        ClusterOccurrence(2, 1, IDENTITY, (1., 0., 0.)),
        ClusterOccurrence(3, 1, IDENTITY, (-1., 0., 0.)))
    atlas = learn_overlap_ports(
        (sodium, chloride), occurrences, minimum_overlap=2,
        allowed_occurrence_pairs=frozenset({(1, 2)}))
    assert atlas.witnessed_relations == 1
    assert len(atlas.ports) == 1


if __name__ == "__main__":
    test_nacl_six_directions_are_one_symmetry_quotiented_port()
    test_irregular_port_is_invariant_to_arbitrary_global_rotation()
    test_reflected_occurrence_is_rejected_not_folded_into_rotation_port()
    test_unlike_species_coincidence_is_a_connection_conflict()
    test_unordered_occurrence_pose_is_fitted_without_a_central_atom()
    test_occurrence_pair_filter_limits_the_witnessed_relation_graph()
    print("finite proper-SE(3) oriented overlap ports: passed")
