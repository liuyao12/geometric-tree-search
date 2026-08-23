"""Tests for the shared tolerant colored-position scorer."""

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index, colored_position_match)


def test_scorer_accepts_quantized_geometry_but_preserves_species():
    index = colored_position_index(
        ((1.123456789, 2., 3.), (4., 5., 6.)), ("A", "B"))
    assert colored_position_match((1.123457, 2., 3.), "A", index)
    assert not colored_position_match((1.123457, 2., 3.), "B", index)
    assert colored_action_labels(
        (((1.123457, 2., 3.), "A"), ((4., 5., 6.), "B")), index) == \
        (True, True)
    assert not colored_position_match((1.12347, 2., 3.), "A", index)


if __name__ == "__main__":
    test_scorer_accepts_quantized_geometry_but_preserves_species()
    print("colored-position scorer: passed")
