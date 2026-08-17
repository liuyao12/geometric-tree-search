#!/usr/bin/env python3

import math
import random

from materials_gcts_frontier_state_grammar import (
    FrontierWaveSnapshot, compile_frontier_state_grammar)


def _triangle(scale, center):
    x, y, z = center
    return ((x, y, z), (x + scale, y, z),
            (x + .5 * scale, y + math.sqrt(3) * .5 * scale, z))


def _expanding_fixture():
    waves = []
    for wave, (scale, copies) in enumerate(((1., 1), (2., 2), (4., 4)), 1):
        positions = tuple(
            point for copy in range(copies)
            for point in _triangle(scale, (copy * 40., wave * 80., 0.)))
        waves.append(FrontierWaveSnapshot(
            wave, positions, tuple("A" for _ in positions)))
    return tuple(waves)


def test_expanding_frontier_state_is_detected_without_material_metadata():
    grammar = compile_frontier_state_grammar(
        _expanding_fixture(), maximum_nodes=3)
    assert grammar.complete_cover
    assert grammar.repeated_covered_atoms == grammar.atom_count == 21
    assert grammar.exponential_gate_passed
    witness = next(item for item in grammar.stationary_witnesses
                   if item.covered_atoms == (3, 6, 12))
    assert math.isclose(witness.learned_scale_ratio, 2.)
    assert witness.support_growth_ratios == (2., 2.)
    assert not grammar.target_used


def test_reflection_is_not_merged_with_a_proper_chiral_state():
    tetrahedron = ((1., 1., 1.), (1., -1., -1.), (-1., 1., -1.),
                   (-1., -1., 1.))
    reflected = tuple((-x, y, z) for x, y, z in tetrahedron)
    first = FrontierWaveSnapshot(1, tetrahedron, ("A", "B", "C", "D"))
    translated = tuple((x + 10., y + 20., z - 7.)
                       for x, y, z in tetrahedron)
    second = FrontierWaveSnapshot(2, translated, ("A", "B", "C", "D"))
    third = FrontierWaveSnapshot(3, reflected, ("A", "B", "C", "D"))
    grammar = compile_frontier_state_grammar(
        (first, second, third), maximum_nodes=4)
    assert grammar.complete_cover
    tetra_type = next(state for state in grammar.recurring_state_types
                      if state.support_size == 4)
    assert len(tetra_type.occurrences) == 2
    assert tetra_type.independent_waves == 2
    assert not grammar.exponential_gate_passed


def test_amorphous_control_keeps_residuals_and_rejects_recurrence():
    rng = random.Random(731)
    waves = []
    for wave in range(1, 4):
        points = []
        while len(points) < 9:
            point = tuple(rng.uniform(-10., 10.) for _ in range(3))
            if all(math.dist(point, other) > .8 for other in points):
                points.append(point)
        waves.append(FrontierWaveSnapshot(
            wave, tuple(points), tuple(f"X{wave}-{index}"
                                       for index in range(len(points)))))
    grammar = compile_frontier_state_grammar(waves, maximum_nodes=4)
    assert grammar.complete_cover
    assert not grammar.recurring_state_types
    assert len(grammar.residual_sites) == grammar.atom_count
    assert not grammar.exponential_gate_passed


def test_tainted_or_invalid_inputs_fail_closed():
    waves = _expanding_fixture()
    tainted = (waves[0], waves[1], FrontierWaveSnapshot(
        waves[2].wave, waves[2].positions, waves[2].species, True))
    grammar = compile_frontier_state_grammar(tainted, maximum_nodes=3)
    assert grammar.target_used
    assert not grammar.exponential_gate_passed
    try:
        compile_frontier_state_grammar((waves[0], waves[0]), maximum_nodes=3)
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("duplicate wave numbers must fail")


def test_permutation_and_proper_rigid_motion_preserve_scientific_grammar():
    original = compile_frontier_state_grammar(
        _expanding_fixture(), maximum_nodes=3)
    transformed = []
    for wave in _expanding_fixture():
        rows = tuple(reversed(tuple(zip(wave.species, wave.positions))))
        species = tuple(item[0] for item in rows)
        # (x, y, z) -> (y, -x, z) is a determinant +1 rotation.
        positions = tuple((point[1] + 17., -point[0] - 3., point[2] + 5.)
                          for _label, point in rows)
        transformed.append(FrontierWaveSnapshot(
            wave.wave, positions, species))
    moved = compile_frontier_state_grammar(
        transformed, maximum_nodes=3)
    assert moved.grammar_digest == original.grammar_digest
    assert moved.repeated_covered_atoms == original.repeated_covered_atoms
    assert moved.exponential_gate_passed


if __name__ == "__main__":
    test_expanding_frontier_state_is_detected_without_material_metadata()
    test_reflection_is_not_merged_with_a_proper_chiral_state()
    test_amorphous_control_keeps_residuals_and_rejects_recurrence()
    test_tainted_or_invalid_inputs_fail_closed()
    test_permutation_and_proper_rigid_motion_preserve_scientific_grammar()
    print("frontier-state grammar tests: passed")
