#!/usr/bin/env python3

from materials_gcts_section_marking import (
    ColoredPoint, MarkingExample, SectionSettings, describe_examples,
    fit_marker, fit_marker_auto, predict, transform_rigid)


def _toy_cloud():
    centers = ((0., 0., 0.), (4., 0., 0.), (0., 4., 0.), (4., 4., 0.))
    shell = ((1., 0., 0.), (-1., 0., 0.), (0., .55, 0.),
             (0., -.55, 0.), (0., 0., .25), (0., 0., -.25))
    points = []
    for center in centers:
        for offset in shell:
            points.append(ColoredPoint(
                tuple(center[axis] + offset[axis] for axis in range(3)),
                ("A",)))
    return tuple(points), centers


def test_generic_sections_are_rigid_motion_invariant() -> None:
    points, centers = _toy_cloud()
    examples = (MarkingExample(0, 1, 1), MarkingExample(0, 2, 0),
                MarkingExample(2, 3, 1), MarkingExample(1, 3, 0))
    original = describe_examples(points, centers, examples, 1.2,
                                 (.4, .8, 1.2), False)
    rotation = ((0., -1., 0.), (1., 0., 0.), (0., 0., 1.))
    translation = (7., -3., 2.)
    moved_points = tuple(ColoredPoint(
        transform_rigid(point.position, rotation, translation), point.colors)
                         for point in points)
    moved_centers = tuple(transform_rigid(center, rotation, translation)
                          for center in centers)
    moved = describe_examples(moved_points, moved_centers, examples, 1.2,
                              (.4, .8, 1.2), False)
    for left_family, right_family in zip(original, moved):
        for left, right in zip(left_family, right_family):
            assert all(abs(a - b) < 1e-10 for a, b in zip(left, right))


def test_generic_marker_filters_actions_without_material_labels() -> None:
    points, centers = _toy_cloud()
    training = (MarkingExample(0, 1, 1), MarkingExample(0, 2, 0),
                MarkingExample(2, 3, 1), MarkingExample(1, 3, 0))
    marker = fit_marker(
        points, centers, training, 1.2, SectionSettings(1, .5),
        SectionSettings(1, .5), (.4, .8, 1.2), chemical=False)
    results = predict(marker, points, centers, training)
    assert [result.accepted for result in results] == [True, False, True, False]
    assert marker.descriptor_dimensions == 29


def test_settings_are_selected_with_parent_groups_held_out() -> None:
    points, centers = _toy_cloud()
    training = (MarkingExample(0, 1, 1, "parent-a"),
                MarkingExample(0, 2, 0, "parent-a"),
                MarkingExample(2, 3, 1, "parent-b"),
                MarkingExample(1, 3, 0, "parent-b"))
    marker = fit_marker_auto(points, centers, training, 1.2,
                             (.4, .8, 1.2), chemical=False)
    results = predict(marker, points, centers, training)
    assert [result.accepted for result in results] == [True, False, True, False]
    assert marker.histogram.settings.neighbors == 1
    assert marker.moments.settings.neighbors == 1


def test_periodic_crystal_control_does_not_invent_rejections() -> None:
    # A B2-like translated motif: once the quotient has established that every
    # integer-cell displacement is legal, no local marking should reject one.
    centers = tuple((4. * x, 4. * y, 4. * z)
                    for x in range(2) for y in range(2) for z in range(2))
    points = []
    for center in centers:
        points.append(ColoredPoint(center, ("A",)))
        points.append(ColoredPoint(
            tuple(center[axis] + 1.0 for axis in range(3)), ("B",)))
    examples = tuple(MarkingExample(0, source, 1, "periodic-parent")
                     for source in range(1, len(centers)))
    marker = fit_marker_auto(tuple(points), centers, examples, 2.0,
                             (.75, 1.5, 2.0), chemical=True)
    assert all(result.accepted
               for result in predict(marker, tuple(points), centers, examples))
    assert marker.histogram.settings == SectionSettings(1, .5)
    assert marker.moments.settings == SectionSettings(1, .5)


if __name__ == "__main__":
    test_generic_sections_are_rigid_motion_invariant()
    test_generic_marker_filters_actions_without_material_labels()
    test_settings_are_selected_with_parent_groups_held_out()
    test_periodic_crystal_control_does_not_invent_rejections()
    print("generic bounded GCTS section marking: all assertions passed")
