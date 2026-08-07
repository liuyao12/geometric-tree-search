#!/usr/bin/env python3

import math

import materials_gcts_blind_continuation as blind
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_periodic_growth import replicate
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_parametric_recursive import apply_rule, discover_rule, evaluate


def test_generic_parametric_recursive_dispatch() -> None:
    result = evaluate()
    assert result.crystal.discovered_family == "translation_quotient"
    assert result.crystal.verified_growth == 512.0
    assert result.crystal.exact_reconstruction
    assert result.crystal.projected_atoms >= 1_000_000
    assert all(value > 0 for value in result.crystal.hierarchy_supports)

    assert result.quasicrystal.discovered_family == "internal_section_inflation"
    assert result.quasicrystal.verified_growth > 3.0
    assert result.quasicrystal.exact_reconstruction
    assert result.quasicrystal.rule_residual < 1e-5
    assert result.quasicrystal.projected_atoms >= 1_000_000
    assert tuple(result.quasicrystal.hierarchy_supports) == (14, 49, 270)

    assert (result.substitution_quasicrystal.discovered_family ==
            "substitution_product")
    assert result.substitution_quasicrystal.exact_reconstruction
    assert tuple(result.substitution_quasicrystal.hierarchy_supports) == (
        4, 17, 81)

    assert result.amorphous.discovered_family == "none"
    assert not result.amorphous.deterministic
    assert result.amorphous.projected_atoms is None
    assert tuple(result.amorphous.hierarchy_supports) == (0, 0, 0)


def test_iqc_rule_is_rotation_and_translation_invariant() -> None:
    configuration, _ = oracle_patch(3, 9.0)
    azimuth, tilt = 0.37, -0.29
    ca, sa = math.cos(azimuth), math.sin(azimuth)
    ct, st = math.cos(tilt), math.sin(tilt)

    def move(point):
        x, y, z = point
        first = (ca * x - sa * y, sa * x + ca * y, z)
        second = (first[0], ct * first[1] - st * first[2],
                  st * first[1] + ct * first[2])
        return (second[0] + 4.2, second[1] - 3.1, second[2] + 1.7)

    rotated = AtomicConfiguration(
        "rotated-IQC", tuple(move(point) for point in configuration.positions),
        configuration.species)
    rule = discover_rule(rotated)
    assert rule.family == "internal_section_inflation"
    assert rule.residual is not None and rule.residual < 1e-5
    grown = apply_rule(rotated, rule)
    oracle, _ = oracle_patch(4, 9.0 * rule.scale)
    expected = {(blind._site_key(move(point)), chemical)
                for point, chemical in zip(oracle.positions, oracle.species)}
    actual = {(blind._site_key(point), chemical)
              for point, chemical in zip(grown.positions, grown.species)}
    assert actual == expected


def test_crystal_rule_does_not_require_a_supplied_cell() -> None:
    source = next(item for item in benchmark_systems()
                  if item.name == "NaCl-rocksalt")
    finite = AtomicConfiguration(
        "finite-rocksalt", source.positions, source.species, None, False)
    rule = discover_rule(finite)
    assert rule.family == "translation_quotient"
    grown = apply_rule(finite, rule)
    expected_configuration = replicate(source)
    expected = {(blind._site_key(point), chemical)
                for point, chemical in zip(expected_configuration.positions,
                                            expected_configuration.species)}
    actual = {(blind._site_key(point), chemical)
              for point, chemical in zip(grown.positions, grown.species)}
    assert actual == expected


def test_substitution_rule_is_rotation_and_translation_invariant() -> None:
    configuration = make_input(9)
    angle = 0.41
    cosine, sine = math.cos(angle), math.sin(angle)

    def move(point):
        x, y, z = point
        return (cosine * x - sine * z + 2.3,
                y - 1.4,
                sine * x + cosine * z + 0.6)

    moved = AtomicConfiguration(
        "moved-Fibonacci-product", tuple(move(point)
                                          for point in configuration.positions),
        configuration.species)
    rule = discover_rule(moved)
    assert rule.family == "substitution_product"
    grown = apply_rule(moved, rule)
    expected_configuration = make_input(15)
    expected = {(blind._site_key(move(point)), chemical)
                for point, chemical in zip(expected_configuration.positions,
                                            expected_configuration.species)}
    actual = {(blind._site_key(point), chemical)
              for point, chemical in zip(grown.positions, grown.species)}
    assert actual == expected
