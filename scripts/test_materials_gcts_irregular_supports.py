#!/usr/bin/env python3

from materials_gcts_irregular_supports import (
    enumerate_frozen_vocabulary, fit_frozen_vocabulary,
    learn_irregular_cover)
from materials_gcts_irregular_supports_benchmark import evaluate


def _tiny_irregular_example():
    # Two congruent, non-spherical L-shaped colored supports, separated far
    # enough that the learner cannot confuse their copies by a shared radius.
    motif = ((0., 0., 0.), (1., 0., 0.), (1., 2., 0.), (1., 2., 3.),
             (5., 2., 3.))
    positions = motif + tuple((x + 10., -z, y) for x, y, z in motif)
    species = ("A", "B", "A", "C", "B") * 2
    return species, positions


def main() -> None:
    species, positions = _tiny_irregular_example()
    cover = learn_irregular_cover(
        species, positions, minimum_neighbors=2, maximum_neighbors=2,
        shell_gap=0.05, distance_tolerance=1e-6)
    assert cover.complete
    assert cover.repeated_type_count >= 1
    assert any(item.hierarchy_level == 1 and item.support_size >= 4
               for item in cover.support_types if item.kind == "repeated")

    # A deliberately non-repeating cloud exercises the explicit gap path.
    gap_cover = learn_irregular_cover(
        ("A", "A", "B", "B"),
        ((0., 0., 0.), (1., 0., 0.), (0., 3., 0.), (0., 0., 7.)),
        minimum_neighbors=1, maximum_neighbors=1,
        distance_tolerance=1e-6)
    assert gap_cover.complete
    assert gap_cover.repeated_type_count == 0
    assert gap_cover.gap_type_count == 2
    assert {item.kind for item in gap_cover.support_types} == {"gap"}

    vocabulary, _ = fit_frozen_vocabulary(
        species, positions, minimum_neighbors=2, maximum_neighbors=2,
        shell_gap=0.05, distance_tolerance=1e-6)
    enlarged_positions = positions + ((30., 31., 37.),)
    frozen = enumerate_frozen_vocabulary(
        vocabulary, species + ("Z",), enlarged_positions)
    assert frozen.coverage_of(range(len(positions))) == 1.0

    benchmark = evaluate()
    assert tuple(case.system for case in benchmark.cases) == (
        "NaCl-rocksalt", "Icosahedral-6D-model-set",
        "Cd5.7Yb-offcenter-seed")
    for case in benchmark.cases:
        assert case.complete_cover
        assert case.repeated_types >= 1
        assert case.merged_types >= 1
        assert case.largest_support > 1
        assert case.repeated_coverage > 0
        # Residuals are represented explicitly and canonically by species;
        # no test assumes that a difficult real cloud has zero gaps.
        assert case.gap_types <= case.species
        assert case.frozen_target_atoms > case.atoms
        assert case.frozen_occurrences > 0
        assert case.frozen_core_coverage > 0.99
    cases = {case.system: case for case in benchmark.cases}
    assert cases["NaCl-rocksalt"].frozen_heldout_coverage == 1.0
    assert cases["Icosahedral-6D-model-set"].frozen_heldout_coverage > 0.5
    # The predeclared off-centre crop prevents global icosahedral rotations
    # about the fixed point from masquerading as independent motif evidence.
    # Its genuinely repeated irregular supports transfer substantially, while
    # the remaining 23% stays an explicit red continuation target.
    assert cases["Cd5.7Yb-offcenter-seed"].frozen_heldout_coverage > 0.70
    assert cases["Cd5.7Yb-offcenter-seed"].frozen_heldout_coverage < 0.90
    print("generic irregular supports: all assertions passed", benchmark)


if __name__ == "__main__":
    main()
